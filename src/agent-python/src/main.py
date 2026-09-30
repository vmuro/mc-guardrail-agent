import sys
import os
import json
import argparse
from typing import List, Dict, Any

# Garante que a raiz do repositório esteja no PYTHONPATH
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from src.core.evaluator import evaluate_client_portfolio, collect_market_data_for_tickers
from src.core.logger import log_event

# URL Base para a tela de consentimento (ngrok ou localhost)
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
    return collect_market_data_for_tickers(unique_tickers)


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

    res = evaluate_client_portfolio(
        client_id=client_id,
        budget=budget,
        risk_profile=risk_profile,
        watchlist=watchlist,
        client_name=client_name,
        segment=segment,
        market_data=market_data,
        fido_base_url=FIDO_BASE_URL,
        send_notifications=True
    )

    print("\n" + "-" * 75)
    print(f"📊 RESULTADO DE GOVERNANÇA: {client_id}")
    print(f"   Status: {res['summary']}")
    print(f"   Capital Alocado: R$ {res['totalAllocated']:,.2f} | Saldo: R$ {res['remainingBudget']:,.2f}")
    print("-" * 75)

    if res.get("approvedOrders"):
        print(f"✅ ORDENS APROVADAS ({len(res['approvedOrders'])}):")
        for idx, item in enumerate(res["approvedOrders"], 1):
            cost_str = f" | Total: R$ {item['totalCost']:,.2f}" if item["action"] == "BUY" else ""
            print(f"  {idx}. [{item['ticker']}] {item['action']} | {item['quantity']}x @ R$ {item['unitPrice']:,.2f}{cost_str}")
            print(f"     Status: {item['status']} | {item['reason']}")
    
    if res.get("regulatoryConsents"):
        print(f"\n🔐 NÃO-REPÚDIO & CVM COMPLIANCE:")
        for rec in res["regulatoryConsents"]:
            cid = rec.get("challengeId", "n/a")
            print(f"  - Desafio ID: {cid} | Status: PENDING_BIOMETRIC | TTL: 120s")
            print(f"    🔗 URL WebAuthn: {rec.get('consentUrl', f'{FIDO_BASE_URL}/consent.html?challengeId={cid}')}")

    if res.get("rejectedOrders"):
        print(f"\n🛑 ORDENS REJEITADAS ({len(res['rejectedOrders'])}):")
        for idx, item in enumerate(res["rejectedOrders"], 1):
            print(f"  {idx}. [{item['ticker']}] {item['action']} | Motivo: {item['reason']}")


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
