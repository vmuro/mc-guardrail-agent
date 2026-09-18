#!/usr/bin/env bash
# ==============================================================================
# GuardrailAI - Script Oficial de Deploy no Google Cloud Run Jobs
# ==============================================================================
set -e

# Cores para terminal
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

echo -e "${CYAN}==============================================================================${NC}"
echo -e "${CYAN}🚀  GUARDRAIL-AI: DEPLOY OFICIAL NO GOOGLE CLOUD RUN JOBS                    ${NC}"
echo -e "${CYAN}==============================================================================${NC}"

# 1. Configurações Oficiais do Projeto da Equipe
PROJECT_ID=${PROJECT_ID:-"gft-brazil-bu-gcp"}
REGION=${REGION:-"us-central1"}
REPO_NAME=${REPO_NAME:-"repo-guardrailai"}
IMAGE_NAME=${IMAGE_NAME:-"guardrail-agent"}
JOB_NAME=${JOB_NAME:-"guardrail-agent-job"}
EMAIL_ACCOUNT=${EMAIL_ACCOUNT:-"658856974250-compute@developer.gserviceaccount.com"}
IMAGE_TAG=${IMAGE_TAG:-"latest"}
BUILD_METHOD=${BUILD_METHOD:-"docker"} # "docker" (local) ou "cloud-build" (remoto)


IMAGE_URI="${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPO_NAME}/${IMAGE_NAME}:${IMAGE_TAG}"

echo -e "   -> Projeto GCP:   ${GREEN}${PROJECT_ID}${NC}"
echo -e "   -> Região:        ${GREEN}${REGION}${NC}"
echo -e "   -> Repositório:   ${GREEN}${REPO_NAME}${NC}"
echo -e "   -> Imagem Alvo:   ${CYAN}${IMAGE_URI}${NC}"
echo -e "   -> Cloud Run Job: ${GREEN}${JOB_NAME}${NC}"
echo -e "   -> Método Build:  ${YELLOW}${BUILD_METHOD}${NC}"

# 2. Verificação de Ferramentas
echo -e "\n🔍 ${BLUE}[1/5] Verificando autenticação no Google Cloud...${NC}"
if ! command -v gcloud &> /dev/null; then
    echo -e "${RED}❌ Erro: Google Cloud SDK ('gcloud') não está instalado ou no PATH.${NC}"
    exit 1
fi

gcloud config set project "${PROJECT_ID}" --quiet

# 3. Autenticação do Docker com o Artifact Registry
echo -e "\n🔑 ${BLUE}[2/5] Autenticando Docker com o Artifact Registry...${NC}"
gcloud auth configure-docker "${REGION}-docker.pkg.dev" --quiet

# 4. Build e Push da Imagem
echo -e "\n🔨 ${BLUE}[3/5] Construindo e enviando a imagem do container...${NC}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
AGENT_DIR="${ROOT_DIR}/agent-python"

if [ "$BUILD_METHOD" == "docker" ]; then
    echo -e "   -> Executando 'docker build' local a partir de agent-python..."
    docker build -t "${IMAGE_URI}" "${AGENT_DIR}"
    
    echo -e "   -> Executando 'docker push' para ${IMAGE_URI}..."
    docker push "${IMAGE_URI}"
else
    echo -e "   -> Submetendo build ao Google Cloud Build..."
    gcloud builds submit --tag "${IMAGE_URI}" "${AGENT_DIR}" --quiet
fi

# 5. Deploy do Cloud Run Job
echo -e "\n🚀 ${BLUE}[4/5] Implantando o Cloud Run Job no GCP...${NC}"
gcloud run jobs deploy "${JOB_NAME}" \
    --image="${IMAGE_URI}" \
    --region="${REGION}" \
    --set-env-vars="CLIENTS_CONFIG_FILE=config/clients.json,PROJECT_ID=${PROJECT_ID},LOCATION=${REGION}" \
    --max-retries=1 \
    --task-timeout=600s \
    --memory=1Gi \
    --cpu=1 \
    --quiet

echo -e "${GREEN}✅ Cloud Run Job '${JOB_NAME}' implantado com sucesso!${NC}"

# 6. Resumo e Comandos para Executar
echo -e "\n📋 ${BLUE}[5/5] Resumo da Implantação e Execução:${NC}"
echo -e "${CYAN}------------------------------------------------------------------------------${NC}"
echo -e "• Job Name:  ${GREEN}${JOB_NAME}${NC}"
echo -e "• Imagem:    ${GREEN}${IMAGE_URI}${NC}"
echo -e "• Região:    ${GREEN}${REGION}${NC}"
echo -e "${CYAN}------------------------------------------------------------------------------${NC}"
echo -e "\n👉 ${YELLOW}Para executar o Job agora no GCP:${NC}"
echo -e "   gcloud run jobs execute ${JOB_NAME} --region=${REGION}"
echo -e "\n👉 ${YELLOW}Para agendar via Cloud Scheduler (Segunda a Sexta às 09:30):${NC}"
echo -e "   gcloud scheduler jobs create http trigger-${JOB_NAME} \\"
echo -e "     --location=${REGION} \\"
echo -e "     --schedule=\"30 9 * * 1-5\" \\"
echo -e "     --time-zone=\"America/Sao_Paulo\" \\"
echo -e "     --uri=\"https://run.googleapis.com/v2/projects/${PROJECT_ID}/locations/${REGION}/jobs/${JOB_NAME}:run\" \\"
echo -e "     --http-method=POST \\"
echo -e "     --oauth-service-account-email=\"${EMAIL_ACCOUNT}\" \\"
echo -e "     --oauth-token-scope=\"https://www.googleapis.com/auth/cloud-platform\""
echo -e "\n${GREEN}🎉 Processo concluído com sucesso!${NC}"

