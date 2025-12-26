#!/bin/bash
# Script para iniciar todos los servicios de desarrollo:
# - FastAPI (uvicorn)
# - MCP Servers (11 servers on ports 8081-8091)
# - Celery workers
# - Celery Beat
# - Flower monitoring

set -e

# Colores para logs
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Directorio base
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$PROJECT_DIR"

# Directorio para logs
LOG_DIR="$PROJECT_DIR/logs"
mkdir -p "$LOG_DIR"

# Variables para PIDs
FASTAPI_PID=""
MCP_PIDS=""
CELERY_PIDS=""

# Función para limpiar procesos al salir
cleanup() {
    echo -e "\n${YELLOW}Deteniendo todos los servicios...${NC}"

    # Detener FastAPI
    if [ -n "$FASTAPI_PID" ] && kill -0 "$FASTAPI_PID" 2>/dev/null; then
        echo -e "${CYAN}Deteniendo FastAPI...${NC}"
        kill $FASTAPI_PID || true
    fi

    # Detener todos los procesos de MCP
    echo -e "${CYAN}Deteniendo MCP servers...${NC}"
    pkill -f "app.infrastructure.mcp.servers" || true

    # Detener todos los procesos de Celery
    echo -e "${CYAN}Deteniendo Celery workers...${NC}"
    pkill -f "celery.*worker" || true
    pkill -f "celery.*beat" || true
    pkill -f "flower" || true

    sleep 2
    echo -e "${GREEN}✅ Todos los servicios detenidos${NC}"
    exit 0
}

trap cleanup SIGINT SIGTERM

# Verificar que el virtualenv existe
if [ ! -d "env" ]; then
    echo -e "${RED}❌ Error: Virtualenv no encontrado${NC}"
    echo "Ejecuta: make venv && pip install -e '.[dev,test]'"
    exit 1
fi

# Verificar que Redis está corriendo
if ! redis-cli ping > /dev/null 2>&1; then
    echo -e "${YELLOW}⚠️  Redis no está corriendo${NC}"
    echo -e "${CYAN}Intentando iniciar Redis con Docker...${NC}"
    if command -v docker >/dev/null 2>&1; then
        make up.db || {
            echo -e "${RED}❌ Error: No se pudo iniciar Redis${NC}"
            echo "Inicia Redis manualmente: make up.db o redis-server"
            exit 1
        }
        sleep 3
    else
        echo -e "${RED}❌ Error: Docker no disponible y Redis no está corriendo${NC}"
        echo "Inicia Redis manualmente: redis-server"
        exit 1
    fi
fi

echo -e "${MAGENTA}════════════════════════════════════════════════════════════${NC}"
echo -e "${MAGENTA}🚀 INICIANDO ENTORNO DE DESARROLLO COMPLETO${NC}"
echo -e "${MAGENTA}════════════════════════════════════════════════════════════${NC}"
echo -e "${CYAN}Servicios a iniciar:${NC}"
echo -e "  📡 FastAPI Server (puerto 8080)"
echo -e "  🔌 MCP Servers (11 servers, puertos 8081-8091)"
echo -e "  🐝 Celery Workers (9 workers especializados)"
echo -e "  ⏰ Celery Beat (scheduler)"
echo -e "  🌸 Flower (monitoring UI, puerto 5555)"
echo -e "${MAGENTA}════════════════════════════════════════════════════════════${NC}\n"

# 1. Iniciar FastAPI
echo -e "${GREEN}📡 Iniciando FastAPI Server...${NC}"
. env/bin/activate && PYTHONPATH=src python3.12 -m uvicorn app.run:make_app \
    --factory \
    --host 0.0.0.0 \
    --port 8080 \
    --reload \
    > "$LOG_DIR/fastapi.log" 2>&1 &
FASTAPI_PID=$!
echo -e "${GREEN}  ✅ FastAPI (PID: $FASTAPI_PID) - http://0.0.0.0:8080${NC}"

# Esperar a que FastAPI inicie
sleep 3

# Verificar que FastAPI está corriendo
if ! kill -0 $FASTAPI_PID 2>/dev/null; then
    echo -e "${RED}  ❌ FastAPI no pudo iniciar. Revisa logs: tail -f $LOG_DIR/fastapi.log${NC}"
    exit 1
fi

echo -e "${GREEN}  ✅ FastAPI iniciado correctamente${NC}\n"

# 2. Iniciar MCP Servers
echo -e "${GREEN}🔌 Iniciando MCP Servers...${NC}"
bash "$SCRIPT_DIR/start_all_mcp.sh" &
MCP_SCRIPT_PID=$!

# Esperar a que los MCP servers inicien
sleep 5

