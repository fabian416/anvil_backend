# Module: LLM Rankings

**Route**: `/admin/intelligence-ops/rankings`  
**Auth Required**: Yes (Admin Only)  
**Package**: `admin/intelligence-ops/rankings`

## 1. Overview
Enables administrators to view and manage model rankings for different agent types. Rankings determine which models are selected for specific agents based on performance metrics (success rate, latency, cost). Admins can customize ranking weights, recalculate rankings, and create manual overrides.

## 2. API Contract

### Get Rankings
**Endpoint**: `GET /api/admin/llm/rankings`  
**Query Params**:
- `agent_type` (string, optional): Filter by agent type (e.g., "swap_agent").

#### Response Body (`RankingResponse`)
| Field | Type | Description |
|---|---|---|
| `success` | `boolean` | Whether request was successful |
| `data` | `RankingListData` | Ranking list data |

**RankingListData Object**:
| Field | Type | Description |
|---|---|---|
| `rankings` | `AgentRanking[]` | Array of agent rankings |
| `last_recalculated_at` | `string` | ISO 8601 timestamp of last recalculation |

**AgentRanking Object**:
| Field | Type | Description |
|---|---|---|
| `agent_type` | `string` | Agent type identifier |
| `models` | `RankedModel[]` | Array of ranked models |

**RankedModel Object**:
| Field | Type | Description |
|---|---|---|
| `rank` | `number` | Ranking position (1 = highest) |
| `model_id` | `string` | Model UUID |
| `model_name` | `string` | Model display name |
| `provider` | `string` | Provider name |
| `ranking_score` | `number` | Overall ranking score (0-1) |
| `success_rate` | `number` | Success rate (0-1) |
| `avg_latency_ms` | `number` | Average latency in milliseconds |
| `avg_cost_per_request` | `number` | Average cost per request (USD) |
| `total_requests` | `number` | Total requests |
| `has_override` | `boolean` | Whether this ranking has a manual override |

