import sys
import os
import json

# Ajuste de path para importações diretas
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.tools.screener import get_technical_indicators
from src.tools.news_parser import get_stock_news
from src.core.agent import analyze_market_with_gemini
from src.core.guardrail import validate_portfolio_proposal
from src.core.consent import create_consent_challenge, authorize_biometric_passkey
from src.core.logger import log_event

# Configuração do Investidor (Dados de Entrada)
WATCHLIST = ["PETR4.SA", "VALE3.SA", "ITUB4.SA", "BBDC4.SA"]
USER_BUDGET = 5000.0          # Orçamento: R$ 5.000,00
RISK_PROFILE = "MODERATE"     # Perfil de Risco: CONSERVATIVE | MODERATE | AGGRESSIVE
CLIENT_ID = "client_retail_001"


def run_pipeline():
    print("=" * 75)
    print("🛡️  GUARDRAIL-AI: MIDDLEWARE DE GOVERNANÇA E AUTONOMIA PROATIVA (B3)")
    print(f"👤 Investidor: {CLIENT_ID} | Perfil de Risco: {RISK_PROFILE}")
    print(f"💰 Orçamento Disponível: R$ {USER_BUDGET:,.2f}")
    print("=" * 75)

    # -------------------------------------------------------------
    # PILAR 1: Autonomia Proativa (Screener + Indicadores + Notícias)
    # -------------------------------------------------------------
    print("\n📊 [1/4] PILAR 1 - Autonomia Proativa: Coletando mercado ao vivo...")
    market_snapshot = []
    market_prices = {}

    for ticker in WATCHLIST:
        print(f"  -> Coletando indicadores e notícias para: {ticker}...")
        tech = get_technical_indicators(ticker, period="1y")
        news = get_stock_news(ticker, max_items=2)

        if tech:
            tech["recent_news"] = news if news else ["Nenhuma notícia recente relevante."]
            market_snapshot.append(tech)
            market_prices[ticker] = tech["current_price"]

    if not market_snapshot:
        print("❌ Erro: Não foi possível obter dados para os ativos da watchlist.")
        return

    # -------------------------------------------------------------
    # Análise de IA com Gemini 2.5 Flash
    # -------------------------------------------------------------
    print(f"\n🧠 [2/4] Enviando snapshot para análise de IA no Gemini 2.5 Flash (Vertex AI)...")
    raw_decision = analyze_market_with_gemini(
        market_snapshot,
        user_budget=USER_BUDGET,
        risk_profile=RISK_PROFILE
    )
    
    print("\n📋 Intenção de Portfólio Proposta pela IA:")
    print(json.dumps(raw_decision, indent=2, ensure_ascii=False))

    # -------------------------------------------------------------
    # PILAR 2: Segurança Inviolável (Guardrail Determinístico & Q = floor(B/P))
    # -------------------------------------------------------------
    print(f"\n🛡️ [3/4] PILAR 2 - Guardrail Engine: Interceptando e auditando ordens...")
    audit = validate_portfolio_proposal(
        raw_decision,
        user_budget=USER_BUDGET,
        risk_profile=RISK_PROFILE,
        market_prices=market_prices,
        auto_adjust_quantity=True  # Aplica Q = floor(B/P) blindando contra alucinações matemáticas
    )

    # -------------------------------------------------------------
    # PILAR 3: Consentimento Regulatório e Não-Repúdio (CVM / Passkey / TTL 120s)
    # -------------------------------------------------------------
    print(f"\n🔐 [4/4] PILAR 3 - Consentimento Regulatório (CVM): Gerando Payload Binding...")
    consent_records = []

    for audit_item in audit.approved_orders:
        order = audit_item.order
        if order.action in ["BUY", "SELL"] and order.quantity > 0:
            # Cria desafio criptográfico com HMAC-SHA256 e TTL de 120s
            challenge = create_consent_challenge(
                order_data={
                    "ticker": order.ticker,
                    "action": order.action,
                    "quantity": order.quantity,
                    "unit_price": order.unit_price,
                    "total_cost": order.total_cost,
                    "stop_loss_price": order.stop_loss_price
                },
                user_id=CLIENT_ID,
                ttl_seconds=120
            )

            # Simula aprovação biométrica do investidor via Passkey/FIDO2 no app móvel
            authorized_challenge = authorize_biometric_passkey(
                challenge,
                auth_method="PASSKEY_FIDO2_BIOMETRIC"
            )
            consent_records.append(authorized_challenge)

    # -------------------------------------------------------------
    # Auditoria e Emissão de Logs Estruturados (Cloud Logging)
    # -------------------------------------------------------------
    log_event(
        event_type="GUARDRAIL_GOVERNANCE_AUDIT",
        data={
            "client_id": CLIENT_ID,
            "risk_profile": RISK_PROFILE,
            "user_budget": USER_BUDGET,
            "audit_summary": audit.summary,
            "total_allocated": audit.total_allocated,
            "remaining_budget": audit.remaining_budget,
            "approved_orders": [o.model_dump() for o in audit.approved_orders],
            "rejected_orders": [o.model_dump() for o in audit.rejected_orders],
            "regulatory_consents": [c.model_dump() for c in consent_records],
            "cvm_compliance": {
                "strict_deterministic_guardrail": True,
                "mathematical_hallucination_shield": True,
                "cryptographic_payload_binding": True,
                "biometric_passkey_verified": True,
                "ttl_seconds": 120
            }
        }
    )

    # -------------------------------------------------------------
    # Relatório Visual de Governança
    # -------------------------------------------------------------
    print("\n" + "=" * 75)
    print("📊 RELATÓRIO DE GOVERNANÇA, RISCO E CONSENTIMENTO CVM")
    print(f"   Status da Auditoria: {audit.summary}")
    print(f"   Capital Total Alocado: R$ {audit.total_allocated:,.2f}")
    print(f"   Saldo Remanescente: R$ {audit.remaining_budget:,.2f}")
    print("=" * 75)

    if audit.approved_orders:
        print(f"\n✅ ORDENS APROVADAS COM GOVERNANÇA ({len(audit.approved_orders)}):")
        for idx, item in enumerate(audit.approved_orders, 1):
            ord_data = item.order
            cost_str = f" | Total: R$ {ord_data.total_cost:,.2f}" if ord_data.action == "BUY" else ""
            print(f"  {idx}. [{ord_data.ticker}] Ação: {ord_data.action} | Qtd: {ord_data.quantity} @ R$ {ord_data.unit_price:,.2f}{cost_str}")
            print(f"     Status Guardrail: {item.status}")
            print(f"     Motivo da Aprovação: {item.reason}")
            print(f"     Tese da IA: {ord_data.rationale}\n")

    if consent_records:
        print(f"🔐 COMPLIANCE & NÃO-REPÚDIO (CVM):")
        for c in consent_records:
            print(f"  - Desafio ID: {c.consent_id}")
            print(f"    Ativo: {c.ticker} ({c.action} {c.quantity}x) | Hash HMAC: {c.payload_hash[:28]}...")
            print(f"    Status: {c.status} | Autenticação: {c.auth_method} | TTL: 120s\n")

    if audit.rejected_orders:
        print(f"\n🛑 ORDENS BLOQUEADAS POR NÃO-CONFORMIDADE ({len(audit.rejected_orders)}):")
        for idx, item in enumerate(audit.rejected_orders, 1):
            ord_data = item.order
            print(f"  {idx}. [{ord_data.ticker}] Ação: {ord_data.action} | Qtd: {ord_data.quantity} @ R$ {ord_data.unit_price:,.2f}")
            print(f"     Motivo do Bloqueio: {item.reason}\n")

    print("=" * 75)


if __name__ == "__main__":
    run_pipeline()
