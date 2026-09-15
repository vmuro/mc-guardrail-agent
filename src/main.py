import sys
import os
import json

# Ajuste de path para importações diretas
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.tools.screener import get_technical_indicators
from src.tools.news_parser import get_stock_news
from src.core.agent import analyze_market_with_gemini
from src.core.guardrail import validate_portfolio_proposal
from src.core.logger import log_event

# Tickers da B3 para monitoramento no MVP
WATCHLIST = ["PETR4.SA", "VALE3.SA", "ITUB4.SA", "BBDC4.SA"]
USER_BUDGET = 5000.0  # R$ 5.000,00


def run_pipeline():
    print("=" * 70)
    print("🚀 AGENTE PROATIVO DE INVESTIMENTOS (B3) - PORTFÓLIO & RISK GUARDRAIL")
    print(f"💰 Orçamento Total Disponível: R$ {USER_BUDGET:,.2f}")
    print(f"🎯 Limite de Concentração por Ativo: R$ {USER_BUDGET * 0.35:,.2f} (35%)")
    print("=" * 70)

    # 1. Coleta de Dados de Mercado
    print("\n📊 [1/4] Coletando indicadores técnicos avançados e notícias...")
    market_snapshot = []

    for ticker in WATCHLIST:
        print(f"  -> Processando ativo: {ticker}...")
        tech = get_technical_indicators(ticker, period="1y")
        news = get_stock_news(ticker, max_items=2)

        if tech:
            tech["recent_news"] = news if news else ["Nenhuma notícia recente relevante."]
            market_snapshot.append(tech)

    if not market_snapshot:
        print("❌ Erro crítico: Não foi possível obter dados para os ativos da watchlist.")
        return

    # 2. Tomada de Decisão com Gemini 2.5 Flash
    print("\n🧠 [2/4] Enviando snapshot consolidado para o Gemini 2.5 Flash (Vertex AI)...")
    raw_decision = analyze_market_with_gemini(market_snapshot, user_budget=USER_BUDGET)
    
    print("\n📋 Proposta de Portfólio Gerada pela IA:")
    print(json.dumps(raw_decision, indent=2, ensure_ascii=False))

    # 3. Validação Determinística de Segurança (Guardrail)
    print("\n🛡️ [3/4] Submetendo proposta à auditoria determinística do Guardrail...")
    audit = validate_portfolio_proposal(raw_decision, user_budget=USER_BUDGET)

    # 4. Auditoria e Registro de Logs Estruturados
    print("\n📝 [4/4] Registrando evento de auditoria nos logs estruturados...")
    log_event(
        event_type="PORTFOLIO_AUDIT",
        data={
            "proposal": raw_decision,
            "audit_summary": audit.summary,
            "total_allocated": audit.total_allocated,
            "remaining_budget": audit.remaining_budget,
            "approved_count": len(audit.approved_orders),
            "rejected_count": len(audit.rejected_orders),
            "approved_orders": [o.model_dump() for o in audit.approved_orders],
            "rejected_orders": [o.model_dump() for o in audit.rejected_orders],
            "user_budget": USER_BUDGET
        }
    )

    # 5. Relatório Final de Execução
    print("\n" + "=" * 70)
    print(f"📊 RELATÓRIO DE GOVERNANÇA E AUDITORIA DO GUARDRAIL")
    print(f"   Status Geral: {audit.summary}")
    print(f"   Capital Total Alocado: R$ {audit.total_allocated:,.2f}")
    print(f"   Saldo Disponível Restante: R$ {audit.remaining_budget:,.2f}")
    print("=" * 70)

    if audit.approved_orders:
        print(f"\n✅ ORDENS APROVADAS PARA EXECUÇÃO ({len(audit.approved_orders)}):")
        for idx, item in enumerate(audit.approved_orders, 1):
            ord_data = item.order
            cost_str = f" | Total: R$ {ord_data.total_cost:,.2f}" if ord_data.action == "BUY" else ""
            print(f"  {idx}. [{ord_data.ticker}] Ação: {ord_data.action} | Qtd: {ord_data.quantity} @ R$ {ord_data.unit_price:,.2f}{cost_str}")
            print(f"     Motivo Guardrail: {item.reason}")
            print(f"     Tese da IA: {ord_data.rationale}\n")

    if audit.rejected_orders:
        print(f"\n🛑 ORDENS REJEITADAS POR NÃO-CONFORMIDADE ({len(audit.rejected_orders)}):")
        for idx, item in enumerate(audit.rejected_orders, 1):
            ord_data = item.order
            print(f"  {idx}. [{ord_data.ticker}] Ação: {ord_data.action} | Qtd: {ord_data.quantity} @ R$ {ord_data.unit_price:,.2f}")
            print(f"     Motivo da Rejeição: {item.reason}\n")

    print("=" * 70)


if __name__ == "__main__":
    run_pipeline()
