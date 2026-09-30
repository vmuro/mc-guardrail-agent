import pytest
import os
import json
from unittest.mock import patch
from src.main import load_job_configuration


def test_load_single_client_defaults():
    """Valida o carregamento dos parâmetros padrão quando nenhum arquivo de configuração é encontrado."""
    with patch("sys.argv", ["main.py"]), patch("os.path.exists", return_value=False):
        clients = load_job_configuration()
        assert len(clients) == 1
        assert clients[0]["client_id"] == "client_retail_001"
        assert clients[0]["budget"] == 5000.0
        assert clients[0]["risk_profile"] == "MODERATE"
        assert "PETR4.SA" in clients[0]["watchlist"]


def test_load_single_client_cli_args():
    """Valida a sobreposição de parâmetros via flags de linha de comando."""
    test_args = [
        "main.py",
        "--client-id", "vip_investor_99",
        "--budget", "15000.0",
        "--risk-profile", "AGGRESSIVE",
        "--watchlist", "VALE3.SA,PETR4.SA,WEGE3.SA"
    ]
    with patch("sys.argv", test_args):
        clients = load_job_configuration()
        assert len(clients) == 1
        assert clients[0]["client_id"] == "vip_investor_99"
        assert clients[0]["budget"] == 15000.0
        assert clients[0]["risk_profile"] == "AGGRESSIVE"
        assert clients[0]["watchlist"] == ["VALE3.SA", "PETR4.SA", "WEGE3.SA"]


def test_load_multi_client_json_config(tmp_path):
    """Valida o carregamento de arquivo de lote de múltiplos clientes."""
    config_file = tmp_path / "test_clients.json"
    mock_clients = [
        {
            "client_id": "c1",
            "segment": "Varejo",
            "budget": 3000.0,
            "risk_profile": "CONSERVATIVE",
            "watchlist": ["ITUB4.SA"]
        },
        {
            "client_id": "c2",
            "segment": "Wealth",
            "budget": 50000.0,
            "risk_profile": "AGGRESSIVE",
            "watchlist": ["PETR4.SA", "VALE3.SA"]
        }
    ]
    config_file.write_text(json.dumps(mock_clients), encoding="utf-8")

    test_args = ["main.py", "--config", str(config_file)]
    with patch("sys.argv", test_args):
        clients = load_job_configuration()
        assert len(clients) == 2
        assert clients[0]["client_id"] == "c1"
        assert clients[1]["client_id"] == "c2"
        assert clients[1]["budget"] == 50000.0
