from typing import Literal, Optional, List, Dict, Any
from pydantic import BaseModel, Field


# Parâmetros padrão de governança de risco
MAX_CONCENTRATION_PCT = 0.35  # Máximo de 35% do orçamento total em um único ativo
MAX_ALLOWED_DROP_PCT = 0.15   # Perda máxima tolerada no stop-loss (15%)


class OrderItem(BaseModel):
    """Modelo estrito para cada ordem individual proposta pelo agente."""
    ticker: str = Field(..., description="Código do ativo na B3 (ex: PETR4.SA)")
    action: Literal["BUY", "HOLD", "SELL"] = Field(..., description="Ação sugerida")
    quantity: int = Field(default=0, ge=0, description="Quantidade de ações")
    unit_price: float = Field(default=0.0, ge=0.0, description="Preço unitário de referência")
    stop_loss_price: Optional[float] = Field(default=0.0, ge=0.0, description="Preço de stop-loss")
    rationale: str = Field(default="", description="Justificativa da recomendação")

    @property
    def total_cost(self) -> float:
        """Calcula o valor financeiro total da operação."""
        return round(self.quantity * self.unit_price, 2)


class PortfolioProposal(BaseModel):
    """Proposta consolidada de alocação de portfólio emitida pela IA."""
    allocations: List[OrderItem] = Field(default_factory=list, description="Lista de ordens sugeridas")
    portfolio_rationale: str = Field(default="", description="Visão geral da estratégia de alocação")


class OrderAudit(BaseModel):
    """Resultado da auditoria determinística para uma ordem individual."""
    order: OrderItem
    is_valid: bool
    status: Literal["APPROVED", "REJECTED"]
    reason: str


class PortfolioAuditResult(BaseModel):
    """Resultado consolidado da auditoria do portfólio pelo Guardrail."""
    is_valid: bool
    has_rejected_orders: bool
    approved_orders: List[OrderAudit]
    rejected_orders: List[OrderAudit]
    total_allocated: float
    remaining_budget: float
    summary: str


