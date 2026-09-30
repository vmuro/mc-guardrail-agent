import pytest
from unittest.mock import patch, MagicMock
from src.core.evaluator import evaluate_client_portfolio


def test_evaluate_client_portfolio_custom_orders():
    """Valida avaliação determinística direta de ordens enviadas pelo cliente."""
    market_data = {
        "PETR4.SA": {"current_price": 38.50, "rsi": 45.0}
    }
    custom_orders = [
        {
            "ticker": "PETR4.SA",
            "action": "BUY",
            "quantity": 100,  # 100 * 38.50 = 3850 (Teto 20% de 5000 = 1000 => Auto-ajusta para 25)
            "unit_price": 38.50,
            "stop_loss_price": 36.00,
            "rationale": "Ordem de teste"
        }
    ]

    with patch("src.core.evaluator.create_fido_consent_challenge") as mock_fido:
        mock_fido.return_value = {"challengeId": "chal-mock-123"}
        with patch("src.core.evaluator.send_push_notification") as mock_push:
            mock_push.return_value = True

            result = evaluate_client_portfolio(
                client_id="CLI-001",
                budget=5000.00,
                risk_profile="CONSERVATIVE",
                watchlist=["PETR4.SA"],
                custom_orders=custom_orders,
                market_data=market_data,
                send_notifications=True
            )

            assert result["clientId"] == "CLI-001"
            assert result["riskProfile"] == "CONSERVATIVE"
            assert result["budget"] == 5000.00
            assert result["isValid"] is True
            assert len(result["approvedOrders"]) == 1

            approved = result["approvedOrders"][0]
            assert approved["ticker"] == "PETR4.SA"
            assert approved["quantity"] == 25  # 25 * 38.50 = 962.50 <= 1000
            assert approved["status"] == "AUTO_ADJUSTED"
            assert approved["challengeId"] == "chal-mock-123"
            assert "challengeId=chal-mock-123" in approved["consentUrl"]

            assert mock_fido.call_count == 1
            assert mock_push.call_count == 1


def test_evaluate_client_portfolio_rejection():
    """Valida rejeição de ordem com stop-loss inválido."""
    market_data = {
        "VALE3.SA": {"current_price": 60.00}
    }
    custom_orders = [
        {
            "ticker": "VALE3.SA",
            "action": "BUY",
            "quantity": 10,
            "unit_price": 60.00,
            "stop_loss_price": 65.00,  # Inválido para COMPRA (stop acima do preço)
            "rationale": "Stop loss errado"
        }
    ]

    result = evaluate_client_portfolio(
        client_id="CLI-002",
        budget=5000.00,
        risk_profile="CONSERVATIVE",
        custom_orders=custom_orders,
        market_data=market_data,
        send_notifications=False
    )

    assert result["isValid"] is False
    assert len(result["approvedOrders"]) == 0
    assert len(result["rejectedOrders"]) == 1
    assert "inválido" in result["rejectedOrders"][0]["reason"].lower()
