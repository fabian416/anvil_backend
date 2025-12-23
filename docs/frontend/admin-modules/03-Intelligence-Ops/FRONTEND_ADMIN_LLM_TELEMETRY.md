# Module: LLM Telemetry

**Route**: `/admin/intelligence-ops/telemetry`  
**Auth Required**: Yes (Admin Only)  
**Package**: `admin/intelligence-ops/telemetry`

## 1. Overview
Enables administrators to monitor and analyze LLM orchestration metrics and analytics. Provides comprehensive insights into request volume, latency, costs, token usage, and performance by provider, model, and agent. Supports real-time updates via WebSocket.

## 2. API Contract

### Get Telemetry Overview
**Endpoint**: `GET /api/admin/llm/telemetry/overview`  
**Query Params**:
- `period` (string, optional): Time period - `1h`, `24h`, `7d`, `30d` (Default: `24h`).

#### Response Body (`TelemetryResponse`)
| Field | Type | Description |
|---|---|---|
| `success` | `boolean` | Whether request was successful |
| `data` | `TelemetryOverviewData` | Telemetry overview data |

**TelemetryOverviewData Object**:
| Field | Type | Description |
|---|---|---|
| `period` | `string` | Time period used |
| `total_requests` | `number` | Total requests in period |
| `success_rate` | `number` | Overall success rate (0-1) |
| `avg_latency_ms` | `number` | Average latency in milliseconds |
| `p95_latency_ms` | `number` | 95th percentile latency |
| `total_cost_usd` | `number` | Total cost in USD |
| `total_tokens` | `TokenCounts` | Total token counts |
| `requests_by_provider` | `ProviderMetrics[]` | Request metrics by provider |
| `requests_by_agent` | `AgentMetrics[]` | Request metrics by agent |
| `retry_rate` | `number` | Retry rate (0-1) |
| `circuit_breakers_open` | `number` | Number of open circuit breakers |

**TokenCounts Object**:
| Field | Type | Description |
|---|---|---|
| `input` | `number` | Total input tokens |
| `output` | `number` | Total output tokens |

**ProviderMetrics Object**:
| Field | Type | Description |
|---|---|---|
| `provider` | `string` | Provider name |
| `count` | `number` | Request count |
| `success_rate` | `number` | Success rate (0-1) |
| `avg_latency_ms` | `number` | Average latency |

**AgentMetrics Object**:
| Field | Type | Description |
|---|---|---|
| `agent` | `string` | Agent type |
| `count` | `number` | Request count |
| `avg_latency_ms` | `number` | Average latency |

**JSON Example**:
```json
{
  "success": true,
  "data": {
    "period": "24h",
    "total_requests": 45231,
    "success_rate": 0.987,
    "avg_latency_ms": 1245,
    "p95_latency_ms": 2500,
    "total_cost_usd": 127.45,
    "total_tokens": {
      "input": 15000000,
      "output": 8500000
    },
    "requests_by_provider": [
      {
        "provider": "vertex_ai",
        "count": 25000,
        "success_rate": 0.99,
        "avg_latency_ms": 1100
      }
    ],
    "requests_by_agent": [
      {
        "agent": "swap_agent",
        "count": 18000,
        "avg_latency_ms": 1050
      }
    ],
    "retry_rate": 0.032,
    "circuit_breakers_open": 0
  }
}
```

### Get Telemetry Time Series
**Endpoint**: `GET /api/admin/llm/telemetry/timeseries`  
**Query Params**:
- `metric` (string, optional): Metric type - `requests`, `latency`, `cost`, `errors`, `tokens` (Default: `requests`).
- `period` (string, optional): Time period - `1h`, `24h`, `7d`, `30d` (Default: `24h`).
- `group_by` (string, optional): Grouping dimension - `provider`, `model`, `agent` (Default: `provider`).
- `interval` (string, optional): Interval - `auto`, `5m`, `1h`, `1d` (Default: `auto`).

#### Response Body (`TelemetryResponse`)
| Field | Type | Description |
|---|---|---|
| `success` | `boolean` | Whether request was successful |
| `data` | `TelemetryTimeSeriesData` | Time series data |

