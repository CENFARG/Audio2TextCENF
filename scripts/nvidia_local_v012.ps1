# NVIDIA Riva NIM - Script para Windows PowerShell
# Uso:
#   1. Genera API key en https://build.nvidia.com/
#   2. $env:NGC_API_KEY = "<tu_api_key>"
#   3. powershell -ExecutionPolicy Bypass -File scripts/nvidia_local.ps1

Write-Host "=================================="  -ForegroundColor Cyan
Write-Host "NVIDIA Riva NIM - Parakeet CTC 0.6b ES" -ForegroundColor Cyan
Write-Host "=================================="  -ForegroundColor Cyan
Write-Host ""

# Verificar API key
if (-not $env:NGC_API_KEY) {
    Write-Host "ERROR: NGC_API_KEY no está configurada" -ForegroundColor Red
    Write-Host ""
    Write-Host "Pasos:"
    Write-Host "1. Ve a https://build.nvidia.com/"
    Write-Host "2. Genera una API key"
    Write-Host "3. Ejecuta: `$env:NGC_API_KEY = '<tu_api_key>'`"
    Write-Host ""
    exit 1
}

Write-Host "✓ NGC_API_KEY detectada" -ForegroundColor Green

# Verificar Docker
Write-Host ""
Write-Host "Verificando Docker..."
docker version | Out-Null
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Docker no está corriendo" -ForegroundColor Red
    Write-Host "Inicia Docker Desktop primero"
    exit 1
}

# Verificar NVIDIA GPU
Write-Host ""
Write-Host "Verificando NVIDIA GPU..."
nvidia-smi | Out-Null
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: nvidia-smi no encontrado. ¿Tienes NVIDIA GPU?" -ForegroundColor Red
    Write-Host ""
    Write-Host "Requisitos:"
    Write-Host "  - NVIDIA GPU con soporte CUDA"
    Write-Host "  - NVIDIA Driver instalado"
    Write-Host "  - Docker Desktop con soporte NVIDIA"
    Write-Host ""
    exit 1
}

$gpuName = nvidia-smi --query-gpu=name --format=csv,noheader
Write-Host "✓ GPU detectada: $gpuName" -ForegroundColor Green

# Login en NVIDIA container registry
Write-Host ""
Write-Host "Login en nvcr.io..."
$env:NGC_API_KEY | docker login nvcr.io --username oauth --password-stdin

if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Login falló. Verifica tu API key" -ForegroundColor Red
    exit 1
}

Write-Host "✓ Login exitoso" -ForegroundColor Green

# Parar contenedor anterior si existe
Write-Host ""
Write-Host "Limpiando contenedores anteriores..."
docker stop parakeet-ctc-0.6b-es 2>$null | Out-Null
docker rm parakeet-ctc-0.6b-es 2>$null | Out-Null

# Levantar contenedor
Write-Host ""
Write-Host "Levantando contenedor NVIDIA Riva NIM..." -ForegroundColor Yellow
Write-Host "Esto puede tomar hasta 30 minutos la primera vez..." -ForegroundColor Yellow

docker run -d `
  --name parakeet-ctc-0.6b-es `
  --runtime=nvidia `
  --gpus '"device=0"' `
  --shm-size=8GB `
  -e NGC_API_KEY=$env:NGC_API_KEY `
  -e NIM_HTTP_API_PORT=9000 `
  -e NIM_GRPC_API_PORT=50051 `
  -p 9000:9000 `
  -p 50051:50051 `
  -e NIM_TAGS_SELECTOR=mode=str,vad=silero,diarizer=sortformer `
  nvcr.io/nim/nvidia/parakeet-ctc-0.6b-es:latest

if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Contenedor falló al iniciar" -ForegroundColor Red
    exit 1
}

Write-Host "✓ Contenedor iniciado" -ForegroundColor Green

# Esperar a que el servicio esté listo
Write-Host ""
Write-Host "Esperando a que el servicio esté listo..." -ForegroundColor Yellow
Write-Host "Puedes monitorear con: docker logs -f parakeet-ctc-0.6b-es" -ForegroundColor Cyan

$MAX_WAIT = 1800  # 30 minutos
$WAIT_TIME = 0
$READY = $false

while ($WAIT_TIME -lt $MAX_WAIT -and -not $READY) {
    try {
        $response = Invoke-RestMethod -Uri "http://localhost:9000/v1/health/ready" -TimeoutSec 5
        if ($response.ready -eq $true) {
            $READY = $true
        }
    } catch {
        # Servicio no está listo aún
    }

    if (-not $READY) {
        Start-Sleep -Seconds 10
        $WAIT_TIME += 10
        Write-Host "." -NoNewline
    }
}

Write-Host ""

if ($READY) {
    Write-Host "=================================="  -ForegroundColor Green
    Write-Host "✓ ¡Servicio listo!" -ForegroundColor Green
    Write-Host "=================================="  -ForegroundColor Green
    Write-Host ""
    Write-Host "Servicios disponibles:" -ForegroundColor Cyan
    Write-Host "  - HTTP API: http://localhost:9000" -ForegroundColor White
    Write-Host "  - gRPC API: localhost:50051" -ForegroundColor White
    Write-Host ""
    Write-Host "Comandos útiles:" -ForegroundColor Cyan
    Write-Host "  Ver logs: docker logs -f parakeet-ctc-0.6b-es" -ForegroundColor White
    Write-Host "  Detener: docker stop parakeet-ctc-0.6b-es" -ForegroundColor White
    Write-Host ""
} else {
    Write-Host "ERROR: Timeout esperando el servicio" -ForegroundColor Red
    Write-Host "Verifica los logs: docker logs parakeet-ctc-0.6b-es" -ForegroundColor Yellow
    exit 1
}
