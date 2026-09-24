#!/usr/bin/env bash
set -euo pipefail

# ==============================================================================
# CONFIGURAÇÕES GERAIS
# ==============================================================================
PROJECT_ID="${PROJECT_ID:-gft-brazil-bu-gcp}"
REGION="${REGION:-us-central1}"
REPO_NAME="${REPO_NAME:-repo-guardrailai}"

FIDO_SERVICE_NAME="fido-consent-server"
AGENT_SERVICE_NAME="guardrail-agent-service"
AGENT_JOB_NAME="guardrail-agent-job"
SERVICE_ACCOUNT="${SERVICE_ACCOUNT:-sa-guardrail-agent@${PROJECT_ID}.iam.gserviceaccount.com}"


echo "================================================================="
echo "🚀 Deploy GuardrailAI no Google Cloud Platform"
echo "   Projeto: $PROJECT_ID | Região: $REGION"
echo "   Artifact Registry: $REPO_NAME"
echo "   Service Account:   $SERVICE_ACCOUNT"
echo "================================================================="

# 1. Configurar autenticação Docker -> Artifact Registry
echo "🔑 [1/5] Autenticando Docker com GCP..."
gcloud auth print-access-token | docker login -u oauth2accesstoken --password-stdin "https://${REGION}-docker.pkg.dev"

REGISTRY_BASE="${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPO_NAME}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

if [ -d "$REPO_ROOT/agent-python" ]; then
    AGENT_DIR="$REPO_ROOT/agent-python"
else
    AGENT_DIR="$REPO_ROOT"
fi

# 2. Build & Push do Guardrail Agent (Python)
echo ""
echo "🤖 [2/5] Processando Guardrail Agent a partir de: $AGENT_DIR..."
AGENT_IMAGE="${REGISTRY_BASE}/guardrail-agent:latest"

echo "🔨 [Docker Build] Guardrail Agent..."
docker build -t "$AGENT_IMAGE" "$AGENT_DIR"

echo "⬆️ [Docker Push] Enviando imagem Agent..."
docker push "$AGENT_IMAGE"

# 3. Deploy do Guardrail Agent como Cloud Run Service (API de Governança / Avaliação)
echo ""
echo "🚀 [3/5] Deploying Guardrail Agent Service no Cloud Run..."
gcloud run deploy "$AGENT_SERVICE_NAME" \
    --image="$AGENT_IMAGE" \
    --region="$REGION" \
    --platform=managed \
    --port=8000 \
    --service-account="$SERVICE_ACCOUNT" \
    --set-env-vars="PROJECT_ID=${PROJECT_ID},LOCATION=${REGION},MODEL_NAME=gemini-2.5-flash" \
    --project="$PROJECT_ID"

AGENT_SERVICE_URL=$(gcloud run services describe "$AGENT_SERVICE_NAME" --region="$REGION" --format='value(status.url)' --project="$PROJECT_ID")
echo "   🔗 URL Agent Service: $AGENT_SERVICE_URL"

# 4. Build & Push do FIDO Consent Server
echo ""
echo "🌐 [4/5] Verificando FIDO Consent Server..."
FIDO_IMAGE="${REGISTRY_BASE}/fido-server:latest"

if [ -d "$REPO_ROOT/fido-server" ]; then
    echo "🔨 [Docker Build] FIDO Server..."
    docker build -t "$FIDO_IMAGE" "$REPO_ROOT/fido-server"
    echo "⬆️ [Docker Push] Enviando imagem FIDO..."
    docker push "$FIDO_IMAGE"

    echo "🚀 [Cloud Run] Atualizando FIDO Server integrado ao Agent Python..."
    gcloud run deploy "$FIDO_SERVICE_NAME" \
        --image="$FIDO_IMAGE" \
        --region="$REGION" \
        --platform=managed \
        --service-account="$SERVICE_ACCOUNT" \
        --set-env-vars="PROJECT_ID=${PROJECT_ID},LOCATION=${REGION},AGENT_PYTHON_URL=${AGENT_SERVICE_URL}" \
        --project="$PROJECT_ID"
else
    echo "ℹ️ Diretório fido-server não encontrado. Mantendo serviço existente e configurando AGENT_PYTHON_URL..."
    gcloud run services update "$FIDO_SERVICE_NAME" \
        --region="$REGION" \
        --update-env-vars="AGENT_PYTHON_URL=${AGENT_SERVICE_URL}" \
        --project="$PROJECT_ID"
fi

# Obter a URL pública do FIDO Server
FIDO_URL=$(gcloud run services describe "$FIDO_SERVICE_NAME" --region="$REGION" --format='value(status.url)' --project="$PROJECT_ID" 2>/dev/null || echo "http://localhost:8080")
echo "   🔗 URL FIDO: $FIDO_URL"

# Atualizar Agent Service com a URL pública do FIDO Server para desafios de consentimento
echo "🔄 Atualizando referências do FIDO no Agent Service..."
gcloud run services update "$AGENT_SERVICE_NAME" \
    --region="$REGION" \
    --update-env-vars="SPRING_FIDO_BASE_URL=${FIDO_URL},FIDO_BASE_URL=${FIDO_URL}" \
    --project="$PROJECT_ID"

# 5. Deploy do Cloud Run Job (Batch)
echo ""
echo "⚙️ [5/5] Deploying Guardrail Agent Job..."
gcloud run jobs deploy "$AGENT_JOB_NAME" \
    --image="$AGENT_IMAGE" \
    --region="$REGION" \
    --command="python" \
    --args="src/main.py" \
    --service-account="$SERVICE_ACCOUNT" \
    --set-env-vars="PROJECT_ID=${PROJECT_ID},LOCATION=${REGION},SPRING_FIDO_BASE_URL=${FIDO_URL},FIDO_BASE_URL=${FIDO_URL},MODEL_NAME=gemini-2.5-flash" \
    --max-retries=1 \
    --task-timeout=600s \
    --project="$PROJECT_ID"

echo ""
echo "================================================================="
echo "✅ DEPLOY FINALIZADO COM SUCESSO!"
echo "================================================================="
echo "Interface Web de Avaliação: ${FIDO_URL}/evaluate.html"
echo "Tela de Consentimento:     ${FIDO_URL}/consent.html"
echo "API Agent Python:          ${AGENT_SERVICE_URL}/docs"
echo "================================================================="
echo "Para executar o Job Batch manualmente:"
echo "  gcloud run jobs execute $AGENT_JOB_NAME --region=$REGION --project=$PROJECT_ID"
echo "================================================================="
