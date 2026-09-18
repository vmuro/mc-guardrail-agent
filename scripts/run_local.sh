#!/usr/bin/env bash
# ==============================================================================
# GuardrailAI - Execução Local Conjunta (FIDO Server + Agent Python)
# ==============================================================================
set -e

CYAN='\033[0;36m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${CYAN}==============================================================================${NC}"
echo -e "${CYAN}🚀  GUARDRAIL-AI: INICIANDO SERVIÇOS EM AMBIENTE LOCAL                        ${NC}"
echo -e "${CYAN}==============================================================================${NC}"

# 1. Iniciar Servidor FIDO (Java Spring Boot) em segundo plano
echo -e "\n☕ ${YELLOW}[1/2] Iniciando Servidor FIDO Spring Boot (Porta 8080)...${NC}"
cd "$(dirname "$0")/../fido-server"
chmod +x mvnw
./mvnw spring-boot:run > fido_server.log 2>&1 &
FIDO_PID=$!
echo -e "   -> FIDO Server iniciado com PID ${GREEN}${FIDO_PID}${NC} (logs em fido-server/fido_server.log)"

# Aguarda inicialização do Spring Boot
echo -e "   -> Aguardando FIDO Server responder em http://localhost:8080..."
for i in {1..30}; do
    if curl -s http://localhost:8080/api/consent/status/ping > /dev/null 2>&1 || curl -s -o /dev/null -w "%{http_code}" http://localhost:8080/consent.html | grep -q "200"; then
        echo -e "${GREEN}   -> FIDO Server online!${NC}"
        break
    fi
    sleep 1
done

# 2. Executar Agente Python
echo -e "\n🐍 ${YELLOW}[2/2] Executando Agente de Governança Python...${NC}"
cd "$(dirname "$0")/../agent-python"

if [ -d ".venv" ]; then
    source .venv/bin/activate
elif [ -d "../.venv" ]; then
    source ../.venv/bin/activate
fi

python src/main.py --config ../config/clients.json

echo -e "\n${GREEN}✅ Execução concluída com sucesso!${NC}"
echo -e "💡 Para encerrar o FIDO Server em segundo plano: kill ${FIDO_PID}"