# Verificar que los MCP servers estén corriendo
echo -e "${CYAN}  Verificando MCP servers...${NC}"
MCP_RUNNING=0
for port in {8081..8091}; do
    if curl -s http://localhost:$port/health > /dev/null 2>&1; then
        ((MCP_RUNNING++))
    fi
done

if [ $MCP_RUNNING -eq 11 ]; then
    echo -e "${GREEN}  ✅ MCP Servers iniciados correctamente (11/11 servers running)${NC}"
elif [ $MCP_RUNNING -gt 0 ]; then
    echo -e "${YELLOW}  ⚠️  MCP Servers parcialmente iniciados ($MCP_RUNNING/11 servers running)${NC}"
else
    echo -e "${RED}  ❌ MCP Servers no iniciados (verificar logs)${NC}"
fi

echo -e "${CYAN}  Ver endpoints: http://localhost:8081-8091/tools${NC}"
echo -e "${CYAN}  Ver logs MCP: tail -f $LOG_DIR/mcp/*.log${NC}\n"

# 3. Iniciar Celery workers, Beat y Flower
echo -e "${GREEN}🐝 Iniciando Celery (workers + beat + flower)...${NC}"
echo -e "${CYAN}   Nota: Los logs de Celery se mostrarán en tiempo real${NC}\n"

# El script de Celery ya maneja su propio cleanup, pero lo capturamos aquí también
bash "$SCRIPT_DIR/start_all_celery.sh" &
CELERY_SCRIPT_PID=$!

# Esperar un momento para que Celery inicie
sleep 3

# Mostrar resumen completo
echo -e "\n${MAGENTA}════════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}✅ ENTORNO DE DESARROLLO INICIADO${NC}"
echo -e "${MAGENTA}════════════════════════════════════════════════════════════${NC}"
echo -e "${YELLOW}🌐 Endpoints Disponibles:${NC}"
echo -e "  ${CYAN}FastAPI:${NC}       http://localhost:8080"
echo -e "  ${CYAN}FastAPI Docs:${NC}  http://localhost:8080/docs"
echo -e "  ${CYAN}Flower:${NC}        http://localhost:5555"
echo -e ""
echo -e "${YELLOW}🔌 MCP Servers (11 servers):${NC}"
echo -e "  ${CYAN}Core Data & Market Intelligence:${NC}"
echo -e "    • 1inch:      http://localhost:8081/tools"
echo -e "    • DeFiLlama:  http://localhost:8082/tools"
echo -e "    • TheGraph:   http://localhost:8083/tools"
echo -e "    • CoinGecko:  http://localhost:8084/tools"
echo -e "    • Aave:       http://localhost:8085/tools"
echo -e "    • Portfolio:  http://localhost:8086/tools"
echo -e "  ${CYAN}Advanced DeFi & Trading:${NC}"
echo -e "    • Perplexity: http://localhost:8087/tools"
echo -e "    • Morpho:     http://localhost:8088/tools"
echo -e "    • Curve:      http://localhost:8089/tools"
echo -e "    • Hyperliquid: http://localhost:8090/tools"
echo -e "    • LayerZero:  http://localhost:8091/tools"
echo -e ""
echo -e "${YELLOW}📊 Celery Workers (9 workers):${NC}"
echo -e "  • AGENTS       - Procesamiento de agentes IA"
echo -e "  • RISK         - Monitoreo de riesgo"
echo -e "  • TRANSACTIONS - Confirmación de transacciones blockchain"
echo -e "  • LLM          - Ranking y orchestration de LLM"
echo -e "  • DISTILLATION - Procesamiento de LLM y caché"
echo -e "  • PROJECTS     - Knowledge base y proyectos"
echo -e "  • GRAPH        - Mantenimiento de grafo y embeddings"
echo -e "  • EMAIL        - Envío de emails"
echo -e "  • MAINTENANCE  - Tareas de limpieza y mantenimiento"
echo -e ""
echo -e "${YELLOW}📝 Ver Logs:${NC}"
echo -e "  ${CYAN}make logs-fastapi${NC}  - FastAPI logs"
echo -e "  ${CYAN}make logs-mcp${NC}      - MCP servers logs"
echo -e "  ${CYAN}make logs-celery${NC}   - Celery workers logs"
echo -e "  ${CYAN}make logs-all${NC}      - All logs combined"
echo -e ""
echo -e "${YELLOW}🛑 Detener Todo:${NC}"
echo -e "  ${CYAN}make stop-dev${NC}      - Detiene todos los servicios"
echo -e "  ${CYAN}Ctrl+C${NC}             - Detiene este script y todos los servicios"
echo -e "${MAGENTA}════════════════════════════════════════════════════════════${NC}\n"

# Esperar indefinidamente (el script de Celery se encarga de mostrar logs)
wait $CELERY_SCRIPT_PID

# Si el script de Celery termina, hacer cleanup
cleanup
