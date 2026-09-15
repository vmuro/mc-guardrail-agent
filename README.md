# Agente Proativo de Investimentos com Gemini e Guardrail


 INSTRUÇÕES PARA A EQUIPE:
 - Este é um MODELO. Preencha todos os campos entre colchetes [ ... ]
   e apague os comentários (blocos de comentário) antes de submeter.
 - Não altere a estrutura de pastas descrita ao final — o time
   organizador espera encontrar os artefatos exatamente nesses
   diretórios.
 - Use APENAS dados mock, públicos ou sintéticos. É PROIBIDO usar
   dados reais de clientes, confidenciais ou sensíveis.
 - Confidencial — Uso Interno GFT.

=====================================================================

-->
# [NOME DO AGENTE]

> _[Uma frase de efeito que resume o que o agente faz — ex.: "Assistente de IA que monitora liquidez de fundos em tempo real."]_

**Desafio de Agentes de IA — Mercado de Capitais** Iniciativa DGCU07 + BDP em parceria com o Google · SMC26 (27 a 29 de outubro)

---

##  Equipe

|Papel|Nome|E-mail GFT|
|---|---|---|
|**Capitão**|Victor Rosa|vrmu@gft.com|

**Nome da equipe:** [Nome do time]

<!-- Times de 1 a 4 pessoas. Remova as linhas de integrantes não utilizadas. -->

---

## 🎯 O Problema

<!-- 2 a 4 parágrafos. Que dor real de negócio o agente resolve? Qual o contexto no Mercado de Capitais? Quem sofre com esse problema hoje? -->

[Descreva o problema que o agente resolve.]

**Público-alvo:** [Quem usa / se beneficia do agente]

---

## 💡 A Solução

<!-- Explique o que o agente faz, como resolve o problema e por que a abordagem é adequada. Destaque criatividade e inovação. -->

[Descreva a solução em linguagem clara.]

### Principais Funcionalidades

- [Funcionalidade 1]
- [Funcionalidade 2]
- [Funcionalidade 3]

---

## 📊 Impacto

<!-- Qual o valor gerado? Sempre que possível, quantifique. -->

- **Eficiência:** [ex.: reduz em X% o tempo de análise de ...]
- **Redução de erros:** [ex.: elimina a etapa manual de ...]
- **Valor para o cliente / negócio:** [ex.: ...]

---

Este projeto é um MVP (Minimum Viable Product) de um agente autônomo de investimentos focado em *Swing Trade* no mercado brasileiro (B3). O agente utiliza a IA do Google (Gemini) para análise de mercado e um Guardrail determinístico para garantir que as operações sigam regras de risco e orçamento.


## Arquitetura

O sistema opera como um pipeline de processamento em lote, implantado como um **Cloud Run Job** e acionado por um **Cloud Scheduler**.

O fluxo é o seguinte:
1.  **Cloud Scheduler**: Dispara o job em uma programação definida (ex: diariamente).
2.  **Cloud Run Job**: Executa o container da aplicação.
3.  **Aplicação Python**:
    1.  **Coleta de Dados**: Busca indicadores técnicos (`yfinance`, `ta`) e notícias (`feedparser`).
    2.  **Análise de IA**: Envia os dados para o **Gemini 2.5 Flash** (via Vertex AI) para obter uma recomendação (`BUY`/`SELL`/`HOLD`).
    3.  **Auditoria de Risco**: A recomendação é validada por um **Guardrail** (`Pydantic`) que checa orçamento, stop-loss e limites de risco.
    4.  **Logging**: O resultado final é registrado no **Cloud Logging** para auditoria.

## Estrutura do Projeto

```
.
├── src/
│   ├── core/
│   │   ├── agent.py       # Módulo de integração com o Gemini AI
│   │   ├── guardrail.py   # Módulo de validação de risco (Pydantic)
│   │   └── logger.py      # Módulo de logging estruturado
│   ├── tools/
│   │   ├── screener.py    # Ferramenta para coleta de indicadores técnicos
│   │   └── news_parser.py # Ferramenta para coleta de notícias
│   └── main.py            # Orquestrador principal do pipeline
├── Dockerfile             # Definição do container da aplicação
└── requirements.txt       # Dependências Python do projeto
```

## Pré-requisitos

*   Python 3.12+
*   Docker
*   Google Cloud SDK (`gcloud`)
*   Um projeto no Google Cloud com as seguintes APIs habilitadas:
    *   Artifact Registry (`artifactregistry.googleapis.com`)
    *   Cloud Build (`cloudbuild.googleapis.com`)
    *   Cloud Run (`run.googleapis.com`)
    *   Vertex AI (`aiplatform.googleapis.com`)
    *   Cloud Scheduler (`cloudscheduler.googleapis.com`)

## Como Executar Localmente

1.  **Crie e ative um ambiente virtual:**
    ```bash
    python -m venv .venv
    source .venv/bin/activate
    ```

2.  **Instale as dependências:**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Execute o pipeline principal:**
    ```bash
    python -m src.main
    ```

## Como Fazer o Deploy na Nuvem (Cloud Run)

1.  **Configure a autenticação do Docker com o Artifact Registry:**
    ```bash
    gcloud auth configure-docker us-central1-docker.pkg.dev
    ```

2.  **Construa a imagem Docker localmente, apontando para o seu repositório:**
    *(Substitua `<PROJECT_ID>` e `<REPO_NAME>` pelos valores do seu projeto)*
    ```bash
    docker build -t us-central1-docker.pkg.dev/<PROJECT_ID>/<REPO_NAME>/guardrail-agent:latest .
    ```

3.  **Envie a imagem para o Artifact Registry:**
    ```bash
    docker push us-central1-docker.pkg.dev/<PROJECT_ID>/<REPO_NAME>/guardrail-agent:latest
    ```

4.  **Implante o Cloud Run Job usando a imagem enviada:**
    ```bash
    gcloud run jobs deploy guardrail-agent-job \
      --image us-central1-docker.pkg.dev/<PROJECT_ID>/<REPO_NAME>/guardrail-agent:latest \
      --region us-central1
    ```

## Como Executar na Nuvem

*   **Manualmente (para teste):**
    ```bash
    gcloud run jobs execute guardrail-agent-job --region us-central1
    ```
*   **Automaticamente:**
    Configure um **Cloud Scheduler** para invocar a URI do Cloud Run Job em uma programação cron.

