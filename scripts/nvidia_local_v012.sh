#!/bin/bash
# NVIDIA Riva NIM - Script para levantar parakeet-ctc-0.6b-es localmente
#
# Uso:
#   1. Genera API key en https://build.nvidia.com/
#   2. Exporta: export NGC_API_KEY=<tu_api_key>
#   3. Ejecuta: bash scripts/nvidia_local.sh

echo "=================================="
echo "NVIDIA Riva NIM - Parakeet CTC 0.6b ES"
echo "=================================="

# Verificar API key
if [ -z "$NGC_API_KEY" ]; then
    echo "ERROR: NGC_API_KEY no está configurada"
    echo ""
    echo "Pasos:"
    echo "1. Ve a https://build.nvidia.com/"
    echo "2. Genera una API key"
    echo "3. Ejecuta: export NGC_API_KEY=<tu_api_key>"
    echo ""
    exit 1
fi

echo "✓ NGC_API_KEY detectada"

# Login en NVIDIA container registry
echo ""
echo "Login en nvcr.io..."
echo "$NGC_API_KEY" | docker login nvcr.io --username oauth --password-stdin

if [ $? -ne 0 ]; then
    echo "ERROR: Login falló. Verifica tu API key"
    exit 1
fi

echo "✓ Login exitoso"

# Verificar NVIDIA GPU
echo ""
echo "Verificando NVIDIA GPU..."
if ! command -v nvidia-smi &> /dev/null; then
    echo "ERROR: nvidia-smi no encontrado. ¿Tienes NVIDIA GPU instalada?"
    echo ""
    echo "Requisitos:"
    echo "  - NVIDIA GPU con soporte CUDA"
    echo "  - NVIDIA Driver instalado"
    echo "  - Docker con runtime nvidia"
    echo ""
    exit 1
fi

nvidia-smi --query-gpu=name --format=csv,noheader
echo "✓ GPU detectada"

# Parar contenedor anterior si existe
echo ""
echo "Limpiando contenedores anteriores..."
docker stop parakeet-ctc-0.6b-es 2>/dev/null || true
docker rm parakeet-ctc-0.6b-es 2>/dev/null || true

# Levantar contenedor
echo ""
echo "Levantando contenedor NVIDIA Riva NIM..."
echo "Esto puede tomar hasta 30 minutos la primera vez..."

docker run -d \
  --name parakeet-ctc-0.6b-es \
  --runtime=nvidia \
  --gpus '"device=0"' \
  --shm-size=8GB \
  -e NGC_API_KEY="$NGC_API_KEY" \
  -e NIM_HTTP_API_PORT=9000 \
  -e NIM_GRPC_API_PORT=50051 \
  -p 9000:9000 \
  -p 50051:50051 \
  -e NIM_TAGS_SELECTOR=mode=str,vad=silero,diarizer=sortformer \
  nvcr.io/nim/nvidia/parakeet-ctc-0.6b-es:latest

if [ $? -ne 0 ]; then
    echo "ERROR: Contenedor falló al iniciar"
    exit 1
fi

echo "✓ Contenedor iniciado"

# Esperar a que el servicio esté listo
echo ""
echo "Esperando a que el servicio esté listo (puede tardar varios minutos)..."
echo "Puedes monitorear con: docker logs -f parakeet-ctc-0.6b-es"

MAX_WAIT=1800  # 30 minutos
WAIT_TIME=0
while [ $WAIT_TIME -lt $MAX_WAIT ]; do
    if curl -s http://localhost:9000/v1/health/ready | grep -q '"ready":true'; then
        echo ""
        echo "=================================="
        echo "✓ ¡Servicio listo!"
        echo "=================================="
        echo ""
        echo "Servicios disponibles:"
        echo "  - HTTP API: http://localhost:9000"
        echo "  - gRPC API: localhost:50051"
        echo ""
        echo "Logs en tiempo real:"
        echo "  docker logs -f parakeet-ctc-0.6b-es"
        echo ""
        echo "Detener:"
        echo "  docker stop parakeet-ctc-0.6b-es"
        echo ""
        exit 0
    fi

    sleep 10
    WAIT_TIME=$((WAIT_TIME + 10))
    echo -n "."
done

echo ""
echo "ERROR: Timeout esperando el servicio"
echo "Verifica los logs: docker logs parakeet-ctc-0.6b-es"
exit 1
