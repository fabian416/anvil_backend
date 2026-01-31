# Infrastructure Guide - Complete Docker Setup

## 📋 Table of Contents

1. [Quick Start](#quick-start)
2. [Architecture Overview](#architecture-overview)
3. [Service Details](#service-details)
4. [Operational Guide](#operational-guide)
5. [Troubleshooting](#troubleshooting)
6. [Production Deployment](#production-deployment)

---

## Quick Start

### Start Everything (One Command)

```bash
cd /home/lucholeonel/CODE-werify/freelance/anvil_backend
docker-compose -f docker-compose.yaml up -d
```

**That's it!** All 27 services will start automatically. Wait ~30 seconds for health checks.

### Verify Everything is Running

```bash
# Check all services
docker-compose -f docker-compose.yaml ps

# Quick health check
curl http://localhost:8080/health
```

---

## Architecture Overview

### 27 Services Total ✅

```
┌─────────────────────────────────────────────────────────┐
│                                                           │
│  🌐 API & Core Services (3)                              │
│  ├─ FastAPI (8080) - HTTP API                            │
│  ├─ PostgreSQL (5432) - Database                         │
│  └─ Redis (6379) - Cache & Broker                        │
│                                                           │
│  📋 Task Scheduling & Workers (11)                       │
│  ├─ Celery Beat (1) - Scheduler                          │
│  ├─ Celery Worker General (1)                            │
│  └─ Specialized Workers (9)                              │
│     ├─ agents (8 concurrency)                            │
│     ├─ transactions (6 concurrency) 🔥 CRITICAL          │
│     ├─ graph (2 concurrency)                             │
│     ├─ distillation (4 concurrency)                      │
│     ├─ projects (3 concurrency)                          │
│     ├─ llm (4 concurrency)                               │
│     ├─ maintenance (2 concurrency)                       │
│     ├─ risk (3 concurrency)                              │
│     └─ email (2 concurrency)                             │
│                                                           │
│  🔌 MCP Servers (11)                                     │
│  ├─ 1inch (8081) - DEX Aggregator                        │
│  ├─ Defillama (8082) - DeFi Protocols                    │
│  ├─ The Graph (8083) - Blockchain Indexing              │
│  ├─ CoinGecko (8084) - Crypto Market Data               │
│  ├─ Aave (8085) - Lending Protocol                       │
│  ├─ Portfolio (8086) - Analytics                         │
│  ├─ Perplexity (8087) - AI Search                        │
│  ├─ Morpho (8088) - Lending Optimization                │
│  ├─ Curve (8089) - Stablecoin DEX                        │
│  ├─ Hyperliquid (8090) - Perpetuals Exchange             │
│  └─ LayerZero (8091) - Cross-chain Messaging             │
│                                                           │
│  � Reverse Proxy (1)                                    │
│  └─ Caddy - HTTPS & Routing (80, 443)                    │
│                                                           │
│  📊 Monitoring (1)                                       │
│  └─ Flower (5555) - Celery Dashboard                     │
│                                                           │
│  🛠️ Utilities (1)                                         │
│  └─ TX Confirmation - Blockchain Confirmation           │
│                                                           │
│  TOTAL: 28 SERVICES                                       │
│                                                           │
└─────────────────────────────────────────────────────────┘
```

### Service Dependencies

```
Application Layer:
  FastAPI → PostgreSQL ✓
  FastAPI → Redis ✓
  
Proxy Layer:
  Caddy → FastAPI (API routes) ✓
  Caddy → Flower (/flower/*) ✓
  Caddy → MCP Servers (/mcp/*) ✓
  
Task Layer:
  Celery Beat → Redis ✓
  Celery Workers → Redis (broker) ✓
  Celery Workers → PostgreSQL (results) ✓
  
MCP Layer:
  MCP Servers → Redis (optional cache) ✓
  
Monitoring:
  Flower → Redis ✓
  Flower → Celery Workers ✓
```

---

## Service Details

### 1. API Server - FastAPI (8080)

**Purpose**: RESTful HTTP API with 233+ endpoints

```bash
# Health check
curl http://localhost:8080/health

# View API documentation
open http://localhost:8080/docs

# View all endpoints
curl http://localhost:8080/openapi.json | jq .
```

**Ports**: 8080 (HTTP)  
**Image Size**: 250MB  
**Health Check**: Every 30 seconds  

### 2. Database - PostgreSQL (5432)

**Purpose**: Primary data store, 79+ tables

```bash
# Connect
psql -h localhost -U anvil -d anvil_db

# List tables
\dt

# Check database size
SELECT pg_size_pretty(pg_database_size('anvil_db'));

# View active connections
SELECT count(*) FROM pg_stat_activity;
```

**Ports**: 5432 (PostgreSQL)  
**Image**: postgres:16-alpine  
**Volume**: `pg_data` (persistent)  
**Credentials**: 
- User: `anvil`
- Password: `changethis` (change in production!)
- Database: `anvil_db`

### 3. Cache & Broker - Redis (6379)

**Purpose**: Caching, Celery message broker, session storage

```bash
# Connect
redis-cli -h localhost

# Check memory
INFO memory

# Monitor commands
MONITOR

# Clear cache
FLUSHDB

# Check keys
KEYS *
```

**Ports**: 6379 (Redis)  
**Image**: redis:7-alpine  
**Volume**: `redis_data` (persistent)  

### 4. Task Scheduler - Celery Beat

**Purpose**: Schedule periodic tasks

```bash
# View logs
docker-compose logs -f celery-beat

# Scheduled tasks are defined in:
# - app/application/scheduled_tasks.py
# - Configuration in docker-compose.yaml
```

**Queue**: Default (all tasks)  
**Image Size**: 180MB  

### 5. Celery Workers (11 Total)

#### General Worker
- **Queue**: All queues
- **Purpose**: Fallback, handles all task types
- **Concurrency**: Auto (defaults)

#### Specialized Workers

| Worker | Queue | Concurrency | Purpose |
|--------|-------|-------------|---------|
| agents | agents | 8 | AI operations, embeddings |
| transactions | transactions | 6 | 🔥 Blockchain operations (CRITICAL) |
| graph | graph | 2 | CPU-intensive graph processing |
| distillation | distillation | 4 | LLM model operations |
| projects | projects | 3 | Knowledge base management |
| llm | llm | 4 | Ranking & ranking operations |
| maintenance | maintenance | 2 | Cleanup, maintenance tasks |
| risk | risk | 3 | Risk assessment operations |
| email | email | 2 | Email sending |

**Each Worker**:
- Image Size: 180MB
- Health Check: Yes
- Logging: STDOUT + docker logs

### 6. MCP Servers (11 Total)

Model Context Protocol servers for external data access.

```bash
# Test MCP server
curl http://localhost:8081/

# View MCP logs
docker-compose logs -f mcp-1inch

# Check all MCP servers
for port in {8081..8091}; do
  echo -n "Port $port: "
  curl -s http://localhost:$port/ | head -1 || echo "❌"
done
```

**Each MCP Server**:
- Image Size: 180MB
- Health Check: Yes
- Protocol: HTTP/JSON-RPC

### 7. Monitoring - Flower (5555)

Celery task monitoring dashboard.

```bash
# Open dashboard
open http://localhost:5555

# View API
curl http://localhost:5555/api/workers
curl http://localhost:5555/api/tasks
```

**Features**:
- Real-time task monitoring
- Worker status
- Task history
- Resource usage

### 8. TX Confirmation Worker

Blockchain transaction confirmation.

```bash
# View logs
docker-compose logs -f tx-confirmation

# Check status
docker-compose ps tx-confirmation
```

---

## Operational Guide

### Daily Operations

#### Morning Checklist

```bash
#!/bin/bash
echo "🌅 Morning Infrastructure Check"

# 1. All services running?
echo "1️⃣ Service count:"
docker-compose ps --format "{{.Service}}" | wc -l

# 2. Healthy?
echo "2️⃣ Healthy services:"
docker-compose ps --format "{{.Service}}: {{.Status}}" | grep healthy | wc -l

# 3. API responding?
echo "3️⃣ FastAPI:"
curl -s http://localhost:8080/health | jq .status

# 4. Database?
echo "4️⃣ PostgreSQL:"
psql -h localhost -U anvil -d anvil_db -c "SELECT '✅ OK';" 2>/dev/null || echo "❌ Error"

# 5. Redis?
echo "5️⃣ Redis:"
redis-cli -h localhost ping

# 6. Workers?
echo "6️⃣ Celery workers:"
docker-compose ps --format "{{.Service}}: {{.State}}" | grep celery-worker | wc -l
```

#### Scaling for Load

```bash
# Detect high load
docker stats --no-stream | grep -E "celery|fastapi"

# Scale up agents (AI operations)
docker-compose -f docker-compose.yaml up -d --scale celery-worker-agents=3

# Scale up transactions (blockchain)
docker-compose -f docker-compose.yaml up -d --scale celery-worker-transactions=2

# View new setup
docker-compose ps --format "{{.Service}}" | wc -l
```

#### Performance Monitoring

```bash
# Real-time resource usage
watch -n 1 'docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}"'

# Database queries
docker exec anvil_postgres psql -U anvil -d anvil_db -c "
  SELECT query, calls, total_time 
  FROM pg_stat_statements 
  ORDER BY total_time DESC 
  LIMIT 10;"

# Redis memory
docker exec anvil_redis redis-cli info memory | grep used

# Task queue depth
docker exec anvil_redis redis-cli LLEN celery
```

### Maintenance

#### Database Backups

```bash
# Backup
docker exec anvil_postgres pg_dump -U anvil anvil_db > backup-$(date +%Y%m%d-%H%M%S).sql

# Restore
docker exec -i anvil_postgres psql -U anvil anvil_db < backup-20250124-120000.sql
```

#### Clean Up

```bash
# Remove old containers
docker-compose down

# Clean up dangling images
docker image prune -f

# Clean up unused volumes
docker volume prune -f

# Clean Docker system
docker system prune -f
```

#### Restart Strategy

```bash
# Graceful restart (keep data)
docker-compose down
docker-compose up -d

# Full restart with volume reset
docker-compose down -v
docker-compose build
docker-compose up -d

# Restart single service
docker-compose restart celery-worker-agents
```

---

## Troubleshooting

### Common Issues

#### Issue: Services keep restarting

```bash
# 1. Check logs
docker-compose logs --tail=100

# 2. Check resource
docker stats --no-stream

# 3. Check dependencies
docker-compose ps
docker inspect anvil_fastapi | grep -A 10 "DependsOn\|HealthCheck"

# 4. Full restart
docker-compose down
docker-compose up -d
```

#### Issue: Database won't connect

```bash
# 1. Check PostgreSQL running
docker-compose ps postgres

# 2. Check port
docker port anvil_postgres 5432

# 3. Test connection
docker exec anvil_postgres pg_isready -U anvil

# 4. Check credentials
psql -h localhost -U anvil -d anvil_db

# 5. Check volumes
docker volume ls | grep pg_data
```

#### Issue: Celery tasks not processing

```bash
# 1. Check Celery Beat
docker-compose ps celery-beat
docker-compose logs -f celery-beat

# 2. Check worker queues
docker-compose ps | grep celery-worker

# 3. Check Redis
redis-cli -h localhost ping

# 4. Monitor Flower
open http://localhost:5555

# 5. Check task queue
redis-cli -h localhost LLEN celery
redis-cli -h localhost KEYS "celery*"
```

#### Issue: Memory/CPU spike

```bash
# 1. Identify culprit
docker stats --no-stream | sort -k4 -rh | head -5

# 2. Check logs
docker logs <container_name> --tail=50

# 3. Scale down worker
docker-compose up -d --scale celery-worker-agents=1

# 4. Restart container
docker-compose restart <service>

# 5. Check Redis memory
docker exec anvil_redis redis-cli info memory

# 6. Check DB connections
docker exec anvil_postgres psql -U anvil -d anvil_db -c "SELECT count(*) FROM pg_stat_activity;"
```

### Debug Commands

```bash
# View all environment variables
docker-compose config | grep -A 50 environment

# Execute bash in container
docker-compose exec fastapi bash

# Check network connectivity
docker-compose exec fastapi ping redis
docker-compose exec fastapi ping postgres

# View container resource limits
docker inspect anvil_fastapi | grep -A 20 Resources

# View all port bindings
docker-compose ps --format "table {{.Service}}\t{{.Ports}}"
```

---

## Production Deployment

### Pre-Production Checklist

```bash
# 1. Update credentials
sed -i 's/changethis/YOUR_STRONG_PASSWORD/g' docker-compose.yaml

# 2. Set production environment
export APP_ENV=production

# 3. Test full deployment
docker-compose build
docker-compose up -d

# 4. Run migrations
docker-compose run --rm fastapi alembic upgrade head

# 5. Verify all services
docker-compose ps
```

### Kubernetes Conversion

```bash
# Install kompose
brew install kompose  # or appropriate package manager

# Convert to Kubernetes manifests
cd /home/lucholeonel/CODE-werify/freelance/anvil_backend
kompose convert -f docker-compose.yaml -o k8s/

# Review generated files
ls k8s/

# Adjust resources in generated YAML files
# - Update memory/CPU limits in deployment files
# - Configure persistent volumes for postgres/redis
# - Set up ingress for FastAPI
```

### Recommendations

**Reverse Proxy**: Caddy (automatic HTTPS, configured) ✅  
**Database**: Use managed PostgreSQL (AWS RDS, Cloud SQL)  
**Cache**: Use managed Redis (ElastiCache, Memorystore)  
**Containers**: Docker Compose (current) or Kubernetes  
**Monitoring**: Prometheus + Grafana  
**Logging**: ELK Stack or Cloud Logging  
**Secrets**: Use secrets manager (Vault, Secrets Manager)  

---

## Production Architecture (Current Setup)

### HTTPS & Routing with Caddy

```
Internet (HTTPS:443)
    ↓
Caddy (automatic SSL)
    ├─ /health, /api/v1/* → FastAPI:8080
    ├─ /flower/* → Flower:5555
    └─ /mcp/{service}/* → MCP Servers (8081-8091)
         ├─ /mcp/1inch/* → 8081
         ├─ /mcp/defillama/* → 8082
         ├─ /mcp/thegraph/* → 8083
         ├─ /mcp/coingecko/* → 8084
         ├─ /mcp/aave/* → 8085
         ├─ /mcp/portfolio/* → 8086
         ├─ /mcp/perplexity/* → 8087
         ├─ /mcp/morpho/* → 8088
         ├─ /mcp/curve/* → 8089
         ├─ /mcp/hyperliquid/* → 8090
         └─ /mcp/layerzero/* → 8091
```

**Caddyfile Location**: `docker/Caddyfile`

### Public Endpoints (via Caddy)

| URL Pattern | Destination | Purpose |
|-------------|-------------|---------|
| `https://{domain}/health` | FastAPI:8080 | Health check |
| `https://{domain}/api/v1/*` | FastAPI:8080 | API routes |
| `https://{domain}/flower/*` | Flower:5555 | Celery monitoring |
| `https://{domain}/mcp/{service}/*` | MCP:808x | MCP services |

---

## Key Metrics to Monitor

- **API Response Time**: `curl -w "@curl-format.txt"` or APM tool
- **Task Queue Depth**: `redis-cli LLEN celery`
- **Worker Count**: `docker-compose ps | grep celery | wc -l`
- **Database Connections**: `pg_stat_activity` query
- **Redis Memory**: `INFO memory` command
- **CPU/Memory**: `docker stats`

---

## Emergency Procedures

### Service Down

```bash
# 1. Check status
docker-compose ps

# 2. View logs
docker-compose logs <service> --tail=100

# 3. Restart
docker-compose restart <service>

# 4. If still down: full restart
docker-compose down
docker-compose up -d
```

### Data Loss Prevention

```bash
# Backup before risky operations
docker exec anvil_postgres pg_dump -U anvil anvil_db > backup.sql
docker exec anvil_redis redis-cli BGSAVE

# Never use: docker-compose down -v (deletes data!)
# Safe: docker-compose down (keeps volumes)
```

### Recovery

```bash
# Restore from backup
docker exec -i anvil_postgres psql -U anvil anvil_db < backup.sql

# Check integrity
psql -h localhost -U anvil -d anvil_db -c "SELECT COUNT(*) FROM your_tables;"
```

---

## Support & Documentation

- **Docker Logs**: `docker-compose logs -f <service>`
- **Container Inspection**: `docker inspect <container_name>`
- **Network Inspection**: `docker network inspect anvil-docker_anvil-network`
- **Volume Inspection**: `docker volume inspect <volume_name>`
- **Health Checks**: `docker inspect <container> | grep -A 5 Health`

**Related Documentation**:
- [docker/README.md](../../docker/README.md) - Complete Docker reference
- [PostgreSQL Manual](https://www.postgresql.org/docs/)
- [Redis Manual](https://redis.io/docs/)
- [Celery Documentation](https://docs.celeryproject.io/)

---

**Last Updated**: January 24, 2026  
**Infrastructure Status**: ✅ All 27 services operational and tested
