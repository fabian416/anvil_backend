#!/bin/bash

# ==============================================================================
# QUICK REFERENCE - Docker Commands for Anvil Backend
# ==============================================================================

# Color codes
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

show_help() {
    echo ""
    echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║     Docker Infrastructure - Anvil Backend Quick Reference     ║${NC}"
    echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    
    echo -e "${YELLOW}📚 INITIALIZATION & SETUP${NC}"
    echo "  ${GREEN}./docker-init.sh${NC}"
    echo "    → Complete setup: build, migrate, start, verify"
    echo ""
    
    echo -e "${YELLOW}🚀 START / STOP SERVICES${NC}"
    echo "  ${GREEN}docker-compose -f docker/docker-compose.yaml up -d${NC}"
    echo "    → Start all services in background"
    echo ""
    echo "  ${GREEN}docker-compose -f docker/docker-compose.yaml down${NC}"
    echo "    → Stop all services"
    echo ""
    echo "  ${GREEN}docker-compose -f docker/docker-compose.yaml down -v${NC}"
    echo "    → Stop all services and remove volumes"
    echo ""
    
    echo -e "${YELLOW}📊 VIEW LOGS${NC}"
    echo "  ${GREEN}docker-compose -f docker/docker-compose.yaml logs -f${NC}"
    echo "    → View all service logs (follow mode)"
    echo ""
    echo "  ${GREEN}docker-compose -f docker/docker-compose.yaml logs -f fastapi${NC}"
    echo "    → View FastAPI logs"
    echo ""
    echo "  ${GREEN}docker-compose -f docker/docker-compose.yaml logs -f celery-worker-agents${NC}"
    echo "    → View specific worker logs"
    echo ""
    
    echo -e "${YELLOW}📈 SCALE SERVICES${NC}"
    echo "  ${GREEN}docker-compose -f docker/docker-compose.yaml up -d --scale celery-worker-agents=3${NC}"
    echo "    → Scale agents worker to 3 instances"
    echo ""
    echo "  ${GREEN}docker-compose -f docker/docker-compose.yaml up -d --scale celery-worker-transactions=2${NC}"
    echo "    → Scale transactions worker to 2 instances (CRITICAL)"
    echo ""
    
    echo -e "${YELLOW}🔄 REBUILD IMAGES${NC}"
    echo "  ${GREEN}docker-compose -f docker/docker-compose.yaml build --no-cache${NC}"
    echo "    → Rebuild all images"
    echo ""
    echo "  ${GREEN}docker-compose -f docker/docker-compose.yaml build --no-cache fastapi${NC}"
    echo "    → Rebuild specific image"
    echo ""
    
    echo -e "${YELLOW}🗄️  DATABASE OPERATIONS${NC}"
    echo "  ${GREEN}docker-compose -f docker/docker-compose.yaml run --rm fastapi alembic upgrade head${NC}"
    echo "    → Run database migrations"
    echo ""
    echo "  ${GREEN}psql -h localhost -U anvil -d anvil_db${NC}"
    echo "    → Connect to PostgreSQL"
    echo ""
    
    echo -e "${YELLOW}💾 REDIS OPERATIONS${NC}"
    echo "  ${GREEN}redis-cli -h localhost${NC}"
    echo "    → Connect to Redis CLI"
    echo ""
    echo "  ${GREEN}docker exec anvil_redis redis-cli monitor${NC}"
    echo "    → Monitor Redis commands"
    echo ""
    
    echo -e "${YELLOW}📱 ACCESS SERVICES${NC}"
    echo "  ${GREEN}http://localhost:8080${NC}"
    echo "    → FastAPI API"
    echo ""
    echo "  ${GREEN}http://localhost:8080/docs${NC}"
    echo "    → FastAPI Swagger Docs"
    echo ""
    echo "  ${GREEN}http://localhost:8080/health${NC}"
    echo "    → Health Check"
    echo ""
    echo "  ${GREEN}http://localhost:5555${NC}"
    echo "    → Flower Celery Monitoring"
    echo ""
    echo "  ${GREEN}http://localhost:8081-8091${NC}"
    echo "    → MCP Servers (1inch, Defillama, The Graph, etc.)"
    echo ""
    
    echo -e "${YELLOW}🔍 STATUS & INSPECTION${NC}"
    echo "  ${GREEN}docker-compose -f docker/docker-compose.yaml ps${NC}"
    echo "    → List all running containers"
    echo ""
    echo "  ${GREEN}docker stats${NC}"
    echo "    → Monitor resource usage"
    echo ""
    echo "  ${GREEN}docker inspect anvil_fastapi${NC}"
    echo "    → Inspect container details"
    echo ""
    
    echo -e "${YELLOW}🛠️  TROUBLESHOOTING${NC}"
    echo "  ${GREEN}docker-compose -f docker/docker-compose.yaml ps${NC}"
    echo "    → Check if all services are running"
    echo ""
    echo "  ${GREEN}docker-compose -f docker/docker-compose.yaml logs --tail=100 fastapi${NC}"
    echo "    → View last 100 lines of FastAPI logs"
    echo ""
    echo "  ${GREEN}curl http://localhost:8080/health${NC}"
    echo "    → Test FastAPI health endpoint"
    echo ""
    
    echo -e "${YELLOW}📖 DOCUMENTATION${NC}"
    echo "  ${GREEN}docker/README.md${NC}"
    echo "    → Complete Docker documentation"
    echo ""
    echo "  ${GREEN}DOCKER_SETUP_COMPLETE.md${NC}"
    echo "    → Setup summary and next steps"
    echo ""
    
    echo -e "${GREEN}════════════════════════════════════════════════════════════${NC}"
    echo ""
}

# Show help if no arguments or --help
if [ $# -eq 0 ] || [ "$1" == "--help" ] || [ "$1" == "-h" ]; then
    show_help
    exit 0
fi

# Common shortcuts
case "$1" in
    start)
        docker-compose -f docker/docker-compose.yaml up -d
        ;;
    stop)
        docker-compose -f docker/docker-compose.yaml down
        ;;
    logs)
        docker-compose -f docker/docker-compose.yaml logs -f "${@:2}"
        ;;
    ps)
        docker-compose -f docker/docker-compose.yaml ps
        ;;
    build)
        docker-compose -f docker/docker-compose.yaml build --no-cache "${@:2}"
        ;;
    scale)
        docker-compose -f docker/docker-compose.yaml up -d --scale "$2"
        ;;
    *)
        show_help
        exit 1
        ;;
esac
