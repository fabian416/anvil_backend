# Docker Infrastructure - Anvil Backend

## Overview

Complete Docker containerization of the Anvil Backend hexagonal architecture with 27 independent services, optimized multi-stage builds, and production-ready Kubernetes configuration.

**Current Status**: ✅ All 27 services running and healthy

**Infrastructure Architecture:**
- **API Server**: FastAPI (8080) - REST API with health checks
- **Database**: PostgreSQL 16-alpine (5432) - Primary data store with 79+ tables
- **Cache/Broker**: Redis 7-alpine (6379) - Cache & Celery message broker
- **Task Scheduler**: Celery Beat (1 instance) - Task scheduling and orchestration
- **Workers**: Celery Workers (11 total)
  - 1 General worker (all queues fallback)
  - 9 Specialized workers with dedicated queues:
    - `agents` (8 concurrency) - AI/ML operations
    - `transactions` (6 concurrency) - 🔥 **CRITICAL** blockchain operations
    - `graph` (2 concurrency) - CPU-bound embeddings and graph processing
    - `distillation` (4 concurrency) - LLM model operations
    - `projects` (3 concurrency) - Knowledge base management
    - `llm` (4 concurrency) - Ranking and ranking operations
    - `maintenance` (2 concurrency) - System cleanup and maintenance
    - `risk` (3 concurrency) - Risk assessment and monitoring
    - `email` (2 concurrency) - Email delivery and notifications
- **MCP Servers**: 11 independent Model Context Protocol servers (ports 8081-8091)
  - DeFi/DEX: 1inch (8081), Defillama (8082), Curve (8089), Morpho (8088)
  - Blockchain: The Graph (8083), LayerZero (8091)
  - Crypto Data: CoinGecko (8084), Perplexity (8087)
  - Protocols: Aave (8085), Portfolio (8086), Hyperliquid (8090)
- **Monitoring**: Flower dashboard (5555) - Real-time Celery task monitoring
- **Utilities**: TX Confirmation worker - Blockchain transaction confirmation

**Total**: 27 services ✅

## Quick Start

### 1. ⚡ Fastest Way - One Command

```bash
cd /home/lucholeonel/CODE-werify/freelance/anvil_backend

# Start all 27 services with one command
docker-compose -f docker-compose.yaml up -d

# Wait ~30 seconds for health checks, then verify
docker-compose ps
```

### 2. 🔨 Full Setup from Scratch

```bash
cd /home/lucholeonel/CODE-werify/freelance/anvil_backend

# 1. Build all 14 Docker images (first time only, ~5-10 mins)
docker-compose -f docker-compose.yaml build

# 2. Start everything
docker-compose -f docker-compose.yaml up -d

# 3. Wait for health checks
sleep 30

# 4. Run database migrations (if needed)
docker-compose -f docker-compose.yaml run --rm fastapi alembic upgrade head

# 5. Verify all services
docker-compose -f docker-compose.yaml ps
```

### 3. ✅ Verification

```bash
# Check all 27 services are running
docker-compose -f docker-compose.yaml ps | grep -E "Up|healthy"

# Test FastAPI health
curl http://localhost:8080/health

# Test Redis
redis-cli -h localhost ping

# Test PostgreSQL
psql -h localhost -U anvil -d anvil_db -c "SELECT 1"

# View Flower dashboard
open http://localhost:5555  # or http://localhost:5555 in browser
```

## 🌐 Service Access Points

### Core Services
| Service | Port | URL | Purpose |
|---------|------|-----|---------|
| **FastAPI** | 8080 | http://localhost:8080 | REST API endpoints |
| **FastAPI Docs** | 8080 | http://localhost:8080/docs | Swagger/OpenAPI UI |
| **FastAPI Health** | 8080 | http://localhost:8080/health | Health status check |
| **Flower** | 5555 | http://localhost:5555 | Celery task monitoring ✨ |
| **PostgreSQL** | 5432 | localhost:5432 | Database (anvil_db) |
| **Redis** | 6379 | localhost:6379 | Cache & Celery broker |

