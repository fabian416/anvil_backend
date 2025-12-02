# FRONTEND_ADMIN_GRAPHRAG_DASHBOARD

## Admin GraphRAG Management Module

**User Type:** Admin  
**Module:** GraphRAG System Administration  
**Route:** `/admin/graphrag`  
**Platform:** Web (Admin Panel)  
**Version:** 1.0 - Platform Management

---

## 📋 Module Overview

### Title
**GraphRAG Admin** - Knowledge Graph Management

### Description
Administrative control panel for managing the GraphRAG system, including graph data quality, embeddings generation, query performance monitoring, and cache management.

### Key Capabilities
- Graph integrity validation
- Embedding generation & management
- Query performance monitoring
- Cache statistics & control
- Protocol data management
- Relationship validation
- Search quality metrics
- System health monitoring

---

## 👤 Admin User Stories

### AS-ADMIN-GRAPHRAG-001: Monitor Graph Health
**As an** admin  
**I want to** monitor graph data quality  
**So that** I can ensure system reliability

**Acceptance Criteria:**
- Overall health score displayed
- Issue count by severity
- Quick fix actions
- Historical trends

---

### AS-ADMIN-GRAPHRAG-002: Manage Embeddings
**As an** admin  
**I want to** generate and update protocol embeddings  
**So that** search quality remains high

**Acceptance Criteria:**
- Trigger embedding generation
- View generation progress
- See embedding coverage
- Regenerate failed embeddings

---

### AS-ADMIN-GRAPHRAG-003: Monitor Performance
**As an** admin  
**I want to** track query performance metrics  
**So that** I can optimize the system

**Acceptance Criteria:**
- Average query latency
- Cache hit rate
- Popular queries
- Slow query log

---

## 🖼️ Wireframes

### View 1: GraphRAG Dashboard Overview

```
┌─────────────────────────────────────────────────────────────┐
│  [←] Admin Home          GraphRAG Dashboard      [Refresh] │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  System Health                                 🟢 Excellent │
│  ┌─────────────────────────────────────────────────────────┐│
│  │  Graph Integrity:        ✅ 98%         [Validate]     ││
│  │  Embedding Coverage:     ✅ 96%         [Generate]     ││
│  │  Cache Hit Rate:         ✅ 78%         [View]         ││
│  │  Avg Query Latency:      ✅ 145ms       [Analyze]      ││
│  └─────────────────────────────────────────────────────────┘│
│                                                             │
│  ⚠️ Active Issues (3)                          [View All →] │
│  ┌─────────────────────────────────────────────────────────┐│
│  │  🟡 MEDIUM: 5 protocols missing embeddings              ││
│  │     Affected: Protocol A, Protocol B, ...               ││
│  │     [Generate Embeddings] [View Details]                ││
│  ├─────────────────────────────────────────────────────────┤│
│  │  🟢 LOW: 12 protocols missing optional properties       ││
│  │     Impact: Minor                                       ││
│  │     [Update Properties] [Ignore]                        ││
│  └─────────────────────────────────────────────────────────┘│
│                                                             │
│  Quick Actions                                              │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐        │
│  │   Validate   │ │   Generate   │ │   Clear      │        │
│  │    Graph     │ │  Embeddings  │ │   Cache      │        │
│  └──────────────┘ └──────────────┘ └──────────────┘        │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐        │
│  │   Import     │ │   Export     │ │   Backup     │        │
│  │    Data      │ │    Data      │ │    Graph     │        │
│  └──────────────┘ └──────────────┘ └──────────────┘        │
│                                                             │
│  ┌───────────────────────────────┬───────────────────────┐ │
│  │  Graph Statistics             │  Query Performance    │ │
│  │                               │                       │ │
│  │  Total Protocols:   450       │  Queries Today: 1,234 │ │
│  │  Total Tokens:      1,250     │  Avg Latency:   145ms │ │
│  │  Total Chains:      15        │  Cache Hits:    78%   │ │
│  │  Relationships:     3,500     │  Errors:        2     │ │
│  │  Last Updated:      2 min ago │  Slow Queries:  5     │ │
│  │                               │                       │ │
│  │  [View Details →]             │  [View Metrics →]     │ │
│  └───────────────────────────────┴───────────────────────┘ │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

### View 2: Embedding Management

```
┌─────────────────────────────────────────────────────────────┐
│  [←] GraphRAG Dashboard      Embedding Management           │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Embedding Coverage                                    96%  │
│  ┌─────────────────────────────────────────────────────────┐│
│  │  ████████████████████████████████████████░░░░░░        ││
│  │                                                         ││
│  │  Generated:  432 / 450 protocols                        ││
│  │  Missing:    18 protocols                               ││
│  │  Failed:     5 protocols                                ││
│  │  Model:      text-embedding-3-small                     ││
│  │  Last Run:   2 hours ago                                ││
│  └─────────────────────────────────────────────────────────┘│
│                                                             │
│  ┌─────────────────────────────────────────────────────────┐│
│  │  [Generate Missing] [Regenerate Failed] [Regenerate All]││
│  └─────────────────────────────────────────────────────────┘│
│                                                             │
│  Missing Embeddings (18)                                    │
│  ┌─────────────────────────────────────────────────────────┐│
│  │  ☐ Protocol Alpha          Category: Lending            ││
│  │     Reason: Recently added                              ││
│  │  ☐ Protocol Beta           Category: DEX                ││
│  │     Reason: Generation failed                           ││
│  │  ☐ Protocol Gamma          Category: Staking            ││
│  │     Reason: Insufficient data                           ││
│  │  ... 15 more                                            ││
│  │                                                         ││
│  │  [Select All] [Generate Selected (0)]                   ││
│  └─────────────────────────────────────────────────────────┘│
│                                                             │
│  Failed Embeddings (5)                                      │
│  ┌─────────────────────────────────────────────────────────┐│
│  │  Protocol Delta           Error: API rate limit         ││
│  │  [Retry] [View Logs]                                    ││
│  │  ─────────────────────────────────────────────────────  ││
│  │  Protocol Epsilon         Error: Invalid description    ││
│  │  [Fix Data] [Retry]                                     ││
│  │  ... 3 more                                             ││
│  └─────────────────────────────────────────────────────────┘│
│                                                             │
│  Embedding Statistics                                       │
│  • Avg generation time: 1.2s per protocol                   │
│  • Total vectors: 432 (384 dimensions each)                 │
│  • Storage used: 125 MB                                     │
│  • Cost this month: $12.50                                  │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

