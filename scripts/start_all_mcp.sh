#!/bin/bash
# Script to start all enabled MCP servers
# Each server runs on its own port and logs to separate files

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Project directories
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$PROJECT_DIR"

# Log directory for MCP servers
MCP_LOG_DIR="$PROJECT_DIR/logs/mcp"
mkdir -p "$MCP_LOG_DIR"

# Cleanup function
cleanup() {
    echo -e "\n${YELLOW}Deteniendo todos los servidores MCP...${NC}"
    pkill -f "app.infrastructure.mcp.servers" || true
    sleep 2
    echo -e "${GREEN}✅ Todos los servidores MCP detenidos${NC}"
    exit 0
}

trap cleanup SIGINT SIGTERM

echo -e "${MAGENTA}════════════════════════════════════════════════════════════${NC}"
echo -e "${MAGENTA}🔌 INICIANDO SERVIDORES MCP${NC}"
echo -e "${MAGENTA}════════════════════════════════════════════════════════════${NC}\n"

# Activate virtualenv
. env/bin/activate

# MCP Server configurations (name:port:module)
# Based on config/local/config.toml [mcp.servers]
declare -a MCP_SERVERS=(
    # Core Data & Market Intelligence (6 servers)
    "1inch:8081:oneinch_mcp"
    "DeFiLlama:8082:defillama_mcp"
    "TheGraph:8083:thegraph_mcp"
    "CoinGecko:8084:coingecko_mcp"
    "Aave:8085:aave_mcp"
    "Portfolio:8086:portfolio_mcp"

    # Advanced DeFi & Trading (5 servers)
    "Perplexity:8087:perplexity_mcp"
    "Morpho:8088:morpho_mcp"
    "Curve:8089:curve_mcp"
    "Hyperliquid:8090:hyperliquid_mcp"
    "LayerZero:8091:layerzero_mcp"
)

echo -e "${GREEN}🚀 Iniciando servidores MCP...${NC}\n"

# Start each MCP server
for server_config in "${MCP_SERVERS[@]}"; do
    IFS=':' read -r name port module <<< "$server_config"

    echo -e "${CYAN}  → Iniciando ${name} MCP Server (puerto ${port})...${NC}"

    PYTHONPATH=src python3.12 -m "app.infrastructure.mcp.servers.${module}" \
        > "$MCP_LOG_DIR/${module}.log" 2>&1 &

    SERVER_PID=$!
    echo -e "${GREEN}    ✅ ${name} MCP Server (PID: $SERVER_PID) - http://0.0.0.0:${port}${NC}"

    # Brief pause between server starts
    sleep 0.5
done

echo -e "\n${MAGENTA}════════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}✅ Todos los servidores MCP iniciados correctamente${NC}"
echo -e "${MAGENTA}════════════════════════════════════════════════════════════${NC}\n"

echo -e "${CYAN}📊 Endpoints disponibles (11 servers):${NC}"
echo -e "${YELLOW}Core Data & Market Intelligence:${NC}"
echo -e "  • 1inch:      http://localhost:8081/tools"
echo -e "  • DeFiLlama:  http://localhost:8082/tools"
echo -e "  • TheGraph:   http://localhost:8083/tools"
echo -e "  • CoinGecko:  http://localhost:8084/tools"
echo -e "  • Aave:       http://localhost:8085/tools"
echo -e "  • Portfolio:  http://localhost:8086/tools"
echo -e "${YELLOW}Advanced DeFi & Trading:${NC}"
echo -e "  • Perplexity: http://localhost:8087/tools"
echo -e "  • Morpho:     http://localhost:8088/tools"
echo -e "  • Curve:      http://localhost:8089/tools"
echo -e "  • Hyperliquid: http://localhost:8090/tools"
echo -e "  • LayerZero:  http://localhost:8091/tools"

echo -e "\n${CYAN}📝 Logs:${NC}"
echo -e "  Ver logs: tail -f $MCP_LOG_DIR/*.log"
echo -e "  Logs individuales: ls -la $MCP_LOG_DIR/"

echo -e "\n${YELLOW}Presiona Ctrl+C para detener todos los servidores MCP...${NC}\n"

# Wait for any process to exit
wait -n

# If any process exits, cleanup all
cleanup
