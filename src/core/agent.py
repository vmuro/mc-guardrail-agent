import json
from google import genai
from google.genai import types

PROJECT_ID = "gft-brazil-bu-gcp"
LOCATION = "us-central1"
MODEL_NAME = "gemini-2.5-flash"

SYSTEM_INSTRUCTION = """
Você é um analista sênior de investimentos focado em estratégias de Swing Trade na B3.
Sua missão é analisar os dados técnicos (preço, RSI_14, SMA_20) e as notícias recentes fornecidas no snapshot de mercado.

Critérios de Decisão:
1. Identifique ativos com assimetria positiva de risco/retorno (ex: RSI em região de sobrevenda/recuperação ou cruzamento positivo de médias, respaldado por notícias neutras ou positivas).
2. Se nenhuma oportunidade clara for encontrada, recomende a ação "HOLD" (Aguardar).
3. Caso recomende "BUY", defina uma quantidade condizente com o orçamento, preço unitário de referência e obrigatoriamente um preço de stop_loss_price abaixo do preço de entrada.
4. Responda SEMPRE E EXCLUSIVAMENTE em formato JSON válido, sem blocos markdown adicionais.

Esquema JSON esperado:
{
  "ticker": "TICKER.SA",
  "action": "BUY" | "HOLD" | "SELL",
  "quantity": 100,
  "unit_price": 0.0,
  "stop_loss_price": 0.0,
  "rationale": "Explicação concisa da tese baseada em técnica e notícias."
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
    Envia o snapshot de mercado e o orçamento para o Gemini tomar a decisão.
    """
    client = get_client()

    prompt = f"""
Dados de Mercado Coletados:
{json.dumps(market_snapshot, indent=2, ensure_ascii=False)}

Orçamento Máximo Disponível: R$ {user_budget:.2f}

Analise os dados e retorne a proposta de investimento estruturada em JSON.
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
            "ticker": "NENHUM",
            "action": "HOLD",
            "quantity": 0,
            "unit_price": 0.0,
            "stop_loss_price": 0.0,
            "rationale": f"Falha ao interpretar resposta: {response.text}"
        }

if __name__ == "__main__":
    mock_data = [
        {
            "ticker": "PETR4.SA",
            "current_price": 38.50,
            "rsi_14": 32.5,
            "sma_20": 39.10,
            "recent_news": ["Petrobras aprova novos dividendos e investimentos robustos."]
        },
        {
            "ticker": "VALE3.SA",
            "current_price": 62.10,
            "rsi_14": 68.0,
            "sma_20": 60.00,
            "recent_news": ["Minério de ferro recua na Ásia."]
        }
    ]

    print(f"🤖 Consultando {MODEL_NAME} via Google GenAI SDK...")
    resultado = analyze_market_with_gemini(mock_data, user_budget=4000.0)
    print("\nDecisão Estruturada da IA:")
    print(json.dumps(resultado, indent=2, ensure_ascii=False))
