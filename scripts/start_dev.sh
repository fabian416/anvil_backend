#!/bin/bash
# Script para iniciar todos los servicios de desarrollo:
# - FastAPI (uvicorn)
# - MCP Servers (11 servers on ports 8081-8091)
# - Celery workers
# - Celery Beat
# - Flower monitoring

# Enable job control for proper signal handling
set -m

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
mkdir -p "$LOG_DIR/mcp"
mkdir -p "$LOG_DIR/celery"

# File to store PIDs for cleanup
PID_FILE="$LOG_DIR/.dev_pids"
> "$PID_FILE"  # Clear the file

# Track all background process PIDs
declare -a ALL_PIDS=()

# Función para limpiar procesos al salir
cleanup() {
    # Prevent multiple cleanup calls
    if [ -n "${CLEANUP_DONE:-}" ]; then
        return
    fi
    CLEANUP_DONE=1

    echo -e "\n${YELLOW}════════════════════════════════════════════════════════════${NC}"
    echo -e "${YELLOW}🛑 Deteniendo todos los servicios de desarrollo...${NC}"
    echo -e "${YELLOW}════════════════════════════════════════════════════════════${NC}"

    # Kill all tracked PIDs
    if [ -f "$PID_FILE" ]; then
        while read -r pid; do
            if kill -0 "$pid" 2>/dev/null; then
                echo -e "${CYAN}  Deteniendo PID $pid...${NC}"
                kill "$pid" 2>/dev/null || true
            fi
        done < "$PID_FILE"
    fi

    # Also use pkill as backup to ensure all processes are stopped
    echo -e "${CYAN}  Limpiando procesos restantes...${NC}"
    pkill -f "uvicorn app.run:make_app" 2>/dev/null || true
    pkill -f "app.infrastructure.mcp.servers" 2>/dev/null || true
    pkill -f "celery.*worker" 2>/dev/null || true
    pkill -f "celery.*beat" 2>/dev/null || true
    pkill -f "flower" 2>/dev/null || true

    # Kill any tail processes from log viewing
    pkill -f "tail -f.*logs/" 2>/dev/null || true

    sleep 1

    # Clean up PID file
    rm -f "$PID_FILE"

    echo -e "${GREEN}✅ Todos los servicios detenidos${NC}"
}

# Trap multiple signals for proper cleanup
trap cleanup SIGINT SIGTERM EXIT

# Helper function to track PIDs
track_pid() {
    echo "$1" >> "$PID_FILE"
    ALL_PIDS+=("$1")
}

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

# ============================================
# Stop existing processes first
# ============================================
echo -e "${YELLOW}🛑 Deteniendo procesos existentes...${NC}"

# Kill existing processes (try graceful first)
pkill -f "uvicorn app.run:make_app" 2>/dev/null || true
pkill -f "python.*uvicorn.*app.run" 2>/dev/null || true
pkill -f "app.infrastructure.mcp.servers" 2>/dev/null || true
pkill -f "celery.*worker" 2>/dev/null || true
pkill -f "celery.*beat" 2>/dev/null || true
pkill -f "flower" 2>/dev/null || true
pkill -f "tail -f.*logs/" 2>/dev/null || true

# Wait for processes to stop
sleep 2

# Force kill any remaining processes
pkill -9 -f "uvicorn app.run:make_app" 2>/dev/null || true
pkill -9 -f "python.*uvicorn.*app.run" 2>/dev/null || true
pkill -9 -f "app.infrastructure.mcp.servers" 2>/dev/null || true
pkill -9 -f "celery.*worker" 2>/dev/null || true
pkill -9 -f "celery.*beat" 2>/dev/null || true
pkill -9 -f "flower" 2>/dev/null || true

# Kill any process using port 8080 (FastAPI)
if command -v lsof >/dev/null 2>&1; then
    lsof -ti :8080 | xargs kill -9 2>/dev/null || true
fi

# Clear Python bytecode cache to ensure fresh code is loaded
echo -e "${CYAN}🧹 Limpiando Python bytecode cache...${NC}"
find "$PROJECT_DIR/src" -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find "$PROJECT_DIR/src" -name "*.pyc" -delete 2>/dev/null || true
export PYTHONDONTWRITEBYTECODE=1

# Kill any process using ports 8081-8091 (MCP servers)
for port in {8081..8091}; do
    lsof -ti :$port | xargs kill -9 2>/dev/null || true
done

# Kill any process using port 5555 (Flower)
lsof -ti :5555 | xargs kill -9 2>/dev/null || true

# Clean up PID file from previous run
rm -f "$PID_FILE"

# Wait a bit more to ensure ports are released
sleep 2

