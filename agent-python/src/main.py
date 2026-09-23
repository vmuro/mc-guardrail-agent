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
from src.core.consent import create_fido_consent_challenge
from src.core.notifier import send_push_notification
from src.core.logger import log_event

# URL Base para a tela de consentimento FIDO2 (ngrok ou localhost)
FIDO_BASE_URL = os.getenv("FIDO_BASE_URL", "http://localhost:8080").rstrip("/")

def load_job_configuration() -> List[Dict[str, Any]]:
    """
    Carrega a configuração dos clientes para a execução do Job.
    """
    parser = argparse.ArgumentParser(description="GuardrailAI: Middleware B2B de Governança para Mercado de Capitais (B3)")
    parser.add_argument("--config", "-f", type=str, default=os.getenv("CLIENTS_CONFIG_FILE"), help="Caminho para arquivo JSON de múltiplos clientes.")
    parser.add_argument("--client-id", "-c", type=str, default=os.getenv("CLIENT_ID", "client_retail_001"), help="Identificador do cliente/investidor.")
    parser.add_argument("--budget", "-b", type=float, default=float(os.getenv("USER_BUDGET", "5000.0")), help="Orçamento disponível em R$.")
    parser.add_argument("--risk-profile", "-r", type=str, choices=["CONSERVATIVE", "MODERATE", "AGGRESSIVE"], default=os.getenv("RISK_PROFILE", "MODERATE"), help="Perfil de risco do investidor.")
    parser.add_argument("--watchlist", "-w", type=str, default=os.getenv("WATCHLIST", "PETR4.SA,VALE3.SA,ITUB4.SA,BBDC4.SA"), help="Lista de tickers separados por vírgula.")
    args, _ = parser.parse_known_args()

    config_specified_in_cli = any(arg in sys.argv for arg in ["--config", "-f"])
    cli_single_specified = any(arg in sys.argv for arg in ["--client-id", "-c", "--budget", "-b", "--risk-profile", "-r", "--watchlist", "-w"])

    if config_specified_in_cli or (args.config and not cli_single_specified):
        for config_path in [args.config, os.path.join(REPO_ROOT, args.config), os.path.join(REPO_ROOT, "..", args.config)]:
            if os.path.exists(config_path):
                with open(config_path, "r", encoding="utf-8") as f:
                    return json.load(f)

    if cli_single_specified:
        return [{
            "client_id": args.client_id,
            "name": f"Investidor {args.client_id}",
            "segment": "Investidor Individual",
            "budget": args.budget,
            "risk_profile": args.risk_profile,
            "watchlist": [t.strip().upper() for t in args.watchlist.split(",")]
        }]

    for json_path in [os.path.join(REPO_ROOT, "config/clients.json"), os.path.join(REPO_ROOT, "../config/clients.json")]:
        if os.path.exists(json_path):
            with open(json_path, "r", encoding="utf-8") as f:
                return json.load(f)

    return [{
        "client_id": args.client_id, "name": f"Investidor {args.client_id}", "segment": "Investidor Individual",
        "budget": args.budget, "risk_profile": args.risk_profile,
        "watchlist": [t.strip().upper() for t in args.watchlist.split(",")]
    }]

def collect_market_data(unique_tickers: List[str]) -> Dict[str, Any]:
    market_snapshot_by_ticker = {}
    for ticker in unique_tickers:
        print(f"  -> Coletando indicadores técnicos e notícias para: {ticker}...")
        try:
            tech = get_technical_indicators(ticker, period="1y")
            if tech:
                tech["recent_news"] = get_stock_news(ticker, max_items=2) or ["Nenhuma notícia recente relevante."]
                market_snapshot_by_ticker[ticker] = tech
        except Exception as e:
            print(f"⚠️ Erro ao coletar {ticker}: {e}")
    return market_snapshot_by_ticker

