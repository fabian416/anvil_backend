# Intelligence Ops API Documentation

> **Complete API Documentation**  
> **Methodology**: CTO Engineering Framework (First Principles + Design Thinking + Systems Thinking)  
> **Base URLs**: `/api/admin/llm`, `/api/admin/agents`, `/api/admin/distillation`

---

## 📋 Table of Contents

1. [LLM Configuration Endpoints](#llm-configuration-endpoints)
2. [Budget Management Endpoints](#budget-management-endpoints)
3. [Circuit Breaker Endpoints](#circuit-breaker-endpoints)
4. [Ranking Management Endpoints](#ranking-management-endpoints)
5. [Telemetry Endpoints](#telemetry-endpoints)
6. [Agent Management Endpoints](#agent-management-endpoints)
7. [Distillation Management Endpoints](#distillation-management-endpoints)
8. [Distillation Validation Endpoints](#distillation-validation-endpoints)
9. [Request/Response Schemas](#requestresponse-schemas)
10. [Error Handling](#error-handling)
11. [WebSocket Connections](#websocket-connections)
12. [API Design Trade-off Analysis](#api-design-trade-off-analysis)

---

## 🔌 LLM Configuration Endpoints

### 1. List Models

**Method**: `GET`  
**Endpoint**: `/api/admin/llm/models`  
**Auth Required**: Yes (Bearer Token - Admin Only)

#### Request

##### Query Parameters
| Parameter | Type | Required | Description | Default |
|----------|------|----------|-------------|---------|
| `provider_id` | `UUID` | No | Filter by provider | All providers |
| `is_enabled` | `boolean` | No | Filter by enabled status | All models |
| `tier` | `string` | No | Filter by tier | All tiers |

**Valid `tier` Values**: `premium`, `standard`, `economy`

#### Response

##### Success Response (200 OK)
```typescript
interface ModelListResponse {
  success: boolean;
  data: {
    models: Model[];
    total: number;
  };
}

interface Model {
  id: string;                            // UUID
  provider_id: string;                   // UUID
  provider_name: string;
  model_id: string;
  display_name: string;
  model_family: string;
  capabilities: string[];
  context_window: number;
  cost_per_1k_input: number;             // Decimal
  cost_per_1k_output: number;            // Decimal
  carousel_position: number;
  tier: string;
  is_enabled: boolean;
  circuit_breaker_state: string | null;  // "closed" | "open" | "half_open"
}
```

**JSON Example**:
```json
{
  "success": true,
  "data": {
    "models": [
      {
        "id": "550e8400-e29b-41d4-a716-446655440000",
        "provider_id": "660e8400-e29b-41d4-a716-446655440001",
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
    "total": 12
  }
}
```

---

### 2. Update Model

**Method**: `PUT`  
**Endpoint**: `/api/admin/llm/models/{model_id}`  
**Auth Required**: Yes (Bearer Token - Admin Only)

#### Request

##### Path Parameters
| Parameter | Type | Required | Description |
|----------|------|----------|-------------|
| `model_id` | `UUID` | **Yes** | Model identifier |

##### Request Body
```typescript
interface UpdateModelRequest {
  is_enabled?: boolean;
  carousel_position?: number;
  cost_per_1k_input?: number;           // Decimal
  cost_per_1k_output?: number;          // Decimal
}
```

**JSON Example**:
```json
{
  "is_enabled": true,
  "carousel_position": 2,
  "cost_per_1k_input": 0.00125,
  "cost_per_1k_output": 0.00375
}
```

#### Response

##### Success Response (200 OK)
```typescript
interface ModelListResponse {
  success: boolean;
  data: {
    model_id: string;
    updated: boolean;
  };
}
```

---

### 3. Get Model Performance

**Method**: `GET`  
**Endpoint**: `/api/admin/llm/models/{model_id}/performance`  
**Auth Required**: Yes (Bearer Token - Admin Only)

#### Request

##### Path Parameters
| Parameter | Type | Required | Description |
|----------|------|----------|-------------|
| `model_id` | `UUID` | **Yes** | Model identifier |

##### Query Parameters
| Parameter | Type | Required | Description | Default |
|----------|------|----------|-------------|---------|
| `period` | `string` | No | Time period | `24h` |
| `agent_type` | `string` | No | Filter by agent | All agents |

**Valid `period` Values**: `24h`, `7d`, `30d`

#### Response

##### Success Response (200 OK)
```typescript
interface ModelPerformanceResponse {
  success: boolean;
  data: {
    model_id: string;
    period: string;
    metrics: {
      total_requests: number;
      successful_requests: number;
      failed_requests: number;
      success_rate: number;              // 0-1
      avg_latency_ms: number;
      p50_latency_ms: number;
      p95_latency_ms: number;
      p99_latency_ms: number;
      total_cost_usd: number;
    };
  };
}
```

---

## 💰 Budget Management Endpoints

### 4. List Budgets

**Method**: `GET`  
**Endpoint**: `/api/admin/llm/budgets`  
**Auth Required**: Yes (Bearer Token - Admin Only)

#### Response

##### Success Response (200 OK)
```typescript
interface BudgetResponse {
  success: boolean;
  data: {
    budgets: Budget[];
  };
}

interface Budget {
  id: string;                             // UUID
  name: string;
  budget_type: 'daily' | 'weekly' | 'monthly';
  budget_amount_usd: number;              // Decimal
  current_spend_usd: number;              // Decimal
  percentage_used: number;                // 0-100
  warning_threshold_percent: number;      // 0-100
  critical_threshold_percent: number;    // 0-100
  is_hard_limit: boolean;
  period_start: string;                   // ISO 8601
  period_end: string;                    // ISO 8601
}
```

---

### 5. Create Budget

**Method**: `POST`  
**Endpoint**: `/api/admin/llm/budgets`  
**Auth Required**: Yes (Bearer Token - Admin Only)

#### Request

##### Request Body
```typescript
interface CreateBudgetRequest {
  name: string;
  budget_type: 'daily' | 'weekly' | 'monthly';
  budget_amount_usd: number;             // Decimal
  warning_threshold_percent?: number;    // 0-100, default: 80
  critical_threshold_percent?: number;  // 0-100, default: 95
  is_hard_limit?: boolean;               // default: false
  notify_emails?: string[];
  notify_slack_channel?: string;
}
```

**JSON Example**:
```json
{
  "name": "Daily Operations",
  "budget_type": "daily",
  "budget_amount_usd": 500.00,
  "warning_threshold_percent": 80,
  "critical_threshold_percent": 95,
  "is_hard_limit": false,
  "notify_emails": ["admin@example.com"],
  "notify_slack_channel": "#alerts"
}
```

#### Response

##### Success Response (201 Created)
```typescript
interface BudgetResponse {
  success: boolean;
  data: {
    budget_id: string;                   // UUID
    name: string;
    created: boolean;
  };
}
```

---

### 6. Update Budget

**Method**: `PUT`  
**Endpoint**: `/api/admin/llm/budgets/{budget_id}`  
**Auth Required**: Yes (Bearer Token - Admin Only)

#### Request

##### Path Parameters
| Parameter | Type | Required | Description |
|----------|------|----------|-------------|
| `budget_id` | `UUID` | **Yes** | Budget identifier |

##### Request Body
```typescript
interface UpdateBudgetRequest {
  budget_amount_usd?: number;            // Decimal
  warning_threshold_percent?: number;    // 0-100
  critical_threshold_percent?: number;   // 0-100
  is_hard_limit?: boolean;
}
```

#### Response

##### Success Response (200 OK)
```typescript
interface BudgetResponse {
  success: boolean;
  data: {
    budget_id: string;
    updated: boolean;
  };
}
```

---

### 7. Delete Budget

**Method**: `DELETE`  
**Endpoint**: `/api/admin/llm/budgets/{budget_id}`  
**Auth Required**: Yes (Bearer Token - Admin Only)

#### Request

##### Path Parameters
| Parameter | Type | Required | Description |
|----------|------|----------|-------------|
| `budget_id` | `UUID` | **Yes** | Budget identifier |

#### Response

##### Success Response (204 No Content)
No response body

---

## ⚡ Circuit Breaker Endpoints

### 8. List Circuit Breakers

**Method**: `GET`  
**Endpoint**: `/api/admin/llm/circuit-breakers`  
**Auth Required**: Yes (Bearer Token - Admin Only)

#### Response

##### Success Response (200 OK)
```typescript
interface CircuitBreakerResponse {
  success: boolean;
  data: {
    circuit_breakers: CircuitBreaker[];
    summary: {
      closed: number;
      open: number;
      half_open: number;
    };
  };
}

interface CircuitBreaker {
  id: string;                             // UUID
  entity_type: string;                    // "model" | "provider"
  entity_id: string;                      // UUID
  entity_name: string;
  state: 'closed' | 'open' | 'half_open';
  failure_count: number;
  consecutive_failures: number;
  last_failure_at: string | null;         // ISO 8601
  config: {
    failure_threshold: number;
    success_threshold: number;
    timeout_seconds: number;
  };
}
```

---

### 9. Reset Circuit Breaker

**Method**: `POST`  
**Endpoint**: `/api/admin/llm/circuit-breakers/{breaker_id}/reset`  
**Auth Required**: Yes (Bearer Token - Admin Only)

#### Request

##### Path Parameters
| Parameter | Type | Required | Description |
|----------|------|----------|-------------|
| `breaker_id` | `UUID` | **Yes** | Circuit breaker identifier |

#### Response

##### Success Response (200 OK)
```typescript
interface CircuitBreakerResponse {
  success: boolean;
  data: {
    circuit_breaker_id: string;
    previous_state: string;
    new_state: 'closed';
    reset_at: string;                     // ISO 8601
  };
}
```

---

## 📊 Ranking Management Endpoints

### 10. Get Rankings

**Method**: `GET`  
**Endpoint**: `/api/admin/llm/rankings`  
**Auth Required**: Yes (Bearer Token - Admin Only)

#### Request

##### Query Parameters
| Parameter | Type | Required | Description | Default |
|----------|------|----------|-------------|---------|
| `agent_type` | `string` | No | Filter by agent type | All agents |

#### Response

##### Success Response (200 OK)
```typescript
interface RankingResponse {
  success: boolean;
  data: {
    rankings: AgentRanking[];
    last_recalculated_at: string;        // ISO 8601
  };
}

interface AgentRanking {
  agent_type: string;
  models: RankedModel[];
}

interface RankedModel {
  rank: number;
  model_id: string;                      // UUID
  model_name: string;
  provider: string;
  ranking_score: number;                 // 0-1
  success_rate: number;                 // 0-1
  avg_latency_ms: number;
  avg_cost_per_request: number;
  total_requests: number;
  has_override: boolean;
}
```

---

### 11. Update Ranking Weights

**Method**: `PUT`  
**Endpoint**: `/api/admin/llm/rankings/weights`  
**Auth Required**: Yes (Bearer Token - Admin Only)

#### Request

##### Request Body
```typescript
interface UpdateWeightsRequest {
  agent_type: string;
  weights: {
    success_weight: number;              // Decimal, should sum to ~1.0
    latency_weight: number;             // Decimal
    cost_weight: number;                 // Decimal
    recency_weight: number;              // Decimal
  };
}
```

**JSON Example**:
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

#### Response

##### Success Response (200 OK)
```typescript
interface RankingResponse {
  success: boolean;
  data: {
    agent_type: string;
    weights_updated: boolean;
  };
}
```

---

### 12. Recalculate Rankings

**Method**: `POST`  
**Endpoint**: `/api/admin/llm/rankings/recalculate`  
**Auth Required**: Yes (Bearer Token - Admin Only)

#### Request

##### Request Body
```typescript
interface RecalculateRequest {
  agent_type?: string;                   // Optional: Recalculate specific agent
}
```

#### Response

##### Success Response (200 OK)
```typescript
interface RankingResponse {
  success: boolean;
  data: {
    recalculated_count: number;
    agent_types_affected: string[];
    duration_ms: number;
  };
}
```

---

### 13. Create Ranking Override

**Method**: `POST`  
**Endpoint**: `/api/admin/llm/rankings/override`  
**Auth Required**: Yes (Bearer Token - Admin Only)

#### Request

##### Request Body
```typescript
interface RankingOverrideRequest {
  agent_type: string;
  model_id: string;                      // UUID
  override_score: number;                // Decimal
  reason: string;
  expires_at?: string;                   // ISO 8601, optional
}
```

#### Response

##### Success Response (200 OK)
```typescript
interface RankingResponse {
  success: boolean;
  data: {
    override_id: string;                 // UUID
    agent_type: string;
    model_id: string;
    override_score: number;
    created: boolean;
  };
}
```

---

## 📈 Telemetry Endpoints

### 14. Get Telemetry Overview

**Method**: `GET`  
**Endpoint**: `/api/admin/llm/telemetry/overview`  
**Auth Required**: Yes (Bearer Token - Admin Only)

#### Request

##### Query Parameters
| Parameter | Type | Required | Description | Default |
|----------|------|----------|-------------|---------|
| `period` | `string` | No | Time period | `24h` |

**Valid `period` Values**: `1h`, `24h`, `7d`, `30d`

#### Response

##### Success Response (200 OK)
```typescript
interface TelemetryResponse {
  success: boolean;
  data: {
    period: string;
    total_requests: number;
    success_rate: number;                // 0-1
    avg_latency_ms: number;
    p95_latency_ms: number;
    total_cost_usd: number;
    total_tokens: {
      input: number;
      output: number;
    };
    requests_by_provider: Array<{
      provider: string;
      count: number;
      success_rate: number;
      avg_latency_ms: number;
    }>;
    requests_by_agent: Array<{
      agent: string;
      count: number;
      avg_latency_ms: number;
    }>;
    retry_rate: number;                  // 0-1
    circuit_breakers_open: number;
  };
}
```

---

### 15. Get Telemetry Time-Series

**Method**: `GET`  
**Endpoint**: `/api/admin/llm/telemetry/timeseries`  
**Auth Required**: Yes (Bearer Token - Admin Only)

#### Request

##### Query Parameters
| Parameter | Type | Required | Description | Default |
|----------|------|----------|-------------|---------|
| `metric` | `string` | No | Metric type | `requests` |
| `period` | `string` | No | Time period | `24h` |
| `group_by` | `string` | No | Grouping dimension | `provider` |
| `interval` | `string` | No | Time interval | `auto` |

**Valid `metric` Values**: `requests`, `latency`, `cost`, `errors`, `tokens`

**Valid `period` Values**: `1h`, `24h`, `7d`, `30d`

**Valid `group_by` Values**: `provider`, `model`, `agent`

**Valid `interval` Values**: `auto`, `5m`, `1h`, `1d`

#### Response

##### Success Response (200 OK)
```typescript
interface TelemetryResponse {
  success: boolean;
  data: {
    metric: string;
    period: string;
    interval: string;
    data: TimeSeriesDataPoint[];
  };
}
```

---

### 16. Get Cost Analysis

**Method**: `GET`  
**Endpoint**: `/api/admin/llm/telemetry/cost`  
**Auth Required**: Yes (Bearer Token - Admin Only)

#### Request

##### Query Parameters
| Parameter | Type | Required | Description | Default |
|----------|------|----------|-------------|---------|
| `period` | `string` | No | Time period | `30d` |

**Valid `period` Values**: `7d`, `30d`, `90d`

#### Response

##### Success Response (200 OK)
```typescript
interface TelemetryResponse {
  success: boolean;
  data: {
    period: string;
    total_cost_usd: number;
    cost_by_provider: Array<{
      provider: string;
      cost: number;
      percentage: number;
    }>;
    cost_by_agent: Array<{
      agent: string;
      cost: number;
      requests: number;
    }>;
    cost_by_model: Array<{
      model: string;
      cost: number;
    }>;
    daily_trend: Array<{
      date: string;                      // ISO 8601 date
      cost: number;
    }>;
    projected_monthly_cost: number;
    budget_status: {
      monthly_budget: number;
      current_spend: number;
      percentage_used: number;            // 0-100
      days_remaining: number;
    };
  };
}
```

---

## 🤖 Agent Management Endpoints

### 17. List Agents

**Method**: `GET`  
**Endpoint**: `/api/admin/agents/`  
**Auth Required**: Yes (Bearer Token - Admin Only)

#### Response

##### Success Response (200 OK)
```typescript
interface AgentRead {
  type: AgentType;
  name: string;
  description: string;
  is_active: boolean;
}

type AgentType = 'TRADING' | 'RESEARCH' | 'YIELD_FARMING' | 'RISK_ANALYSIS' | 'PORTFOLIO';
```

**JSON Example**:
```json
[
  {
    "type": "TRADING",
    "name": "Trading Agent",
    "description": "Analyzes market trends",
    "is_active": true
  },
  {
    "type": "RESEARCH",
    "name": "Research Agent",
    "description": "Deep dive into protocols",
    "is_active": true
  }
]
```

---

## 🧪 Distillation Management Endpoints

### 18. Create Static Response

**Method**: `POST`  
**Endpoint**: `/api/admin/distillation/static-responses`  
**Auth Required**: Yes (Bearer Token - Admin Only)

#### Request

##### Request Body
```typescript
interface StaticResponseCreate {
  intent: string;
  variant: string;
  response_template: string;
  template_variables: string[];
  data_source: string;
  conditions: { [key: string]: any };
  priority: number;
  is_active: boolean;
}
```

#### Response

##### Success Response (201 Created)
```typescript
interface StaticResponseResponse {
  id: string;                            // UUID
  intent: string;
  variant: string;
  response_template: string;
  template_variables: string[];
  data_source: string;
  conditions: { [key: string]: any };
  priority: number;
  is_active: boolean;
  created_at: string;                    // ISO 8601
  updated_at: string;                    // ISO 8601
}
```

---

### 19. List Static Responses

**Method**: `GET`  
**Endpoint**: `/api/admin/distillation/static-responses`  
**Auth Required**: Yes (Bearer Token - Admin Only)

#### Request

##### Query Parameters
| Parameter | Type | Required | Description | Default |
|----------|------|----------|-------------|---------|
| `intent` | `string` | No | Filter by intent | All intents |
| `is_active` | `boolean` | No | Filter by active status | All responses |

#### Response

##### Success Response (200 OK)
Returns `StaticResponseResponse[]`

---

### 20. Update Static Response

**Method**: `PATCH`  
**Endpoint**: `/api/admin/distillation/static-responses/{response_id}`  
**Auth Required**: Yes (Bearer Token - Admin Only)

#### Request

##### Path Parameters
| Parameter | Type | Required | Description |
|----------|------|----------|-------------|
| `response_id` | `UUID` | **Yes** | Static response identifier |

##### Request Body
```typescript
interface StaticResponseUpdate {
  response_template?: string;
  is_active?: boolean;
}
```

#### Response

##### Success Response (200 OK)
Returns `StaticResponseResponse`

---

### 21. Delete Static Response

**Method**: `DELETE`  
**Endpoint**: `/api/admin/distillation/static-responses/{response_id}`  
**Auth Required**: Yes (Bearer Token - Admin Only)

#### Request

##### Path Parameters
| Parameter | Type | Required | Description |
|----------|------|----------|-------------|
| `response_id` | `UUID` | **Yes** | Static response identifier |

#### Response

##### Success Response (204 No Content)
No response body

---

### 22. Get Distillation Config

**Method**: `GET`  
**Endpoint**: `/api/admin/distillation/config`  
**Auth Required**: Yes (Bearer Token - Admin Only)

#### Response

##### Success Response (200 OK)
```typescript
interface DistillationConfigResponse {
  enabled: boolean;
  cache_enabled: boolean;
  static_responses_enabled: boolean;
  semantic_cache_enabled: boolean;
  min_confidence_threshold: number;     // 0-1
  semantic_similarity_threshold: number;  // 0-1
  max_classification_latency_ms: number;
}
```

---

### 23. Update Distillation Config

**Method**: `PATCH`  
**Endpoint**: `/api/admin/distillation/config`  
**Auth Required**: Yes (Bearer Token - Admin Only)

#### Request

##### Request Body
```typescript
interface DistillationConfigUpdate {
  enabled?: boolean;
  cache_enabled?: boolean;
  static_responses_enabled?: boolean;
  semantic_cache_enabled?: boolean;
  min_confidence_threshold?: number;     // 0-1
  semantic_similarity_threshold?: number; // 0-1
  max_classification_latency_ms?: number;
}
```

#### Response

##### Success Response (200 OK)
Returns `DistillationConfigResponse`

---

### 24. Invalidate Cache

**Method**: `POST`  
**Endpoint**: `/api/admin/distillation/cache/invalidate`  
**Auth Required**: Yes (Bearer Token - Admin Only)

#### Request

##### Request Body
```typescript
interface CacheInvalidateRequest {
  cache_type: 'exact' | 'semantic' | 'all';
  filters?: { [key: string]: any };
}
```

#### Response

##### Success Response (204 No Content)
No response body

---

### 25. Get Cache Stats

**Method**: `GET`  
**Endpoint**: `/api/admin/distillation/cache/stats`  
**Auth Required**: Yes (Bearer Token - Admin Only)

#### Response

##### Success Response (200 OK)
```typescript
interface CacheStatsResponse {
  exact_cache: {
    hits: number;
    misses: number;
    hit_rate: number;                   // 0-1
  };
  semantic_cache: {
    hits: number;
    misses: number;
    hit_rate: number;                    // 0-1
  };
}
```

---

### 26. Get Distillation Telemetry Requests

**Method**: `GET`  
**Endpoint**: `/api/admin/distillation/telemetry/requests`  
**Auth Required**: Yes (Bearer Token - Admin Only)

#### Request

##### Query Parameters
| Parameter | Type | Required | Description | Default |
|----------|------|----------|-------------|---------|
| `user_id` | `UUID` | No | Filter by user | All users |
| `intent` | `string` | No | Filter by intent | All intents |
| `route_type` | `string` | No | Filter by route type | All types |
| `limit` | `number` | No | Max results | `100` |

**Valid `limit` Range**: 1-1000

#### Response

##### Success Response (200 OK)
```typescript
interface DistillationTelemetryResponse {
  request_id: string;                    // UUID
  user_id: string | null;                // UUID
  original_query: string;
  intent: string;
  complexity: string;
  route_type: string;
  cache_hit: boolean;
  cache_level: string;
  classification_latency_ms: number;
  created_at: string;                    // ISO 8601
}
```

Returns `DistillationTelemetryResponse[]`

---

### 27. Get Distillation Telemetry Summary

**Method**: `GET`  
**Endpoint**: `/api/admin/distillation/telemetry/summary`  
**Auth Required**: Yes (Bearer Token - Admin Only)

#### Request

##### Query Parameters
| Parameter | Type | Required | Description | Default |
|----------|------|----------|-------------|---------|
| `hours` | `number` | No | Number of hours | `24` |

**Valid `hours` Range**: 1-168 (7 days)

#### Response

##### Success Response (200 OK)
```typescript
interface DistillationSummaryResponse {
  hour: string;                          // ISO 8601 hour
  total_requests: number;
  cache_hits: number;
  static_responses: number;
  light_llm: number;
  full_llm: number;
  rejected: number;
  avg_classification_ms: number;
  avg_confidence: number;                 // 0-1
}
```

Returns `DistillationSummaryResponse[]`

---

## ✅ Distillation Validation Endpoints

### 28. List Validation Responses

**Method**: `GET`  
**Endpoint**: `/api/admin/distillation/validation/responses`  
**Auth Required**: Yes (Bearer Token - Admin Only)

#### Request

##### Query Parameters
| Parameter | Type | Required | Description | Default |
|----------|------|----------|-------------|---------|
| `status` | `string` | No | Filter by status | All statuses |
| `intent` | `string` | No | Filter by intent | All intents |
| `limit` | `number` | No | Max results | `50` |
| `offset` | `number` | No | Pagination offset | `0` |

**Valid `status` Values**: `pending`, `approved`, `rejected`

#### Response

##### Success Response (200 OK)
```typescript
interface ValidationResponse {
  id: string;                            // UUID
  intent: string;
  original_query: string;
  proposed_response: string;
  confidence: number;                    // 0-1
  status: 'pending' | 'approved' | 'rejected';
  created_at: string;                    // ISO 8601
  reviewed_by: string | null;            // User ID
  reviewed_at: string | null;            // ISO 8601
  rejection_reason: string | null;
}
```

Returns paginated list with `total`, `limit`, `offset`

---

### 29. Get Validation Response

**Method**: `GET`  
**Endpoint**: `/api/admin/distillation/validation/responses/{response_id}`  
**Auth Required**: Yes (Bearer Token - Admin Only)

#### Request

##### Path Parameters
| Parameter | Type | Required | Description |
|----------|------|----------|-------------|
| `response_id` | `UUID` | **Yes** | Validation response identifier |

#### Response

##### Success Response (200 OK)
Returns `ValidationResponse` with full details including metadata

---

### 30. Approve Validation Response

**Method**: `PATCH`  
**Endpoint**: `/api/admin/distillation/validation/responses/{response_id}/approve`  
**Auth Required**: Yes (Bearer Token - Admin Only)

#### Request

##### Path Parameters
| Parameter | Type | Required | Description |
|----------|------|----------|-------------|
| `response_id` | `UUID` | **Yes** | Validation response identifier |

##### Request Body
```typescript
interface ApproveRequest {
  notes?: string;
}
```

#### Response

##### Success Response (200 OK)
```json
{
  "success": true,
  "message": "Validation response approved"
}
```

---

### 31. Reject Validation Response

**Method**: `PATCH`  
**Endpoint**: `/api/admin/distillation/validation/responses/{response_id}/reject`  
**Auth Required**: Yes (Bearer Token - Admin Only)

#### Request

##### Path Parameters
| Parameter | Type | Required | Description |
|----------|------|----------|-------------|
| `response_id` | `UUID` | **Yes** | Validation response identifier |

##### Request Body
```typescript
interface RejectRequest {
  reason: string;                        // Required
  notes?: string;
}
```

#### Response

##### Success Response (200 OK)
```json
{
  "success": true,
  "message": "Validation response rejected"
}
```

---

### 32. Get Validation Analytics

**Method**: `GET`  
**Endpoint**: `/api/admin/distillation/validation/analytics`  
**Auth Required**: Yes (Bearer Token - Admin Only)

#### Request

##### Query Parameters
| Parameter | Type | Required | Description | Default |
|----------|------|----------|-------------|---------|
| `period` | `string` | No | Time period | `7d` |
| `intent` | `string` | No | Filter by intent | All intents |

**Valid `period` Values**: `24h`, `7d`, `30d`

#### Response

##### Success Response (200 OK)
```typescript
interface ValidationAnalyticsResponse {
  period: string;
  total_responses: number;
  pending: number;
  approved: number;
  rejected: number;
  approval_rate: number;                 // 0-1
  average_confidence: number;            // 0-1
  by_intent: Array<{
    intent: string;
    total: number;
    approved: number;
    rejected: number;
    pending: number;
  }>;
  trends: Array<{
    date: string;                        // ISO 8601 date
    total: number;
    approved: number;
    rejected: number;
  }>;
}
```

---

## 📝 Request/Response Schemas

### Complete TypeScript Interfaces

See individual endpoint sections above for detailed schemas.

### Common Types

```typescript
// Time series data point
interface TimeSeriesDataPoint {
  timestamp: string;                     // ISO 8601
  value: number;
  label: string | null;
}

// Error response format
interface ErrorResponse {
  detail: string;
}
```

---

## ⚠️ Error Handling

### Common Error Patterns

1. **Authentication Errors (401)**
   - Invalid or expired token
   - **Action**: Refresh token, if fails → redirect to login

2. **Authorization Errors (403)**
   - Not admin user
   - **Action**: Show error: "Admin access required"

3. **Validation Errors (400)**
   - Invalid parameters
   - Invalid request body
   - **Action**: Show inline field errors

4. **Not Found Errors (404)**
   - Model not found
   - Budget not found
   - Static response not found
   - **Action**: Show error: "Resource not found"

5. **Service Unavailable (503)**
   - Backend service down
   - **Action**: Show error message + Retry button

### Error Handling Summary

| Status | Error Code | Description | UI Behavior |
|--------|------------|-------------|-------------|
| `400` | `BadRequestError` | Invalid parameters | Show inline errors |
| `401` | `AuthenticationError` | Invalid token | Redirect to login |
| `403` | `AuthorizationError` | Not admin | Show error: "Admin access required" |
| `404` | `NotFoundError` | Resource not found | Show error: "Resource not found" |
| `500` | `Exception` | Internal server error | Show error: "Internal error" + Retry |
| `503` | `DataMapperError` | Service unavailable | Show error: "Service unavailable" + Retry |

---

## 🔐 Authentication

All endpoints require:
- **Bearer Token**: Admin JWT token in `Authorization` header
- **Admin Role**: User must have admin privileges

**Header Format**:
```http
Authorization: Bearer {jwt_token}
```

---

## 📡 WebSocket Connections

### LLM Dashboard WebSocket

**Endpoint**: `ws://localhost:8000/api/admin/llm/dashboard/ws`  
**Auth Required**: Yes (JWT Token in Query Parameter)  
**Purpose**: Real-time updates for LLM dashboard metrics

#### Connection

**Connection URL**:
```
ws://localhost:8000/api/admin/llm/dashboard/ws?token={jwt_token}
```

#### Client-to-Server Messages

##### Heartbeat (Ping)
```typescript
interface PingMessage {
  type: "ping";
}
```

#### Server-to-Client Messages

##### Connection Confirmed
```typescript
interface ConnectionMessage {
  type: "connection";
  status: "connected";
  timestamp: string;                     // ISO 8601
}
```

##### Heartbeat Response (Pong)
```typescript
interface PongMessage {
  type: "pong";
  timestamp: string;                     // ISO 8601
}
```

##### Metrics Update
```typescript
interface MetricsUpdateMessage {
  type: "metrics_update";
  data: {
    total_requests: number;
    total_cost_usd: number;
    avg_response_time_ms: number;
    error_rate: number;
  };
  timestamp: string;                     // ISO 8601
}
```

#### Connection Lifecycle

1. **Connect**: Client connects with JWT token
2. **Receive Updates**: Server broadcasts updates periodically
3. **Heartbeat**: Client sends ping every 30 seconds
4. **Disconnect**: Client closes connection or server disconnects on error

---

## 🎯 API Design Trade-off Analysis (CTO Methodology)

### Key Design Decisions

| Decision | Alternative | Trade-off | Rationale |
|----------|------------|-----------|-----------|
| **WebSocket for Real-time Updates** | Polling | Real-time vs. Resource usage | WebSocket reduces server load vs. polling, but requires connection management |
| **Separate Endpoints per Submodule** | Single Aggregated Endpoint | Granularity vs. Performance | Separate endpoints allow focused queries, but increase request count |
| **Cost Impact Display** | Hidden Costs | Transparency vs. Complexity | Showing cost impact improves decision-making, but adds UI complexity |
| **Ranking Override System** | Fixed Rankings | Flexibility vs. Maintenance | Overrides allow emergency adjustments, but require careful management |

### Risk Assessment

**Cognitive Limitations:**
- WebSocket connection management may be complex for frontend developers
- Multiple submodules may overwhelm admins
- Cost calculations may be inaccurate

**Technical Debt:**
- WebSocket reconnection logic must handle network failures gracefully
- Ranking calculations may become slow with many models
- Budget enforcement requires careful coordination

**Validation Strategy:**
- ✅ Monitor WebSocket connection health
- ✅ Track endpoint performance
- ✅ Validate cost calculations
- ✅ Alert on budget threshold breaches

---

## 🔗 Related Documentation

- **Backend Controllers**: `src/app/presentation/http/controllers/admin/llm/`
- **Backend Controllers**: `src/app/presentation/http/controllers/admin/agents/`
- **Backend Controllers**: `src/app/presentation/http/controllers/admin/distillation/`
- **Response Schemas**: `src/app/presentation/http/schemas/`
- **Frontend Implementation**: `03-Intelligence-Ops/IMPLEMENTATION.md`
- **UI/UX Design**: `03-Intelligence-Ops/UI_UX.md`

---

**Last Updated**: 2024-01-01  
**API Version**: v1  
**Status**: Production Ready
