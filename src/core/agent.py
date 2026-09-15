import json
from google import genai
from google.genai import types

PROJECT_ID = "gft-brazil-bu-gcp"
LOCATION = "us-central1"
MODEL_NAME = "gemini-2.5-flash"

SYSTEM_INSTRUCTION = """
Você é um estrategista e analista sênior de investimentos focado em Swing Trade e gestão de portfólio na B3.
Sua missão é analisar o snapshot de mercado consolidado (preço, RSI_14, Médias EMA9/EMA21/SMA20/SMA200, MACD, Bandas de Bollinger e Notícias recentes) para cada ativo da watchlist e construir uma proposta de alocação de portfólio diversificada e prudente.

Critérios de Decisão Técnica e Estratégica:
1. **Tendência e Momentum**:
   - Tendência de alta: EMA 9 > EMA 21 e preço acima da SMA 200.
   - Reversão / Recuperação: RSI em região de sobrevenda (< 35) com inflexão positiva do MACD Histogram (macd_diff > 0) ou repique na Banda Inferior de Bollinger.
2. **Construção de Portfólio e Diversificação**:
   - Analise TODOS os ativos fornecidos no snapshot.
   - Defina uma ação ("BUY", "HOLD" ou "SELL") para cada ativo.
   - Respeite o orçamento máximo total fornecido (`user_budget`).
   - Não concentre mais de 35% do orçamento total em um único ativo (teto de alocação prudente por ativo).
3. **Gestão de Risco para Compras (BUY)**:
   - Para cada ordem de "BUY", determine a quantidade inteira de ações (`quantity`), o preço unitário de referência (`unit_price`) e obrigatoriamente um preço de stop loss de segurança (`stop_loss_price`).
   - O `stop_loss_price` deve ser estritamente menor que `unit_price`, posicionado em suportes técnicos ou médias, com perda máxima não superior a 15% do preço de entrada.
4. **Formato de Resposta**:
   - Responda SEMPRE E EXCLUSIVAMENTE em formato JSON estruturado válido, sem tags markdown adicionais.

Esquema JSON obrigatório:
{
  "portfolio_rationale": "Resumo macro da tese e distribuição de capital no portfólio.",
  "allocations": [
    {
      "ticker": "TICKER.SA",
      "action": "BUY" | "HOLD" | "SELL",
      "quantity": 100,
      "unit_price": 0.0,
      "stop_loss_price": 0.0,
      "rationale": "Explicação técnica e fundamentalista da recomendação."
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


def analyze_market_with_gemini(market_snapshot: list[dict], user_budget: float = 5000.0) -> dict:
    """
    Envia o snapshot completo de mercado e o orçamento para o Gemini 2.5 Flash
    estruturar a proposta de portfólio multi-ativo.
    """
    client = get_client()

    prompt = f"""
Snapshot Consolidado de Mercado (Indicadores Técnicos + Notícias):
{json.dumps(market_snapshot, indent=2, ensure_ascii=False)}

Orçamento Máximo Total Disponível: R$ {user_budget:.2f}
Teto Máximo de Concentração por Ativo: R$ {user_budget * 0.35:.2f} (35%)

Analise todos os ativos e retorne a proposta de alocação de portfólio no esquema JSON especificado.
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
            "portfolio_rationale": f"Falha ao interpretar resposta do modelo: {response.text}",
            "allocations": [
                {
                    "ticker": item.get("ticker", "UNKNOWN"),
                    "action": "HOLD",
                    "quantity": 0,
                    "unit_price": item.get("current_price", 0.0),
                    "stop_loss_price": 0.0,
                    "rationale": "Fallback para HOLD devido a erro no parsing do JSON retornado."
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
            "recent_news": ["Petrobras aprova novos dividendos e investimentos robustos."]
        },
        {
            "ticker": "VALE3.SA",
            "current_price": 62.10,
            "rsi_14": 55.0,
            "ema_9": 61.50,
            "ema_21": 60.80,
            "sma_20": 60.50,
            "sma_200": 58.00,
            "macd": 0.80,
            "macd_signal": 0.65,
            "macd_diff": 0.15,
            "bollinger_high": 64.00,
            "bollinger_low": 59.00,
            "bollinger_pband": 0.62,
            "recent_news": ["Demanda por minério se estabiliza na Ásia."]
        }
    ]

    print(f"🤖 Consultando {MODEL_NAME} para proposta de portfólio multi-ativo...")
    resultado = analyze_market_with_gemini(mock_data, user_budget=5000.0)
    print("\nProposta Estruturada da IA:")
    print(json.dumps(resultado, indent=2, ensure_ascii=False))
