# UC-DASHBOARD: Dashboard & Analytics

**Version:** 1.0.0  
**Status:** ✅ LIVE (Production)  
**Category:** Core Platform  
**Total Use Cases:** 4

---

## 📊 **OVERVIEW**

Basic dashboard and analytics providing market overview, protocol metrics, and user analytics.

### **Business Value**
- Market data visualization
- Protocol metrics tracking
- User analytics for admins
- Real-time updates

### **Technical Stack**
- **Backend:** FastAPI
- **Data Sources:** MCP servers (DeFiLlama, CoinGecko)
- **Real-time:** WebSocket support
- **Caching:** Redis

---

## 🎯 **USE CASES**

### **UC-DASH-1: Basic Dashboard**
- **Status:** ✅ LIVE
- **Endpoint:** `GET /api/v1/dashboard`
- **Interactor:** `GetDashboardData`
- **Capabilities:** Aggregate market data, protocol metrics

### **UC-DASH-2: Market Overview**
- **Status:** ✅ LIVE
- **Data Sources:** CoinGecko, DeFiLlama
- **Capabilities:** Top tokens, market cap, trending

### **UC-DASH-3: Protocol Metrics**
- **Status:** ✅ LIVE
- **Data Source:** DeFiLlama MCP
- **Capabilities:** TVL, volume, protocol stats

### **UC-DASH-4: User Metrics**
- **Status:** ✅ LIVE (Admin only)
- **Repository:** `UserMetricsRepository`
- **Capabilities:** User activity, API usage, subscription stats

---

## 🏗️ **ARCHITECTURE**

```
Application Layer:
  └─ queries/
     └─ get_dashboard_data.py

Infrastructure Layer:
  └─ adapters/
     └─ dashboard_aggregation_service.py

Presentation Layer:
  └─ controllers/dashboard/
     └─ router.py
```

---

## 📚 **RELATED DOCUMENTATION**

- [Dashboard Service](../../../src/app/application/queries/)
- [MCP Integration](../../../src/app/infrastructure/mcp/)

---

**Status:** ✅ 100% Complete (4/4 use cases live)  
**Last Updated:** December 2, 2025
