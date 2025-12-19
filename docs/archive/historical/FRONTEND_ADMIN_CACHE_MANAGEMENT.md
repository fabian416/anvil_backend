# FRONTEND_ADMIN_CACHE_MANAGEMENT

## Admin Cache Management Module

**User Type:** Admin  
**Module:** Cache & Performance Management  
**Route:** `/admin/cache`  
**Platform:** Web (Admin Panel)  
**Version:** 1.0

---

## 📋 Module Overview

### Title
**Cache Management** - Redis Cache Control & Performance Monitoring

### Description
Administrative interface for managing Redis cache layers, monitoring hit rates, invalidating stale data, and optimizing query performance across GraphRAG, ML, and API layers.

### Key Capabilities
- Cache statistics visualization
- Cache invalidation controls
- Hit rate monitoring
- Memory usage tracking
- Key pattern analysis
- Performance optimization
- Automated cache warming
- TTL management

---

## 🖼️ Wireframes

### View 1: Cache Dashboard

```
┌─────────────────────────────────────────────────────────────┐
│  [←] Admin Home       Cache Management         [Refresh]    │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Cache Overview                            🟢 Healthy      │
│  ┌─────────────────────────────────────────────────────────┐│
│  │  Total Keys:        124,567                            ││
│  │  Memory Used:       2.4 GB / 8 GB  (30%)               ││
│  │  Hit Rate:          82.5% ████████░░  (Target: >70%)   ││
│  │  Miss Rate:         17.5%                              ││
│  │  Evictions:         1,234 (last 24h)                   ││
│  │  Avg Response:      3.2ms                              ││
│  └─────────────────────────────────────────────────────────┘│
│                                                             │
│  Cache Layers                                               │
│  ┌─────────────────────────────────────────────────────────┐│
│  │  🔷 GraphRAG Query Cache              Hit: 85% 🟢      ││
│  │     Keys: 45,234  |  Mem: 850 MB  |  TTL: 5 min       ││
│  │     [View Details] [Invalidate] [Warm Cache]          ││
│  ├─────────────────────────────────────────────────────────┤│
│  │  🧠 ML Prediction Cache               Hit: 78% 🟢      ││
│  │     Keys: 28,567  |  Mem: 420 MB  |  TTL: 15 min      ││
│  │     [View Details] [Invalidate] [Warm Cache]          ││
│  ├─────────────────────────────────────────────────────────┤│
│  │  📊 Protocol Data Cache               Hit: 92% 🟢      ││
│  │     Keys: 12,456  |  Mem: 320 MB  |  TTL: 1 hour      ││
│  │     [View Details] [Invalidate] [Warm Cache]          ││
│  ├─────────────────────────────────────────────────────────┤│
│  │  🔗 API Response Cache                Hit: 75% 🟡      ││
│  │     Keys: 38,310  |  Mem: 810 MB  |  TTL: varies      ││
│  │     [View Details] [Invalidate] [Warm Cache]          ││
│  └─────────────────────────────────────────────────────────┘│
│                                                             │
│  Quick Actions                                              │
│  ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌─────────┐ │
│  │  Clear All │ │   Warm     │ │  Optimize  │ │  Export │ │
│  │   Expired  │ │   Common   │ │    TTLs    │ │  Stats  │ │
│  └────────────┘ └────────────┘ └────────────┘ └─────────┘ │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### View 2: Cache Layer Details

```
┌─────────────────────────────────────────────────────────────┐
│  [←] Cache Management    GraphRAG Query Cache Details       │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  GraphRAG Query Cache                         🟢 Performing │
│                                                             │
│  Statistics (Last 24h)                                      │
│  ┌─────────────────────────────────────────────────────────┐│
│  │  Hit Rate Trend                                         ││
│  │  100%┤                                                  ││
│  │   90%┤        ╭────────╮                                ││
│  │   80%┤    ╭───╯        ╰───╮                            ││
│  │   70%┤────╯                ╰────                        ││
│  │   60%┼──────────────────────────────────────────▶      ││
│  │       0h    6h    12h   18h   24h                      ││
│  │                                                         ││
│  │  Current: 85%  |  Avg: 83%  |  Best: 92%              ││
│  └─────────────────────────────────────────────────────────┘│
│                                                             │
│  Top Cached Queries                                         │
│  ┌─────────────────────────────────────────────────────────┐│
│  │  Query Pattern              Hits    Hit %   Mem         ││
│  │  ──────────────────────────────────────────────────     ││
│  │  "safe staking protocols"   1,234   95%    12 MB       ││
│  │  "aave risk analysis"         856   92%     8 MB       ││
│  │  "similar to compound"        645   88%     6 MB       ││
│  │  "ethereum lending"           523   85%     5 MB       ││
│  │  ... 20 more                                            ││
│  │                                                         ││
│  │  [Export Top 100] [Clear Pattern]                      ││
│  └─────────────────────────────────────────────────────────┘│
│                                                             │
│  Configuration                                              │
│  ┌─────────────────────────────────────────────────────────┐│
│  │  Default TTL:       [300 seconds ▼]  (5 minutes)       ││
│  │  Max Keys:          [50000 ▼]                          ││
│  │  Eviction Policy:   [LRU ▼]                            ││
│  │  Auto-Invalidate:   ☑ On protocol updates              ││
│  │  Cache Warming:     ☑ Enabled (top 100 queries)        ││
│  │                                                         ││
│  │  [Save Configuration]                                   ││
│  └─────────────────────────────────────────────────────────┘│
│                                                             │
│  [Invalidate Layer] [Warm Top Queries] [Back]              │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### View 3: Cache Key Browser

