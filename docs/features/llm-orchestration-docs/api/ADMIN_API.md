# Admin API Documentation

## Overview

The Admin API provides comprehensive control over the LLM orchestration system for administrators and business stakeholders.

---

## Authentication

All admin endpoints require JWT authentication with appropriate permissions.

```http
Authorization: Bearer <admin_jwt_token>
```

### Permissions

| Permission | Description |
|------------|-------------|
| `llm.read` | View providers, models, rankings, telemetry |
| `llm.config.read` | View business configuration |
| `llm.config.write` | Modify configuration, budgets |
| `llm.admin` | Full administrative access |

---

## Provider Management

### GET /admin/llm/providers

List all LLM providers with status.

**Permission**: `llm.read`

**Response**:
```json
{
  "success": true,
  "data": {
    "providers": [
      {
        "id": "uuid",
        "name": "vertex_ai",
        "display_name": "Google Vertex AI",
        "priority": 1,
        "is_enabled": true,
        "health_status": "healthy",
        "last_health_check": "2025-12-01T10:00:00Z",
        "model_count": 3,
        "enabled_model_count": 3,
        "circuit_breaker_state": "closed"
      },
      {
        "id": "uuid",
        "name": "deepinfra",
        "display_name": "DeepInfra",
        "priority": 2,
        "is_enabled": true,
        "health_status": "healthy",
        "last_health_check": "2025-12-01T10:00:00Z",
        "model_count": 3,
        "enabled_model_count": 3,
        "circuit_breaker_state": "closed"
      }
    ],
    "health_summary": {
      "healthy": 3,
      "degraded": 0,
      "down": 0
    }
  }
}
```

### PUT /admin/llm/providers/{id}

Update provider configuration.

**Permission**: `llm.config.write`

**Request**:
```json
{
  "is_enabled": true,
  "priority": 2,
  "config": {
    "region": "us-west1"
  }
}
```

**Response**:
```json
{
  "success": true,
  "data": {
    "provider_id": "uuid",
    "updated_fields": ["priority", "config"],
    "audit_id": "uuid"
  }
}
```

### POST /admin/llm/providers/{id}/health-check

Trigger manual health check.

**Permission**: `llm.admin`

**Response**:
```json
{
  "success": true,
  "data": {
    "provider_id": "uuid",
    "status": "healthy",
    "latency_ms": 145,
    "checked_at": "2025-12-01T10:30:00Z",
    "models_tested": 3,
    "models_healthy": 3
  }
}
```

---

## Model Management

### GET /admin/llm/models

List all models across providers.

**Permission**: `llm.read`

**Query Parameters**:
- `provider_id`: Filter by provider
- `is_enabled`: Filter by enabled status
- `tier`: Filter by tier (premium, standard, economy)

**Response**:
```json
{
  "success": true,
  "data": {
    "models": [
      {
        "id": "uuid",
        "provider_id": "uuid",
        "provider_name": "vertex_ai",
        "model_id": "gemini-1.5-pro",
        "display_name": "Gemini 1.5 Pro",
        "model_family": "gemini",
        "capabilities": ["chat", "code", "vision", "function_calling"],
        "context_window": 1000000,
        "cost_per_1k_input": 0.00125,
        "cost_per_1k_output": 0.00375,
        "carousel_position": 1,
        "tier": "premium",
        "is_enabled": true,
        "circuit_breaker_state": "closed"
      }
    ],
    "total": 9
  }
}
```

### PUT /admin/llm/models/{id}

Update model configuration.

**Permission**: `llm.config.write`

**Request**:
```json
{
  "is_enabled": true,
  "carousel_position": 2,
  "cost_per_1k_input": 0.0015,
  "cost_per_1k_output": 0.004
}
```

### GET /admin/llm/models/{id}/performance

Get detailed model performance metrics.

**Permission**: `llm.read`

**Query Parameters**:
- `period`: 24h, 7d, 30d
- `agent_type`: Filter by agent (optional)

