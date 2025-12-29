#!/bin/bash
# Script para iniciar todos los workers de Celery, Beat y Flower
# Muestra logs en tiempo real de todos los procesos
#
# Note: This script is primarily for standalone use.
# When using 'make start-dev', Celery workers are started inline.

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
LOG_DIR="$PROJECT_DIR/logs/celery"
mkdir -p "$LOG_DIR"

# Track all PIDs
declare -a CELERY_PIDS=()

# Función para limpiar procesos al salir
cleanup() {
    echo -e "\n${YELLOW}Deteniendo todos los procesos de Celery...${NC}"
    
    # Kill tracked PIDs first
    for pid in "${CELERY_PIDS[@]}"; do
        if kill -0 "$pid" 2>/dev/null; then
            kill "$pid" 2>/dev/null || true
        fi
    done
    
    # Backup: pkill any remaining
    pkill -f "celery.*worker" 2>/dev/null || true
    pkill -f "celery.*beat" 2>/dev/null || true
    pkill -f "flower" 2>/dev/null || true
    pkill -f "tail -f.*celery" 2>/dev/null || true
    
    sleep 1
    echo -e "${GREEN}✅ Todos los procesos detenidos${NC}"
    exit 0
}

trap cleanup SIGINT SIGTERM EXIT

# Verificar que Redis está corriendo
if ! redis-cli ping > /dev/null 2>&1; then
    echo -e "${RED}❌ Error: Redis no está corriendo${NC}"
    echo "Inicia Redis con: make up.db o redis-server"
    exit 1
fi

echo -e "${GREEN}🚀 Iniciando todos los servicios de Celery...${NC}\n"

# Activate virtualenv
source env/bin/activate

# Iniciar todos los workers en background
echo -e "${CYAN}📦 Iniciando workers especializados...${NC}"

# Celery Worker configurations (name:queue:concurrency:max_tasks)
declare -a CELERY_WORKERS=(
    "maintenance:maintenance:2:500"
    "agents:agents:8:200"
    "graph:graph:2:100"
    "distillation:distillation:4:300"
    "projects:projects:3:200"
    "llm:llm:4:250"
    "transactions:transactions:6:500"
    "risk:risk:3:300"
    "email:email:2:1000"
)

for worker_config in "${CELERY_WORKERS[@]}"; do
    IFS=':' read -r name queue concurrency max_tasks <<< "$worker_config"
    
    PYTHONPATH=src ./env/bin/celery -A app.infrastructure.celery.app.celery_app worker \
        --loglevel=INFO \
        -Q "$queue" \
        -n "${name}@%h" \
        --concurrency="$concurrency" \
        --max-tasks-per-child="$max_tasks" \
        > "$LOG_DIR/${name}.log" 2>&1 &
    
    WORKER_PID=$!
    CELERY_PIDS+=("$WORKER_PID")
    echo -e "${GREEN}  ✅ ${name} worker (PID: $WORKER_PID)${NC}"
    sleep 0.2
done

# Iniciar Celery Beat
echo -e "\n${CYAN}⏰ Iniciando Celery Beat...${NC}"
PYTHONPATH=src ./env/bin/celery -A app.infrastructure.celery.app.celery_app beat \
    --loglevel=INFO \
    > "$LOG_DIR/beat.log" 2>&1 &
BEAT_PID=$!
CELERY_PIDS+=("$BEAT_PID")
echo -e "${GREEN}  ✅ Celery Beat (PID: $BEAT_PID)${NC}"

# Iniciar Flower
echo -e "\n${CYAN}🌸 Iniciando Flower (monitoring UI)...${NC}"
PYTHONPATH=src ./env/bin/python -m flower \
    -A app.infrastructure.celery.app.celery_app \
    --broker=redis://localhost:6379/0 \
    flower \
    --address=0.0.0.0 \
    --port=5555 \
    > "$LOG_DIR/flower.log" 2>&1 &
FLOWER_PID=$!
CELERY_PIDS+=("$FLOWER_PID")
echo -e "${GREEN}  ✅ Flower (PID: $FLOWER_PID) - http://localhost:5555${NC}"

# Esperar un momento para que todos inicien
sleep 2

# Verificar que todos están corriendo
echo -e "\n${CYAN}🔍 Verificando procesos...${NC}"
ALL_RUNNING=true
for pid in "${CELERY_PIDS[@]}"; do
    if ! kill -0 "$pid" 2>/dev/null; then
        echo -e "${RED}  ❌ Proceso $pid no está corriendo${NC}"
        ALL_RUNNING=false
    fi
done

if [ "$ALL_RUNNING" = true ]; then
    echo -e "${GREEN}✅ Todos los procesos están corriendo (${#CELERY_PIDS[@]} procesos)${NC}\n"
else
    echo -e "${YELLOW}⚠️  Algunos procesos pueden no haber iniciado correctamente${NC}\n"
fi

# Mostrar logs en tiempo real
echo -e "${MAGENTA}════════════════════════════════════════════════════════════${NC}"
echo -e "${MAGENTA}📊 LOGS EN TIEMPO REAL - Presiona Ctrl+C para detener todo${NC}"
echo -e "${MAGENTA}════════════════════════════════════════════════════════════${NC}\n"

# Check if multitail is available
if command -v multitail >/dev/null 2>&1; then
    echo -e "${GREEN}Usando multitail para logs combinados...${NC}\n"
    multitail \
        -cT ansi -s 2 \
        -l "tail -f $LOG_DIR/maintenance.log" -t "MAINTENANCE" \
        -l "tail -f $LOG_DIR/agents.log" -t "AGENTS" \
        -l "tail -f $LOG_DIR/graph.log" -t "GRAPH" \
        -l "tail -f $LOG_DIR/distillation.log" -t "DISTILLATION" \
        -l "tail -f $LOG_DIR/projects.log" -t "PROJECTS" \
        -l "tail -f $LOG_DIR/llm.log" -t "LLM" \
        -l "tail -f $LOG_DIR/transactions.log" -t "TRANSACTIONS" \
        -l "tail -f $LOG_DIR/risk.log" -t "RISK" \
        -l "tail -f $LOG_DIR/email.log" -t "EMAIL" \
        -l "tail -f $LOG_DIR/beat.log" -t "BEAT" \
        -l "tail -f $LOG_DIR/flower.log" -t "FLOWER"
else
    echo -e "${YELLOW}Nota: Instala 'multitail' para mejor visualización de logs${NC}"
    echo -e "${YELLOW}      apt-get install multitail (Linux) o brew install multitail (macOS)${NC}\n"
    echo -e "${CYAN}Logs se escriben a: $LOG_DIR/*.log${NC}"
    echo -e "${CYAN}Ver todos: tail -f $LOG_DIR/*.log${NC}\n"
    
    # Wait indefinitely, checking if processes are alive
    while true; do
        running=0
        for pid in "${CELERY_PIDS[@]}"; do
            if kill -0 "$pid" 2>/dev/null; then
                ((running++))
            fi
        done
        
        if [ $running -eq 0 ]; then
            echo -e "${RED}All Celery processes have exited${NC}"
            break
        fi
        
        sleep 5
    done
fi
