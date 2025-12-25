#!/bin/bash
# Log Summary Script - Shows recent activity and errors from all services

set -e

# Colores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
CYAN='\033[0;36m'
WHITE='\033[1;37m'
NC='\033[0m'

# Directorio base
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$PROJECT_DIR"

LOG_DIR="$PROJECT_DIR/logs"
CELERY_LOG_DIR="$LOG_DIR/celery"

# Default: últimas 50 líneas
LINES=${1:-50}

echo -e "${MAGENTA}════════════════════════════════════════════════════════════${NC}"
echo -e "${MAGENTA}📋 RESUMEN DE LOGS - ÚLTIMAS $LINES LÍNEAS${NC}"
echo -e "${MAGENTA}════════════════════════════════════════════════════════════${NC}\n"

# Función para contar errores en un archivo
count_errors() {
    local file=$1
    if [ -f "$file" ]; then
        grep -i "error\|exception\|traceback\|failed" "$file" 2>/dev/null | wc -l || echo "0"
    else
        echo "0"
    fi
}

# Función para mostrar resumen de un log
show_log_summary() {
    local file=$1
    local label=$2
    local color=$3

    if [ ! -f "$file" ]; then
        echo -e "${YELLOW}  ⚠️  $label: Archivo no encontrado${NC}"
        return
    fi

    local size=$(du -h "$file" | cut -f1)
    local errors=$(count_errors "$file")
    local last_modified=$(stat -c %y "$file" 2>/dev/null || stat -f "%Sm" "$file" 2>/dev/null)

    echo -e "${color}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${WHITE}📄 $label${NC}"
    echo -e "${CYAN}   Tamaño: $size | Errores: $errors | Modificado: ${last_modified:0:19}${NC}"

    if [ "$errors" -gt 0 ]; then
        echo -e "${RED}   ⚠️  Se encontraron $errors líneas con errores${NC}"
        echo -e "${YELLOW}   Últimos errores:${NC}"
        grep -i "error\|exception\|traceback" "$file" 2>/dev/null | tail -3 | sed 's/^/     /' || true
    else
        echo -e "${GREEN}   ✅ No se encontraron errores recientes${NC}"
    fi

    echo -e "${CYAN}   Últimas $LINES líneas:${NC}"
    tail -n "$LINES" "$file" | head -5 | sed 's/^/     /' || true
    echo ""
}

# FastAPI
if [ -f "$LOG_DIR/fastapi.log" ]; then
    show_log_summary "$LOG_DIR/fastapi.log" "FastAPI Server" "$WHITE"
fi

# Celery Workers
if [ -d "$CELERY_LOG_DIR" ]; then
    echo -e "${MAGENTA}🐝 CELERY WORKERS${NC}\n"

    [ -f "$CELERY_LOG_DIR/maintenance.log" ] && show_log_summary "$CELERY_LOG_DIR/maintenance.log" "Maintenance Worker" "$BLUE"
    [ -f "$CELERY_LOG_DIR/agents.log" ] && show_log_summary "$CELERY_LOG_DIR/agents.log" "Agents Worker" "$GREEN"
    [ -f "$CELERY_LOG_DIR/graph.log" ] && show_log_summary "$CELERY_LOG_DIR/graph.log" "Graph Worker" "$CYAN"
    [ -f "$CELERY_LOG_DIR/distillation.log" ] && show_log_summary "$CELERY_LOG_DIR/distillation.log" "Distillation Worker" "$YELLOW"
    [ -f "$CELERY_LOG_DIR/projects.log" ] && show_log_summary "$CELERY_LOG_DIR/projects.log" "Projects Worker" "$MAGENTA"
    [ -f "$CELERY_LOG_DIR/llm.log" ] && show_log_summary "$CELERY_LOG_DIR/llm.log" "LLM Worker" "$RED"
    [ -f "$CELERY_LOG_DIR/transactions.log" ] && show_log_summary "$CELERY_LOG_DIR/transactions.log" "Transactions Worker" "$GREEN"
    [ -f "$CELERY_LOG_DIR/risk.log" ] && show_log_summary "$CELERY_LOG_DIR/risk.log" "Risk Worker" "$YELLOW"
    [ -f "$CELERY_LOG_DIR/email.log" ] && show_log_summary "$CELERY_LOG_DIR/email.log" "Email Worker" "$CYAN"
    [ -f "$CELERY_LOG_DIR/beat.log" ] && show_log_summary "$CELERY_LOG_DIR/beat.log" "Celery Beat" "$MAGENTA"
    [ -f "$CELERY_LOG_DIR/flower.log" ] && show_log_summary "$CELERY_LOG_DIR/flower.log" "Flower" "$BLUE"
fi

# Resumen total
echo -e "${MAGENTA}════════════════════════════════════════════════════════════${NC}"
echo -e "${WHITE}📊 RESUMEN GENERAL${NC}"

total_errors=0
if [ -f "$LOG_DIR/fastapi.log" ]; then
    fastapi_errors=$(count_errors "$LOG_DIR/fastapi.log")
    total_errors=$((total_errors + fastapi_errors))
fi

if [ -d "$CELERY_LOG_DIR" ]; then
    for log in "$CELERY_LOG_DIR"/*.log; do
        if [ -f "$log" ]; then
            errors=$(count_errors "$log")
            total_errors=$((total_errors + errors))
        fi
    done
fi

if [ "$total_errors" -eq 0 ]; then
    echo -e "${GREEN}✅ No se encontraron errores en ningún servicio${NC}"
else
    echo -e "${RED}⚠️  Total de líneas con errores: $total_errors${NC}"
    echo -e "${YELLOW}   Revisa los logs individuales para más detalles${NC}"
fi

# Uso del disco
total_size=$(du -sh "$LOG_DIR" 2>/dev/null | cut -f1 || echo "N/A")
echo -e "${CYAN}💾 Espacio usado por logs: $total_size${NC}"

echo -e "${MAGENTA}════════════════════════════════════════════════════════════${NC}\n"

# Comandos útiles
echo -e "${CYAN}💡 Comandos útiles:${NC}"
echo -e "   ${WHITE}make logs-all${NC}      - Ver todos los logs en tiempo real"
echo -e "   ${WHITE}make logs-fastapi${NC}  - Ver solo logs de FastAPI"
echo -e "   ${WHITE}make logs-celery${NC}   - Ver solo logs de Celery"
echo -e "   ${WHITE}make logs-tail${NC}     - Monitor interactivo con colores"
echo ""