### MCP Servers (Model Context Protocol)
| Service | Port | URL | Purpose |
|---------|------|-----|---------|
| 1inch MCP | 8081 | http://localhost:8081 | DEX aggregator data |
| Defillama MCP | 8082 | http://localhost:8082 | DeFi protocol data |
| The Graph MCP | 8083 | http://localhost:8083 | Blockchain indexing |
| CoinGecko MCP | 8084 | http://localhost:8084 | Crypto market data |
| Aave MCP | 8085 | http://localhost:8085 | Lending protocol data |
| Portfolio MCP | 8086 | http://localhost:8086 | Portfolio analytics |
| Perplexity MCP | 8087 | http://localhost:8087 | AI search capabilities |
| Morpho MCP | 8088 | http://localhost:8088 | Lending optimization |
| Curve MCP | 8089 | http://localhost:8089 | Stablecoin DEX data |
| Hyperliquid MCP | 8090 | http://localhost:8090 | Perpetuals exchange |
| LayerZero MCP | 8091 | http://localhost:8091 | Cross-chain messaging |

## 📊 Service Status and Verification

### Current Status (27/27 Services)

```bash
# View all running services
docker-compose -f docker-compose.yaml ps

# Count running services
docker-compose -f docker-compose.yaml ps --format "{{.Service}}" | wc -l

# Show only healthy services
docker-compose -f docker-compose.yaml ps --format "{{.Service}}: {{.Status}}" | grep healthy

# Show all services with status
docker-compose -f docker-compose.yaml ps --format "{{.Service}}: {{.Status}}" | sort
```

### Quick Health Check

```bash
# All services in one check
echo "📊 FastAPI:" && curl -s http://localhost:8080/health | jq . || echo "❌"
echo "📊 Redis:" && redis-cli -h localhost ping
echo "📊 PostgreSQL:" && psql -h localhost -U anvil -d anvil_db -c "SELECT 1" 2>/dev/null && echo "✅" || echo "❌"
echo "📊 Flower:" && curl -s http://localhost:5555 | head -1 | grep -q DOCTYPE && echo "✅" || echo "❌"
```

## Common Commands

### View Logs

```bash
# All services
docker-compose -f docker-compose.yaml logs -f

# Specific service
docker-compose -f docker-compose.yaml logs -f fastapi
docker-compose -f docker-compose.yaml logs -f celery-worker-agents
docker-compose -f docker-compose.yaml logs -f celery-beat

# MCP servers
docker-compose -f docker-compose.yaml logs -f mcp-1inch
docker-compose -f docker-compose.yaml logs -f mcp-defillama

# Last 50 lines only
docker-compose -f docker-compose.yaml logs --tail=50 fastapi
```

### Scale Services

```bash
# Scale agents worker to 3 instances (handle more AI operations)
docker-compose -f docker-compose.yaml up -d --scale celery-worker-agents=3

# Scale transactions worker to 2 instances (CRITICAL for blockchain)
docker-compose -f docker-compose.yaml up -d --scale celery-worker-transactions=2

# Scale graph worker to 4 instances (CPU-bound work)
docker-compose -f docker-compose.yaml up -d --scale celery-worker-graph=4

# View new total service count
docker-compose ps | tail -1
```

### Stop Services

```bash
# Stop all services (keep volumes and data)
docker-compose -f docker-compose.yaml down

# Stop all services and remove volumes (WARNING: data loss)
docker-compose -f docker-compose.yaml down -v

# Stop specific service
docker-compose -f docker-compose.yaml stop celery-worker-agents

# Start stopped service
docker-compose -f docker-compose.yaml start celery-worker-agents

# Restart specific service
docker-compose -f docker-compose.yaml restart celery-worker-agents
```

### Rebuild Images

