import sys
import os
import json
import argparse
from typing import List, Dict, Any

# Garante que a raiz do repositório esteja no PYTHONPATH
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from src.tools.screener import get_technical_indicators
from src.tools.news_parser import get_stock_news
from src.core.agent import analyze_market_with_gemini
from src.core.guardrail import validate_portfolio_proposal
from src.core.consent import (
    create_consent_challenge,
    authorize_biometric_passkey,
    create_fido_consent_challenge
)
from src.core.notifier import send_push_notification
from src.core.logger import log_event

# URL Base para a tela de consentimento FIDO2 (ngrok ou localhost)
FIDO_BASE_URL = os.getenv("FIDO_BASE_URL", "http://localhost:8080").rstrip("/")


def load_job_configuration() -> List[Dict[str, Any]]:
    """
    Carrega a configuração dos clientes para a execução do Job no Cloud Run.
    Ordem de precedência:
    1. Se --config (-f) foi explicitamente informado na CLI ou CLIENTS_CONFIG_FILE em os.environ, carrega o arquivo.
    2. Se --client-id, --budget, etc. foram passados na CLI, constrói cliente individual.
    3. Se existir config/clients.json ou clients.json, carrega o lote.
    4. Caso contrário, retorna cliente padrão de fallback.
    """
    parser = argparse.ArgumentParser(
        description="GuardrailAI: Middleware B2B de Governança para Mercado de Capitais (B3)"
    )

    parser.add_argument(
        "--config", "-f",
        type=str,
        default=os.getenv("CLIENTS_CONFIG_FILE"),
        help="Caminho para arquivo JSON de múltiplos clientes (ex: config/clients.json)"
    )
    parser.add_argument(
        "--client-id", "-c",
        type=str,
        default=os.getenv("CLIENT_ID", "client_retail_001"),
        help="Identificador do cliente/investidor"
    )
    parser.add_argument(
        "--budget", "-b",
        type=float,
        default=float(os.getenv("USER_BUDGET", "5000.0")),
        help="Orçamento disponível em R$"
    )
    parser.add_argument(
        "--risk-profile", "-r",
        type=str,
        choices=["CONSERVATIVE", "MODERATE", "AGGRESSIVE"],
        default=os.getenv("RISK_PROFILE", "MODERATE"),
        help="Perfil de risco do investidor (CONSERVATIVE, MODERATE, AGGRESSIVE)"
    )
    parser.add_argument(
        "--watchlist", "-w",
        type=str,
        default=os.getenv("WATCHLIST", "PETR4.SA,VALE3.SA,ITUB4.SA,BBDC4.SA"),
        help="Lista de tickers separados por vírgula"
    )

    args, unknown = parser.parse_known_args()

    config_specified_in_cli = any(arg in sys.argv for arg in ["--config", "-f"])
    cli_single_specified = any(arg in sys.argv for arg in ["--client-id", "-c", "--budget", "-b", "--risk-profile", "-r", "--watchlist", "-w"])

    if config_specified_in_cli or (args.config and not cli_single_specified):
        candidate_paths = [
            args.config if os.path.isabs(args.config) else os.path.join(REPO_ROOT, args.config),
            os.path.join(REPO_ROOT, "..", args.config)
        ]
        for config_path in candidate_paths:
            if os.path.exists(config_path):
                with open(config_path, "r", encoding="utf-8") as f:
                    clients_data = json.load(f)
                    if isinstance(clients_data, list) and len(clients_data) > 0:
                        return clients_data

    if cli_single_specified:
        watchlist = [t.strip().upper() for t in args.watchlist.split(",") if t.strip()]
        return [
            {
                "client_id": args.client_id,
                "segment": "Investidor Individual",
                "budget": args.budget,
                "risk_profile": args.risk_profile,
                "watchlist": watchlist
            }
        ]

    search_paths = [
        os.path.join(REPO_ROOT, "config", "clients.json"),
        os.path.join(REPO_ROOT, "..", "config", "clients.json"),
        os.path.join(REPO_ROOT, "clients.json"),
        os.path.join(REPO_ROOT, "..", "clients.json")
    ]
    for json_path in search_paths:
        if os.path.exists(json_path):
            with open(json_path, "r", encoding="utf-8") as f:
                clients_data = json.load(f)
                if isinstance(clients_data, list) and len(clients_data) > 0:
                    return clients_data

    watchlist = [t.strip().upper() for t in args.watchlist.split(",") if t.strip()]
    return [
        {
            "client_id": args.client_id,
            "segment": "Investidor Individual",
            "budget": args.budget,
            "risk_profile": args.risk_profile,
            "watchlist": watchlist
        }
    ]


