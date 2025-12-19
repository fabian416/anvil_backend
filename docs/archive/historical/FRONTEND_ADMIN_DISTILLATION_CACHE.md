# FRONTEND_ADMIN_DISTILLATION_CACHE

## Admin Distillation Cache Management Module

**User Type:** Admin  
**Module:** Cache Management  
**Route:** `/admin/distillation/cache`  
**Access Level:** Full CRUD (Admin) | Read-Only (Operator)

---

## 📋 Module Overview

### Title
**Cache Management** - Response Cache Control

### Description
Management interface for the semantic and exact-match response cache. Enables administrators to view cached responses, configure cache policies, manually invalidate entries, and monitor cache effectiveness.

### Key Capabilities
- View cached responses with metadata
- Configure TTL and eviction policies
- Manual cache invalidation
- Semantic similarity tuning
- Cache warming capabilities
- Performance monitoring

---

## 👤 User Stories

### US-ADMIN-CACHE-001: View Cache Contents
**As a** platform administrator  
**I want to** see what's in the cache  
**So that** I understand cached responses

### US-ADMIN-CACHE-002: Configure Cache Policies
**As a** platform administrator  
**I want to** set cache TTL and size limits  
**So that** cache stays fresh and efficient

### US-ADMIN-CACHE-003: Invalidate Cache Entries
**As a** platform administrator  
**I want to** remove specific entries  
**So that** outdated responses aren't served

### US-ADMIN-CACHE-004: Monitor Cache Performance
**As a** platform administrator  
**I want to** see hit/miss rates  
**So that** I can optimize cache effectiveness

---

## 🖼️ Views & Wireframes

### View 1: Cache Dashboard

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│  💾 Cache Management                              [🧹 Clear All] [⚙️ Configure]     │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                      │
│  ┌─ Cache Stats ───────────────────────────────────────────────────────────────────┐│
│  │  📊 4,521 Entries    💾 124 MB / 500 MB    🎯 32% Hit Rate    ⏱️ Avg: 8ms      ││
│  │     1,205 exact         25% capacity         12% exact / 20% semantic          ││
│  │     3,316 semantic                                                              ││
│  └─────────────────────────────────────────────────────────────────────────────────┘│
│                                                                                      │
│  ┌─ Filters ───────────────────────────────────────────────────────────────────────┐│
│  │ Type: [All ▼]    Intent: [All ▼]    Age: [All ▼]    [🔍 Search queries...]     ││
│  └─────────────────────────────────────────────────────────────────────────────────┘│
│                                                                                      │
│  ┌─────────────────────────────────────────────────────────────────────────────────┐│
│  │ □ │ QUERY                          │ TYPE     │ HITS │ AGE    │ EXPIRES │ SIZE ││
│  ├───┼────────────────────────────────┼──────────┼──────┼────────┼─────────┼──────┤│
│  │ □ │ what's the price of eth        │ 📌 Exact │ 2,450│ 2h     │ 4h      │ 1.2KB││
│  │ □ │ ethereum price now             │ 🔗 Sem   │ 1,820│ 2h     │ 4h      │ 1.2KB││
│  │ □ │ how much is ETH                │ 🔗 Sem   │ 945  │ 2h     │ 4h      │ 1.2KB││
│  │ □ │ current gas fees               │ 📌 Exact │ 890  │ 30m    │ 1h      │ 0.8KB││
│  │ □ │ gas price ethereum             │ 🔗 Sem   │ 672  │ 30m    │ 1h      │ 0.8KB││
│  │ □ │ what is aave                   │ 📌 Exact │ 542  │ 2d     │ 5d      │ 3.2KB││
│  │ □ │ explain aave protocol          │ 🔗 Sem   │ 423  │ 2d     │ 5d      │ 3.2KB││
│  │ □ │ my wallet balance              │ 📌 Exact │ 312  │ 5m     │ 15m     │ 0.5KB││
│  └───┴────────────────────────────────┴──────────┴──────┴────────┴─────────┴──────┘│
│                                                                                      │
│  ┌─ Selected: 0 ───────────────────────────────────────────────────────────────────┐│
│  │ [Select All]  [🗑️ Invalidate Selected]  [📤 Export]                            ││
│  └─────────────────────────────────────────────────────────────────────────────────┘│
│                                                                                      │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

