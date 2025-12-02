# FRONTEND_ADMIN_SYSTEM_HEALTH

## Admin System Health Module

**User Type:** Admin  
**Module:** System Health  
**Route:** `/admin/system`  
**Access Level:** Read (All) | Manage (Super Admin)

---

## 📋 Module Overview

### Title
**System Health** - Infrastructure Monitoring

### Description
Real-time monitoring dashboard for platform infrastructure including server health, database performance, API latency, external service status, and resource utilization.

### Key Capabilities
- Real-time system metrics
- Service health monitoring
- Database performance
- API latency tracking
- External integration status
- Alert configuration

---

## 🖼️ Views & Wireframes

### View 1: System Health Dashboard

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│  🖥️ System Health                                    [🔔 Alerts] [📊 History]       │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                      │
│  ┌─ Overall Status ────────────────────────────────────────────────────────────────┐│
│  │                                                                                  ││
│  │  🟢 ALL SYSTEMS OPERATIONAL                              Uptime: 99.97% (30d)  ││
│  │                                                                                  ││
│  └─────────────────────────────────────────────────────────────────────────────────┘│
│                                                                                      │
│  CORE SERVICES                                                                      │
│  ┌─────────────────────────────────────────────────────────────────────────────────┐│
│  │                                                                                  ││
│  │  ┌─────────────────────┐  ┌─────────────────────┐  ┌─────────────────────┐      ││
│  │  │ 🟢 API Gateway      │  │ 🟢 Auth Service     │  │ 🟢 AI Orchestrator  │      ││
│  │  │    Latency: 45ms    │  │    Latency: 23ms    │  │    Latency: 850ms   │      ││
│  │  │    RPS: 1,245       │  │    RPS: 342         │  │    RPS: 89          │      ││
│  │  │    Error: 0.02%     │  │    Error: 0.01%     │  │    Error: 0.15%     │      ││
│  │  └─────────────────────┘  └─────────────────────┘  └─────────────────────┘      ││
│  │                                                                                  ││
│  │  ┌─────────────────────┐  ┌─────────────────────┐  ┌─────────────────────┐      ││
│  │  │ 🟢 Blockchain Svc   │  │ 🟢 Notification Svc │  │ 🟡 Analytics Svc    │      ││
│  │  │    Latency: 120ms   │  │    Latency: 35ms    │  │    Latency: 450ms   │      ││
│  │  │    RPS: 567         │  │    RPS: 123         │  │    RPS: 78          │      ││
│  │  │    Error: 0.05%     │  │    Error: 0.00%     │  │    Error: 0.25%     │      ││
│  │  └─────────────────────┘  └─────────────────────┘  └─────────────────────┘      ││
│  │                                                                                  ││
│  └─────────────────────────────────────────────────────────────────────────────────┘│
│                                                                                      │
│  DATABASE                                         INFRASTRUCTURE                    │
│  ┌────────────────────────────────────┐          ┌────────────────────────────────┐ │
│  │                                    │          │                                │ │
│  │  PostgreSQL Primary                │          │  CPU Usage                     │ │
│  │  🟢 Healthy │ Connections: 45/100  │          │  [████████░░░░░░░░░░] 42%     │ │
│  │  Query Latency: 12ms (avg)         │          │                                │ │
│  │                                    │          │  Memory Usage                  │ │
│  │  PostgreSQL Replica                │          │  [██████████████░░░░] 68%     │ │
│  │  🟢 Synced │ Lag: 0.2s             │          │                                │ │
│  │                                    │          │  Disk Usage                    │ │
│  │  Redis Cache                       │          │  [████████████░░░░░░] 58%     │ │
│  │  🟢 Healthy │ Memory: 2.1GB/8GB    │          │                                │ │
│  │  Hit Rate: 94.2%                   │          │  Network I/O                   │ │
│  │                                    │          │  In: 125 MB/s │ Out: 89 MB/s  │ │
│  │  TimescaleDB                       │          │                                │ │
│  │  🟢 Healthy │ Chunks: 1,245        │          │                                │ │
│  │                                    │          │                                │ │
│  └────────────────────────────────────┘          └────────────────────────────────┘ │
│                                                                                      │
│  EXTERNAL INTEGRATIONS                                                              │
│  ┌─────────────────────────────────────────────────────────────────────────────────┐│
│  │                                                                                  ││
│  │  🟢 Privy (Auth)        │ 🟢 Chainalysis       │ 🟢 1inch API                   ││
│  │     Latency: 89ms       │    Latency: 124ms    │    Latency: 156ms              ││
│  │                                                                                  ││
│  │  🟢 Vertex AI           │ 🟢 DeepInfra         │ 🟡 AWS Bedrock                 ││
│  │     Latency: 650ms      │    Latency: 720ms    │    Latency: 1,200ms            ││
│  │                                                                                  ││
│  │  🟢 Coingecko           │ 🟢 Alchemy           │ 🟢 Infura                      ││
│  │     Latency: 45ms       │    Latency: 35ms     │    Latency: 42ms               ││
│  │                                                                                  ││
│  └─────────────────────────────────────────────────────────────────────────────────┘│
│                                                                                      │
│  RECENT INCIDENTS                                                                   │
│  ┌─────────────────────────────────────────────────────────────────────────────────┐│
│  │                                                                                  ││
│  │  🟡 Nov 30, 14:23 - Analytics Service degraded (25 min) - Resolved             ││
│  │  🟢 Nov 28, 09:15 - Scheduled maintenance completed                             ││
│  │  🔴 Nov 25, 03:42 - Database failover triggered (8 min) - Resolved             ││
│  │                                                                                  ││
│  │  [View All Incidents →]                                                         ││
│  │                                                                                  ││
│  └─────────────────────────────────────────────────────────────────────────────────┘│
│                                                                                      │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 🔌 API Endpoints

### Get System Health

```typescript
// GET /admin/system/health
interface GetSystemHealthResponse {
  success: true;
  data: {
    overall_status: 'operational' | 'degraded' | 'partial_outage' | 'major_outage';
    uptime_30d: number;
    services: ServiceHealth[];
    databases: DatabaseHealth[];
    infrastructure: {
      cpu_percent: number;
      memory_percent: number;
      disk_percent: number;
      network_in_mbps: number;
      network_out_mbps: number;
    };
    external_integrations: IntegrationHealth[];
    recent_incidents: Incident[];
  };
}

interface ServiceHealth {
  name: string;
  status: 'healthy' | 'degraded' | 'down';
  latency_ms: number;
  requests_per_second: number;
  error_rate: number;
  last_check: string;
}

interface DatabaseHealth {
  name: string;
  type: 'postgresql' | 'redis' | 'timescaledb';
  status: 'healthy' | 'degraded' | 'down';
  connections_used: number;
  connections_max: number;
  latency_ms?: number;
  replica_lag_seconds?: number;
  cache_hit_rate?: number;
  memory_used_gb?: number;
  memory_max_gb?: number;
}

interface IntegrationHealth {
  name: string;
  status: 'healthy' | 'degraded' | 'down';
  latency_ms: number;
  last_check: string;
}

interface Incident {
  id: string;
  severity: 'critical' | 'major' | 'minor' | 'maintenance';
  title: string;
  started_at: string;
  resolved_at?: string;
  duration_minutes?: number;
  status: 'investigating' | 'identified' | 'monitoring' | 'resolved';
}
```

---

*Document Version: 1.0*  
*Last Updated: December 1, 2025*  
*Module: System Health*
