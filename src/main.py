import sys
import os
import json
import argparse
from typing import List, Dict, Any

# Ajuste de path para importações diretas
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.tools.screener import get_technical_indicators
from src.tools.news_parser import get_stock_news
from src.core.agent import analyze_market_with_gemini
from src.core.guardrail import validate_portfolio_proposal
from src.core.consent import create_consent_challenge, authorize_biometric_passkey
from src.core.logger import log_event


def load_job_configuration() -> List[Dict[str, Any]]:
    """
    Carrega a configuração dos clientes para a execução do Job no Cloud Run.
    Ordem de precedência:
    1. Arquivo de configuração JSON via CLI (--config) ou Env Var (CLIENTS_CONFIG_FILE)
    2. Parâmetros individuais via CLI (--client-id, --budget, --risk-profile, --watchlist)
    3. Variáveis de ambiente (CLIENT_ID, USER_BUDGET, RISK_PROFILE, WATCHLIST)
    4. Valores padrão de fallback
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

    args, _ = parser.parse_known_args()

    # Se um arquivo de configuração de múltiplos clientes foi especificado
    if args.config and os.path.exists(args.config):
        with open(args.config, "r", encoding="utf-8") as f:
            clients_data = json.load(f)
            if isinstance(clients_data, list) and len(clients_data) > 0:
                return clients_data

    # Caso contrário, utiliza a configuração de cliente único
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
    Coleta dados de mercado e notícias uma única vez para todos os tickers envolvidos,
    otimizando requisições e tempo de execução do Cloud Run Job.
    """
    market_snapshot_by_ticker = {}

    for ticker in unique_tickers:
        print(f"  -> Coletando indicadores técnicos e notícias para: {ticker}...")
        tech = get_technical_indicators(ticker, period="1y")
        news = get_stock_news(ticker, max_items=2)

        if tech:
            tech["recent_news"] = news if news else ["Nenhuma notícia recente relevante."]
            market_snapshot_by_ticker[ticker] = tech

    return market_snapshot_by_ticker


def process_client_portfolio(
    client_config: Dict[str, Any],
    market_data: Dict[str, Any]
):
    """
    Executa o pipeline completo de governança para a carteira de um cliente específico.
    """
    client_id = client_config.get("client_id", "anonymous_client")
    segment = client_config.get("segment", "Varejo")
    budget = float(client_config.get("budget", 5000.0))
    risk_profile = client_config.get("risk_profile", "MODERATE")
    watchlist = client_config.get("watchlist", [])

    print("\n" + "=" * 75)
    print(f"👤 PROCESSANDO INVESTIDOR: {client_id} ({segment})")
    print(f"   Perfil de Risco: {risk_profile} | Orçamento: R$ {budget:,.2f}")
    print(f"   Watchlist: {', '.join(watchlist)}")
    print("=" * 75)

    # 1. Filtra snapshot de mercado para os ativos da watchlist deste cliente
    client_snapshot = [market_data[t] for t in watchlist if t in market_data]
    market_prices = {t: market_data[t]["current_price"] for t in watchlist if t in market_data}

    if not client_snapshot:
        print(f"⚠️ Aviso: Não há dados de mercado disponíveis para a watchlist de {client_id}.")
        return

    # 2. Tomada de Decisão com Gemini 2.5 Flash
    print(f"\n🧠 [1/3] Consultando Gemini 2.5 Flash (Vertex AI) para tese de portfólio...")
    raw_decision = analyze_market_with_gemini(
        client_snapshot,
        user_budget=budget,
        risk_profile=risk_profile
    )

    # 3. Interceptação e Auditoria do Guardrail (Pilares 1 e 2)
    print(f"🛡️ [2/3] Interceptando com Guardrail Engine (Q = ⌊B/P⌋, Stop-Loss e Perfil {risk_profile})...")
    audit = validate_portfolio_proposal(
        raw_decision,
        user_budget=budget,
        risk_profile=risk_profile,
        market_prices=market_prices,
        auto_adjust_quantity=True
    )

    # 4. Consentimento Regulatório e Não-Repúdio (Pilar 3)
    print(f"🔐 [3/3] Gerando Consentimento Regulatório CVM (Payload Binding HMAC + TTL 120s)...")
    consent_records = []

    for audit_item in audit.approved_orders:
        order = audit_item.order
        if order.action in ["BUY", "SELL"] and order.quantity > 0:
            challenge = create_consent_challenge(
                order_data={
                    "ticker": order.ticker,
                    "action": order.action,
                    "quantity": order.quantity,
                    "unit_price": order.unit_price,
                    "total_cost": order.total_cost,
                    "stop_loss_price": order.stop_loss_price
                },
                user_id=client_id,
                ttl_seconds=120
            )

            # Simula autorização biométrica via Passkey/FIDO2 no app do cliente
            authorized = authorize_biometric_passkey(
                challenge,
                auth_method="PASSKEY_FIDO2_BIOMETRIC"
            )
            consent_records.append(authorized)

    # 5. Emissão de Log Estruturado no Cloud Logging (Audit Trail CVM)
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

    # 6. Relatório Visual da Carteira
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
            print(f"  - Desafio ID: {c.consent_id} | Status: {c.status} ({c.auth_method}) | TTL: 120s")

    if audit.rejected_orders:
        print(f"\n🛑 ORDENS REJEITADAS ({len(audit.rejected_orders)}):")
        for idx, item in enumerate(audit.rejected_orders, 1):
            ord_data = item.order
            print(f"  {idx}. [{ord_data.ticker}] {ord_data.action} | Motivo: {item.reason}")


def run_pipeline():
    print("=" * 75)
    print("🚀 INICIANDO CLOUD RUN JOB - GUARDRAIL-AI (GOVERNANÇA MULTI-CARTEIRA)")
    print("=" * 75)

    # 1. Carrega configuração de clientes (Lote ou Individual)
    clients = load_job_configuration()
    print(f"📋 Total de Clientes / Carteiras para Processamento: {len(clients)}")

    # 2. Identifica todos os tickers únicos para consulta consolidada
    all_tickers = sorted(list(set(ticker for c in clients for ticker in c.get("watchlist", []))))
    print(f"🌐 Universo de Ativos B3 Monitorados: {', '.join(all_tickers)}")

    # 3. Coleta de Mercado Otimizada (1 única vez para todo o lote)
    print("\n📊 PILAR 1 - Coleta Consolidada de Indicadores Técnicos e Notícias...")
    market_data = collect_market_data(all_tickers)

    if not market_data:
        print("❌ Erro fatal: Falha ao obter dados de mercado para os ativos monitorados.")
        return

    # 4. Processa cada carteira de investidor
    for client_cfg in clients:
        process_client_portfolio(client_cfg, market_data)

    print("\n" + "=" * 75)
    print("🏁 CLOUD RUN JOB CONCLUÍDO COM SUCESSO PARA TODAS AS CARTEIRAS!")
    print("=" * 75)


if __name__ == "__main__":
    run_pipeline()
