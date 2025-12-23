# Module: System Stats

**Route**: `/admin/system-health/stats`  
**Auth Required**: Yes (Admin Only)  
**Package**: `admin/system-health/stats`

## 1. Overview
Provides high-level system statistics for administrators. Offers a quick overview of active conversations, message counts, agent usage, and other key system metrics. Real-time stats that reflect current system state.

## 2. API Contract

### Get System Statistics
**Endpoint**: `GET /api/admin/stats/`  
**Query Params**: None

#### Response Body (`AdminStats`)
| Field | Type | Description |
|---|---|---|
| `active_conversations` | `number` | Number of currently active conversations |
| `total_messages` | `number` | Total number of messages in the system |
| `active_agents` | `number` | Number of active agents |
| `agent_usage` | `AgentUsage[]` | Array of agent usage statistics by type |

**AgentUsage Object**:
| Field | Type | Description |
|---|---|---|
| `agent_type` | `string` | Agent type identifier |
| `count` | `number` | Usage count for this agent |

**JSON Example**:
```json
{
  "active_conversations": 10,
  "total_messages": 150,
  "active_agents": 5,
  "agent_usage": [
    {
      "agent_type": "trading",
      "count": 50
    },
    {
      "agent_type": "research",
      "count": 30
    },
    {
      "agent_type": "yield_farming",
      "count": 20
    },
    {
      "agent_type": "risk_analysis",
      "count": 15
    },
    {
      "agent_type": "portfolio",
      "count": 10
    }
  ]
}
```

### Error Codes
| Status | Error Code | Description | UI Behavior |
|---|---|---|---|
| `401` | `AuthenticationError` | Invalid or expired token | Redirect to login |
| `403` | `AuthorizationError` | Not admin | Show error: "Admin access required" |
| `500` | `Exception` | Internal server error | Show error: "Failed to load stats" + Retry button |
| `503` | `DataMapperError` | Service unavailable | Show error: "Service unavailable" + Retry button |

## 3. Implementation Flow

1. **Mount**: Call `useStats()` hook which fetches `/api/admin/stats/`.
2. **Display**:
   - Summary cards: Display `active_conversations`, `total_messages`, `active_agents` in large number cards.
   - Agent usage chart: Display `agent_usage` array in a bar chart (horizontal or vertical) or pie chart showing distribution.
   - Agent type badges: Display agent types with usage counts, sorted by count (highest to lowest).
3. **Auto-refresh**: Poll stats every 30 seconds or 1 minute (configurable toggle).
4. **Manual refresh**: Provide "Refresh" button to manually update statistics.
5. **Loading state**: Show loading indicator while fetching stats.
6. **Error state**: Display error message if stats fetch fails, provide retry button.