**Response**:
```json
{
  "success": true,
  "data": {
    "model_id": "uuid",
    "period": "7d",
    "metrics": {
      "total_requests": 15000,
      "successful_requests": 14700,
      "failed_requests": 300,
      "success_rate": 0.98,
      "avg_latency_ms": 1245,
      "p50_latency_ms": 980,
      "p95_latency_ms": 2500,
      "p99_latency_ms": 4200,
      "total_input_tokens": 5000000,
      "total_output_tokens": 2500000,
      "total_cost_usd": 125.50,
      "avg_cost_per_request": 0.0084
    },
    "by_agent": [
      {
        "agent_type": "swap_agent",
        "requests": 8000,
        "success_rate": 0.985,
        "avg_latency_ms": 1100
      }
    ],
    "trend": {
      "success_rate_change": 0.02,
      "latency_change": -150,
      "direction": "improving"
    }
  }
}
```

---

## Ranking Management

### GET /admin/llm/rankings

View current rankings per agent.

**Permission**: `llm.read`

**Query Parameters**:
- `agent_type`: Filter by agent type

**Response**:
```json
{
  "success": true,
  "data": {
    "rankings": [
      {
        "agent_type": "swap_agent",
        "models": [
          {
            "rank": 1,
            "model_id": "uuid",
            "model_name": "gemini-1.5-pro",
            "provider": "vertex_ai",
            "ranking_score": 0.8945,
            "success_rate": 0.985,
            "avg_latency_ms": 1100,
            "avg_cost_per_request": 0.0072,
            "total_requests": 8000,
            "has_override": false
          },
          {
            "rank": 2,
            "model_id": "uuid",
            "model_name": "claude-3-5-sonnet",
            "provider": "bedrock",
            "ranking_score": 0.8721,
            "success_rate": 0.978,
            "avg_latency_ms": 1350,
            "avg_cost_per_request": 0.0095,
            "total_requests": 5000,
            "has_override": false
          }
        ]
      }
    ],
    "last_recalculated_at": "2025-12-01T09:00:00Z"
  }
}
```

### PUT /admin/llm/rankings/weights

Update ranking weight profiles.

**Permission**: `llm.config.write`

**Request**:
```json
{
  "agent_type": "swap_agent",
  "weights": {
    "success_weight": 0.55,
    "latency_weight": 0.30,
    "cost_weight": 0.10,
    "recency_weight": 0.05
  }
}
```

### POST /admin/llm/rankings/recalculate

Force ranking recalculation.

**Permission**: `llm.admin`

**Request**:
```json
{
  "agent_type": "swap_agent"
}
```

**Response**:
```json
{
  "success": true,
  "data": {
    "recalculated_count": 9,
    "agent_types_affected": ["swap_agent"],
    "duration_ms": 150
  }
}
```

### POST /admin/llm/rankings/override

Manually set model priority for agent.

**Permission**: `llm.admin`

**Request**:
```json
{
  "agent_type": "swap_agent",
  "model_id": "uuid",
  "override_score": 0.95,
  "reason": "Testing new model performance",
  "expires_at": "2025-12-08T00:00:00Z"
}
```

---

## Request Monitoring

### GET /admin/llm/requests

List LLM requests with filters.

**Permission**: `llm.read`

**Query Parameters**:
- `status`: pending, completed, failed, etc.
- `agent_type`: Filter by agent
- `provider_id`: Filter by provider
- `model_id`: Filter by model
- `user_id`: Filter by user
- `from_date`, `to_date`: Date range
- `min_latency_ms`, `max_latency_ms`: Latency filter
- `min_cost`, `max_cost`: Cost filter
- `limit`, `offset`: Pagination

**Response**:
```json
{
  "success": true,
  "data": {
    "requests": [
      {
        "id": "uuid",
        "request_id": "req_abc123",
        "user_id": "uuid",
        "agent_type": "swap_agent",
        "status": "completed",
        "selected_model": "gemini-1.5-pro",
        "selected_provider": "vertex_ai",
        "attempt_count": 1,
        "total_latency_ms": 1234,
        "input_tokens": 500,
        "output_tokens": 800,
        "actual_cost_usd": 0.0065,
        "created_at": "2025-12-01T10:00:00Z",
        "completed_at": "2025-12-01T10:00:01.234Z"
      }
    ],
    "summary": {
      "total": 15000,
      "completed": 14700,
      "failed": 200,
      "timeout": 100,
      "avg_latency_ms": 1245,
      "total_cost_usd": 125.50
    },
    "pagination": {
      "total": 15000,
      "limit": 50,
      "offset": 0,
      "has_more": true
    }
  }
}
```

