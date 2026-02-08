# Discovery Module — Document 6: API Spec — Admin Endpoints

## Base Path: `/api/v1/admin/discovery`
## Auth: JWT Bearer token + role check (`system_admin` OR `content_admin` from admin_roles table)

---

## 1. Category Management

### 1.1 GET /admin/discovery/categories
**Description:** List all categories (including inactive).
**Auth:** Admin required

### Response 200
```json
{
  "categories": [
    {
      "id": "uuid-news",
      "slug": "news",
      "name": "News",
      "icon": "newspaper",
      "sort_order": 1,
      "is_active": true,
      "is_default": true,
      "config": {},
      "section_count": 42,
      "created_at": "2026-01-15T00:00:00Z",
      "updated_at": "2026-02-08T10:00:00Z",
      "created_by": "uuid-admin"
    }
  ]
}
```

### 1.2 POST /admin/discovery/categories
**Description:** Create a new category.
**Auth:** Admin required

### Request Body
```json
{
  "slug": "alpha_signals",
  "name": "Alpha Signals",
  "description": "On-chain whale alerts and smart money flows",
  "icon": "signal",
  "sort_order": 3,
  "is_active": true,
  "is_default": false,
  "config": {}
}
```

**Validation:**
- `slug`: 1-50 chars, lowercase alphanumeric + underscores, UNIQUE
- `name`: 1-100 chars
- `sort_order`: integer ≥ 0

### Response 201
```json
{
  "id": "uuid-new",
  "slug": "alpha_signals",
  "name": "Alpha Signals",
  "message": "Category created successfully"
}
```

**Side effects:** Invalidates `discovery:categories` cache.

### 1.3 PATCH /admin/discovery/categories/{slug}
**Description:** Update category fields (partial update).
**Auth:** Admin required

### Request Body (any subset)
```json
{
  "name": "Alpha Signals Pro",
  "is_active": false,
  "sort_order": 5,
  "config": {"max_articles": 100}
}
```

**Critical behavior:** Setting `is_active: false` hides the entire category tab for ALL users immediately.

### Response 200
```json
{
  "id": "uuid-alpha",
  "slug": "alpha_signals",
  "message": "Category updated successfully"
}
```

**Side effects:** Invalidates `discovery:categories`, `discovery:sections:*`, `discovery:feed:*` caches.

### 1.4 DELETE /admin/discovery/categories/{slug}
**Description:** Soft delete (sets is_active=false). Hard delete only if no sections exist.
**Auth:** Admin required

### Response 200
```json
{"message": "Category deactivated", "slug": "alpha_signals"}
```

### Response 409 (has sections)
```json
{"detail": "Cannot hard delete category with existing sections. Use PATCH to deactivate."}
```

---

## 2. Section Management

### 2.1 GET /admin/discovery/sections
**Description:** List all sections (including inactive), optionally filtered by category.
**Auth:** Admin required

### Query Parameters
| Param | Type | Default | Description |
|-------|------|---------|-------------|
| category | string | null | Filter by category slug |
| include_inactive | bool | true | Include inactive sections |

### Response 200
```json
{
  "sections": [
    {
      "id": "uuid-politics",
      "category_slug": "news",
      "parent_id": null,
      "parent_slug": null,
      "slug": "politics",
      "name": "Politics",
      "icon": "landmark",
      "sort_order": 1,
      "is_active": true,
      "is_default": true,
      "metadata": {"keywords": ["politics", "government", "policy", "legislation"]},
      "subsection_count": 11,
      "article_count": 1250,
      "created_at": "2026-01-15T00:00:00Z"
    }
  ]
}
```

### 2.2 POST /admin/discovery/sections
**Description:** Create a new section or subsection.
**Auth:** Admin required

### Request Body
```json
{
  "category_slug": "news",
  "parent_slug": "tech_science",
  "slug": "quantum_computing",
  "name": "Quantum Computing",
  "description": "Quantum computing breakthroughs and commercial applications",
  "icon": "atom",
  "sort_order": 17,
  "is_active": true,
  "is_default": false,
  "metadata": {
    "keywords": ["quantum", "qubit", "quantum computing", "ibm quantum", "google quantum"]
  }
}
```

**Validation:**
- `category_slug`: must reference existing active category
- `parent_slug`: null for top-level, or must reference existing section in same category
- `slug`: 1-100 chars, unique within category
- `metadata.keywords`: required for news collection — these drive Celery fetch queries

### Response 201
```json
{
  "id": "uuid-quantum",
  "slug": "quantum_computing",
  "category_slug": "news",
  "parent_slug": "tech_science",
  "message": "Section created successfully. News collection will begin within 15 minutes."
}
```

**Side effects:**
- Invalidates `discovery:sections:news` cache
- New section appears in next Celery beat cycle (≤15 min)
- If `is_default: true` → new users auto-see this section

