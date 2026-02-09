# Discovery Module — Document 5: API Spec — User Endpoints

## Base Path: `/api/v1/discovery`
## Auth: JWT Bearer token (optional for feed/search, required for interests)

---

## 1. GET /discovery/categories

**Description:** Returns all active discovery categories (tabs).
**Auth:** Optional (public)
**Cache:** `discovery:categories` TTL 300s
**Target:** < 100ms

### Response 200
```json
{
  "categories": [
    {
      "slug": "news",
      "name": "News",
      "icon": "newspaper",
      "sort_order": 1,
      "has_user_preferences": true
    },
    {
      "slug": "vaults",
      "name": "Today's Vaults",
      "icon": "vault",
      "sort_order": 2,
      "has_user_preferences": false
    }
  ]
}
```

---

## 2. GET /discovery/interests

**Description:** Returns the full section tree with user's enabled/disabled state.
**Auth:** Required (JWT)
**Cache:** `discovery:interests:{user_id}` TTL 120s
**Target:** < 300ms

### Response 200
```json
{
  "sections": [
    {
      "id": "uuid-politics",
      "slug": "politics",
      "name": "Politics",
      "icon": "landmark",
      "is_enabled": true,
      "subsections": [
        {
          "id": "uuid-world-affairs",
          "slug": "world_affairs",
          "name": "World Affairs",
          "is_enabled": true
        },
        {
          "id": "uuid-us-politics",
          "slug": "us_politics",
          "name": "US Politics",
          "is_enabled": true
        },
        {
          "id": "uuid-europe",
          "slug": "europe",
          "name": "Europe",
          "is_enabled": false
        }
      ]
    },
    {
      "id": "uuid-crypto",
      "slug": "crypto_defi",
      "name": "Crypto & DeFi",
      "icon": "bitcoin",
      "is_enabled": true,
      "subsections": [
        {
          "id": "uuid-bitcoin",
          "slug": "bitcoin",
          "name": "Bitcoin",
          "is_enabled": true
        },
        {
          "id": "uuid-ethereum",
          "slug": "ethereum",
          "name": "Ethereum",
          "is_enabled": true
        },
        {
          "id": "uuid-defi-protocols",
          "slug": "defi_protocols",
          "name": "DeFi Protocols",
          "is_enabled": true
        }
      ]
    }
  ]
}
```

**Logic:** If user has no explicit preference for a section → `is_enabled` = section's `is_default` value.

---

## 3. PUT /discovery/interests

**Description:** Save user's interest preferences (batch UPSERT).
**Auth:** Required (JWT)
**Target:** < 200ms

### Request Body
```json
{
  "interests": [
    {"section_id": "uuid-world-affairs", "is_enabled": true},
    {"section_id": "uuid-us-politics", "is_enabled": false},
    {"section_id": "uuid-bitcoin", "is_enabled": true},
    {"section_id": "uuid-meme-coins", "is_enabled": true}
  ]
}
```

**Validation:** 1 ≤ interests.length ≤ 200

### Response 200
```json
{
  "saved": 4,
  "message": "Interests updated successfully"
}
```

**Side effects:**
- Invalidates `discovery:interests:{user_id}` cache
- Invalidates `discovery:feed:{user_id}:*` cache (all feed pages)

---

## 4. GET /discovery/news

**Description:** Personalized news feed with three-tier fallback.
**Auth:** Optional (anonymous gets trending-only feed)
**Cache:** `discovery:feed:{user_id}:{page}:{section}` TTL 60s
**Target:** < 800ms

### Query Parameters
| Param | Type | Default | Description |
|-------|------|---------|-------------|
| page | int | 1 | Page number (≥1) |
| page_size | int | 20 | Items per page (1-50) |
| section | string | null | Filter by section slug (e.g., "crypto_defi", "bitcoin") |

### Response 200
```json
{
  "articles": [
    {
      "id": "uuid-article-1",
      "title": "Aave pauses USDT lending after oracle delay",
      "summary": "Aave governance voted to temporarily pause USDT deposits following a 2-hour Chainlink oracle delay...",
      "image_url": "https://cdn.reuters.com/article/aave-oracle.jpg",
      "source_name": "Reuters",
      "source_url": "https://reuters.com/technology/aave-oracle-2026",
      "section_slug": "defi_protocols",
      "section_name": "DeFi Protocols",
      "parent_section_slug": "crypto_defi",
      "published_at": "2026-02-08T10:30:00Z",
      "time_ago": "2h ago",
      "tags": ["aave", "oracle", "usdt", "defi"],
      "sentiment": "negative"
    },
    {
      "id": "uuid-article-2",
      "title": "Bitcoin ETF inflows hit $2.4B weekly record",
      "summary": "Spot Bitcoin ETFs saw record weekly inflows of $2.4 billion...",
      "image_url": null,
      "source_name": "Bloomberg",
      "source_url": "https://bloomberg.com/btc-etf",
      "section_slug": "bitcoin",
      "section_name": "Bitcoin",
      "parent_section_slug": "crypto_defi",
      "published_at": "2026-02-08T09:15:00Z",
      "time_ago": "3h ago",
      "tags": ["bitcoin", "etf", "institutional"],
      "sentiment": "positive"
    }
  ],
  "page": 1,
  "page_size": 20,
  "total": 20,
  "has_more": true,
  "feed_type": "personalized"
}
```

