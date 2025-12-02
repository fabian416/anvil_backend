# FRONTEND_ADMIN_DISTILLATION_DASHBOARD

## Admin Distillation Dashboard Module

**User Type:** Admin / Operator  
**Module:** Distillation Dashboard  
**Route:** `/admin/distillation`  
**Access Level:** View (All) | Configure (Admin)

---

## 📋 Module Overview

### Title
**Distillation Dashboard** - Intelligent Request Routing Analytics

### Description
Central monitoring interface for the Distillation Pass system, which pre-processes user requests to determine optimal handling paths. Visualizes routing decisions, cache performance, cost savings, and intent classification accuracy in real-time.

### Key Capabilities
- Real-time routing decision breakdown (Cache, Static, Light LLM, Full LLM, Reject)
- Cache hit rates with exact vs semantic breakdown
- Estimated cost savings from distillation
- Intent classification distribution and confidence metrics
- Static response library usage analytics
- Classification latency monitoring
- Quick access to configuration management

---

## 👤 User Stories

### US-ADMIN-DISTILL-001: View Routing Breakdown
**As a** platform administrator  
**I want to** see how requests are being routed by the distillation system  
**So that** I can understand the effectiveness of the pre-processing layer

**Acceptance Criteria:**
- Pie/donut chart showing route type distribution
- Percentage breakdown: Cache, Static, Light LLM, Full LLM, Reject
- Comparison to previous period (up/down indicators)
- Click on segment to drill down to details
- Real-time updates as new requests processed
- Time period selector (1h, 24h, 7d, 30d)

### US-ADMIN-DISTILL-002: Monitor Cache Performance
**As a** platform administrator  
**I want to** see cache hit rates and effectiveness  
**So that** I can optimize caching strategies

**Acceptance Criteria:**
- Combined cache hit rate displayed prominently
- Breakdown: Exact cache hits vs Semantic cache hits
- Cache size (entries, memory usage)
- Average cache entry age
- Top cached queries list
- Cache invalidation controls

### US-ADMIN-DISTILL-003: Track Cost Savings
**As a** finance-aware administrator  
**I want to** see estimated cost savings from distillation  
**So that** I can justify and optimize the system

**Acceptance Criteria:**
- Estimated cost saved displayed in USD
- Requests avoided (that would have gone to full LLM)
- Savings breakdown by route type
- Comparison to baseline (no distillation)
- Projected monthly savings
- Cost per request with vs without distillation

### US-ADMIN-DISTILL-004: View Intent Classification
**As a** platform administrator  
**I want to** see how user intents are being classified  
**So that** I can identify gaps in classification

**Acceptance Criteria:**
- Intent distribution chart (top 10 intents)
- Average classification confidence score
- Low confidence classifications highlighted
- Misclassification rate (if feedback available)
- Intent trends over time
- Ability to view sample queries per intent

### US-ADMIN-DISTILL-005: Monitor Classification Latency
**As a** platform operator  
**I want to** ensure classification is not adding significant latency  
**So that** user experience remains fast

**Acceptance Criteria:**
- Average classification latency displayed
- P50, P95, P99 latency percentiles
- Latency trend over time chart
- Alert if latency exceeds threshold (100ms)
- Breakdown by route type
- Comparison to target (<50ms)

### US-ADMIN-DISTILL-006: View Static Response Usage
**As a** platform administrator  
**I want to** see which static responses are being used  
**So that** I can optimize the static response library

**Acceptance Criteria:**
- Top used static responses list
- Usage count and percentage
- Response effectiveness (user follow-up rate)
- Last updated timestamp
- Quick link to edit response
- Coverage gaps identified

---

## 🖼️ Views & Wireframes

