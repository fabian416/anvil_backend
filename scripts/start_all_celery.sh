#!/bin/bash
# Script para iniciar todos los workers de Celery, Beat y Flower
# Muestra logs en tiempo real de todos los procesos

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

# Función para limpiar procesos al salir
cleanup() {
    echo -e "\n${YELLOW}Deteniendo todos los procesos de Celery...${NC}"
    pkill -f "celery.*worker" || true
    pkill -f "celery.*beat" || true
    pkill -f "flower" || true
    sleep 2
    echo -e "${GREEN}✅ Todos los procesos detenidos${NC}"
    exit 0
}

trap cleanup SIGINT SIGTERM

# Verificar que Redis está corriendo
if ! redis-cli ping > /dev/null 2>&1; then
    echo -e "${RED}❌ Error: Redis no está corriendo${NC}"
    echo "Inicia Redis con: make up.db o redis-server"
    exit 1
fi

echo -e "${GREEN}🚀 Iniciando todos los servicios de Celery...${NC}\n"

# Iniciar todos los workers en background
echo -e "${CYAN}📦 Iniciando workers especializados...${NC}"

PYTHONPATH=src ./env/bin/celery -A app.infrastructure.celery.app.celery_app worker \
    --loglevel=INFO \
    -Q maintenance \
    -n maintenance@%h \
    --concurrency=2 \
    --max-tasks-per-child=500 \
    > "$LOG_DIR/maintenance.log" 2>&1 &
MAINTENANCE_PID=$!
echo -e "${GREEN}  ✅ Maintenance worker (PID: $MAINTENANCE_PID)${NC}"

PYTHONPATH=src ./env/bin/celery -A app.infrastructure.celery.app.celery_app worker \
    --loglevel=INFO \
    -Q agents \
    -n agents@%h \
    --concurrency=8 \
    --max-tasks-per-child=200 \
    > "$LOG_DIR/agents.log" 2>&1 &
AGENTS_PID=$!
echo -e "${GREEN}  ✅ Agents worker (PID: $AGENTS_PID)${NC}"

PYTHONPATH=src ./env/bin/celery -A app.infrastructure.celery.app.celery_app worker \
    --loglevel=INFO \
    -Q graph \
    -n graph@%h \
    --concurrency=2 \
    --max-tasks-per-child=100 \
    > "$LOG_DIR/graph.log" 2>&1 &
GRAPH_PID=$!
echo -e "${GREEN}  ✅ Graph worker (PID: $GRAPH_PID)${NC}"

PYTHONPATH=src ./env/bin/celery -A app.infrastructure.celery.app.celery_app worker \
    --loglevel=INFO \
    -Q distillation \
    -n distillation@%h \
    --concurrency=4 \
    --max-tasks-per-child=300 \
    > "$LOG_DIR/distillation.log" 2>&1 &
DISTILLATION_PID=$!
echo -e "${GREEN}  ✅ Distillation worker (PID: $DISTILLATION_PID)${NC}"

PYTHONPATH=src ./env/bin/celery -A app.infrastructure.celery.app.celery_app worker \
    --loglevel=INFO \
    -Q projects \
    -n projects@%h \
    --concurrency=3 \
    --max-tasks-per-child=200 \
    > "$LOG_DIR/projects.log" 2>&1 &
PROJECTS_PID=$!
echo -e "${GREEN}  ✅ Projects worker (PID: $PROJECTS_PID)${NC}"

PYTHONPATH=src ./env/bin/celery -A app.infrastructure.celery.app.celery_app worker \
    --loglevel=INFO \
    -Q llm \
    -n llm@%h \
    --concurrency=4 \
    --max-tasks-per-child=250 \
    > "$LOG_DIR/llm.log" 2>&1 &
LLM_PID=$!
echo -e "${GREEN}  ✅ LLM worker (PID: $LLM_PID)${NC}"

PYTHONPATH=src ./env/bin/celery -A app.infrastructure.celery.app.celery_app worker \
    --loglevel=INFO \
    -Q transactions \
    -n transactions@%h \
    --concurrency=6 \
    --max-tasks-per-child=500 \
    > "$LOG_DIR/transactions.log" 2>&1 &
TRANSACTIONS_PID=$!
echo -e "${GREEN}  ✅ Transactions worker (PID: $TRANSACTIONS_PID)${NC}"

PYTHONPATH=src ./env/bin/celery -A app.infrastructure.celery.app.celery_app worker \
    --loglevel=INFO \
    -Q risk \
    -n risk@%h \
    --concurrency=3 \
    --max-tasks-per-child=300 \
    > "$LOG_DIR/risk.log" 2>&1 &
