# Admin Module: System Metrics

> **Technical Specification**: `FRONTEND_ADMIN_SYSTEM_METRICS`
> **Base URL**: `/api/admin/metrics`

## 📖 Overview
The **System Metrics** module provides low-level infrastructure monitoring. While the "Dashboards" provide business value (Chat/Security), this view focuses on the "Machine" itself.

### Key Capabilities
1.  **Resource Usage**: CPU, Memory, and Disk usage of the backend containers.
2.  **API Latency**: Global p95/p99 latency tracking.
3.  **Database Health**: Connection pool status and query performance.

---

## 🔌 API Endpoints

### 1. System Status
**GET** `/api/admin/metrics/status`
Real-time health check.

**Response**:
```json
{
  "status": "healthy",
  "uptime_seconds": 125000,
  "version": "1.5.0",
  "database": "connected",
  "redis": "connected"
}
```

---

## 🎨 UI/UX Guidelines

- **Real-time Graphs**: Utilize time-series charts (e.g., Grafana style) for CPU/Memory.
- **Traffic Lights**: Simple Green/Red indicators for Database and Cache connectivity.