### View 1: Distillation Dashboard (Default View)

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│  🔬 Distillation Pass                              Period: [24h ▼]    🔄 Live       │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                      │
│  ┌─ Summary ───────────────────────────────────────────────────────────────────────┐│
│  │  📊 45,231 Requests    💾 34% Cache Hit    ⚡ 15ms Avg Latency    💰 $352 Saved ││
│  │     processed today       +2% vs yesterday     under 50ms target    40% reduction││
│  └─────────────────────────────────────────────────────────────────────────────────┘│
│                                                                                      │
│  ┌─────────────────────────────────────────┐ ┌─────────────────────────────────────┐│
│  │ ROUTING BREAKDOWN                       │ │ CACHE PERFORMANCE                   ││
│  │                                         │ │                                     ││
│  │         ┌─────────────┐                 │ │  Combined Hit Rate                  ││
│  │        /   Cache       \                │ │  ┌─────────────────────────────────┐││
│  │       /     34%         \               │ │  │ ████████████████░░░░ 34.1%      │││
│  │      │───────────────────│              │ │  └─────────────────────────────────┘││
│  │      │    Static │ Full │               │ │                                     ││
│  │      │     20%   │ 18%  │               │ │  Exact Cache: 18.2% (8,230 hits)   ││
│  │      │───────────────────│              │ │  Semantic Cache: 15.9% (7,190 hits)││
│  │       \   Light   Reject/               │ │                                     ││
│  │        \   28%    0.3% /                │ │  Cache Entries: 15,420             ││
│  │         └─────────────┘                 │ │  Cache Size: 45.2 MB               ││
│  │                                         │ │  Avg Entry Age: 2.3 hours          ││
│  │  ■ Cache (34%) ■ Static (20%)          │ │                                     ││
│  │  ■ Light LLM (28%) ■ Full LLM (18%)    │ │  [🗑️ Clear Cache] [⚙️ Configure]   ││
│  │  ■ Reject (0.3%)                       │ │                                     ││
│  └─────────────────────────────────────────┘ └─────────────────────────────────────┘│
│                                                                                      │
│  ┌─────────────────────────────────────────┐ ┌─────────────────────────────────────┐│
│  │ COST SAVINGS                            │ │ CLASSIFICATION LATENCY              ││
│  │                                         │ │                                     ││
│  │  Estimated Saved Today                  │ │        Latency Distribution         ││
│  │  ┌─────────────────────────────────────┐│ │                                     ││
│  │  │         $352.40                     ││ │  50ms ┤  ╭──╮                       ││
│  │  │         40% cost reduction          ││ │       │ ╭╯  ╰╮      Target: <50ms  ││
│  │  └─────────────────────────────────────┘│ │  25ms ┤╭╯    ╰──────●───────       ││
│  │                                         │ │       ││         P95: 35ms         ││
│  │  Requests Avoided: 24,320               │ │   0ms └──────────────────────▶     ││
│  │  (Would have gone to Full LLM)          │ │        00:00       12:00    Now    ││
│  │                                         │ │                                     ││
│  │  ┌───────────────────────────────────┐  │ │  Avg: 15ms │ P50: 12ms │ P99: 48ms││
│  │  │ Savings by Route                  │  │ │                                     ││
│  │  │ Cache hits:     $245.20 (70%)     │  │ │  ✅ Under target (50ms)            ││
│  │  │ Static resp:    $78.50 (22%)      │  │ │                                     ││
│  │  │ Light LLM:      $28.70 (8%)       │  │ │                                     ││
│  │  └───────────────────────────────────┘  │ │                                     ││
│  │                                         │ │                                     ││
│  │  Monthly Projection: ~$10,500           │ │                                     ││
│  └─────────────────────────────────────────┘ └─────────────────────────────────────┘│
│                                                                                      │
│  ┌─────────────────────────────────────────────────────────────────────────────────┐│
│  │ INTENT CLASSIFICATION                                                            ││
│  │                                                                                  ││
│  │ Top Intents (24h)                              Confidence Distribution          ││
│  │                                                                                  ││
│  │ price_check      ████████████████████  27.6%   High (>90%)  ████████████ 68%   ││
│  │ swap_request     ██████████████        18.1%   Medium       ████████     24%   ││
│  │ explain_concept  ██████████            11.9%   Low (<70%)   ███          8%    ││
│  │ balance_check    █████████             10.6%                                    ││
│  │ stake_request    ███████               8.2%    Avg Confidence: 87.3%           ││
│  │ how_to           ██████                6.5%                                     ││
│  │ greeting         █████                 5.8%    ⚠️ 3,621 low-confidence         ││
│  │ apy_check        ████                  4.2%       classifications               ││
│  │ borrow_request   ███                   3.8%                                     ││
│  │ other            ███                   3.3%    [View Details →]                 ││
│  │                                                                                  ││
│  └─────────────────────────────────────────────────────────────────────────────────┘│
│                                                                                      │
│  ┌─────────────────────────────────────────────────────────────────────────────────┐│
│  │ STATIC RESPONSE USAGE                                                            ││
│  │                                                                                  ││
│  │ Response                          │ Hits    │ % of Static │ Last Updated        ││
│  │ ─────────────────────────────────┼─────────┼─────────────┼─────────────────────││
│  │ 🏷️ price_check (default)         │ 5,420   │ 60.2%       │ Auto-updated        ││
│  │ 👋 greeting (default)             │ 2,150   │ 23.9%       │ 7 days ago          ││
│  │ ⛽ gas_check (default)            │ 890     │ 9.9%        │ Auto-updated        ││
│  │ 💰 balance_check (default)        │ 540     │ 6.0%        │ Auto-updated        ││
│  │                                                                                  ││
│  │ [📝 Manage Static Responses →]                                                   ││
│  └─────────────────────────────────────────────────────────────────────────────────┘│
│                                                                                      │
│  ┌─────────────────────────────────────────────────────────────────────────────────┐│
│  │ QUICK ACTIONS                                                                    ││
│  │                                                                                  ││
│  │  [⚙️ Configuration]  [📝 Static Responses]  [🗑️ Clear Cache]  [🧪 Test Query]  ││
│  │                                                                                  ││
│  └─────────────────────────────────────────────────────────────────────────────────┘│
│                                                                                      │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