### View 2: Cache Entry Detail

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│  💾 Cache Entry: "what's the price of eth"                                  [✕]     │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                      │
│  ENTRY METADATA                                                                     │
│  ┌───────────────────────────────────────────────────────────────────────────────┐  │
│  │  Cache Key: price_eth_exact_v2_abc123def                                     │  │
│  │  Type: Exact Match                                                            │  │
│  │  Created: Dec 1, 2025, 12:32:15 PM                                           │  │
│  │  Expires: Dec 1, 2025, 4:32:15 PM (4h TTL)                                   │  │
│  │  Hits: 2,450                                                                  │  │
│  │  Size: 1.2 KB                                                                 │  │
│  └───────────────────────────────────────────────────────────────────────────────┘  │
│                                                                                      │
│  CACHED RESPONSE                                                                    │
│  ┌───────────────────────────────────────────────────────────────────────────────┐  │
│  │  The current price of ETH is $2,145.32 (+2.3% 24h).                          │  │
│  │                                                                               │  │
│  │  Data source: CoinGecko                                                       │  │
│  │  Last updated: 2 hours ago                                                    │  │
│  └───────────────────────────────────────────────────────────────────────────────┘  │
│                                                                                      │
│  SEMANTIC VARIANTS (linked entries)                                                 │
│  ┌───────────────────────────────────────────────────────────────────────────────┐  │
│  │  • "ethereum price now" (similarity: 0.94) - 1,820 hits                      │  │
│  │  • "how much is ETH" (similarity: 0.91) - 945 hits                           │  │
│  │  • "ETH USD price" (similarity: 0.89) - 234 hits                             │  │
│  │  • "what is eth worth" (similarity: 0.87) - 156 hits                         │  │
│  └───────────────────────────────────────────────────────────────────────────────┘  │
│                                                                                      │
│  ─────────────────────────────────────────────────────────────────────────────────  │
│                                                                                      │
│  [🗑️ Invalidate This Entry]    [🔗 Invalidate All Variants]    [Close]             │
│                                                                                      │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

