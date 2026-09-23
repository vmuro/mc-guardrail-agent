#!/usr/bin/env bash
set -euo pipefail

# ==============================================================================
# CONFIGURAÇÕES GERAIS
# ==============================================================================
PROJECT_ID="${PROJECT_ID:-gft-brazil-bu-gcp}"
REGION="${REGION:-us-central1}"
REPO_NAME="${REPO_NAME:-repo-guardrailai}"

FIDO_SERVICE_NAME="fido-consent-server"
AGENT_JOB_NAME="guardrail-agent-job"

echo "================================================================="
echo "🚀 Deploy GuardrailAI no Google Cloud Platform"
echo "   Projeto: $PROJECT_ID | Região: $REGION"
echo "   Artifact Registry: $REPO_NAME"
echo "================================================================="

# 1. Configurar autenticação Docker -> Artifact Registry
echo "🔑 [1/4] Autenticando Docker com GCP..."
gcloud auth print-access-token | docker login -u oauth2accesstoken --password-stdin "https://${REGION}-docker.pkg.dev"

REGISTRY_BASE="${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPO_NAME}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

if [ -d "$REPO_ROOT/agent-python" ]; then
    AGENT_DIR="$REPO_ROOT/agent-python"
else
    AGENT_DIR="$REPO_ROOT"
fi

# 2. Build & Push do FIDO Consent Server
echo ""
echo "🌐 [2/4] Verificando FIDO Consent Server..."
FIDO_IMAGE="${REGISTRY_BASE}/fido-server:latest"

if [ -d "$REPO_ROOT/fido-server" ]; then
    echo "🔨 [Docker Build] FIDO Server..."
    docker build -t "$FIDO_IMAGE" "$REPO_ROOT/fido-server"
    echo "⬆️ [Docker Push] Enviando imagem FIDO..."
    docker push "$FIDO_IMAGE"

    echo "🚀 [Cloud Run] Atualizando FIDO Server..."
    gcloud run deploy "$FIDO_SERVICE_NAME" \
        --image="$FIDO_IMAGE" \
        --region="$REGION" \
        --platform=managed \
        --allow-unauthenticated \
        --set-env-vars="PROJECT_ID=${PROJECT_ID},LOCATION=${REGION}" \
        --project="$PROJECT_ID"
else
    echo "ℹ️ Diretório fido-server não encontrado. Mantendo serviço existente."
fi

# Obter a URL pública do FIDO Server
FIDO_URL=$(gcloud run services describe "$FIDO_SERVICE_NAME" --region="$REGION" --format='value(status.url)' --project="$PROJECT_ID" 2>/dev/null || echo "http://localhost:8080")
echo "   🔗 URL FIDO: $FIDO_URL"

# 3. Build & Push do Guardrail Agent (Python)
echo ""
echo "🤖 [3/4] Processando Guardrail Agent a partir de: $AGENT_DIR..."
AGENT_IMAGE="${REGISTRY_BASE}/guardrail-agent:latest"

echo "🔨 [Docker Build] Guardrail Agent..."
docker build -t "$AGENT_IMAGE" "$AGENT_DIR"

echo "⬆️ [Docker Push] Enviando imagem Agent..."
docker push "$AGENT_IMAGE"

# 4. Deploy do Cloud Run Job
echo ""
echo "⚙️ [4/4] Deploying Guardrail Agent Job..."
gcloud run jobs deploy "$AGENT_JOB_NAME" \
    --image="$AGENT_IMAGE" \
    --region="$REGION" \
    --set-env-vars="PROJECT_ID=${PROJECT_ID},LOCATION=${REGION},SPRING_FIDO_BASE_URL=${FIDO_URL},FIDO_BASE_URL=${FIDO_URL},MODEL_NAME=gemini-2.5-flash" \
    --max-retries=1 \
    --task-timeout=600s \
    --project="$PROJECT_ID"

echo ""
echo "================================================================="
echo "✅ DEPLOY FINALIZADO COM SUCESSO!"
echo "================================================================="
echo "Para executar o Job manualmente:"
echo "  gcloud run jobs execute $AGENT_JOB_NAME --region=$REGION --project=$PROJECT_ID"
echo "================================================================="