### View 2: Intent Details Drill-Down

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│  🔬 Distillation > Intent: price_check                                      [✕]     │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                      │
│  INTENT: price_check                                           Period: [24h ▼]      │
│                                                                                      │
│  ┌────────────────────┬────────────────────┬────────────────────┬─────────────────┐ │
│  │ TOTAL CLASSIFIED   │ AVG CONFIDENCE     │ ROUTE DISTRIBUTION │ CACHE HIT RATE  │ │
│  │ 12,500             │ 94.2%              │ Static: 78%        │ 45%             │ │
│  │ +15% vs yesterday  │ High               │ Cache: 20%         │                 │ │
│  │                    │                    │ LLM: 2%            │                 │ │
│  └────────────────────┴────────────────────┴────────────────────┴─────────────────┘ │
│                                                                                      │
│  SAMPLE QUERIES                                                                     │
│  ┌─────────────────────────────────────────────────────────────────────────────────┐│
│  │ Query                                    │ Confidence │ Route   │ Entities      ││
│  │ ────────────────────────────────────────┼────────────┼─────────┼───────────────││
│  │ "What's the ETH price?"                  │ 98.2%      │ Static  │ ETH           ││
│  │ "BTC price now"                          │ 96.5%      │ Cache   │ BTC           ││
│  │ "How much is Solana worth?"              │ 94.1%      │ Static  │ SOL           ││
│  │ "Current ethereum price in usd"          │ 97.8%      │ Cache   │ ETH           ││
│  │ "What's the value of 10 ETH?"            │ 78.3%      │ LLM     │ ETH, 10       ││
│  └─────────────────────────────────────────────────────────────────────────────────┘│
│                                                                                      │
│  LOW CONFIDENCE SAMPLES (for review)                                                │
│  ┌─────────────────────────────────────────────────────────────────────────────────┐│
│  │ Query                                    │ Confidence │ Possible Confusion      ││
│  │ ────────────────────────────────────────┼────────────┼─────────────────────────││
│  │ "ETH price prediction"                   │ 62.1%      │ price_check vs strategy ││
│  │ "Is BTC a good price now?"               │ 58.9%      │ price_check vs advice   ││
│  │ "Compare ETH and SOL prices"             │ 67.2%      │ price_check vs compare  ││
│  └─────────────────────────────────────────────────────────────────────────────────┘│
│                                                                                      │
│  TREND OVER TIME                                                                    │
│  ┌─────────────────────────────────────────────────────────────────────────────────┐│
│  │  800 ┤        ╭──╮                           Peak: 14:00 (lunch time)           ││
│  │      │       ╭╯  ╰╮    ╭──╮                                                     ││
│  │  400 ┤    ╭──╯    ╰────╯  ╰──╮                                                  ││
│  │      │ ╭──╯                  ╰──                                                ││
│  │    0 └───────────────────────────────▶                                          ││
│  │       00:00    06:00    12:00    18:00    Now                                   ││
│  └─────────────────────────────────────────────────────────────────────────────────┘│
│                                                                                      │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

