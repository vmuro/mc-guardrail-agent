# 🚀 Guia Unificado de Execução: Local & Google Cloud (GCP)
## GuardrailAI · Desafio de Agentes de IA · Mercado de Capitais (GFT × Google · SMC26)

Este documento consolida todas as instruções para execução do projeto **GuardrailAI**, tanto em ambiente de desenvolvimento **Local** (bare-metal ou conteinerizado) quanto em ambiente remoto no **Google Cloud Platform (GCP)** no contexto da competição.

---

## 📋 Sumário
1. [Visão Geral dos Componentes](#-visão-geral-dos-componentes)
2. [Parte 1: Execução em Ambiente Local](#-parte-1-execução-em-ambiente-local)
   - [2.1 Pré-requisitos](#21-pré-requisitos)
   - [2.2 Inicialização com 1 Comando (Recomendado)](#22-inicialização-com-1-comando-recomendado)
   - [2.3 Execução via Docker Compose](#23-execução-via-docker-compose)
   - [2.4 Execução Modular (Serviço por Serviço)](#24-execução-modular-serviço-por-serviço)
   - [2.5 Execução das Suítes de Testes](#25-execução-das-suítes-de-testes)
3. [Parte 2: Execução e Deploy Remoto no Google Cloud (GCP)](#-parte-2-execução-e-deploy-remoto-no-google-cloud-gcp)
   - [3.1 Arquitetura de Projetos no GCP](#31-arquitetura-de-projetos-no-gcp)
   - [3.2 Autenticação e Configuração da CLI (gcloud)](#32-autenticação-e-configuração-da-cli-gcloud)
   - [3.3 Deploy Automatizado no Cloud Run](#33-deploy-automatizado-no-cloud-run)
   - [3.4 Acesso Remoto Seguro via Proxy Local (Zero-Trust)](#34-acesso-remoto-seguro-via-proxy-local-zero-trust)
4. [Parte 3: Interfaces Web e Experiência do Usuário no Chrome](#-parte-3-interfaces-web-e-experiência-do-usuário-no-chrome)
   - [4.1 Painéis Web Disponíveis](#41-painéis-web-disponíveis)
   - [4.2 Configuração de Notificações Push Web (Chrome & FCM)](#42-configuração-de-notificações-push-web-chrome--fcm)
   - [4.3 Autorização Biométrica Passkey / FIDO2](#43-autorização-biométrica-passkey--fido2)
5. [Resolução de Problemas Comuns (FAQ)](#-resolução-de-problemas-comuns-faq)

---

## 🏛️ Visão Geral dos Componentes

O GuardrailAI é composto por dois serviços complementares que operam de forma integrada:

| Módulo | Tecnologia | Porta Padrão | Responsabilidade |
|---|---|:---:|---|
| **`agent-python`** | Python 3.10+, FastAPI, Vertex AI | `8000` | Coleta de dados B3, raciocínio com Gemini 2.5 Flash, cálculo do Guardrail determinístico e disparo de notificações push (FCM). |
| **`fido-server`** | Java 21, Spring Boot 4.x | `8080` | Armazenamento de desafios com TTL de 120s, orquestração WebAuthn (Passkeys) e painel web de avaliação. |

---

## 💻 Parte 1: Execução em Ambiente Local

### 2.1 Pré-requisitos
- **Git** instalado.
- **Python 3.10+** (com `pip` e suporte a `venv`).
- **Java 21 JDK** (para compilação direta do servidor Spring Boot, ou utilize Docker).
- **Docker & Docker Compose** (opcional, para execução conteinerizada).
- **Google Chrome** (para testes de notificações Web Push e biometria Passkey).

Clone o repositório e acesse a raiz:
```bash
git clone https://github.com/vrmuro/mc-guardrail-agent.git
cd mc-guardrail-agent
```

#### Perfis Sintéticos Pré-configurados:
Os perfis simulados de investidores estão disponíveis em [`data/clients.json`](../data/clients.json):
- `CLI-001` (Perfil Conservador, Teto de Risco 20%)
- `CLI-002` (Perfil Moderado, Teto de Risco 35%)
- `CLI-003` (Perfil Agressivo, Teto de Risco 50%)

---

### 2.2 Inicialização com 1 Comando (Recomendado)

O projeto inclui scripts que sobem automaticamente o Servidor FIDO (Java) e o Agente de Governança (Python) em sincronia:

#### No Linux / macOS / WSL (Ubuntu):
```bash
chmod +x scripts/run_local.sh
./scripts/run_local.sh
```

#### No Windows (PowerShell):
```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\scripts\run_local.ps1
```

O script realizará:
1. Compilação e inicialização do `fido-server` na porta `8080`.
2. Aguarda o healthcheck de prontidão do servidor Java.
3. Ativação do ambiente Python e inicialização da API FastAPI na porta `8000`.

---

### 2.3 Execução via Docker Compose

Caso prefira rodar ambos os serviços isolados em contêineres Docker:

```bash
docker compose up --build
```

Para encerrar:
```bash
docker compose down
```

---

### 2.4 Execução Modular (Serviço por Serviço)

Caso deseje executar ou debugar cada componente em terminais separados:

#### Terminal 1 — Servidor FIDO (Java Spring Boot):
```bash
cd src/fido-server

# No Linux / macOS:
./mvnw spring-boot:run

# No Windows:
.\mvnw.cmd spring-boot:run
```
*Disponível em: `http://localhost:8080`*

#### Terminal 2 — Agente Python (FastAPI / Screener):
```bash
cd src/agent-python

# Ativar ambiente virtual
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Modo 1: API REST FastAPI (utilizada pela interface web)
uvicorn src.server:app --host 0.0.0.0 --port 8000 --reload

# Modo 2: Execução em lote (Batch CLI com os clientes padrão)
python src/main.py --config ../../data/clients.json

# Modo 3: Execução dinâmica via linha de comando
python src/main.py --client-id "CLI-002" --budget 10000 --risk "MODERATE" --watchlist "PETR4.SA,VALE3.SA,ITUB4.SA"
```

---

### 2.5 Execução das Suítes de Testes

O repositório possui cobertura completa de testes unitários e de integração em ambas as linguagens:

#### Testes Python (Pytest):
```bash
cd src/agent-python
.venv/bin/pytest -v tests
```
*Valida: Guardrail numérico `Q = floor(B / P)`, Stop-loss, Screener B3, integração FIDO e Notificador FCM (25/25 testes).*

#### Testes Java (Maven):
```bash
cd src/fido-server
./mvnw test
```
*Valida: Desafios de consentimento, expiração de TTL (120s), verificação de hash canônico e controllers REST (6/6 testes).*

---

## ☁️ Parte 2: Execução e Deploy Remoto no Google Cloud (GCP)

### 3.1 Arquitetura de Projetos no GCP

Durante o desafio SMC26, a governança de nuvem segue a separação estrita de dois projetos Google Cloud:

1. **`prj-gft-br-merc-cap-1` (Projeto de Frontend & Gemini Enterprise):**
   - Hospeda as instâncias do **Gemini Enterprise (AI Applications)** e os fluxos corporativos.
   - Os participantes possuem acesso de consumo no frontend.
2. **`gft-brazil-bu-gcp` (Projeto de Engenharia / Backend):**
   - Projeto onde os serviços conteinerizados do GuardrailAI são hospedados no **Cloud Run** e expostos como **Tools**.

---

### 3.2 Autenticação e Configuração da CLI (`gcloud`)

Autentique sua estação local com credenciais de aplicação do Google Cloud:
```bash
# 1. Login nas credenciais de aplicação
gcloud auth application-default login

# 2. Login na CLI do gcloud
gcloud auth login

# 3. Definir o projeto oficial do desenvolvedor
gcloud config set project gft-brazil-bu-gcp
```

---

### 3.3 Deploy Automatizado no Cloud Run

O repositório inclui um pipeline completo de empacotamento conteinerizado, envio ao Artifact Registry e deploy nos serviços gerenciados do Cloud Run:

```bash
chmod +x scripts/deploy_cloud_run.sh
./scripts/deploy_cloud_run.sh
```

#### Recursos Provisionados:
- **`guardrail-agent-service` (Cloud Run Service):**
  - Imagem: `us-central1-docker.pkg.dev/gft-brazil-bu-gcp/repo-guardrailai/guardrail-agent:latest`
  - Porta `8000`, conectado à API Vertex AI na região `us-central1`.
- **`fido-consent-server` (Cloud Run Service):**
  - Imagem: `us-central1-docker.pkg.dev/gft-brazil-bu-gcp/repo-guardrailai/fido-server:latest`
  - Porta `8080`, gerenciando as requisições WebAuthn e interfaces estáticas.
- **`guardrail-agent-job` (Cloud Run Job):**
  - Execução batch em larga escala para auditoria de carteiras periódica.

---

### 3.4 Acesso Remoto Seguro via Proxy Local (Zero-Trust)

Por segurança e conformidade regulatória, os serviços do Cloud Run no projeto `gft-brazil-bu-gcp` não precisam ficar abertos publicamente na internet. 

Para interagir com o ambiente remoto a partir do seu navegador local de forma criptografada e autenticada:

```bash
gcloud run services proxy fido-consent-server \
    --region=us-central1 \
    --project=gft-brazil-bu-gcp \
    --port=8080
```

Com o proxy em execução, acesse `http://localhost:8080/evaluate.html` no Chrome. Todas as chamadas locais serão roteadas com segurança para os contêineres rodando no Google Cloud.

---

## 🌐 Parte 3: Interfaces Web e Experiência do Usuário no Chrome

### 4.1 Painéis Web Disponíveis

- **Painel de Avaliação de Portfólio & Auditoria:**  
  `http://localhost:8080/evaluate.html`  
  *Permite selecionar clientes sintéticos (`CLI-001`, `CLI-002`, `CLI-003`), definir carteira de ativos e disparar a avaliação de IA com Guardrail determinístico.*
- **Interface de Consentimento Biométrico (Passkey / WebAuthn):**  
  `http://localhost:8080/consent.html?challengeId=<UUID>`  
  *Exibe o resumo inviolável da ordem de compra, o timer regressivo do TTL (120s) e o leitor de biometria para autorização regulatória.*

---

### 4.2 Configuração de Notificações Push Web (Chrome & FCM)

Para receber as notificações no padrão **Data-Only** na área de trabalho:
1. Abra `http://localhost:8080/evaluate.html` no Google Chrome.
2. No pop-up nativo do navegador, clique em **Permitir** (*Allow*).
3. O Service Worker [`firebase-messaging-sw.js`](../src/fido-server/src/main/resources/static/firebase-messaging-sw.js) salvará o token FCM da sessão no `localStorage`.
4. Ao clicar em *"Executar Avaliação"*, uma notificação nativa do sistema operacional surgirá na tela.
5. Clicando na notificação, a tela de biometria correspondente à ordem recomendada é aberta automaticamente.

*(Para detalhes sobre geração da chave `fcm-service-account.json`, consulte [`docs/FCM_SETUP.md`](FCM_SETUP.md)).*

---

### 4.3 Autorização Biométrica Passkey / FIDO2

1. Na tela de consentimento, verifique os dados: Ticker, Quantidade recalculada pela fórmula $Q = \lfloor B / P \rfloor$, Preço e Stop-Loss.
2. Clique no botão de confirmação biométrica.
3. Utilize a chave de segurança do dispositivo (Windows Hello, Touch ID do macOS, ou autenticação do smartphone).
4. O servidor registrará o status como `APPROVED` e gravará o hash canônico no log de auditoria.

---

## ❓ Resolução de Problemas Comuns (FAQ)

1. **"Erro: port 8080 or 8000 already in use"**
   - Encerre instâncias anteriores com `fuser -k 8080/tcp` e `fuser -k 8000/tcp` (Linux) ou pelo Gerenciador de Tarefas (Windows).
2. **"Notificação push não aparece no Chrome"**
   - Verifique se o **Assistente de Foco** (Windows) ou modo **Não Incomodar** (macOS) não está ativo.
   - No Chrome, clique no ícone de ajustes ao lado da URL e confirme se **Notificações** está definido como **Permitir**.
3. **"FIDO Server não conecta com o Agente Python"**
   - Certifique-se de que o backend Python esteja ativo na porta 8000 ou que a variável `AGENT_PYTHON_URL` no `application.yml` aponte para o endereço correto.
