#!/bin/bash

# Leer IMAGE_TAG del .env
if [ -f .env ]; then
    IMAGE_TAG=$(grep "^IMAGE_TAG=" .env | cut -d'=' -f2)
    echo "✓ Tag configurado: $IMAGE_TAG"
else
    IMAGE_TAG="infra"
    echo "⚠️  .env no encontrado, asumiendo tag: $IMAGE_TAG"
fi

echo "=== DIAGNOSTICO DE CONTENEDORES CRASHEANDO ==="
echo ""

# Lista de contenedores con problemas
CRASHING=(
    "anvil_tx_confirmation"
    "anvil_celery_maintenance"
    "anvil_celery_worker"
    "anvil_celery_projects"
    "anvil_fastapi"
    "anvil_mcp_morpho"
    "anvil_mcp_layerzero"
    "anvil_mcp_thegraph"
    "anvil_mcp_defillama"
    "anvil_mcp_1inch"
    "anvil_mcp_aave"
    "anvil_mcp_perplexity"
    "anvil_mcp_curve"
    "anvil_mcp_coingecko"
    "anvil_mcp_hyperliquid"
    "anvil_mcp_portfolio"
)

echo "Revisando logs de los últimos 50 errores de cada servicio..."
echo ""

for container in "${CRASHING[@]}"; do
    echo "==================================="
    echo "CONTAINER: $container"
    echo "==================================="
    docker logs --tail 50 $container 2>&1 | grep -E "(Error|Exception|Traceback|ImportError|ModuleNotFoundError|Failed|CRITICAL)" | tail -20
    echo ""
done

echo ""
echo "=== VERIFICAR IMAGENES DISPONIBLES ==="
echo "Imágenes con tag :$IMAGE_TAG descargadas:"
docker images | grep ":$IMAGE_TAG" | wc -l
echo ""
echo "Listado de imágenes con tag :$IMAGE_TAG:"
docker images | grep ":$IMAGE_TAG"
echo ""
echo "Tamaños esperados: 280-320MB (optimizadas)"
echo ""
echo "=== VERIFICAR TAG EN docker-compose.production.yaml ==="
grep "IMAGE_TAG" docker-compose.production.yaml || echo "No se encontró IMAGE_TAG en el archivo"
echo ""
echo "=== VERIFICAR .env ==="
grep "IMAGE_TAG" .env 2>/dev/null || echo "No hay .env o no tiene IMAGE_TAG"