### View 3: Test Query Tool

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│  🧪 Test Distillation Query                                                 [✕]     │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                      │
│  Enter a query to see how the distillation system would process it:                 │
│                                                                                      │
│  ┌─────────────────────────────────────────────────────────────────────────────────┐│
│  │ What's the current ETH price and should I buy more?                             ││
│  └─────────────────────────────────────────────────────────────────────────────────┘│
│  [🔍 Analyze]                                                                        │
│                                                                                      │
│  ────────────────────────────────────────────────────────────────────────────────   │
│                                                                                      │
│  ANALYSIS RESULTS                                              Latency: 12ms        │
│                                                                                      │
│  ┌────────────────────┬────────────────────┬────────────────────┬─────────────────┐ │
│  │ INTENT             │ COMPLEXITY         │ ROUTE              │ MODEL TIER      │ │
│  │ price_check        │ moderate           │ FULL_LLM           │ standard        │ │
│  │ Confidence: 72.3%  │ (multiple parts)   │ (compound query)   │                 │ │
│  └────────────────────┴────────────────────┴────────────────────┴─────────────────┘ │
│                                                                                      │
│  ENTITIES EXTRACTED                                                                 │
│  ┌─────────────────────────────────────────────────────────────────────────────────┐│
│  │ Tokens: [ETH]                                                                    ││
│  │ Protocols: []                                                                    ││
│  │ Chains: []                                                                       ││
│  │ Amounts: []                                                                      ││
│  └─────────────────────────────────────────────────────────────────────────────────┘│
│                                                                                      │
│  ROUTING DECISION                                                                   │
│  ┌─────────────────────────────────────────────────────────────────────────────────┐│
│  │ Route: FULL_LLM                                                                  ││
│  │ Reason: Query contains multiple intents (price check + investment advice).      ││
│  │         Cannot be fully satisfied by cache or static response.                  ││
│  │                                                                                  ││
│  │ Cache Check: MISS                                                                ││
│  │   - Exact: No match                                                             ││
│  │   - Semantic: Best match 0.78 similarity (below 0.95 threshold)                 ││
│  │     Query: "What is the ETH price?" (different intent)                          ││
│  │                                                                                  ││
│  │ Static Check: PARTIAL                                                            ││
│  │   - Price component could be answered statically                                ││
│  │   - Investment advice requires LLM                                              ││
│  └─────────────────────────────────────────────────────────────────────────────────┘│
│                                                                                      │
│  EXPECTED RESPONSE TIME: ~2,000ms (Full LLM)                                        │
│  EXPECTED COST: ~$0.008                                                             │
│                                                                                      │
│  ⚠️ Note: This query would be cheaper if split into two separate queries            │
│                                                                                      │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 🔌 API Endpoints

### Get Distillation Overview

```typescript
// GET /admin/distillation/telemetry/overview?period=24h
// Get distillation metrics overview

interface GetDistillationOverviewResponse {
  success: true;
  data: {
    period: string;
    total_requests: number;
    
    route_breakdown: {
      reject: number;
      cache: number;
      static: number;
      light_llm: number;
      full_llm: number;
    };
    
    route_percentages: {
      reject: number;
      cache: number;
      static: number;
      light_llm: number;
      full_llm: number;
    };
    
    cache_metrics: {
      exact_hit_rate: number;
      semantic_hit_rate: number;
      combined_hit_rate: number;
      total_entries: number;
      size_mb: number;
      avg_entry_age_hours: number;
    };
    
    classification_metrics: {
      avg_latency_ms: number;
      p50_latency_ms: number;
      p95_latency_ms: number;
      p99_latency_ms: number;
      avg_confidence: number;
      low_confidence_count: number;
    };
    
    cost_savings: {
      estimated_saved_usd: number;
      requests_avoided: number;
      savings_by_route: Record<string, number>;
      projected_monthly_usd: number;
    };
    
    comparison: {
      requests_change_pct: number;
      cache_hit_change_pct: number;
      savings_change_pct: number;
    };
  };
}
```

### Get Intent Distribution

