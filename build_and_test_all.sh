#!/bin/bash
# Script to build and test all Docker images one by one
# Usage: ./build_and_test_all.sh

set -e

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "🔨 Building and testing all Docker images..."
echo ""

# Track results
SUCCESSFUL=()
FAILED=()

# Function to build and test an image
build_and_test() {
    local service=$1
    local dockerfile=$2
    local image_name=$3
    
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo -e "${YELLOW}📦 Building: $service${NC}"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    
    # Build
    if docker build -f "$dockerfile" -t "$image_name" . 2>&1 | tee "/tmp/build_${service}.log"; then
        echo -e "${GREEN}✅ Build successful: $service${NC}"
        
        # Get image size
        SIZE=$(docker images "$image_name" --format "{{.Size}}")
        echo -e "${GREEN}   Size: $SIZE${NC}"
        
        SUCCESSFUL+=("$service ($SIZE)")
        
        # Save build log
        echo "   Build log saved: /tmp/build_${service}.log"
    else
        echo -e "${RED}❌ Build failed: $service${NC}"
        FAILED+=("$service")
        echo "   Check log: /tmp/build_${service}.log"
        return 1
    fi
}

# Define all images to build
declare -A IMAGES

# API
IMAGES["fastapi"]="docker/Dockerfile.fastapi|ghcr.io/lucholeonel/anvil-backend-api:infra"

# Celery
IMAGES["celery-worker"]="docker/Dockerfile.celery|ghcr.io/lucholeonel/anvil-backend-celery-worker:infra"
IMAGES["celery-beat"]="docker/Dockerfile.celery-beat|ghcr.io/lucholeonel/anvil-backend-celery-beat:infra"

# Celery Specialized Workers
IMAGES["celery-worker-llm"]="docker/Dockerfile.celery-workers.llm|ghcr.io/lucholeonel/anvil-backend-celery-worker-llm:infra"
IMAGES["celery-worker-agents"]="docker/Dockerfile.celery-workers.agents|ghcr.io/lucholeonel/anvil-backend-celery-worker-agents:infra"
IMAGES["celery-worker-graph"]="docker/Dockerfile.celery-workers.graph|ghcr.io/lucholeonel/anvil-backend-celery-worker-graph:infra"
IMAGES["celery-worker-distillation"]="docker/Dockerfile.celery-workers.distillation|ghcr.io/lucholeonel/anvil-backend-celery-worker-distillation:infra"
IMAGES["celery-worker-risk"]="docker/Dockerfile.celery-workers.risk|ghcr.io/lucholeonel/anvil-backend-celery-worker-risk:infra"
IMAGES["celery-worker-email"]="docker/Dockerfile.celery-workers.email|ghcr.io/lucholeonel/anvil-backend-celery-worker-email:infra"
IMAGES["celery-worker-transactions"]="docker/Dockerfile.celery-workers.transactions|ghcr.io/lucholeonel/anvil-backend-celery-worker-transactions:infra"
IMAGES["celery-worker-projects"]="docker/Dockerfile.celery-workers.projects|ghcr.io/lucholeonel/anvil-backend-celery-worker-projects:infra"
IMAGES["celery-worker-maintenance"]="docker/Dockerfile.celery-workers.maintenance|ghcr.io/lucholeonel/anvil-backend-celery-worker-maintenance:infra"

# MCP Servers (all use same Dockerfile.mcp)
IMAGES["mcp-1inch"]="docker/Dockerfile.mcp|ghcr.io/lucholeonel/anvil-backend-mcp-1inch:infra"
IMAGES["mcp-defillama"]="docker/Dockerfile.mcp|ghcr.io/lucholeonel/anvil-backend-mcp-defillama:infra"
IMAGES["mcp-thegraph"]="docker/Dockerfile.mcp|ghcr.io/lucholeonel/anvil-backend-mcp-thegraph:infra"
IMAGES["mcp-coingecko"]="docker/Dockerfile.mcp|ghcr.io/lucholeonel/anvil-backend-mcp-coingecko:infra"
IMAGES["mcp-aave"]="docker/Dockerfile.mcp|ghcr.io/lucholeonel/anvil-backend-mcp-aave:infra"
IMAGES["mcp-portfolio"]="docker/Dockerfile.mcp|ghcr.io/lucholeonel/anvil-backend-mcp-portfolio:infra"
IMAGES["mcp-perplexity"]="docker/Dockerfile.mcp|ghcr.io/lucholeonel/anvil-backend-mcp-perplexity:infra"
IMAGES["mcp-morpho"]="docker/Dockerfile.mcp|ghcr.io/lucholeonel/anvil-backend-mcp-morpho:infra"
IMAGES["mcp-curve"]="docker/Dockerfile.mcp|ghcr.io/lucholeonel/anvil-backend-mcp-curve:infra"
IMAGES["mcp-hyperliquid"]="docker/Dockerfile.mcp|ghcr.io/lucholeonel/anvil-backend-mcp-hyperliquid:infra"
IMAGES["mcp-layerzero"]="docker/Dockerfile.mcp|ghcr.io/lucholeonel/anvil-backend-mcp-layerzero:infra"

# TX Confirmation
IMAGES["tx-confirmation"]="docker/Dockerfile.tx-confirmation|ghcr.io/lucholeonel/anvil-backend-tx-confirmation:infra"

# Build each image
for service in "${!IMAGES[@]}"; do
    IFS='|' read -r dockerfile image_name <<< "${IMAGES[$service]}"
    
    # Ask before building each (optional)
    # read -p "Build $service? (y/n) " -n 1 -r
    # echo
    # if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    #     echo "⏭️  Skipped: $service"
    #     continue
    # fi
    
    build_and_test "$service" "$dockerfile" "$image_name" || true
    
    # Small delay to not overwhelm system
    sleep 1
done

# Summary
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📊 BUILD SUMMARY"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo -e "${GREEN}✅ Successful builds (${#SUCCESSFUL[@]}):${NC}"
for img in "${SUCCESSFUL[@]}"; do
    echo "   • $img"
done

if [ ${#FAILED[@]} -gt 0 ]; then
    echo ""
    echo -e "${RED}❌ Failed builds (${#FAILED[@]}):${NC}"
    for img in "${FAILED[@]}"; do
        echo "   • $img"
    done
    echo ""
    echo "Check individual logs in /tmp/build_*.log"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if [ ${#FAILED[@]} -eq 0 ]; then
    echo -e "${GREEN}🎉 All images built successfully!${NC}"
    echo ""
    echo "Next steps:"
    echo "1. Push images: ./push_all_images.sh"
    echo "2. Deploy to server: ssh server && docker compose pull && docker compose up -d"
    exit 0
else
    echo -e "${RED}⚠️  Some builds failed. Fix errors before pushing.${NC}"
    exit 1
fi
