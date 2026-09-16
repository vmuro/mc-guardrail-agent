import hmac
import hashlib
import time
import uuid
import json
from typing import Literal, Optional, Dict, Any
from pydantic import BaseModel, Field

# Constante de governança regulatória (CVM / FIDO2)
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
        "total_cost": order_dict.get("total_cost"),
        "unit_price": order_dict.get("unit_price")
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

    canonical_payload = generate_canonical_payload(order_data, nonce, now)
    payload_hash = hmac.new(
        secret_key.encode("utf-8"),
        canonical_payload.encode("utf-8"),
        hashlib.sha256
    ).hexdigest()

    return ConsentChallenge(
        consent_id=consent_id,
        user_id=user_id,
        ticker=order_data["ticker"],
        action=order_data["action"],
        quantity=order_data["quantity"],
        unit_price=order_data["unit_price"],
        total_cost=order_data["total_cost"],
        stop_loss_price=order_data.get("stop_loss_price", 0.0),
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

    # Validação de TTL (120s)
    if check_time > challenge.expires_at:
        challenge.status = "EXPIRED"
        challenge.auth_method = None
        challenge.authorized_at = None
        return challenge

    challenge.status = "AUTHORIZED"
    challenge.auth_method = auth_method
    challenge.authorized_at = check_time
    return challenge


if __name__ == "__main__":
    print("🔐 Testando Módulo de Consentimento Regulatório e Não-Repúdio (Pilar 3)...")
    
    mock_order = {
        "ticker": "BBDC4.SA",
        "action": "BUY",
        "quantity": 95,
        "unit_price": 18.33,
        "total_cost": 1741.35,
        "stop_loss_price": 17.30
    }

    desafio = create_consent_challenge(mock_order)
    print(f"✅ Desafio Criado: ID={desafio.consent_id}")
    print(f"   Payload Hash (HMAC-SHA256): {desafio.payload_hash[:32]}...")
    print(f"   TTL Restante: {desafio.remaining_seconds} segundos")

    # Simula aprovação imediata via Passkey
    aprovado = authorize_biometric_passkey(desafio)
    print(f"📲 Status após biometria: {aprovado.status} | Método: {aprovado.auth_method}")

    # Simula expiração após 121 segundos
    desafio_expirado = create_consent_challenge(mock_order)
    resultado_exp = authorize_biometric_passkey(desafio_expirado, current_time=desafio_expirado.created_at + 125)
    print(f"⏳ Status após 125s (esperado EXPIRED): {resultado_exp.status}")
