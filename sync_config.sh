#!/bin/bash

# Script para sincronizar configuración y reiniciar servicios
# Uso: bash sync_config.sh

set -e

echo "========================================="
echo "SINCRONIZAR CONFIGURACIÓN AL SERVIDOR"
echo "========================================="
echo ""

# Colores
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Variables
SERVER_USER="${SERVER_USER:-ec2-user}"
SERVER_HOST="${SERVER_HOST:-getramppy.com}"
SERVER_PATH="${SERVER_PATH:-/opt/docker/anvil}"

echo -e "${YELLOW}Servidor:${NC} ${SERVER_USER}@${SERVER_HOST}"
echo -e "${YELLOW}Directorio:${NC} ${SERVER_PATH}"
echo ""

# 1. Copiar directorio config/
echo "1️⃣  Copiando directorio config/..."
rsync -avz --progress \
  ./config/ \
  "${SERVER_USER}@${SERVER_HOST}:${SERVER_PATH}/config/"

if [ $? -eq 0 ]; then
  echo -e "${GREEN}✓${NC} Directorio config/ sincronizado"
else
  echo -e "${RED}✗${NC} Error copiando config/"
  exit 1
fi

# 2. Copiar docker-compose.production.yaml actualizado
echo ""
echo "2️⃣  Copiando docker-compose.production.yaml..."
scp docker-compose.production.yaml \
  "${SERVER_USER}@${SERVER_HOST}:${SERVER_PATH}/docker-compose.production.yaml"

if [ $? -eq 0 ]; then
  echo -e "${GREEN}✓${NC} docker-compose.production.yaml actualizado"
else
  echo -e "${RED}✗${NC} Error copiando docker-compose.production.yaml"
  exit 1
fi

# 3. Reiniciar servicios afectados
echo ""
echo "3️⃣  Reiniciando servicios..."
echo ""

ssh "${SERVER_USER}@${SERVER_HOST}" << 'ENDSSH'
cd /opt/docker/anvil

echo "📋 Reiniciando servicios afectados..."

# Servicios que necesitan el volumen config/
SERVICES=(
  "anvil_fastapi"
  "anvil_celery_worker"
  "anvil_celery_beat"
  "anvil_celery_agents"
  "anvil_celery_transactions"
  "anvil_celery_graph"
  "anvil_celery_distillation"
  "anvil_celery_projects"
  "anvil_celery_llm"
  "anvil_celery_maintenance"
  "anvil_celery_risk"
  "anvil_celery_email"
  "anvil_tx_confirmation"
)

for service in "${SERVICES[@]}"; do
  echo "  Reiniciando $service..."
  docker restart "$service" > /dev/null 2>&1
done

echo ""
echo "✅ Servicios reiniciados"
echo ""
echo "⏳ Esperando 10 segundos para que arranquen..."
sleep 10

echo ""
echo "📊 Estado de los servicios:"
docker ps --filter "name=anvil_" --format "table {{.Names}}\t{{.Status}}" | grep -E "(fastapi|celery|tx-confirmation)"

echo ""
echo "🔍 Verificando logs de FastAPI:"
echo ""
docker logs anvil_fastapi --tail 20

ENDSSH

echo ""
echo -e "${GREEN}=========================================${NC}"
echo -e "${GREEN}SINCRONIZACIÓN COMPLETADA${NC}"
echo -e "${GREEN}=========================================${NC}"
echo ""
echo "Próximos pasos en el servidor:"
echo "1. Verificar logs: docker logs anvil_fastapi --tail 50"
echo "2. Test local: curl http://localhost:8080/health"
echo "3. Test HTTPS: curl https://getramppy.com/health"
