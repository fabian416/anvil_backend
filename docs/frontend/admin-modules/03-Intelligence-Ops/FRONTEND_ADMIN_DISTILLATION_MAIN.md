# Module: Distillation Management

**Route**: `/admin/intelligence-ops/distillation`  
**Auth Required**: Yes (Admin Only)  
**Package**: `admin/intelligence-ops/distillation`

## 1. Overview
Enables administrators to manage AI response optimization through static responses, configuration, cache management, and telemetry. Distillation optimizes AI responses by routing simple queries to static responses or lightweight models, reducing costs and latency.

## 2. API Contract

### List Static Responses
**Endpoint**: `GET /api/admin/distillation/static-responses`  
**Query Params**:
- `intent` (string, optional): Filter by intent.
- `is_active` (boolean, optional): Filter by active status.

#### Response Body (`StaticResponseResponse[]`)
Array of static response objects.

**StaticResponseResponse Object**:
| Field | Type | Description |
|---|---|---|
| `id` | `string` | Static response UUID |
| `intent` | `string` | Intent identifier |
| `variant` | `string` | Response variant |
| `response_template` | `string` | Response template with variables |
| `template_variables` | `string[]` | Array of template variable names |
| `data_source` | `string` | Data source identifier |
| `conditions` | `{ [key: string]: any }` | Conditions for matching |
| `priority` | `number` | Priority (higher = preferred) |
| `is_active` | `boolean` | Whether response is active |
| `created_at` | `string` | ISO 8601 creation timestamp |
| `updated_at` | `string` | ISO 8601 update timestamp |

**JSON Example**:
```json
[
  {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "intent": "price_query",
    "variant": "default",
    "response_template": "The current price of {token} is ${price}",
    "template_variables": ["token", "price"],
    "data_source": "coingecko",
    "conditions": {"min_confidence": 0.9},
    "priority": 1,
    "is_active": true,
    "created_at": "2023-10-01T10:00:00Z",
    "updated_at": "2023-10-01T10:00:00Z"
  }
]
```

### Create Static Response
**Endpoint**: `POST /api/admin/distillation/static-responses`  
**Query Params**: None

#### Request Body (`StaticResponseCreate`)
| Field | Type | Description |
|---|---|---|
| `intent` | `string` | Intent identifier (required) |
| `variant` | `string` | Response variant (required) |
| `response_template` | `string` | Response template (required) |
| `template_variables` | `string[]` | Array of template variable names (required) |
| `data_source` | `string` | Data source identifier (required) |
| `conditions` | `{ [key: string]: any }` | Conditions for matching (required) |
| `priority` | `number` | Priority (required) |
| `is_active` | `boolean` | Whether response is active (Default: true) |

**JSON Example**:
```json
{
  "intent": "price_query",
  "variant": "default",
  "response_template": "The current price of {token} is ${price}",
  "template_variables": ["token", "price"],
  "data_source": "coingecko",
  "conditions": {"min_confidence": 0.9},
  "priority": 1,
  "is_active": true
}
```

#### Response Body (`StaticResponseResponse`)
Returns created static response object.

### Update Static Response
**Endpoint**: `PATCH /api/admin/distillation/static-responses/{response_id}`  
**Path Params**:
- `response_id` (string, **required**): Static response UUID.

#### Request Body (`StaticResponseUpdate`)
| Field | Type | Description |
|---|---|---|
| `response_template` | `string` | Optional: Updated template |
| `is_active` | `boolean` | Optional: Updated active status |
| `priority` | `number` | Optional: Updated priority |

**JSON Example**:
```json
{
  "response_template": "Updated template with {token} at ${price}",
  "is_active": false,
  "priority": 2
}
```

#### Response Body (`StaticResponseResponse`)
Returns updated static response object.

### Delete Static Response
**Endpoint**: `DELETE /api/admin/distillation/static-responses/{response_id}`  
**Path Params**:
- `response_id` (string, **required**): Static response UUID.

#### Response
`204 No Content` - No response body

### Get Distillation Config
**Endpoint**: `GET /api/admin/distillation/config`  
**Query Params**: None

#### Response Body (`DistillationConfigResponse`)
| Field | Type | Description |
|---|---|---|
| `enabled` | `boolean` | Whether distillation is enabled |
| `cache_enabled` | `boolean` | Whether cache is enabled |
| `static_responses_enabled` | `boolean` | Whether static responses are enabled |
| `semantic_cache_enabled` | `boolean` | Whether semantic cache is enabled |
| `min_confidence_threshold` | `number` | Minimum confidence threshold (0-1) |
| `semantic_similarity_threshold` | `number` | Semantic similarity threshold (0-1) |
| `max_classification_latency_ms` | `number` | Maximum classification latency in milliseconds |

