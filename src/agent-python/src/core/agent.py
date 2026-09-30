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
    """Inicializa o cliente oficial google-genai para Vertex AI ou Gemini Developer API."""
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if api_key and not os.getenv("GOOGLE_GENAI_USE_VERTEXAI"):
        return genai.Client(api_key=api_key)
    return genai.Client(
        vertexai=True,
        project=PROJECT_ID,
        location=LOCATION
    )


def generate_deterministic_portfolio_proposal(
    market_snapshot: list[dict],
    user_budget: float = 5000.0,
    risk_profile: str = "MODERATE"
) -> dict:
    """
    Árvore de decisão técnica estatística determinística (Regras algorítmicas de governança).
    Atuada como motor de alta resiliência e disponibilidade (garantindo continuidade quando
    credenciais de nuvem ou quotas não estiverem configuradas).
    """
    allocations = []
    
    stop_pct = {
        "CONSERVATIVE": 0.05,
        "MODERATE": 0.10,
        "AGGRESSIVE": 0.14
    }.get(risk_profile, 0.10)

    for item in market_snapshot:
        ticker = item.get("ticker", "UNKNOWN")
        current_price = float(item.get("current_price") or 0.0)
        if current_price <= 0:
            continue

        ema_9 = item.get("ema_9")
        ema_21 = item.get("ema_21")
        sma_20 = item.get("sma_20")
        sma_200 = item.get("sma_200")
        rsi_14 = item.get("rsi_14")
        macd_diff = item.get("macd_diff")

        # Regra 1: AÇÃO "BUY"
        # (EMA_9 > EMA_21) E (preço > SMA_200 se disponível) E (RSI_14 entre 35.0 e 70.0)
        is_trend_up = (ema_9 is not None and ema_21 is not None and ema_9 > ema_21)
        is_above_sma200 = (sma_200 is None or current_price >= sma_200)
        is_rsi_valid = (rsi_14 is not None and 35.0 <= rsi_14 <= 70.0)

        if is_trend_up and is_above_sma200 and is_rsi_valid:
            if risk_profile == "CONSERVATIVE":
                ref_stop = min(ema_21, sma_20) if (ema_21 and sma_20) else (current_price * (1.0 - stop_pct))
                stop_loss_price = max(ref_stop, current_price * 0.92)  # Queda máx 8%
            else:
                stop_loss_price = round(current_price * (1.0 - stop_pct), 2)

            stop_loss_price = round(stop_loss_price, 2)
            rationale = (
                f"Sinal de COMPRA algorítmica: EMA9 ({ema_9}) > EMA21 ({ema_21}), "
                f"RSI14 ({rsi_14}) em zona favorável de momentum e preço ({current_price}) acima de suportes."
            )
            allocations.append({
                "ticker": ticker,
                "action": "BUY",
                "quantity": 100,
                "unit_price": current_price,
                "stop_loss_price": stop_loss_price,
                "rationale": rationale
            })
        else:
            reasons = []
            if ema_9 is not None and ema_21 is not None and ema_9 <= ema_21:
                reasons.append(f"EMA9 ({ema_9}) <= EMA21 ({ema_21})")
            if sma_200 is not None and current_price < sma_200:
                reasons.append(f"preço ({current_price}) < SMA200 ({sma_200})")
            if rsi_14 is not None and (rsi_14 < 35.0 or rsi_14 > 70.0):
                reasons.append(f"RSI14 ({rsi_14}) fora da faixa ideal 35-70")
            if macd_diff is not None and macd_diff < 0:
                reasons.append(f"MACD histograma ({macd_diff}) negativo")

            detail = ", ".join(reasons) if reasons else "Critérios técnicos de entrada não preenchidos."
            rationale = f"Recomendação de CAUTELA (HOLD): {detail}."
            allocations.append({
                "ticker": ticker,
                "action": "HOLD",
                "quantity": 0,
                "unit_price": 0.0,
                "stop_loss_price": 0.0,
                "rationale": rationale
            })

    buy_count = sum(1 for a in allocations if a["action"] == "BUY")
    rationale_summary = (
        f"Auditoria Determinística de Mercado: Identificados {buy_count} ativo(s) com alinhamento "
        f"estatístico de médias e momentum para o perfil de risco {risk_profile}."
    )

    return {
        "portfolio_rationale": rationale_summary,
        "allocations": allocations
    }


def analyze_market_with_gemini(
    market_snapshot: list[dict],
    user_budget: float = 5000.0,
    risk_profile: str = "MODERATE"
) -> dict:
    """
    Envia o snapshot completo de mercado e parâmetros do investidor com
    temperatura 0.0 para garantir consistência e reprodutibilidade total.
    Em caso de ausência de credenciais GCP (ADC) ou erro de API, ativa
    automaticamente a árvore de decisão determinística de segurança.
    """
    try:
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
            parsed = json.loads(response.text)
            if "allocations" in parsed and isinstance(parsed["allocations"], list):
                return parsed
        except json.JSONDecodeError:
            print(f"⚠️ Resposta do Gemini não é JSON válido: {response.text}")

    except Exception as e:
        print(f"⚠️ [AVISO] Gemini/Vertex AI indisponível ou credenciais ausentes ({type(e).__name__}: {e}).")
        print("🛡️ [GUARDRAIL] Ativando motor de decisão técnica determinística local (Alta Disponibilidade)...")

    return generate_deterministic_portfolio_proposal(market_snapshot, user_budget, risk_profile)

