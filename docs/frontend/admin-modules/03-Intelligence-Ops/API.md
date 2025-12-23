# Intelligence Ops API Documentation

> **Complete API Documentation**  
> **Base URLs**: `/api/admin/llm`, `/api/admin/agents`, `/api/admin/distillation`

---

## 🔌 LLM Configuration Endpoints

### Models
- **GET** `/api/admin/llm/models` - List models
- **PUT** `/api/admin/llm/models/{model_id}` - Update model
- **GET** `/api/admin/llm/models/{model_id}/performance` - Get performance

### Budgets
- **GET** `/api/admin/llm/budgets` - List budgets
- **POST** `/api/admin/llm/budgets` - Create budget
- **PUT** `/api/admin/llm/budgets/{budget_id}` - Update budget
- **DELETE** `/api/admin/llm/budgets/{budget_id}` - Delete budget

### Circuit Breakers
- **GET** `/api/admin/llm/circuit-breakers` - List circuit breakers
- **POST** `/api/admin/llm/circuit-breakers/{provider_id}/reset` - Reset circuit breaker

### Rankings
- **GET** `/api/admin/llm/rankings` - Get rankings
- **PUT** `/api/admin/llm/rankings/weights` - Update weights
- **POST** `/api/admin/llm/rankings/recalculate` - Recalculate
- **POST** `/api/admin/llm/rankings/override` - Create override

### Telemetry
- **GET** `/api/admin/llm/telemetry/overview` - Get overview
- **GET** `/api/admin/llm/telemetry/timeseries` - Get time-series
- **GET** `/api/admin/llm/telemetry/cost` - Get cost analysis

---

## 🤖 Agent Management Endpoints

- **GET** `/api/admin/agents/` - List agents

---

## 🧪 Distillation Endpoints

### Static Responses
- **POST** `/api/admin/distillation/static-responses` - Create
- **GET** `/api/admin/distillation/static-responses` - List
- **PATCH** `/api/admin/distillation/static-responses/{response_id}` - Update
- **DELETE** `/api/admin/distillation/static-responses/{response_id}` - Delete

### Configuration
- **GET** `/api/admin/distillation/config` - Get config
- **PATCH** `/api/admin/distillation/config` - Update config

### Cache
- **POST** `/api/admin/distillation/cache/invalidate` - Invalidate
- **GET** `/api/admin/distillation/cache/stats` - Get stats

### Telemetry
- **GET** `/api/admin/distillation/telemetry/requests` - Get requests
- **GET** `/api/admin/distillation/telemetry/summary` - Get summary

### Validation
- **GET** `/api/admin/distillation/validation/responses` - List responses
- **GET** `/api/admin/distillation/validation/responses/{response_id}` - Get response
- **PATCH** `/api/admin/distillation/validation/responses/{response_id}/approve` - Approve
- **PATCH** `/api/admin/distillation/validation/responses/{response_id}/reject` - Reject
- **GET** `/api/admin/distillation/validation/analytics` - Get analytics

---

## ⚠️ Error Handling

| Status | Error Code | Description |
|--------|------------|-------------|
| `401` | `AuthenticationError` | Not authenticated |
| `403` | `AuthorizationError` | Not authorized |
| `404` | `NotFoundError` | Resource not found |
| `503` | `DataMapperError` | Service unavailable |

---

## 🔐 Authentication

All endpoints require admin authentication with Bearer token.
