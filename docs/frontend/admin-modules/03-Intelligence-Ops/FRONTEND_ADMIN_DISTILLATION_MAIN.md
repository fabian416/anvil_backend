# Admin Module: Distillation Management

> **Technical Specification**: `FRONTEND_ADMIN_DISTILLATION_MAIN`
> **Backend Controller**: `admin/distillation_router.py`
> **Base URL**: `/api/admin/distillation`

## 📖 Overview
The **Distillation Management** submodule enables administrators to manage AI response optimization through static responses, configuration, cache management, and telemetry. Distillation optimizes AI responses by routing simple queries to static responses or lightweight models, reducing costs and latency.

### Key Capabilities
1. **Static Response Management**: Create, list, update, and delete static response templates.
2. **Configuration**: Manage distillation settings (enabled/disabled, cache settings, thresholds).
3. **Cache Management**: Invalidate cache entries and view cache statistics.
4. **Telemetry**: View distillation request telemetry and hourly summaries.

---

## 🔌 API Endpoints

### Static Responses

#### 1. Create Static Response
**POST** `/api/admin/distillation/static-responses`
Create a new static response template.

**Request Body (`StaticResponseCreate`)**:
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

**Response (`StaticResponseResponse`)**:
```json
{
  "id": "uuid",
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
```

#### 2. List Static Responses
**GET** `/api/admin/distillation/static-responses`
List all static response templates.

| Parameter | Type | Required | Description |
| :--- | :--- | :--- | :--- |
| `intent` | `str` | No | Filter by intent. |
| `is_active` | `bool` | No | Filter by active status. |

**Response (`List[StaticResponseResponse]`)**:
```json
[
  {
    "id": "uuid",
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

#### 3. Update Static Response
**PATCH** `/api/admin/distillation/static-responses/{response_id}`
Update a static response template.

**Request Body (`StaticResponseUpdate`)**:
```json
{
  "response_template": "Updated template",
  "is_active": false
}
```

**Response**: `StaticResponseResponse`

#### 4. Delete Static Response
**DELETE** `/api/admin/distillation/static-responses/{response_id}`
Delete a static response template.

**Response**: `204 No Content`

### Configuration

#### 5. Get Distillation Config
**GET** `/api/admin/distillation/config`
Get current distillation configuration.

**Response (`DistillationConfigResponse`)**:
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

#### 6. Update Distillation Config
**PATCH** `/api/admin/distillation/config`
Update distillation configuration.

**Request Body (`DistillationConfigUpdate`)**:
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

**Response**: `DistillationConfigResponse`

### Cache Management

#### 7. Invalidate Cache
**POST** `/api/admin/distillation/cache/invalidate`
Invalidate cache entries.

**Request Body (`CacheInvalidateRequest`)**:
```json
{
  "cache_type": "exact",
  "filters": {"intent": "price_query"}
}
```

**Response**: `204 No Content`

**Cache Types**:
- `exact`: Exact match cache
- `semantic`: Semantic similarity cache
- `all`: Both caches

#### 8. Get Cache Stats
**GET** `/api/admin/distillation/cache/stats`
Get cache statistics.

**Response (`CacheStatsResponse`)**:
```json
{
  "exact_cache": {
    "hits": 1500,
    "misses": 200,
    "hit_rate": 0.882
  },
  "semantic_cache": {
    "hits": 800,
    "misses": 100,
    "hit_rate": 0.889
  }
}
```

### Telemetry

#### 9. Get Telemetry Requests
**GET** `/api/admin/distillation/telemetry/requests`
Get distillation telemetry requests.

| Parameter | Type | Required | Description |
| :--- | :--- | :--- | :--- |
| `user_id` | `UUID` | No | Filter by user ID. |
| `intent` | `str` | No | Filter by intent. |
| `route_type` | `str` | No | Filter by route type. |
| `limit` | `int` | No | Limit results (max 1000, default 100). |

**Response (`List[DistillationTelemetryResponse]`)**:
```json
[
  {
    "request_id": "uuid",
    "user_id": "user-uuid",
    "original_query": "What is the price of ETH?",
    "intent": "price_query",
    "complexity": "simple",
    "route_type": "static_response",
    "cache_hit": true,
    "cache_level": "exact",
    "classification_latency_ms": 15,
    "created_at": "2023-10-01T10:00:00Z"
  }
]
```

#### 10. Get Telemetry Summary
**GET** `/api/admin/distillation/telemetry/summary`
Get hourly distillation telemetry summary.

| Parameter | Type | Required | Description |
| :--- | :--- | :--- | :--- |
| `hours` | `int` | No | Number of hours to retrieve (max 168, default 24). |

**Response (`List[DistillationSummaryResponse]`)**:
```json
[
  {
    "hour": "2023-10-01T10:00:00Z",
    "total_requests": 1500,
    "cache_hits": 800,
    "static_responses": 400,
    "light_llm": 200,
    "full_llm": 100,
    "rejected": 0,
    "avg_classification_ms": 20,
    "avg_confidence": 0.92
  }
]
```

---

## 🎨 UI/UX Guidelines

### Static Response Management
- **List View**: Table showing all static responses with intent, variant, template preview, and active status.
- **Create Form**: Multi-step form for creating static responses:
  1. Intent and variant selection
  2. Template editor with variable placeholders
  3. Data source configuration
  4. Conditions and priority settings
- **Edit View**: Inline editing or modal for updating responses.
- **Status Toggle**: Quick toggle for enabling/disabling responses.

### Configuration Panel
- **Toggle Switches**: Enable/disable distillation features.
- **Threshold Sliders**: Adjust confidence and similarity thresholds.
- **Latency Input**: Set maximum classification latency.
- **Save Button**: Prominent save button with confirmation.

### Cache Management
- **Cache Stats Dashboard**: Visual display of cache hit rates and statistics.
- **Invalidation Controls**: Dropdown to select cache type and filters.
- **Confirmation**: Require confirmation before invalidating cache.

### Telemetry Dashboard
- **Request List**: Paginated table of telemetry requests with filters.
- **Summary Charts**: Visual charts showing hourly summaries:
  - Request volume over time
  - Cache hit rates
  - Route type distribution
  - Average confidence scores
- **Filters**: Filter by user, intent, route type, and time range.

---

## 🔒 Security Considerations

- **Admin Only**: All endpoints require admin authentication.
- **Sensitive Data**: Telemetry may contain user queries; ensure proper access controls.
- **Cache Invalidation**: Require confirmation for cache invalidation operations.
