# Module: Chat Dashboard & Analytics

**Route**: `/admin/overview/chat`  
**Auth Required**: Yes (Admin Only)  
**Package**: `admin/overview/chat`

## 1. Overview
Displays real-time analytics for the platform's AI chat interactions. Provides mission control visibility into usage, agent performance, costs, errors, and cache efficiency.

## 2. API Contract

### Get Chat Dashboard Summary
**Endpoint**: `GET /api/admin/chat/dashboard`  
**Query Params**:
- `date_from` (datetime, optional): Start date for analytics (Default: 30 days ago, ISO 8601 format).
- `date_to` (datetime, optional): End date for analytics (Default: Now, ISO 8601 format).

#### Response Body (`AdminChatDashboardSummaryResponse`)
| Field | Type | Description |
|---|---|---|
| `date_from` | `string` | ISO 8601 start date |
| `date_to` | `string` | ISO 8601 end date |
| `total_conversations` | `number` | Total conversations in period |
| `total_messages` | `number` | Total messages sent |
| `total_active_users` | `number` | Unique active users |
| `total_cost_usd` | `number` | Total cost in USD |
| `total_agent_invocations` | `number` | Total agent calls |
| `most_used_agent` | `string` | Agent type with most invocations |
| `avg_success_rate` | `number` | Average success rate (0-1) |
| `avg_response_time_ms` | `number` | Average response time in milliseconds |
| `error_rate` | `number` | Error rate (0-1) |
| `cache_hit_rate` | `number` | Cache hit rate (0-1) |
| `top_agents` | `AgentLeaderboardEntry[]` | Top 5 agents by invocations |
| `conversation_trend` | `TimeSeriesDataPoint[]` | Daily conversation count trend |
| `cost_trend` | `TimeSeriesDataPoint[]` | Daily cost trend |

**AgentLeaderboardEntry Object**:
| Field | Type | Description |
|---|---|---|
| `agent_type` | `string` | Agent identifier (e.g., "swap_agent") |
| `agent_name` | `string` | Display name |
| `rank` | `number` | Leaderboard rank |
| `total_invocations` | `number` | Total invocations |
| `success_rate` | `number` | Success rate (0-1) |
| `avg_response_time_ms` | `number` | Average response time |
| `total_cost_usd` | `number` | Total cost for this agent |
| `error_count` | `number` | Total errors |
| `last_used` | `string \| null` | ISO 8601 timestamp or null |

**TimeSeriesDataPoint Object**:
| Field | Type | Description |
|---|---|---|
| `timestamp` | `string` | ISO 8601 timestamp |
| `value` | `number` | Metric value |
| `label` | `string \| null` | Optional label |

**JSON Example**:
```json
{
  "date_from": "2024-01-01T00:00:00Z",
  "date_to": "2024-01-15T10:30:00Z",
  "total_conversations": 1250,
  "total_messages": 8900,
  "total_active_users": 450,
  "total_cost_usd": 125.50,
  "total_agent_invocations": 5000,
  "most_used_agent": "swap_agent",
  "avg_success_rate": 0.987,
  "avg_response_time_ms": 1200,
  "error_rate": 0.005,
  "cache_hit_rate": 0.45,
  "top_agents": [
    {
      "agent_type": "swap_agent",
      "agent_name": "Swap Agent",
      "rank": 1,
      "total_invocations": 2500,
      "success_rate": 0.99,
      "avg_response_time_ms": 800,
      "total_cost_usd": 50.00,
      "error_count": 25,
      "last_used": "2024-01-15T10:25:00Z"
    }
  ],
  "conversation_trend": [
    {
      "timestamp": "2024-01-01T00:00:00Z",
      "value": 80,
      "label": null
    }
  ],
  "cost_trend": [
    {
      "timestamp": "2024-01-01T00:00:00Z",
      "value": 4.50,
      "label": null
    }
  ]
}
```

