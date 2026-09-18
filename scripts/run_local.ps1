# ==============================================================================
# GuardrailAI - Execução Local Conjunta no Windows (PowerShell)
# ==============================================================================
$ErrorActionPreference = "Stop"

Write-Host "==============================================================================" -ForegroundColor Cyan
Write-Host "🚀  GUARDRAIL-AI: INICIANDO SERVIÇOS EM AMBIENTE LOCAL (WINDOWS)              " -ForegroundColor Cyan
Write-Host "==============================================================================" -ForegroundColor Cyan

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RootDir = Split-Path -Parent $ScriptDir
$FidoDir = Join-Path $RootDir "fido-server"
$AgentDir = Join-Path $RootDir "agent-python"

# 1. Iniciar Servidor FIDO em nova janela de processo
Write-Host "`n☕ [1/2] Iniciando Servidor FIDO Spring Boot (Porta 8080)..." -ForegroundColor Yellow
$FidoProcess = Start-Process -FilePath "cmd.exe" -ArgumentList "/c cd /d `"$FidoDir`" && mvnw.cmd spring-boot:run" -PassThru

Write-Host "   -> Servidor FIDO iniciado no processo ID $($FidoProcess.Id)" -ForegroundColor Green
Write-Host "   -> Aguardando 10 segundos para inicialização do Spring Boot..." -ForegroundColor Gray
Start-Sleep -Seconds 10

# 2. Executar Agente Python
Write-Host "`n🐍 [2/2] Executando Agente de Governança Python..." -ForegroundColor Yellow
Push-Location $AgentDir

if (Test-Path ".venv\Scripts\Activate.ps1") {
    & .venv\Scripts\Activate.ps1
} elseif (Test-Path "..\.venv\Scripts\Activate.ps1") {
    & ..\.venv\Scripts\Activate.ps1
}

python src/main.py --config ..\config\clients.json
Pop-Location

Write-Host "`n✅ Execução do Agente concluída!" -ForegroundColor Green
Write-Host "💡 O Servidor FIDO permanece ativo na janela do terminal. Feche a janela para encerrá-lo." -ForegroundColor Yellow
