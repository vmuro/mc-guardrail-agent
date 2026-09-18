import os
import json
from google import genai
from google.genai import types

PROJECT_ID = os.getenv("PROJECT_ID", "gft-brazil-bu-gcp")
LOCATION = os.getenv("LOCATION", "us-central1")
MODEL_NAME = os.getenv("MODEL_NAME", "gemini-2.5-flash")

if "GOOGLE_CLOUD_PROJECT" not in os.environ:
    os.environ["GOOGLE_CLOUD_PROJECT"] = PROJECT_ID
if "GOOGLE_CLOUD_LOCATION" not in os.environ:
    os.environ["GOOGLE_CLOUD_LOCATION"] = LOCATION

SYSTEM_INSTRUCTION = """
Você é o módulo de análise cognitiva do GuardrailAI, um middleware B2B de governança de investimentos focado no mercado de capitais brasileiro (B3).
Sua missão é analisar o snapshot consolidado de mercado (preço real, RSI_14, Médias EMA9/EMA21/SMA20/SMA200, MACD, Bandas de Bollinger e Notícias recentes) para cada ativo da watchlist e formular a tese de alocação de mercado.

Responsabilidades do Analista de IA:
1. **Identificação de Oportunidades Técnicas e Fundamentais**:
   - Tendência de alta: EMA 9 > EMA 21 e preço acima da SMA 200.
   - Sinais de exaustão/sobrecompra: RSI > 70 ou toque na Banda Superior de Bollinger (sugira HOLD ou SELL).
   - Sinais de reversão/recuperação: RSI < 35 com inflexão do MACD histograma (macd_diff > 0).
2. **Definição de Ações e Estratégia de Risco**:
   - Para cada ativo da watchlist, defina uma ação ("BUY", "HOLD" ou "SELL").
   - Para ordens "BUY", sugira o preço de entrada de referência (`unit_price`) e obrigatoriamente um preço de stop loss de segurança (`stop_loss_price`) posicionado abaixo de suportes técnicos.
   - A quantidade exata de ações será recalculada deterministicamente pelo motor de governança para blindar contra erros de cálculo.
3. **Formato Exclusivo de Resposta**:
   - Responda SEMPRE E EXCLUSIVAMENTE em formato JSON estruturado válido.

Esquema JSON esperado:
{
  "portfolio_rationale": "Resumo macro da tese e oportunidades identificadas no mercado.",
  "allocations": [
    {
      "ticker": "TICKER.SA",
      "action": "BUY" | "HOLD" | "SELL",
      "quantity": 100,
      "unit_price": 0.0,
      "stop_loss_price": 0.0,
      "rationale": "Tese fundamentada com base em técnica e notícias."
    }
  ]
}
"""


def get_client() -> genai.Client:
    """Inicializa o cliente oficial google-genai para Vertex AI."""
    return genai.Client(
        vertexai=True,
        project=PROJECT_ID,
        location=LOCATION
    )


def analyze_market_with_gemini(
    market_snapshot: list[dict],
    user_budget: float = 5000.0,
    risk_profile: str = "MODERATE"
) -> dict:
    """
    Envia o snapshot completo de mercado e parâmetros do investidor para o Gemini 2.5 Flash
    estruturar a proposta de análise e teses de investimento.
    """
    client = get_client()

    prompt = f"""
Snapshot Consolidado de Mercado (Indicadores Técnicos + Notícias):
{json.dumps(market_snapshot, indent=2, ensure_ascii=False)}

Parâmetros do Investidor:
- Orçamento Total Disponível: R$ {user_budget:.2f}
- Perfil de Risco Declarado: {risk_profile}

Analise todos os ativos da watchlist e formule a proposta no esquema JSON especificado.
"""

    config = types.GenerateContentConfig(
        system_instruction=SYSTEM_INSTRUCTION,
        temperature=0.2,
        response_mime_type="application/json"
    )

    response = client.models.generate_content(
        model=MODEL_NAME,
        contents=prompt,
        config=config
    )

    try:
        return json.loads(response.text)
    except json.JSONDecodeError:
        return {
            "portfolio_rationale": f"Falha no parsing da resposta do modelo: {response.text}",
            "allocations": [
                {
                    "ticker": item.get("ticker", "UNKNOWN"),
                    "action": "HOLD",
                    "quantity": 0,
                    "unit_price": item.get("current_price", 0.0),
                    "stop_loss_price": 0.0,
                    "rationale": "Fallback para HOLD devido a erro no processamento JSON."
                }
                for item in market_snapshot
            ]
        }


if __name__ == "__main__":
    mock_data = [
        {
            "ticker": "PETR4.SA",
            "current_price": 38.50,
            "rsi_14": 32.5,
            "ema_9": 38.20,
            "ema_21": 38.80,
            "sma_20": 39.10,
            "sma_200": 36.50,
            "macd": -0.45,
            "macd_signal": -0.50,
            "macd_diff": 0.05,
            "bollinger_high": 40.50,
            "bollinger_low": 37.80,
            "bollinger_pband": 0.25,
            "recent_news": ["Petrobras aprova novos dividendos."]
        }
    ]

    print(f"🤖 Consultando Gemini 2.5 Flash no GuardrailAI...")
    resultado = analyze_market_with_gemini(mock_data, user_budget=5000.0, risk_profile="MODERATE")
    print(json.dumps(resultado, indent=2, ensure_ascii=False))
