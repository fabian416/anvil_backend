# Module: Retry System

**Route**: `/admin/system-health/retry`  
**Auth Required**: Yes (Admin Only)  
**Package**: `admin/system-health/retry`

## 1. Overview
Enables administrators to monitor and control the retry system for service reliability. Provides visibility into service status, circuit breakers, and retry metrics, allowing admins to manage service availability and troubleshoot issues.

## 2. API Contract

### List Services
**Endpoint**: `GET /api/v1/admin/retry/services`  
**Query Params**: None

#### Response Body (`ServiceListResponse`)
| Field | Type | Description |
|---|---|---|
| `services` | `ServiceStatusResponse[]` | Array of service status objects |

**ServiceStatusResponse Object**:
| Field | Type | Description |
|---|---|---|
| `service_name` | `string` | Service identifier |
| `enabled` | `boolean` | Whether service is enabled |
| `circuit_state` | `string` | Circuit breaker state: `CLOSED`, `OPEN`, `HALF_OPEN` |
| `failure_count` | `number` | Total failure count |
| `success_count` | `number` | Total success count |
| `last_error` | `string \| null` | Last error message or null |
| `last_error_at` | `string \| null` | ISO 8601 timestamp of last error or null |
| `override_reason` | `string \| null` | Manual override reason or null |
| `override_expires_at` | `string \| null` | ISO 8601 expiration timestamp or null |

**JSON Example**:
```json
{
  "services": [
    {
      "service_name": "openai_api",
      "enabled": true,
      "circuit_state": "CLOSED",
      "failure_count": 0,
      "success_count": 100,
      "last_error": null,
      "last_error_at": null,
      "override_reason": null,
      "override_expires_at": null
    },
    {
      "service_name": "anthropic_api",
      "enabled": true,
      "circuit_state": "OPEN",
      "failure_count": 6,
      "success_count": 50,
      "last_error": "Rate limit exceeded",
      "last_error_at": "2024-01-15T10:00:00Z",
      "override_reason": null,
      "override_expires_at": null
    }
  ]
}
```

### Get Service Status
**Endpoint**: `GET /api/v1/admin/retry/services/{service_name}`  
**Path Params**:
- `service_name` (string, **required**): Service identifier.

#### Response Body (`ServiceStatusResponse`)
Returns detailed service status object (same structure as above).

### Disable Service
**Endpoint**: `POST /api/v1/admin/retry/services/{service_name}/disable`  
**Path Params**:
- `service_name` (string, **required**): Service identifier.

#### Request Body (`DisableServiceRequest`)
| Field | Type | Description |
|---|---|---|
| `reason` | `string` | Reason for disabling (required) |
| `duration_minutes` | `number \| null` | Optional: Duration in minutes (null = indefinite) |

**JSON Example**:
```json
{
  "reason": "Maintenance window",
  "duration_minutes": 60
}
```

#### Response
`200 OK` - Returns success message

### Enable Service
**Endpoint**: `POST /api/v1/admin/retry/services/{service_name}/enable`  
**Path Params**:
- `service_name` (string, **required**): Service identifier.

#### Request Body (`EnableServiceRequest`)
| Field | Type | Description |
|---|---|---|
| `reason` | `string` | Reason for enabling (required) |

**JSON Example**:
```json
{
  "reason": "Maintenance complete"
}
```

#### Response
`200 OK` - Returns success message

### Get Circuit Breakers
**Endpoint**: `GET /api/v1/admin/retry/circuit-breakers`  
**Query Params**: None

#### Response Body (`CircuitBreakerStatusResponse[]`)
Array of circuit breaker status objects.

**CircuitBreakerStatusResponse Object**:
| Field | Type | Description |
|---|---|---|
| `service_name` | `string` | Service identifier |
| `state` | `string` | Breaker state: `CLOSED`, `OPEN`, `HALF_OPEN` |
| `failure_count` | `number` | Failure count |
| `success_count` | `number` | Success count |
| `opened_at` | `string \| null` | ISO 8601 timestamp when opened or null |
| `config` | `CircuitBreakerConfig` | Breaker configuration |

**CircuitBreakerConfig Object**:
| Field | Type | Description |
|---|---|---|
| `failure_threshold` | `number` | Failure threshold to open |
| `success_threshold` | `number` | Success threshold to close |
| `timeout_seconds` | `number` | Timeout in seconds |

**JSON Example**:
```json
[
  {
    "service_name": "openai_api",
    "state": "CLOSED",
    "failure_count": 0,
    "success_count": 100,
    "opened_at": null,
    "config": {
      "failure_threshold": 5,
      "success_threshold": 2,
      "timeout_seconds": 60
    }
  }
]
```

