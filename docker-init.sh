#!/bin/bash

# ========================================
# Docker Initialization Script for Anvil
# ========================================
# Use: chmod +x docker-init.sh && ./docker-init.sh

set -e

echo "========================================="
echo "Anvil Docker Infrastructure Initialization"
echo "========================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# ========================================
# 1. BUILD ALL IMAGES
# ========================================

echo -e "${YELLOW}Step 1: Building all Docker images...${NC}"
echo ""

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

docker-compose -f "$SCRIPT_DIR/docker-compose.yaml" build --no-cache

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ All images built successfully${NC}"
else
    echo -e "${RED}✗ Failed to build images${NC}"
    exit 1
fi

echo ""

# ========================================
# 2. START INFRASTRUCTURE SERVICES
# ========================================

echo -e "${YELLOW}Step 2: Starting infrastructure services (PostgreSQL & Redis)...${NC}"
echo ""

docker-compose -f "$SCRIPT_DIR/docker-compose.yaml" up -d postgres redis

# Wait for services to be healthy
echo "Waiting for PostgreSQL to be ready..."
sleep 10

echo "Waiting for Redis to be ready..."
sleep 5

echo -e "${GREEN}✓ Infrastructure services are running${NC}"
echo ""

# ========================================
# 3. RUN DATABASE MIGRATIONS
# ========================================

echo -e "${YELLOW}Step 3: Running database migrations...${NC}"
echo ""

docker-compose -f "$SCRIPT_DIR/docker-compose.yaml" run --rm fastapi alembic upgrade head

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Database migrations completed${NC}"
else
    echo -e "${RED}✗ Database migrations failed${NC}"
    exit 1
fi

echo ""

# ========================================
# 4. START ALL SERVICES
# ========================================

echo -e "${YELLOW}Step 4: Starting all services...${NC}"
echo ""

docker-compose -f "$SCRIPT_DIR/docker/docker-compose.yaml" up -d

# Give services time to start
sleep 10

echo -e "${GREEN}✓ All services started${NC}"
echo ""

# ========================================
# 5. VERIFY SERVICES
# ========================================

echo -e "${YELLOW}Step 5: Verifying services...${NC}"
echo ""

# Check FastAPI
if curl -s http://localhost:8080/health > /dev/null 2>&1; then
    echo -e "${GREEN}✓ FastAPI is healthy${NC}"
else
    echo -e "${YELLOW}⚠ FastAPI is not yet responding (may still be starting)${NC}"
fi

# Check Redis
if docker exec anvil_redis redis-cli ping > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Redis is healthy${NC}"
else
    echo -e "${RED}✗ Redis is not responding${NC}"
fi

# Check PostgreSQL
if docker exec anvil_postgres pg_isready -U anvil > /dev/null 2>&1; then
    echo -e "${GREEN}✓ PostgreSQL is healthy${NC}"
else
    echo -e "${RED}✗ PostgreSQL is not responding${NC}"
fi

echo ""

# ========================================
# 6. DISPLAY INFORMATION
# ========================================

echo -e "${GREEN}=========================================${NC}"
echo -e "${GREEN}Docker Infrastructure Ready!${NC}"
echo -e "${GREEN}=========================================${NC}"
echo ""

echo "Available Services:"
echo "  • FastAPI API:           http://localhost:8080"
echo "    - Health Check:        http://localhost:8080/health"
echo "    - Docs:                http://localhost:8080/docs"
echo ""
echo "  • Flower Monitoring:     http://localhost:5555"
echo ""
echo "  • Database (PostgreSQL): localhost:5432"
echo "    - User: anvil"
echo "    - Database: anvil_db"
echo ""
echo "  • Cache (Redis):         localhost:6379"
echo ""
echo "  • MCP Servers:"
echo "    - 1inch:               http://localhost:8081"
echo "    - Defillama:           http://localhost:8082"
echo "    - The Graph:           http://localhost:8083"
echo "    - CoinGecko:           http://localhost:8084"
echo "    - Aave:                http://localhost:8085"
echo "    - Portfolio:           http://localhost:8086"
echo "    - Perplexity:          http://localhost:8087"
echo "    - Morpho:              http://localhost:8088"
echo "    - Curve:               http://localhost:8089"
echo "    - Hyperliquid:         http://localhost:8090"
echo "    - LayerZero:           http://localhost:8091"
echo ""

echo -e "${YELLOW}Useful Commands:${NC}"
echo ""
echo "View logs:"
echo "  docker-compose logs -f fastapi"
echo "  docker-compose logs -f celery-worker-agents"
echo "  docker-compose logs -f celery-beat"
echo ""
echo "Scale a service:"
echo "  docker-compose up -d --scale celery-worker-agents=3"
echo "  docker-compose up -d --scale celery-worker-transactions=2"
echo ""
echo "Stop all services:"
echo "  docker-compose down"
echo ""
echo "Stop and remove volumes:"
echo "  docker-compose down -v"
echo ""
echo "Rebuild specific image:"
echo "  docker-compose build --no-cache fastapi"
echo ""
echo "Connect to database:"
echo "  psql -h localhost -U anvil -d anvil_db"
echo ""
echo "Connect to Redis:"
echo "  redis-cli -h localhost"
echo ""

echo -e "${GREEN}✓ Setup complete!${NC}"
