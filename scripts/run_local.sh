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
MODE="${1:-server}"
echo -e "\n🐍 ${YELLOW}[2/2] Iniciando Agente de Governança Python (${MODE})...${NC}"
cd "$(dirname "$0")/../agent-python"

if [ -d ".venv" ]; then
    source .venv/bin/activate
elif [ -d "venv" ]; then
    source venv/bin/activate
elif [ -d "../.venv" ]; then
    source ../.venv/bin/activate
elif [ -d "../venv" ]; then
    source ../venv/bin/activate
fi

if [ "$MODE" = "cli" ]; then
    python src/main.py --config ../config/clients.json
    echo -e "\n${GREEN}✅ Execução CLI concluída com sucesso!${NC}"
    echo -e "💡 Para encerrar o FIDO Server em segundo plano: kill ${FIDO_PID}"
else
    echo -e "   -> Servidor de Governança Python ativo na porta 8000."
    echo -e "   -> ${CYAN}Acesse a interface web de avaliação em:${NC} ${GREEN}http://localhost:8080/evaluate.html${NC}"
    echo -e "   -> ${CYAN}Tela de consentimento:${NC} ${GREEN}http://localhost:8080/consent.html${NC}"
    python src/server.py
fi