### Get Agent Performance
**Endpoint**: `GET /api/admin/chat/dashboard/agents/performance`  
**Query Params**:
- `date_from` (datetime, optional): Start date (Default: 30 days ago).
- `date_to` (datetime, optional): End date (Default: Now).
- `agent_type` (string, optional): Filter by agent type.
- `sort_by` (string, optional): Sort metric - `invocations`, `success_rate`, `avg_response_time`, `total_cost` (Default: `invocations`).
- `limit` (number, optional): Max results (Default: 10).

#### Response Body (`AgentPerformanceResponse`)
| Field | Type | Description |
|---|---|---|
| `date_from` | `string` | ISO 8601 start date |
| `date_to` | `string` | ISO 8601 end date |
| `total_agents` | `number` | Total number of agents |
| `leaderboard` | `AgentLeaderboardEntry[]` | Ranked agent list |
| `total_invocations` | `number` | Total invocations across all agents |
| `overall_success_rate` | `number` | Overall success rate (0-1) |
| `avg_response_time_ms` | `number` | Average response time |
| `total_cost_usd` | `number` | Total cost across all agents |
| `invocation_trend` | `TimeSeriesDataPoint[]` | Invocation trend over time |
| `response_time_trend` | `TimeSeriesDataPoint[]` | Response time trend over time |

### Get Cache Efficiency
**Endpoint**: `GET /api/admin/chat/dashboard/cache/efficiency`  
**Query Params**:
- `date_from` (datetime, optional): Start date (Default: 7 days ago).
- `date_to` (datetime, optional): End date (Default: Now).

#### Response Body (`CacheEfficiencyResponse`)
| Field | Type | Description |
|---|---|---|
| `date_from` | `string` | ISO 8601 start date |
| `date_to` | `string` | ISO 8601 end date |
| `overall_hit_rate` | `number` | Overall cache hit rate (0-1) |
| `overall_miss_rate` | `number` | Overall cache miss rate (0-1) |
| `total_memory_usage_mb` | `number` | Total memory usage in MB |
| `total_cache_entries` | `number` | Total cache entries |
| `cache_statistics` | `CacheStatistics[]` | Per-cache-type statistics |
| `avg_cache_hit_time_ms` | `number` | Average hit lookup time |
| `avg_cache_miss_time_ms` | `number` | Average miss lookup time |
| `estimated_time_saved_seconds` | `number` | Estimated time saved by cache |
| `hit_rate_trend` | `TimeSeriesDataPoint[]` | Hit rate trend over time |
| `memory_usage_trend` | `TimeSeriesDataPoint[]` | Memory usage trend over time |

### Get Cost Tracking
**Endpoint**: `GET /api/admin/chat/dashboard/costs`  
**Query Params**:
- `date_from` (datetime, optional): Start date (Default: 30 days ago).
- `date_to` (datetime, optional): End date (Default: Now).
- `group_by` (string, optional): Group dimension - `agent`, `model`, `day`, `user` (Default: `agent`).

#### Response Body (`CostTrackingResponse`)
| Field | Type | Description |
|---|---|---|
| `date_from` | `string` | ISO 8601 start date |
| `date_to` | `string` | ISO 8601 end date |
| `total_cost_usd` | `number` | Total cost in USD |
| `avg_cost_per_conversation` | `number` | Average cost per conversation |
| `total_tokens_used` | `number` | Total tokens used |
| `cost_breakdown` | `CostBreakdownEntry[]` | Cost breakdown by group_by dimension |
| `most_expensive_agent` | `string` | Agent with highest cost |
| `most_expensive_model` | `string` | Model with highest cost |
| `highest_cost_user_id` | `number \| null` | User ID with highest cost |
| `projected_monthly_cost_usd` | `number` | Projected monthly cost |
| `cost_change_percentage` | `number` | Cost change vs previous period |
| `daily_cost_trend` | `TimeSeriesDataPoint[]` | Daily cost trend |
| `cost_by_agent_trend` | `{ [agent: string]: TimeSeriesDataPoint[] }` | Cost trend per agent |