def process_client_portfolio(client_config: Dict[str, Any], market_data: Dict[str, Any]):
    client_id = client_config.get("client_id", "anonymous_client")
    client_name = client_config.get("name", client_id)
    segment = client_config.get("segment", "Varejo")
    budget = float(client_config.get("budget", client_config.get("allocated_budget", 5000.0)))
    risk_profile = client_config.get("risk_profile", "MODERATE")
    raw_watchlist = client_config.get("watchlist", [])
    watchlist = [t.strip().upper() for t in raw_watchlist.split(",")] if isinstance(raw_watchlist, str) else [str(t).strip().upper() for t in raw_watchlist]

    print("\n" + "=" * 75)
    print(f"👤 PROCESSANDO INVESTIDOR: {client_name} ({segment}) [ID: {client_id}]")
    print(f"   Perfil de Risco: {risk_profile} | Orçamento: R$ {budget:,.2f}")
    print(f"   Watchlist: {', '.join(watchlist)}")
    print("=" * 75)

    client_snapshot = [market_data[t] for t in watchlist if t in market_data]
    if not client_snapshot:
        print(f"⚠️ Aviso: Não há dados de mercado para a watchlist de {client_id}.")
        return

    print("\n🧠 [1/3] Consultando Gemini (Vertex AI) para tese de portfólio...")
    raw_decision = analyze_market_with_gemini(client_snapshot, budget, risk_profile)

    print(f"🛡️ [2/3] Interceptando com Guardrail Engine...")
    audit = validate_portfolio_proposal(raw_decision, budget, risk_profile, {t: market_data[t].get("current_price") for t in market_data})

    print(f"🔐 [3/3] Gerando Consentimento Regulatório e Disparando Notificações...")
    consent_records = []
    processed_challenges = set()
    for audit_item in audit.approved_orders:
        order = audit_item.order
        if order.action in ["BUY", "SELL"] and order.quantity > 0:
            order_payload = {
                "ticker": order.ticker, "action": order.action, "quantity": order.quantity,
                "unit_price": order.unit_price, "total_cost": order.total_cost,
                "stop_loss_price": order.stop_loss_price, "rationale": order.rationale,
                "client_name": client_name
            }
            
            # Ponto único de criação e envio
            fido_res = create_fido_consent_challenge(client_config, order_payload)
            challenge_id = fido_res.get("challengeId", "challenge_simulated")
            consent_url = f"{FIDO_BASE_URL}/consent.html?challengeId={challenge_id}"
            
            # Idempotência: Garante estritamente 1 notificação por ordem/desafio
            if challenge_id not in processed_challenges:
                print(f"📲 Disparando Notificação Push (FCM Data-Only) para autorização [{challenge_id}]...")
                send_push_notification(
                    client_name=client_name,
                    order=order_payload,
                    consent_url=consent_url,
                    challenge_id=challenge_id
                )
                processed_challenges.add(challenge_id)
            
            # Adiciona o registro do desafio para o log final
            consent_records.append(fido_res)

    log_event("GUARDRAIL_GOVERNANCE_AUDIT", {
        "client_id": client_id, "risk_profile": risk_profile, "audit_summary": audit.summary,
        "approved_orders": [o.model_dump() for o in audit.approved_orders],
        "rejected_orders": [o.model_dump() for o in audit.rejected_orders],
        "regulatory_consents": consent_records
    })

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
        for rec in consent_records:
            cid = rec.get("challengeId", "n/a")
            print(f"  - Desafio ID: {cid} | Status: PENDING_BIOMETRIC | TTL: 120s")
            print(f"    🔗 URL WebAuthn: {FIDO_BASE_URL}/consent.html?challengeId={cid}")

    if audit.rejected_orders:
        print(f"\n🛑 ORDENS REJEITADAS ({len(audit.rejected_orders)}):")
        for idx, item in enumerate(audit.rejected_orders, 1):
            print(f"  {idx}. [{item.order.ticker}] {item.order.action} | Motivo: {item.reason}")

def run_pipeline():
    print("=" * 75)
    print("🚀 INICIANDO CLOUD RUN JOB - GUARDRAIL-AI")
    print("=" * 75)
    clients = load_job_configuration()
    print(f"📋 Total de Clientes para Processamento: {len(clients)}")

    all_tickers = sorted(list(set(
        t.strip().upper() for c in clients
        for t in (c.get("watchlist").split(",") if isinstance(c.get("watchlist"), str) else c.get("watchlist", []))
        if t.strip()
    )))
    print(f"🌐 Universo de Ativos B3 Monitorados: {', '.join(all_tickers)}")
    
    print("\n📊 PILAR 1 - Coleta Consolidada de Dados de Mercado...")
    market_data = collect_market_data(all_tickers)
    if not market_data:
        print("❌ Erro fatal: Falha ao obter dados de mercado.")
        return

    for client_cfg in clients:
        process_client_portfolio(client_cfg, market_data)

    print("\n" + "=" * 75)
    print("🏁 CLOUD RUN JOB CONCLUÍDO COM SUCESSO!")
    print("=" * 75)

if __name__ == "__main__":
    run_pipeline()
