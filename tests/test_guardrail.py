import pytest
from src.core.guardrail import (
    OrderItem,
    validate_single_order,
    validate_portfolio_proposal,
    MAX_CONCENTRATION_PCT,
    MAX_ALLOWED_DROP_PCT
)


def test_buy_order_approved_within_limits():
    """Valida que uma ordem de compra dentro de 35% e com stop seguro é aprovada."""
    order = OrderItem(
        ticker="PETR4.SA",
        action="BUY",
        quantity=40,
        unit_price=35.0,  # Total: 1400.0 (28% de 5000)
        stop_loss_price=32.0,  # ~8.5% de perda (<= 15%)
        rationale="Momento de alta com RSI saudável."
    )
    audit = validate_single_order(order, user_budget=5000.0, current_allocated=0.0)
    assert audit.is_valid is True
    assert audit.status == "APPROVED"
    assert "aprovada" in audit.reason.lower()


def test_buy_order_rejected_concentration_exceeded():
    """Valida rejeição quando o custo excede 35% do orçamento total."""
    order = OrderItem(
        ticker="VALE3.SA",
        action="BUY",
        quantity=50,
        unit_price=60.0,  # Total: 3000.0 (60% de 5000, limite é 1750)
        stop_loss_price=55.0,
        rationale="Tese de alta."
    )
    audit = validate_single_order(order, user_budget=5000.0, current_allocated=0.0)
    assert audit.is_valid is False
    assert audit.status == "REJECTED"
    assert "concentração" in audit.reason.lower()


def test_buy_order_rejected_cumulative_budget_exceeded():
    """Valida rejeição quando a ordem estoura o saldo restante do orçamento."""
    order = OrderItem(
        ticker="ITUB4.SA",
        action="BUY",
        quantity=30,
        unit_price=40.0,  # Total: 1200.0 (dentro dos 35%), mas resta apenas 500
        stop_loss_price=37.0,
        rationale="Tese bancária."
    )
    audit = validate_single_order(order, user_budget=5000.0, current_allocated=4600.0)
    assert audit.is_valid is False
    assert audit.status == "REJECTED"
    assert "orçamento excedido" in audit.reason.lower()


def test_buy_order_rejected_missing_stop_loss():
    """Valida rejeição quando o stop-loss é ausente ou zero."""
    order = OrderItem(
        ticker="BBDC4.SA",
        action="BUY",
        quantity=100,
        unit_price=14.0,
        stop_loss_price=0.0,
        rationale="Sem stop loss."
    )
    audit = validate_single_order(order, user_budget=5000.0, current_allocated=0.0)
    assert audit.is_valid is False
    assert audit.status == "REJECTED"
    assert "stop_loss_price" in audit.reason.lower()


def test_buy_order_rejected_stop_loss_greater_than_price():
    """Valida rejeição quando o stop-loss é maior ou igual ao preço de entrada."""
    order = OrderItem(
        ticker="PETR4.SA",
        action="BUY",
        quantity=30,
        unit_price=35.0,
        stop_loss_price=36.0,  # Stop acima da entrada
        rationale="Stop incoerente."
    )
    audit = validate_single_order(order, user_budget=5000.0, current_allocated=0.0)
    assert audit.is_valid is False
    assert audit.status == "REJECTED"
    assert "estritamente menor" in audit.reason.lower()


def test_buy_order_rejected_stop_loss_excessive_drop():
    """Valida rejeição quando o stop-loss excede o limite máximo de 15% de perda."""
    order = OrderItem(
        ticker="PETR4.SA",
        action="BUY",
        quantity=30,
        unit_price=40.0,
        stop_loss_price=30.0,  # 25% de perda (> 15%)
        rationale="Stop muito distante."
    )
    audit = validate_single_order(order, user_budget=5000.0, current_allocated=0.0)
    assert audit.is_valid is False
    assert audit.status == "REJECTED"
    assert "excessivamente distante" in audit.reason.lower()


def test_hold_order_approved():
    """Valida que ordem HOLD é aprovada sem alocação de capital."""
    order = OrderItem(
        ticker="VALE3.SA",
        action="HOLD",
        quantity=0,
        unit_price=60.0,
        rationale="Aguardando confirmação."
    )
    audit = validate_single_order(order, user_budget=5000.0, current_allocated=1000.0)
    assert audit.is_valid is True
    assert audit.status == "APPROVED"


def test_sell_order_valid_and_invalid():
    """Valida aprovação e rejeição de ordens de venda."""
    valid_sell = OrderItem(
        ticker="PETR4.SA",
        action="SELL",
        quantity=100,
        unit_price=38.0,
        rationale="Realização de lucro."
    )
    audit_valid = validate_single_order(valid_sell, user_budget=5000.0, current_allocated=0.0)
    assert audit_valid.is_valid is True
    assert audit_valid.status == "APPROVED"

    invalid_sell = OrderItem(
        ticker="PETR4.SA",
        action="SELL",
        quantity=0,
        unit_price=38.0,
        rationale="Venda sem quantidade."
    )
    audit_invalid = validate_single_order(invalid_sell, user_budget=5000.0, current_allocated=0.0)
    assert audit_invalid.is_valid is False
    assert audit_invalid.status == "REJECTED"


def test_portfolio_partial_approval():
    """Valida cenário misto com aprovação de ordens válidas e rejeição das inválidas."""
    raw_portfolio = {
        "portfolio_rationale": "Estratégia diversificada com 1 ordem válida e 1 com stop inválido.",
        "allocations": [
            {
                "ticker": "PETR4.SA",
                "action": "BUY",
                "quantity": 30,
                "unit_price": 35.0,  # 1050.0 (OK)
                "stop_loss_price": 32.5,  # OK
                "rationale": "Ordem válida."
            },
            {
                "ticker": "VALE3.SA",
                "action": "BUY",
                "quantity": 30,
                "unit_price": 60.0,  # 1800.0 (> 1750, viola 35%)
                "stop_loss_price": 55.0,
                "rationale": "Concentração excessiva."
            },
            {
                "ticker": "BBDC4.SA",
                "action": "HOLD",
                "quantity": 0,
                "unit_price": 14.0,
                "stop_loss_price": 0.0,
                "rationale": "Manter posição."
            }
        ]
    }

    result = validate_portfolio_proposal(raw_portfolio, user_budget=5000.0)
    assert result.is_valid is True
    assert result.has_rejected_orders is True
    assert len(result.approved_orders) == 2  # PETR4 (BUY) + BBDC4 (HOLD)
    assert len(result.rejected_orders) == 1  # VALE3 (Concentration)
    assert result.total_allocated == 1050.0
    assert result.remaining_budget == 3950.0
