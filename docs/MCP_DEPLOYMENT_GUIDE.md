# MCP Servers Deployment Guide

Complete guide for deploying and managing the 4 MCP (Model Context Protocol) servers.

---

## 📊 **MCP Servers Overview**

| Server | Port | Tools | Purpose |
|--------|------|-------|---------|
| **1inch** | 8081 | 4 | DEX aggregation, swaps, liquidity |
| **DeFiLlama** | 8082 | 5 | Protocol analytics, TVL data |
| **The Graph** | 8083 | 4 | Blockchain queries, subgraphs |
| **CoinGecko** | 8084 | 6 | Market data, prices, trending |

**Total: 4 servers, 19 tools**

---

## 🚀 **Quick Start**

### **Local Development (Individual Servers)**

Run each server in a separate terminal:

```bash
# Terminal 1: 1inch DEX Aggregator
make mcp.oneinch

# Terminal 2: DeFiLlama Protocol Analytics
make mcp.defillama

# Terminal 3: The Graph Blockchain Data
make mcp.thegraph

# Terminal 4: CoinGecko Market Data
make mcp.coingecko
```

### **Local Development (Docker Compose)**

Start all MCP servers at once:

```bash
# Start all MCP servers
make up.mcp.local

# View logs
make logs.mcp

# Stop all servers
make down.mcp
```

### **Production Deployment**

```bash
# Set environment
export APP_ENV=prod

# Configure API keys in config/prod/.env.prod
# ONEINCH_API_KEY=your_key
# THEGRAPH_API_KEY=your_key
# COINGECKO_API_KEY=your_key

# Start all MCP servers
make up.mcp.prod

# Monitor logs
make logs.mcp

# Check health
curl http://localhost:8081/health
curl http://localhost:8082/health
curl http://localhost:8083/health
curl http://localhost:8084/health
```

---

## 📋 **Makefile Commands**

### **Individual Server Commands**

```bash
make mcp.oneinch      # Start 1inch server (port 8081)
make mcp.defillama    # Start DeFiLlama server (port 8082)
make mcp.thegraph     # Start The Graph server (port 8083)
make mcp.coingecko    # Start CoinGecko server (port 8084)
make mcp.stop         # Stop all MCP servers
```

### **Docker Compose Commands**

```bash
make up.mcp           # Start all servers (local)
make up.mcp.local     # Start all servers (local, explicit)
make up.mcp.prod      # Start all servers (production)
make down.mcp         # Stop all MCP servers
make logs.mcp         # View logs from all servers
```

### **Help Command**

```bash
make mcp.all          # Shows usage instructions
```

---

## 🔧 **Configuration**

### **Environment Variables**

#### **Optional API Keys:**

```bash
# config/local/.env.local or config/prod/.env.prod

# 1inch API Key (optional, for higher rate limits)
ONEINCH_API_KEY=your_1inch_api_key

# The Graph API Key (optional, for hosted service)
THEGRAPH_API_KEY=your_thegraph_api_key

# CoinGecko API Key (optional, for pro features)
COINGECKO_API_KEY=your_coingecko_api_key
```

**Note:** All servers work without API keys but may have rate limits.

### **Docker Compose Files**

- **Local:** `config/local/docker-compose-mcp.yml`
- **Production:** `config/prod/docker-compose-mcp.yml`

---

## 🔍 **Testing MCP Servers**

### **Health Checks**

```bash
# Check all servers
curl http://localhost:8081/health  # 1inch
curl http://localhost:8082/health  # DeFiLlama
curl http://localhost:8083/health  # The Graph
curl http://localhost:8084/health  # CoinGecko
```

**Expected Response:**
```json
{
  "status": "healthy",
  "server": "oneinch",
  "tools_registered": 4
}
```

### **Tool Discovery**

```bash
# List available tools
curl http://localhost:8081/tools  # 1inch tools
curl http://localhost:8082/tools  # DeFiLlama tools
curl http://localhost:8083/tools  # The Graph tools
curl http://localhost:8084/tools  # CoinGecko tools
```

**Expected Response:**
```json
{
  "server": "oneinch",
  "description": "1inch DEX aggregator...",
  "tools": [
    {
      "name": "get_swap_quote",
      "description": "Get swap quote...",
      "parameters": {...}
    }
  ]
}
```

### **Execute Tools**

```bash
# 1inch: Get swap quote
curl -X POST http://localhost:8081/execute/get_swap_quote \
  -H "Content-Type: application/json" \
  -d '{
    "params": {
      "chain_id": 1,
      "from_token": "0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE",
      "to_token": "0x6B175474E89094C44Da98b954EedeAC495271d0F",
      "amount": "1000000000000000000"
    }
  }'

# DeFiLlama: Get chains
curl -X POST http://localhost:8082/execute/get_chains \
  -H "Content-Type: application/json" \
  -d '{"params": {}}'

# CoinGecko: Get trending tokens
curl -X POST http://localhost:8084/execute/get_trending_tokens \
  -H "Content-Type: application/json" \
  -d '{"params": {}}'
```

