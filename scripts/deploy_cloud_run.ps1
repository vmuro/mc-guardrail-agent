# ==============================================================================
# GuardrailAI - Script de Deploy Automatizado no Google Cloud Run Jobs (PowerShell)
# ==============================================================================
param (
    [string]$ProjectId = $(gcloud config get-value project 2>$null),
    [string]$Region = "us-central1",
    [string]$RepoName = "guardrail-artifacts",
    [string]$JobName = "guardrail-agent-job",
    [string]$ImageTag = "latest",
    [string]$BuildMethod = "cloud-build" # "cloud-build" ou "docker"
)

$ErrorActionPreference = "Stop"

if (-not $ProjectId) {
    $ProjectId = "gft-brazil-bu-gcp"
}

Write-Host "==============================================================================" -ForegroundColor Cyan
Write-Host "🚀  GUARDRAIL-AI: DEPLOY NO GOOGLE CLOUD RUN JOBS (PowerShell)               " -ForegroundColor Cyan
Write-Host "==============================================================================" -ForegroundColor Cyan

# 1. Verificação de Pré-requisitos
Write-Host "`n🔍 [1/6] Verificando ferramentas e autenticação no Google Cloud..." -ForegroundColor Blue

if (-not (Get-Command gcloud -ErrorAction SilentlyContinue)) {
    Write-Error "❌ Erro: Google Cloud SDK ('gcloud') não está instalado ou no PATH."
}

Write-Host "   -> GCP Project ID: $ProjectId" -ForegroundColor Green
Write-Host "   -> Região: $Region" -ForegroundColor Green

gcloud config set project $ProjectId --quiet

# 2. Habilitação de APIs
Write-Host "`n⚙️ [2/6] Garantindo que as APIs do Google Cloud estejam habilitadas..." -ForegroundColor Blue
$apis = @(
    "run.googleapis.com",
    "artifactregistry.googleapis.com",
    "cloudbuild.googleapis.com",
    "aiplatform.googleapis.com",
    "cloudscheduler.googleapis.com",
    "logging.googleapis.com"
)

foreach ($api in $apis) {
    Write-Host "   - Habilitando API: $api..."
    gcloud services enable $api --quiet
}

# 3. Artifact Registry
Write-Host "`n📦 [3/6] Verificando repositório no Artifact Registry ($RepoName)..." -ForegroundColor Blue
$repoCheck = gcloud artifacts repositories describe $RepoName --location=$Region 2>$null
if (-not $repoCheck) {
    Write-Host "   -> Criando repositório '$RepoName' na região '$Region'..."
    gcloud artifacts repositories create $RepoName `
        --repository-format=docker `
        --location=$Region `
        --description="Repositório Docker para o GuardrailAI" `
        --quiet
} else {
    Write-Host "   -> Repositório '$RepoName' já existe."
}

$imageUri = "$Region-docker.pkg.dev/$ProjectId/$RepoName/${JobName}:$ImageTag"
Write-Host "   -> Imagem Alvo: $imageUri" -ForegroundColor Cyan

# 4. Build e Push
Write-Host "`n🔨 [4/6] Construindo imagem do container (Método: $BuildMethod)..." -ForegroundColor Blue
if ($BuildMethod -eq "docker") {
    gcloud auth configure-docker "$Region-docker.pkg.dev" --quiet
    docker build -t $imageUri .
    docker push $imageUri
} else {
    gcloud builds submit --tag $imageUri . --quiet
}

# 5. Deploy do Cloud Run Job
Write-Host "`n🚀 [5/6] Implantando o Cloud Run Job ($JobName)..." -ForegroundColor Blue
gcloud run jobs deploy $JobName `
    --image=$imageUri `
    --region=$Region `
    --set-env-vars="CLIENTS_CONFIG_FILE=config/clients.json,PROJECT_ID=$ProjectId,LOCATION=$Region" `
    --max-retries=1 `
    --task-timeout=600s `
    --memory=1Gi `
    --cpu=1 `
    --quiet

Write-Host "✅ Cloud Run Job '$JobName' implantado com sucesso!" -ForegroundColor Green

# 6. Resumo
Write-Host "`n📋 [6/6] Resumo da Implantação:" -ForegroundColor Blue
Write-Host "------------------------------------------------------------------------------" -ForegroundColor Cyan
Write-Host "• Job Name: $JobName" -ForegroundColor Green
Write-Host "• Imagem:   $imageUri" -ForegroundColor Green
Write-Host "• Região:   $Region" -ForegroundColor Green
Write-Host "------------------------------------------------------------------------------" -ForegroundColor Cyan
Write-Host "`n👉 Para executar o Job manualmente agora no GCP:" -ForegroundColor Yellow
Write-Host "   gcloud run jobs execute $JobName --region=$Region"
