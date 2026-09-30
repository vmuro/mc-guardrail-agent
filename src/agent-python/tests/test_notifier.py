import pytest
from unittest.mock import patch, MagicMock
from src.core.notifier import send_push_notification


def test_send_push_notification_simulation_when_no_firebase():
    """Valida que retorna True no modo de simulação quando Firebase não está conectado."""
    with patch("src.core.notifier.firebase_admin._apps", []):
        order = {"ticker": "PETR4.SA", "action": "BUY", "total_cost": 1500.0}
        result = send_push_notification("Investidor Teste", order, "http://localhost:8080/consent.html")
        assert result is True


def test_send_push_notification_data_only_payload():
    """Valida que o payload gerado é estritamente Data-Only (sem objeto notification)."""
    with patch("src.core.notifier.firebase_admin._apps", ["mock_app"]):
        with patch("src.core.notifier.messaging.send") as mock_send:
            mock_send.return_value = "projects/test/messages/msg_123"

            order = {
                "ticker": "PETR4.SA",
                "action": "BUY",
                "total_cost": 1540.0,
                "quantity": 40,
                "unit_price": 38.50
            }
            consent_url = "http://localhost:8080/consent.html?challengeId=chal-uuid-999"
            challenge_id = "chal-uuid-999"

            success = send_push_notification(
                client_name="Investidor Moderado",
                order=order,
                consent_url=consent_url,
                challenge_id=challenge_id
            )

            assert success is True
            assert mock_send.call_count == 1

            sent_message = mock_send.call_args[0][0]

            # REGRA CRÍTICA: Não pode conter o bloco 'notification' (para evitar duplicidade no Windows)
            assert sent_message.notification is None, "Bloco 'notification' não deve existir no padrão Data-Only"

            # REGRA CRÍTICA: Não pode conter 'webpush' com notification
            assert sent_message.webpush is None, "Webpush notification não deve existir no padrão Data-Only"

            # Dados completos no payload 'data'
            data = sent_message.data
            assert data["title"] == "🚨 GuardrailAI - Autorização de Ordem"
            assert "PETR4.SA" in data["body"]
            assert data["consentUrl"] == consent_url
            assert data["challengeId"] == challenge_id
            assert data["ticker"] == "PETR4.SA"
            assert data["action"] == "BUY"
            assert data["total_cost"] == "1540.00"
            assert data["tag"] == f"guardrail-order-{challenge_id}"


def test_send_push_notification_tag_fallback():
    """Valida geração de tag quando challenge_id não for informado."""
    with patch("src.core.notifier.firebase_admin._apps", ["mock_app"]):
        with patch("src.core.notifier.messaging.send") as mock_send:
            mock_send.return_value = "msg_456"

            order = {"ticker": "VALE3.SA", "action": "SELL", "total_cost": 3000.0}
            send_push_notification("Cliente", order, "http://localhost:8080/consent.html")

            sent_message = mock_send.call_args[0][0]
            assert sent_message.data["tag"] == "guardrail-order-VALE3.SA"
            assert sent_message.notification is None


def test_send_push_notification_error_handling():
    """Valida tratamento seguro de erro caso o envio FCM falhe."""
    with patch("src.core.notifier.firebase_admin._apps", ["mock_app"]):
        with patch("src.core.notifier.messaging.send", side_effect=Exception("FCM connection timeout")):
            order = {"ticker": "ITUB4.SA", "action": "BUY", "total_cost": 800.0}
            result = send_push_notification("Cliente", order, "http://localhost:8080/consent.html")
            assert result is False
