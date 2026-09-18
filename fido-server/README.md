# GuardrailAI - FIDO/WebAuthn Server

Servidor de **Consentimento Regulatório, Assinatura Biométrica (Passkey / WebAuthn) e Não-Repúdio (CVM)** implementado em **Java 21 e Spring Boot 4.x**.

---

## 🏛️ Responsabilidades do Módulo

1. **Gestão de Desafios de Consentimento (`ConsentChallenge`):**
   - Recebe solicitações de autorização de ordens geradas pelo `agent-python`.
   - Gerencia a validade temporal estrita de **TTL de 120 segundos** (Time-To-Live).
   - Controla os estados regulatórios: `PENDING`, `APPROVED`, `REJECTED`, `EXPIRED`.

2. **Verificação Biométrica & Não-Repúdio:**
   - Interface WebAuthn/FIDO2 no endpoint estático `/consent.html`.
   - Validação de assinaturas criptográficas anti-tampering e vinculação do payload canônico (`canonicalPayload` + `orderHash`).

---

## 📡 Endpoints REST da API

| Método | Endpoint | Descrição |
|---|---|---|
| `POST` | `/api/consent/challenges` | Registra um novo desafio de consentimento com TTL de 120s. |
| `GET` | `/api/consent/status/{challengeId}` | Consulta o status em tempo real do desafio (utilizado por polling pelo agente e interface web). |
| `POST` | `/api/consent/verify` | Valida a assinatura biométrica WebAuthn enviada pelo dispositivo do usuário. |

### Exemplo de Payload para Registro (`POST /api/consent/challenges`)

```json
{
  "challengeId": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "clientId": "CLI-001",
  "userHandle": "user_cli_001",
  "orderHash": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
  "canonicalPayload": "{\"action\":\"BUY\",\"created_at\":1710000000,\"quantity\":40,\"ticker\":\"PETR4.SA\"}",
  "ttlSeconds": 120
}
```

---

## 🚀 Como Executar Localmente

### 1. Pré-requisitos
- **Java 21 JDK** instalado e configurado na variável `JAVA_HOME`.
- Maven 3.9+ (ou utilizar o `./mvnw` embutido).

### 2. Executando o Servidor Spring Boot
```bash
cd fido-server

# No Linux / WSL / macOS:
./mvnw spring-boot:run

# No Windows (PowerShell / CMD):
.\mvnw.cmd spring-boot:run
```

O servidor estará disponível em `http://localhost:8080`.

### 3. Acessando a Interface de Consentimento Biométrico
Abra no navegador (ou compartilhe via ngrok para testes em smartphone):
```
http://localhost:8080/consent.html?challengeId=<ID_DO_DESAFIO>
```

---

## 🐳 Executando via Docker

```bash
docker build -t guardrail-fido-server:latest .
docker run -p 8080:8080 guardrail-fido-server:latest
```
