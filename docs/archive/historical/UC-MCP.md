# UC-MCP: Data Providers (MCP Servers)

**Version:** 1.0.0  
**Status:** ✅ LIVE (Production)  
**Category:** Core Platform  
**Total Use Cases:** 6

---

## 📊 **OVERVIEW**

Model Context Protocol (MCP) servers providing external DeFi data access through standardized tool interfaces.

### **Business Value**
- Real-time DeFi data access
- DEX aggregation data (1inch)
- Protocol analytics (DeFiLlama)
- On-chain data (The Graph)
- Market data (CoinGecko)

### **Technical Stack**
- **Protocol:** MCP (Model Context Protocol)
- **Framework:** FastAPI
- **Deployment:** Docker Compose
- **Servers:** 4 operational MCP servers

---

## 🎯 **USE CASES**

### **UC-MCP-1: 1inch DEX Data**
- **Status:** ✅ LIVE
- **Server:** `OneInchMCPServer`
- **Port:** 8001
- **Tools:** 
  - `get_quote` - Get swap quotes
  - `get_swap` - Execute swap
  - `get_liquidity` - Check liquidity
  - `get_protocols` - List DEX protocols

### **UC-MCP-2: DeFiLlama Protocol Data**
- **Status:** ✅ LIVE
- **Server:** `DeFiLlamaMCPServer`
- **Port:** 8002
- **Tools:**
  - `get_protocol_tvl` - Get protocol TVL
  - `get_protocols` - List all protocols
  - `get_yields` - Get yield opportunities
  - `get_chains` - List supported chains

### **UC-MCP-3: The Graph Queries**
- **Status:** ✅ LIVE
- **Server:** `TheGraphMCPServer`
- **Port:** 8003
- **Tools:**
  - `query_subgraph` - Execute GraphQL queries
  - `get_protocol_data` - Get protocol on-chain data
  - `get_transactions` - Query transaction history

### **UC-MCP-4: CoinGecko Market Data**
- **Status:** ✅ LIVE
- **Server:** `CoinGeckoMCPServer`
- **Port:** 8004
- **Tools:**
  - `get_price` - Get current prices
  - `get_market_data` - Get market stats
  - `get_trending` - Get trending tokens
  - `get_historical` - Get price history

### **UC-MCP-5: MCP Tool Discovery**
- **Status:** ✅ LIVE
- **Endpoint:** `GET /mcp/tools`
- **Response:** List of available tools with schemas

### **UC-MCP-6: MCP Tool Execution**
- **Status:** ✅ LIVE
- **Endpoint:** `POST /mcp/execute`
- **Request:** `{tool_name, parameters}`
- **Response:** Tool execution result

---

## 🏗️ **ARCHITECTURE**

```
Infrastructure Layer:
  └─ mcp/
     ├─ base.py (MCPServer base class)
     ├─ oneinch_server.py
     ├─ defillama_server.py
     ├─ thegraph_server.py
     └─ coingecko_server.py

Deployment:
  ├─ config/local/docker-compose-mcp.yml
  ├─ config/prod/docker-compose-mcp.yml
  └─ Makefile (mcp.* targets)
```

---

## 📚 **RELATED DOCUMENTATION**

- [MCP Servers Implementation](../../PHASES_2_3_COMPLETE_SUMMARY.md)
- [MCP Deployment Guide](../implementation/DEPLOY-MCP.md)
- [Makefile MCP Commands](../../../Makefile)

---

**Status:** ✅ 100% Complete (6/6 use cases live)  
**Last Updated:** December 2, 2025