### GET /admin/llm/requests/{id}

Get request details with full attempt history.

**Permission**: `llm.read`

**Response**:
```json
{
  "success": true,
  "data": {
    "request": {
      "id": "uuid",
      "request_id": "req_abc123",
      "user_id": "uuid",
      "agent_type": "swap_agent",
      "session_id": "uuid",
      "status": "completed",
      "status_history": [
        {"status": "pending", "timestamp": "...", "details": "Request received"},
        {"status": "selecting_model", "timestamp": "...", "details": "Querying rankings"},
        {"status": "executing", "timestamp": "...", "details": "Attempt 1: gemini-1.5-pro"},
        {"status": "completed", "timestamp": "...", "details": "Success"}
      ],
      "selected_provider_id": "uuid",
      "selected_model_id": "uuid",
      "selection_reason": "ranking",
      "input_tokens": 500,
      "output_tokens": 800,
      "total_latency_ms": 1234,
      "actual_cost_usd": 0.0065,
      "created_at": "2025-12-01T10:00:00Z",
      "completed_at": "2025-12-01T10:00:01.234Z"
    },
    "attempts": [
      {
        "attempt_number": 1,
        "provider": "vertex_ai",
        "model": "gemini-1.5-pro",
        "status": "completed",
        "latency_ms": 1234,
        "input_tokens": 500,
        "output_tokens": 800,
        "cost_usd": 0.0065,
        "started_at": "2025-12-01T10:00:00.050Z",
        "completed_at": "2025-12-01T10:00:01.234Z"
      }
    ]
  }
}
```

---

## Telemetry Dashboard

### GET /admin/llm/telemetry/overview

High-level telemetry summary.

**Permission**: `llm.read`

**Query Parameters**:
- `period`: 1h, 24h, 7d, 30d

