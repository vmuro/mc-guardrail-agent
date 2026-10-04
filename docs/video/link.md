# 🎥 Vídeos de Demonstração e Pitch — GuardrailAI
## Desafio de Agentes de IA · Mercado de Capitais (GFT × Google · SMC26)

Este diretório reúne as gravações oficiais de demonstração prática e apresentação da arquitetura do **GuardrailAI**.

---

## 📌 1. Apresentação Geral & Pitch de Negócio

- **Arquivo:** [`Apresentacao-GuardrailAI.mp4`](./Apresentacao-GuardrailAI.mp4) (24 MB)
- **Assistir no Repositório (GitLab / GitHub):** 🎥 **[Abrir Vídeo da Apresentação Geral](./Apresentacao-GuardrailAI.mp4)**
- **Duração Estimada:** 3 a 5 minutos
- **Equipe:** GuardrailAI (Capitão: Victor Rosa - `vrmu@gft.com`)
- **Conteúdo:** Apresentação completa do problema de alucinações e omissões matemáticas em LLMs no mercado de capitais (B3), conformidade regulatória CVM, os 3 pilares da arquitetura e demonstração integrada.

<video src="./Apresentacao-GuardrailAI.mp4" controls width="100%">
  Seu navegador não suporta reprodução direta de vídeo. <a href="./Apresentacao-GuardrailAI.mp4">Clique aqui para abrir o arquivo Apresentacao-GuardrailAI.mp4</a>.
</video>

---

## 📌 2. Demonstração 1: Solicitação e Avaliação de Ordem pelo Operador (Fluxo Interativo Web)

- **Arquivo:** [`Solicitacao-Avaliacao-Ativos.mp4`](./Solicitacao-Avaliacao-Ativos.mp4) (21 MB)
- **Assistir no Repositório (GitLab / GitHub):** 🎥 **[Abrir Vídeo: Avaliação de Ativos pelo Operador](./Solicitacao-Avaliacao-Ativos.mp4)**
- **Fluxo Demonstrado:**
  1. O operador acessa o painel web interativo (`/evaluate.html`), seleciona o perfil do cliente e a cesta de ativos a avaliar.
  2. O motor analítico (Gemini 2.5) formula as recomendações e o **Guardrail Engine** executa a validação matemática determinística de risco e limites de capital.
  3. Com a ordem aprovada, é gerado o desafio regulatório com hash canônico no `fido-consent-server`.
  4. O operador efetua a autorização imediata na interface web, assinando a ordem digitalmente com biometria (Passkey / WebAuthn) antes da expiração do TTL de 120 segundos.

<video src="./Solicitacao-Avaliacao-Ativos.mp4" controls width="100%">
  Seu navegador não suporta reprodução direta de vídeo. <a href="./Solicitacao-Avaliacao-Ativos.mp4">Clique aqui para abrir o arquivo Solicitacao-Avaliacao-Ativos.mp4</a>.
</video>

---

## 📌 3. Demonstração 2: Avaliação Agendada em Batch e Notificação Push (Fluxo Autônomo com Assinatura Remota)

- **Arquivo:** [`Solicitacao-Avaliacao-Agendada.mp4`](./Solicitacao-Avaliacao-Agendada.mp4) (4.1 MB)
- **Assistir no Repositório (GitLab / GitHub):** 🎥 **[Abrir Vídeo: Avaliação Agendada e Notificação Push](./Solicitacao-Avaliacao-Agendada.mp4)**
- **Fluxo Demonstrado:**
  1. O operador **não** realiza a solicitação manual; um **Cloud Run Job agendado (rotina batch)** é executado autonomamente em segundo plano.
  2. O agente processa a carteira, coleta indicadores na B3 e gera as ordens recomendadas auditadas matematicamente.
  3. O backend despacha uma **notificação Web Push (FCM Data-Only)** diretamente para o navegador Google Chrome do operador.
  4. O operador recebe o alerta nativo do sistema operacional, clica na notificação e é automaticamente direcionado à tela de consentimento (`/consent.html?challengeId=...`).
  5. O operador revisa a ordem gerada pelo job e efetua a autorização assinando a ordem com biometria/Passkey.

<video src="./Solicitacao-Avaliacao-Agendada.mp4" controls width="100%">
  Seu navegador não suporta reprodução direta de vídeo. <a href="./Solicitacao-Avaliacao-Agendada.mp4">Clique aqui para abrir o arquivo Solicitacao-Avaliacao-Agendada.mp4</a>.
</video>

---

> 💡 **Dica de Reprodução no GitLab/GitHub:** Ao clicar em qualquer um dos links acima, o player de vídeo nativo é carregado diretamente na interface web da plataforma, com suporte a tela cheia e controle de velocidade.
