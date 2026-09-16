import pytest
import time
from src.core.consent import (
    create_consent_challenge,
    authorize_biometric_passkey,
    verify_payload_integrity,
    generate_canonical_payload,
    CONSENT_TTL_SECONDS
)


def test_create_consent_challenge_valid():
    """Valida a criação de desafio com HMAC-SHA256 e TTL de 120 segundos."""
    order_data = {
        "ticker": "PETR4.SA",
        "action": "BUY",
        "quantity": 40,
        "unit_price": 38.50,
        "total_cost": 1540.00,
        "stop_loss_price": 36.00
    }

    challenge = create_consent_challenge(order_data, user_id="user_test_123")
    assert challenge.consent_id is not None
    assert challenge.user_id == "user_test_123"
    assert challenge.ticker == "PETR4.SA"
    assert challenge.status == "PENDING"
    assert len(challenge.payload_hash) == 64  # SHA256 hex string length
    assert challenge.expires_at == challenge.created_at + CONSENT_TTL_SECONDS
    assert challenge.remaining_seconds > 110


def test_authorize_biometric_passkey_within_ttl():
    """Valida que a aprovação biométrica dentro de 120s resulta em AUTHORIZED."""
    order_data = {
        "ticker": "VALE3.SA",
        "action": "BUY",
        "quantity": 25,
        "unit_price": 60.00,
        "total_cost": 1500.00,
        "stop_loss_price": 55.00
    }

    challenge = create_consent_challenge(order_data)
    authorized = authorize_biometric_passkey(challenge, auth_method="PASSKEY_FIDO2_BIOMETRIC")

    assert authorized.status == "AUTHORIZED"
    assert authorized.auth_method == "PASSKEY_FIDO2_BIOMETRIC"
    assert authorized.authorized_at is not None


def test_authorize_biometric_passkey_expired_ttl():
    """Valida que a autorização após os 120 segundos é rejeitada com status EXPIRED."""
    order_data = {
        "ticker": "ITUB4.SA",
        "action": "BUY",
        "quantity": 30,
        "unit_price": 40.00,
        "total_cost": 1200.00,
        "stop_loss_price": 37.00
    }

    challenge = create_consent_challenge(order_data)
    # Simula 125 segundos após a criação
    expired_time = challenge.created_at + 125.0
    result = authorize_biometric_passkey(challenge, current_time=expired_time)

    assert result.status == "EXPIRED"
    assert result.auth_method is None
    assert result.authorized_at is None


def test_payload_integrity_anti_tampering():
    """Valida detecção de adulteração (anti-tampering) no payload da ordem."""
    order_data = {
        "ticker": "BBDC4.SA",
        "action": "BUY",
        "quantity": 90,
        "unit_price": 18.00,
        "total_cost": 1620.00,
        "stop_loss_price": 17.00
    }

    challenge = create_consent_challenge(order_data)
    assert verify_payload_integrity(challenge, order_data) is True

    # Modifica o preço em 1 centavo
    tampered_order = dict(order_data)
    tampered_order["unit_price"] = 18.01
    assert verify_payload_integrity(challenge, tampered_order) is False
