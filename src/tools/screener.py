import yfinance as yf
import pandas as pd
from ta.momentum import RSIIndicator
from ta.trend import SMAIndicator
from typing import Optional, Dict, Any


def get_technical_indicators(ticker: str, period: str = "3mo") -> Optional[Dict[str, Any]]:
    """
    Coleta dados históricos do ativo na B3 e calcula RSI (14) e SMA (20).
    """
    try:
        # Baixa histórico recente de cotações
        stock = yf.Ticker(ticker)
        df = stock.history(period=period)

        if df.empty or len(df) < 20:
            return None

        # Cálculo dos Indicadores Técnicos
        rsi_series = RSIIndicator(close=df["Close"], window=14).rsi()
        sma_series = SMAIndicator(close=df["Close"], window=20).sma_indicator()

        current_price = float(df["Close"].iloc[-1])
        rsi_14 = float(rsi_series.iloc[-1])
        sma_20 = float(sma_series.iloc[-1])

        return {
            "ticker": ticker,
            "current_price": round(current_price, 2),
            "rsi_14": round(rsi_14, 2),
            "sma_20": round(sma_20, 2)
        }
    except Exception as e:
        print(f"⚠️ Erro ao calcular indicadores para {ticker}: {e}")
        return None


if __name__ == "__main__":
    test_ticker = "PETR4.SA"
    print(f"🔍 Testando Screener para {test_ticker}...")
    dados = get_technical_indicators(test_ticker)
    print(dados)
