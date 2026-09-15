import pytest
import pandas as pd
import numpy as np
from unittest.mock import patch, MagicMock
from src.tools.screener import get_technical_indicators


def test_screener_technical_indicators_calculation():
    """Valida o cálculo correto de todos os indicadores técnicos com dados simulados."""
    # Gera 220 dias de dados sintéticos para garantir cálculo de todos os indicadores (inclusive SMA 200)
    dates = pd.date_range(start="2025-01-01", periods=220, freq="B")
    np.random.seed(42)
    base_price = 30.0
    returns = np.random.normal(0.001, 0.02, 220)
    prices = base_price * np.cumprod(1 + returns)

    mock_df = pd.DataFrame({
        "Open": prices * 0.99,
        "High": prices * 1.02,
        "Low": prices * 0.98,
        "Close": prices,
        "Volume": np.random.randint(1000000, 5000000, 220)
    }, index=dates)

    with patch("yfinance.Ticker") as mock_ticker:
        mock_instance = MagicMock()
        mock_instance.history.return_value = mock_df
        mock_ticker.return_value = mock_instance

        indicators = get_technical_indicators("TEST3.SA", period="1y")

        assert indicators is not None
        assert indicators["ticker"] == "TEST3.SA"
        assert indicators["current_price"] > 0
        assert 0 <= indicators["rsi_14"] <= 100
        assert indicators["ema_9"] > 0
        assert indicators["ema_21"] > 0
        assert indicators["sma_20"] > 0
        assert indicators["sma_200"] is not None and indicators["sma_200"] > 0
        assert indicators["macd"] is not None
        assert indicators["macd_signal"] is not None
        assert indicators["macd_diff"] is not None
        assert indicators["bollinger_high"] > indicators["bollinger_low"]
        assert indicators["bollinger_pband"] is not None


def test_screener_handles_empty_or_short_history():
    """Valida retorno gracioso de None quando o ativo não tem dados suficientes."""
    empty_df = pd.DataFrame()
    with patch("yfinance.Ticker") as mock_ticker:
        mock_instance = MagicMock()
        mock_instance.history.return_value = empty_df
        mock_ticker.return_value = mock_instance

        result = get_technical_indicators("INVALID.SA")
        assert result is None
