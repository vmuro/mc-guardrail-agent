from typing import Literal, Optional, List, Dict, Any
from pydantic import BaseModel, Field


# Definição dos Perfis de Risco do Investidor e seus parâmetros regulatórios
RISK_PROFILES = {
    "CONSERVATIVE": {
        "max_concentration_pct": 0.20,  # Máximo de 20% do orçamento por ativo
        "max_allowed_drop_pct": 0.08,   # Stop-loss máximo de 8% de perda
        "description": "Perfil Conservador: foco em preservação de capital e risco estrito."
    },
    "MODERATE": {
        "max_concentration_pct": 0.35,  # Máximo de 35% do orçamento por ativo
        "max_allowed_drop_pct": 0.12,   # Stop-loss máximo de 12% de perda
        "description": "Perfil Moderado: equilíbrio entre retorno e controle de volatilidade."
    },
    "AGGRESSIVE": {
        "max_concentration_pct": 0.50,  # Máximo de 50% do orçamento por ativo
        "max_allowed_drop_pct": 0.15,   # Stop-loss máximo de 15% de perda
        "description": "Perfil Agressivo: maior tolerância a risco e posições mais concentradas."
    }
}


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
    status: Literal["APPROVED", "REJECTED", "AUTO_ADJUSTED"]
    reason: str
    original_quantity: Optional[int] = None
    original_cost: Optional[float] = None
    applied_risk_profile: str = "MODERATE"


class PortfolioAuditResult(BaseModel):
    """Resultado consolidado da auditoria do portfólio pelo Guardrail."""
    is_valid: bool
    has_rejected_orders: bool
    approved_orders: List[OrderAudit]
    rejected_orders: List[OrderAudit]
    total_allocated: float
    remaining_budget: float
    summary: str
    risk_profile: str