### Reset Circuit Breaker
**Endpoint**: `POST /api/v1/admin/retry/circuit-breakers/{service_name}/reset`  
**Path Params**:
- `service_name` (string, **required**): Service identifier.

#### Request Body (`ResetCircuitBreakerRequest`)
| Field | Type | Description |
|---|---|---|
| `reason` | `string` | Reason for reset (required) |

**JSON Example**:
```json
{
  "reason": "Issue resolved, provider has recovered"
}
```

#### Response
`200 OK` - Returns success message

### Get Service Metrics
**Endpoint**: `GET /api/v1/admin/retry/metrics/{service_name}`  
**Path Params**:
- `service_name` (string, **required**): Service identifier.

**Query Params**:
- `days` (number, optional): Number of days to look back (Default: 7, Max: 30).

#### Response Body (`ServiceMetricsResponse`)
| Field | Type | Description |
|---|---|---|
| `service_name` | `string` | Service identifier |
| `period_days` | `number` | Period in days |
| `total_requests` | `number` | Total requests |
| `successful_requests` | `number` | Successful requests |
| `failed_requests` | `number` | Failed requests |
| `success_rate` | `number` | Success rate (0-1) |
| `avg_latency_ms` | `number` | Average latency in milliseconds |
| `p95_latency_ms` | `number` | 95th percentile latency |
| `retry_count` | `number` | Total retry count |
| `circuit_breaker_opens` | `number` | Number of times circuit breaker opened |
| `daily_metrics` | `DailyServiceMetric[]` | Daily metrics breakdown |

**DailyServiceMetric Object**:
| Field | Type | Description |
|---|---|---|
| `date` | `string` | ISO 8601 date |
| `requests` | `number` | Request count |
| `success_rate` | `number` | Success rate (0-1) |
| `avg_latency_ms` | `number` | Average latency |

### Error Codes
| Status | Error Code | Description | UI Behavior |
|---|---|---|---|
| `401` | `AuthenticationError` | Invalid or expired token | Redirect to login |
| `403` | `AuthorizationError` | Not admin | Show error: "Admin access required" |
| `404` | `NotFoundError` | Service not found | Show error: "Service not found" |
| `400` | `DomainFieldError` | Invalid request data (missing reason) | Show error: "Reason is required" |
| `409` | `DomainConflictError` | Service already in requested state | Show error: "Service is already {state}" |
| `500` | `Exception` | Internal server error | Show error: "Failed to manage retry system" + Retry button |
| `503` | `DataMapperError` | Service unavailable | Show error: "Service unavailable" + Retry button |

## 3. Implementation Flow

1. **Mount**: Call `useRetryServices()` hook which fetches `/api/v1/admin/retry/services`.
2. **Display**:
   - Service status table: Display `services` array with columns: Service Name, Status (Enabled/Disabled badge), Circuit State (with color coding), Failure Count, Success Count, Last Error, Actions.
   - Circuit state indicators:
     - **CLOSED (Green)**: Normal operation, requests allowed.
     - **OPEN (Red)**: Circuit is open, requests blocked.
     - **HALF_OPEN (Yellow)**: Testing state, limited requests allowed.
3. **Service Control**:
   - **Disable Service**: On "Disable" button click:
     - Open disable modal with reason field (required) and optional duration.
     - Call `POST /api/v1/admin/retry/services/{service_name}/disable` with reason and duration.
     - On success: Update service status, show success toast, invalidate query cache.
   - **Enable Service**: On "Enable" button click:
     - Open enable modal with reason field (required).
     - Call `POST /api/v1/admin/retry/services/{service_name}/enable` with reason.
     - On success: Update service status, show success toast, invalidate query cache.
4. **Circuit Breaker Management**:
   - Call `GET /api/v1/admin/retry/circuit-breakers` to display circuit breaker status.
   - **Reset Circuit Breaker**: On "Reset" button click (only available when state is `OPEN` or `HALF_OPEN`):
     - Show confirmation modal with reason field (required).
     - Call `POST /api/v1/admin/retry/circuit-breakers/{service_name}/reset` with reason.
     - On success: Update circuit breaker state to "CLOSED", show success toast, invalidate query cache.
5. **View Service Metrics**: On "View Metrics" button click:
   - Call `GET /api/v1/admin/retry/metrics/{service_name}` with optional days parameter.
   - Display metrics in modal or navigate to metrics view:
     - Summary cards: Total requests, success rate, average latency.
     - Daily metrics chart: Line chart showing daily request counts and success rates.
6. **Auto-refresh**: Poll service status every 30 seconds for real-time updates.
