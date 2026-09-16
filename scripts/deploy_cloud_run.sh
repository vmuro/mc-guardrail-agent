#!/usr/bin/env bash
# ==============================================================================
# GuardrailAI - Script de Deploy Automatizado no Google Cloud Run Jobs
# ==============================================================================
set -e

# Cores para terminal
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

echo -e "${CYAN}==============================================================================${NC}"
echo -e "${CYAN}🚀  GUARDRAIL-AI: DEPLOY NO GOOGLE CLOUD RUN JOBS                            ${NC}"
echo -e "${CYAN}==============================================================================${NC}"

# 1. Configurações Padrão (podem ser sobrescritas por variáveis de ambiente)
DEFAULT_PROJECT_ID=$(gcloud config get-value project 2>/dev/null || echo "gft-brazil-bu-gcp")
PROJECT_ID=${PROJECT_ID:-$DEFAULT_PROJECT_ID}
REGION=${REGION:-"us-central1"}
REPO_NAME=${REPO_NAME:-"guardrail-artifacts"}
JOB_NAME=${JOB_NAME:-"guardrail-agent-job"}
IMAGE_TAG=${IMAGE_TAG:-"latest"}
BUILD_METHOD=${BUILD_METHOD:-"cloud-build"} # "cloud-build" ou "docker"

# 2. Verificação de Pré-requisitos
echo -e "\n🔍 ${BLUE}[1/6] Verificando ferramentas e autenticação no Google Cloud...${NC}"

if ! command -v gcloud &> /dev/null; then
    echo -e "${RED}❌ Erro: Google Cloud SDK ('gcloud') não está instalado ou no PATH.${NC}"
    exit 1
fi

CURRENT_AUTH=$(gcloud auth list --filter=status:ACTIVE --format="value(account)" 2>/dev/null || echo "")
if [ -z "$CURRENT_AUTH" ]; then
    echo -e "${YELLOW}⚠️ Nenhuma conta ativa encontrada no gcloud. Executando login...${NC}"
    gcloud auth login
fi

echo -e "   -> Conta Ativa: ${GREEN}$(gcloud auth list --filter=status:ACTIVE --format="value(account)")${NC}"
echo -e "   -> GCP Project ID: ${GREEN}${PROJECT_ID}${NC}"
echo -e "   -> Região: ${GREEN}${REGION}${NC}"

gcloud config set project "${PROJECT_ID}" --quiet

# 3. Habilitação das APIs Necessárias
echo -e "\n⚙️ ${BLUE}[2/6] Garantindo que as APIs do Google Cloud estejam habilitadas...${NC}"
APIS=(
    "run.googleapis.com"
    "artifactregistry.googleapis.com"
    "cloudbuild.googleapis.com"
    "aiplatform.googleapis.com"
    "cloudscheduler.googleapis.com"
    "logging.googleapis.com"
)

for API in "${APIS[@]}"; do
    echo -e "   - Habilitando API: ${API}..."
    gcloud services enable "$API" --quiet
done

# 4. Criação do Repositório no Artifact Registry (se não existir)
echo -e "\n📦 ${BLUE}[3/6] Verificando repositório no Artifact Registry (${REPO_NAME})...${NC}"
if ! gcloud artifacts repositories describe "${REPO_NAME}" --location="${REGION}" &> /dev/null; then
    echo -e "   -> Criando repositório '${REPO_NAME}' na região '${REGION}'..."
    gcloud artifacts repositories create "${REPO_NAME}" \
        --repository-format=docker \
        --location="${REGION}" \
        --description="Repositório Docker para o GuardrailAI" \
        --quiet
else
    echo -e "   -> Repositório '${REPO_NAME}' já existe."
fi

IMAGE_URI="${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPO_NAME}/${JOB_NAME}:${IMAGE_TAG}"
echo -e "   -> Imagem Alvo: ${CYAN}${IMAGE_URI}${NC}"

# 5. Build e Push da Imagem do Container
echo -e "\n🔨 ${BLUE}[4/6] Construindo imagem do container (Método: ${BUILD_METHOD})...${NC}"

if [ "$BUILD_METHOD" == "docker" ]; then
    echo -e "   -> Configurando autenticação do Docker..."
    gcloud auth configure-docker "${REGION}-docker.pkg.dev" --quiet
    
    echo -e "   -> Executando docker build..."
    docker build -t "${IMAGE_URI}" .
    
    echo -e "   -> Executando docker push..."
    docker push "${IMAGE_URI}"
else
    # Build remoto no Cloud Build (não depende do daemon do Docker local)
    echo -e "   -> Submetendo build ao Google Cloud Build..."
    gcloud builds submit --tag "${IMAGE_URI}" . --quiet
fi

# 6. Deploy do Cloud Run Job
echo -e "\n🚀 ${BLUE}[5/6] Implantando o Cloud Run Job (${JOB_NAME})...${NC}"
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

# 7. Resumo e Próximos Passos
echo -e "\n📋 ${BLUE}[6/6] Resumo da Implantação e Comandos Úteis:${NC}"
echo -e "${CYAN}------------------------------------------------------------------------------${NC}"
echo -e "• Job Name: ${GREEN}${JOB_NAME}${NC}"
echo -e "• Imagem:   ${GREEN}${IMAGE_URI}${NC}"
echo -e "• Região:   ${GREEN}${REGION}${NC}"
echo -e "${CYAN}------------------------------------------------------------------------------${NC}"
echo -e "\n👉 ${YELLOW}Para executar o Job manualmente agora no GCP:${NC}"
echo -e "   gcloud run jobs execute ${JOB_NAME} --region=${REGION}"
echo -e "\n👉 ${YELLOW}Para agendar execução diária com o Cloud Scheduler (ex: 09:30 BRT):${NC}"
echo -e "   gcloud scheduler jobs create http trigger-${JOB_NAME} \\"
echo -e "     --schedule=\"30 9 * * 1-5\" \\"
echo -e "     --time-zone=\"America/Sao_Paulo\" \\"
echo -e "     --uri=\"https://${REGION}-run.googleapis.com/v1/namespaces/${PROJECT_ID}/jobs/${JOB_NAME}:run\" \\"
echo -e "     --http-method=POST \\"
echo -e "     --oauth-service-account-email=\"\$(gcloud config get-value account)\""
echo -e "\n${GREEN}🎉 Deploy finalizado com sucesso!${NC}"