**TelemetryTimeSeriesData Object**:
| Field | Type | Description |
|---|---|---|
| `metric` | `string` | Metric type |
| `period` | `string` | Time period |
| `interval` | `string` | Interval used |
| `data` | `TimeSeriesPoint[]` | Array of time series points |

**TimeSeriesPoint Object**:
| Field | Type | Description |
|---|---|---|
| `timestamp` | `string` | ISO 8601 timestamp |
| `value` | `number` | Metric value |
| `breakdown` | `{ [key: string]: number }` | Optional: Breakdown by group_by dimension |

**JSON Example**:
```json
{
  "success": true,
  "data": {
    "metric": "requests",
    "period": "24h",
    "interval": "1h",
    "data": [
      {
        "timestamp": "2024-01-15T00:00:00Z",
        "value": 1500,
        "breakdown": {
          "vertex_ai": 800,
          "deepinfra": 400,
          "bedrock": 300
        }
      }
    ]
  }
}
```

### Get Cost Analysis
**Endpoint**: `GET /api/admin/llm/telemetry/cost`  
**Query Params**:
- `period` (string, optional): Time period - `1h`, `24h`, `7d`, `30d` (Default: `24h`).
- `group_by` (string, optional): Grouping - `provider`, `model`, `agent`, `day` (Default: `provider`).

#### Response Body (`TelemetryResponse`)
| Field | Type | Description |
|---|---|---|
| `success` | `boolean` | Whether request was successful |
| `data` | `CostAnalysisData` | Cost analysis data |

**CostAnalysisData Object**:
| Field | Type | Description |
|---|---|---|
| `period` | `string` | Time period |
| `total_cost_usd` | `number` | Total cost in USD |
| `avg_cost_per_request` | `number` | Average cost per request |
| `cost_breakdown` | `CostBreakdownEntry[]` | Cost breakdown by group_by |
| `projected_monthly_cost` | `number` | Projected monthly cost |
| `cost_trend` | `TimeSeriesPoint[]` | Cost trend over time |

**CostBreakdownEntry Object**:
| Field | Type | Description |
|---|---|---|
| `key` | `string` | Group key (provider/model/agent name) |
| `cost_usd` | `number` | Cost in USD |
| `percentage` | `number` | Percentage of total (0-100) |
| `request_count` | `number` | Request count |

### Error Codes
| Status | Error Code | Description | UI Behavior |
|---|---|---|---|
| `401` | `AuthenticationError` | Invalid or expired token | Redirect to login |
| `403` | `AuthorizationError` | Not admin | Show error: "Admin access required" |
| `400` | `DomainFieldError` | Invalid period or metric parameter | Show error: "Invalid parameter" + Reset to defaults |
| `500` | `Exception` | Internal server error | Show error: "Failed to load telemetry" + Retry button |
| `503` | `DataMapperError` | Service unavailable | Show error: "Service unavailable" + Retry button |

## 3. Implementation Flow

1. **Mount**: Call `useTelemetryOverview(period)` hook which fetches `/api/admin/llm/telemetry/overview`.
2. **Display**:
   - Overview cards: Display `total_requests`, `success_rate`, `avg_latency_ms`, `total_cost_usd` in summary cards.
   - Provider breakdown: Display `requests_by_provider` in a table or chart.
   - Agent breakdown: Display `requests_by_agent` in a table or chart.
   - Token usage: Display `total_tokens.input` and `total_tokens.output`.
3. **Period Selection**: On period change (1h, 24h, 7d, 30d), update `period` query param and refetch overview.
4. **Time Series Charts**: 
   - Call `GET /api/admin/llm/telemetry/timeseries` with selected `metric`, `period`, `group_by`, `interval`.
   - Display time series chart using `data` array.
   - Support metric switching (requests, latency, cost, errors, tokens).
   - Support group_by switching (provider, model, agent).
5. **Cost Analysis**: 
   - Call `GET /api/admin/llm/telemetry/cost` with selected `period` and `group_by`.
   - Display cost breakdown chart using `cost_breakdown`.
   - Display projected monthly cost.
   - Display cost trend chart.
6. **Real-time Updates**: Connect to WebSocket endpoint `/api/admin/llm/dashboard/ws` for live telemetry updates (optional).
