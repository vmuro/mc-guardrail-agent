# GuardrailAI

> _Middleware B2B de governança que combina autonomia proativa de mercado (Gemini / Vertex AI) com motor de Guardrails 100% determinísticos, blindagem contra alucinações matemáticas e consentimento regulatório (CVM)._

**Desafio de Agentes de IA — Mercado de Capitais**  
Iniciativa DGCU07 + BDP em parceria com o Google · SMC26 (27 a 29 de outubro)

---

## 👥 Equipe

| Papel | Nome | E-mail GFT |
|---|---|---|
| **Capitão** | Victor Rosa | vrmu@gft.com |

**Nome da equipe:** GuardrailAI

---

## 🎯 O Problema

As corretoras, instituições financeiras e investidores enfrentam um receio crítico em delegar a execução de ordens e análises de mercado a modelos de Inteligência Artificial generativa devido à imprevisibilidade e ao risco inerente de **alucinações matemáticas na leitura de preços e quantidades**.

Embora os modelos de linguagem (LLMs) possam sugerir alocações dinâmicas e oportunidades de mercado, correm o risco de **omitir parâmetros fundamentais de gestão de risco — como o preço de Stop-Loss —**, o que poderia expor o capital do cliente a prejuízos descontrolados.

Os sistemas tradicionais carecem de uma camada intermediária (*middleware*) robusta que combine uma **verificação determinística estrita** (recalculando tetos financeiros e limites de orçamento em código) com um **fluxo de consentimento regulatório auditável** e compatível com as normas da CVM.

**Público-alvo:**
- **Investidores Individuais (Varejo Alta Renda):** Co-piloto automatizado para leitura de dados e gestão de carteira pessoal sem necessidade de acompanhamento em tempo integral.
- **Escritórios de Investimento & Assessores (AAI):** Monitoramento contínuo e supervisão simultânea de centenas de carteiras de clientes com escala e personalização.
- **Gestoras & Wealth Management:** Execução de rotinas de rebalanceamento com cumprimento estrito de mandatos e eliminação de viés operacional.

---

## 💡 A Solução

O **GuardrailAI** é um middleware B2B de governança que atua como ponte segura entre modelos de inteligência artificial generativa e os sistemas de execução no Mercado de Capitais. A solução desacopla a inteligência analítica da execução financeira, estruturada em **3 Pilares Fundamentais**:

1. **Autonomia Proativa (Screener + ReAct):** O utilizador define apenas o orçamento ($B$) e o perfil de risco. O agente varre autonomamente a watchlist da B3, processa indicadores técnicos (MACD, Bollinger, EMAs 9/21/50/200, RSI) e notícias, identificando a melhor oportunidade com tese fundamentada.
2. **Segurança Inviolável (Guardrail Engine 100% Determinístico):** A IA atua de forma estritamente analítica e nunca envia ordens diretas à bolsa. Toda intenção em JSON é interceptada por uma camada determinística em código que recalcula a quantidade exata ($Q = \lfloor B/P \rfloor$), rejeita ordens sem Stop-Loss (ou com perda > 15%) e impõe tetos rígidos de concentração por perfil de risco.
3. **Consentimento Regulatório e Não-Repúdio (CVM):** Operações geram uma solicitação com **Payload Binding Criptográfico (HMAC-SHA256)**, notificação Push instantânea (FCM) e autorização biométrica **Passkey / FIDO2 (WebAuthn)** com **TTL estrito de 120 segundos**, produzindo trilha de auditoria imutável no Cloud Logging.

### Principais Funcionalidades

- **Varredura Técnica Multi-Indicador B3:** Cálculo automático de momentum, reversão à média e suporte/resistência em tempo real.
- **Blindagem Matemática Antialucinação ($Q = \lfloor B/P \rfloor$):** Recálculo exato de quantidades em código determinístico, impossibilitando erros de escala ou ordens fracionárias incorretas.
- **Gestão Obrigatória de Risco (Stop-Loss Ativo):** Bloqueio sistemático de ordens sem preço de saída de proteção ou com distorção matemática.
- **Consentimento Biométrico FIDO2 com TTL de 120s:** Assinatura na ponta do investidor (TouchID, FaceID, Windows Hello) com validade curta contra volatilidade excessiva.
- **Notificações Push Web (FCM Data-Only):** Envio instantâneo da solicitação para o dispositivo cadastrado do cliente.
- **Arquitetura Zero-Trust de Identidade:** Interceptors que validam tokens de identidade do Google Cloud antes de liberar qualquer execução.

---

## 📊 Impacto

- **Eficiência:** Reduz em **mais de 90%** o tempo necessário para varredura técnica de mercado, cálculo de risco e checagem de conformidade de ordens.
- **Redução de erros:** **0% de alucinações matemáticas** em alocação financeira e garantia de 100% de ordens aprovadas com Stop-Loss válido.
- **Valor para o cliente / negócio:** Conformidade regulatória plena com a CVM, não-repúdio via criptografia de chave pública e proteção do investidor contra variações bruscas de mercado.