```typescript
// GET /admin/distillation/telemetry/intents?period=24h
// Get intent classification distribution

interface GetIntentDistributionResponse {
  success: true;
  data: {
    period: string;
    intents: Array<{
      intent: string;
      count: number;
      percentage: number;
      avg_confidence: number;
      route_distribution: Record<string, number>;
    }>;
    confidence_distribution: {
      high: number;      // >90%
      medium: number;    // 70-90%
      low: number;       // <70%
    };
    avg_confidence: number;
    low_confidence_samples: Array<{
      query: string;
      intent: string;
      confidence: number;
      possible_alternatives: string[];
    }>;
  };
}
```

### Get Cache Stats

```typescript
// GET /admin/distillation/cache/stats
// Get detailed cache statistics

interface GetCacheStatsResponse {
  success: true;
  data: {
    exact_cache: {
      total_entries: number;
      size_mb: number;
      hit_rate_24h: number;
      avg_ttl_seconds: number;
      top_keys: Array<{
        key: string;
        query_preview: string;
        hit_count: number;
        created_at: string;
      }>;
    };
    semantic_cache: {
      total_entries: number;
      size_mb: number;
      hit_rate_24h: number;
      avg_similarity: number;
    };
    combined_hit_rate: number;
    estimated_cost_saved_24h_usd: number;
  };
}
```

### Test Query

```typescript
// POST /admin/distillation/test
// Test distillation on a query

interface TestDistillationRequest {
  query: string;
  include_cache_check?: boolean;
  include_static_check?: boolean;
}

interface TestDistillationResponse {
  success: true;
  data: {
    query: string;
    normalized_query: string;
    
    classification: {
      intent: string;
      confidence: number;
      complexity: string;
      latency_ms: number;
    };
    
    entities: {
      tokens: string[];
      protocols: string[];
      chains: string[];
      amounts: string[];
    };
    
    routing_decision: {
      route_type: string;
      reason: string;
      suggested_model_tier: string | null;
    };
    
    cache_check?: {
      exact_hit: boolean;
      semantic_hit: boolean;
      semantic_best_match?: {
        query: string;
        similarity: number;
      };
    };
    
    static_check?: {
      available: boolean;
      template?: string;
      data_source?: string;
    };
    
    expected_response_time_ms: number;
    expected_cost_usd: number;
  };
}
```

### Invalidate Cache

```typescript
// POST /admin/distillation/cache/invalidate
// Invalidate cache entries

interface InvalidateCacheRequest {
  cache_type: 'exact' | 'semantic' | 'all';
  filter?: {
    intent?: string;
    older_than_hours?: number;
  };
}

interface InvalidateCacheResponse {
  success: true;
  data: {
    invalidated_count: number;
    cache_type: string;
  };
}
```

---

## 📊 Data Structures

### Module State

```typescript
interface DistillationDashboardState {
  // Overview Data
  overview: DistillationOverview | null;
  intentDistribution: IntentDistribution | null;
  cacheStats: CacheStats | null;
  staticResponseUsage: StaticResponseUsage[];
  
  // UI State
  loading: {
    overview: boolean;
    intents: boolean;
    cache: boolean;
    static: boolean;
    test: boolean;
  };
  
  errors: {
    overview: Error | null;
    intents: Error | null;
    cache: Error | null;
  };
  
  // Filters
  period: '1h' | '24h' | '7d' | '30d';
  
  // Drill-down
  selectedIntent: string | null;
  intentDetails: IntentDetails | null;
  
  // Test Tool
  testToolOpen: boolean;
  testQuery: string;
  testResult: TestDistillationResponse['data'] | null;
  
  // Cache Actions
  clearingCache: boolean;
  
  // Real-time
  wsConnected: boolean;
  lastUpdate: string | null;
}
```

---

## 🎨 Component Specifications

### RouteBreakdownChart

```typescript
interface RouteBreakdownChartProps {
  data: {
    reject: number;
    cache: number;
    static: number;
    light_llm: number;
    full_llm: number;
  };
  onSegmentClick?: (routeType: string) => void;
  showLegend?: boolean;
  animated?: boolean;
}
```

### CachePerformanceCard

```typescript
interface CachePerformanceCardProps {
  stats: CacheStats;
  onClearCache: () => void;
  onConfigure: () => void;
  loading?: boolean;
}
```

### CostSavingsCard

