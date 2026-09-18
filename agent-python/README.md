# GuardrailAI - Agent Python

Módulo do **Agente de IA e Motor de Guardrails Determinísticos** para o Mercado de Capitais (B3).

---

## 🏛️ Responsabilidades do Módulo

1. **Screener & Ingestão de Mercado (`src/tools/`):**
   - Coleta de dados históricos e cotações em tempo real de ações da B3 via `yfinance`.
   - Cálculo determinístico de indicadores técnicos: **MACD**, **Bandas de Bollinger**, **Médias Móveis (EMA 9, 21, 50, 200)** e **RSI**.
   - Coleta e análise de sentimento de notícias financeiras recentes via Google News RSS.

2. **Raciocínio Cognitivo (`src/core/agent.py`):**
   - Formulação de teses de alocação de carteira através do **Gemini 2.5 Flash** (via Vertex AI / Google GenAI SDK).

3. **Guardrail 100% Determinístico (`src/core/guardrail.py`):**
   - **Blindagem contra alucinações numéricas**: $Q = \lfloor B / P \rfloor$ (recalcula a quantidade máxima inteira permitida com base no orçamento e preço real).
   - **Stop-Loss Obrigatório**: Bloqueio de ordens sem Stop-Loss ou com perda superior ao perfil de risco.
   - **Enforcement de Perfis de Risco**: `CONSERVATIVE` (teto 20%), `MODERATE` (teto 35%), `AGGRESSIVE` (teto 50%).

4. **Consentimento Regulatório & Não-Repúdio (`src/core/consent.py`):**
   - Geração de **Payload Binding Criptográfico (HMAC-SHA256)** inviolável.
   - Comunicação via API REST com o `fido-server` para autorização biométrica **Passkey/WebAuthn** com TTL estrito de 120s.
   - Disparo de notificações via WhatsApp para os investidores.

---

## 🚀 Como Executar Localmente

### 1. Pré-requisitos e Ambiente Virtual
```bash
# Na raiz do projeto ou dentro de agent-python:
cd agent-python

# Criar e ativar ambiente virtual
python3 -m venv .venv
source .venv/bin/activate  # Linux/Mac/WSL
# ou no Windows: .venv\Scripts\activate

# Instalar dependências
pip install -r requirements.txt
```

### 2. Executar Suíte de Testes Automatizados
```bash
pytest -v
```

### 3. Executar o Pipeline

- **Modo Padrão (utilizando clientes do `config/clients.json` compartilhado):**
  ```bash
  python src/main.py --config ../config/clients.json
  ```

- **Modo Dinâmico via CLI:**
  ```bash
  python src/main.py --client-id "investidor_vip_007" --budget 12000 --risk "AGGRESSIVE" --watchlist "PETR4.SA,VALE3.SA,ITUB4.SA"
  ```

---

## 🐳 Executando via Docker

```bash
docker build -t guardrail-agent:latest .
docker run --rm -v $(pwd)/../config:/app/config guardrail-agent:latest
```