---

## 🏛️ Arquitetura

![Arquitetura da Solução](docs/arquitetura.png)

**Descrição do fluxo:**
1. O investidor ou assessor solicita a avaliação via interface web ou conector Gemini Enterprise.
2. O **Módulo Python (FastAPI)** coleta dados da B3, aciona o **Gemini 2.5 Flash (Vertex AI)** para elaboração de tese e submete as propostas ao **Guardrail Engine**.
3. O Guardrail recalcula deterministicamente quantidades e tetos de risco. Ordens aprovadas geram um hash criptográfico (HMAC-SHA256).
4. O **Módulo Java (Spring Boot / FIDO2)** registra o desafio em memória concorrente com TTL de 120 segundos e dispara uma Notificação Push via **Firebase Cloud Messaging**.
5. O investidor assina biometricamente o desafio via **WebAuthn Passkey** na tela de consentimento. A ordem assinada e auditada é persistida com registro imutável no **Google Cloud Logging**.

---

## 🛠️ Stack Tecnológica

| Camada | Tecnologia |
|---|---|
| Plataforma de IA | Gemini Enterprise & Google Cloud Vertex AI |
| Abordagem | Code (Vertex AI + ADK) + Low-Code Tool para Gemini Enterprise |
| Modelo(s) | Gemini 2.5 Flash |
| Recursos usados | Function Calling, ReAct Multi-Indicador, WebAuthn FIDO2, FCM Web Push, Cloud Logging |
| Backend & Governança | Python 3.12 (FastAPI, Pandas, TA, Pytest) |
| Servidor de Consentimento | Java 21 (Spring Boot 4.x, Maven, WebAuthn) |
| Infraestrutura em Nuvem | Google Cloud Run (Services & Jobs), Artifact Registry |

---

## ▶️ Demo

🔗 **Link da demo online (Cloud Run via Proxy):**  
- **Painel de Avaliação de Portfólio:** `http://localhost:8080/evaluate.html`
- **Painel de Consentimento Biométrico FIDO2:** `http://localhost:8080/consent.html`

> 📘 **Guia Completo de Execução:** Para o passo a passo detalhado de inicialização local (com 1 comando em Linux/Windows/Docker), execução modular, testes, deploy no Cloud Run e acesso seguro via proxy, consulte o **[`docs/GUIA_EXECUCAO.md`](docs/GUIA_EXECUCAO.md)**.

**Perfis Sintéticos para Teste:**
Os perfis simulados de investidores estão pré-configurados em [`data/clients.json`](data/clients.json):
- `CLI-001` (Perfil Conservador, Teto de Risco 20%)
- `CLI-002` (Perfil Moderado, Teto de Risco 35%)
- `CLI-003` (Perfil Agressivo, Teto de Risco 50%)

### 🔔 Notificações Push no Google Chrome (FCM):
Para receber alertas em tempo real e assinar biometricamente as ordens recomendadas:
1. Acesse o painel em `http://localhost:8080/evaluate.html` no Chrome (contexto seguro/`localhost`).
2. Clique em **Permitir** (*Allow*) no pop-up nativo de notificações.
3. Ao submeter uma avaliação, clique na notificação que surge na área de trabalho para abrir a tela de consentimento Passkey com TTL de 120s.
- 📖 *Para o guia completo de credenciais e permissões no Chrome, consulte [`docs/FCM_SETUP.md`](docs/FCM_SETUP.md) e [`docs/GUIA_EXECUCAO.md`](docs/GUIA_EXECUCAO.md).*

---

## 🎥 Vídeos (Pitch + Demonstrações Práticas)

Os vídeos oficiais de apresentação e demonstração estão disponíveis no diretório [`docs/video/`](docs/video/):

1. **Apresentação Geral & Pitch de Negócio (3 a 5 min):**  
   🎥 [`Apresentacao-GuardrailAI.mp4`](docs/video/Apresentacao-GuardrailAI.mp4) — Visão geral executiva, conformidade regulatória B3/CVM e os 3 pilares da arquitetura.
2. **Demo 1 — Solicitação e Avaliação de Ordem pelo Operador (Fluxo Web):**  
   🎥 [`Solicitacao-Avaliacao-Ativos.mp4`](docs/video/Solicitacao-Avaliacao-Ativos.mp4) — O operador solicita a avaliação interativa de ativos via painel web e efetua a autorização assinando a ordem com biometria Passkey/FIDO2.
3. **Demo 2 — Avaliação Agendada e Notificação Push (Fluxo Batch Autônomo):**  
   🎥 [`Solicitacao-Avaliacao-Agendada.mp4`](docs/video/Solicitacao-Avaliacao-Agendada.mp4) — O operador não solicita a avaliação; um job agendado no Cloud Run executa a avaliação em lote, despacha notificação Web Push (FCM) e o operador autoriza a execução assinando a ordem.

Consulte o documento oficial com roteiro e players embutidos em [`docs/video/link.md`](docs/video/link.md).