**JSON Example**:
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
            "model_id": "550e8400-e29b-41d4-a716-446655440000",
            "model_name": "gemini-1.5-pro",
            "provider": "vertex_ai",
            "ranking_score": 0.8945,
            "success_rate": 0.985,
            "avg_latency_ms": 1100,
            "avg_cost_per_request": 0.0072,
            "total_requests": 8000,
            "has_override": false
          }
        ]
      }
    ],
    "last_recalculated_at": "2024-01-15T09:00:00Z"
  }
}
```

### Update Ranking Weights
**Endpoint**: `PUT /api/admin/llm/rankings/weights`  
**Query Params**: None

#### Request Body (`UpdateWeightsRequest`)
| Field | Type | Description |
|---|---|---|
| `agent_type` | `string` | Agent type (required) |
| `weights` | `RankingWeights` | Ranking weight configuration (required) |

**RankingWeights Object**:
| Field | Type | Description |
|---|---|---|
| `success_weight` | `number` | Weight for success rate (should sum to ~1.0) |
| `latency_weight` | `number` | Weight for latency |
| `cost_weight` | `number` | Weight for cost |
| `recency_weight` | `number` | Weight for recency |

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

#### Response Body (`RankingResponse`)
| Field | Type | Description |
|---|---|---|
| `success` | `boolean` | Whether request was successful |
| `data` | `WeightUpdateData` | Weight update data |

**WeightUpdateData Object**:
| Field | Type | Description |
|---|---|---|
| `agent_type` | `string` | Agent type |
| `weights_updated` | `boolean` | Whether weights were updated |

### Recalculate Rankings
**Endpoint**: `POST /api/admin/llm/rankings/recalculate`  
**Query Params**: None

#### Request Body (`RecalculateRequest`)
| Field | Type | Description |
|---|---|---|
| `agent_type` | `string` | Optional: Recalculate specific agent, or omit for all agents |

**JSON Example**:
```json
{
  "agent_type": "swap_agent"
}
```

#### Response Body (`RankingResponse`)
| Field | Type | Description |
|---|---|---|
| `success` | `boolean` | Whether request was successful |
| `data` | `RecalculateData` | Recalculation data |

**RecalculateData Object**:
| Field | Type | Description |
|---|---|---|
| `recalculated_count` | `number` | Number of rankings recalculated |
| `agent_types_affected` | `string[]` | Array of affected agent types |
| `duration_ms` | `number` | Recalculation duration in milliseconds |

### Create Ranking Override
**Endpoint**: `POST /api/admin/llm/rankings/override`  
**Query Params**: None

#### Request Body (`RankingOverrideRequest`)
| Field | Type | Description |
|---|---|---|
| `agent_type` | `string` | Agent type (required) |
| `model_id` | `string` | Model UUID (required) |
| `override_score` | `number` | Override ranking score (required) |
| `reason` | `string` | Reason for override (required) |
| `expires_at` | `string` | Optional: ISO 8601 expiration timestamp |

**JSON Example**:
```json
{
  "agent_type": "swap_agent",
  "model_id": "550e8400-e29b-41d4-a716-446655440000",
  "override_score": 0.95,
  "reason": "Emergency: Force this model for critical operations",
  "expires_at": "2024-01-20T00:00:00Z"
}
```

#### Response Body (`RankingResponse`)
| Field | Type | Description |
|---|---|---|
| `success` | `boolean` | Whether request was successful |
| `data` | `OverrideCreateData` | Override creation data |

**OverrideCreateData Object**:
| Field | Type | Description |
|---|---|---|
| `override_id` | `string` | Created override UUID |
| `agent_type` | `string` | Agent type |
| `model_id` | `string` | Model UUID |
| `override_score` | `number` | Override score |
| `created` | `boolean` | Whether override was created |

### Error Codes
| Status | Error Code | Description | UI Behavior |
|---|---|---|---|
| `401` | `AuthenticationError` | Invalid or expired token | Redirect to login |
| `403` | `AuthorizationError` | Not admin | Show error: "Admin access required" |
| `400` | `DomainFieldError` | Invalid weights (don't sum to ~1.0) or invalid request | Show error: "Weights must sum to approximately 1.0" |
| `404` | `NotFoundError` | Agent type or model not found | Show error: "Agent type or model not found" |
| `500` | `Exception` | Internal server error | Show error: "Failed to update rankings" + Retry button |
| `503` | `DataMapperError` | Service unavailable | Show error: "Service unavailable" + Retry button |

## 3. Implementation Flow

1. **Mount**: Call `useRankings(agentType)` hook which fetches `/api/admin/llm/rankings`.
2. **Display**:
   - Rankings table: Display `rankings` array grouped by `agent_type`, showing ranked models with columns: Rank, Model Name, Provider, Ranking Score, Success Rate, Latency, Cost, Override Indicator.
   - Override badge: Show badge if `has_override` is true.
   - Last recalculated: Display `last_recalculated_at` timestamp.
3. **Filter by Agent**: On agent type selection, update `agent_type` query param and refetch.
4. **Update Weights**: On "Edit Weights" button click:
   - Open weight configuration modal.
   - Show current weights with sliders/inputs.
   - Validate that weights sum to ~1.0.
   - On submit, call `PUT /api/admin/llm/rankings/weights` with request body.
   - On success: Show success toast, invalidate query cache.
5. **Recalculate Rankings**: On "Recalculate" button click:
   - Show confirmation modal: "This will recalculate rankings for all models. This may take a few moments."
   - Call `POST /api/admin/llm/rankings/recalculate` with optional `agent_type`.
   - Show loading state during recalculation.
   - On success: Refresh rankings, show success toast with `duration_ms`.
6. **Create Override**: On "Create Override" button click:
   - Open override creation modal.
   - Select agent type and model.
   - Enter override score and reason.
   - Optional: Set expiration date.
   - On submit, call `POST /api/admin/llm/rankings/override` with request body.
   - On success: Refresh rankings, show success toast, invalidate query cache.
