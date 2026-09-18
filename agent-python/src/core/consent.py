"""
Módulo de Consentimento Regulatório, Não-Repúdio (CVM), FIDO/WebAuthn e Notificação WhatsApp.
"""
import os
import time
import uuid
import hmac
import hashlib
import json
import logging
import requests
from typing import Literal, Optional, Dict, Any
from pydantic import BaseModel, Field

from .notifier import send_whatsapp_notification

logger = logging.getLogger("GuardrailAI.Consent")

# URL base do servidor Spring Boot WebAuthn
SPRING_FIDO_BASE_URL = os.getenv("SPRING_FIDO_BASE_URL", "http://localhost:8080")
CONSENT_WEB_BASE_URL = os.getenv("CONSENT_WEB_BASE_URL", "https://seu-dominio-ngrok.ngrok-free.app")
CONSENT_TTL_SECONDS = 120  # Janela estrita de 120 segundos para autorização biométrica


class ConsentChallenge(BaseModel):
    """
    Desafio de consentimento regulatório gerado para uma ordem financeira.
    Possui vinculação criptográfica inviolável (Payload Binding) e validade temporal estrita.
    """
    consent_id: str = Field(..., description="UUID único da solicitação de consentimento")
    user_id: str = Field(default="client_retail_001", description="Identificador do investidor")
    ticker: str = Field(..., description="Código do ativo na B3")
    action: Literal["BUY", "HOLD", "SELL"] = Field(..., description="Ação da ordem")
    quantity: int = Field(..., ge=0, description="Quantidade exata de ações calculada")
    unit_price: float = Field(..., ge=0.0, description="Preço unitário real de execução")
    total_cost: float = Field(..., ge=0.0, description="Custo financeiro total da operação")
    stop_loss_price: float = Field(default=0.0, ge=0.0, description="Preço de stop-loss obrigatório")
    nonce: str = Field(..., description="Nonce criptográfico aleatório anti-replay")
    created_at: float = Field(..., description="Timestamp UTC de emissão")
    expires_at: float = Field(..., description="Timestamp UTC de expiração (created_at + 120s)")
    payload_hash: str = Field(..., description="Assinatura HMAC-SHA256 do payload canônico da ordem")
    status: Literal["PENDING", "AUTHORIZED", "EXPIRED", "TAMPERED", "REJECTED_BY_USER"] = Field(
        default="PENDING",
        description="Status regulatório do consentimento"
    )
    auth_method: Optional[str] = Field(
        default=None,
        description="Método de autenticação (ex: PASSKEY_FIDO2_BIOMETRIC)"
    )
    authorized_at: Optional[float] = Field(
        default=None,
        description="Timestamp UTC em que o investidor autorizou biometricamente"
    )

    @property
    def remaining_seconds(self) -> float:
        """Retorna o tempo restante de validade em segundos."""
        rem = self.expires_at - time.time()
        return max(0.0, round(rem, 1))

    @property
    def is_expired(self) -> bool:
        """Verifica se a janela de 120 segundos foi ultrapassada."""
        return time.time() > self.expires_at


def generate_canonical_payload(order_dict: Dict[str, Any], nonce: str, created_at: float) -> str:
    """
    Gera a representação canônica ordenada dos dados da ordem para garantir não-adulteração.
    """
    canonical_data = {
        "action": order_dict.get("action"),
        "created_at": created_at,
        "nonce": nonce,
        "quantity": order_dict.get("quantity"),
        "stop_loss_price": order_dict.get("stop_loss_price"),
        "ticker": order_dict.get("ticker"),
        "total_cost": order_dict.get("total_cost", order_dict.get("total_amount", 0.0)),
        "unit_price": order_dict.get("unit_price", order_dict.get("estimated_price", 0.0))
    }
    return json.dumps(canonical_data, sort_keys=True, separators=(',', ':'))


def create_consent_challenge(
    order_data: Dict[str, Any],
    user_id: str = "client_retail_001",
    secret_key: str = "guardrail_hmac_secret_key_cvm_2026",
    ttl_seconds: int = CONSENT_TTL_SECONDS
) -> ConsentChallenge:
    """
    Cria um desafio de consentimento regulatório com Payload Binding criptográfico (HMAC-SHA256)
    e janela temporal estrita de 120 segundos para autorização biométrica (Passkey / FIDO2).
    """
    now = time.time()
    nonce = uuid.uuid4().hex
    consent_id = str(uuid.uuid4())

    unit_price = float(order_data.get("unit_price", order_data.get("estimated_price", 0.0)))
    quantity = int(order_data.get("quantity", 0))
    total_cost = float(order_data.get("total_cost", order_data.get("total_amount", round(quantity * unit_price, 2))))

    canonical_payload = generate_canonical_payload(order_data, nonce, now)
    payload_hash = hmac.new(
        secret_key.encode("utf-8"),
        canonical_payload.encode("utf-8"),
        hashlib.sha256
    ).hexdigest()

    challenge = ConsentChallenge(
        consent_id=consent_id,
        user_id=user_id,
        ticker=order_data.get("ticker", "DESCONHECIDO"),
        action=order_data.get("action", "BUY"),
        quantity=quantity,
        unit_price=unit_price,
        total_cost=total_cost,
        stop_loss_price=float(order_data.get("stop_loss_price", 0.0)),
        nonce=nonce,
        created_at=now,
        expires_at=now + ttl_seconds,
        payload_hash=payload_hash,
        status="PENDING"
    )

    # Dispara notificação via WhatsApp se houver telefone informado
    phone = order_data.get("whatsapp_phone") or order_data.get("phone")
    if phone:
        consent_url = f"{CONSENT_WEB_BASE_URL}/consent.html?challengeId={consent_id}"
        send_whatsapp_notification(
            phone=phone,
            client_name=order_data.get("client_name", user_id),
            order=order_data,
            consent_url=consent_url
        )

    return challenge


