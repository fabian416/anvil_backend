# MCP Servers - Quick Reference Card

Quick commands for deploying and managing MCP servers.

---

## 🚀 **Quick Start**

```bash
# Local Development (Docker Compose)
make up.mcp.local

# Production Deployment
export APP_ENV=prod
make up.mcp.prod

# Stop All Servers
make down.mcp
```

---

## 📋 **All Makefile Commands**

### **Individual Servers**
```bash
make mcp.oneinch      # Port 8081
make mcp.defillama    # Port 8082
make mcp.thegraph     # Port 8083
make mcp.coingecko    # Port 8084
make mcp.stop         # Stop all
```

### **Docker Compose**
```bash
make up.mcp           # Start all (local)
make up.mcp.local     # Start all (local)
make up.mcp.prod      # Start all (prod)
make down.mcp         # Stop all
make logs.mcp         # View logs
```

---

## 🔍 **Health Checks**

```bash
curl http://localhost:8081/health  # 1inch
curl http://localhost:8082/health  # DeFiLlama
curl http://localhost:8083/health  # The Graph
curl http://localhost:8084/health  # CoinGecko
```

**Expected:** `{"status": "healthy", "server": "...", "tools_registered": N}`

---

## 🛠️ **Tool Discovery**

```bash
curl http://localhost:8081/tools  # List 1inch tools
curl http://localhost:8082/tools  # List DeFiLlama tools
curl http://localhost:8083/tools  # List The Graph tools
curl http://localhost:8084/tools  # List CoinGecko tools
```

---

## ⚙️ **Configuration**

### **API Keys (Optional)**

Add to `config/local/.env.local` or `config/prod/.env.prod`:

```bash
ONEINCH_API_KEY=your_key_here
THEGRAPH_API_KEY=your_key_here
COINGECKO_API_KEY=your_key_here
```

---

## 📊 **Monitoring**

```bash
# View logs
make logs.mcp

# Check containers
docker ps | grep mcp

# Follow specific server
docker logs -f anvil_mcp_oneinch
```

---

## 🐛 **Troubleshooting**

```bash
# Restart all servers
make down.mcp && make up.mcp

# Check port availability
netstat -tuln | grep 808[1-4]

# Kill process on port
lsof -ti:8081 | xargs kill -9
```

---

## 📚 **Server Details**

| Server | Port | Tools | Purpose |
|--------|------|-------|---------|
| 1inch | 8081 | 4 | DEX aggregation |
| DeFiLlama | 8082 | 5 | Protocol analytics |
| The Graph | 8083 | 4 | Blockchain queries |
| CoinGecko | 8084 | 6 | Market data |

**Total:** 4 servers, 19 tools

---

## 🔗 **API Endpoints**

All servers expose:
- `/` - Server info
- `/health` - Health check
- `/tools` - Tool discovery
- `/execute/{tool_name}` - Execute tool
- `/docs` - OpenAPI/Swagger docs

---

## 📖 **Full Documentation**

See `docs/MCP_DEPLOYMENT_GUIDE.md` for complete documentation.

---

**Last Updated:** December 2, 2025