**Response**:
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
      {"provider": "vertex_ai", "count": 25000, "success_rate": 0.99, "avg_latency_ms": 1100},
      {"provider": "deepinfra", "count": 12000, "success_rate": 0.98, "avg_latency_ms": 1400},
      {"provider": "bedrock", "count": 8231, "success_rate": 0.975, "avg_latency_ms": 1350}
    ],
    "requests_by_agent": [
      {"agent": "swap_agent", "count": 18000, "avg_latency_ms": 1050},
      {"agent": "trading_agent", "count": 12000, "avg_latency_ms": 1200},
      {"agent": "portfolio_agent", "count": 8000, "avg_latency_ms": 1500}
    ],
    "retry_rate": 0.032,
    "circuit_breakers_open": 0
  }
}
```

### GET /admin/llm/telemetry/timeseries

Time-series metrics for charts.

**Permission**: `llm.read`

**Query Parameters**:
- `metric`: requests, latency, cost, errors, tokens
- `period`: 1h, 24h, 7d, 30d
- `group_by`: provider, model, agent
- `interval`: auto, 5m, 1h, 1d

**Response**:
```json
{
  "success": true,
  "data": {
    "metric": "requests",
    "period": "24h",
    "interval": "1h",
    "data": [
      {
        "timestamp": "2025-12-01T00:00:00Z",
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

### GET /admin/llm/telemetry/cost

Cost analysis and projections.

**Permission**: `llm.read`

**Query Parameters**:
- `period`: 7d, 30d, 90d

**Response**:
```json
{
  "success": true,
  "data": {
    "period": "30d",
    "total_cost_usd": 2847.50,
    "cost_by_provider": [
      {"provider": "vertex_ai", "cost": 1200.00, "percentage": 42.1},
      {"provider": "bedrock", "cost": 950.00, "percentage": 33.4},
      {"provider": "deepinfra", "cost": 697.50, "percentage": 24.5}
    ],
    "cost_by_agent": [
      {"agent": "swap_agent", "cost": 1100.00, "requests": 180000},
      {"agent": "trading_agent", "cost": 850.00, "requests": 120000}
    ],
    "cost_by_model": [
      {"model": "gemini-1.5-pro", "cost": 800.00},
      {"model": "claude-3-5-sonnet", "cost": 650.00}
    ],
    "daily_trend": [
      {"date": "2025-11-01", "cost": 85.50},
      {"date": "2025-11-02", "cost": 92.30}
    ],
    "projected_monthly_cost": 3150.00,
    "budget_status": {
      "monthly_budget": 10000.00,
      "current_spend": 2847.50,
      "percentage_used": 28.5,
      "days_remaining": 15
    }
  }
}
```

---

## Budget Management

### GET /admin/llm/budgets

View cost budgets.

**Permission**: `llm.read`

**Response**:
```json
{
  "success": true,
  "data": {
    "budgets": [
      {
        "id": "uuid",
        "name": "Daily Operations",
        "budget_type": "daily",
        "budget_amount_usd": 500.00,
        "current_spend_usd": 127.45,
        "percentage_used": 25.5,
        "warning_threshold_percent": 80,
        "critical_threshold_percent": 95,
        "is_hard_limit": false,
        "period_start": "2025-12-01T00:00:00Z",
        "period_end": "2025-12-02T00:00:00Z"
      }
    ]
  }
}
```

### POST /admin/llm/budgets

Create new budget.

**Permission**: `llm.config.write`

**Request**:
```json
{
  "name": "Weekly API Costs",
  "budget_type": "weekly",
  "budget_amount_usd": 2500.00,
  "warning_threshold_percent": 75,
  "critical_threshold_percent": 90,
  "is_hard_limit": true,
  "notify_emails": ["finance@company.com"],
  "notify_slack_channel": "#llm-alerts"
}
```

---

## Circuit Breaker Management

### GET /admin/llm/circuit-breakers

View circuit breaker states.

**Permission**: `llm.read`

**Response**:
```json
{
  "success": true,
  "data": {
    "circuit_breakers": [
      {
        "id": "uuid",
        "entity_type": "model",
        "entity_id": "uuid",
        "entity_name": "gemini-1.5-pro",
        "state": "closed",
        "failure_count": 2,
        "consecutive_failures": 0,
        "last_failure_at": "2025-12-01T09:30:00Z",
        "config": {
          "failure_threshold": 5,
          "success_threshold": 3,
          "timeout_seconds": 60
        }
      }
    ],
    "summary": {
      "closed": 9,
      "open": 0,
      "half_open": 0
    }
  }
}
```

### POST /admin/llm/circuit-breakers/{id}/reset

Manually reset circuit breaker.

**Permission**: `llm.admin`

**Response**:
```json
{
  "success": true,
  "data": {
    "circuit_breaker_id": "uuid",
    "previous_state": "open",
    "new_state": "closed",
    "reset_at": "2025-12-01T10:30:00Z"
  }
}
```

---

## Health & Diagnostics

### GET /admin/llm/health

Overall system health.

**Permission**: `llm.read`

**Response**:
```json
{
  "success": true,
  "data": {
    "status": "healthy",
    "providers": [
      {"name": "vertex_ai", "status": "healthy", "latency_ms": 45},
      {"name": "deepinfra", "status": "healthy", "latency_ms": 120},
      {"name": "bedrock", "status": "healthy", "latency_ms": 89}
    ],
    "queue_depth": 5,
    "active_requests": 12,
    "circuit_breakers_open": 0,
    "error_rate_1h": 0.013,
    "avg_latency_1h_ms": 1150
  }
}
```

### POST /admin/llm/diagnostics/test

Run diagnostic test.

**Permission**: `llm.admin`

**Request**:
```json
{
  "provider_id": "uuid",
  "model_id": "uuid",
  "test_prompt": "Hello, respond with 'OK'"
}
```

**Response**:
```json
{
  "success": true,
  "data": {
    "results": [
      {
        "provider": "vertex_ai",
        "model": "gemini-1.5-pro",
        "status": "success",
        "latency_ms": 890,
        "response_preview": "OK",
        "tokens": {"input": 8, "output": 2}
      }
    ]
  }
}
```

---

## Error Codes

| Code | HTTP | Description |
|------|------|-------------|
| `LLM_PROVIDER_NOT_FOUND` | 404 | Provider doesn't exist |
| `LLM_MODEL_NOT_FOUND` | 404 | Model doesn't exist |
| `LLM_PERMISSION_DENIED` | 403 | Insufficient permissions |
| `LLM_INVALID_CONFIG` | 400 | Invalid configuration |
| `LLM_BUDGET_EXCEEDED` | 403 | Budget limit reached |
| `LLM_OPERATION_FAILED` | 500 | Operation failed |