def validate_single_order(
    order: OrderItem,
    user_budget: float,
    current_allocated: float,
    max_concentration_pct: float = MAX_CONCENTRATION_PCT,
    max_allowed_drop_pct: float = MAX_ALLOWED_DROP_PCT
) -> OrderAudit:
    """
    Aplica regras determinísticas de risco e conformidade a uma ordem individual.
    """
    max_single_asset_budget = user_budget * max_concentration_pct

    # 1. Validação de HOLD
    if order.action == "HOLD":
        return OrderAudit(
            order=order,
            is_valid=True,
            status="APPROVED",
            reason=f"Ação HOLD para {order.ticker} aprovada. Nenhuma ordem de capital enviada."
        )

    # 2. Validação de SELL
    if order.action == "SELL":
        if order.quantity <= 0:
            return OrderAudit(
                order=order,
                is_valid=False,
                status="REJECTED",
                reason=f"Ordem de VENDA rejeitada para {order.ticker}: quantidade deve ser maior que zero."
            )
        return OrderAudit(
            order=order,
            is_valid=True,
            status="APPROVED",
            reason=f"Ordem de VENDA de {order.quantity} ações de {order.ticker} aprovada para realização de lucro/proteção."
        )

    # 3. Validação de BUY
    if order.action == "BUY":
        if order.quantity <= 0 or order.unit_price <= 0:
            return OrderAudit(
                order=order,
                is_valid=False,
                status="REJECTED",
                reason=f"Ordem de COMPRA inválida para {order.ticker}: quantidade e preço unitário devem ser > 0."
            )

        # Regra A: Limite de Concentração por Ativo (máx 35% do orçamento total)
        if order.total_cost > max_single_asset_budget:
            return OrderAudit(
                order=order,
                is_valid=False,
                status="REJECTED",
                reason=(
                    f"Limite de concentração violado para {order.ticker}: custo total R$ {order.total_cost:.2f} "
                    f"excede o teto de {int(max_concentration_pct * 100)}% do orçamento "
                    f"(máx permitido: R$ {max_single_asset_budget:.2f})."
                )
            )

        # Regra B: Orçamento Cumulativo Disponível
        if (current_allocated + order.total_cost) > user_budget:
            remaining = round(user_budget - current_allocated, 2)
            return OrderAudit(
                order=order,
                is_valid=False,
                status="REJECTED",
                reason=(
                    f"Orçamento excedido para {order.ticker}: custo R$ {order.total_cost:.2f} "
                    f"ultrapassa o saldo disponível restante de R$ {remaining:.2f} (Total: R$ {user_budget:.2f})."
                )
            )

        # Regra C: Stop-Loss Obrigatório e > 0
        if not order.stop_loss_price or order.stop_loss_price <= 0:
            return OrderAudit(
                order=order,
                is_valid=False,
                status="REJECTED",
                reason=f"Ordem de COMPRA rejeitada para {order.ticker}: 'stop_loss_price' é obrigatório e deve ser > 0."
            )

        # Regra D: Stop-Loss estritamente menor que preço de entrada
        if order.stop_loss_price >= order.unit_price:
            return OrderAudit(
                order=order,
                is_valid=False,
                status="REJECTED",
                reason=(
                    f"Stop-loss inválido para {order.ticker}: R$ {order.stop_loss_price:.2f} deve ser estritamente "
                    f"menor que o preço de entrada (R$ {order.unit_price:.2f})."
                )
            )

        # Regra E: Limite Máximo de Perda no Stop Loss (máx 15%)
        min_allowed_stop = order.unit_price * (1.0 - max_allowed_drop_pct)
        if order.stop_loss_price < round(min_allowed_stop, 2):
            return OrderAudit(
                order=order,
                is_valid=False,
                status="REJECTED",
                reason=(
                    f"Stop-loss excessivamente distante para {order.ticker} (> {int(max_allowed_drop_pct * 100)}% de perda). "
                    f"Entrada: R$ {order.unit_price:.2f}, Stop: R$ {order.stop_loss_price:.2f} "
                    f"(mínimo seguro: R$ {min_allowed_stop:.2f})."
                )
            )

        # Se passou em todas as regras
        return OrderAudit(
            order=order,
            is_valid=True,
            status="APPROVED",
            reason=(
                f"Ordem de COMPRA aprovada para {order.ticker}: {order.quantity} ações a R$ {order.unit_price:.2f} "
                f"(Total: R$ {order.total_cost:.2f}, Stop: R$ {order.stop_loss_price:.2f})."
            )
        )

    return OrderAudit(
        order=order,
        is_valid=False,
        status="REJECTED",
        reason=f"Ação desconhecida: {order.action}"
    )