def compute_deterministic_quantity(price: float, max_budget_for_asset: float) -> int:
    """
    Fórmula matemática determinística: Q = floor(B / P)
    Elimina qualquer risco de alucinação numérica do LLM.
    """
    if price <= 0 or max_budget_for_asset <= 0:
        return 0
    return int(max_budget_for_asset // price)


def validate_single_order(
    order: OrderItem,
    user_budget: float,
    current_allocated: float,
    risk_profile: str = "MODERATE",
    real_market_price: Optional[float] = None,
    auto_adjust_quantity: bool = True
) -> OrderAudit:
    """
    Aplica regras determinísticas de risco e conformidade a uma ordem individual.
    Implementa os Pilares 1 (Blindagem Matemática Q = floor(B/P)) e 2 (Segurança Inviolável).
    """
    profile_config = RISK_PROFILES.get(risk_profile, RISK_PROFILES["MODERATE"])
    max_concentration_pct = profile_config["max_concentration_pct"]
    max_allowed_drop_pct = profile_config["max_allowed_drop_pct"]

    max_single_asset_budget = round(user_budget * max_concentration_pct, 2)
    effective_remaining_budget = round(user_budget - current_allocated, 2)

    # 1. Validação de HOLD
    if order.action == "HOLD":
        return OrderAudit(
            order=order,
            is_valid=True,
            status="APPROVED",
            reason=f"Ação HOLD para {order.ticker} aprovada. Nenhuma alocação de capital.",
            applied_risk_profile=risk_profile
        )

    # 2. Validação de SELL
    if order.action == "SELL":
        if order.quantity <= 0:
            return OrderAudit(
                order=order,
                is_valid=False,
                status="REJECTED",
                reason=f"Ordem de VENDA rejeitada para {order.ticker}: quantidade deve ser maior que zero.",
                applied_risk_profile=risk_profile
            )

        # Preenche o preço real de mercado para exibição informativa
        price_to_use = real_market_price if real_market_price and real_market_price > 0 else order.unit_price
        sell_order = OrderItem(
            ticker=order.ticker,
            action="SELL",
            quantity=order.quantity,
            unit_price=price_to_use,
            stop_loss_price=0.0,
            rationale=order.rationale
        )

        estimated_total = round(order.quantity * price_to_use, 2)
        total_str = f" (Estimativa: R$ {estimated_total:,.2f})" if price_to_use > 0 else ""

        return OrderAudit(
            order=sell_order,
            is_valid=True,
            status="APPROVED",
            reason=f"Ordem de VENDA de {order.quantity} ações de {order.ticker} aprovada para realização/proteção{total_str}.",
            applied_risk_profile=risk_profile
        )

    # 3. Validação de BUY
    if order.action == "BUY":
        # Utiliza o preço real do Screener para auditoria se disponível
        price_to_use = real_market_price if real_market_price and real_market_price > 0 else order.unit_price

        if price_to_use <= 0:
            return OrderAudit(
                order=order,
                is_valid=False,
                status="REJECTED",
                reason=f"Ordem de COMPRA inválida para {order.ticker}: preço unitário inválido (R$ {price_to_use:.2f}).",
                applied_risk_profile=risk_profile
            )

        # Regra A: Stop-Loss Obrigatório e > 0
        if not order.stop_loss_price or order.stop_loss_price <= 0:
            return OrderAudit(
                order=order,
                is_valid=False,
                status="REJECTED",
                reason=f"Ordem de COMPRA rejeitada para {order.ticker}: 'stop_loss_price' é obrigatório e deve ser > 0.",
                applied_risk_profile=risk_profile
            )

        # Regra B: Stop-Loss estritamente menor que preço de entrada
        if order.stop_loss_price >= price_to_use:
            return OrderAudit(
                order=order,
                is_valid=False,
                status="REJECTED",
                reason=(
                    f"Stop-loss inválido para {order.ticker}: R$ {order.stop_loss_price:.2f} deve ser estritamente "
                    f"menor que o preço de entrada (R$ {price_to_use:.2f})."
                )
            )

        # Regra C: Limite Máximo de Perda no Stop Loss pelo Perfil de Risco
        min_allowed_stop = price_to_use * (1.0 - max_allowed_drop_pct)
        if order.stop_loss_price < round(min_allowed_stop, 2):
            return OrderAudit(
                order=order,
                is_valid=False,
                status="REJECTED",
                reason=(
                    f"Stop-loss excessivamente distante para {order.ticker} no perfil {risk_profile} "
                    f"(queda máxima permitida: {int(max_allowed_drop_pct * 100)}%). "
                    f"Entrada: R$ {price_to_use:.2f}, Stop: R$ {order.stop_loss_price:.2f} "
                    f"(mínimo seguro: R$ {min_allowed_stop:.2f})."
                ),
                applied_risk_profile=risk_profile
            )

        # Regra D: Orçamento do Ativo e Blindagem Matemática Q = floor(B / P)
        allocated_budget_for_asset = min(effective_remaining_budget, max_single_asset_budget)
        deterministic_q = compute_deterministic_quantity(price_to_use, allocated_budget_for_asset)

        if deterministic_q <= 0:
            return OrderAudit(
                order=order,
                is_valid=False,
                status="REJECTED",
                reason=(
                    f"Saldo insuficiente para comprar 1 ação de {order.ticker} a R$ {price_to_use:.2f} "
                    f"(orçamento disponível para este ativo: R$ {allocated_budget_for_asset:.2f})."
                ),
                applied_risk_profile=risk_profile
            )

        # Se a IA sugeriu quantidade maior que o permitido matematicamente (Alucinação Numérica)
        initial_cost = order.total_cost
        initial_qty = order.quantity

        if order.quantity > deterministic_q:
            if auto_adjust_quantity:
                # Auto-ajuste determinístico: corrige a alucinação da IA aplicando Q = floor(B/P)
                adjusted_order = OrderItem(
                    ticker=order.ticker,
                    action="BUY",
                    quantity=deterministic_q,
                    unit_price=price_to_use,
                    stop_loss_price=order.stop_loss_price,
                    rationale=order.rationale
                )
                return OrderAudit(
                    order=adjusted_order,
                    is_valid=True,
                    status="AUTO_ADJUSTED",
                    reason=(
                        f"Quantidade auto-ajustada deterministicamente (Q = ⌊B/P⌋): de {initial_qty} para {deterministic_q} ações "
                        f"a R$ {price_to_use:.2f} (Total: R$ {adjusted_order.total_cost:.2f}, "
                        f"teto {int(max_concentration_pct * 100)}% = R$ {max_single_asset_budget:.2f})."
                    ),
                    original_quantity=initial_qty,
                    original_cost=initial_cost,
                    applied_risk_profile=risk_profile
                )
            else:
                return OrderAudit(
                    order=order,
                    is_valid=False,
                    status="REJECTED",
                    reason=(
                        f"Limite de concentração violado para {order.ticker}: custo total R$ {initial_cost:.2f} "
                        f"excede o teto de {int(max_concentration_pct * 100)}% (máx: R$ {max_single_asset_budget:.2f})."
                    ),
                    applied_risk_profile=risk_profile
                )

        # Se a ordem da IA já veio dentro dos limites matemáticos exatos
        validated_order = OrderItem(
            ticker=order.ticker,
            action="BUY",
            quantity=order.quantity,
            unit_price=price_to_use,
            stop_loss_price=order.stop_loss_price,
            rationale=order.rationale
        )
        return OrderAudit(
            order=validated_order,
            is_valid=True,
            status="APPROVED",
            reason=(
                f"Ordem de COMPRA aprovada para {order.ticker}: {validated_order.quantity} ações a R$ {price_to_use:.2f} "
                f"(Total: R$ {validated_order.total_cost:.2f}, Stop: R$ {order.stop_loss_price:.2f})."
            ),
            applied_risk_profile=risk_profile
        )

    return OrderAudit(
        order=order,
        is_valid=False,
        status="REJECTED",
        reason=f"Ação desconhecida: {order.action}",
        applied_risk_profile=risk_profile
    )


def validate_portfolio_proposal(
    raw_proposal: Dict[str, Any],
    user_budget: float = 5000.0,
    risk_profile: str = "MODERATE",
    market_prices: Optional[Dict[str, float]] = None,
    auto_adjust_quantity: bool = True
) -> PortfolioAuditResult:
    """
    Audita a proposta de portfólio da IA, aplicando filtragem inteligente por ordem,
    regras de risco por perfil e recálculo determinístico de quantidades.
    """
    # 1. Normalização de dados
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
            summary=f"Erro fatal no esquema da proposta: {str(err)}",
            risk_profile=risk_profile
        )

    if not proposal.allocations:
        return PortfolioAuditResult(
            is_valid=False,
            has_rejected_orders=True,
            approved_orders=[],
            rejected_orders=[],
            total_allocated=0.0,
            remaining_budget=user_budget,
            summary="Nenhuma ordem de investimento foi enviada na proposta.",
            risk_profile=risk_profile
        )

    approved_orders: List[OrderAudit] = []
    rejected_orders: List[OrderAudit] = []
    current_allocated = 0.0

    for item in proposal.allocations:
        real_price = market_prices.get(item.ticker) if market_prices else None
        
        audit = validate_single_order(
            order=item,
            user_budget=user_budget,
            current_allocated=current_allocated,
            risk_profile=risk_profile,
            real_market_price=real_price,
            auto_adjust_quantity=auto_adjust_quantity
        )

        if audit.is_valid:
            approved_orders.append(audit)
            if audit.order.action == "BUY":
                current_allocated = round(current_allocated + audit.order.total_cost, 2)
        else:
            rejected_orders.append(audit)

    has_approved = len(approved_orders) > 0
    has_rejected = len(rejected_orders) > 0
    remaining_budget = round(user_budget - current_allocated, 2)

    if has_approved and not has_rejected:
        summary = f"Portfólio 100% aprovado ({risk_profile})! {len(approved_orders)} ordem(ns) válidas, R$ {current_allocated:.2f} alocados."
    elif has_approved and has_rejected:
        summary = (
            f"Aprovação parcial ({risk_profile}): {len(approved_orders)} ordem(ns) aprovadas (R$ {current_allocated:.2f}) "
            f"e {len(rejected_orders)} ordem(ns) rejeitadas."
        )
    else:
        summary = f"Todas as {len(rejected_orders)} ordens foram rejeitadas pelo Guardrail ({risk_profile})."

    return PortfolioAuditResult(
        is_valid=has_approved,
        has_rejected_orders=has_rejected,
        approved_orders=approved_orders,
        rejected_orders=rejected_orders,
        total_allocated=current_allocated,
        remaining_budget=remaining_budget,
        summary=summary,
        risk_profile=risk_profile
    )


