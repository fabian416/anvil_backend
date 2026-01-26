# AI Telemetry System Endpoints Specification

> **Last Updated**: 2026-01-25  
> **Status**: Production  
> **Maintainers**: @backend-engineer @error-detective @code-reviewer

---

## Executive Summary

The AI Telemetry System provides comprehensive observability APIs for:
1. **Feature Flags** - Runtime telemetry configuration
2. **API Metrics** - External API call tracking
3. **Distributed Tracing** - Request tracing
4. **LLM Telemetry** - LLM provider monitoring
5. **Database Telemetry** - Query performance tracking
6. **Prometheus Export** - Metrics for scraping

**Base Path**: `/api/v1/telemetry`  
**Authentication**: Public (read) / Admin (write)

---

## 1. Feature Flags Endpoints

### GET /telemetry/flags

Get current telemetry feature flags.

**Authentication**: None (public)

**Response**:
```json
{
  "global_enabled": true,
  "api_telemetry_enabled": true,
  "llm_telemetry_enabled": true,
  "db_telemetry_enabled": true,
  "tracing_enabled": true,
  "api_sample_rate": 1.0,
  "llm_sample_rate": 1.0,
  "db_sample_rate": 0.1,
  "disabled_apis": [],
  "disabled_llm_providers": []
}
```

---

### PUT /telemetry/flags

Update telemetry feature flags at runtime.

**Authentication**: Required (Admin Bearer Token)

**Query Parameters**:
| Parameter | Type | Description |
|-----------|------|-------------|
| `global_enabled` | bool | Master telemetry switch |
| `api_telemetry_enabled` | bool | Toggle API telemetry |
| `llm_telemetry_enabled` | bool | Toggle LLM telemetry |
| `db_telemetry_enabled` | bool | Toggle database telemetry |
| `tracing_enabled` | bool | Toggle distributed tracing |
| `api_sample_rate` | float | API sampling rate (0.0-1.0) |
| `llm_sample_rate` | float | LLM sampling rate (0.0-1.0) |
| `db_sample_rate` | float | DB sampling rate (0.0-1.0) |

---

### POST /telemetry/flags/disable-api/{api_name}

Disable telemetry for a specific API.

**Authentication**: Required (Admin)

**Path Parameters**:
- `api_name`: Name of the API (e.g., "coingecko", "uniswap")

---

### POST /telemetry/flags/enable-api/{api_name}

Re-enable telemetry for a specific API.

**Authentication**: Required (Admin)

---

### POST /telemetry/flags/disable-llm/{provider}

Disable telemetry for a specific LLM provider.

**Authentication**: Required (Admin)

**Path Parameters**:
- `provider`: Provider name (e.g., "vertex_ai", "openai")

---

### POST /telemetry/flags/enable-llm/{provider}

Re-enable telemetry for a specific LLM provider.

**Authentication**: Required (Admin)

---

### POST /telemetry/flags/save

Persist current telemetry flags to Redis.

**Authentication**: Required (Admin)

---

### POST /telemetry/flags/load

Load telemetry flags from Redis.

**Authentication**: Required (Admin)

---

### DELETE /telemetry/flags/saved

Delete persisted telemetry flags from Redis.

**Authentication**: Required (Admin)

---

## 2. API Metrics Endpoints

### GET /telemetry/metrics

Get API telemetry metrics.

**Authentication**: None (public)

**Query Parameters**:
| Parameter | Type | Description |
|-----------|------|-------------|
| `api` | string | Filter by API name (optional) |

**Response**:
```json
{
  "summary": {
    "apis_tracked": 15,
    "total_requests": 125000,
    "total_errors": 1250,
    "error_rate": 0.01,
    "avg_latency_ms": 245,
    "total_cost_usd": 125.50
  },
  "apis": {
    "coingecko": {
      "total_requests": 50000,
      "successful_requests": 49500,
      "failed_requests": 500,
      "cache_hits": 25000,
      "avg_latency_ms": 150,
      "p95_latency_ms": 350,
      "p99_latency_ms": 500
    }
  }
}
```

---

### GET /telemetry/prometheus

Get metrics in Prometheus/OpenMetrics format.

**Authentication**: None (public)

**Response**: `text/plain`
```
# HELP anvil_api_requests_total Total API requests
# TYPE anvil_api_requests_total counter
anvil_api_requests_total{api="coingecko",status="success"} 49500
anvil_api_requests_total{api="coingecko",status="error"} 500
# HELP anvil_api_request_duration_seconds Request duration
# TYPE anvil_api_request_duration_seconds histogram
...
```

---

### GET /telemetry/traces

Get recent distributed traces.

**Authentication**: None (public)

**Query Parameters**:
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `limit` | int | 20 | Maximum traces (1-100) |