def verify_payload_integrity(
    challenge: ConsentChallenge,
    current_order_data: Dict[str, Any],
    secret_key: str = "guardrail_hmac_secret_key_cvm_2026"
) -> bool:
    """
    Verifica se os dados da ordem não foram adulterados (anti-tampering).
    """
    canonical_payload = generate_canonical_payload(current_order_data, challenge.nonce, challenge.created_at)
    expected_hash = hmac.new(
        secret_key.encode("utf-8"),
        canonical_payload.encode("utf-8"),
        hashlib.sha256
    ).hexdigest()

    return hmac.compare_digest(challenge.payload_hash, expected_hash)


def authorize_biometric_passkey(
    challenge: ConsentChallenge,
    auth_method: str = "PASSKEY_FIDO2_BIOMETRIC",
    current_time: Optional[float] = None
) -> ConsentChallenge:
    """
    Processa a autorização biométrica via Passkey/FIDO2.
    Valida estritamente se o tempo decorrido está dentro do TTL de 120 segundos.
    """
    check_time = current_time if current_time is not None else time.time()

    if check_time > challenge.expires_at:
        challenge.status = "EXPIRED"
        challenge.auth_method = None
        challenge.authorized_at = None
        return challenge

    challenge.status = "AUTHORIZED"
    challenge.auth_method = auth_method
    challenge.authorized_at = check_time
    return challenge


# Integracão FIDO WebAuthn com Spring Boot
def create_fido_consent_challenge(client: Dict[str, Any], order: Dict[str, Any]) -> Dict[str, Any]:
    """
    1. Gera o desafio de consentimento.
    2. Registra o desafio no Spring Security FIDO Server se disponível.
    3. Dispara a notificação via WhatsApp para o investidor.
    """
    client_id = client.get("client_id", "client_retail_001")
    order_data = dict(order)
    order_data["whatsapp_phone"] = client.get("whatsapp_phone")
    order_data["client_name"] = client.get("name", client_id)

    challenge = create_consent_challenge(order_data, user_id=client_id)

    challenge_data = {
        "challengeId": challenge.consent_id,
        "clientId": client_id,
        "userHandle": client.get("fido_user_handle", client_id),
        "orderHash": challenge.payload_hash,
        "canonicalPayload": generate_canonical_payload(order, challenge.nonce, challenge.created_at),
        "ttlSeconds": CONSENT_TTL_SECONDS,
        "status": "PENDING"
    }

    try:
        resp = requests.post(
            f"{SPRING_FIDO_BASE_URL}/api/consent/challenges",
            json=challenge_data,
            timeout=2
        )
        if resp.status_code not in [200, 201]:
            logger.warning(f"[CONSENT] Spring FIDO indisponível ({resp.status_code}). Operando em modo local.")
    except Exception as err:
        logger.warning(f"[CONSENT] Falha ao contatar Spring FIDO ({err}). Operando em modo local.")

    return challenge_data


def poll_for_fido_approval(challenge_id: str, timeout: int = CONSENT_TTL_SECONDS, interval: int = 2) -> Dict[str, Any]:
    """
    Aguarda a assinatura biométrica do cliente através de polling no servidor Spring.
    """
    start_time = time.time()
    logger.info(f"[CONSENT] Aguardando aprovação biométrica para Challenge: {challenge_id} (TTL: {timeout}s)...")

    while time.time() - start_time < timeout:
        try:
            resp = requests.get(f"{SPRING_FIDO_BASE_URL}/api/consent/status/{challenge_id}", timeout=2)
            if resp.status_code == 200:
                data = resp.json()
                status = data.get("status")
                if status == "APPROVED":
                    logger.info(f"✅ [CONSENT] Ordem aprovada biometricamente via FIDO! Assinatura: {data.get('signature_id')}")
                    return {"approved": True, "details": data}
                elif status == "REJECTED":
                    logger.warning(f"❌ [CONSENT] Ordem rejeitada pelo usuário.")
                    return {"approved": False, "reason": "USER_REJECTED"}
        except Exception:
            pass

        time.sleep(interval)

    logger.warning(f"⏱️ [CONSENT] Desafio {challenge_id} expirou (TTL ultrapassado).")
    return {"approved": False, "reason": "TTL_EXPIRED"}
