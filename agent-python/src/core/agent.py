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
Você é o módulo de análise cognitiva e governança algorítmica do GuardrailAI (B3).
Sua missão é classificar deterministicamente os ativos da watchlist aplicando a seguinte ÁRVORE DE DECISÃO TÉCNICA ESTATÍSTICA:

1. REGRAS DE CLASSIFICAÇÃO DE AÇÃO (ESTRITAS):
   - AÇÃO "BUY":
     * Critério obrigatório: (EMA_9 > EMA_21) E (preço > SMA_200) E (RSI_14 entre 35.0 e 70.0).
     * Preço de Entrada (unit_price): exatamente o `current_price` do snapshot.
     * Preço de Stop Loss (stop_loss_price):
       - CONSERVATIVE: exatamente min(EMA_21, SMA_20) ou (current_price * 0.95), respeitando queda máx de 8%.
       - MODERATE: (current_price * 0.90), respeitando queda máx de 12%.
       - AGGRESSIVE: (current_price * 0.86), respeitando queda máx de 15%.
   - AÇÃO "SELL":
     * Critério obrigatório: Ativo em posse com quebra estrutural severa OU toque na Banda Superior com RSI > 75.
     * unit_price: exatamente o `current_price`.
     * stop_loss_price: 0.0.
   - AÇÃO "HOLD":
     * Critério obrigatório: Ativo com (EMA_9 < EMA_21), ou (preço < SMA_200), ou MACD negativo (macd_diff < 0) sem reversão confirmada.
     * Para ativos em tendência de baixa sem compra autorizada, a recomendação padrão de segurança é SEMPRE "HOLD" (não alocar capital).
     * unit_price: 0.0, stop_loss_price: 0.0, quantity: 0.

2. QUANTIDADE:
   - Defina sempre `quantity: 100` como base para BUY. A quantidade final será recalculada matematicamente pelo Guardrail Engine (Q = ⌊B/P⌋).

3. FORMATO EXCLUSIVO DE SAÍDA:
   - Responda SEMPRE E EXCLUSIVAMENTE em formato JSON com o seguinte esquema:

{
  "portfolio_rationale": "Resumo macro da tese e oportunidades identificadas no mercado.",
  "allocations": [
    {
      "ticker": "TICKER.SA",
      "action": "BUY" | "HOLD" | "SELL",
      "quantity": 100,
      "unit_price": 0.0,
      "stop_loss_price": 0.0,
      "rationale": "Tese técnica objetiva citando valores exatos de EMA9, EMA21, SMA200, RSI e MACD."
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
    Envia o snapshot completo de mercado e parâmetros do investidor com
    temperatura 0.0 para garantir consistência e reprodutibilidade total.
    """
    client = get_client()

    prompt = f"""
Snapshot Consolidado de Mercado:
{json.dumps(market_snapshot, indent=2, ensure_ascii=False)}

Parâmetros do Investidor:
- Orçamento Disponível: R$ {user_budget:.2f}
- Perfil de Risco Declarado: {risk_profile}

Aplique a árvore de decisão matemática e retorne as alocações no formato JSON.
"""

    # Configuração calibrada para zero alucinação e máxima repetibilidade
    config = types.GenerateContentConfig(
        system_instruction=SYSTEM_INSTRUCTION,
        temperature=0.0,       # Decodificação Greedy determinística
        top_p=0.1,             # Restrição máxima de amostragem
        top_k=1,               # Seleciona sempre o token mais provável
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
