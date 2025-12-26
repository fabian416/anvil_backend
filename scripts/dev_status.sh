#!/bin/bash
# Quick status check for all development services

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
MAGENTA='\033[0;35m'
NC='\033[0m'

echo -e "${MAGENTA}════════════════════════════════════════════════════════════${NC}"
echo -e "${MAGENTA}📊 ESTADO DEL ENTORNO DE DESARROLLO${NC}"
echo -e "${MAGENTA}════════════════════════════════════════════════════════════${NC}\n"

# Check FastAPI
echo -e "${YELLOW}📡 FastAPI Server:${NC}"
if curl -s http://localhost:8080/health > /dev/null 2>&1 || curl -s http://localhost:8080 > /dev/null 2>&1; then
    echo -e "  ${GREEN}✅ Running${NC} - http://localhost:8080"
else
    echo -e "  ${RED}❌ Not running${NC}"
fi

# Check MCP Servers
echo -e "\n${YELLOW}🔌 MCP Servers (11 total):${NC}"
MCP_RUNNING=0
MCP_SERVERS=(
    "8081:1inch"
    "8082:DeFiLlama"
    "8083:TheGraph"
    "8084:CoinGecko"
    "8085:Aave"
    "8086:Portfolio"
    "8087:Perplexity"
    "8088:Morpho"
    "8089:Curve"
    "8090:Hyperliquid"
    "8091:LayerZero"
)

for server in "${MCP_SERVERS[@]}"; do
    IFS=':' read -r port name <<< "$server"
    if curl -s http://localhost:$port/health > /dev/null 2>&1; then
        echo -e "  ${GREEN}✅${NC} $name (port $port)"
        ((MCP_RUNNING++))
    else
        echo -e "  ${RED}❌${NC} $name (port $port)"
    fi
done

echo -e "  ${CYAN}Total: $MCP_RUNNING/11 running${NC}"

# Check Redis
echo -e "\n${YELLOW}🔴 Redis:${NC}"
if redis-cli ping > /dev/null 2>&1; then
    echo -e "  ${GREEN}✅ Running${NC}"
else
    echo -e "  ${RED}❌ Not running${NC}"
fi

# Check PostgreSQL
echo -e "\n${YELLOW}🐘 PostgreSQL:${NC}"
if pg_isready -q > /dev/null 2>&1; then
    echo -e "  ${GREEN}✅ Running${NC}"
else
    echo -e "  ${RED}❌ Not running${NC}"
fi

# Check Celery Workers
echo -e "\n${YELLOW}🐝 Celery Workers:${NC}"
CELERY_RUNNING=$(pgrep -f "celery.*worker" | wc -l)
if [ $CELERY_RUNNING -gt 0 ]; then
    echo -e "  ${GREEN}✅ Running${NC} - $CELERY_RUNNING worker processes"
else
    echo -e "  ${RED}❌ Not running${NC}"
fi

# Check Celery Beat
echo -e "\n${YELLOW}⏰ Celery Beat:${NC}"
if pgrep -f "celery.*beat" > /dev/null 2>&1; then
    echo -e "  ${GREEN}✅ Running${NC}"
else
    echo -e "  ${RED}❌ Not running${NC}"
fi

# Check Flower
echo -e "\n${YELLOW}🌸 Flower:${NC}"
if curl -s http://localhost:5555 > /dev/null 2>&1; then
    echo -e "  ${GREEN}✅ Running${NC} - http://localhost:5555"
else
    echo -e "  ${RED}❌ Not running${NC}"
fi

echo -e "\n${MAGENTA}════════════════════════════════════════════════════════════${NC}"
echo -e "${CYAN}Comandos útiles:${NC}"
echo -e "  ${CYAN}make start-dev${NC}  - Iniciar todos los servicios"
echo -e "  ${CYAN}make stop-dev${NC}   - Detener todos los servicios"
echo -e "  ${CYAN}make logs-all${NC}   - Ver todos los logs"
echo -e "${MAGENTA}════════════════════════════════════════════════════════════${NC}\n"