**Response**:
```json
[
  {
    "trace_id": "abc123",
    "root_span": "POST /api/v1/chat/message",
    "duration_ms": 1250,
    "status": "success",
    "span_count": 15,
    "timestamp": "2026-01-25T12:00:00Z"
  }
]
```

---

### GET /telemetry/traces/{trace_id}

Get detailed spans for a specific trace.

**Authentication**: None (public)

**Response**:
```json
[
  {
    "span_id": "span123",
    "parent_span_id": null,
    "name": "POST /api/v1/chat/message",
    "kind": "SERVER",
    "start_time": "2026-01-25T12:00:00.000Z",
    "end_time": "2026-01-25T12:00:01.250Z",
    "duration_ms": 1250,
    "attributes": {},
    "events": []
  }
]
```

---

### GET /telemetry/slow-calls

Get slowest API calls.

**Authentication**: None (public)

**Query Parameters**:
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `threshold_ms` | float | 1000 | Minimum latency |
| `limit` | int | 10 | Maximum calls (1-100) |

---

### GET /telemetry/slow-traces

Get slowest traces.

**Authentication**: None (public)

**Query Parameters**:
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `threshold_ms` | float | 1000 | Minimum latency |
| `limit` | int | 10 | Maximum traces (1-100) |

---

### GET /telemetry/errors

Get recent API errors.

**Authentication**: None (public)

**Query Parameters**:
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `api` | string | - | Filter by API (optional) |
| `limit` | int | 20 | Maximum errors (1-100) |

---

### GET /telemetry/health

Get telemetry system health.

**Authentication**: None (public)

**Response**:
```json
{
  "status": "healthy",
  "components": {
    "api_telemetry": {
      "status": "active",
      "apis_tracked": 15,
      "total_requests": 125000
    },
    "tracing": {
      "status": "active",
      "recent_traces": 10
    }
  },
  "summary": {...}
}
```

---

### POST /telemetry/reset

Reset telemetry metrics.

**Authentication**: Required (Admin)

**Query Parameters**:
| Parameter | Type | Description |
|-----------|------|-------------|
| `api` | string | API to reset (all if not specified) |

---

## 3. LLM Telemetry Endpoints

### GET /telemetry/llm/metrics

Get LLM provider telemetry metrics.

**Authentication**: None (public)

**Query Parameters**:
| Parameter | Type | Description |
|-----------|------|-------------|
| `provider` | string | Filter by provider (optional) |

**Response**:
```json
{
  "total_calls": 45000,
  "total_cost_usd": 125.50,
  "total_tokens": 15000000,
  "success_rate": 0.98,
  "monthly_cost_usd": 2500.00,
  "monthly_budget_usd": 10000.00,
  "budget_used_percent": 25.0,
  "provider_count": 3,
  "providers": {
    "vertex_ai": {
      "provider": "vertex_ai",
      "total_calls": 30000,
      "successful_calls": 29700,
      "failed_calls": 300,
      "rate_limited_calls": 50,
      "total_input_tokens": 10000000,
      "total_output_tokens": 5000000,
      "total_cost_usd": 75.00,
      "success_rate": 0.99,
      "avg_latency_ms": 1100,
      "p50_latency_ms": 900,
      "p90_latency_ms": 1500,
      "p99_latency_ms": 2500
    }
  }
}
```

---

### GET /telemetry/llm/costs

Get LLM cost breakdown.

**Authentication**: None (public)

**Response**:
```json
{
  "monthly_total_usd": 2500.00,
  "monthly_budget_usd": 10000.00,
  "budget_remaining_usd": 7500.00,
  "by_provider": {
    "vertex_ai": 1500.00,
    "deepinfra": 800.00,
    "bedrock": 200.00
  },
  "by_model": {
    "gemini-1.5-pro": 1200.00,
    "meta-llama/Meta-Llama-3.1-70B-Instruct": 800.00,
    "gemini-2.0-flash": 300.00
  }
}
```

---

### GET /telemetry/llm/models

Get LLM model usage statistics.

**Authentication**: None (public)

**Response**:
```json
{
  "gemini-1.5-pro": {
    "providers": ["vertex_ai"],
    "calls": 25000,
    "input_tokens": 8000000,
    "output_tokens": 4000000,
    "cost_usd": 1200.00
  }
}
```

---

### GET /telemetry/llm/alerts

Get LLM telemetry alerts.

**Authentication**: None (public)

**Query Parameters**:
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `severity` | string | - | Filter by severity (info, warning, error, critical) |
| `hours` | int | 24 | Look back period (1-168) |

