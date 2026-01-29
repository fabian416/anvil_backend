#!/bin/bash

echo "=== DIAGNOSTICO COMPLETO DE IMAGENES ==="
echo ""

# Leer IMAGE_TAG del .env
if [ -f .env ]; then
    IMAGE_TAG=$(grep "^IMAGE_TAG=" .env | cut -d'=' -f2)
    echo "✓ Tag configurado en .env: $IMAGE_TAG"
else
    IMAGE_TAG="infra"
    echo "⚠️ No hay .env, usando: $IMAGE_TAG"
fi
echo ""

# Lista de todas las imágenes que deberían existir
EXPECTED_IMAGES=(
    "ghcr.io/lucholeonel/anvil-backend-api:$IMAGE_TAG"
    "ghcr.io/lucholeonel/anvil-backend-celery-worker:$IMAGE_TAG"
    "ghcr.io/lucholeonel/anvil-backend-celery-beat:$IMAGE_TAG"
    "ghcr.io/lucholeonel/anvil-backend-celery-worker-agents:$IMAGE_TAG"
    "ghcr.io/lucholeonel/anvil-backend-celery-worker-transactions:$IMAGE_TAG"
    "ghcr.io/lucholeonel/anvil-backend-celery-worker-graph:$IMAGE_TAG"
    "ghcr.io/lucholeonel/anvil-backend-celery-worker-distillation:$IMAGE_TAG"
    "ghcr.io/lucholeonel/anvil-backend-celery-worker-projects:$IMAGE_TAG"
    "ghcr.io/lucholeonel/anvil-backend-celery-worker-llm:$IMAGE_TAG"
    "ghcr.io/lucholeonel/anvil-backend-celery-worker-maintenance:$IMAGE_TAG"
    "ghcr.io/lucholeonel/anvil-backend-celery-worker-risk:$IMAGE_TAG"
    "ghcr.io/lucholeonel/anvil-backend-celery-worker-email:$IMAGE_TAG"
    "ghcr.io/lucholeonel/anvil-backend-mcp-1inch:$IMAGE_TAG"
    "ghcr.io/lucholeonel/anvil-backend-mcp-defillama:$IMAGE_TAG"
    "ghcr.io/lucholeonel/anvil-backend-mcp-thegraph:$IMAGE_TAG"
    "ghcr.io/lucholeonel/anvil-backend-mcp-coingecko:$IMAGE_TAG"
    "ghcr.io/lucholeonel/anvil-backend-mcp-aave:$IMAGE_TAG"
    "ghcr.io/lucholeonel/anvil-backend-mcp-portfolio:$IMAGE_TAG"
    "ghcr.io/lucholeonel/anvil-backend-mcp-perplexity:$IMAGE_TAG"
    "ghcr.io/lucholeonel/anvil-backend-mcp-morpho:$IMAGE_TAG"
    "ghcr.io/lucholeonel/anvil-backend-mcp-curve:$IMAGE_TAG"
    "ghcr.io/lucholeonel/anvil-backend-mcp-hyperliquid:$IMAGE_TAG"
    "ghcr.io/lucholeonel/anvil-backend-mcp-layerzero:$IMAGE_TAG"
    "ghcr.io/lucholeonel/anvil-backend-tx-confirmation:$IMAGE_TAG"
)

echo "1. VERIFICANDO IMAGENES LOCALES"
echo "================================"
MISSING=0
PRESENT=0
WRONG_SIZE=0

for img in "${EXPECTED_IMAGES[@]}"; do
    if docker image inspect "$img" >/dev/null 2>&1; then
        SIZE=$(docker image inspect "$img" --format='{{.Size}}' | awk '{print $1/1024/1024}')
        SIZE_INT=$(printf "%.0f" $SIZE)
        
        if [ "$SIZE_INT" -gt 500 ]; then
            echo "⚠️  $img - PRESENTE pero GRANDE (${SIZE_INT}MB, esperado: 280-320MB)"
            WRONG_SIZE=$((WRONG_SIZE + 1))
        else
            echo "✓  $img - OK (${SIZE_INT}MB)"
            PRESENT=$((PRESENT + 1))
        fi
    else
        echo "✗  $img - FALTA"
        MISSING=$((MISSING + 1))
    fi
done

echo ""
echo "2. RESUMEN"
echo "=========="
echo "Imágenes correctas: $PRESENT/24"
echo "Imágenes faltantes: $MISSING/24"
echo "Imágenes con tamaño incorrecto: $WRONG_SIZE/24"

echo ""
echo "3. VERIFICAR EN GITHUB"
echo "======================"
echo "Verificando si las imágenes existen en GitHub Container Registry..."
echo ""

# Probar si el tag existe en GitHub
TEST_IMG="ghcr.io/lucholeonel/anvil-backend-api:$IMAGE_TAG"
echo "Probando: $TEST_IMG"
if docker manifest inspect "$TEST_IMG" >/dev/null 2>&1; then
    echo "✓ La imagen :$IMAGE_TAG EXISTE en GitHub"
    MANIFEST_SIZE=$(docker manifest inspect "$TEST_IMG" 2>/dev/null | jq -r '.config.size' 2>/dev/null || echo "unknown")
    echo "  Tamaño del manifest: $MANIFEST_SIZE bytes"
else
    echo "✗ La imagen :$IMAGE_TAG NO EXISTE en GitHub"
    echo ""
    echo "PROBLEMA: El tag '$IMAGE_TAG' no existe en GitHub Container Registry."
    echo ""
    echo "Posibles causas:"
    echo "1. El workflow de GitHub Actions no ha corrido en el branch 'infra'"
    echo "2. El workflow falló"
    echo "3. El tag se llama diferente (ej: 'development', 'staging')"
    echo ""
    echo "Verifica en: https://github.com/lucholeonel/anvil_backend/actions"
fi

echo ""
echo "4. TAGS DISPONIBLES"
echo "==================="
echo "Tags que SÍ tienes localmente:"
docker images | grep "ghcr.io/lucholeonel/anvil-backend" | awk '{print $1":"$2}' | sort | uniq

echo ""
echo "5. RECOMENDACION"
echo "================"
if [ $MISSING -gt 0 ]; then
    echo "⚠️ Faltan $MISSING imágenes. Ejecuta:"
    echo "   docker compose -f docker-compose.production.yaml pull"
fi

if [ $WRONG_SIZE -gt 0 ]; then
    echo "⚠️ $WRONG_SIZE imágenes tienen tamaño incorrecto (> 500MB)."
    echo "   Esto significa que son imágenes VIEJAS sin optimizar."
    echo "   Las nuevas deberían ser 280-320MB."
    echo ""
    echo "   Para actualizar:"
    echo "   docker compose -f docker-compose.production.yaml pull"
fi
