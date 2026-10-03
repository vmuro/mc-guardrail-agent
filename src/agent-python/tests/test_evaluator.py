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


def test_evaluate_client_portfolio_with_hold_order():
    """Valida avaliação determinística com ordem do tipo HOLD inicial (garante que canonical_payload seja None sem UnboundLocalError)."""
    market_data = {
        "VALE3.SA": {"current_price": 60.00}
    }
    custom_orders = [
        {
            "ticker": "VALE3.SA",
            "action": "HOLD",
            "quantity": 0,
            "unit_price": 0.0,
            "stop_loss_price": 0.0,
            "rationale": "Tendência de baixa"
        }
    ]

    result = evaluate_client_portfolio(
        client_id="CLI-003",
        budget=5000.00,
        risk_profile="CONSERVATIVE",
        custom_orders=custom_orders,
        market_data=market_data,
        send_notifications=False
    )

    assert result["isValid"] is True
    assert len(result["approvedOrders"]) == 1
    hold_order = result["approvedOrders"][0]
    assert hold_order["ticker"] == "VALE3.SA"
    assert hold_order["action"] == "HOLD"
    assert hold_order["challengeId"] is None


def test_get_web_consent_base_url_cloud_run_fallback(monkeypatch):
    """Garante que URLs diretas do Cloud Run (*.run.app) revertam para o proxy Zero-Trust (localhost:8080)."""
    from src.core.evaluator import get_web_consent_base_url
    monkeypatch.delenv("CONSENT_WEB_BASE_URL", raising=False)
    monkeypatch.delenv("FIDO_WEB_BASE_URL", raising=False)

    url = get_web_consent_base_url("https://fido-consent-server-ykxwctwdea-uc.a.run.app")
    assert url == "http://localhost:8080"


def test_get_web_consent_base_url_explicit_consent_web_url(monkeypatch):
    """Garante que CONSENT_WEB_BASE_URL tenha prioridade máxima quando configurada."""
    from src.core.evaluator import get_web_consent_base_url
    monkeypatch.setenv("CONSENT_WEB_BASE_URL", "https://proxy.guardrail.ai")

    url = get_web_consent_base_url("https://fido-consent-server-ykxwctwdea-uc.a.run.app")
    assert url == "https://proxy.guardrail.ai"


def test_evaluate_client_portfolio_cloud_run_url_fallback():
    """Valida que o consentUrl gerado não aponte para *.run.app (evitando 403 Forbidden)."""
    market_data = {
        "PETR4.SA": {"current_price": 30.00}
    }
    custom_orders = [
        {
            "ticker": "PETR4.SA",
            "action": "BUY",
            "quantity": 10,
            "unit_price": 30.00,
            "stop_loss_price": 28.00,
            "rationale": "Ordem de teste Cloud Run URL"
        }
    ]

    with patch("src.core.evaluator.create_fido_consent_challenge") as mock_fido:
        mock_fido.return_value = {"challengeId": "chal-test-403"}
        with patch("src.core.evaluator.send_push_notification") as mock_push:
            mock_push.return_value = True

            result = evaluate_client_portfolio(
                client_id="CLI-CLOUD",
                budget=5000.00,
                risk_profile="MODERATE",
                custom_orders=custom_orders,
                market_data=market_data,
                fido_base_url="https://fido-consent-server-ykxwctwdea-uc.a.run.app",
                send_notifications=True
            )

            approved = result["approvedOrders"][0]
            assert "chal-test-403" in approved["consentUrl"]
            # Não deve conter .run.app, deve usar http://localhost:8080
            assert "https://fido-consent-server-ykxwctwdea-uc.a.run.app" not in approved["consentUrl"]
            assert approved["consentUrl"].startswith("http://localhost:8080/consent.html")
            
            # Garante que o push notification também recebeu a URL acessível
            mock_push.assert_called_once()
            _, kwargs = mock_push.call_args
            assert kwargs["consent_url"].startswith("http://localhost:8080/consent.html")

