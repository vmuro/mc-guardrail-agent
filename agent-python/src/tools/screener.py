import yfinance as yf
import pandas as pd
from ta.momentum import RSIIndicator
from ta.trend import SMAIndicator, EMAIndicator, MACD
from ta.volatility import BollingerBands
from typing import Optional, Dict, Any


def get_technical_indicators(ticker: str, period: str = "1y") -> Optional[Dict[str, Any]]:
    """
    Coleta dados históricos do ativo na B3 e calcula indicadores técnicos avançados:
    - Preço Atual
    - RSI (14 períodos)
    - Médias Móveis: EMA 9, EMA 21, SMA 20, SMA 200
    - MACD: Linha MACD, Sinal e Histograma
    - Bandas de Bollinger: Superior, Inferior e %B
    """
    try:
        # Baixa histórico recente de cotações
        stock = yf.Ticker(ticker)
        df = stock.history(period=period)

        if df.empty or len(df) < 20:
            return None

        close_series = df["Close"]
        current_price = float(close_series.iloc[-1])

        # RSI (14)
        rsi_series = RSIIndicator(close=close_series, window=14).rsi()
        rsi_14 = float(rsi_series.iloc[-1]) if not pd.isna(rsi_series.iloc[-1]) else None

        # Médias Móveis
        ema_9_series = EMAIndicator(close=close_series, window=9).ema_indicator()
        ema_21_series = EMAIndicator(close=close_series, window=21).ema_indicator()
        sma_20_series = SMAIndicator(close=close_series, window=20).sma_indicator()
        
        ema_9 = float(ema_9_series.iloc[-1]) if not pd.isna(ema_9_series.iloc[-1]) else None
        ema_21 = float(ema_21_series.iloc[-1]) if not pd.isna(ema_21_series.iloc[-1]) else None
        sma_20 = float(sma_20_series.iloc[-1]) if not pd.isna(sma_20_series.iloc[-1]) else None

        sma_200 = None
        if len(df) >= 200:
            sma_200_series = SMAIndicator(close=close_series, window=200).sma_indicator()
            sma_200_val = sma_200_series.iloc[-1]
            if not pd.isna(sma_200_val):
                sma_200 = round(float(sma_200_val), 2)

        # MACD (12, 26, 9)
        macd_indicator = MACD(close=close_series, window_slow=26, window_fast=12, window_sign=9)
        macd_val = macd_indicator.macd().iloc[-1]
        macd_signal_val = macd_indicator.macd_signal().iloc[-1]
        macd_diff_val = macd_indicator.macd_diff().iloc[-1]

        macd = round(float(macd_val), 3) if not pd.isna(macd_val) else None
        macd_signal = round(float(macd_signal_val), 3) if not pd.isna(macd_signal_val) else None
        macd_diff = round(float(macd_diff_val), 3) if not pd.isna(macd_diff_val) else None

        # Bandas de Bollinger (20 períodos, 2 desvios padrão)
        bb_indicator = BollingerBands(close=close_series, window=20, window_dev=2)
        bb_high_val = bb_indicator.bollinger_hband().iloc[-1]
        bb_low_val = bb_indicator.bollinger_lband().iloc[-1]
        bb_pband_val = bb_indicator.bollinger_pband().iloc[-1]

        bollinger_high = round(float(bb_high_val), 2) if not pd.isna(bb_high_val) else None
        bollinger_low = round(float(bb_low_val), 2) if not pd.isna(bb_low_val) else None
        bollinger_pband = round(float(bb_pband_val), 3) if not pd.isna(bb_pband_val) else None

        return {
            "ticker": ticker,
            "current_price": round(current_price, 2),
            "rsi_14": round(rsi_14, 2) if rsi_14 is not None else None,
            "ema_9": round(ema_9, 2) if ema_9 is not None else None,
            "ema_21": round(ema_21, 2) if ema_21 is not None else None,
            "sma_20": round(sma_20, 2) if sma_20 is not None else None,
            "sma_200": sma_200,
            "macd": macd,
            "macd_signal": macd_signal,
            "macd_diff": macd_diff,
            "bollinger_high": bollinger_high,
            "bollinger_low": bollinger_low,
            "bollinger_pband": bollinger_pband
        }
    except Exception as e:
        print(f"⚠️ Erro ao calcular indicadores para {ticker}: {e}")
        return None


if __name__ == "__main__":
    test_ticker = "PETR4.SA"
    print(f"🔍 Testando Screener Avançado para {test_ticker}...")
    dados = get_technical_indicators(test_ticker)
    import json
    print(json.dumps(dados, indent=2, ensure_ascii=False))