### Get Error Monitoring
**Endpoint**: `GET /api/admin/chat/dashboard/errors`  
**Query Params**:
- `date_from` (datetime, optional): Start date (Default: 7 days ago).
- `date_to` (datetime, optional): End date (Default: Now).
- `severity` (string, optional): Filter by severity - `critical`, `high`, `medium`, `low`.

#### Response Body (`ErrorMonitoringResponse`)
| Field | Type | Description |
|---|---|---|
| `date_from` | `string` | ISO 8601 start date |
| `date_to` | `string` | ISO 8601 end date |
| `total_errors` | `number` | Total error count |
| `error_rate` | `number` | Error rate (0-1) |
| `errors_by_type` | `ErrorTypeCount[]` | Errors grouped by type |
| `errors_by_agent` | `ErrorAgentCount[]` | Errors grouped by agent |
| `top_errors` | `TopError[]` | Top errors by count |
| `error_trend` | `TimeSeriesDataPoint[]` | Error count trend over time |

### Get Active Users
**Endpoint**: `GET /api/admin/chat/dashboard/users/active`  
**Query Params**:
- `date_from` (datetime, optional): Start date (Default: 30 days ago).
- `date_to` (datetime, optional): End date (Default: Now).

#### Response Body (`ActiveUsersResponse`)
| Field | Type | Description |
|---|---|---|
| `date_from` | `string` | ISO 8601 start date |
| `date_to` | `string` | ISO 8601 end date |
| `dau` | `number` | Daily Active Users |
| `wau` | `number` | Weekly Active Users |
| `mau` | `number` | Monthly Active Users |
| `retention_rate` | `number` | User retention rate (0-1) |
| `avg_sessions_per_user` | `number` | Average sessions per user |
| `new_users_count` | `number` | New users in period |
| `returning_users_count` | `number` | Returning users in period |
| `user_activity_trend` | `TimeSeriesDataPoint[]` | Daily active users trend |

### Export Dashboard Data
**Endpoint**: `GET /api/admin/chat/dashboard/export`  
**Query Params**:
- `date_from` (datetime, optional): Start date (Default: 30 days ago).
- `date_to` (datetime, optional): End date (Default: Now).
- `format` (string, **required**): Export format - `json`, `csv`.
- `include_sections` (string[], optional): Sections to include - `agents`, `costs`, `errors`, `users`, `conversations` (Default: all).

#### Response
Returns export data in requested format (JSON or CSV file download).

### Error Codes
| Status | Error Code | Description | UI Behavior |
|---|---|---|---|
| `401` | `AuthenticationError` | Invalid or expired token | Redirect to login |
| `403` | `AuthorizationError` | Not admin | Show error: "Admin access required" |
| `400` | `DomainFieldError` | Invalid date format or parameter | Show error: "Invalid date format" + Reset to defaults |
| `500` | `Exception` | Internal server error | Show error: "Failed to load dashboard" + Retry button |
| `503` | `DataMapperError` | Service unavailable | Show error: "Service temporarily unavailable" + Retry button |

## 3. Implementation Flow

1. **Mount**: Call `useChatDashboard(dateFrom, dateTo)` hook which fetches `/api/admin/chat/dashboard`.
2. **Display**:
   - Summary cards: `total_conversations`, `total_messages`, `total_active_users`, `total_cost_usd`.
   - Sparkline charts: Use `conversation_trend` and `cost_trend` for mini charts in summary cards.
   - Agent leaderboard: Display `top_agents` in a table with sortable columns.
   - Cost breakdown: Use `cost_breakdown` from cost tracking endpoint for stacked bar chart.
   - Error summary: Display `error_rate` and `top_errors` in error monitoring section.
3. **Date Range Selection**: Update `date_from` and `date_to` query params, refetch all dashboard data.
4. **Real-time Updates**: Connect to WebSocket endpoint `/api/admin/llm/dashboard/ws` for live metrics updates (optional).
5. **Export**: On export button click, call export endpoint with current filters, trigger file download.
