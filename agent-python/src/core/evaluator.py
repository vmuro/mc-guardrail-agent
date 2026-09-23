import os
import uuid
from typing import List, Dict, Any, Optional

from src.tools.screener import get_technical_indicators
from src.tools.news_parser import get_stock_news
from src.core.agent import analyze_market_with_gemini
from src.core.guardrail import validate_portfolio_proposal
from src.core.consent import create_fido_consent_challenge
from src.core.notifier import send_push_notification
from src.core.logger import log_event

FIDO_BASE_URL = os.getenv("FIDO_BASE_URL", "http://localhost:8080").rstrip("/")


def collect_market_data_for_tickers(tickers: List[str]) -> Dict[str, Any]:
    """Coleta indicadores técnicos e notícias para uma lista de tickers."""
    market_snapshot = {}
    for ticker in tickers:
        t = ticker.strip().upper()
        if not t:
            continue
        try:
            tech = get_technical_indicators(t, period="1y")
            if tech:
                tech["recent_news"] = get_stock_news(t, max_items=2) or ["Nenhuma notícia recente relevante."]
                market_snapshot[t] = tech
        except Exception as e:
            print(f"⚠️ Erro ao coletar {t}: {e}")
    return market_snapshot


def evaluate_client_portfolio(
    client_id: str,
    budget: float,
    risk_profile: str = "MODERATE",
    watchlist: Optional[List[str]] = None,
    custom_orders: Optional[List[Dict[str, Any]]] = None,
    client_name: Optional[str] = None,
    segment: Optional[str] = "Varejo",
    market_data: Optional[Dict[str, Any]] = None,
    fido_base_url: Optional[str] = None,
    send_notifications: bool = True,
    device_token: Optional[str] = None
) -> Dict[str, Any]:
    """
    Executa a avaliação completa de portfólio e ordens com governança determinística.
    Suporta:
      1. Modo Autônomo com IA (Watchlist -> Screener B3 -> Gemini Flash -> Guardrail)
      2. Modo Auditoria Direta (custom_orders -> Guardrail puro determinístico)
    """
    base_url = (fido_base_url or FIDO_BASE_URL).rstrip("/")
    clean_client_name = client_name or f"Investidor {client_id}"
    clean_watchlist = [t.strip().upper() for t in (watchlist or []) if t.strip()]

    # Determina tickers necessários para cotação em tempo real
    needed_tickers = list(clean_watchlist)
    if custom_orders:
        for ord_item in custom_orders:
            t = ord_item.get("ticker", "").strip().upper()
            if t and t not in needed_tickers:
                needed_tickers.append(t)

    # Coleta dados de mercado caso não tenham sido fornecidos externamente
    current_market_data = dict(market_data or {})
    missing_tickers = [t for t in needed_tickers if t not in current_market_data]
    if missing_tickers:
        fetched = collect_market_data_for_tickers(missing_tickers)
        current_market_data.update(fetched)

    # 1. Definição da Proposta (Gemini ou Ordens Diretas)
    if custom_orders and len(custom_orders) > 0:
        # Modo Auditoria Direta: cliente enviou ordens pré-definidas
        raw_decision = {
            "portfolio_rationale": "Auditoria de ordens propostas diretamente pelo cliente.",
            "allocations": custom_orders
        }
    else:
        # Modo Autônomo: consulta Gemini 2.5 Flash para tese de portfólio
        client_snapshot = [current_market_data[t] for t in clean_watchlist if t in current_market_data]
        if not client_snapshot:
            # Fallback seguro caso não haja dados de mercado para a watchlist
            return {
                "evaluation_id": f"eval-{uuid.uuid4().hex[:8]}",
                "client_id": client_id,
                "client_name": clean_client_name,
                "risk_profile": risk_profile,
                "budget": budget,
                "total_allocated": 0.0,
                "remaining_budget": budget,
                "is_valid": False,
                "summary": f"Erro: Nenhum dado de mercado localizado para a watchlist {clean_watchlist}.",
                "approved_orders": [],
                "rejected_orders": [],
                "regulatory_consents": [],
                "notifications_sent": False
            }
        raw_decision = analyze_market_with_gemini(client_snapshot, budget, risk_profile)

    # 2. Interceptação pelo Guardrail Engine Determinístico
    market_prices = {
        t: current_market_data[t].get("current_price")
        for t in current_market_data
        if current_market_data[t].get("current_price") is not None
    }
    audit = validate_portfolio_proposal(
        raw_proposal=raw_decision,
        user_budget=budget,
        risk_profile=risk_profile,
        market_prices=market_prices,
        auto_adjust_quantity=True
    )

    # 3. Geração de Desafios FIDO2 e Notificações Push
    client_config = {
        "client_id": client_id,
        "name": clean_client_name,
        "segment": segment,
        "budget": budget,
        "risk_profile": risk_profile,
        "fido_user_handle": f"user_{client_id.lower().replace('-', '_')}"
    }

    consent_records = []
    processed_challenges = set()
    approved_orders_out = []

    for audit_item in audit.approved_orders:
        order = audit_item.order
        challenge_id = None
        consent_url = None

        if order.action in ["BUY", "SELL"] and order.quantity > 0:
            order_payload = {
                "ticker": order.ticker,
                "action": order.action,
                "quantity": order.quantity,
                "unit_price": order.unit_price,
                "total_cost": order.total_cost,
                "stop_loss_price": order.stop_loss_price,
                "rationale": order.rationale,
                "client_name": clean_client_name
            }

            fido_res = create_fido_consent_challenge(client_config, order_payload)
            challenge_id = fido_res.get("challengeId", f"chal-{uuid.uuid4().hex[:8]}")
            consent_url = f"{base_url}/consent.html?challengeId={challenge_id}"
            canonical_payload = fido_res.get("canonicalPayload")
            order_hash = fido_res.get("orderHash", challenge_id)

            if send_notifications and challenge_id not in processed_challenges:
                send_push_notification(
                    client_name=clean_client_name,
                    order=order_payload,
                    consent_url=consent_url,
                    challenge_id=challenge_id,
                    device_token=device_token
                )
                processed_challenges.add(challenge_id)

            consent_records.append({
                "challengeId": challenge_id,
                "consentUrl": consent_url,
                "ticker": order.ticker,
                "action": order.action,
                "status": "PENDING"
            })

        approved_orders_out.append({
            "ticker": order.ticker,
            "action": order.action,
            "quantity": order.quantity,
            "unitPrice": order.unit_price,
            "totalCost": order.total_cost,
            "stopLossPrice": order.stop_loss_price,
            "status": audit_item.status,
            "reason": audit_item.reason,
            "rationale": order.rationale,
            "challengeId": challenge_id,
            "consentUrl": consent_url,
            "canonicalPayload": canonical_payload,
            "orderHash": order_hash,
            "ttlSeconds": 120
        })

    rejected_orders_out = [
        {
            "ticker": item.order.ticker,
            "action": item.order.action,
            "quantity": item.order.quantity,
            "unitPrice": item.order.unit_price,
            "totalCost": item.order.total_cost,
            "stopLossPrice": item.order.stop_loss_price,
            "status": item.status,
            "reason": item.reason,
            "rationale": item.order.rationale
        }
        for item in audit.rejected_orders
    ]

    log_event("GUARDRAIL_GOVERNANCE_AUDIT", {
        "client_id": client_id,
        "risk_profile": risk_profile,
        "audit_summary": audit.summary,
        "approved_orders": [o.model_dump() for o in audit.approved_orders],
        "rejected_orders": [o.model_dump() for o in audit.rejected_orders],
        "regulatory_consents": consent_records
    })

    return {
        "evaluationId": f"eval-{uuid.uuid4().hex[:8]}",
        "clientId": client_id,
        "clientName": clean_client_name,
        "riskProfile": risk_profile,
        "budget": budget,
        "totalAllocated": audit.total_allocated,
        "remainingBudget": audit.remaining_budget,
        "isValid": audit.is_valid,
        "summary": audit.summary,
        "portfolioRationale": raw_decision.get("portfolio_rationale", "") if isinstance(raw_decision, dict) else "",
        "approvedOrders": approved_orders_out,
        "rejectedOrders": rejected_orders_out,
        "regulatoryConsents": consent_records,
        "ttlSeconds": 120,
        "notificationsSent": len(consent_records) > 0
    }