```bash
# Rebuild all images (slow, but clears build cache)
docker-compose -f docker-compose.yaml build --no-cache

# Rebuild specific image
docker-compose -f docker-compose.yaml build --no-cache fastapi
docker-compose -f docker-compose.yaml build --no-cache celery-worker-agents

# Quick rebuild (uses cache)
docker-compose -f docker-compose.yaml build
```

### Database Operations

```bash
# Connect to PostgreSQL
psql -h localhost -U anvil -d anvil_db

# Run migrations
docker-compose -f docker-compose.yaml run --rm fastapi alembic upgrade head

# Rollback migrations (one step)
docker-compose -f docker-compose.yaml run --rm fastapi alembic downgrade -1

# Create new migration
docker-compose -f docker-compose.yaml run --rm fastapi alembic revision --autogenerate -m "Your migration name"

# View migration history
docker-compose -f docker-compose.yaml run --rm fastapi alembic history
```

### Redis Operations

```bash
# Connect to Redis CLI
redis-cli -h localhost

# From container
docker exec -it anvil_redis redis-cli

# Monitor all commands in real-time
docker exec -it anvil_redis redis-cli monitor

# Check memory usage
docker exec -it anvil_redis redis-cli info memory

# Clear all data
docker exec -it anvil_redis redis-cli flushall
```

### Service Inspection

```bash
# Check container status
docker-compose -f docker-compose.yaml ps

# Inspect container details
docker inspect anvil_fastapi
docker inspect anvil_celery_agents

# Execute command in container
docker-compose -f docker-compose.yaml exec fastapi ls -la /app
docker-compose -f docker-compose.yaml exec postgres psql -U anvil -d anvil_db -c "SELECT 1"
```

## Environment Variables

All services share these base environment variables (set in docker-compose.yaml):

```
APP_ENV=local
DATABASE_URL=postgresql://anvil:changethis@postgres:5432/anvil_db
REDIS_URL=redis://redis:6379
POSTGRES_HOST=postgres
POSTGRES_USER=anvil
POSTGRES_PASSWORD=changethis
POSTGRES_DB=anvil_db
POSTGRES_PORT=5432
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/1
```

For production, update these in:
1. `docker-compose.yaml` environment sections
2. `.env` files in `config/local/` or `config/prod/`

## Dockerfile Reference

### 1. Dockerfile.fastapi (250MB)
- Purpose: FastAPI HTTP API server
- Base: python:3.12-slim
- CMD: `uvicorn app.run:make_app --factory --host 0.0.0.0 --port 8080 --loop uvloop`
- Port: 8080
- Health check: Every 30s (GET /health)

### 2. Dockerfile.celery (200MB)
- Purpose: General Celery worker (all queues)
- Base: python:3.12-slim
- CMD: `celery -A app.infrastructure.celery.app.celery_app worker`

### 3. Dockerfile.celery-beat (180MB)
- Purpose: Celery Beat scheduler
- Base: python:3.12-slim
- CMD: `celery -A app.infrastructure.celery.app.celery_app beat`

### 4. Specialized Celery Workers

#### Dockerfile.celery-workers.agents (180MB)
- Queue: agents
- Concurrency: 8 (high capacity, AI operations)
- CMD: `-Q agents -n agents@%h --concurrency=8`

#### Dockerfile.celery-workers.transactions (180MB)
- Queue: transactions
- Concurrency: 6 (CRITICAL, blockchain operations)
- CMD: `-Q transactions -n transactions@%h --concurrency=6`

#### Dockerfile.celery-workers.graph (180MB)
- Queue: graph
- Concurrency: 2 (CPU-bound, embeddings)
- CMD: `-Q graph -n graph@%h --concurrency=2`

#### Dockerfile.celery-workers.distillation (180MB)
- Queue: distillation
- Concurrency: 4 (LLM processing)
- CMD: `-Q distillation -n distillation@%h --concurrency=4`

#### Dockerfile.celery-workers.projects (180MB)
- Queue: projects
- Concurrency: 3 (Knowledge base)
- CMD: `-Q projects -n projects@%h --concurrency=3`