**feed_type values:**
- `"personalized"` — articles from user's enabled sections
- `"adjacent"` — mixed: user sections + sibling sections (page not fully filled)
- `"trending"` — anonymous/no-preferences, highest relevance_score globally

**Feed algorithm:**
1. Get user's enabled section IDs
2. If section filter → narrow to that section's children
3. Fetch from enabled sections (personalized)
4. If < page_size → fill with adjacent (sibling sections under same parent)
5. If still < page_size → fill with trending (global top by relevance_score)

---

## 5. GET /discovery/news/search

**Description:** Hybrid search combining cached DB results + real-time Perplexity Sonar.
**Auth:** Optional
**Cache:** `discovery:search:{query_hash}` TTL 30s
**Target:** < 2s

### Query Parameters
| Param | Type | Default | Description |
|-------|------|---------|-------------|
| q | string | required | Search query (2-200 chars) |
| page | int | 1 | Page number |
| page_size | int | 20 | Items per page (1-50) |
| section | string | null | Filter by section slug |

### Response 200
Same schema as GET /discovery/news, with `feed_type: "search"`.

**Search algorithm:**
1. **Parallel** via asyncio.gather:
   - Task 1: PostgreSQL full-text search (GIN index, cached articles)
   - Task 2: Perplexity Sonar real-time search (fresh web results)
2. Merge: DB results first (fast/trusted), then Sonar results (fresh/new)
3. Dedup by content_hash — skip articles already in DB results
4. Sonar-only results get temporary IDs: `"sonar-{hash[:12]}"`

---

## 6. GET /discovery/vaults

**Description:** Today's DeFi vault opportunities.
**Auth:** Optional (public)
**Cache:** `discovery:vaults:{sort}:{chain}` TTL 60s
**Target:** < 400ms

### Query Parameters
| Param | Type | Default | Description |
|-------|------|---------|-------------|
| sort | string | "apy_desc" | Sort: `apy_desc`, `tvl_desc`, `risk_asc` |
| chain | string | null | Filter by chain: "base", "ethereum", etc. |
| asset | string | null | Filter by asset: "USDC", "ETH", etc. |

### Response 200
```json
{
  "vaults": [
    {
      "id": "uuid-vault-1",
      "protocol": "morpho",
      "protocol_display": "Morpho",
      "vault_name": "Morpho USDC",
      "chain": "base",
      "chain_name": "Base",
      "asset_symbol": "USDC",
      "supply_apy": 8.5200,
      "reward_apy": 2.1000,
      "total_apy": 10.6200,
      "tvl_usd": "45230000.00",
      "risk_level": "low",
      "is_curated": true,
      "cta": "Deposit USDC to earn 10.6% APY",
      "intent_trigger": "lending_deposit"
    },
    {
      "id": "uuid-vault-2",
      "protocol": "aave-v3",
      "protocol_display": "Aave V3",
      "vault_name": "Aave V3 ETH",
      "chain": "ethereum",
      "chain_name": "Ethereum",
      "asset_symbol": "ETH",
      "supply_apy": 3.2100,
      "reward_apy": 0.0000,
      "total_apy": 3.2100,
      "tvl_usd": "1250000000.00",
      "risk_level": "low",
      "is_curated": true,
      "cta": "Deposit ETH to earn 3.2% APY",
      "intent_trigger": "lending_deposit"
    }
  ],
  "updated_at": "2026-02-08T12:05:00Z"
}
```

**`intent_trigger`** — when user taps a vault card, the mobile app sends this intent to the Anvil agent squad to initiate a lending deposit flow.

---

## Error Responses

### 400 Bad Request
```json
{"detail": "Search query must be between 2 and 200 characters"}
```

### 401 Unauthorized (interests endpoints)
```json
{"detail": "Not authenticated"}
```

### 422 Validation Error
```json
{
  "detail": [
    {
      "loc": ["body", "interests"],
      "msg": "ensure this value has at least 1 items",
      "type": "value_error"
    }
  ]
}
```

### 503 Service Unavailable (search when all providers down)
```json
{"detail": "News search temporarily unavailable. Please try again."}
```
