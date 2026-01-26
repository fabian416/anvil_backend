# Retry & Resilience Endpoints Specification

> **Last Updated**: 2026-01-25  
> **Status**: Production  
> **Maintainers**: @backend-engineer @error-detective @code-reviewer

---

## Executive Summary

The Retry & Resilience system provides **admin-only APIs** for:
1. **Service Management** - Enable/disable services manually
2. **Circuit Breaker Control** - View and reset circuit breakers
3. **Metrics & Telemetry** - View retry metrics and service health

**Base Path**: `/api/v1/admin/retry`

> **Note**: This is an admin-only module. There are no guest or user endpoints.

---

## 1. Service Management Endpoints

### GET /admin/retry/services

List all services with their retry status.

**Authentication**: Required (Admin)

**Response** (`ServiceListResponse`):
```json
{
  "services": [
    {
      "service_name": "defillama_mcp",
      "enabled": true,
      "circuit_state": "CLOSED",
      "failure_count": 0,
      "success_count": 150,
      "last_error": null,
      "last_error_at": null,
      "override_reason": null,
      "override_expires_at": null
    },
    {
      "service_name": "1inch_mcp",
      "enabled": false,
      "circuit_state": "OPEN",
      "failure_count": 5,
      "success_count": 0,
      "last_error": "503 Service Unavailable",
      "last_error_at": "2026-01-25T12:30:00Z",
      "override_reason": "1inch API experiencing outage - https://status.1inch.io",
      "override_expires_at": "2026-01-25T15:30:00Z"
    }
  ]
}
```

---

### GET /admin/retry/services/{service_name}

Get detailed status for a specific service.

**Authentication**: Required (Admin)

**Path Parameters**:
| Parameter | Type | Description |
|-----------|------|-------------|
| `service_name` | string | Service identifier (e.g., `defillama_mcp`, `1inch_mcp`) |

**Response** (`ServiceStatusResponse`):
```json
{
  "service_name": "defillama_mcp",
  "enabled": true,
  "circuit_state": "CLOSED",
  "failure_count": 2,
  "success_count": 245,
  "last_error": "timeout",
  "last_error_at": "2026-01-25T10:15:00Z",
  "override_reason": null,
  "override_expires_at": null
}
```

---

### POST /admin/retry/services/{service_name}/disable

Manually disable a service.

**Authentication**: Required (Admin)

**Path Parameters**:
| Parameter | Type | Description |
|-----------|------|-------------|
| `service_name` | string | Service identifier |