---

## 📊 **Monitoring**

### **Docker Compose Logs**

```bash
# All servers
make logs.mcp

# Specific server
docker logs -f anvil_mcp_oneinch
docker logs -f anvil_mcp_defillama
docker logs -f anvil_mcp_thegraph
docker logs -f anvil_mcp_coingecko
```

### **Container Status**

```bash
docker ps | grep mcp

# Expected output:
# anvil_mcp_oneinch      Up 5 minutes      0.0.0.0:8081->8081/tcp
# anvil_mcp_defillama    Up 5 minutes      0.0.0.0:8082->8082/tcp
# anvil_mcp_thegraph     Up 5 minutes      0.0.0.0:8083->8083/tcp
# anvil_mcp_coingecko    Up 5 minutes      0.0.0.0:8084->8084/tcp
```

### **Health Check Monitoring**

```bash
# Production health checks (automatic)
# Runs every 30s via Docker healthcheck

# Manual check
docker inspect anvil_mcp_oneinch_prod | grep Health -A 10
```

---

## 🔐 **Security**

### **API Key Management**

1. **Never commit API keys to git**
2. **Use environment variables**
3. **Rotate keys regularly**
4. **Use separate keys for dev/prod**

### **Network Security**

```bash
# Production: Use reverse proxy (Nginx, Traefik)
# Restrict access to internal network only
# Enable HTTPS/TLS

# Example Nginx config:
# location /mcp/oneinch/ {
#     proxy_pass http://localhost:8081/;
# }
```

### **Rate Limiting**

```bash
# Implement at reverse proxy level
# Or use API keys for higher limits
```

---

## 🐛 **Troubleshooting**

### **Server Won't Start**

```bash
# Check port availability
netstat -tuln | grep 808[1-4]

# Kill process on port (if needed)
lsof -ti:8081 | xargs kill -9

# Check logs
make logs.mcp
```

### **Import Errors**

```bash
# Ensure PYTHONPATH is set
export PYTHONPATH=src

# Check dependencies
pip list | grep -E "fastapi|pydantic|httpx"
```

### **Connection Refused**

```bash
# Verify server is running
curl http://localhost:8081/health

# Check Docker network
docker network inspect anvil_network

# Restart servers
make down.mcp && make up.mcp
```

### **API Rate Limits**

```bash
# Add API keys to .env file
# Restart servers to apply changes
make down.mcp && make up.mcp
```

---

## 📈 **Performance**

### **Expected Response Times**

| Endpoint | Typical | Target |
|----------|---------|--------|
| Health check | <10ms | <50ms |
| Tool discovery | <100ms | <200ms |
| Tool execution | 100ms-2s | <5s |

### **Optimization**

1. **Enable caching** for frequently accessed data
2. **Use API keys** for higher rate limits
3. **Scale horizontally** with load balancer
4. **Monitor metrics** with Prometheus/Grafana

---

## 🔄 **Updates & Maintenance**

### **Updating MCP Servers**

```bash
# Pull latest code
git pull

# Rebuild Docker images
make down.mcp
make up.mcp

# Verify health
curl http://localhost:8081/health
```

### **Backup & Recovery**

```bash
# No persistent data (stateless servers)
# Configuration only:
# - config/local/.env.local
# - config/prod/.env.prod
# - docker-compose-mcp.yml
```

---

## 📚 **API Documentation**

### **Detailed Tool Documentation**

- **1inch Tools:** See `src/app/infrastructure/mcp/servers/oneinch_mcp.py`
- **DeFiLlama Tools:** See `src/app/infrastructure/mcp/servers/defillama_mcp.py`
- **The Graph Tools:** See `src/app/infrastructure/mcp/servers/thegraph_mcp.py`
- **CoinGecko Tools:** See `src/app/infrastructure/mcp/servers/coingecko_mcp.py`

### **OpenAPI/Swagger**

Each server exposes OpenAPI docs:

```bash
http://localhost:8081/docs  # 1inch
http://localhost:8082/docs  # DeFiLlama
http://localhost:8083/docs  # The Graph
http://localhost:8084/docs  # CoinGecko
```

---

## 🎯 **Production Checklist**

- [ ] Configure API keys in `.env.prod`
- [ ] Test all servers locally first
- [ ] Set up reverse proxy (Nginx/Traefik)
- [ ] Enable HTTPS/TLS certificates
- [ ] Configure rate limiting
- [ ] Set up monitoring (health checks)
- [ ] Configure log aggregation
- [ ] Test failover scenarios
- [ ] Document API endpoints
- [ ] Train team on operations

---

## 📞 **Support**

**Issues:** Open a GitHub issue  
**Documentation:** See `docs/` directory  
**Server Code:** `src/app/infrastructure/mcp/servers/`  
**Tests:** `tests/integration/mcp/`

---

**Last Updated:** December 2, 2025  
**Version:** 1.0.0  
**Status:** Production Ready ✅
