# ☁️ Guia de Acesso e Infraestrutura no Google Cloud (GCP)
## Desafio de Agentes de IA · Mercado de Capitais (GFT × Google · SMC26)

> 💡 **Nota de Documentação:** As instruções deste documento foram consolidadas e integradas ao guia completo do projeto em: **[`docs/GUIA_EXECUCAO.md`](GUIA_EXECUCAO.md)** (cobrindo execução local com 1 comando, Docker, testes, deploy e proxy seguro no Cloud Run).

Para garantir o isolamento, a segurança e a governança de custos durante o Hackathon, o ambiente no Google Cloud (GCP) é dividido em **dois projetos principais**:

---

## 🏛️ Divisão de Projetos no GCP

### 1. `prj-gft-br-merc-cap-1` (Projeto de Frontend & IA)
* **O que é:** Hospeda o **Gemini Enterprise (AI Applications)** e as instâncias/aplicações low-code de cada grupo.
* **Acesso:** Os participantes têm acesso **exclusivamente de uso no frontend** (interface do Gemini Enterprise). Não é permitido criar novos recursos de infraestrutura (como buckets, funções ou bancos) neste projeto.

### 2. `gft-brazil-bu-gcp` (Projeto do Desenvolvedor / Backend)
* **O que é:** Canteiro de obras para criação de ferramentas, dados e serviços que dão suporte ao agente no Gemini Enterprise.
* **Acesso:** Cada participante tem permissão de desenvolvedor para criar e gerenciar recursos **isolados por equipe**.

---

## 🛠️ Como Criar e Utilizar os Recursos no Projeto BU (`gft-brazil-bu-gcp`)

Todo código, banco de dados ou conector do GuardrailAI foi criado no projeto `gft-brazil-bu-gcp` para depois ser vinculado como **Tool** no frontend da aplicação no Gemini Enterprise (`prj-gft-br-merc-cap-1`).

### 1. Autenticação Local (SDK / Terminal)
Para que os seus scripts e ferramentas locais se comuniquem com o GCP, autentique-se via CLI com o comando:
```bash
gcloud auth application-default login
```

E configure o projeto padrão:
```bash
gcloud config set project gft-brazil-bu-gcp
```

---

## 🚀 Deploy dos Serviços no Cloud Run

O projeto conta com automação completa de build e deploy conteinerizado para o Cloud Run:

```bash
# Execução do script oficial de deploy
./scripts/deploy_cloud_run.sh
```

### Componentes Hospedados:
1. **`guardrail-agent-service` (Cloud Run Service)**:
   - Imagem: `us-central1-docker.pkg.dev/gft-brazil-bu-gcp/repo-guardrailai/guardrail-agent:latest`
   - Porta: `8000` (FastAPI)
   - Integração: Vertex AI (`gemini-2.5-flash`) na região `us-central1`.
2. **`fido-consent-server` (Cloud Run Service)**:
   - Imagem: `us-central1-docker.pkg.dev/gft-brazil-bu-gcp/repo-guardrailai/fido-server:latest`
   - Porta: `8080` (Java 21 / Spring Boot)
   - Armazenamento em memória concorrente de desafios biométricos FIDO2 com TTL de 120s.
3. **`guardrail-agent-job` (Cloud Run Job)**:
   - Execução em batch para varredura e rebalanceamento de carteiras de múltiplos clientes.

#### Executando o Job via Linha de Comando (`gcloud`):
```bash
# Execução padrão (aguarda término e exibe status):
gcloud run jobs execute guardrail-agent-job \
    --region=us-central1 \
    --project=gft-brazil-bu-gcp \
    --wait

# Execução customizada para cliente específico via variáveis de ambiente:
gcloud run jobs execute guardrail-agent-job \
    --region=us-central1 \
    --project=gft-brazil-bu-gcp \
    --update-env-vars="CLIENT_ID=CLI-002,USER_BUDGET=10000,RISK_PROFILE=MODERATE,WATCHLIST=PETR4.SA\,VALE3.SA\,ITUB4.SA" \
    --wait

# Consultar logs da última execução:
gcloud logging read "resource.type=cloud_run_job AND resource.labels.job_name=guardrail-agent-job" \
    --project=gft-brazil-bu-gcp \
    --limit=50 \
    --format="value(textPayload)"
```

---

## 🔒 Acesso Seguro via Proxy Local

Para acessar com segurança os serviços privados do Cloud Run sem expô-los à internet pública:

```bash
gcloud run services proxy fido-consent-server \
    --region=us-central1 \
    --project=gft-brazil-bu-gcp \
    --port=8080
```

Em seguida, acesse no navegador:
- **Painel de Avaliação:** `http://localhost:8080/evaluate.html`
- **Painel de Consentimento FIDO2:** `http://localhost:8080/consent.html`