### 2.3 PATCH /admin/discovery/sections/{id}
**Description:** Update section fields (partial update).
**Auth:** Admin required

### Request Body (any subset)
```json
{
  "is_active": false,
  "is_default": true,
  "name": "Quantum Computing & Qubits",
  "metadata": {
    "keywords": ["quantum", "qubit", "quantum supremacy", "topological qubit"]
  }
}
```

**Critical behaviors:**
- `is_active: false` → hides section from ALL users, stops Celery collection for it
- `is_default: true` → auto-enables for users who haven't set explicit preference
- Changing `metadata.keywords` → next Celery cycle uses new keywords

### Response 200
```json
{
  "id": "uuid-quantum",
  "message": "Section updated successfully"
}
```

**Side effects:** Invalidates `discovery:sections:*`, `discovery:feed:*` caches.

### 2.4 DELETE /admin/discovery/sections/{id}
**Description:** Soft delete (cascade deactivation). Subsections also deactivated.
**Auth:** Admin required

### Response 200
```json
{
  "id": "uuid-quantum",
  "message": "Section and 0 subsections deactivated"
}
```

---

## 3. Provider Management

### 3.1 GET /admin/discovery/providers
**Description:** List all providers with health stats.
**Auth:** Admin required

### Response 200
```json
{
  "providers": [
    {
      "slug": "perplexity_sonar",
      "name": "Perplexity Sonar",
      "provider_type": "sonar",
      "is_active": true,
      "is_primary": true,
      "priority": 100,
      "rate_limit_per_minute": 50,
      "rate_limit_per_day": 5000,
      "health": {
        "daily_request_count": 1847,
        "daily_remaining": 3153,
        "consecutive_errors": 0,
        "last_fetched_at": "2026-02-08T12:00:00Z",
        "status": "healthy"
      },
      "supported_sections": ["politics", "tech_science", "crypto_defi", "economy_finance", "world"],
      "config": {
        "model": "sonar",
        "search_context_size": "low",
        "temperature": 0.1,
        "max_tokens": 1024
      }
    },
    {
      "slug": "newsapi",
      "name": "NewsAPI",
      "provider_type": "api",
      "is_active": true,
      "is_primary": false,
      "priority": 50,
      "health": {
        "daily_request_count": 12,
        "daily_remaining": 9988,
        "consecutive_errors": 0,
        "last_fetched_at": "2026-02-08T11:45:00Z",
        "status": "healthy"
      }
    }
  ]
}
```

**Health status values:**
- `"healthy"` — consecutive_errors = 0, recently fetched
- `"degraded"` — 1-5 consecutive errors
- `"unhealthy"` — 6-9 consecutive errors
- `"disabled"` — ≥10 consecutive errors (circuit breaker tripped) OR is_active=false

### 3.2 PATCH /admin/discovery/providers/{slug}
**Description:** Update provider configuration.
**Auth:** Admin required

### Request Body (any subset)
```json
{
  "is_active": false,
  "rate_limit_per_minute": 30,
  "config": {"model": "sonar-pro", "search_context_size": "medium"}
}
```

**Use cases:**
- Disable a provider: `{"is_active": false}`
- Throttle: `{"rate_limit_per_minute": 20}`
- Upgrade Sonar model: `{"config": {"model": "sonar-pro"}}`
- Reset circuit breaker: `{"consecutive_errors": 0, "is_active": true}`

### Response 200
```json
{
  "slug": "perplexity_sonar",
  "message": "Provider updated successfully"
}
```

### 3.3 POST /admin/discovery/providers/{slug}/reset
**Description:** Reset error counters and re-enable provider.
**Auth:** Admin required

### Response 200
```json
{
  "slug": "perplexity_sonar",
  "consecutive_errors": 0,
  "is_active": true,
  "message": "Provider reset and re-enabled"
}
```

---

## 4. Admin Dashboard Stats (Future)

### GET /admin/discovery/stats
```json
{
  "articles": {
    "total_active": 12450,
    "collected_today": 847,
    "by_provider": {
      "perplexity_sonar": 620,
      "newsapi": 180,
      "cryptopanic": 47
    }
  },
  "graph": {
    "total_entities": 3200,
    "total_relationships": 8900,
    "entities_today": 145
  },
  "cost": {
    "sonar_requests_today": 1847,
    "estimated_daily_cost_usd": 17.60,
    "estimated_monthly_cost_usd": 528.00
  },
  "users": {
    "with_custom_interests": 340,
    "active_today": 125
  }
}
```

---

## Auth Middleware

```python
# Required role: system_admin OR content_admin
async def require_admin(user=Depends(get_current_user)):
    if user.role not in ("system_admin", "content_admin"):
        raise HTTPException(status_code=403, detail="Admin access required")
    return user
```

All admin endpoints use `Depends(require_admin)` for authorization.
