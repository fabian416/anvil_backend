#!/bin/bash

# Leer IMAGE_TAG del .env
if [ -f .env ]; then
    IMAGE_TAG=$(grep "^IMAGE_TAG=" .env | cut -d'=' -f2)
    echo "✓ Usando tag del .env: $IMAGE_TAG"
else
    IMAGE_TAG="infra"
    echo "⚠️  .env no encontrado, usando tag: $IMAGE_TAG"
fi

echo "=== DIAGNOSTICO DE PULL DE IMAGENES ==="
echo ""

# 1. Test de velocidad de descarga de una imagen
echo "1. Bajando UNA imagen para medir velocidad..."
time docker pull ghcr.io/lucholeonel/anvil-backend-api:${IMAGE_TAG}

echo ""
echo "2. Verificando compartición de capas..."
docker images --format "table {{.Repository}}\t{{.Tag#!/bin/bash

# Script para bajar imágenes con control de concurrencia
# Uso: bash pull_images.sh [número_paralelo]
# Ejemplo: bash pull_images.sh 3  (baja 3 imágenes a la vez)

PARALLEL=${1:-3}  # Default: 3 imágenes simultáneas

# Leer IMAGE_TAG del .env
if [ -f .env ]; then
    IMAGE_TAG=$(grep "^IMAGE_TAG=" .env | cut -d'=' -f2)
    echo "✓ Leyendo .env: IMAGE_TAG=$IMAGE_TAG"
else
    echo "⚠️  WARNING: .env no encontrado, usando tag por defecto"
    IMAGE_TAG="infra"
fi

echo "=== PULL DE IMAGENES OPTIMIZADAS ==="
echo "Tag a descargar: $IMAGE_TAG"
echo "Concurrencia: $PARALLEL imágenes a la vez"
echo "Tamaño total estimado: ~7-8GB"
echo ""

export IMAGE_TAG

# Lista de todos los servicios
SERVICES=(
    "postgres"
    "redis"
    "fastapi"
    "celery-worker"
    "celery-beat"
    "celery-worker-agents"
    "celery-worker-transactions"
    "celery-worker-graph"
    "celery-worker-distillation"
    "celery-worker-projects"
    "celery-worker-llm"
    "celery-worker-maintenance"
    "celery-worker-risk"
    "celery-worker-email"
    "mcp-1inch"
    "mcp-defillama"
    "mcp-thegraph"
    "mcp-coingecko"
    "mcp-aave"
    "mcp-portfolio"
    "mcp-perplexity"
    "mcp-morpho"
    "mcp-curve"
    "mcp-hyperliquid"
    "mcp-layerzero"
    "tx-confirmation"
)

TOTAL=${#SERVICES[@]}
CURRENT=0

echo "Total de servicios: $TOTAL"
echo ""

# Función para hacer pull de un servicio
pull_service() {
    local service=$1
    local idx=$2
    echo "[$idx/$TOTAL] Pulling $service..."
    docker compose -f docker-compose.production.yaml pull $service 2>&1 | grep -E "(Pulling|Downloaded|Already|Error)" || echo "  ✓ $service"
}

export -f pull_service
export TOTAL

# Pull con concurrencia controlada usando xargs
printf '%s\n' "${SERVICES[@]}" | nl | xargs -P $PARALLEL -I {} bash -c 'pull_service $(echo {} | awk "{print \$2}") $(echo {} | awk "{print \$1}")'

echo ""
echo "=== VERIFICACION ==="
echo "Imágenes descargadas con tag :$IMAGE_TAG"
docker images | grep anvil-backend | grep ":$IMAGE_TAG"
echo ""
echo "Total de imágenes anvil-backend: $(docker images | grep anvil-backend | grep ":$IMAGE_TAG" | wc -l)"
echo "Infraestructura (postgres/redis):"
docker images | grep -E "^(postgres|redis)" | grep alpine

echo ""
echo "✅ Pull completado"
echo ""
echo "NOTA: Las imágenes pueden aparecer con múltiples tags (infra, sha-XXXXX)"
echo "      Son LA MISMA imagen, solo con diferentes nombres."
echo ""
echo "Siguiente paso:"
echo "  docker compose -f docker-compose.production.yaml up -d"
}}\t{{.Size}}\t{{.ID}}" | grep anvil

echo ""
echo "3. Inspeccionando capas de 2 imágenes diferentes..."
echo "--- API layers ---"
docker inspect ghcr.io/lucholeonel/anvil-backend-api:${IMAGE_TAG} | jq '.[0].RootFS.Layers' | head -5

echo "--- Celery LLM layers ---"
docker inspect ghcr.io/lucholeonel/anvil-backend-celery-worker-llm:${IMAGE_TAG} 2>/dev/null | jq '.[0].RootFS.Layers' | head -5 || echo "Imagen no descargada aún"

echo ""
echo "4. Espacio en disco disponible..."
df -h /var/lib/docker

echo ""
echo "=== RECOMENDACIONES ==="
echo "- Si el 'time' del pull fue > 2 minutos, tu conexión es lenta"
echo "- Si las primeras capas (sha256:...) NO coinciden entre imágenes, NO están compartiendo base"
echo "- Si tienes < 50GB libres, puede causar lentitud"
echo ""
echo "Tag actual en uso: $IMAGE_TAG"
echo "Para verificar imágenes: docker images | grep :$IMAGE_TAG"
