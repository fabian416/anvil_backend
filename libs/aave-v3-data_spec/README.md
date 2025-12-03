# Aave V3 Data API - Integration Specification

**Library:** aave-v3-data  
**Type:** Real-Time DeFi Lending Protocol Data  
**Priority:** 🟡 **MEDIUM** (Data Intelligence, Risk Analysis)  
**Integration Complexity:** 🟢 Low (REST API, JSON data)

## **OVERVIEW**
Public, real-time Aave V3 lending rates, reserve parameters, and liquidity data across 13+ blockchains. No API key required.

## **BUSINESS VALUE**
- **Risk Analysis**: Real-time health factor monitoring
- **Yield Optimization**: Best lending rates across chains
- **Protocol Intelligence**: Governance changes tracking
- **User Tools**: Lending/borrowing calculator

## **INTEGRATION POINTS**
1. **Research Agent**: "What are current USDC lending rates on Aave?"
2. **Risk Dashboard**: Display health factors and liquidation warnings
3. **Yield Comparison**: Compare Aave rates with Compound, etc.

## **IMPLEMENTATION** (2 weeks - 40 hours)

### **Phase 1: Data Fetcher Service**
```
src/app/infrastructure/aave/
├── client.py          # HTTP client for aave-v3-data API
├── services/
│   ├── rates.py       # Lending/borrowing rates
│   └── reserves.py    # Reserve parameters
└── models/
    ├── reserve.py
    └── rate.py
```

### **Phase 2: API Endpoints**
- `GET /api/v1/aave/rates/{chain}/{asset}` - Current rates
- `GET /api/v1/aave/reserves/{chain}` - All reserves
- `GET /api/v1/aave/compare` - Compare rates across chains

### **Phase 3: MCP Server**
```python
# src/app/infrastructure/mcp/servers/aave_mcp.py
Tools:
- get_lending_rate
- get_borrowing_rate
- calculate_health_factor
- find_best_rate
```

## **CONFIGURATION**
```python
@dataclass
class AaveConfig:
    enabled: bool = False
    api_url: str = "https://th3nolo.github.io/aave-v3-data/aave_v3_data.json"
    cache_ttl: int = 3600  # 1 hour (data updates daily)
```

**Environment:**
```bash
AAVE_DATA_ENABLED=false
AAVE_CACHE_TTL=3600
```

## **COST**
- Development: 40 hours × $150 = $6,000
- Infrastructure: $0/month (free public API + caching)
- **ROI**: Improved user decision-making, reduced liquidations

**Status:** 📋 Ready  
**Timeline:** 2 weeks
