import sys
import os
import json

# Ajuste de path para importações diretas
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.tools.screener import get_technical_indicators
from src.tools.news_parser import get_stock_news
from src.core.agent import analyze_market_with_gemini
from src.core.guardrail import validate_proposal
from src.core.logger import log_event

# Tickers da B3 para monitoramento no MVP
WATCHLIST = ["PETR4.SA", "VALE3.SA", "ITUB4.SA", "BBDC4.SA"]
USER_BUDGET = 5000.0  # R$ 5.000,00


def run_pipeline():
    print("=" * 60)
    print("🚀 INICIANDO AGENTE PROATIVO DE INVESTIMENTOS (B3)")
    print(f"💰 Orçamento Disponível: R$ {USER_BUDGET:.2f}")
    print("=" * 60)

    # 1. Coleta de Dados de Mercado
    print("\n📊 [1/4] Coletando indicadores técnicos e notícias...")
    market_snapshot = []

    for ticker in WATCHLIST:
        print(f"  -> Processando ativo: {ticker}...")
        tech = get_technical_indicators(ticker)
        news = get_stock_news(ticker, max_items=2)

        if tech:
            market_snapshot.append({
                "ticker": ticker,
                "current_price": tech["current_price"],
                "rsi_14": tech["rsi_14"],
                "sma_20": tech["sma_20"],
                "recent_news": news if news else ["Nenhuma notícia recente relevante."]
            })

    if not market_snapshot:
        print("❌ Erro: Não foi possível obter dados para os ativos da watchlist.")
        return

    # 2. Tomada de Decisão com Gemini
    print("\n🧠 [2/4] Enviando snapshot consolidado para o Gemini 2.5 Flash...")
    raw_decision = analyze_market_with_gemini(market_snapshot, user_budget=USER_BUDGET)
    
    print("\n📋 Decisão Proposta pela IA:")
    print(json.dumps(raw_decision, indent=2, ensure_ascii=False))

    # 3. Validação Determinística de Segurança (Guardrail)
    print("\n🛡️ [3/4] Submetendo proposta à auditoria do Guardrail...")
    audit = validate_proposal(raw_decision, user_budget=USER_BUDGET)

    # 4. Auditoria e Resultado
    print("\n📝 [4/4] Registrando evento de auditoria nos logs...")
    log_event(
        event_type="DECISION_AUDIT",
        data={
            "proposal": raw_decision,
            "guardrail_status": audit.status,
            "guardrail_reason": audit.reason,
            "user_budget": USER_BUDGET
        }
    )

    print("\n" + "=" * 60)
    if audit.is_valid:
        print(f"✅ OPERAÇÃO APROVADA PELO GUARDRAIL!")
        print(f"   Status: {audit.status}")
        print(f"   Detalhes: {audit.reason}")
    else:
        print(f"🛑 OPERAÇÃO REJEITADA PELO GUARDRAIL!")
        print(f"   Status: {audit.status}")
        print(f"   Motivo da Rejeição: {audit.reason}")
    print("=" * 60)


if __name__ == "__main__":
    run_pipeline()
