# FRONTEND_ADMIN_DATA_SOURCES

## Admin Data Source Configuration Module

**User Type:** Admin  
**Module:** External Data Source Management  
**Route:** `/admin/data-sources`  
**Platform:** Web (Admin Panel)  
**Version:** 1.0

---

## 📋 Module Overview

### Title
**Data Sources** - External API & Data Provider Management

### Description
Configuration and monitoring of external data sources including DeFi APIs (DefiLlama, The Graph, 1inch), blockchain RPCs, oracle providers, and data sync status.

### Key Capabilities
- Data source configuration
- API health monitoring
- Sync status tracking
- Rate limit management
- Error logging & alerts
- Data freshness metrics
- Provider failover setup
- Cost tracking

---

## 🖼️ Wireframes

### View 1: Data Sources Dashboard

```
┌─────────────────────────────────────────────────────────────┐
│  [←] Admin Home       Data Sources             [+ Add New]  │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Active Data Sources (8)                       🟢 All Healthy│
│                                                             │
│  ┌─────────────────────────────────────────────────────────┐│
│  │  🟢 DefiLlama API                           Active      ││
│  │                                                         ││
│  │  Status: ✅ Healthy  |  Uptime: 99.8%                   ││
│  │  Last Sync: 2 min ago  |  Next: in 28 min               ││
│  │  Requests Today: 1,234  |  Rate Limit: 2,000/day        ││
│  │  Cost: $0 (Free tier)                                   ││
│  │                                                         ││
│  │  Data Provided:                                         ││
│  │  • Protocol TVL (450 protocols)                         ││
│  │  • Chain statistics (15 chains)                         ││
│  │  • Historical data (365 days)                           ││
│  │                                                         ││
│  │  [Configure] [View Logs] [Test Connection]              ││
│  └─────────────────────────────────────────────────────────┘│
│                                                             │
│  ┌─────────────────────────────────────────────────────────┐│
│  │  🟢 The Graph Protocol Subgraphs            Active      ││
│  │                                                         ││
│  │  Status: ✅ Healthy  |  Uptime: 99.9%                   ││
│  │  Last Sync: 5 min ago  |  Next: in 25 min               ││
│  │  Queries Today: 3,456  |  Rate Limit: 10,000/day        ││
│  │  Cost: $25/month                                        ││
│  │                                                         ││
│  │  Subgraphs Tracked:                                     ││
│  │  • Aave V3 (Ethereum, Arbitrum, Polygon)                ││
│  │  • Uniswap V3 (Multi-chain)                             ││
│  │  • Curve Finance                                        ││
│  │  ... 25 more                                            ││
│  │                                                         ││
│  │  [Configure] [View Logs] [Add Subgraph]                 ││
│  └─────────────────────────────────────────────────────────┘│
│                                                             │
│  ┌─────────────────────────────────────────────────────────┐│
│  │  🟡 1inch DEX Aggregator                    Warning     ││
│  │                                                         ││
│  │  Status: ⚠️ Rate Limited  |  Uptime: 98.2%              ││
│  │  Last Sync: 15 min ago  |  Next: in 45 min              ││
│  │  Requests Today: 950  |  Rate Limit: 1,000/day (90%)    ││
│  │  Cost: $0 (Free tier)                                   ││
│  │                                                         ││
│  │  ⚠️ Approaching rate limit. Consider upgrading.         ││
│  │                                                         ││
│  │  [Upgrade Plan] [Configure] [View Logs]                 ││
│  └─────────────────────────────────────────────────────────┘│
│                                                             │
│  [View All 8 Sources] [Add New Source] [Bulk Configure]     │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### View 2: Data Source Configuration

```
┌─────────────────────────────────────────────────────────────┐
│  [←] Data Sources    Configure: DefiLlama API               │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Basic Configuration                                        │
│  ┌─────────────────────────────────────────────────────────┐│
│  │  Source Name:      DefiLlama API                        ││
│  │  API Endpoint:     https://api.llama.fi                 ││
│  │  API Key:          ••••••••••••••••  [Show] [Rotate]    ││
│  │  Enabled:          ☑ Active                             ││
│  └─────────────────────────────────────────────────────────┘│
│                                                             │
│  Sync Configuration                                         │
│  ┌─────────────────────────────────────────────────────────┐│
│  │  Sync Interval:    [30 minutes ▼]                       ││
│  │  Sync Schedule:    ○ Interval  ● Cron                   ││
│  │  Cron Expression:  */30 * * * *                         ││
│  │  Timeout:          [30 seconds ▼]                       ││
│  │  Retry Attempts:   [3 ▼]                                ││
│  │  Retry Delay:      [5 seconds ▼]                        ││
│  └─────────────────────────────────────────────────────────┘│
│                                                             │
│  Rate Limiting                                              │
│  ┌─────────────────────────────────────────────────────────┐│
│  │  Daily Limit:      [2000 ▼] requests                    ││
│  │  Current Usage:    1,234 (62%)                          ││
│  │  Reset Time:       in 4 hours                           ││
│  │  Alert Threshold:  [90% ▼]                              ││
│  └─────────────────────────────────────────────────────────┘│
│                                                             │
│  Failover Configuration                                     │
│  ┌─────────────────────────────────────────────────────────┐│
│  │  Failover Enabled: ☑                                    ││
│  │  Backup Source:    [CoinGecko API ▼]                    ││
│  │  Failover After:   [3 ▼] consecutive failures           ││
│  │  Auto-Recovery:    ☑ Enabled                            ││
│  └─────────────────────────────────────────────────────────┘│
│                                                             │
│  Data Coverage                                              │
│  ┌─────────────────────────────────────────────────────────┐│
│  │  Protocols:        ☑ Enabled (450 protocols)            ││
│  │  TVL Data:         ☑ Enabled                            ││
│  │  Price Data:       ☑ Enabled                            ││
│  │  Historical:       ☑ Enabled (365 days)                 ││
│  │  Chain Stats:      ☑ Enabled (15 chains)                ││
│  └─────────────────────────────────────────────────────────┘│
│                                                             │
│  ┌─────────────────────────────────────────────────────────┐│
│  │  [Test Connection] [Save Changes] [Reset to Defaults]   ││
│  └─────────────────────────────────────────────────────────┘│
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### View 3: Sync Status & Logs