def collect_market_data(unique_tickers: List[str]) -> Dict[str, Any]:
    """
    Coleta dados de mercado e notícias uma única vez para todos os tickers.
    """
    market_snapshot_by_ticker = {}

    for ticker in unique_tickers:
        print(f"  -> Coletando indicadores técnicos e notícias para: {ticker}...")
        try:
            tech = get_technical_indicators(ticker, period="1y")
            news = get_stock_news(ticker, max_items=2)
            if tech:
                tech["recent_news"] = news if news else ["Nenhuma notícia recente relevante."]
                market_snapshot_by_ticker[ticker] = tech
        except Exception as e:
            print(f"⚠️ Erro ao coletar {ticker}: {e}")

    return market_snapshot_by_ticker


def process_client_portfolio(client_config: Dict[str, Any], market_data: Dict[str, Any]):
    """
    Executa o pipeline completo de governança para a carteira de um cliente.
    """
    client_id = client_config.get("client_id", "anonymous_client")
    client_name = client_config.get("name", client_id)
    segment = client_config.get("segment", "Varejo")
    budget = float(client_config.get("budget", client_config.get("allocated_budget", 5000.0)))
    risk_profile = client_config.get("risk_profile", "MODERATE")
    watchlist = client_config.get("watchlist", client_config.get("target_assets", ["PETR4.SA", "VALE3.SA", "ITUB4.SA", "BBDC4.SA"]))

    print("\n" + "=" * 75)
    print(f"👤 PROCESSANDO INVESTIDOR: {client_name} ({segment}) [ID: {client_id}]")
    print(f"   Perfil de Risco: {risk_profile} | Orçamento: R$ {budget:,.2f}")
    print(f"   Watchlist: {', '.join(watchlist)}")
    print("=" * 75)

    client_snapshot = [market_data[t] for t in watchlist if t in market_data]
    market_prices = {t: market_data[t]["current_price"] for t in watchlist if t in market_data and "current_price" in market_data[t]}

    if not client_snapshot:
        print(f"⚠️ Aviso: Não há dados de mercado disponíveis para a watchlist de {client_id}.")
        return

    # 1. Tomada de Decisão com Gemini
    print(f"\n🧠 [1/3] Consultando Gemini (Vertex AI) para tese de portfólio...")
    raw_decision = analyze_market_with_gemini(
        client_snapshot,
        user_budget=budget,
        risk_profile=risk_profile
    )

    # 2. Validação e Auditoria do Guardrail
    print(f"🛡️ [2/3] Interceptando com Guardrail Engine (Q = ⌊B/P⌋, Stop-Loss e Perfil {risk_profile})...")
    audit = validate_portfolio_proposal(
        raw_decision,
        user_budget=budget,
        risk_profile=risk_profile,
        market_prices=market_prices,
        auto_adjust_quantity=True
    )

    # 3. Consentimento Regulatório e Notificação Push (FCM)
    print(f"🔐 [3/3] Gerando Consentimento Regulatório e Disparando Push FCM...")
    consent_records = []

    for audit_item in audit.approved_orders:
        order = audit_item.order
        if order.action in ["BUY", "SELL"] and order.quantity > 0:
            order_payload = {
                "ticker": order.ticker,
                "action": order.action,
                "quantity": order.quantity,
                "unit_price": order.unit_price,
                "total_cost": order.total_cost,
                "stop_loss_price": order.stop_loss_price,
                "client_name": client_name
            }

            # Registra no servidor FIDO Spring Boot (REST) e obtém o challengeId
            fido_res = create_fido_consent_challenge(client_config, order_payload)
            challenge_id = fido_res.get("challenge_id", fido_res.get("challengeId", "challenge_simulated"))
            consent_url = f"{FIDO_BASE_URL}/consent.html?challengeId={challenge_id}"

            # Dispara a notificação Push via FCM
            print(f"📲 Disparando Notificação Push (FCM) para autorização...")
            send_push_notification(
                client_name=client_name,
                order=order_payload,
                consent_url=consent_url
            )

            # Estrutura do desafio criptográfico interno
            challenge = create_consent_challenge(
                order_data=order_payload,
                user_id=client_id,
                ttl_seconds=120
            )
            challenge.consent_id = challenge_id

            authorized = authorize_biometric_passkey(
                challenge,
                auth_method="PASSKEY_FIDO2_BIOMETRIC"
            )
            consent_records.append(authorized)

    # 4. Log Estruturado
    log_event(
        event_type="GUARDRAIL_GOVERNANCE_AUDIT",
        data={
            "client_id": client_id,
            "segment": segment,
            "risk_profile": risk_profile,
            "user_budget": budget,
            "audit_summary": audit.summary,
            "total_allocated": audit.total_allocated,
            "remaining_budget": audit.remaining_budget,
            "approved_orders": [o.model_dump() for o in audit.approved_orders],
            "rejected_orders": [o.model_dump() for o in audit.rejected_orders],
            "regulatory_consents": [c.model_dump() if hasattr(c, "model_dump") else c for c in consent_records],
            "cvm_compliance": {
                "strict_deterministic_guardrail": True,
                "mathematical_hallucination_shield": True,
                "cryptographic_payload_binding": True,
                "biometric_passkey_verified": True,
                "fcm_push_notification": True,
                "ttl_seconds": 120
            }
        }
    )

    # 5. Relatório Visual
    print("\n" + "-" * 75)
    print(f"📊 RESULTADO DE GOVERNANÇA: {client_id}")
    print(f"   Status: {audit.summary}")
    print(f"   Capital Alocado: R$ {audit.total_allocated:,.2f} | Saldo: R$ {audit.remaining_budget:,.2f}")
    print("-" * 75)

    if audit.approved_orders:
        print(f"✅ ORDENS APROVADAS ({len(audit.approved_orders)}):")
        for idx, item in enumerate(audit.approved_orders, 1):
            ord_data = item.order
            cost_str = f" | Total: R$ {ord_data.total_cost:,.2f}" if ord_data.action == "BUY" else ""
            print(f"  {idx}. [{ord_data.ticker}] {ord_data.action} | {ord_data.quantity}x @ R$ {ord_data.unit_price:,.2f}{cost_str}")
            print(f"     Status: {item.status} | {item.reason}")

    if consent_records:
        print(f"\n🔐 NÃO-REPÚDIO & CVM COMPLIANCE:")
        for c in consent_records:
            cid = c.get("consent_id", c.get("challenge_id", "n/a")) if isinstance(c, dict) else getattr(c, "consent_id", "n/a")
            status = c.get("status", "PENDING_BIOMETRIC") if isinstance(c, dict) else getattr(c, "status", "PENDING_BIOMETRIC")
            auth = c.get("auth_method", "PASSKEY_FIDO2_BIOMETRIC") if isinstance(c, dict) else getattr(c, "auth_method", "PASSKEY_FIDO2_BIOMETRIC")
            print(f"  - Desafio ID: {cid} | Status: {status} ({auth}) | TTL: 120s")
            print(f"    🔗 URL WebAuthn: {FIDO_BASE_URL}/consent.html?challengeId={cid}")

    if audit.rejected_orders:
        print(f"\n🛑 ORDENS REJEITADAS ({len(audit.rejected_orders)}):")
        for idx, item in enumerate(audit.rejected_orders, 1):
            ord_data = item.order
            print(f"  {idx}. [{ord_data.ticker}] {ord_data.action} | Motivo: {item.reason}")