# Verify ports are free
if command -v lsof >/dev/null 2>&1; then
    if lsof -i :8080 >/dev/null 2>&1; then
        echo -e "${RED}⚠️  Advertencia: Puerto 8080 todavía en uso${NC}"
        lsof -i :8080
    fi
fi

echo -e "${GREEN}✅ Procesos anteriores detenidos${NC}\n"

echo -e "${MAGENTA}════════════════════════════════════════════════════════════${NC}"
echo -e "${MAGENTA}🚀 INICIANDO ENTORNO DE DESARROLLO COMPLETO${NC}"
echo -e "${MAGENTA}════════════════════════════════════════════════════════════${NC}"
echo -e "${CYAN}Servicios a iniciar:${NC}"
echo -e "  📡 FastAPI Server (puerto 8080)"
echo -e "  🔌 MCP Servers (11 servers, puertos 8081-8091)"
if [ "${CELERY_DEV_MODE:-light}" = "full" ]; then
    echo -e "  🐝 Celery Workers (9 workers especializados)"
else
    echo -e "  🐝 Celery Worker (1 worker general para desarrollo)"
fi
echo -e "  ⏰ Celery Beat (scheduler)"
echo -e "  🌸 Flower (monitoring UI, puerto 5555)"
echo -e "${MAGENTA}════════════════════════════════════════════════════════════${NC}\n"

# Activate virtualenv
source env/bin/activate

# Use venv Python explicitly to ensure correct environment
VENV_PYTHON="./env/bin/python3.12"

# ============================================
# 1. Start FastAPI
# ============================================
echo -e "${GREEN}📡 Iniciando FastAPI Server...${NC}"
PYTHONPATH=src $VENV_PYTHON -m uvicorn app.run:make_app \
    --factory \
    --host 0.0.0.0 \
    --port 8080 \
    --reload \
    > "$LOG_DIR/fastapi.log" 2>&1 &
FASTAPI_PID=$!
track_pid $FASTAPI_PID
echo -e "${GREEN}  ✅ FastAPI (PID: $FASTAPI_PID) - http://0.0.0.0:8080${NC}"

# Wait for FastAPI to start
sleep 3

# Verify FastAPI is running
if ! kill -0 $FASTAPI_PID 2>/dev/null; then
    echo -e "${RED}  ❌ FastAPI no pudo iniciar. Revisa logs: tail -f $LOG_DIR/fastapi.log${NC}"
    exit 1
fi
echo -e "${GREEN}  ✅ FastAPI iniciado correctamente${NC}\n"

# ============================================
# 2. Start MCP Servers (inline, not as subprocess)
# ============================================
echo -e "${GREEN}🔌 Iniciando MCP Servers...${NC}"

# MCP Server configurations (name:port:module)
declare -a MCP_SERVERS=(
    "1inch:8081:oneinch_mcp"
    "DeFiLlama:8082:defillama_mcp"
    "TheGraph:8083:thegraph_mcp"
    "CoinGecko:8084:coingecko_mcp"
    "Aave:8085:aave_mcp"
    "Portfolio:8086:portfolio_mcp"
    "Perplexity:8087:perplexity_mcp"
    "Morpho:8088:morpho_mcp"
    "Curve:8089:curve_mcp"
    "Hyperliquid:8090:hyperliquid_mcp"
    "LayerZero:8091:layerzero_mcp"
)

for server_config in "${MCP_SERVERS[@]}"; do
    IFS=':' read -r name port module <<< "$server_config"
    
    PYTHONPATH=src $VENV_PYTHON -m "app.infrastructure.mcp.servers.${module}" \
        > "$LOG_DIR/mcp/${module}.log" 2>&1 &
    
    MCP_PID=$!
    track_pid $MCP_PID
    echo -e "${CYAN}  ✅ ${name} (PID: $MCP_PID) - port ${port}${NC}"
    sleep 0.3
done

# Wait for MCP servers to initialize
sleep 3

# Verify MCP servers
MCP_RUNNING=0
for port in {8081..8091}; do
    if curl -s --max-time 1 http://localhost:$port/health > /dev/null 2>&1; then
        ((MCP_RUNNING++))
    fi
done

if [ $MCP_RUNNING -eq 11 ]; then
    echo -e "${GREEN}  ✅ MCP Servers: 11/11 running${NC}"
elif [ $MCP_RUNNING -gt 0 ]; then
    echo -e "${YELLOW}  ⚠️  MCP Servers: $MCP_RUNNING/11 running${NC}"
else
    echo -e "${YELLOW}  ⚠️  MCP Servers: starting (check logs)${NC}"
fi
echo ""

# ============================================
# 3. Start Celery Workers (inline, not as subprocess)
# ============================================
echo -e "${GREEN}🐝 Iniciando Celery Workers...${NC}"