### View 3: Cache Management

```
┌─────────────────────────────────────────────────────────────┐
│  [←] GraphRAG Dashboard      Cache Management               │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Cache Performance                              🟢 Excellent│
│  ┌─────────────────────────────────────────────────────────┐│
│  │  Hit Rate:         78%  ████████████████░░░░░░          ││
│  │  Miss Rate:        22%  █████░░░░░░░░░░░░░░░░           ││
│  │  Total Hits:       15,420                               ││
│  │  Total Misses:     4,350                                ││
│  │  Avg Latency:                                           ││
│  │    • Cached:       8.5ms                                ││
│  │    • Uncached:     145.2ms                              ││
│  │  Cache Size:       128.5 MB / 256 MB (50%)              ││
│  │  Evictions:        450 this week                        ││
│  └─────────────────────────────────────────────────────────┘│
│                                                             │
│  ┌───────────────────┬─────────────────────────────────────┐│
│  │  [Clear All]      │  [Clear Expired]  [Optimize]       ││
│  └───────────────────┴─────────────────────────────────────┘│
│                                                             │
│  Most Cached Queries (Last 24h)                             │
│  ┌─────────────────────────────────────────────────────────┐│
│  │  #1  "safe staking protocols"                           ││
│  │       Hits: 234  |  Avg: 7ms  |  [Clear]                ││
│  │  #2  "lending platforms ethereum"                       ││
│  │       Hits: 187  |  Avg: 9ms  |  [Clear]                ││
│  │  #3  "high yield defi"                                  ││
│  │       Hits: 156  |  Avg: 8ms  |  [Clear]                ││
│  │  #4  "dex arbitrum"                                     ││
│  │       Hits: 142  |  Avg: 7ms  |  [Clear]                ││
│  │  #5  "liquid staking"                                   ││
│  │       Hits: 128  |  Avg: 8ms  |  [Clear]                ││
│  │                                                         ││
│  │  [View All →]                                           ││
│  └─────────────────────────────────────────────────────────┘│
│                                                             │
│  Cache Keys by Type                                         │
│  • Search queries:      1,234 keys (45 MB)                  │
│  • Protocol details:    450 keys (28 MB)                    │
│  • Graph traversals:    892 keys (35 MB)                    │
│  • Similarity searches: 345 keys (20 MB)                    │
│                                                             │
│  Eviction Policy: LRU (Least Recently Used)                 │
│  TTL: 5 minutes (queries), 1 hour (details)                 │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 🔌 Admin API Endpoints

### Validate Graph Integrity

```typescript
// POST /api/v1/graph/validate
interface ValidationResponse {
  is_valid: boolean;
  issues: Array<{
    issue_type: string;
    severity: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
    count: number;
    details: string;
    affected_entities: string[];
  }>;
  summary: {
    total_issues: number;
    critical_issues: number;
    warnings: number;
  };
}
```

### Generate Embeddings

```typescript
// POST /api/v1/graph/generate-embeddings
interface GenerateEmbeddingsRequest {
  protocol_ids?: string[]; // Optional: specific protocols
  force_regenerate?: boolean;
}

