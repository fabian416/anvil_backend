# LLM Orchestration System Endpoints Specification

> **Last Updated**: 2026-01-25  
> **Status**: Production  
> **Maintainers**: @backend-engineer @error-detective @code-reviewer

---

## Executive Summary

The LLM Orchestration System provides comprehensive APIs for:
1. **Admin Dashboard** - System health, metrics, real-time monitoring
2. **Model Ranking** - Adaptive model selection and management
3. **Provider Management** - LLM provider configuration
4. **Telemetry** - Metrics, cost analysis, performance tracking
5. **Circuit Breakers** - Fault tolerance management
6. **Budget Management** - Cost control and alerts

**Base Path**: `/api/v1/admin/llm`  
**Authentication**: Admin Bearer Token (all endpoints)

---

## 1. Dashboard Endpoints

**Base Path**: `/api/v1/admin/llm/dashboard`  
**Tags**: `Admin - Dashboard`

### GET /dashboard

Get complete dashboard data optimized for UI rendering.

**Query Parameters**:
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `period` | string | 24h | Time period (1h, 24h, 7d, 30d) |

**Response**:
```json
{
  "success": true,
  "data": {
    "system_health": {...},
    "providers": [...],
    "top_models": [...],
    "metrics_summary": {...},
    "cost_summary": {...},
    "recent_requests": [...],
    "active_alerts": [...],
    "last_updated": "2026-01-25T12:00:00Z"
  }
}
```

---

### WebSocket /dashboard/ws

Real-time updates via WebSocket.

**Message Types**:
- `connection` - Connection status
- `heartbeat` - Keep-alive (every 30s)
- `request_update` - New request telemetry
- `alert` - Budget/circuit breaker alerts
- `metrics_update` - Metric updates

**Usage**:
```javascript
const ws = new WebSocket('ws://localhost:8000/api/v1/admin/llm/dashboard/ws');
ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  // data.type: 'request_update', 'alert', 'metrics_update'
};
```

---

### POST /dashboard/export

Export dashboard data in CSV or PDF format.

**Request Body**:
```json
{
  "format": "csv",
  "data_type": "requests",
  "period": "30d",
  "filters": {
    "provider": "vertex_ai",
    "agent_type": "swap_agent"
  }
}
```

---

### GET /dashboard/health

Dashboard health check (no authentication required).

**Response**:
```json
{
  "success": true,
  "data": {
    "status": "healthy",
    "components": {
      "database": "healthy",
      "cache": "healthy",
      "websocket": "healthy"
    }
  }
}
```

---

## 2. Model Ranking Endpoints

**Base Path**: `/api/v1/admin/llm/rankings`  
**Tags**: `Admin - LLM Ranking`

### GET /rankings

Get overview of all agent types with their top models.

**Response**:
```json
{
  "total_agent_types": 10,
  "agent_types": [
    {
      "agent_type": "swap_agent",
      "total_models": 5,
      "top_model": "gemini-1.5-pro",
      "top_model_score": 0.95,
      "last_recalculated_at": "2026-01-25T10:00:00Z"
    }
  ]
}
```

---

### GET /rankings/{agent_type}

Get detailed rankings for a specific agent type.

**Path Parameters**:
| Parameter | Type | Description |
|-----------|------|-------------|
| `agent_type` | string | Agent type (e.g., swap_agent, chat_agent) |

**Response**:
```json
{
  "agent_type": "swap_agent",
  "total_models": 5,
  "models": [
    {
      "model_id": "uuid",
      "model_name": "gemini-1.5-pro",
      "provider_name": "vertex_ai",
      "display_name": "Gemini 1.5 Pro",
      "ranking_score": 0.95,
      "position": 1,
      "success_rate": 0.99,
      "avg_latency_ms": 1200,
      "avg_cost_per_request": 0.002,
      "total_requests": 50000,
      "successful_requests": 49500,
      "failed_requests": 500,
      "last_used_at": "2026-01-25T11:30:00Z",
      "has_override": false,
      "override_reason": null
    }
  ],
  "last_recalculated_at": "2026-01-25T10:00:00Z"
}
```

---

### POST /rankings/{agent_type}/recalculate

Manually trigger ranking recalculation.

**Response**:
```json
{
  "agent_type": "swap_agent",
  "models_evaluated": 5,
  "models_updated": 3,
  "changes_made": 2,
  "recalculated_at": "2026-01-25T12:00:00Z",
  "success": true,
  "message": "Recalculated 3 models"
}
```

---

### PUT /rankings/{agent_type}/{model_id}/override

Set manual ranking override.

**Request Body**:
```json
{
  "override_score": 1.0,
  "reason": "Testing new model",
  "expires_in_hours": 24
}
```

---

### DELETE /rankings/{agent_type}/{model_id}/override

Remove manual ranking override.

---

### POST /rankings/models/register/vertex-ai

Register new Vertex AI model.

**Request Body**:
```json
{
  "model_id": "gemini-2.0-flash",
  "display_name": "Gemini 2.0 Flash",
  "description": "Fast, cost-effective model",
  "context_window": 1000000,
  "input_cost_per_1k": 0.00015,
  "output_cost_per_1k": 0.0006,
  "max_output_tokens": 8192,
  "supports_streaming": true,
  "agent_types": ["swap_agent", "chat_agent"]
}
```

---

### POST /rankings/models/register/deepinfra

Register new DeepInfra model.

---

## 3. Provider Endpoints

**Base Path**: `/api/v1/admin/llm/providers`  
**Tags**: `Admin - LLM Providers`

### GET /providers

List all configured LLM providers.