```
┌─────────────────────────────────────────────────────────────┐
│  [←] Data Sources    Sync Status & Logs                     │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Recent Sync Operations                                     │
│  ┌─────────────────────────────────────────────────────────┐│
│  │  ✅ DefiLlama - TVL Update          2 min ago           ││
│  │     Duration: 2.3s  |  Protocols: 450  |  Success      ││
│  │     [View Details]                                      ││
│  ├─────────────────────────────────────────────────────────┤│
│  │  ✅ The Graph - Aave V3             5 min ago           ││
│  │     Duration: 1.8s  |  Events: 234  |  Success         ││
│  │     [View Details]                                      ││
│  ├─────────────────────────────────────────────────────────┤│
│  │  ⚠️ 1inch API - Price Data          8 min ago           ││
│  │     Duration: 5.2s  |  Tokens: 1,250  |  Rate Limited  ││
│  │     [View Details] [Retry Now]                          ││
│  ├─────────────────────────────────────────────────────────┤│
│  │  ✅ Chainlink - Price Feeds         10 min ago          ││
│  │     Duration: 1.5s  |  Feeds: 85  |  Success           ││
│  │     [View Details]                                      ││
│  └─────────────────────────────────────────────────────────┘│
│                                                             │
│  Error Log (Last 24h)                                       │
│  ┌─────────────────────────────────────────────────────────┐│
│  │  🔴 1inch API - Rate limit exceeded        2 hours ago  ││
│  │     Error: 429 Too Many Requests                        ││
│  │     Action: Switched to backup (CoinGecko)              ││
│  │     [View Full Log]                                     ││
│  ├─────────────────────────────────────────────────────────┤│
│  │  🟡 The Graph - Timeout                    5 hours ago  ││
│  │     Error: Request timeout after 30s                    ││
│  │     Action: Retried successfully                        ││
│  │     [View Full Log]                                     ││
│  └─────────────────────────────────────────────────────────┘│
│                                                             │
│  Data Freshness                                             │
│  • Protocol TVL: Fresh (2 min old) ✅                        │
│  • Price feeds: Fresh (1 min old) ✅                         │
│  • Historical data: Stale (2 hours old) ⚠️                   │
│  • Chain stats: Fresh (5 min old) ✅                         │
│                                                             │
│  [Refresh All] [View Schedule]                              │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 🔌 Admin API Endpoints

### List Data Sources

```typescript
// GET /api/v1/admin/data-sources
interface DataSourcesResponse {
  sources: Array<{
    id: string;
    name: string;
    type: 'api' | 'rpc' | 'subgraph' | 'oracle';
    status: 'active' | 'inactive' | 'error' | 'rate_limited';
    health_score: number; // 0-100
    uptime_percentage: number;
    last_sync: string;
    next_sync: string;
    requests_today: number;
    rate_limit: number;
    cost_monthly: number;
  }>;
  total_sources: number;
  healthy_sources: number;
}
```

### Configure Data Source

```typescript
// PUT /api/v1/admin/data-sources/:id
interface ConfigureDataSourceRequest {
  api_key?: string;
  sync_interval_minutes?: number;
  enabled?: boolean;
  rate_limit?: number;
  failover_source_id?: string;
}

interface ConfigureDataSourceResponse {
  success: boolean;
  source: DataSource;
}
```

### Trigger Manual Sync

```typescript
// POST /api/v1/admin/data-sources/:id/sync
interface ManualSyncResponse {
  job_id: string;
  status: 'queued' | 'running';
  estimated_duration_seconds: number;
}
```

### Get Sync Logs

```typescript
// GET /api/v1/admin/data-sources/:id/logs?limit=50
interface SyncLogsResponse {
  logs: Array<{
    id: string;
    source_id: string;
    started_at: string;
    completed_at?: string;
    status: 'success' | 'failed' | 'running';
    duration_seconds?: number;
    records_synced?: number;
    error?: string;
  }>;
  total_logs: number;
}
```

---

## 🎨 Component Specifications

```typescript
interface DataSourcesDashboardProps {
  refreshInterval?: number;
}

interface DataSourceCardProps {
  source: DataSource;
  onConfigure: () => void;
  onTest: () => void;
  onViewLogs: () => void;
}

interface SyncStatusIndicatorProps {
  lastSync: Date;
  nextSync: Date;
  isRunning: boolean;
}

interface RateLimitGaugeProps {
  current: number;
  limit: number;
  resetTime: Date;
}
```

---

*Document Version: 1.0*  
*Last Updated: December 1, 2025*  
*Module: Admin Data Sources*
