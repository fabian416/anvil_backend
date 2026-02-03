# Distillation System API Endpoints

> **Complete endpoint reference organized by access level**
> **Version:** 2.0 (Intent-Free Routing)
> **Last Updated:** 2026-01-26

---

## Table of Contents

- [Overview](#overview)
- [Access Levels](#access-levels)
- [Guest Endpoints](#guest-endpoints)
- [User Endpoints](#user-endpoints)
- [Admin Endpoints](#admin-endpoints)
  - [Static Response Management](#static-response-management)
  - [Configuration Management](#configuration-management)
  - [Cache Management](#cache-management)
  - [Telemetry & Monitoring](#telemetry--monitoring)
- [Error Responses](#error-responses)
- [Integration Examples](#integration-examples)

---

## Overview

The Distillation System exposes **Admin-only endpoints** for system configuration and monitoring. The actual distillation functionality is **integrated into the chat system** and runs transparently during message processing.

### Endpoint Summary

| Access Level | Endpoint Count | Purpose |
|--------------|----------------|---------|
| **Guest** | 0 | No guest-accessible endpoints |
| **User** | 0 | Integrated into chat (transparent) |
| **Admin** | 10 | Configuration + Monitoring |

### Base Paths

```
Admin Endpoints:  /api/v1/admin/distillation/*
```

### Authentication

**Admin Endpoints:**
- Requires: JWT token with admin role
- Header: `Authorization: Bearer <token>`
- Role: `admin` or `superadmin`

**Integration Point (Transparent):**
- Distillation runs automatically in `send_message_with_distillation.py`
- No direct user-facing endpoints

---

## Access Levels

### Guest (Unauthenticated)

**Current Status:** No guest-accessible endpoints

**Rationale:**
- Distillation is a system-level optimization
- Configuration should not be exposed to guests
- Integrated transparently into chat system

### User (Authenticated)

**Current Status:** No user-accessible endpoints

**Rationale:**
- Distillation runs transparently during chat
- Users don't need direct access
- All functionality via chat endpoints:
  - `POST /api/v1/conversations/{id}/messages` (uses distillation)

### Admin (Administrative)

**Available Endpoints:**
- Static Response Management (4 endpoints)
- Configuration Management (2 endpoints)
- Cache Management (2 endpoints)
- Telemetry & Monitoring (2 endpoints)

---

## Guest Endpoints

**None available**

All distillation functionality is integrated into the authenticated chat system.

---

## User Endpoints

**None available**

Users interact with distillation **transparently** through the chat system:

### Integration Point: Chat Messages

**Endpoint:** `POST /api/v1/conversations/{conversation_id}/messages`

**Distillation Flow:**
```
User sends message
  ↓
send_message_with_distillation.py
  ↓
DistillationEngine.distill() (if enabled)
  ↓
Routing decision (cache/light LLM/full LLM)
  ↓
Response returned to user
```

**Example:**

```bash
# User sends message (distillation runs transparently)
curl -X POST http://localhost:8000/api/v1/conversations/{id}/messages \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "content": "what is ETH",
    "language": "en"
  }'

# Response includes distillation metadata (in development mode)
{
  "id": "uuid",
  "conversation_id": "uuid",
  "role": "assistant",
  "content": "Ethereum (ETH) is...",
  "metadata": {
    "distillation": {
      "route_type": "CACHE",
      "complexity": "simple",
      "cache_hit": true,
      "cache_level": "exact",
      "classification_latency_ms": 5
    }
  },
  "created_at": "2026-01-26T12:00:00Z"
}
```

---

## Admin Endpoints

### Static Response Management

#### 1. Create Static Response

**Endpoint:** `POST /api/v1/admin/distillation/static-responses`

**Purpose:** Create a new static response template for an intent.

**Access:** Admin only

**Implementation:**
- **Controller:** `/home/ubuntu/anvil_backend/src/app/presentation/http/controllers/admin/distillation_router.py:39`
- **Handler:** `DistillationStaticRepositorySqla.add_response()`
- **Domain:** `StaticResponse` entity

**Request Schema:**

```python
{
  "intent": "price_check",           # Intent category (Intent enum)
  "variant": "default",              # Variant name (default, morning, etc.)
  "response_template": "The current price of {token} is ${price}.",
  "template_variables": ["token", "price"],  # Variables to inject
  "data_source": "coingecko_api",    # Data source for variables (optional)
  "conditions": {},                  # Conditions for variant selection (optional)
  "priority": 1,                     # Priority (higher = first)
  "is_active": true                  # Whether response is active
}
```

**Response Schema:**

```python
{
  "id": "uuid",
  "intent": "price_check",
  "variant": "default",
  "response_template": "The current price of {token} is ${price}.",
  "template_variables": ["token", "price"],
  "data_source": "coingecko_api",
  "conditions": {},
  "priority": 1,
  "is_active": true,
  "created_at": "2026-01-26T12:00:00Z",
  "updated_at": "2026-01-26T12:00:00Z"
}
```

**Example Request:**

```bash
curl -X POST http://localhost:8000/api/v1/admin/distillation/static-responses \
  -H "Authorization: Bearer <admin-token>" \
  -H "Content-Type: application/json" \
  -d '{
    "intent": "price_check",
    "variant": "default",
    "response_template": "The current price of {token} is ${price} ({change_24h}% 24h).",
    "template_variables": ["token", "price", "change_24h"],
    "data_source": "coingecko_api",
    "priority": 1,
    "is_active": true
  }'
```

**Business Logic:**
1. Validate intent (must be valid Intent enum value)
2. Create StaticResponse entity with UUID
3. Store in `distillation_static_responses` table
4. Return created response

**Error Responses:**
- `400 Bad Request`: Invalid intent or missing required fields
- `401 Unauthorized`: Missing or invalid admin token
- `409 Conflict`: Duplicate (intent + variant) combination

---

#### 2. List Static Responses

**Endpoint:** `GET /api/v1/admin/distillation/static-responses`

**Purpose:** List all static response templates with optional filters.

**Access:** Admin only

**Implementation:**
- **Controller:** `/home/ubuntu/anvil_backend/src/app/presentation/http/controllers/admin/distillation_router.py:85`
- **Handler:** `DistillationStaticRepositorySqla.list_responses()`

**Query Parameters:**
- `intent` (optional): Filter by intent (e.g., "price_check")
- `is_active` (optional): Filter by active status (true/false)

**Response Schema:**

```python
[
  {
    "id": "uuid",
    "intent": "greeting",
    "variant": "default",
    "response_template": "Hello! I'm Anvil...",
    "template_variables": [],
    "data_source": null,
    "conditions": {},
    "priority": 1,
    "is_active": true,
    "created_at": "2025-12-01T00:00:00Z",
    "updated_at": "2025-12-01T00:00:00Z"
  },
  ...
]
```

**Example Requests:**

```bash
# List all static responses
curl http://localhost:8000/api/v1/admin/distillation/static-responses \
  -H "Authorization: Bearer <admin-token>"

# Filter by intent
curl "http://localhost:8000/api/v1/admin/distillation/static-responses?intent=greeting" \
  -H "Authorization: Bearer <admin-token>"

# Filter by active status
curl "http://localhost:8000/api/v1/admin/distillation/static-responses?is_active=true" \
  -H "Authorization: Bearer <admin-token>"
```

**Business Logic:**
1. Parse query parameters
2. Query `distillation_static_responses` table with filters
3. Return list of StaticResponse entities

---

#### 3. Update Static Response

**Endpoint:** `PATCH /api/v1/admin/distillation/static-responses/{response_id}`

**Purpose:** Update an existing static response template.

**Access:** Admin only

**Implementation:**
- **Controller:** `/home/ubuntu/anvil_backend/src/app/presentation/http/controllers/admin/distillation_router.py:119`
- **Handler:** `DistillationStaticRepositorySqla.update_response()`

**Path Parameters:**
- `response_id`: UUID of the static response

**Request Schema:**

```python
{
  "response_template": "Updated template with {token}",  # Optional
  "is_active": false                                     # Optional
}
```

**Response Schema:**

```python
{
  "id": "uuid",
  "intent": "price_check",
  "variant": "default",
  "response_template": "Updated template with {token}",
  "template_variables": ["token"],
  "data_source": "coingecko_api",
  "conditions": {},
  "priority": 1,
  "is_active": false,
  "created_at": "2025-12-01T00:00:00Z",
  "updated_at": "2026-01-26T12:00:00Z"
}
```

**Example Request:**

```bash
curl -X PATCH http://localhost:8000/api/v1/admin/distillation/static-responses/{id} \
  -H "Authorization: Bearer <admin-token>" \
  -H "Content-Type: application/json" \
  -d '{
    "response_template": "Updated: The price of {token} is ${price}",
    "is_active": true
  }'
```

**Business Logic:**
1. Fetch existing StaticResponse by ID
2. Update provided fields (partial update)
3. Update `updated_at` timestamp
4. Save to database
5. Return updated response

**Error Responses:**
- `404 Not Found`: Static response ID not found
- `400 Bad Request`: Invalid update data

---

#### 4. Delete Static Response

**Endpoint:** `DELETE /api/v1/admin/distillation/static-responses/{response_id}`

**Purpose:** Delete a static response template.

**Access:** Admin only

**Implementation:**
- **Controller:** `/home/ubuntu/anvil_backend/src/app/presentation/http/controllers/admin/distillation_router.py:157`
- **Handler:** `DistillationStaticRepositorySqla.delete_response()`

**Path Parameters:**
- `response_id`: UUID of the static response

**Response:**
- **Status Code:** `204 No Content`
- **Body:** Empty

**Example Request:**

```bash
curl -X DELETE http://localhost:8000/api/v1/admin/distillation/static-responses/{id} \
  -H "Authorization: Bearer <admin-token>"
```

**Business Logic:**
1. Delete StaticResponse by ID
2. Remove from `distillation_static_responses` table
3. Return 204 No Content

**Error Responses:**
- `404 Not Found`: Static response ID not found

---

### Configuration Management

#### 5. Get Distillation Configuration

**Endpoint:** `GET /api/v1/admin/distillation/config`

**Purpose:** Retrieve current distillation system configuration.

**Access:** Admin only

**Implementation:**
- **Controller:** `/home/ubuntu/anvil_backend/src/app/presentation/http/controllers/admin/distillation_router.py:172`
- **Handler:** `DistillationConfigRepositorySqla.get_config()`

**Response Schema:**

```python
{
  "enabled": true,                          # Whether distillation is enabled
  "cache_enabled": true,                    # Whether caching is enabled
  "static_responses_enabled": false,        # Static responses (disabled in v2.0)
  "semantic_cache_enabled": true,           # Semantic similarity cache
  "min_confidence_threshold": 0.7,          # Min confidence for classification
  "semantic_similarity_threshold": 0.95,    # Min similarity for semantic cache
  "max_classification_latency_ms": 100      # Max latency budget
}
```

**Example Request:**

```bash
curl http://localhost:8000/api/v1/admin/distillation/config \
  -H "Authorization: Bearer <admin-token>"
```

**Business Logic:**
1. Query `distillation_config` table
2. Parse config_value JSON for each config_key
3. Return DistillationConfig object

**Configuration Keys:**
- `feature_flags`: enabled, cache_enabled, static_responses_enabled, semantic_cache_enabled
- `thresholds`: min_confidence, semantic_similarity, max_latency_ms
- `routing_rules`: force_full_llm_intents, cache_ttl_by_intent

---

#### 6. Update Distillation Configuration

**Endpoint:** `PATCH /api/v1/admin/distillation/config`

**Purpose:** Update distillation system configuration (runtime toggle).

**Access:** Admin only

**Implementation:**
- **Controller:** `/home/ubuntu/anvil_backend/src/app/presentation/http/controllers/admin/distillation_router.py:194`
- **Handler:** `DistillationConfigRepositorySqla.update_config()`

**Request Schema:**

```python
{
  "enabled": true,                          # Optional
  "cache_enabled": true,                    # Optional
  "static_responses_enabled": false,        # Optional
  "semantic_cache_enabled": true,           # Optional
  "min_confidence_threshold": 0.75,         # Optional
  "semantic_similarity_threshold": 0.95,    # Optional
  "max_classification_latency_ms": 100      # Optional
}
```

**Response Schema:** Same as GET /config

**Example Request:**

```bash
# Disable distillation system
curl -X PATCH http://localhost:8000/api/v1/admin/distillation/config \
  -H "Authorization: Bearer <admin-token>" \
  -H "Content-Type: application/json" \
  -d '{
    "enabled": false
  }'

# Enable cache and semantic search
curl -X PATCH http://localhost:8000/api/v1/admin/distillation/config \
  -H "Authorization: Bearer <admin-token>" \
  -H "Content-Type: application/json" \
  -d '{
    "cache_enabled": true,
    "semantic_cache_enabled": true,
    "semantic_similarity_threshold": 0.95
  }'
```

**Business Logic:**
1. Fetch current configuration
2. Update provided fields (partial update)
3. Validate thresholds (0.0 to 1.0 for confidence/similarity)
4. Save to `distillation_config` table
5. Return updated configuration

**Error Responses:**
- `400 Bad Request`: Invalid threshold values

**⚠️ Impact:**
- Changes take effect **immediately**
- No server restart required
- Affects all new requests

---

### Cache Management

#### 7. Invalidate Cache

**Endpoint:** `POST /api/v1/admin/distillation/cache/invalidate`

**Purpose:** Invalidate cache entries (manual cache cleanup).

**Access:** Admin only

**Implementation:**
- **Controller:** `/home/ubuntu/anvil_backend/src/app/presentation/http/controllers/admin/distillation_router.py:236`
- **Handler:** `DistillationCacheRepositorySqla.invalidate_exact_cache()`, `invalidate_semantic_cache()`

**Request Schema:**

```python
{
  "cache_type": "all",     # "exact" | "semantic" | "all"
  "filters": {             # Optional filters
    "intent": "price_check",           # Filter by intent
    "older_than_hours": 24             # Delete entries older than N hours
  }
}
```

**Response:**
- **Status Code:** `204 No Content`
- **Body:** Empty

**Example Requests:**

```bash
# Invalidate all cache
curl -X POST http://localhost:8000/api/v1/admin/distillation/cache/invalidate \
  -H "Authorization: Bearer <admin-token>" \
  -H "Content-Type: application/json" \
  -d '{
    "cache_type": "all"
  }'

# Invalidate exact cache only
curl -X POST http://localhost:8000/api/v1/admin/distillation/cache/invalidate \
  -H "Authorization: Bearer <admin-token>" \
  -H "Content-Type: application/json" \
  -d '{
    "cache_type": "exact"
  }'

# Invalidate old entries (>24 hours)
curl -X POST http://localhost:8000/api/v1/admin/distillation/cache/invalidate \
  -H "Authorization: Bearer <admin-token>" \
  -H "Content-Type: application/json" \
  -d '{
    "cache_type": "all",
    "filters": {
      "older_than_hours": 24
    }
  }'
```

**Business Logic:**
1. Parse cache_type and filters
2. Delete entries from `distillation_cache_exact` (if cache_type = "exact" or "all")
3. Delete entries from `distillation_cache_semantic` (if cache_type = "semantic" or "all")
4. Apply filters (intent, older_than_hours)
5. Return 204 No Content

**Use Cases:**
- Clear cache after model updates
- Remove stale data
- Force re-generation of responses

---

#### 8. Get Cache Statistics

**Endpoint:** `GET /api/v1/admin/distillation/cache/stats`

**Purpose:** Retrieve cache performance statistics.

**Access:** Admin only

**Implementation:**
- **Controller:** `/home/ubuntu/anvil_backend/src/app/presentation/http/controllers/admin/distillation_router.py:255`
- **Handler:** `DistillationCacheRepositorySqla.get_exact_cache_stats()`, `get_semantic_cache_stats()`

**Response Schema:**

```python
{
  "exact_cache": {
    "total_entries": 1523,
    "total_hits": 45234,
    "avg_hit_count": 29.7,
    "oldest_entry": "2025-12-15T08:30:00Z",
    "newest_entry": "2026-01-26T12:00:00Z"
  },
  "semantic_cache": {
    "total_entries": 892,
    "total_hits": 8901,
    "avg_hit_count": 9.98,
    "oldest_entry": "2026-01-20T14:22:00Z",
    "newest_entry": "2026-01-26T12:00:00Z"
  }
}
```

**Example Request:**

```bash
curl http://localhost:8000/api/v1/admin/distillation/cache/stats \
  -H "Authorization: Bearer <admin-token>"
```

**Business Logic:**
1. Query `distillation_cache_exact` table:
   - COUNT(*) as total_entries
   - SUM(hit_count) as total_hits
   - AVG(hit_count) as avg_hit_count
   - MIN(created_at) as oldest_entry
   - MAX(created_at) as newest_entry
2. Query `distillation_cache_semantic` table (same metrics)
3. Return combined statistics

**Metrics Explained:**
- **total_entries**: Number of cached responses
- **total_hits**: Total cache hits (sum of all hit_count)
- **avg_hit_count**: Average reuse per cached entry
- **oldest_entry**: First cached entry timestamp
- **newest_entry**: Most recent cached entry timestamp

---

### Telemetry & Monitoring

#### 9. Get Telemetry Requests

**Endpoint:** `GET /api/v1/admin/distillation/telemetry/requests`

**Purpose:** Retrieve recent distillation request logs with filters.

**Access:** Admin only

**Implementation:**
- **Controller:** `/home/ubuntu/anvil_backend/src/app/presentation/http/controllers/admin/distillation_router.py:275`
- **Handler:** `DistillationTelemetryRepositorySqla.get_requests()`

**Query Parameters:**
- `user_id` (optional): Filter by user ID (UUID)
- `intent` (optional): Filter by intent (e.g., "price_check")
- `route_type` (optional): Filter by route type (e.g., "CACHE", "LIGHT_LLM")
- `limit` (optional): Max results (default: 100, max: 1000)

**Response Schema:**

```python
[
  {
    "request_id": "uuid-string",
    "user_id": "uuid",
    "original_query": "what is ETH",
    "intent": "unclear",               # Intent (always "unclear" in v2.0)
    "complexity": "simple",            # Complexity level
    "route_type": "CACHE",             # Routing decision
    "cache_hit": true,                 # Whether cache was hit
    "cache_level": "exact",            # Cache level (exact/semantic)
    "classification_latency_ms": 5,    # Latency
    "created_at": "2026-01-26T12:00:00Z"
  },
  ...
]
```

**Example Requests:**

```bash
# Get last 100 requests
curl http://localhost:8000/api/v1/admin/distillation/telemetry/requests \
  -H "Authorization: Bearer <admin-token>"

# Filter by route type
curl "http://localhost:8000/api/v1/admin/distillation/telemetry/requests?route_type=CACHE&limit=50" \
  -H "Authorization: Bearer <admin-token>"

# Filter by user
curl "http://localhost:8000/api/v1/admin/distillation/telemetry/requests?user_id={uuid}" \
  -H "Authorization: Bearer <admin-token>"
```

**Business Logic:**
1. Parse query parameters
2. Query `distillation_requests` table with filters
3. Order by `created_at DESC`
4. Limit results
5. Return list of DistillationTelemetry entries

---

#### 10. Get Telemetry Summary

**Endpoint:** `GET /api/v1/admin/distillation/telemetry/summary`

**Purpose:** Retrieve hourly aggregated telemetry metrics.

**Access:** Admin only

**Implementation:**
- **Controller:** `/home/ubuntu/anvil_backend/src/app/presentation/http/controllers/admin/distillation_router.py:312`
- **Handler:** `DistillationTelemetryRepositorySqla.get_hourly_summary()`

**Query Parameters:**
- `hours` (optional): Number of hours to retrieve (default: 24, max: 168)

**Response Schema:**

```python
[
  {
    "hour": "2026-01-26T12:00:00Z",
    "total_requests": 1523,
    "cache_hits": 687,
    "static_responses": 0,           # Deprecated in v2.0
    "light_llm": 412,
    "full_llm": 424,
    "rejected": 0,
    "avg_classification_ms": 15,
    "avg_confidence": 1.0            # Always 1.0 in v2.0 (no classification)
  },
  ...
]
```

**Example Requests:**

```bash
# Get last 24 hours
curl http://localhost:8000/api/v1/admin/distillation/telemetry/summary \
  -H "Authorization: Bearer <admin-token>"

# Get last 7 days
curl "http://localhost:8000/api/v1/admin/distillation/telemetry/summary?hours=168" \
  -H "Authorization: Bearer <admin-token>"
```

**Business Logic:**
1. Parse `hours` parameter
2. Query `distillation_telemetry_hourly` table
3. Filter by `hour_bucket >= NOW() - INTERVAL '{hours} hours'`
4. Order by `hour_bucket DESC`
5. Return hourly summaries

**Metrics Explained:**
- **total_requests**: Total queries in hour
- **cache_hits**: Cache hits (exact + semantic)
- **static_responses**: Static template responses (0 in v2.0)
- **light_llm**: Light LLM calls (Gemini Flash)
- **full_llm**: Full LLM calls (Claude Sonnet)
- **rejected**: Rejected queries (spam, harmful)
- **avg_classification_ms**: Average classification latency
- **avg_confidence**: Average confidence (1.0 in v2.0)

**Use Cases:**
- Monitor system performance
- Track cost savings (cache hit rate)
- Identify performance regressions
- Analyze routing distribution

---

## Error Responses

### Standard Error Format

All endpoints return errors in this format:

```python
{
  "detail": "Error message",
  "error_code": "ERROR_CODE",
  "status_code": 400
}
```

### Common Error Codes

| Status Code | Error Code | Description |
|-------------|-----------|-------------|
| `400` | `INVALID_REQUEST` | Invalid request data |
| `401` | `UNAUTHORIZED` | Missing or invalid auth token |
| `403` | `FORBIDDEN` | Insufficient permissions (not admin) |
| `404` | `NOT_FOUND` | Resource not found |
| `409` | `CONFLICT` | Duplicate resource |
| `422` | `VALIDATION_ERROR` | Pydantic validation failed |
| `500` | `INTERNAL_ERROR` | Server error |

### Error Examples

**1. Unauthorized (Missing Token):**

```bash
curl http://localhost:8000/api/v1/admin/distillation/config

# Response (401)
{
  "detail": "Not authenticated"
}
```

**2. Forbidden (Not Admin):**

```bash
curl http://localhost:8000/api/v1/admin/distillation/config \
  -H "Authorization: Bearer <user-token>"

# Response (403)
{
  "detail": "Insufficient permissions. Admin access required.",
  "error_code": "FORBIDDEN"
}
```

**3. Validation Error:**

```bash
curl -X POST http://localhost:8000/api/v1/admin/distillation/static-responses \
  -H "Authorization: Bearer <admin-token>" \
  -H "Content-Type: application/json" \
  -d '{
    "intent": "invalid_intent",
    "response_template": ""
  }'

# Response (422)
{
  "detail": [
    {
      "loc": ["body", "intent"],
      "msg": "value is not a valid enumeration member",
      "type": "type_error.enum"
    },
    {
      "loc": ["body", "response_template"],
      "msg": "ensure this value has at least 1 characters",
      "type": "value_error.any_str.min_length"
    }
  ]
}
```

**4. Not Found:**

```bash
curl -X PATCH http://localhost:8000/api/v1/admin/distillation/static-responses/invalid-uuid \
  -H "Authorization: Bearer <admin-token>" \
  -H "Content-Type: application/json" \
  -d '{"is_active": false}'

# Response (404)
{
  "detail": "Static response not found",
  "error_code": "NOT_FOUND"
}
```

---

## Integration Examples

### Example 1: Enable/Disable Distillation

**Scenario:** Temporarily disable distillation during maintenance.

```bash
# 1. Disable distillation
curl -X PATCH http://localhost:8000/api/v1/admin/distillation/config \
  -H "Authorization: Bearer <admin-token>" \
  -H "Content-Type: application/json" \
  -d '{
    "enabled": false
  }'

# Response
{
  "enabled": false,
  "cache_enabled": true,
  "static_responses_enabled": false,
  "semantic_cache_enabled": true,
  "min_confidence_threshold": 0.7,
  "semantic_similarity_threshold": 0.95,
  "max_classification_latency_ms": 100
}

# 2. Verify chat still works (distillation bypassed)
curl -X POST http://localhost:8000/api/v1/conversations/{id}/messages \
  -H "Authorization: Bearer <user-token>" \
  -H "Content-Type: application/json" \
  -d '{
    "content": "what is ETH"
  }'

# 3. Re-enable distillation
curl -X PATCH http://localhost:8000/api/v1/admin/distillation/config \
  -H "Authorization: Bearer <admin-token>" \
  -H "Content-Type: application/json" \
  -d '{
    "enabled": true
  }'
```

---

### Example 2: Monitor Cache Performance

**Scenario:** Check cache hit rate and performance.

```bash
# 1. Get cache statistics
curl http://localhost:8000/api/v1/admin/distillation/cache/stats \
  -H "Authorization: Bearer <admin-token>"

# Response
{
  "exact_cache": {
    "total_entries": 1523,
    "total_hits": 45234,
    "avg_hit_count": 29.7,
    "oldest_entry": "2025-12-15T08:30:00Z",
    "newest_entry": "2026-01-26T12:00:00Z"
  },
  "semantic_cache": {
    "total_entries": 892,
    "total_hits": 8901,
    "avg_hit_count": 9.98,
    "oldest_entry": "2026-01-20T14:22:00Z",
    "newest_entry": "2026-01-26T12:00:00Z"
  }
}

# 2. Get hourly summary (last 24 hours)
curl "http://localhost:8000/api/v1/admin/distillation/telemetry/summary?hours=24" \
  -H "Authorization: Bearer <admin-token>"

# Response (truncated)
[
  {
    "hour": "2026-01-26T12:00:00Z",
    "total_requests": 1523,
    "cache_hits": 687,
    "light_llm": 412,
    "full_llm": 424,
    "avg_classification_ms": 15
  },
  ...
]

# 3. Calculate cache hit rate
# cache_hit_rate = 687 / 1523 = 45.1%
```

---

### Example 3: Invalidate Cache After Model Update

**Scenario:** New LLM model deployed, clear cache to regenerate responses.

```bash
# 1. Check current cache size
curl http://localhost:8000/api/v1/admin/distillation/cache/stats \
  -H "Authorization: Bearer <admin-token>"

# Response
{
  "exact_cache": {"total_entries": 1523, ...},
  "semantic_cache": {"total_entries": 892, ...}
}

# 2. Invalidate all cache
curl -X POST http://localhost:8000/api/v1/admin/distillation/cache/invalidate \
  -H "Authorization: Bearer <admin-token>" \
  -H "Content-Type: application/json" \
  -d '{
    "cache_type": "all"
  }'

# Response: 204 No Content

# 3. Verify cache cleared
curl http://localhost:8000/api/v1/admin/distillation/cache/stats \
  -H "Authorization: Bearer <admin-token>"

# Response
{
  "exact_cache": {"total_entries": 0, ...},
  "semantic_cache": {"total_entries": 0, ...}
}

# 4. Monitor cache rebuild
# Wait 1 hour, then check stats again
# Cache will rebuild as users send messages
```

---

### Example 4: Analyze Query Distribution

**Scenario:** Understand what types of queries users are sending.

```bash
# 1. Get recent requests
curl "http://localhost:8000/api/v1/admin/distillation/telemetry/requests?limit=1000" \
  -H "Authorization: Bearer <admin-token>" \
  > requests.json

# 2. Analyze route distribution (using jq)
cat requests.json | jq '[.[] | .route_type] | group_by(.) | map({route: .[0], count: length})'

# Output
[
  {"route": "CACHE", "count": 450},
  {"route": "LIGHT_LLM", "count": 200},
  {"route": "FULL_LLM", "count": 350}
]

# 3. Analyze complexity distribution
cat requests.json | jq '[.[] | .complexity] | group_by(.) | map({complexity: .[0], count: length})'

# Output
[
  {"complexity": "simple", "count": 300},
  {"complexity": "moderate", "count": 500},
  {"complexity": "complex", "count": 200}
]
```

---

### Example 5: Create Custom Static Response

**Scenario:** Add static response for common "hello" variations.

```bash
# 1. Create greeting variant
curl -X POST http://localhost:8000/api/v1/admin/distillation/static-responses \
  -H "Authorization: Bearer <admin-token>" \
  -H "Content-Type: application/json" \
  -d '{
    "intent": "greeting",
    "variant": "enthusiastic",
    "response_template": "Hey there! 👋 Super excited to help you with DeFi today!",
    "template_variables": [],
    "priority": 2,
    "is_active": true
  }'

# 2. Verify created
curl "http://localhost:8000/api/v1/admin/distillation/static-responses?intent=greeting" \
  -H "Authorization: Bearer <admin-token>"

# Response
[
  {
    "id": "uuid-1",
    "intent": "greeting",
    "variant": "default",
    "response_template": "Hello! I'm Anvil...",
    ...
  },
  {
    "id": "uuid-2",
    "intent": "greeting",
    "variant": "enthusiastic",
    "response_template": "Hey there! 👋 Super excited...",
    ...
  }
]

# 3. Test (static responses disabled in v2.0, but template exists)
# Static response won't be used, but template is stored for future use
```

---

## Performance Considerations

### Endpoint Latency Targets

| Endpoint | Target Latency | Notes |
|----------|----------------|-------|
| GET /config | <50ms | Cached in memory |
| PATCH /config | <100ms | Single DB write |
| GET /cache/stats | <200ms | Aggregate query |
| POST /cache/invalidate | <500ms | Bulk delete |
| GET /telemetry/requests | <300ms | Indexed query |
| GET /telemetry/summary | <200ms | Pre-aggregated |

### Rate Limiting

**Admin Endpoints:**
- Rate Limit: 100 requests/minute per admin user
- Burst: 200 requests in 10 seconds
- Response Header: `X-RateLimit-Remaining: 95`

**Monitoring Endpoints:**
- Higher limits for automated monitoring
- Telemetry endpoints: 1000 requests/minute

### Caching Headers

**Static Data (Config, Stats):**
```
Cache-Control: private, max-age=60
ETag: "hash-of-response"
```

**Dynamic Data (Requests, Summary):**
```
Cache-Control: no-cache
```

---

## Security Considerations

### Authentication

**JWT Validation:**
- Token must be valid and not expired
- Token must have `admin` or `superadmin` role
- Token signature verified with RS256

**Example JWT Payload:**

```json
{
  "sub": "user-uuid",
  "email": "admin@example.com",
  "role": "admin",
  "exp": 1738137600,
  "iat": 1738051200
}
```

### Authorization

**Role-Based Access Control (RBAC):**
- `admin`: Full access to all distillation endpoints
- `superadmin`: Full access + ability to modify system config
- `user`: No access to admin endpoints

### Input Validation

**Pydantic Schemas:**
- All request bodies validated with Pydantic
- Type checking enforced
- Range validation for numeric fields
- Enum validation for string fields

**Example Validation:**

```python
class DistillationConfigUpdate(BaseModel):
    enabled: Optional[bool] = Field(None)
    min_confidence_threshold: Optional[float] = Field(None, ge=0.0, le=1.0)
    max_classification_latency_ms: Optional[int] = Field(None, ge=1, le=5000)
```

### SQL Injection Prevention

**SQLAlchemy ORM:**
- All queries use parameterized statements
- No raw SQL with user input
- Input sanitization via Pydantic

### Sensitive Data

**No PII in Telemetry:**
- User IDs stored as UUIDs
- Original queries stored (but no passwords/tokens)
- IP addresses not logged

**Cache Security:**
- Cached responses contain no sensitive data
- Cache invalidation on logout (user-specific caches only)

---

## Changelog

### v2.0 (2026-01-26)
- **BREAKING:** Removed intent-based routing
- All queries now routed by complexity only
- Intent field always set to `Intent.UNCLEAR`
- Static responses disabled (infrastructure kept)

### v1.0 (2025-12-01)
- Initial release
- 10 admin endpoints
- Static response management
- Cache management
- Telemetry tracking

---

**Document Version:** 2.0
**Last Updated:** 2026-01-26
**Status:** Production-Ready