#### Dockerfile.celery-workers.llm (180MB)
- Queue: llm
- Concurrency: 4 (Ranking operations)
- CMD: `-Q llm -n llm@%h --concurrency=4`

#### Dockerfile.celery-workers.maintenance (180MB)
- Queue: maintenance
- Concurrency: 2 (Low priority, cleanup)
- CMD: `-Q maintenance -n maintenance@%h --concurrency=2`

#### Dockerfile.celery-workers.risk (180MB)
- Queue: risk
- Concurrency: 3 (Risk monitoring)
- CMD: `-Q risk -n risk@%h --concurrency=3`

#### Dockerfile.celery-workers.email (180MB)
- Queue: email
- Concurrency: 2 (Email sending)
- CMD: `-Q email -n email@%h --concurrency=2`

### 5. Dockerfile.mcp (180MB, Generic)
- Purpose: Generic MCP server (parametrized)
- ARG: `MCP_SERVER=oneinch_mcp` (configurable per service)
- Base: python:3.12-slim
- CMD: `python -m app.infrastructure.mcp.servers.${MCP_SERVER}`
- Used for: All 11 MCP servers

### 6. Dockerfile.tx-confirmation (180MB)
- Purpose: Transaction confirmation worker
- Base: python:3.12-slim
- CMD: `python -m app.cli.confirm_pending_transactions --loop --log-level INFO`

## Performance Optimization

### Multi-Stage Builds
- Builder stage: Installs dependencies, minimal final size
- Runtime stage: Only what's needed to run the application
- Final image size: 180-250MB per service (vs 500MB+ monolithic)

### Dependency Management
- Uses `uv` for fast, reliable dependency resolution
- Requirements installed in builder stage only
- Runtime stage doesn't include build tools

### Resource Allocation

| Service | CPU | Memory | Priority |
|---------|-----|--------|----------|
| FastAPI | 2 | 1GB | High |
| Celery Beat | 0.5 | 256MB | High |
| Celery Workers (agents) | 2 | 512MB | High |
| Celery Workers (transactions) | 2 | 1GB | 🔥 CRITICAL |
| Celery Workers (other) | 1 | 512MB | Medium |
| MCP Servers | 0.5 | 256MB | Medium |
| PostgreSQL | 2 | 2GB | 🔥 CRITICAL |
| Redis | 1 | 512MB | 🔥 CRITICAL |

## 🔧 Troubleshooting Guide

### ❌ Services won't start

```bash
# 1. Check all logs for errors
docker-compose -f docker-compose.yaml logs --tail=100

# 2. Check specific service
docker-compose -f docker-compose.yaml logs fastapi | tail -50

# 3. Check Docker daemon is running
docker ps

# 4. Check resource availability
docker stats --no-stream

# 5. Try full restart
docker-compose -f docker-compose.yaml down
docker-compose -f docker-compose.yaml up -d
```

### 🗄️ Database connection errors

```bash
# 1. Check PostgreSQL is running and healthy
docker-compose -f docker-compose.yaml ps postgres

# 2. Test PostgreSQL readiness
docker exec anvil_postgres pg_isready -U anvil

# 3. Connect to database
docker exec -it anvil_postgres psql -U anvil -d anvil_db

# 4. Check if anvil_db exists
docker exec anvil_postgres psql -U anvil -c "\l"

# 5. Check volumes are mounted
docker volume ls | grep pg_data
```

### 🎯 Celery workers not processing tasks

```bash
# 1. Check Celery Beat is running
docker-compose -f docker-compose.yaml ps celery-beat

# 2. View Flower dashboard
# Open: http://localhost:5555

# 3. Check specific worker logs
docker-compose -f docker-compose.yaml logs -f celery-worker-agents

# 4. Test Redis connection
docker exec anvil_redis redis-cli ping

# 5. Check Celery Beat is scheduling
docker-compose -f docker-compose.yaml logs celery-beat | tail -50

# 6. Monitor Redis activity
docker exec -it anvil_redis redis-cli monitor
```

### 🚨 High memory or CPU usage

