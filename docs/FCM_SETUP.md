# 🔔 Guia de Configuração: Notificações Push Web (FCM) & Google Chrome

Este documento detalha a dependência de **Firebase Cloud Messaging (FCM)** para envio de Notificações Push Web no **GuardrailAI**, incluindo a geração das credenciais da conta de serviço (*Service Account*) e o procedimento que o usuário/avaliador deve realizar no **Google Chrome** para receber as notificações em tempo real.

---

## 🏛️ 1. Arquitetura de Notificações Push (Data-Only)

O fluxo de autorização regulatória do GuardrailAI utiliza notificações push no padrão **Data-Only** com Service Worker em background:

```
[Agent Python Backend]
       │ (Firebase Admin SDK HTTP v1)
       ▼
[Firebase Cloud Messaging (FCM)]
       │ (Push Network)
       ▼
[Navegador Google Chrome (Máquina do Cliente)]
       │
       ├──> [Service Worker: firebase-messaging-sw.js]
       │         │ (Exibe Toast Nativo do SO)
       │         ▼
       └──> [Clique do Usuário] ──> Abre /consent.html?challengeId=<ID>
```

> **Por que Data-Only?** Mensagens do tipo `notification` acionam o renderizador automático do Chromium, o que frequentemente duplica o popup no Windows. Com payloads `data-only`, o `firebase-messaging-sw.js` assume controle total da notificação, garantindo idempotência e 1 notificação por ordem recomendada.

---

## 🔑 2. Dependência da Conta de Serviço (`fcm-service-account.json`)

Para que o backend do agente Python (`src/agent-python/src/core/notifier.py`) envie notificações push autenticadas ao FCM, é necessária uma **chave privada de conta de serviço** do Firebase.

### Como criar e configurar a Service Account:

1. **Acesse o Firebase Console:**
   - Entre em [https://console.firebase.google.com/](https://console.firebase.google.com/) com a sua conta Google.
   - Selecione o projeto existente (ex.: `guardrail-notifier-mvp` ou o projeto vinculado ao GCP `gft-brazil-bu-gcp`).

2. **Gere a Chave Privada da Conta de Serviço:**
   - Clique no ícone de **Configurações do Projeto** (ícone de engrenagem no menu lateral esquerdo).
   - Acesse a aba **Contas de serviço** (*Service accounts*).
   - Certifique-se de que a opção **Firebase Admin SDK** (Node.js/Python/Java) está selecionada.
   - Clique no botão **Gerar nova chave privada** (*Generate new private key*).
   - Confirme clicando em **Gerar chave**. Um arquivo `.json` será baixado na sua máquina.

3. **Posicione o Arquivo no Projeto:**
   - Renomeie o arquivo baixado para `fcm-service-account.json`.
   - Copie o arquivo para:
     ```bash
     src/agent-python/config/fcm-service-account.json
     ```
   - *(Nota de Segurança: Este arquivo já está registrado no [`.gitignore`](../.gitignore) e nunca será comitado no repositório).*

4. **Variável de Ambiente (`.env`):**
   - No arquivo `.env` da raiz, certifique-se de que a variável aponta para o caminho relativo ou absoluto do arquivo:
     ```bash
     GOOGLE_APPLICATION_CREDENTIALS_FCM="config/fcm-service-account.json"
     ```

> 💡 **Modo Simulação / Fallback:** Caso a chave do Firebase não esteja presente, o módulo [`notifier.py`](../src/agent-python/src/core/notifier.py) opera em modo de simulação resiliente (logando o disparo no console sem interromper o fluxo de governança e avaliação do portfólio).

---

## 💻 3. O que fazer na Máquina do Cliente (Google Chrome)

Para que o avaliador ou investidor receba a notificação push nativa na tela do computador:

### Passo 1: Acessar uma Origem Segura (Localhost ou HTTPS)
A especificação Web Push e a API WebAuthn (Passkeys) exigem **Contexto Seguro** (*Secure Context*).
- **Em ambiente local:** Acesse via `http://localhost:8080/evaluate.html` (o Chrome trata `localhost` como origem segura).
- **Em ambiente remoto / Cloud Run:** Acesse via **HTTPS** ou utilize o túnel seguro do Google Cloud CLI:
  ```bash
  gcloud run services proxy fido-consent-server --region=us-central1 --project=gft-brazil-bu-gcp --port=8080
  ```

### Passo 2: Conceder Permissão de Notificações no Chrome
1. Ao carregar a página [`http://localhost:8080/evaluate.html`](http://localhost:8080/evaluate.html), o Chrome exibirá um pop-up no canto superior esquerdo da tela:
   > *"localhost:8080 deseja enviar notificações"*
2. Clique no botão **Permitir** (*Allow*).
3. **Se o pop-up não aparecer ou já tiver sido bloqueado anteriormente:**
   - Clique no ícone de **Informações do Site / Ajustes** (ao lado esquerdo da barra de URLs do Chrome, junto ao `http://localhost:8080`).
   - Na opção **Notificações**, altere de *Bloquear* ou *Padrão* para **Permitir** (*Allow*).
   - Recarregue a página (`F5` ou `Ctrl+R`).

### Passo 3: Registro do Token FCM e Service Worker
- Ao conceder permissão, a aplicação:
  1. Registra o Service Worker [`/firebase-messaging-sw.js`](../src/fido-server/src/main/resources/static/firebase-messaging-sw.js) no navegador.
  2. Obtém um **FCM Device Token** exclusivo para a sua sessão do Chrome via Firebase JS SDK.
  3. Salva o token no `localStorage` do seu navegador.
  4. Encaminha o token automaticamente ao submeter avaliações no painel.

### Passo 4: Atenção às Configurações do Sistema Operacional
Se a notificação visual não aparecer no canto da tela mesmo com permissão concedida no Chrome:
- **Windows 10 / 11:**
  - Verifique se o **Assistente de Foco** (*Focus Assist* / *Não Incomodar*) não está ativado.
  - Vá em *Configurações do Windows* > *Sistema* > *Notificações* e certifique-se de que o **Google Chrome** tem permissão de emitir notificações sonoras e banners.
- **macOS:**
  - Vá em *Ajustes do Sistema* > *Notificações* > selecione o **Google Chrome** e ative *"Permitir notificações"*.
- **Linux:**
  - Certifique-se de que o daemon de notificações do seu ambiente desktop (ex.: `dunst`, `mako` ou o centralizador do GNOME/KDE) esteja ativo.

---

## 🎯 4. Teste Prático de Ponta a Ponta

1. Abra a tela de avaliação em [`http://localhost:8080/evaluate.html`](http://localhost:8080/evaluate.html) no Chrome.
2. Certifique-se de que as notificações estão **Permitidas**.
3. Selecione o cliente **`CLI-002` (Moderado)** e clique em **Executar Avaliação de Governança**.
4. O backend executará o Screener B3, o raciocínio via Gemini 2.5 e a validação matemática do Guardrail.
5. Em instantes, o Chrome exibirá a notificação nativa:
   > **🚨 GuardrailAI - Autorização de Ordem**  
   > *Nova ordem de BUY para PETR4.SA (R$ 3.480,00)*
6. **Clique diretamente na notificação**: ela abrirá instantaneamente a tela de autorização biométrica:
   ```
   http://localhost:8080/consent.html?challengeId=<UUID_DO_DESAFIO>
   ```
7. Toque no leitor biométrico (Touch ID / Windows Hello / Passkey) para assinar digitalmente a ordem antes da expiração do **TTL de 120 segundos**.
