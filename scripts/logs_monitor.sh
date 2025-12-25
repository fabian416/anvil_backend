#!/bin/bash
# Advanced log monitoring script for all development services
# Shows logs from FastAPI and all Celery workers with color-coded prefixes

set -e

# Colores para logs
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
CYAN='\033[0;36m'
WHITE='\033[1;37m'
NC='\033[0m' # No Color

# Directorio base
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$PROJECT_DIR"

LOG_DIR="$PROJECT_DIR/logs"
CELERY_LOG_DIR="$LOG_DIR/celery"

# Verificar que los directorios de logs existen
if [ ! -d "$LOG_DIR" ]; then
    echo -e "${RED}❌ Error: Directorio de logs no encontrado: $LOG_DIR${NC}"
    echo -e "${YELLOW}Inicia el servidor primero: make start-dev${NC}"
    exit 1
fi

echo -e "${MAGENTA}════════════════════════════════════════════════════════════${NC}"
echo -e "${MAGENTA}📊 MONITOR DE LOGS - TODOS LOS SERVICIOS${NC}"
echo -e "${MAGENTA}════════════════════════════════════════════════════════════${NC}"
echo -e "${WHITE}Presiona Ctrl+C para salir${NC}\n"

# Mostrar información de archivos de log
echo -e "${CYAN}📁 Archivos de log disponibles:${NC}"
echo -e "${GREEN}  FastAPI:${NC} logs/fastapi.log"
if [ -d "$CELERY_LOG_DIR" ]; then
    echo -e "${GREEN}  Celery:${NC}"
    for log in "$CELERY_LOG_DIR"/*.log; do
        if [ -f "$log" ]; then
            filename=$(basename "$log")
            echo -e "    • logs/celery/$filename"
        fi
    done
fi
echo ""

# Función para mostrar logs combinados con prefijos de color
show_logs() {
    # Verificar si multitail está disponible (mejor opción)
    if command -v multitail >/dev/null 2>&1; then
        echo -e "${GREEN}✅ Usando multitail para logs combinados${NC}\n"

        # Construir comando multitail dinámicamente
        MULTITAIL_CMD="multitail -cT ansi -s 2"

        # Agregar FastAPI
        if [ -f "$LOG_DIR/fastapi.log" ]; then
            MULTITAIL_CMD="$MULTITAIL_CMD -l 'tail -f $LOG_DIR/fastapi.log' -t 'FASTAPI'"
        fi

        # Agregar todos los logs de Celery
        if [ -d "$CELERY_LOG_DIR" ]; then
            for log in "$CELERY_LOG_DIR"/*.log; do
                if [ -f "$log" ]; then
                    filename=$(basename "$log" .log)
                    label=$(echo "$filename" | tr '[:lower:]' '[:upper:]')
                    MULTITAIL_CMD="$MULTITAIL_CMD -l 'tail -f $log' -t '$label'"
                fi
            done
        fi

        eval "$MULTITAIL_CMD"
    else
        # Fallback: usar tail -f con sed para colores
        echo -e "${YELLOW}💡 Tip: Instala 'multitail' para mejor visualización${NC}"
        echo -e "${YELLOW}   Ubuntu/Debian: sudo apt-get install multitail${NC}"
        echo -e "${YELLOW}   macOS: brew install multitail${NC}\n"
        echo -e "${GREEN}Mostrando logs combinados...${NC}\n"

        # FastAPI logs
        if [ -f "$LOG_DIR/fastapi.log" ]; then
            tail -f "$LOG_DIR/fastapi.log" | sed "s/^/${WHITE}[FASTAPI]${NC} /" &
        fi

        # Celery logs con diferentes colores
        if [ -d "$CELERY_LOG_DIR" ]; then
            [ -f "$CELERY_LOG_DIR/maintenance.log" ] && tail -f "$CELERY_LOG_DIR/maintenance.log" | sed "s/^/${BLUE}[MAINTENANCE]${NC} /" &
            [ -f "$CELERY_LOG_DIR/agents.log" ] && tail -f "$CELERY_LOG_DIR/agents.log" | sed "s/^/${GREEN}[AGENTS]${NC} /" &
            [ -f "$CELERY_LOG_DIR/graph.log" ] && tail -f "$CELERY_LOG_DIR/graph.log" | sed "s/^/${CYAN}[GRAPH]${NC} /" &
            [ -f "$CELERY_LOG_DIR/distillation.log" ] && tail -f "$CELERY_LOG_DIR/distillation.log" | sed "s/^/${YELLOW}[DISTILLATION]${NC} /" &
            [ -f "$CELERY_LOG_DIR/projects.log" ] && tail -f "$CELERY_LOG_DIR/projects.log" | sed "s/^/${MAGENTA}[PROJECTS]${NC} /" &
            [ -f "$CELERY_LOG_DIR/llm.log" ] && tail -f "$CELERY_LOG_DIR/llm.log" | sed "s/^/${RED}[LLM]${NC} /" &
            [ -f "$CELERY_LOG_DIR/transactions.log" ] && tail -f "$CELERY_LOG_DIR/transactions.log" | sed "s/^/${GREEN}[TRANSACTIONS]${NC} /" &
            [ -f "$CELERY_LOG_DIR/risk.log" ] && tail -f "$CELERY_LOG_DIR/risk.log" | sed "s/^/${YELLOW}[RISK]${NC} /" &
            [ -f "$CELERY_LOG_DIR/email.log" ] && tail -f "$CELERY_LOG_DIR/email.log" | sed "s/^/${CYAN}[EMAIL]${NC} /" &
            [ -f "$CELERY_LOG_DIR/beat.log" ] && tail -f "$CELERY_LOG_DIR/beat.log" | sed "s/^/${MAGENTA}[BEAT]${NC} /" &
            [ -f "$CELERY_LOG_DIR/flower.log" ] && tail -f "$CELERY_LOG_DIR/flower.log" | sed "s/^/${BLUE}[FLOWER]${NC} /" &
        fi

        # Esperar indefinidamente
        wait
    fi
}

# Cleanup function
cleanup() {
    echo -e "\n${YELLOW}Cerrando monitor de logs...${NC}"
    # Kill all background tail processes
    pkill -P $$ || true
    exit 0
}

trap cleanup SIGINT SIGTERM

# Mostrar logs
show_logs
