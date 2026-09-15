from typing import Literal, Optional
from pydantic import BaseModel, Field, field_validator, model_validator


class Proposal(BaseModel):
    """Modelo de dados estrito para a proposta de investimento da IA."""
    ticker: str = Field(..., description="Código do ativo na B3 (ex: PETR4.SA)")
    action: Literal["BUY", "HOLD", "SELL"] = Field(..., description="Ação sugerida")
    quantity: int = Field(default=0, ge=0, description="Quantidade de ações")
    unit_price: float = Field(default=0.0, ge=0.0, description="Preço unitário de referência")
    stop_loss_price: Optional[float] = Field(default=0.0, ge=0.0, description="Preço de stop-loss de segurança")
    rationale: str = Field(default="", description="Justificativa da recomendação")

    @property
    def total_cost(self) -> float:
        """Calcula o valor financeiro total da operação."""
        return self.quantity * self.unit_price


class GuardrailResult(BaseModel):
    """Resultado da auditoria determinística do Guardrail."""
    is_valid: bool
    status: Literal["APPROVED", "REJECTED"]
    reason: str
    proposal: Optional[Proposal] = None


def validate_proposal(raw_proposal: dict, user_budget: float = 5000.0) -> GuardrailResult:
    """
    Executa a validação determinística de risco e conformidade sobre a decisão da IA.
    """
    # 1. Validação de Esquema
    try:
        proposal = Proposal(**raw_proposal)
    except Exception as err:
        return GuardrailResult(
            is_valid=False,
            status="REJECTED",
            reason=f"Erro no formato dos dados: {str(err)}",
            proposal=None
        )

    # 2. Regra: Operações do tipo HOLD
    if proposal.action == "HOLD":
        return GuardrailResult(
            is_valid=True,
            status="APPROVED",
            reason="Ação HOLD aprovada. Nenhuma ordem de capital será enviada.",
            proposal=proposal
        )

    # 3. Regra: Orçamento Máximo
    if proposal.action == "BUY":
        if proposal.total_cost > user_budget:
            return GuardrailResult(
                is_valid=False,
                status="REJECTED",
                reason=(
                    f"Custo total (R$ {proposal.total_cost:.2f}) excede o orçamento "
                    f"disponível de R$ {user_budget:.2f}."
                ),
                proposal=proposal
            )

        # 4. Regra: Presença e Validade de Stop-Loss para Compras
        if not proposal.stop_loss_price or proposal.stop_loss_price <= 0:
            return GuardrailResult(
                is_valid=False,
                status="REJECTED",
                reason="Ordem de COMPRA rejeitada: 'stop_loss_price' é obrigatório e deve ser > 0.",
                proposal=proposal
            )

        if proposal.stop_loss_price >= proposal.unit_price:
            return GuardrailResult(
                is_valid=False,
                status="REJECTED",
                reason=(
                    f"Stop-loss inválido: R$ {proposal.stop_loss_price:.2f} deve ser estritamente "
                    f"menor que o preço de entrada (R$ {proposal.unit_price:.2f})."
                ),
                proposal=proposal
            )

        # 5. Regra: Limite Máximo de Risco (Stop Loss máximo de 15%)
        max_allowed_drop = proposal.unit_price * 0.85
        if proposal.stop_loss_price < max_allowed_drop:
            return GuardrailResult(
                is_valid=False,
                status="REJECTED",
                reason=(
                    f"Stop-loss excessivamente distante (> 15% de perda potencial). "
                    f"Entrada: R$ {proposal.unit_price:.2f}, Stop: R$ {proposal.stop_loss_price:.2f}."
                ),
                proposal=proposal
            )

    return GuardrailResult(
        is_valid=True,
        status="APPROVED",
        reason="Operação em total conformidade com os limites de risco e orçamento.",
        proposal=proposal
    )


if __name__ == "__main__":
    print("🛡️ Testando cenários de segurança do Guardrail...\n")

    cenarios = [
        {
            "nome": "Cenário 1: Compra Segura e no Orçamento",
            "dados": {
                "ticker": "PETR4.SA",
                "action": "BUY",
                "quantity": 100,
                "unit_price": 38.50,
                "stop_loss_price": 37.00,
                "rationale": "RSI sobrevendido e dividendos aprovados."
            },
            "budget": 5000.0
        },
        {
            "nome": "Cenário 2: Compra que estoura o orçamento",
            "dados": {
                "ticker": "VALE3.SA",
                "action": "BUY",
                "quantity": 100,
                "unit_price": 62.00,
                "stop_loss_price": 59.00,
                "rationale": "Repique técnico."
            },
            "budget": 5000.0
        },
        {
            "nome": "Cenário 3: Compra sem Stop-Loss (Alucinação)",
            "dados": {
                "ticker": "ITUB4.SA",
                "action": "BUY",
                "quantity": 100,
                "unit_price": 34.00,
                "stop_loss_price": 0.0,
                "rationale": "Sem stop loss definido."
            },
            "budget": 5000.0
        }
    ]

    for c in cenarios:
        res = validate_proposal(c["dados"], user_budget=c["budget"])
        icone = "✅" if res.is_valid else "❌"
        print(f"{icone} {c['nome']}")
        print(f"   Status: {res.status} | Motivo: {res.reason}\n")