def validate_portfolio_proposal(
    raw_proposal: Dict[str, Any],
    user_budget: float = 5000.0,
    max_concentration_pct: float = MAX_CONCENTRATION_PCT,
    max_allowed_drop_pct: float = MAX_ALLOWED_DROP_PCT
) -> PortfolioAuditResult:
    """
    Audita a proposta de portfólio da IA, aplicando filtragem inteligente por ordem
    e regras cumulativas de orçamento e risco.
    """
    # 1. Normalização de dados (caso a IA retorne uma única ordem ou a estrutura de lista)
    if isinstance(raw_proposal, dict):
        if "allocations" not in raw_proposal and "action" in raw_proposal:
            raw_proposal = {
                "allocations": [raw_proposal],
                "portfolio_rationale": raw_proposal.get("rationale", "")
            }

    try:
        proposal = PortfolioProposal(**raw_proposal)
    except Exception as err:
        return PortfolioAuditResult(
            is_valid=False,
            has_rejected_orders=True,
            approved_orders=[],
            rejected_orders=[],
            total_allocated=0.0,
            remaining_budget=user_budget,
            summary=f"Erro fatal no esquema da proposta: {str(err)}"
        )

    if not proposal.allocations:
        return PortfolioAuditResult(
            is_valid=False,
            has_rejected_orders=True,
            approved_orders=[],
            rejected_orders=[],
            total_allocated=0.0,
            remaining_budget=user_budget,
            summary="Nenhuma ordem de investimento foi enviada na proposta."
        )

    approved_orders: List[OrderAudit] = []
    rejected_orders: List[OrderAudit] = []
    current_allocated = 0.0

    for item in proposal.allocations:
        audit = validate_single_order(
            order=item,
            user_budget=user_budget,
            current_allocated=current_allocated,
            max_concentration_pct=max_concentration_pct,
            max_allowed_drop_pct=max_allowed_drop_pct
        )

        if audit.is_valid:
            approved_orders.append(audit)
            if item.action == "BUY":
                current_allocated = round(current_allocated + item.total_cost, 2)
        else:
            rejected_orders.append(audit)

    has_approved = len(approved_orders) > 0
    has_rejected = len(rejected_orders) > 0
    remaining_budget = round(user_budget - current_allocated, 2)

    if has_approved and not has_rejected:
        summary = f"Portfólio 100% aprovado! {len(approved_orders)} ordem(ns) válidas, R$ {current_allocated:.2f} alocados."
    elif has_approved and has_rejected:
        summary = (
            f"Aprovação parcial: {len(approved_orders)} ordem(ns) aprovadas (R$ {current_allocated:.2f}) "
            f"e {len(rejected_orders)} ordem(ns) rejeitadas."
        )
    else:
        summary = f"Todas as {len(rejected_orders)} ordens da proposta foram rejeitadas pelo Guardrail."

    return PortfolioAuditResult(
        is_valid=has_approved,
        has_rejected_orders=has_rejected,
        approved_orders=approved_orders,
        rejected_orders=rejected_orders,
        total_allocated=current_allocated,
        remaining_budget=remaining_budget,
        summary=summary
    )


# Compatibilidade com API legada de chamada única
def validate_proposal(raw_proposal: dict, user_budget: float = 5000.0) -> PortfolioAuditResult:
    return validate_portfolio_proposal(raw_proposal, user_budget=user_budget)


if __name__ == "__main__":
    print("🛡️ Testando cenários do Guardrail Multi-Ativo...\n")

    cenario_teste = {
        "portfolio_rationale": "Diversificação entre commodities e setor financeiro.",
        "allocations": [
            {
                "ticker": "PETR4.SA",
                "action": "BUY",
                "quantity": 40,
                "unit_price": 38.50,
                "stop_loss_price": 36.00,
                "rationale": "RSI sobrevendido e dividendos."
            },
            {
                "ticker": "VALE3.SA",
                "action": "BUY",
                "quantity": 50,
                "unit_price": 60.00,  # 50 * 60 = 3000 -> excede 35% de 5000 (1750)
                "stop_loss_price": 55.00,
                "rationale": "Violação de concentração intencional."
            },
            {
                "ticker": "ITUB4.SA",
                "action": "BUY",
                "quantity": 30,
                "unit_price": 40.00,
                "stop_loss_price": 30.00,  # 30 < 40*0.85 (34) -> Stop loss > 15% de perda
                "rationale": "Stop loss excessivamente longo."
            },
            {
                "ticker": "BBDC4.SA",
                "action": "HOLD",
                "quantity": 0,
                "unit_price": 14.50,
                "stop_loss_price": 0.0,
                "rationale": "Aguardar melhor momento."
            }
        ]
    }

    resultado = validate_portfolio_proposal(cenario_teste, user_budget=5000.0)
    print(f"📊 Resumo: {resultado.summary}")
    print(f"💰 Alocação Total: R$ {resultado.total_allocated:.2f} | Saldo Restante: R$ {resultado.remaining_budget:.2f}\n")

    print(f"✅ Ordens Aprovadas ({len(resultado.approved_orders)}):")
    for o in resultado.approved_orders:
        print(f"  - [{o.order.ticker}] {o.order.action}: {o.reason}")

    print(f"\n❌ Ordens Rejeitadas ({len(resultado.rejected_orders)}):")
    for o in resultado.rejected_orders:
        print(f"  - [{o.order.ticker}] {o.order.action}: {o.reason}")
