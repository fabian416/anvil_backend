# Module: Agent Management

**Route**: `/admin/intelligence-ops/agents`  
**Auth Required**: Yes (Admin Only)  
**Package**: `admin/intelligence-ops/agents`

## 1. Overview
Enables administrators to view and monitor AI agents available in the system. Provides a list of all agents with their types, names, descriptions, and active status. Currently read-only; future enhancements may include agent configuration and enable/disable controls.

## 2. API Contract

### List Agents
**Endpoint**: `GET /api/admin/agents/`  
**Query Params**: None

#### Response Body (`AgentRead[]`)
Array of agent objects.

**AgentRead Object**:
| Field | Type | Description |
|---|---|---|
| `type` | `string` | Agent type: `TRADING`, `RESEARCH`, `YIELD_FARMING`, `RISK_ANALYSIS`, `PORTFOLIO` |
| `name` | `string` | Agent display name |
| `description` | `string` | Agent description |
| `is_active` | `boolean` | Whether agent is active |

**JSON Example**:
```json
[
  {
    "type": "TRADING",
    "name": "Trading Agent",
    "description": "Analyzes market trends and executes trading strategies",
    "is_active": true
  },
  {
    "type": "RESEARCH",
    "name": "Research Agent",
    "description": "Deep dive into protocols and DeFi opportunities",
    "is_active": true
  },
  {
    "type": "YIELD_FARMING",
    "name": "Yield Farming Agent",
    "description": "Identifies and analyzes yield farming opportunities",
    "is_active": true
  },
  {
    "type": "RISK_ANALYSIS",
    "name": "Risk Analysis Agent",
    "description": "Assesses portfolio and protocol risks",
    "is_active": true
  },
  {
    "type": "PORTFOLIO",
    "name": "Portfolio Agent",
    "description": "Manages and optimizes user portfolios",
    "is_active": true
  }
]
```

### Error Codes
| Status | Error Code | Description | UI Behavior |
|---|---|---|---|
| `401` | `AuthenticationError` | Invalid or expired token | Redirect to login |
| `403` | `AuthorizationError` | Not admin | Show error: "Admin access required" |
| `500` | `Exception` | Internal server error | Show error: "Failed to load agents" + Retry button |
| `503` | `DataMapperError` | Service unavailable | Show error: "Service unavailable" + Retry button |

## 3. Implementation Flow

1. **Mount**: Call `useAgents()` hook which fetches `/api/admin/agents/`.
2. **Display**:
   - Agent cards/table: Display agents array with columns: Type (badge), Name, Description, Status (Active/Inactive badge).
   - Type badges: Color-code by agent type (e.g., Trading=Blue, Research=Green).
   - Status indicators: Green badge for active, Grey badge for inactive.
3. **Sorting**: Allow sorting by type, name, or status (client-side or server-side).
4. **Filtering**: Provide filters for agent type and active status.
5. **Future Enhancements**: Agent configuration management, performance metrics, usage statistics, enable/disable controls (not yet implemented).