**JSON Example**:
```json
{
  "enabled": true,
  "cache_enabled": true,
  "static_responses_enabled": true,
  "semantic_cache_enabled": true,
  "min_confidence_threshold": 0.85,
  "semantic_similarity_threshold": 0.90,
  "max_classification_latency_ms": 100
}
```

### Update Distillation Config
**Endpoint**: `PATCH /api/admin/distillation/config`  
**Query Params**: None

#### Request Body (`DistillationConfigUpdate`)
| Field | Type | Description |
|---|---|---|
| `enabled` | `boolean` | Optional: Enable/disable distillation |
| `cache_enabled` | `boolean` | Optional: Enable/disable cache |
| `static_responses_enabled` | `boolean` | Optional: Enable/disable static responses |
| `semantic_cache_enabled` | `boolean` | Optional: Enable/disable semantic cache |
| `min_confidence_threshold` | `number` | Optional: Minimum confidence threshold |
| `semantic_similarity_threshold` | `number` | Optional: Semantic similarity threshold |
| `max_classification_latency_ms` | `number` | Optional: Maximum classification latency |

**JSON Example**:
```json
{
  "enabled": true,
  "min_confidence_threshold": 0.90,
  "semantic_similarity_threshold": 0.95
}
```

#### Response Body (`DistillationConfigResponse`)
Returns updated configuration object.

### Get Cache Statistics
**Endpoint**: `GET /api/admin/distillation/cache/stats`  
**Query Params**: None

#### Response Body (`CacheStatsResponse`)
| Field | Type | Description |
|---|---|---|
| `total_entries` | `number` | Total cache entries |
| `hit_count` | `number` | Cache hit count |
| `miss_count` | `number` | Cache miss count |
| `hit_rate` | `number` | Cache hit rate (0-1) |
| `memory_usage_mb` | `number` | Memory usage in MB |
| `eviction_count` | `number` | Number of evictions |

### Invalidate Cache
**Endpoint**: `POST /api/admin/distillation/cache/invalidate`  
**Query Params**: None

#### Request Body (`CacheInvalidateRequest`)
| Field | Type | Description |
|---|---|---|
| `intent` | `string` | Optional: Invalidate specific intent |
| `all` | `boolean` | Optional: Invalidate all cache (if true) |

**JSON Example**:
```json
{
  "intent": "price_query"
}
```

#### Response
`204 No Content` - No response body

### Error Codes
| Status | Error Code | Description | UI Behavior |
|---|---|---|---|
| `401` | `AuthenticationError` | Invalid or expired token | Redirect to login |
| `403` | `AuthorizationError` | Not admin | Show error: "Admin access required" |
| `404` | `NotFoundError` | Static response not found | Show error: "Static response not found" |
| `400` | `DomainFieldError` | Invalid request data | Show error: "Invalid static response configuration" |
| `500` | `Exception` | Internal server error | Show error: "Failed to manage distillation" + Retry button |
| `503` | `DataMapperError` | Service unavailable | Show error: "Service unavailable" + Retry button |

## 3. Implementation Flow

1. **Mount**: Call `useStaticResponses({ intent, is_active })` hook which fetches `/api/admin/distillation/static-responses`.
2. **Display**:
   - Static responses table: Display responses array with columns: Intent, Variant, Template Preview, Data Source, Priority, Status (Active/Inactive), Actions.
   - Filter: Provide filters for intent and active status.
3. **Create Static Response**: On "Create" button click:
   - Open create modal/form.
   - Collect all required fields (intent, variant, template, variables, data source, conditions, priority).
   - Validate template variables match template placeholders.
   - On submit, call `POST /api/admin/distillation/static-responses` with request body.
   - On success: Add to list, show success toast, invalidate query cache.
4. **Update Static Response**: On "Edit" button click:
   - Open edit modal with current values pre-populated.
   - Allow updating template, active status, priority.
   - On submit, call `PATCH /api/admin/distillation/static-responses/{response_id}`.
   - On success: Update display, show success toast, invalidate query cache.
5. **Delete Static Response**: On "Delete" button click:
   - Show confirmation modal: "Are you sure you want to delete this static response?"
   - On confirm, call `DELETE /api/admin/distillation/static-responses/{response_id}`.
   - On success: Remove from list, show success toast, invalidate query cache.
6. **Configuration Management**: 
   - Call `GET /api/admin/distillation/config` to load current configuration.
   - Display configuration form with toggles and threshold inputs.
   - On save, call `PATCH /api/admin/distillation/config` with updated values.
   - On success: Update display, show success toast.
7. **Cache Management**:
   - Call `GET /api/admin/distillation/cache/stats` to display cache statistics.
   - On "Invalidate Cache" button click, show confirmation modal.
   - Call `POST /api/admin/distillation/cache/invalidate` with optional intent filter.
   - On success: Refresh cache stats, show success toast.