```
┌─────────────────────────────────────────────────────────────┐
│  [←] Cache Management    Key Browser                        │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Search Keys                                                │
│  ┌─────────────────────────────────────────────────────────┐│
│  │  Pattern: [graphrag:*          ]  [Search]             ││
│  └─────────────────────────────────────────────────────────┘│
│                                                             │
│  Results (125 keys matching pattern)                        │
│  ┌─────────────────────────────────────────────────────────┐│
│  │  Key                           Size    TTL      Actions ││
│  │  ────────────────────────────────────────────────────   ││
│  │  graphrag:query:hash123        45 KB   4m 23s  [Del]   ││
│  │  graphrag:query:hash456        38 KB   2m 15s  [Del]   ││
│  │  graphrag:result:abc123       120 KB   1m 45s  [Del]   ││
│  │  graphrag:embedding:xyz789     15 KB   9m 12s  [Del]   ││
│  │  ... 121 more                                           ││
│  │                                                         ││
│  │  [Select All] [Delete Selected] [Export List]          ││
│  └─────────────────────────────────────────────────────────┘│
│                                                             │
│  Key Details (graphrag:query:hash123)                       │
│  ┌─────────────────────────────────────────────────────────┐│
│  │  Created:     2 hours ago                               ││
│  │  Last Access: 15 seconds ago                            ││
│  │  Hit Count:   23                                        ││
│  │  Size:        45 KB                                     ││
│  │  TTL:         4m 23s remaining                          ││
│  │  Type:        String (JSON)                             ││
│  │                                                         ││
│  │  Value Preview:                                         ││
│  │  {                                                      ││
│  │    "query": "safe staking protocols",                  ││
│  │    "results": [...],                                   ││
│  │    "cached_at": "2025-12-01T10:23:45Z"                 ││
│  │  }                                                      ││
│  │                                                         ││
│  │  [View Full Value] [Update TTL] [Delete Key]           ││
│  └─────────────────────────────────────────────────────────┘│
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 🔌 Admin API Endpoints

### Get Cache Statistics

```typescript
// GET /api/v1/admin/cache/stats
interface CacheStatsResponse {
  global: {
    total_keys: number;
    memory_used_bytes: number;
    memory_limit_bytes: number;
    hit_rate: number;
    miss_rate: number;
    evictions_24h: number;
    avg_response_time_ms: number;
  };
  layers: Array<{
    layer_name: string;
    key_count: number;
    memory_bytes: number;
    hit_rate: number;
    default_ttl_seconds: number;
    top_patterns: string[];
  }>;
}
```

### Invalidate Cache Layer

```typescript
// DELETE /api/v1/admin/cache/layer/:layer_name
interface InvalidateCacheRequest {
  pattern?: string;  // Optional: invalidate only matching keys
  confirm: boolean;  // Required: must be true
}

interface InvalidateCacheResponse {
  success: boolean;
  keys_deleted: number;
  memory_freed_bytes: number;
}
```

### Warm Cache

```typescript
// POST /api/v1/admin/cache/warm
interface WarmCacheRequest {
  layer: string;
  queries?: string[];  // Specific queries to warm
  top_n?: number;      // Or warm top N popular queries
}

interface WarmCacheResponse {
  success: boolean;
  queries_warmed: number;
  estimated_time_seconds: number;
}
```

### Get Top Cached Queries

```typescript
// GET /api/v1/admin/cache/layer/:layer_name/top-queries?limit=100
interface TopQueriesResponse {
  queries: Array<{
    pattern: string;
    hit_count: number;
    hit_rate: number;
    memory_bytes: number;
    avg_response_time_ms: number;
  }>;
  total_queries: number;
}
```

---

## 🎨 Component Specifications

```typescript
interface CacheDashboardProps {
  refreshInterval?: number;
}

interface CacheLayerCardProps {
  layer: CacheLayer;
  onViewDetails: () => void;
  onInvalidate: () => void;
  onWarmCache: () => void;
}

interface CacheStatsChartProps {
  stats: CacheStats[];
  metric: 'hit_rate' | 'memory' | 'keys';
  timeRange: '1h' | '24h' | '7d';
}

interface KeyBrowserProps {
  pattern: string;
  onPatternChange: (pattern: string) => void;
  onDeleteKey: (key: string) => void;
}
```

---

## ⚠️ Error Handling

```typescript
const cacheErrors = {
  CACHE_001: 'Failed to fetch cache statistics',
  CACHE_002: 'Invalidation requires confirmation',
  CACHE_003: 'Cache warming already in progress',
  CACHE_004: 'Invalid cache layer name',
  CACHE_005: 'Pattern too broad (would delete >10k keys)',
};
```

---

*Document Version: 1.0*  
*Last Updated: December 1, 2025*  
*Module: Cache Management*
