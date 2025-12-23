# Module: LLM Configuration

**Route**: `/admin/intelligence-ops/models`  
**Auth Required**: Yes (Admin Only)  
**Package**: `admin/intelligence-ops/models`

## 1. Overview
Allows admins to manage the AI models available to the platform. Includes enabling/disabling specific models, adjusting carousel position (frontend display order), viewing cost rates, and monitoring performance per model.

## 2. API Contract

### List Models
**Endpoint**: `GET /api/admin/llm/models`  
**Query Params**:
- `provider_id` (UUID, optional): Filter by provider.
- `is_enabled` (boolean, optional): Filter by enabled status.
- `tier` (string, optional): Filter by tier - `premium`, `standard`, `economy`.

#### Response Body (`ModelListResponse`)
| Field | Type | Description |
|---|---|---|
| `success` | `boolean` | Whether request was successful |
| `data` | `ModelListData` | Model list data |

**ModelListData Object**:
| Field | Type | Description |
|---|---|---|
| `models` | `Model[]` | Array of model objects |
| `total` | `number` | Total number of models |

**Model Object**:
| Field | Type | Description |
|---|---|---|
| `id` | `string` | Model UUID |
| `provider_id` | `string` | Provider UUID |
| `provider_name` | `string` | Provider name (e.g., "vertex_ai") |
| `model_id` | `string` | Model identifier (e.g., "gemini-1.5-pro") |
| `display_name` | `string` | Display name |
| `model_family` | `string` | Model family (e.g., "gemini") |
| `capabilities` | `string[]` | Array of capabilities |
| `context_window` | `number` | Context window size |
| `cost_per_1k_input` | `number` | Cost per 1k input tokens (USD) |
| `cost_per_1k_output` | `number` | Cost per 1k output tokens (USD) |
| `carousel_position` | `number` | Display order in carousel |
| `tier` | `string` | Model tier |
| `is_enabled` | `boolean` | Whether model is enabled |
| `circuit_breaker_state` | `string \| null` | Circuit breaker state: `closed`, `open`, `half_open`, or null |

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

### Update Model
**Endpoint**: `PUT /api/admin/llm/models/{model_id}`  
**Path Params**:
- `model_id` (string, **required**): Model UUID.

#### Request Body (`UpdateModelRequest`)
| Field | Type | Description |
|---|---|---|
| `is_enabled` | `boolean` | Optional: Enable/disable model |
| `carousel_position` | `number` | Optional: Display order |
| `cost_per_1k_input` | `number` | Optional: Input cost per 1k tokens |
| `cost_per_1k_output` | `number` | Optional: Output cost per 1k tokens |

**JSON Example**:
```json
{
  "is_enabled": false,
  "carousel_position": 5,
  "cost_per_1k_input": 0.0015,
  "cost_per_1k_output": 0.004
}
```

#### Response
`200 OK` - Returns updated `ModelListResponse`

### Get Model Performance
**Endpoint**: `GET /api/admin/llm/models/{model_id}/performance`  
**Path Params**:
- `model_id` (string, **required**): Model UUID.

**Query Params**:
- `period` (string, optional): Time period - `24h`, `7d`, `30d` (Default: `24h`).

#### Response Body (`ModelPerformanceResponse`)
| Field | Type | Description |
|---|---|---|
| `data` | `ModelPerformanceData` | Performance data |

**ModelPerformanceData Object**:
| Field | Type | Description |
|---|---|---|
| `model_id` | `string` | Model identifier |
| `metrics` | `ModelMetrics` | Performance metrics |

**ModelMetrics Object**:
| Field | Type | Description |
|---|---|---|
| `success_rate` | `number` | Success rate (0-1) |
| `avg_latency_ms` | `number` | Average latency in milliseconds |
| `p95_latency_ms` | `number` | 95th percentile latency |
| `total_cost_usd` | `number` | Total cost in USD |

### Error Codes
| Status | Error Code | Description | UI Behavior |
|---|---|---|---|
| `401` | `AuthenticationError` | Invalid or expired token | Redirect to login |
| `403` | `AuthorizationError` | Not admin | Show error: "Admin access required" |
| `404` | `NotFoundError` | Model not found | Show error: "Model not found" |
| `400` | `DomainFieldError` | Invalid request data | Show error: "Invalid model configuration" |
| `500` | `Exception` | Internal server error | Show error: "Failed to update model" + Retry button |
| `503` | `DataMapperError` | Service unavailable | Show error: "Service unavailable" + Retry button |

## 3. Implementation Flow

1. **Mount**: Call `useModels({ provider_id, is_enabled, tier })` hook which fetches `/api/admin/llm/models`.
2. **Display**:
   - Model cards/table: Display `models` array with model information.
   - Toggle switch: Show `is_enabled` status with toggle switch for each model.
   - Circuit breaker status: Display `circuit_breaker_state` with color coding (Green=closed, Red=open, Yellow=half-open).
   - Cost display: Show `cost_per_1k_input` and `cost_per_1k_output` with tooltip explaining "Per 1K Tokens".
3. **Filter**: On filter change (provider, enabled status, tier), update query params and refetch.
4. **Toggle Model**: On toggle switch change:
   - Show confirmation modal with cost impact preview.
   - Call `PUT /api/admin/llm/models/{model_id}` with `is_enabled` update.
   - Optimistically update UI, invalidate query cache.
5. **Edit Model**: On "Edit" button click, open edit modal with current values, allow updating carousel position and costs.
6. **View Performance**: On "Performance" button click, call `GET /api/admin/llm/models/{model_id}/performance`, display metrics in modal or navigate to performance view.
