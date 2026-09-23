"""
Módulo de Consentimento Regulatório, Não-Repúdio (CVM), FIDO/WebAuthn e Notificação Push (FCM).
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

from .notifier import send_push_notification

logger = logging.getLogger("GuardrailAI.Consent")

SPRING_FIDO_BASE_URL = os.getenv("SPRING_FIDO_BASE_URL", "http://localhost:8080").rstrip("/")
CONSENT_WEB_BASE_URL = os.getenv("CONSENT_WEB_BASE_URL", SPRING_FIDO_BASE_URL).rstrip("/")
CONSENT_TTL_SECONDS = 120


class ConsentChallenge(BaseModel):
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
        rem = self.expires_at - time.time()
        return max(0.0, round(rem, 1))

    @property
    def is_expired(self) -> bool:
        return time.time() > self.expires_at


def generate_canonical_payload(order_dict: Dict[str, Any], nonce: str, created_at: float) -> str:
    """Gera a representação canônica ordenada incluindo o rationale analítico."""
    canonical_data = {
        "action": order_dict.get("action"),
        "created_at": created_at,
        "nonce": nonce,
        "quantity": order_dict.get("quantity"),
        "rationale": order_dict.get("rationale", ""), 
        "stop_loss_price": order_dict.get("stop_loss_price", 0.0),
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

    return ConsentChallenge(
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


def verify_payload_integrity(
    challenge: ConsentChallenge,
    current_order_data: Dict[str, Any],
    secret_key: str = "guardrail_hmac_secret_key_cvm_2026"
) -> bool:
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


def get_gcp_id_token(audience: str) -> Optional[str]:
    """Obtém Identity Token OIDC do GCP Metadata Server para chamadas Service-to-Service."""
    try:
        url = f"http://metadata.google.internal/computeMetadata/v1/instance/service-accounts/default/identity?audience={audience}"
        headers = {"Metadata-Flavor": "Google"}
        resp = requests.get(url, headers=headers, timeout=2)
        if resp.status_code == 200:
            return resp.text.strip()
    except Exception:
        pass
    return None


def create_fido_consent_challenge(client: Dict[str, Any], order: Dict[str, Any]) -> Dict[str, Any]:
    """
    Exporta explicitamente a função esperada pelo main.py:
    1. Cria o desafio local.
    2. Registra no Spring Boot FIDO server se ativo (com suporte a Cloud Run IAM).
    3. Retorna o payload estruturado com challengeId.
    """
    client_id = client.get("client_id", "client_retail_001")
    client_name = client.get("name", client_id)
    order_data = dict(order)
    order_data["client_name"] = client_name

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
        headers = {"Content-Type": "application/json"}
        if SPRING_FIDO_BASE_URL.startswith("https://"):
            token = get_gcp_id_token(SPRING_FIDO_BASE_URL)
            if token:
                headers["Authorization"] = f"Bearer {token}"

        resp = requests.post(
            f"{SPRING_FIDO_BASE_URL}/api/consent/challenges",
            json=challenge_data,
            headers=headers,
            timeout=3
        )
        if resp.status_code not in [200, 201]:
            logger.warning(f"[CONSENT] Spring FIDO indisponível ({resp.status_code}). Operando em modo local.")
        else:
            logger.info(f"[CONSENT] Desafio {challenge.consent_id} registrado com sucesso no Spring FIDO.")
    except Exception as err:
        logger.warning(f"[CONSENT] Falha ao contatar Spring FIDO ({err}). Operando em modo local.")

    return challenge_data


def poll_for_fido_approval(challenge_id: str, timeout: int = CONSENT_TTL_SECONDS, interval: int = 2) -> Dict[str, Any]:
    start_time = time.time()
    headers = {}
    if SPRING_FIDO_BASE_URL.startswith("https://"):
        token = get_gcp_id_token(SPRING_FIDO_BASE_URL)
        if token:
            headers["Authorization"] = f"Bearer {token}"

    while time.time() - start_time < timeout:
        try:
            resp = requests.get(f"{SPRING_FIDO_BASE_URL}/api/consent/status/{challenge_id}", headers=headers, timeout=2)
            if resp.status_code == 200:
                data = resp.json()
                if data.get("status") == "APPROVED":
                    return {"approved": True, "details": data}
                elif data.get("status") == "REJECTED":
                    return {"approved": False, "reason": "USER_REJECTED"}
        except Exception:
            pass
        time.sleep(interval)
    return {"approved": False, "reason": "TTL_EXPIRED"}

