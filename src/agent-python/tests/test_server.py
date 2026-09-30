import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient
from src.server import app

client = TestClient(app)


def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "UP", "service": "guardrail-agent-python"}


def test_evaluate_endpoint_with_custom_orders():
    payload = {
        "clientId": "CLI-TEST",
        "budget": 10000.0,
        "riskProfile": "MODERATE",
        "watchlist": ["PETR4.SA"],
        "orders": [
            {
                "ticker": "PETR4.SA",
                "action": "BUY",
                "quantity": 50,
                "unitPrice": 38.50,
                "stopLossPrice": 36.00,
                "rationale": "Teste API"
            }
        ]
    }

    mock_result = {
        "evaluationId": "eval-12345678",
        "clientId": "CLI-TEST",
        "clientName": "Investidor CLI-TEST",
        "riskProfile": "MODERATE",
        "budget": 10000.0,
        "totalAllocated": 1925.0,
        "remainingBudget": 8075.0,
        "isValid": True,
        "summary": "Aprovado",
        "approvedOrders": [],
        "rejectedOrders": [],
        "regulatoryConsents": [],
        "notificationsSent": True
    }

    with patch("src.server.evaluate_client_portfolio", return_value=mock_result) as mock_eval:
        response = client.post("/api/evaluate", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["clientId"] == "CLI-TEST"
        assert data["evaluationId"] == "eval-12345678"
        assert mock_eval.call_count == 1