### View 3: Cache Configuration

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│  ⚙️ Cache Configuration                                                     [✕]     │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                      │
│  CACHE LIMITS                                                                       │
│  ┌───────────────────────────────────────────────────────────────────────────────┐  │
│  │                                                                               │  │
│  │  Maximum Cache Size                                                          │  │
│  │  ┌─────────────────────────────────────────────────────────────────────────┐  │  │
│  │  │ [500        ] MB                                   Current: 124 MB      │  │  │
│  │  └─────────────────────────────────────────────────────────────────────────┘  │  │
│  │                                                                               │  │
│  │  Maximum Entries                                                             │  │
│  │  ┌─────────────────────────────────────────────────────────────────────────┐  │  │
│  │  │ [50000      ]                                      Current: 4,521       │  │  │
│  │  └─────────────────────────────────────────────────────────────────────────┘  │  │
│  │                                                                               │  │
│  │  Eviction Policy                                                             │  │
│  │  ┌─────────────────────────────────────────────────────────────────────────┐  │  │
│  │  │ [●] LRU (Least Recently Used)  [ ] LFU (Least Frequently Used)         │  │  │
│  │  └─────────────────────────────────────────────────────────────────────────┘  │  │
│  │                                                                               │  │
│  └───────────────────────────────────────────────────────────────────────────────┘  │
│                                                                                      │
│  TTL SETTINGS (by intent)                                                           │
│  ┌───────────────────────────────────────────────────────────────────────────────┐  │
│  │                                                                               │  │
│  │  Intent               │ Default TTL   │ Notes                                │  │
│  │  ────────────────────────────────────────────────────────────────────────── │  │
│  │  price_check          │ [4h     ▼]    │ Prices update frequently            │  │
│  │  gas_check            │ [1h     ▼]    │ Gas prices volatile                 │  │
│  │  balance_check        │ [15m    ▼]    │ Balances change often               │  │
│  │  explain_concept      │ [7d     ▼]    │ Concepts don't change               │  │
│  │  greeting             │ [24h    ▼]    │ Static responses                    │  │
│  │  default              │ [4h     ▼]    │ Fallback TTL                        │  │
│  │                                                                               │  │
│  └───────────────────────────────────────────────────────────────────────────────┘  │
│                                                                                      │
│  SEMANTIC MATCHING                                                                  │
│  ┌───────────────────────────────────────────────────────────────────────────────┐  │
│  │                                                                               │  │
│  │  Similarity Threshold                                                        │  │
│  │  ┌─────────────────────────────────────────────────────────────────────────┐  │  │
│  │  │     |─────────────────────●────────────|              0.85              │  │  │
│  │  │     0.7                                1.0                              │  │  │
│  │  └─────────────────────────────────────────────────────────────────────────┘  │  │
│  │  Higher = stricter matching, Lower = more cache hits                         │  │
│  │                                                                               │  │
│  └───────────────────────────────────────────────────────────────────────────────┘  │
│                                                                                      │
│  ─────────────────────────────────────────────────────────────────────────────────  │
│                                                                                      │
│  [Reset to Defaults]                               [Cancel]        [Save Changes]   │
│                                                                                      │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 🔌 API Endpoints

### Get Cache Stats

```typescript
// GET /admin/distillation/cache/stats
interface GetCacheStatsResponse {
  success: true;
  data: {
    total_entries: number;
    exact_entries: number;
    semantic_entries: number;
    size_bytes: number;
    max_size_bytes: number;
    hit_rate_exact: number;
    hit_rate_semantic: number;
    hit_rate_combined: number;
    avg_lookup_ms: number;
    oldest_entry_age_hours: number;
  };
}
```

### List Cache Entries

```typescript
// GET /admin/distillation/cache/entries
interface GetCacheEntriesResponse {
  success: true;
  data: {
    entries: CacheEntry[];
    pagination: Pagination;
  };
}

interface CacheEntry {
  id: string;
  query: string;
  cache_type: 'exact' | 'semantic';
  response_preview: string;
  hits: number;
  created_at: string;
  expires_at: string;
  size_bytes: number;
  intent?: string;
  linked_entries?: string[];
}
```

### Invalidate Cache

```typescript
// DELETE /admin/distillation/cache/entries
interface InvalidateCacheRequest {
  entry_ids?: string[];
  query_pattern?: string;
  intent?: string;
  older_than_hours?: number;
  all?: boolean;
}
```

### Update Cache Config

```typescript
// PUT /admin/distillation/cache/config
interface UpdateCacheConfigRequest {
  max_size_mb?: number;
  max_entries?: number;
  eviction_policy?: 'lru' | 'lfu';
  semantic_threshold?: number;
  ttl_by_intent?: Record<string, number>;
}
```

---

## 🎬 Motion Design

```typescript
const cacheAnimations = {
  entrySelect: {
    backgroundColor: 'rgba(59, 130, 246, 0.1)',
    transition: { duration: 0.15 }
  },
  
  invalidateProgress: {
    width: '100%',
    transition: { duration: 0.5 }
  },
  
  hitCountIncrement: {
    scale: [1, 1.1, 1],
    color: ['#fff', '#10B981', '#fff'],
    transition: { duration: 0.3 }
  }
};
```

---

*Document Version: 1.0*  
*Last Updated: December 1, 2025*  
*Module: Cache Management*
