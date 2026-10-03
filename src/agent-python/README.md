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
   - Disparo de notificações Push Web via **Firebase Cloud Messaging (FCM)** para os investidores.

---

## 🚀 Como Executar Localmente

### 1. Pré-requisitos e Ambiente Virtual
```bash
# Na raiz do repositório:
cd src/agent-python

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

### 3. Executar o Pipeline (Job de Auditoria Batch)

- **Modo Padrão (utilizando clientes do `data/clients.json`):**
  ```bash
  python src/main.py --config ../../data/clients.json
  ```

- **Modo Dinâmico via CLI (suporta `--risk-profile`/`--risk` e envio de push com `--device-token` ou `-t`):**
  ```bash
  python src/main.py --client-id "CLI-002" --budget 10000 --risk "MODERATE" --watchlist "PETR4.SA,VALE3.SA,ITUB4.SA" --device-token "<SEU_TOKEN_FCM>"
  ```

### 4. Executar a API REST FastAPI (Servidor Web)

```bash
python src/server.py
# ou: uvicorn src.server:app --host 0.0.0.0 --port 8000 --reload
```
*Acesse a documentação Swagger interativa em: `http://localhost:8000/docs`.*

### 5. Configuração das Notificações Push (FCM)
- Para habilitar o disparo de notificações Web Push reais, posicione a chave privada da conta de serviço em `config/fcm-service-account.json`.
- Caso o arquivo não esteja presente, o módulo opera em **modo de simulação resiliente** sem falhar.
- **Na Web (`/api/evaluate`):** O navegador Chrome injeta o token automaticamente via payload.
- **No Job Batch / CLI:** Configure a variável `TARGET_DEVICE_TOKEN`, adicione `"device_token"` em `clients.json`, ou use a flag `--device-token`.
- Para obter a chave e configurar o recebimento no Google Chrome, veja [`docs/FCM_SETUP.md`](../../docs/FCM_SETUP.md).

---

## 🐳 Executando via Docker

```bash
# Build da imagem:
docker build -t guardrail-agent:latest .

# Execução como Servidor FastAPI (porta 8000):
docker run --rm -p 8000:8000 guardrail-agent:latest

# Execução pontual como Cloud Run Job / Batch CLI:
docker run --rm guardrail-agent:latest python src/main.py --client-id "CLI-002" --budget 10000 --risk-profile "MODERATE" --watchlist "PETR4.SA,VALE3.SA"
```