# Celery Worker configurations (name:queue:concurrency:max_tasks)
# For development: single worker handling all queues (faster startup, less resource usage)
# For production: use specialized workers with 'make celery' instead
#
# Set CELERY_DEV_MODE=full to use specialized workers (slower startup, more resources)
if [ "${CELERY_DEV_MODE:-light}" = "full" ]; then
    # Full mode: Specialized workers (requires more CPU/RAM)
    # Reduced concurrency for 4-core systems
    declare -a CELERY_WORKERS=(
        "maintenance:maintenance:1:500"
        "agents:agents:2:200"
        "graph:graph:1:100"
        "distillation:distillation:1:300"
        "projects:projects:1:200"
        "llm:llm:1:250"
        "transactions:transactions:2:500"
        "risk:risk:1:300"
        "email:email:1:1000"
    )
else
    # Light mode (default): Single worker for all queues
    declare -a CELERY_WORKERS=(
        "default:maintenance,agents,graph,distillation,projects,llm,transactions,risk,email:4:500"
    )
fi

for worker_config in "${CELERY_WORKERS[@]}"; do
    IFS=':' read -r name queue concurrency max_tasks <<< "$worker_config"
    
    PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src ./env/bin/celery -A app.infrastructure.celery.app.celery_app worker \
        --loglevel=INFO \
        -Q "$queue" \
        -n "${name}@%h" \
        --concurrency="$concurrency" \
        --max-tasks-per-child="$max_tasks" \
        > "$LOG_DIR/celery/${name}.log" 2>&1 &
    
    WORKER_PID=$!
    track_pid $WORKER_PID
    echo -e "${CYAN}  ✅ ${name} worker (PID: $WORKER_PID)${NC}"
    sleep 0.2
done

# Start Celery Beat
echo -e "${GREEN}⏰ Iniciando Celery Beat...${NC}"
PYTHONPATH=src ./env/bin/celery -A app.infrastructure.celery.app.celery_app beat \
    --loglevel=INFO \
    > "$LOG_DIR/celery/beat.log" 2>&1 &
BEAT_PID=$!
track_pid $BEAT_PID
echo -e "${CYAN}  ✅ Celery Beat (PID: $BEAT_PID)${NC}"

# Start Flower
echo -e "${GREEN}🌸 Iniciando Flower...${NC}"
PYTHONPATH=src ./env/bin/python -m flower \
    -A app.infrastructure.celery.app.celery_app \
    --broker=redis://localhost:6379/0 \
    flower \
    --address=0.0.0.0 \
    --port=5555 \
    > "$LOG_DIR/celery/flower.log" 2>&1 &
FLOWER_PID=$!
track_pid $FLOWER_PID
echo -e "${CYAN}  ✅ Flower (PID: $FLOWER_PID) - http://localhost:5555${NC}"

# Wait for Celery to initialize
sleep 3

# Verify Celery workers
CELERY_RUNNING=$(pgrep -f "celery.*worker" | wc -l)
EXPECTED_WORKERS=${#CELERY_WORKERS[@]}
if [ $CELERY_RUNNING -ge $EXPECTED_WORKERS ]; then
    echo -e "${GREEN}  ✅ Celery Workers: $CELERY_RUNNING running${NC}"
else
    echo -e "${YELLOW}  ⚠️  Celery Workers: $CELERY_RUNNING running (expected $EXPECTED_WORKERS)${NC}"
fi

# ============================================
# Show Summary
# ============================================
echo -e "\n${MAGENTA}════════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}✅ ENTORNO DE DESARROLLO INICIADO${NC}"
echo -e "${MAGENTA}════════════════════════════════════════════════════════════${NC}"
echo -e "${YELLOW}🌐 Endpoints Disponibles:${NC}"
echo -e "  ${CYAN}FastAPI:${NC}       http://localhost:8080"
echo -e "  ${CYAN}FastAPI Docs:${NC}  http://localhost:8080/docs"
echo -e "  ${CYAN}Flower:${NC}        http://localhost:5555"
echo -e ""
echo -e "${YELLOW}🔌 MCP Servers:${NC}  http://localhost:8081-8091/tools"
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

echo -e "${CYAN}Esperando... Presiona Ctrl+C para detener todos los servicios.${NC}\n"

# Wait indefinitely - this keeps the script running and responsive to Ctrl+C
# We wait for any of the tracked processes to exit
while true; do
    # Check if key processes are still running
    if ! kill -0 $FASTAPI_PID 2>/dev/null; then
        echo -e "${RED}FastAPI exited unexpectedly${NC}"
        break
    fi
    sleep 5
done

# If we get here, something exited - cleanup will be called by EXIT trap