```typescript
interface CostSavingsCardProps {
  savings: {
    total_usd: number;
    requests_avoided: number;
    by_route: Record<string, number>;
    projected_monthly: number;
  };
  comparison: {
    change_pct: number;
  };
}
```

### IntentDistributionChart

```typescript
interface IntentDistributionChartProps {
  intents: Array<{
    intent: string;
    count: number;
    percentage: number;
  }>;
  onIntentClick: (intent: string) => void;
  maxItems?: number;
}
```

### LatencyDistributionChart

```typescript
interface LatencyDistributionChartProps {
  data: TimeSeriesPoint[];
  percentiles: {
    p50: number;
    p95: number;
    p99: number;
  };
  target_ms: number;
}
```

### TestQueryPanel

```typescript
interface TestQueryPanelProps {
  open: boolean;
  onClose: () => void;
  onTest: (query: string) => void;
  result: TestDistillationResponse['data'] | null;
  loading?: boolean;
}
```

---

## 🎬 Motion Design

```typescript
const distillationAnimations = {
  // Donut chart segments
  chartSegmentEnter: {
    initial: { pathLength: 0 },
    animate: { pathLength: 1 },
    transition: { duration: 0.8, ease: 'easeOut' }
  },
  
  // Metric counter
  metricCount: {
    initial: { opacity: 0 },
    animate: { opacity: 1 },
    transition: { duration: 0.5 }
  },
  
  // Cache hit pulse
  cacheHitPulse: {
    scale: [1, 1.1, 1],
    backgroundColor: ['transparent', 'rgba(16, 185, 129, 0.2)', 'transparent'],
    transition: { duration: 0.3 }
  },
  
  // Cost savings counter
  savingsCounter: {
    scale: [1, 1.05, 1],
    color: ['#10B981', '#34D399', '#10B981'],
    transition: { duration: 2, repeat: Infinity }
  },
  
  // Intent bar grow
  intentBarGrow: {
    initial: { width: 0 },
    animate: { width: '100%' },
    transition: { duration: 0.5, ease: 'easeOut' }
  },
  
  // Test result appear
  testResultAppear: {
    initial: { opacity: 0, y: 20 },
    animate: { opacity: 1, y: 0 },
    transition: { duration: 0.3 }
  },
  
  // Cache clear progress
  cacheClearProgress: {
    width: ['0%', '100%'],
    transition: { duration: 2 }
  }
};
```

---

## ⌨️ Keyboard Shortcuts

```typescript
const distillationShortcuts = {
  't': 'Open test query tool',
  'mod+r': 'Refresh data',
  '1': 'Switch to 1h view',
  '2': 'Switch to 24h view',
  '3': 'Switch to 7d view',
  '4': 'Switch to 30d view',
  'c': 'Go to cache management',
  's': 'Go to static responses',
  'escape': 'Close panels',
};
```

---

## ⚠️ Error Handling

```typescript
const distillationErrorCodes = {
  // Data Errors
  DISTILL_DATA_001: 'Failed to load distillation overview',
  DISTILL_DATA_002: 'Failed to load intent distribution',
  DISTILL_DATA_003: 'Failed to load cache statistics',
  
  // Cache Errors
  DISTILL_CACHE_001: 'Failed to clear cache',
  DISTILL_CACHE_002: 'Cache operation timed out',
  
  // Test Errors
  DISTILL_TEST_001: 'Failed to analyze query',
  DISTILL_TEST_002: 'Query analysis timed out',
  
  // Config Errors
  DISTILL_CFG_001: 'Failed to update configuration',
};
```

---

## 📋 Field Requirements Summary

| Endpoint | Field | Type | Required | Validation |
|----------|-------|------|----------|------------|
| GET /telemetry/overview | period | enum | Yes | 1h, 24h, 7d, 30d |
| POST /cache/invalidate | cache_type | enum | Yes | exact, semantic, all |
| POST /test | query | string | Yes | 1-1000 chars |

---

## 🔒 Security Considerations

1. **Test Queries:** Test queries are logged but not stored permanently
2. **Cache Access:** Cache contents visible only to Admin users
3. **Rate Limiting:** Test endpoint rate limited to prevent abuse
4. **PII Protection:** Query samples anonymized in analytics

---

*Document Version: 1.0*  
*Last Updated: December 1, 2025*  
*Module: Distillation Dashboard*  
*User Type: Admin / Operator*