interface GenerateEmbeddingsResponse {
  generated: number;
  updated: number;
  failed: number;
  total_processed: number;
  processing_time_seconds: number;
  errors?: Array<{
    protocol_id: string;
    protocol_name: string;
    error: string;
  }>;
}
```

### Get Cache Statistics

```typescript
// GET /api/v1/graph/monitoring/cache-stats
interface CacheStatsResponse {
  hit_rate: number; // 0-1
  miss_rate: number; // 0-1
  total_hits: number;
  total_misses: number;
  avg_latency_cached_ms: number;
  avg_latency_uncached_ms: number;
  cache_size_mb: number;
  cache_max_mb: number;
  evictions: number;
  top_queries: Array<{
    query: string;
    hits: number;
    avg_latency_ms: number;
  }>;
}
```

### Clear Cache

```typescript
// DELETE /api/v1/graph/monitoring/cache
interface ClearCacheRequest {
  clear_all?: boolean;
  clear_expired?: boolean;
  clear_pattern?: string; // e.g., "search:*"
}

interface ClearCacheResponse {
  success: boolean;
  keys_deleted: number;
  message: string;
}
```

### Get Graph Analytics

```typescript
// GET /api/v1/graph/analytics
interface GraphAnalyticsResponse {
  overview: {
    total_protocols: number;
    total_tokens: number;
    total_chains: number;
    total_relationships: number;
    last_updated: string;
  };
  top_protocols_by_tvl: Array<{
    protocol_id: string;
    protocol_name: string;
    tvl: number;
    category: string;
  }>;
  category_distribution: Record<string, number>;
  chain_distribution: Record<string, number>;
  risk_summary: {
    average_risk: number;
    low_risk_count: number;
    medium_risk_count: number;
    high_risk_count: number;
    critical_risk_count: number;
  };
}
```

---

## 🎨 Component Specifications

```typescript
interface GraphRAGDashboardProps {
  refreshInterval?: number; // Auto-refresh (ms)
}

interface GraphHealthIndicatorProps {
  healthScore: number; // 0-100
  issues: Issue[];
}

interface EmbeddingProgressProps {
  total: number;
  generated: number;
  failed: number;
  onGenerate: () => void;
}

interface CacheStatsDisplayProps {
  stats: CacheStatsResponse;
  onClear: (options: ClearCacheRequest) => void;
}

interface QueryPerformanceChartProps {
  metrics: Array<{
    timestamp: string;
    latency_ms: number;
    cache_hit: boolean;
  }>;
  timeRange: '1h' | '24h' | '7d' | '30d';
}
```

---

## ⚠️ Error Handling

```typescript
const adminErrors = {
  ADMIN_001: 'Insufficient permissions (admin required)',
  ADMIN_002: 'Validation failed',
  ADMIN_003: 'Embedding generation failed',
  ADMIN_004: 'Cache clear failed',
  
  GRAPH_001: 'Graph data corrupted',
  GRAPH_002: 'Unable to connect to graph database',
  
  EMBED_001: 'OpenAI API error',
  EMBED_002: 'Rate limit exceeded',
  EMBED_003: 'Invalid protocol data',
};
```

---

## 🔒 Security & Permissions

**Admin-Only Access**:
- All endpoints require `admin` role
- User scope validation enforced
- Audit logging for all actions
- Rate limiting (stricter for admins)

**Dangerous Operations**:
- Clear cache: Requires confirmation
- Regenerate all: Requires confirmation
- Export data: Logged and monitored

---

## 📊 Monitoring Metrics

**Health Indicators**:
- Graph integrity: >95% healthy
- Embedding coverage: >90% generated
- Cache hit rate: >70% optimal
- Query latency: <200ms average

**Alerts**:
- Critical issues detected
- Embedding generation failures
- High query latency (>500ms)
- Low cache hit rate (<50%)
- Graph validation failures

---

*Document Version: 1.0*  
*Last Updated: December 1, 2025*  
*Module: Admin GraphRAG Management*
