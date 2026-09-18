import pytest
from src.core.guardrail import (
    OrderItem,
    validate_single_order,
    validate_portfolio_proposal,
    compute_deterministic_quantity,
    RISK_PROFILES
)


def test_deterministic_quantity_formula():
    """Valida a fórmula matemática Q = floor(B / P)."""
    # Orçamento R$ 1.750, Preço R$ 42.35 -> Q = 41
    q = compute_deterministic_quantity(price=42.35, max_budget_for_asset=1750.0)
    assert q == 41
    assert q * 42.35 <= 1750.0


def test_buy_order_approved_within_limits():
    """Valida que uma ordem de compra dentro de 35% e com stop seguro é aprovada."""
    order = OrderItem(
        ticker="PETR4.SA",
        action="BUY",
        quantity=40,
        unit_price=35.0,  # Total: 1400.0 (28% de 5000)
        stop_loss_price=32.0,  # ~8.5% de perda (<= 12% do perfil MODERATE)
        rationale="Momento de alta com RSI saudável."
    )
    audit = validate_single_order(order, user_budget=5000.0, current_allocated=0.0, risk_profile="MODERATE")
    assert audit.is_valid is True
    assert audit.status == "APPROVED"
    assert "aprovada" in audit.reason.lower()


def test_buy_order_auto_adjusted_deterministic():
    """Valida auto-ajuste determinístico quando a IA alucina quantidade excessiva."""
    order = OrderItem(
        ticker="ITUB4.SA",
        action="BUY",
        quantity=400,  # Alucinação: 400 * 42.0 = 16.800 (orçamento total é 5.000)
        unit_price=42.0,
        stop_loss_price=39.5,
        rationale="Tese bancária forte."
    )
    # Teto Moderado (35% de 5000 = 1750) -> Q = floor(1750 / 42.0) = 41 ações
    audit = validate_single_order(
        order,
        user_budget=5000.0,
        current_allocated=0.0,
        risk_profile="MODERATE",
        auto_adjust_quantity=True
    )
    assert audit.is_valid is True
    assert audit.status == "AUTO_ADJUSTED"
    assert audit.order.quantity == 41
    assert audit.order.total_cost == 41 * 42.0
    assert audit.order.total_cost <= 1750.0


def test_risk_profiles_conservative_limit():
    """Valida que o perfil Conservador aplica teto de 20% e stop máx de 8%."""
    order = OrderItem(
        ticker="VALE3.SA",
        action="BUY",
        quantity=25,
        unit_price=60.0,  # 1500.0 (30% de 5000 -> excede 20% = 1000)
        stop_loss_price=57.0,
        rationale="Tese conservadora."
    )
    audit = validate_single_order(
        order,
        user_budget=5000.0,
        current_allocated=0.0,
        risk_profile="CONSERVATIVE",
        auto_adjust_quantity=False
    )
    assert audit.is_valid is False
    assert audit.status == "REJECTED"


def test_buy_order_rejected_missing_stop_loss():
    """Valida rejeição quando o stop-loss é ausente ou zero."""
    order = OrderItem(
        ticker="BBDC4.SA",
        action="BUY",
        quantity=50,
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
        stop_loss_price=36.0,
        rationale="Stop incoerente."
    )
    audit = validate_single_order(order, user_budget=5000.0, current_allocated=0.0)
    assert audit.is_valid is False
    assert audit.status == "REJECTED"
    assert "estritamente menor" in audit.reason.lower()


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