# Compatibilidade com API legada de chamada única
def validate_proposal(raw_proposal: dict, user_budget: float = 5000.0) -> PortfolioAuditResult:
    return validate_portfolio_proposal(raw_proposal, user_budget=user_budget)


if __name__ == "__main__":
    print("🛡️ Testando Guardrail com Q = floor(B/P) e Perfis de Risco...\n")

    cenario_alucinacao = {
        "portfolio_rationale": "Teste de IA alucinando quantidade 500x maior.",
        "allocations": [
            {
                "ticker": "ITUB4.SA",
                "action": "BUY",
                "quantity": 500,  # IA alucinou 500 ações = R$ 21.000 (estoura orçamento de 5k)
                "unit_price": 42.00,
                "stop_loss_price": 39.50,
                "rationale": "Alta do setor financeiro."
            }
        ]
    }

    resultado = validate_portfolio_proposal(cenario_alucinacao, user_budget=5000.0, risk_profile="MODERATE")
    print(f"📊 Resumo: {resultado.summary}")
    for o in resultado.approved_orders:
        print(f"  ✅ [{o.order.ticker}] Status: {o.status} | Qtd Final: {o.order.quantity} | Custo: R$ {o.order.total_cost:.2f}")
        print(f"     Detalhes: {o.reason}")
