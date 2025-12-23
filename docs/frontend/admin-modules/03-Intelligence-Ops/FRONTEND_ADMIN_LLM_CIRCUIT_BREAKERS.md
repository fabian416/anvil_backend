# Module: LLM Circuit Breakers

**Route**: `/admin/intelligence-ops/circuit-breakers`  
**Auth Required**: Yes (Admin Only)  
**Package**: `admin/intelligence-ops/circuit-breakers`

## 1. Overview
Circuit breakers are automated safety mechanisms that stop traffic to failing models (e.g., if OpenAI is down) to prevent cascading failures. This module allows admins to monitor breaker states and manually reset them when external providers have recovered.

## 2. API Contract

### List Circuit Breakers
**Endpoint**: `GET /api/admin/llm/circuit-breakers`  
**Query Params**: None

#### Response Body (`CircuitBreakerResponse`)
| Field | Type | Description |
|---|---|---|
| `success` | `boolean` | Whether request was successful |
| `data` | `CircuitBreakerListData` | Circuit breaker list data |

**CircuitBreakerListData Object**:
| Field | Type | Description |
|---|---|---|
| `circuit_breakers` | `CircuitBreaker[]` | Array of circuit breaker objects |
| `summary` | `CircuitBreakerSummary` | Summary counts |

**CircuitBreaker Object**:
| Field | Type | Description |
|---|---|---|
| `id` | `string` | Circuit breaker UUID |
| `entity_type` | `string` | Entity type (e.g., "model", "provider") |
| `entity_id` | `string` | Entity UUID |
| `entity_name` | `string` | Entity display name |
| `state` | `string` | Breaker state: `closed`, `open`, `half_open` |
| `failure_count` | `number` | Total failure count |
| `consecutive_failures` | `number` | Consecutive failures |
| `last_failure_at` | `string \| null` | ISO 8601 timestamp of last failure or null |
| `config` | `CircuitBreakerConfig` | Breaker configuration |

**CircuitBreakerConfig Object**:
| Field | Type | Description |
|---|---|---|
| `failure_threshold` | `number` | Failure threshold to open |
| `success_threshold` | `number` | Success threshold to close |
| `timeout_seconds` | `number` | Timeout in seconds |

**CircuitBreakerSummary Object**:
| Field | Type | Description |
|---|---|---|
| `closed` | `number` | Number of closed breakers |
| `open` | `number` | Number of open breakers |
| `half_open` | `number` | Number of half-open breakers |

**JSON Example**:
```json
{
  "success": true,
  "data": {
    "circuit_breakers": [
      {
        "id": "550e8400-e29b-41d4-a716-446655440000",
        "entity_type": "model",
        "entity_id": "660e8400-e29b-41d4-a716-446655440001",
        "entity_name": "gpt-4",
        "state": "closed",
        "failure_count": 0,
        "consecutive_failures": 0,
        "last_failure_at": null,
        "config": {
          "failure_threshold": 5,
          "success_threshold": 2,
          "timeout_seconds": 60
        }
      },
      {
        "id": "770e8400-e29b-41d4-a716-446655440002",
        "entity_type": "model",
        "entity_id": "880e8400-e29b-41d4-a716-446655440003",
        "entity_name": "claude-3-opus",
        "state": "open",
        "failure_count": 6,
        "consecutive_failures": 6,
        "last_failure_at": "2024-01-15T10:00:00Z",
        "config": {
          "failure_threshold": 5,
          "success_threshold": 2,
          "timeout_seconds": 60
        }
      }
    ],
    "summary": {
      "closed": 5,
      "open": 1,
      "half_open": 0
    }
  }
}
```

### Reset Circuit Breaker
**Endpoint**: `POST /api/admin/llm/circuit-breakers/{breaker_id}/reset`  
**Path Params**:
- `breaker_id` (string, **required**): Circuit breaker UUID.

#### Request Body (`ResetCircuitBreakerRequest`)
| Field | Type | Description |
|---|---|---|
| `reason` | `string` | Optional: Reason for reset |

**JSON Example**:
```json
{
  "reason": "Provider has recovered, manually resetting breaker"
}
```

#### Response Body (`ResetCircuitBreakerResponse`)
| Field | Type | Description |
|---|---|---|
| `success` | `boolean` | Whether request was successful |
| `data` | `ResetCircuitBreakerData` | Reset data |

**ResetCircuitBreakerData Object**:
| Field | Type | Description |
|---|---|---|
| `previous_state` | `string` | Previous breaker state |
| `new_state` | `string` | New breaker state (should be "closed") |
| `breaker_id` | `string` | Circuit breaker UUID |

**JSON Example**:
```json
{
  "success": true,
  "data": {
    "previous_state": "open",
    "new_state": "closed",
    "breaker_id": "770e8400-e29b-41d4-a716-446655440002"
  }
}
```

### Error Codes
| Status | Error Code | Description | UI Behavior |
|---|---|---|---|
| `401` | `AuthenticationError` | Invalid or expired token | Redirect to login |
| `403` | `AuthorizationError` | Not admin | Show error: "Admin access required" |
| `404` | `NotFoundError` | Circuit breaker not found | Show error: "Circuit breaker not found" |
| `400` | `DomainFieldError` | Invalid request data | Show error: "Invalid reset request" |
| `409` | `DomainConflictError` | Cannot reset (already closed) | Show error: "Circuit breaker is already closed" |
| `500` | `Exception` | Internal server error | Show error: "Failed to reset circuit breaker" + Retry button |
| `503` | `DataMapperError` | Service unavailable | Show error: "Service unavailable" + Retry button |

## 3. Implementation Flow

1. **Mount**: Call `useCircuitBreakers()` hook which fetches `/api/admin/llm/circuit-breakers`.
2. **Display**:
   - Circuit breaker table: Display `circuit_breakers` array with columns: Entity Name, State (with color coding), Failure Count, Last Failure, Actions.
   - State indicators:
     - **Closed (Green)**: System is healthy, traffic is flowing.
     - **Open (Red)**: System is failing, traffic is blocked.
     - **Half-Open (Yellow)**: System is recovering, limited traffic allowed.
   - Summary cards: Display `summary` counts (closed, open, half-open).
3. **Reset Circuit Breaker**: On "Reset" button click (only available when state is `open` or `half_open`):
   - Show confirmation modal: "Are you sure you want to reset this circuit breaker? This will force traffic to resume to this model."
   - Optional: Request reason for reset.
   - Call `POST /api/admin/llm/circuit-breakers/{breaker_id}/reset` with optional reason.
   - On success: Update breaker state to "closed", show success toast, invalidate query cache.
   - On error: Display error message, provide retry option.
4. **Auto-refresh**: Poll circuit breaker status every 30 seconds or use WebSocket for real-time updates.
