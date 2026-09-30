# 🖼️ Imagens, Telas e Demonstrações da Interface — GuardrailAI
## Desafio de Agentes de IA · Mercado de Capitais (GFT × Google · SMC26)

Este diretório reúne as capturas de tela e fluxos visuais demonstrativos do sistema **GuardrailAI**:

### 1. Tela de Avaliação e Governança de Portfólio (`/evaluate.html`)
- Painel para simulação de ordens e auditoria determinística de carteiras.
- Exibição de orçamentos, status da ordem (Aprovada, Ajustada $Q = \lfloor B/P \rfloor$, Rejeitada) e racional analítico gerado pelo Gemini 2.5 Flash.
- Exibição do contador regressivo de TTL de consentimento regulatório (120s).

### 2. Tela de Consentimento Biométrico FIDO2 / Passkey (`/consent.html`)
- Visualização de ordens aprovadas pendentes de assinatura.
- Detalhamento de volume, ticker, preço unitário, Stop-Loss e hash criptográfico HMAC-SHA256.
- Botões de assinatura com autenticação WebAuthn nativa (TouchID, FaceID, Windows Hello).
- Conexão em tempo real via Firebase Cloud Messaging (Web Push) para recebimento de solicitações instantâneas.