RISK_PID=$!
echo -e "${GREEN}  ✅ Risk worker (PID: $RISK_PID)${NC}"

PYTHONPATH=src ./env/bin/celery -A app.infrastructure.celery.app.celery_app worker \
    --loglevel=INFO \
    -Q email \
    -n email@%h \
    --concurrency=2 \
    --max-tasks-per-child=1000 \
    > "$LOG_DIR/email.log" 2>&1 &
EMAIL_PID=$!
echo -e "${GREEN}  ✅ Email worker (PID: $EMAIL_PID)${NC}"

# Iniciar Celery Beat
echo -e "\n${CYAN}⏰ Iniciando Celery Beat...${NC}"
PYTHONPATH=src ./env/bin/celery -A app.infrastructure.celery.app.celery_app beat \
    --loglevel=INFO \
    > "$LOG_DIR/beat.log" 2>&1 &
BEAT_PID=$!
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
echo -e "${GREEN}  ✅ Flower (PID: $FLOWER_PID) - http://localhost:5555${NC}"

# Esperar un momento para que todos inicien
sleep 2

# Verificar que todos están corriendo
echo -e "\n${CYAN}🔍 Verificando procesos...${NC}"
ALL_RUNNING=true
for pid in $MAINTENANCE_PID $AGENTS_PID $GRAPH_PID $DISTILLATION_PID $PROJECTS_PID $LLM_PID $TRANSACTIONS_PID $RISK_PID $EMAIL_PID $BEAT_PID $FLOWER_PID; do
    if ! kill -0 $pid 2>/dev/null; then
        echo -e "${RED}  ❌ Proceso $pid no está corriendo${NC}"
        ALL_RUNNING=false
    fi
done

if [ "$ALL_RUNNING" = true ]; then
    echo -e "${GREEN}✅ Todos los procesos están corriendo${NC}\n"
else
    echo -e "${YELLOW}⚠️  Algunos procesos pueden no haber iniciado correctamente${NC}\n"
fi

# Mostrar logs en tiempo real usando tail -f con colores
echo -e "${MAGENTA}════════════════════════════════════════════════════════════${NC}"
echo -e "${MAGENTA}📊 LOGS EN TIEMPO REAL - Presiona Ctrl+C para detener todo${NC}"
echo -e "${MAGENTA}════════════════════════════════════════════════════════════${NC}\n"

# Función para mostrar logs combinados con prefijos de color
# Usa tail -f en paralelo con colores para cada worker
show_logs() {
    # Verificar si multitail está disponible (mejor opción)
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
        # Fallback: usar tail -f con sed para colores
        echo -e "${YELLOW}Nota: Instala 'multitail' para mejor visualización de logs${NC}"
        echo -e "${YELLOW}      brew install multitail (macOS) o apt-get install multitail (Linux)${NC}\n"
        echo -e "${CYAN}Mostrando logs combinados (puede ser desordenado sin multitail)...${NC}\n"
        
        # Combinar todos los logs con prefijos de color usando procesos en background
        tail -f "$LOG_DIR/maintenance.log" | sed "s/^/${BLUE}[MAINTENANCE]${NC} /" &
        tail -f "$LOG_DIR/agents.log" | sed "s/^/${GREEN}[AGENTS]${NC} /" &
        tail -f "$LOG_DIR/graph.log" | sed "s/^/${CYAN}[GRAPH]${NC} /" &
        tail -f "$LOG_DIR/distillation.log" | sed "s/^/${YELLOW}[DISTILLATION]${NC} /" &
        tail -f "$LOG_DIR/projects.log" | sed "s/^/${MAGENTA}[PROJECTS]${NC} /" &
        tail -f "$LOG_DIR/llm.log" | sed "s/^/${RED}[LLM]${NC} /" &
        tail -f "$LOG_DIR/transactions.log" | sed "s/^/${GREEN}[TRANSACTIONS]${NC} /" &
        tail -f "$LOG_DIR/risk.log" | sed "s/^/${YELLOW}[RISK]${NC} /" &
        tail -f "$LOG_DIR/email.log" | sed "s/^/${CYAN}[EMAIL]${NC} /" &
        tail -f "$LOG_DIR/beat.log" | sed "s/^/${MAGENTA}[BEAT]${NC} /" &
        tail -f "$LOG_DIR/flower.log" | sed "s/^/${BLUE}[FLOWER]${NC} /" &
        
        # Esperar indefinidamente
        wait
    fi
}

# Mostrar logs
show_logs

