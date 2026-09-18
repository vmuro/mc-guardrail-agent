# Contratos de Integração Inter-Módulos

Este diretório contém os schemas e contratos formais de comunicação entre o **Agente Python** (`agent-python`) e o **Servidor Java FIDO/WebAuthn** (`fido-server`).

---

## 📄 Schemas Disponíveis

1. **[consent-challenge.schema.json](./consent-challenge.schema.json):**
   - Especifica a estrutura de dados para registro, consulta de status e verificação de desafios de consentimento biométrico.
   - Garante que alterações em um dos módulos não quebrem a interoperabilidade REST.

---

## 🔒 Princípio de Payload Binding (Anti-Tampering)

```
Ordem Aprovada (Python) ──> Canonical JSON ──> HMAC-SHA256 ──> POST /api/consent/challenges (Java)
                                                                       │
                                                                       ▼
Investidor Biometria (Passkey) ◄── Link WhatsApp/App ◄── Notificação FIDO
```

O `canonicalPayload` é serializado com chaves ordenadas alfabeticamente para garantir correspondência exata de hash (`orderHash`), evitando que qualquer interceptador altere quantidade, ticker, preço ou stop-loss.