**Request Body** (`DisableServiceRequest`):
```json
{
  "reason": "1inch API experiencing outage - https://status.1inch.io/incidents/123",
  "duration_minutes": 180
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `reason` | string | Yes | Reason for disabling |
| `duration_minutes` | int | No | Auto re-enable after duration (None = permanent) |

**Response**:
```json
{
  "message": "Service '1inch_mcp' disabled",
  "reason": "1inch API experiencing outage - https://status.1inch.io/incidents/123",
  "duration_minutes": 180
}
```

**Use Cases**:
- Known API outage
- Rate limit exhausted
- Maintenance window
- Cost control

---

### POST /admin/retry/services/{service_name}/enable

Manually enable a previously disabled service.

**Authentication**: Required (Admin)

**Path Parameters**:
| Parameter | Type | Description |
|-----------|------|-------------|
| `service_name` | string | Service identifier |

**Request Body** (`EnableServiceRequest`):
```json
{
  "reason": "1inch API back online - verified via status page"
}
```

**Response**:
```json
{
  "message": "Service '1inch_mcp' enabled",
  "reason": "1inch API back online - verified via status page"
}
```

---

## 2. Circuit Breaker Endpoints

### GET /admin/retry/circuit-breakers

Get circuit breaker status for all services.

**Authentication**: Required (Admin)

**Response** (`List[CircuitBreakerStatusResponse]`):
```json
[
  {
    "service_name": "defillama_mcp",
    "state": "CLOSED",
    "failure_count": 0,
    "success_count": 10,
    "opened_at": null,
    "config": {
      "failure_threshold": 5,
      "success_threshold": 2,
      "timeout_seconds": 60
    }
  },
  {
    "service_name": "1inch_mcp",
    "state": "OPEN",
    "failure_count": 5,
    "success_count": 0,
    "opened_at": "2026-01-25T12:30:00Z",
    "config": {
      "failure_threshold": 5,
      "success_threshold": 2,
      "timeout_seconds": 60
    }
  },
  {
    "service_name": "coingecko_mcp",
    "state": "HALF_OPEN",
    "failure_count": 0,
    "success_count": 1,
    "opened_at": "2026-01-25T12:29:00Z",
    "config": {
      "failure_threshold": 5,
      "success_threshold": 2,
      "timeout_seconds": 60
    }
  }
]
```

**Circuit Breaker States**:
| State | Description |
|-------|-------------|
| `CLOSED` | Normal operation, requests allowed |
| `OPEN` | Failures exceeded threshold, requests blocked |
| `HALF_OPEN` | Testing recovery, limited requests allowed |

---

### POST /admin/retry/circuit-breakers/{service_name}/reset

Manually reset a circuit breaker to CLOSED state.

**Authentication**: Required (Admin)

**Path Parameters**:
| Parameter | Type | Description |
|-----------|------|-------------|
| `service_name` | string | Service identifier |

**Request Body** (`ResetCircuitBreakerRequest`):
```json
{
  "reason": "Verified service is healthy via external check"
}
```

**Response**:
```json
{
  "message": "Circuit breaker for '1inch_mcp' reset to CLOSED",
  "reason": "Verified service is healthy via external check"
}
```

---

## 3. Metrics Endpoints

### GET /admin/retry/metrics/{service_name}

Get aggregated metrics for a service over time.

**Authentication**: Required (Admin)

**Path Parameters**:
| Parameter | Type | Description |
|-----------|------|-------------|
| `service_name` | string | Service identifier |

**Query Parameters**:
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `days` | int | 7 | Number of days to retrieve (1-90) |

**Response** (`ServiceMetricsResponse`):
```json
{
  "service_name": "defillama_mcp",
  "days": 7,
  "metrics": [
    {
      "date": "2026-01-25",
      "total_requests": 1250,
      "successful_requests": 1200,
      "failed_requests": 50,
      "retry_attempts": 75,
      "avg_latency_ms": 245.5,
      "circuit_breaker_opens": 0,
      "success_rate": 0.96
    },
    {
      "date": "2026-01-24",
      "total_requests": 1100,
      "successful_requests": 1050,
      "failed_requests": 50,
      "retry_attempts": 60,
      "avg_latency_ms": 230.2,
      "circuit_breaker_opens": 1,
      "success_rate": 0.9545
    }
  ],
  "summary": {
    "total_requests": 8500,
    "avg_success_rate": 0.957,
    "avg_latency_ms": 238.5,
    "total_circuit_opens": 2
  }
}
```

---

## 4. Available Services

The following services are monitored by the retry system:

### MCP Servers
| Service Name | Description |
|--------------|-------------|
| `defillama_mcp` | DeFiLlama protocol data |
| `1inch_mcp` | 1inch DEX aggregator |
| `coingecko_mcp` | CoinGecko market data |
| `thegraph_mcp` | The Graph protocol indexer |
| `aave_mcp` | Aave lending protocol |
| `portfolio_mcp` | Portfolio tracking |
| `perplexity_mcp` | Perplexity AI research |
| `morpho_mcp` | Morpho lending optimizer |
| `curve_mcp` | Curve Finance pools |
| `hyperliquid_mcp` | Hyperliquid DEX |
| `layerzero_mcp` | LayerZero bridge |

### LLM Providers
| Service Name | Description |
|--------------|-------------|
| `vertex_ai` | Google Vertex AI |
| `deepinfra` | DeepInfra LLM |
| `openai` | OpenAI GPT models |
| `anthropic` | Anthropic Claude |

### External APIs
| Service Name | Description |
|--------------|-------------|
| `aave_api` | Aave smart contracts |
| `privy_api` | Privy authentication |

---

## 5. Error Responses

### Service Not Found
```json
{
  "detail": "Service 'unknown_service' not found"
}
```
**Status**: 404

### Service Already Disabled
```json
{
  "detail": "Service '1inch_mcp' is already disabled"
}
```
**Status**: 409

### Service Already Enabled
```json
{
  "detail": "Service '1inch_mcp' is not disabled"
}
```
**Status**: 409

---

## 6. API Client Examples

### List All Services
```bash
curl -X GET "http://localhost:8000/api/v1/admin/retry/services" \
  -H "Authorization: Bearer $ADMIN_TOKEN"
```

### Disable Service
```bash
curl -X POST "http://localhost:8000/api/v1/admin/retry/services/1inch_mcp/disable" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "reason": "1inch API outage",
    "duration_minutes": 60
  }'
```

### Enable Service
```bash
curl -X POST "http://localhost:8000/api/v1/admin/retry/services/1inch_mcp/enable" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"reason": "Service recovered"}'
```

### Get Circuit Breakers
```bash
curl -X GET "http://localhost:8000/api/v1/admin/retry/circuit-breakers" \
  -H "Authorization: Bearer $ADMIN_TOKEN"
```

### Reset Circuit Breaker
```bash
curl -X POST "http://localhost:8000/api/v1/admin/retry/circuit-breakers/1inch_mcp/reset" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"reason": "Manual recovery verification"}'
```

### Get Service Metrics
```bash
curl -X GET "http://localhost:8000/api/v1/admin/retry/metrics/defillama_mcp?days=7" \
  -H "Authorization: Bearer $ADMIN_TOKEN"
```

---

## References

- **Router**: `src/app/presentation/http/controllers/admin/retry/router.py`
- **Schemas**: `src/app/presentation/http/controllers/admin/retry/schemas.py`
- **Interactors**: `src/app/application/admin/retry/`