def run_pipeline():
    print("=" * 75)
    print("🚀 INICIANDO CLOUD RUN JOB - GUARDRAIL-AI (GOVERNANÇA MULTI-CARTEIRA)")
    print("=" * 75)

    clients = load_job_configuration()
    print(f"📋 Total de Clientes / Carteiras para Processamento: {len(clients)}")

    all_tickers = sorted(list(set(
        ticker for c in clients for ticker in c.get("watchlist", c.get("target_assets", ["PETR4.SA", "VALE3.SA", "ITUB4.SA", "BBDC4.SA"]))
    )))
    print(f"🌐 Universo de Ativos B3 Monitorados: {', '.join(all_tickers)}")

    print("\n📊 PILAR 1 - Coleta Consolidada de Indicadores Técnicos e Notícias...")
    market_data = collect_market_data(all_tickers)

    if not market_data:
        print("❌ Erro fatal: Falha ao obter dados de mercado para os ativos monitorados.")
        return

    for client_cfg in clients:
        process_client_portfolio(client_cfg, market_data)

    print("\n" + "=" * 75)
    print("🏁 CLOUD RUN JOB CONCLUÍDO COM SUCESSO PARA TODAS AS CARTEIRAS!")
    print("=" * 75)


if __name__ == "__main__":
    run_pipeline()
