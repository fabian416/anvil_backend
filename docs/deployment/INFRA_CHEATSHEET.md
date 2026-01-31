# Infrastructure Quick Reference - Cheat Sheet

## 🚀 Start Everything

```bash
docker-compose -f docker-compose.yaml up -d
```

## ✅ Verify All Systems

```bash
# All services running?
docker-compose ps | grep Up | wc -l  # Should show 28 (including Caddy)

# Health check (local)
curl http://localhost:8080/health

# Health check (production via Caddy)
curl https://anvil.zk-access.xyz/health

# Database working?
psql -h localhost -U postgres -d anvil_db -c "SELECT 1"

# Redis working?
redis-cli -h localhost ping
```

## 📊 Status Dashboard

| Command | Purpose |
|---------|---------|
| `docker-compose ps` | All services status |
| `curl http://localhost:5555` | Flower monitoring dashboard (local) |
| `curl https://anvil.zk-access.xyz/flower/` | Flower via Caddy (production) |
| `docker stats` | Resource usage |
| `docker-compose logs -f fastapi` | API logs |
| `docker-compose logs -f caddy` | Caddy reverse proxy logs |

## 📍 Access Services

### Local (Development)

| Service | URL |
|---------|-----|
| API | http://localhost:8080 |
| Docs | http://localhost:8080/docs |
| Flower | http://localhost:5555 |
| PostgreSQL | localhost:5432 |
| Redis | localhost:6379 |
| MCP Aave | http://localhost:8085/health |

### Production (via Caddy)

| Service | URL |
|---------|-----|
| API | https://anvil.zk-access.xyz |
| Docs | https://anvil.zk-access.xyz/docs |
| Health | https://anvil.zk-access.xyz/health |
| Guest Chat | https://anvil.zk-access.xyz/api/v1/guest/chat |
| Flower | https://anvil.zk-access.xyz/flower/ |
| MCP Aave | https://anvil.zk-access.xyz/mcp/aave/health |
| MCP DeFiLlama | https://anvil.zk-access.xyz/mcp/defillama/health |
| MCP CoinGecko | https://anvil.zk-access.xyz/mcp/coingecko/health |
| All MCPs | https://anvil.zk-access.xyz/mcp/{service}/health |

## 🔧 Common Troubleshooting

### Service won't start?
```bash
docker-compose logs <service_name> | tail -50
docker-compose restart <service_name>
```

### Database not responding?
```bash
docker exec anvil_postgres pg_isready -U anvil
docker-compose ps postgres
```

### Celery tasks not working?
```bash
# Check Flower: http://localhost:5555
# Check worker logs:
docker-compose logs -f celery-worker-agents

# Check Redis:
redis-cli -h localhost ping
```

### Performance issues?
```bash
# Check resource usage
docker stats --no-stream

# Check memory per service
docker stats --format "table {{.Container}}\t{{.MemUsage}}"

# Scale down a worker
docker-compose up -d --scale celery-worker-agents=1
```

## 🛠️ Maintenance Commands

### Scale Up (More Load)
```bash
docker-compose up -d --scale celery-worker-agents=3
docker-compose up -d --scale celery-worker-transactions=2
```

### Database Backup
```bash
docker exec anvil_postgres pg_dump -U anvil anvil_db > backup.sql
```

### Full Restart (Keep Data)
```bash
docker-compose down
docker-compose up -d
```

### Clean Restart (Lose Data!)
```bash
docker-compose down -v
docker-compose build
docker-compose up -d
```

## 📋 Service List (27 Total)

**Core** (3): FastAPI, PostgreSQL, Redis  
**Workers** (11): Celery Beat, 1 general, 9 specialized  
**MCPs** (11): 1inch, Defillama, Graph, CoinGecko, Aave, Portfolio, Perplexity, Morpho, Curve, Hyperliquid, LayerZero  
**Monitoring** (1): Flower  
**Utilities** (1): TX Confirmation  

## 🆘 Emergency Procedures

### Everything down?
```bash
# 1. Check if docker daemon running
docker ps

# 2. Full restart
docker-compose down
docker-compose up -d

# 3. Check logs
docker-compose logs
```

### Data Loss?
```bash
# Restore from backup (if exists)
docker exec -i anvil_postgres psql -U anvil anvil_db < backup.sql
```

### Need Help?
📖 Read: `docs/deployment/INFRASTRUCTURE.md`  
📄 Reference: `docker/README.md`

---

**Quick Links**:
- [Full Infrastructure Guide](../docs/deployment/INFRASTRUCTURE.md)
- [Docker Reference](../docker/README.md)
- [Deployment Guide](../docs/deployment/README.md)

**Status**: 27/27 services operational ✅