---

## 📎 Artefatos Entregáveis

Todos os entregáveis obrigatórios do desafio estão organizados neste repositório conforme a tabela abaixo:

| Entregável | Formato | Onde está | Status |
|---|---|---|---|
| Demo funcional | Link / código | [Seção Demo](#️-demo) + [`/src`](src/) | [x] |
| Vídeo (pitch + demo) | Link (URL) | [Seção Vídeo](#-vídeo-pitch--demo) + [`/docs/video/link.md`](docs/video/link.md) | [x] |
| One-pager (problema, solução, impacto) | **PDF** (1 página) | [`/docs/one-pager.pdf`](docs/one-pager.pdf) | [x] |
| Diagrama de arquitetura | **PDF** + imagem | [`/docs/arquitetura.pdf`](docs/arquitetura.pdf) · [`/docs/arquitetura.png`](docs/arquitetura.png) | [x] |
| Guia Unificado de Execução (Local & GCP) | Markdown | [`/docs/GUIA_EXECUCAO.md`](docs/GUIA_EXECUCAO.md) | [x] |
| Guia de Notificações FCM & Chrome | Markdown | [`/docs/FCM_SETUP.md`](docs/FCM_SETUP.md) | [x] |
| Guia de Infraestrutura GCP (Apêndice) | Markdown | [`/docs/GCP_GUIDE.md`](docs/GCP_GUIDE.md) | [x] |
| Termo de Propriedade & Autoria | Markdown | [`/NOTICE.md`](NOTICE.md) | [x] |

---

## 📁 Estrutura do Repositório

```
.
├── README.md                  ← Este arquivo (o cartão de visita e landing page do agente)
│
├── src/                       ← CÓDIGO-FONTE da solução (Arquitetura Poliglota)
│   ├── requirements.txt       (dependências Python do agente esperadas pela banca)
│   ├── agent-python/          (módulo cognitivo de IA, screener B3, guardrails, FastAPI)
│   │   ├── Dockerfile
│   │   ├── requirements.txt
│   │   ├── src/               (core/, tools/, server.py, main.py)
│   │   └── tests/             (suíte de testes unitários pytest)
│   └── fido-server/           (módulo de consentimento regulatório WebAuthn FIDO2 / Java 21)
│       ├── Dockerfile
│       ├── pom.xml
│       └── src/               (APIs de consentimento biométrico, desafios TTL 120s)
│
├── data/                      ← DADOS mock / públicos / sintéticos
│   ├── clients.json           (perfis simulados de investidores CLI-001, CLI-002, CLI-003)
│   └── README.md              (declaração de origem de dados 100% fictícios e públicos)
│
├── docs/                      ← DOCUMENTAÇÃO e artefatos de entrega
│   ├── one-pager.pdf          → PDF executivo: problema, solução e impacto (OBRIGATÓRIO)
│   ├── arquitetura.pdf        → PDF: diagrama da arquitetura em alta resolução (OBRIGATÓRIO)
│   ├── arquitetura.png        → Imagem do diagrama da solução (referenciada no README)
│   ├── GUIA_EXECUCAO.md       → Guia unificado de execução (Local bare-metal, Docker e GCP Cloud Run)
│   ├── FCM_SETUP.md           → Guia de configuração da Service Account FCM e Google Chrome
│   ├── GCP_GUIDE.md           → Guia técnico de acesso e infraestrutura Google Cloud
│   ├── video/
│   │   └── link.md            → Arquivo texto com o LINK do vídeo de pitch e demo
│   └── imagens/               → Descrição e capturas de tela das interfaces web
│
├── contracts/                 ← JSON Schemas e contratos formais de payload
├── scripts/                   ← Scripts de automação, deploy no Cloud Run e inicialização local
└── NOTICE.md                  ← Propriedade intelectual da GFT; autoria dos participantes
```

### Onde está gravado cada tipo de arquivo:
- **Código e prompts** → [`src/`](src/) e [`src/requirements.txt`](src/requirements.txt).
- **Dados** → [`data/`](data/) (100% sintéticos e documentados em [`data/README.md`](data/README.md)).
- **One-pager** → [`docs/one-pager.pdf`](docs/one-pager.pdf) (formato PDF de 1 página executiva).
- **Diagrama de arquitetura** → [`docs/arquitetura.pdf`](docs/arquitetura.pdf) e [`docs/arquitetura.png`](docs/arquitetura.png).
- **Guia de Execução (Local & GCP)** → [`docs/GUIA_EXECUCAO.md`](docs/GUIA_EXECUCAO.md).
- **Notificações Push & Chrome** → [`docs/FCM_SETUP.md`](docs/FCM_SETUP.md).
- **Infraestrutura Cloud** → [`docs/GCP_GUIDE.md`](docs/GCP_GUIDE.md).
- **Vídeo** → [`docs/video/link.md`](docs/video/link.md).
- **Imagens da demo** → [`docs/imagens/`](docs/imagens/).