```bash
# 1. Check Docker resource usage
docker stats --no-stream

# 2. Check memory per service
docker stats --format "table {{.Container}}\t{{.MemUsage}}"

# 3. Scale down high-concurrency workers
docker-compose -f docker-compose.yaml up -d --scale celery-worker-agents=1

# 4. Check Redis memory
docker exec anvil_redis redis-cli info memory

# 5. Check PostgreSQL connections
docker exec anvil_postgres psql -U anvil -d anvil_db -c "SELECT count(*) FROM pg_stat_activity;"
```

### 🔌 MCP Server not responding

```bash
# 1. Check MCP container is running
docker-compose -f docker-compose.yaml ps mcp-1inch

# 2. Test MCP endpoint directly
curl http://localhost:8081

# 3. Check MCP logs
docker-compose -f docker-compose.yaml logs mcp-1inch | tail -50

# 4. Verify port is accessible
netstat -tulpn | grep 8081  # or ss -tulpn | grep 8081

# 5. Check container health
docker inspect anvil_mcp_1inch | grep -A 3 Health
```

### 🚀 Performance optimization

```bash
# 1. Monitor service health
watch -n 1 'docker-compose ps --format "{{.Service}}: {{.Status}}"'

# 2. Monitor resource usage in real-time
docker stats

# 3. Analyze slow queries
docker exec anvil_postgres psql -U anvil -d anvil_db -c "SELECT query, calls, total_time FROM pg_stat_statements ORDER BY total_time DESC LIMIT 10;"

# 4. Check Redis performance
docker exec anvil_redis redis-cli info stats

# 5. Restart slow service without affecting others
docker-compose -f docker-compose.yaml restart celery-worker-agents
```

## Production Deployment

For production deployment to Kubernetes:

1. **Update credentials** in `docker-compose.yaml`:
   - `POSTGRES_PASSWORD`
   - Other secrets in `config/prod/.secrets.toml`

2. **Use external services**:
   - PostgreSQL: Managed database (AWS RDS, Google Cloud SQL, etc.)
   - Redis: Managed cache (AWS ElastiCache, Google Memorystore, etc.)

3. **Generate Kubernetes manifests**:
   ```bash
   kompose convert -f docker/docker-compose.yaml -o k8s/
   ```

4. **Adjust resource limits** in Kubernetes YAML files

5. **Set up health checks and liveness probes**

6. **Configure auto-scaling** for Celery workers

## ✨ Architecture Benefits

✅ **27 Independent Services**: Each service scales and updates independently  
✅ **Resource Efficient**: 180-250MB per image (vs 500MB+ monolithic)  
✅ **Kubernetes Ready**: All services containerized with health checks  
✅ **Zero Application Changes**: 100% infrastructure layer, no code mods  
✅ **Full Monitoring**: Flower dashboard + health endpoints  
✅ **Production Grade**: Multi-stage builds, health checks, networking  
✅ **Queue-Isolated Workers**: Dedicated workers per task queue  
✅ **DeFi MCP Integration**: 11 specialized blockchain/protocol servers  
✅ **Easy Debugging**: Clear logs and monitoring per service  
✅ **Persistent Data**: PostgreSQL + Redis with named volumes  

## 📈 Scalability Example

```bash
# Scale agents worker to 3 instances (handle more AI operations)
docker-compose -f docker-compose.yaml up -d --scale celery-worker-agents=3

# Scale transactions worker to 2 instances (CRITICAL for blockchain)
docker-compose -f docker-compose.yaml up -d --scale celery-worker-transactions=2

# Scale graph worker to 4 instances (CPU-bound work)
docker-compose -f docker-compose.yaml up -d --scale celery-worker-graph=4

# View new total service count
docker-compose ps | tail -1
```  

## Support

For issues or questions about this Docker infrastructure:
1. Check logs: `docker-compose -f docker/docker-compose.yaml logs`
2. Review this README
3. Check individual Dockerfiles for base configurations
4. Inspect container details with `docker inspect`
