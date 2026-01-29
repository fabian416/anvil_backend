#!/bin/bash

# Script para bajar imágenes con control de concurrencia
# Uso: bash pull_images.sh [número_paralelo]
# Ejemplo: bash pull_images.sh 3  (baja 3 imágenes a la vez)

PARALLEL=${1:-3}

# Detectar el directorio del script
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Buscar el archivo docker-compose
if [ -f "docker-compose.production.yaml" ]; then
    COMPOSE_FILE="docker-compose.production.yaml"
elif [ -f "docker-compose.yaml" ]; then
    COMPOSE_FILE="docker-compose.yaml"
else
    echo "❌ ERROR: No se encontró docker-compose.yaml o docker-compose.production.yaml"
    echo "   Directorio actual: $(pwd)"
    echo "   Archivos disponibles:"
    ls -la *.yaml 2>/dev/null || echo "   (ningún archivo .yaml)"
    exit 1
fi

echo "✓ Usando: $COMPOSE_FILE"
echo "✓ Directorio: $(pwd)"

# Leer IMAGE_TAG del .env
if [ -f .env ]; then
    IMAGE_TAG=$(grep "^IMAGE_TAG=" .env | cut -d'=' -f2)
    echo "✓ Leyendo .env: IMAGE_TAG=$IMAGE_TAG"
else
    IMAGE_TAG="infra"
    echo "⚠️  .env no encontrado, usando: $IMAGE_TAG"
fi

echo "=== PULL DE IMAGENES OPTIMIZADAS ==="
echo "Tag a descargar: $IMAGE_TAG"
echo "Concurrencia: $PARALLEL imágenes a la vez"
echo ""

export IMAGE_TAG

SERVICES=("postgres" "redis" "fastapi" "celery-worker" "celery-beat" "celery-worker-agents" "celery-worker-transactions" "celery-worker-graph" "celery-worker-distillation" "celery-worker-projects" "celery-worker-llm" "celery-worker-maintenance" "celery-worker-risk" "celery-worker-email" "mcp-1inch" "mcp-defillama" "mcp-thegraph" "mcp-coingecko" "mcp-aave" "mcp-portfolio" "mcp-perplexity" "mcp-morpho" "mcp-curve" "mcp-hyperliquid" "mcp-layerzero" "tx-confirmation")

TOTAL=${#SERVICES[@]}
echo "Total de servicios: $TOTAL"
echo ""

pull_service() {
    local service=$1
    local idx=$2
    echo "[$idx/$TOTAL] Pulling $service..."
    
    # Mostrar el output completo sin filtrar
    docker compose -f "$COMPOSE_FILE" pull $service 2>&1 | while IFS= read -r line; do
        echo "    $line"
    done
    
    # Verificar si la imagen existe después del pull
    echo -n "    Estado: "
    if docker compose -f "$COMPOSE_FILE" images $service 2>/dev/null | grep -q "$service"; then
        echo "✓ Descargada"
    else
        echo "✗ Error"
    fi
}

export -f pull_service
export TOTAL
export COMPOSE_FILE

printf '%s\n' "${SERVICES[@]}" | nl | xargs -P $PARALLEL -I {} bash -c 'pull_service $(echo {} | awk "{print \$2}") $(echo {} | awk "{print \$1}")'

echo ""
echo "✅ Pull completado"
echo ""
echo "Verificar imágenes descargadas:"
docker images | grep "ghcr.io/lucholeonel/anvil-backend" | grep ":$IMAGE_TAG"
echo ""
echo "Total: $(docker images | grep "ghcr.io/lucholeonel/anvil-backend" | grep ":$IMAGE_TAG" | wc -l)/24"
echo ""
echo "Para recrear contenedores: docker compose -f $COMPOSE_FILE up -d"