**Response**:
```json
{
  "providers": [
    {
      "name": "vertex_ai",
      "display_name": "Google Vertex AI",
      "status": "healthy",
      "models_count": 5,
      "requests_24h": 25000,
      "success_rate": 0.99
    },
    {
      "name": "deepinfra",
      "display_name": "DeepInfra",
      "status": "healthy",
      "models_count": 3,
      "requests_24h": 10000,
      "success_rate": 0.98
    },
    {
      "name": "bedrock",
      "display_name": "AWS Bedrock",
      "status": "healthy",
      "models_count": 4,
      "requests_24h": 5000,
      "success_rate": 0.99
    }
  ]
}
```

---

### GET /providers/{provider_name}

Get detailed provider information.

---

### PUT /providers/{provider_name}/config

Update provider configuration.

---

## 4. Model Endpoints

**Base Path**: `/api/v1/admin/llm/models`  
**Tags**: `Admin - LLM Models`

### GET /models

List all registered models.

---

### GET /models/{model_id}

Get detailed model information.

---

### PUT /models/{model_id}

Update model configuration.

---

### DELETE /models/{model_id}

Deactivate model.

---

## 5. Telemetry Endpoints

**Base Path**: `/api/v1/admin/llm/telemetry`  
**Tags**: `Admin - LLM Telemetry`

### GET /telemetry/overview

High-level telemetry summary.

**Query Parameters**:
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `period` | string | 24h | Time period (1h, 24h, 7d, 30d) |

**Response**:
```json
{
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
    "requests_by_provider": [...],
    "requests_by_agent": [...],
    "retry_rate": 0.032,
    "circuit_breakers_open": 0
  }
}
```

---

### GET /telemetry/timeseries

Time-series metrics for charts.

**Query Parameters**:
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `metric` | string | requests | Metric type (requests, latency, cost, errors, tokens) |
| `period` | string | 24h | Time period |
| `group_by` | string | provider | Group by (provider, model, agent) |
| `interval` | string | auto | Interval (auto, 5m, 1h, 1d) |

---

### GET /telemetry/cost

Cost analysis and projections.

**Response**:
```json
{
  "data": {
    "period": "30d",
    "total_cost_usd": 2847.50,
    "cost_by_provider": [...],
    "cost_by_agent": [...],
    "cost_by_model": [...],
    "daily_trend": [...],
    "projected_monthly_cost": 3150.00,
    "budget_status": {
      "monthly_budget": 10000.00,
      "current_spend": 2847.50,
      "percentage_used": 28.5
    }
  }
}
```

---

## 6. Circuit Breaker Endpoints

**Base Path**: `/api/v1/admin/llm/circuit-breakers`  
**Tags**: `Admin - Circuit Breakers`

### GET /circuit-breakers

List all circuit breaker states.

**Response**:
```json
{
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
        "last_failure_at": "2026-01-25T09:30:00Z",
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

---

### POST /circuit-breakers/{breaker_id}/reset

Manually reset circuit breaker to closed state.

---

## 7. Budget Endpoints

**Base Path**: `/api/v1/admin/llm/budgets`  
**Tags**: `Admin - LLM Budgets`

### GET /budgets

List all budget configurations.

---

### POST /budgets

Create new budget.

---

### PUT /budgets/{budget_id}

Update budget configuration.

---

### GET /budgets/alerts

Get active budget alerts.

---

## 8. Error Handling

### Standard Error Response

```json
{
  "detail": "Error message",
  "status_code": 500
}
```

### Error Codes

| HTTP Status | Description |
|-------------|-------------|
| 400 | Invalid request parameters |
| 401 | Authentication required |
| 403 | Insufficient permissions |
| 404 | Resource not found |
| 500 | Internal server error |
| 502 | LLM provider unavailable |

---

## 9. API Client Examples

### Get Dashboard Data
```bash
curl -X GET "http://localhost:8000/api/v1/admin/llm/dashboard?period=24h" \
  -H "Authorization: Bearer $ADMIN_TOKEN"
```

### Get Agent Rankings
```bash
curl -X GET "http://localhost:8000/api/v1/admin/llm/rankings/swap_agent" \
  -H "Authorization: Bearer $ADMIN_TOKEN"
```

### Recalculate Rankings
```bash
curl -X POST "http://localhost:8000/api/v1/admin/llm/rankings/swap_agent/recalculate" \
  -H "Authorization: Bearer $ADMIN_TOKEN"
```

### Register New Model
```bash
curl -X POST "http://localhost:8000/api/v1/admin/llm/rankings/models/register/vertex-ai" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "model_id": "gemini-2.0-flash",
    "display_name": "Gemini 2.0 Flash",
    "context_window": 1000000,
    "input_cost_per_1k": 0.00015,
    "output_cost_per_1k": 0.0006,
    "agent_types": ["swap_agent", "chat_agent"]
  }'
```

### Reset Circuit Breaker
```bash
curl -X POST "http://localhost:8000/api/v1/admin/llm/circuit-breakers/{uuid}/reset" \
  -H "Authorization: Bearer $ADMIN_TOKEN"
```

---

## References

- **Main Router**: `src/app/presentation/http/controllers/admin/llm/router.py`
- **Dashboard**: `src/app/presentation/http/controllers/admin/llm/dashboard.py`
- **Rankings**: `src/app/presentation/http/controllers/admin/llm/ranking_router.py`
- **Telemetry**: `src/app/presentation/http/controllers/admin/llm/telemetry.py`
- **Circuit Breakers**: `src/app/presentation/http/controllers/admin/llm/circuit_breakers.py`
- **Budgets**: `src/app/presentation/http/controllers/admin/llm/budgets.py`
