# MCP Servers Deployment Guide

**Version:** 1.0.0  
**Status:** ✅ LIVE  
**Last Updated:** December 2, 2025

---

## 📊 **OVERVIEW**

Deployment guide for all MCP servers (1inch, DeFiLlama, The Graph, CoinGecko).

### **Manual Deployment**
```bash
# Start individual server
make mcp.oneinch.run     # Port 8001
make mcp.defillama.run   # Port 8002
make mcp.thegraph.run    # Port 8003
make mcp.coingecko.run   # Port 8004

# Start all servers
make mcp.all.run
```

### **Docker Deployment**
```bash
# Local environment
make mcp.docker.local.up
make mcp.docker.local.down

# Production environment
make mcp.docker.prod.up
make mcp.docker.prod.down
```

### **Configuration**
- Docker Compose: `config/{env}/docker-compose-mcp.yml`
- Environment: `.env.{APP_ENV}`
- Ports: 8001-8004

---

## 📚 **RELATED DOCUMENTATION**
- [MCP Use Cases](../current/UC-MCP.md)
- [Makefile](../../../Makefile)