**Response**:
```json
[
  {
    "alert_id": "uuid",
    "severity": "warning",
    "provider": "vertex_ai",
    "message": "High error rate for vertex_ai: 5.2%",
    "details": {
      "error_rate": 0.052,
      "threshold": 0.05
    },
    "timestamp": "2026-01-25T12:00:00Z"
  }
]
```

---

### GET /telemetry/llm/providers

Get list of tracked LLM providers with basic metrics.

**Authentication**: None (public)

---

### POST /telemetry/llm/reset

Reset LLM telemetry metrics.

**Authentication**: Required (Admin)

---

## 4. Database Telemetry Endpoints

### GET /telemetry/db/metrics

Get database query telemetry metrics.

**Authentication**: None (public)

**Response**:
```json
{
  "total_queries": 500000,
  "successful_queries": 499000,
  "failed_queries": 1000,
  "success_rate": 0.998,
  "avg_duration_ms": 5.2,
  "p95_duration_ms": 15.0,
  "p99_duration_ms": 50.0,
  "queries_by_type": {
    "SELECT": 400000,
    "INSERT": 80000,
    "UPDATE": 15000,
    "DELETE": 5000
  },
  "slow_query_count": 150
}
```

---

### GET /telemetry/db/slow-queries

Get slow database queries.

**Authentication**: None (public)

**Query Parameters**:
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `threshold_ms` | float | 100 | Minimum latency |
| `limit` | int | 10 | Maximum queries (1-100) |

**Response**:
```json
[
  {
    "query": "SELECT * FROM users WHERE...",
    "query_type": "SELECT",
    "duration_ms": 250,
    "tables": ["users"],
    "row_count": 1000,
    "error_message": null,
    "timestamp": "2026-01-25T12:00:00Z"
  }
]
```

---

### GET /telemetry/db/patterns

Get database query patterns.

**Authentication**: None (public)

**Query Parameters**:
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `order_by` | string | execution_count | Order by metric |
| `limit` | int | 20 | Maximum patterns (1-100) |

---

### GET /telemetry/db/pool

Get database connection pool statistics.

**Authentication**: None (public)

**Response**:
```json
{
  "pool_size": 20,
  "overflow": 10,
  "checked_out": 5,
  "checked_in": 15,
  "checkout_count": 50000,
  "checkin_count": 49995,
  "connect_count": 100,
  "disconnect_count": 80
}
```

---

### GET /telemetry/db/tables/{table}

Get query statistics for a specific table.

**Authentication**: None (public)

---

### GET /telemetry/db/errors

Get recent database query errors.

**Authentication**: None (public)

**Query Parameters**:
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `limit` | int | 20 | Maximum errors (1-100) |

---

### GET /telemetry/db/summary

Get comprehensive database telemetry summary.

**Authentication**: None (public)

---

### POST /telemetry/db/reset

Reset database telemetry metrics.

**Authentication**: Required (Admin)

---

## 5. Monitoring Endpoints

**Base Path**: `/api/v1/monitoring`

### GET /monitoring/health

System health check endpoint.

**Response**:
```json
{
  "status": "healthy",
  "timestamp": "2026-01-25T12:00:00Z",
  "checks": {
    "database": "healthy",
    "redis": "healthy",
    "llm_providers": "healthy"
  }
}
```

---

### GET /monitoring/metrics

Get system metrics in Prometheus format.

---

## 6. API Client Examples

### Get LLM Metrics
```bash
curl -X GET "http://localhost:8000/api/v1/telemetry/llm/metrics"
```

### Get Cost Breakdown
```bash
curl -X GET "http://localhost:8000/api/v1/telemetry/llm/costs"
```

### Get LLM Alerts
```bash
curl -X GET "http://localhost:8000/api/v1/telemetry/llm/alerts?severity=warning&hours=24"
```

### Update Feature Flags (Admin)
```bash
curl -X PUT "http://localhost:8000/api/v1/telemetry/flags?llm_telemetry_enabled=true&llm_sample_rate=0.5" \
  -H "Authorization: Bearer $ADMIN_TOKEN"
```

### Reset LLM Telemetry (Admin)
```bash
curl -X POST "http://localhost:8000/api/v1/telemetry/llm/reset" \
  -H "Authorization: Bearer $ADMIN_TOKEN"
```

### Get Prometheus Metrics
```bash
curl -X GET "http://localhost:8000/api/v1/telemetry/prometheus"
```

---

## References

- **Telemetry Router**: `src/app/presentation/http/controllers/telemetry/router.py`
- **Monitoring Router**: `src/app/presentation/http/controllers/monitoring/router.py`
- **LLM Telemetry**: `src/app/infrastructure/telemetry/llm_telemetry.py`
- **API Telemetry**: `src/app/infrastructure/telemetry/api_telemetry.py`
- **DB Telemetry**: `src/app/infrastructure/telemetry/db_telemetry.py`
