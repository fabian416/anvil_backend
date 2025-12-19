# FRONTEND_USER_GRAPHRAG_SEARCH

## User GraphRAG Protocol Search Module

**User Type:** Authenticated User  
**Module:** Protocol Discovery & Search  
**Route:** `/search`, `/protocols/search`  
**Platform:** Mobile (React Native) & Web  
**Version:** 1.0 - GraphRAG Powered

---

## 📋 Module Overview

### Title
**Protocol Search** - AI-Powered Protocol Discovery

### Description
Advanced protocol search powered by GraphRAG hybrid retrieval combining semantic search with graph intelligence. Users can discover protocols using natural language, understand relationships, and make informed decisions with ML risk scores.

### Key Capabilities
- Hybrid semantic + graph search
- Natural language query understanding
- ML risk scoring per result
- Similar protocol suggestions
- Category and chain filtering
- Risk level filtering
- TVL and audit filtering
- Save search preferences
- Search history tracking
- Protocol comparison

---

## 👤 User Stories

### US-USER-SEARCH-001: Natural Language Protocol Search
**As a** user  
**I want to** search for protocols using natural language  
**So that** I can find protocols by intent, not exact names

**Acceptance Criteria:**
- Enter queries like "safe staking on Ethereum"
- System understands intent (staking, safe=low-risk, Ethereum=chain)
- Results ranked by relevance
- Risk indicators shown

---

### US-USER-SEARCH-002: Filter by Risk Level
**As a** user  
**I want to** filter protocols by risk level  
**So that** I only see protocols matching my risk tolerance

**Acceptance Criteria:**
- Risk filter (LOW/MEDIUM/HIGH/CRITICAL)
- Results update in real-time
- Risk score displayed per protocol
- Clear risk level badges

---

### US-USER-SEARCH-003: Find Similar Protocols
**As a** user  
**I want to** find protocols similar to one I know  
**So that** I can discover alternatives and related options

**Acceptance Criteria:**
- "More like this" button
- Similarity score shown
- Explanation of similarity
- Quick compare option

---

### US-USER-SEARCH-004: Save Search Preferences
**As a** user  
**I want to** save my search filters  
**So that** I can quickly repeat common searches

**Acceptance Criteria:**
- Save search presets
- Name custom searches
- Quick access to saved searches
- Edit/delete presets

---

### US-USER-SEARCH-005: Compare Protocols
**As a** user  
**I want to** compare multiple protocols side-by-side  
**So that** I can make informed decisions

**Acceptance Criteria:**
- Select up to 5 protocols
- Side-by-side comparison view
- Key metrics compared
- Clear winner indicators

---

## 🖼️ Views & Wireframes

### View 1: Search Interface (Mobile)

```
┌─────────────────────────────────────┐
│  [←]    Protocol Search     [⚙️]   │
│                                     │
│  ┌─────────────────────────────────┐│
│  │ 🔍 Search protocols...          ││
│  │    (Try: "low-risk staking")    ││
│  └─────────────────────────────────┘│
│                                     │
│  Quick Searches                     │
│  [Low-Risk] [High APY] [Ethereum]  │
│                                     │
│  ─ Filters ─────────────────────    │
│  Risk: [All] [Low] [Med] [High]    │
│  Chain: [All ▼]                     │
│  Category: [All ▼]                  │
│  TVL: [Any ▼]                       │
│                                     │
│  Recent Searches                    │
│  • Safe staking on Arbitrum        │
│  • High yield lending              │
│  • DEX with low fees               │
│                                     │
│  Trending Searches                  │
│  • Liquid staking                   │
│  • Blue-chip DeFi                   │
│  • Cross-chain bridges             │
│                                     │
│  ─────────────────────────────────  │
│                                     │
│  Popular Protocols                  │
│  ┌─────────────────────────────────┐│
│  │ 🥇 Aave V3                      ││
│  │    Risk: 2.1/10 🟢 LOW          ││
│  │    TVL: $6.2B  |  Lending       ││
│  │    → [View Details]             ││
│  ├─────────────────────────────────┤│
│  │ 🥈 Uniswap V3                   ││
│  │    Risk: 2.5/10 🟢 LOW          ││
│  │    TVL: $3.8B  |  DEX           ││
│  │    → [View Details]             ││
│  └─────────────────────────────────┘│
│                                     │
└─────────────────────────────────────┘
```

---

### View 2: Search Results

```
┌─────────────────────────────────────┐
│  [←]    "safe staking"      [⚙️]   │
│                                     │
│  ┌─────────────────────────────────┐│
│  │ 🔍 safe staking                 ││
│  └─────────────────────────────────┘│
│                                     │
│  Found 8 protocols                  │
│  Sorted by: [Relevance ▼]          │
│                                     │
│  ┌─────────────────────────────────┐│
│  │  🥇 Lido (stETH)           95%  ││
│  │                                 ││
│  │  Risk: 2.3/10 🟢 LOW            ││
│  │  TVL: $28.4B  |  APY: 3.8%      ││
│  │  Chain: Ethereum                ││
│  │  ✓ 15 audits  |  Est. 2020      ││
│  │                                 ││
│  │  💡 Why relevant:               ││
│  │  High semantic match, low risk, ││
│  │  well audited, high TVL         ││
│  │                                 ││
│  │  [View Details] [More Like This]││
│  │  [Add to Compare] [Stake Now →] ││
│  └─────────────────────────────────┘│
│                                     │
│  ┌─────────────────────────────────┐│
│  │  🥈 Rocket Pool (rETH)     89%  ││
│  │                                 ││
│  │  Risk: 2.8/10 🟢 LOW            ││
│  │  TVL: $4.2B  |  APY: 3.6%       ││
│  │  Chain: Ethereum                ││
│  │  ✓ 12 audits  |  Est. 2021      ││
│  │                                 ││
│  │  💡 Why relevant:               ││
│  │  Staking protocol, low risk,    ││
│  │  decentralized                  ││
│  │                                 ││
│  │  [View Details] [More Like This]││
│  │  [Add to Compare] [Stake Now →] ││
│  └─────────────────────────────────┘│
│                                     │
│  ┌─────────────────────────────────┐│
│  │  🥉 Frax (sfrxETH)         82%  ││
│  │                                 ││
│  │  Risk: 3.1/10 🟡 LOW-MED        ││
│  │  TVL: $1.8B  |  APY: 4.2%       ││
│  │  Chain: Ethereum                ││
│  │  ✓ 8 audits  |  Est. 2022       ││
│  │                                 ││
│  │  💡 Why relevant:               ││
│  │  Staking, competitive APY       ││
│  │                                 ││
│  │  [View Details] [More Like This]││
│  │  [Add to Compare] [Stake Now →] ││
│  └─────────────────────────────────┘│
│                                     │
│  [Load More Results (5 remaining)] │
│                                     │
└─────────────────────────────────────┘
```

---

### View 3: Advanced Filters

```
┌─────────────────────────────────────┐
│  [←]    Search Filters      [Reset]│
│                                     │
│  Risk Level                         │
│  ☑ Low (0-3)                        │
│  ☐ Medium (3-5)                     │
│  ☐ High (5-7)                       │
│  ☐ Critical (7-10)                  │
│                                     │
│  Chain                              │
│  ☑ Ethereum                         │
│  ☑ Arbitrum                         │
│  ☐ Polygon                          │
│  ☐ Base                             │
│  ☐ Optimism                         │
│                                     │
│  Category                           │
│  ☐ All                              │
│  ☑ Staking                          │
│  ☐ Lending                          │
│  ☐ DEX                              │
│  ☐ Bridge                           │
│  ☐ Derivatives                      │
│                                     │
│  TVL Range                          │
│  ├────────●────────────┤            │
│  $100M          $10B                │
│                                     │
│  Minimum Audits                     │
│  ├────●────────────────┤            │
│  0              20                  │
│                                     │
│  Protocol Age                       │
│  ☐ New (< 1 year)                   │
│  ☑ Established (1-3 years)          │
│  ☑ Mature (> 3 years)               │
│                                     │
│  Additional                         │
│  ☐ Has governance token             │
│  ☐ Supports my tokens               │
│  ☐ In my portfolio                  │
│                                     │
│  ┌─────────────────────────────────┐│
│  │  [Apply Filters]                ││
│  └─────────────────────────────────┘│
│                                     │
└─────────────────────────────────────┘
```

---

### View 4: Similar Protocols

```
┌─────────────────────────────────────┐
│  [←]    Similar to Lido             │
│                                     │
│  Base Protocol                      │
│  ┌─────────────────────────────────┐│
│  │  Lido Finance                   ││
│  │  Risk: 2.3/10 🟢                ││
│  │  TVL: $28.4B                    ││
│  │  Category: Liquid Staking       ││
│  └─────────────────────────────────┘│
│                                     │
│  Similar Protocols (6 found)        │
│                                     │
│  ┌─────────────────────────────────┐│
│  │  🥇 Rocket Pool        94%      ││
│  │                                 ││
│  │  Risk: 2.8/10 🟢                ││
│  │  TVL: $4.2B                     ││
│  │                                 ││
│  │  💡 Why similar:                ││
│  │  • Both liquid staking          ││
│  │  • Similar risk profile         ││
│  │  • Ethereum-based               ││
│  │  • Community-driven             ││
│  │                                 ││
│  │  [Compare with Lido]            ││
│  └─────────────────────────────────┘│
│                                     │
│  ┌─────────────────────────────────┐│
│  │  🥈 Frax Finance       89%      ││
│  │                                 ││
│  │  Risk: 3.1/10 🟡                ││
│  │  TVL: $1.8B                     ││
│  │                                 ││
│  │  💡 Why similar:                ││
│  │  • Liquid staking ETH           ││
│  │  • Higher APY (4.2% vs 3.8%)    ││
│  │  • Slightly higher risk         ││
│  │  • Newer protocol               ││
│  │                                 ││
│  │  [Compare with Lido]            ││
│  └─────────────────────────────────┘│
│                                     │
│  [View All 6 Similar] [View Graph] │
│                                     │
└─────────────────────────────────────┘
```

---

### View 5: Protocol Comparison

```
┌─────────────────────────────────────┐
│  [←]    Compare Protocols   [Share]│
│                                     │
│  ┌───────┬───────┬───────┬───────┐ │
│  │ Lido  │Rocket │ Frax  │       │ │
│  │ [×]   │ [×]   │ [×]   │ [+]   │ │
│  └───────┴───────┴───────┴───────┘ │
│                                     │
│  ┌─────────────────────────────────┐│
│  │  Risk Score                     ││
│  │  2.3 🟢  │ 2.8 🟢  │ 3.1 🟡     ││
│  │  ────────┴─────────┴────────    ││
│  │  ✓ Winner  Close 2nd  3rd       ││
│  └─────────────────────────────────┘│
│                                     │
│  ┌─────────────────────────────────┐│
│  │  TVL                            ││
│  │  $28.4B  │ $4.2B  │ $1.8B       ││
│  │  ────────┴────────┴─────────    ││
│  │  ✓ Winner  2nd      3rd         ││
│  └─────────────────────────────────┘│
│                                     │
│  ┌─────────────────────────────────┐│
│  │  APY                            ││
│  │  3.8%    │ 3.6%   │ 4.2%        ││
│  │  ────────┴────────┴─────────    ││
│  │  2nd      3rd      ✓ Winner     ││
│  └─────────────────────────────────┘│
│                                     │
│  ┌─────────────────────────────────┐│
│  │  Audits                         ││
│  │  15 ✓    │ 12     │ 8           ││
│  │  ────────┴────────┴─────────    ││
│  │  ✓ Winner  2nd      3rd         ││
│  └─────────────────────────────────┘│
│                                     │
│  ┌─────────────────────────────────┐│
│  │  Age                            ││
│  │  5y ✓    │ 4y     │ 3y          ││
│  │  ────────┴────────┴─────────    ││
│  │  Mature    Mature   Established ││
│  └─────────────────────────────────┘│
│                                     │
│  Overall Winner: Lido (4/5 metrics) │
│                                     │
│  [View Detailed Report]             │
│  [Save Comparison]                  │
│                                     │
└─────────────────────────────────────┘
```

---

### View 6: Search History

```
┌─────────────────────────────────────┐
│  [←]    Search History      [Clear]│
│                                     │
│  Today                              │
│  ┌─────────────────────────────────┐│
│  │ 🔍 safe staking             3PM ││
│  │    8 results  |  Ethereum       ││
│  │    → [Repeat Search]            ││
│  ├─────────────────────────────────┤│
│  │ 🔍 high yield lending      2PM  ││
│  │    12 results  |  All chains    ││
│  │    → [Repeat Search]            ││
│  └─────────────────────────────────┘│
│                                     │
│  Yesterday                          │
│  ┌─────────────────────────────────┐│
│  │ 🔍 DEX with low fees       5PM  ││
│  │    6 results  |  Arbitrum       ││
│  │    → [Repeat Search]            ││
│  ├─────────────────────────────────┤│
│  │ 🔍 blue-chip DeFi         11AM  ││
│  │    15 results  |  All chains    ││
│  │    → [Repeat Search]            ││
│  └─────────────────────────────────┘│
│                                     │
│  This Week                          │
│  ┌─────────────────────────────────┐│
│  │ 🔍 cross-chain bridge     Mon   ││
│  │    4 results  |  Multi-chain    ││
│  │    → [Repeat Search]            ││
│  └─────────────────────────────────┘│
│                                     │
│  Saved Searches                     │
│  ⭐ Safe Staking                    │
│  ⭐ High Yield Opportunities        │
│  ⭐ Blue-Chip Protocols             │
│                                     │
│  [Manage Saved Searches]            │
│                                     │
└─────────────────────────────────────┘
```

---

## 🔌 API Endpoints

### Hybrid Protocol Search

```typescript
// POST /api/v1/graph/search/hybrid
interface HybridSearchRequest {
  query: string;
  limit?: number; // Default: 10
  similarity_threshold?: number; // Default: 0.7
  filters?: {
    risk_level?: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
    chains?: string[];
    categories?: string[];
    min_tvl?: number;
    min_audits?: number;
    max_age_days?: number;
  };
  user_preferences?: {
    risk_tolerance?: 'conservative' | 'moderate' | 'aggressive';
    preferred_chains?: string[];
    excluded_protocols?: string[];
  };
}

interface HybridSearchResponse {
  results: Array<{
    protocol_id: string;
    protocol_name: string;
    similarity_score: number; // 0-1
    combined_score: number; // 0-1 (semantic + graph)
    risk_score: number; // 0-10
    risk_level: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
    tvl: number;
    apy?: number;
    category: string;
    chain: string;
    audit_count: number;
    description: string;
    why_relevant: string;
    tags: string[];
  }>;
  total_results: number;
  search_time_ms: number;
}
```

---

### Find Similar Protocols

```typescript
// POST /api/v1/graph/search/similar-protocols
interface SimilarProtocolsRequest {
  protocol_id: string;
  limit?: number; // Default: 10
  similarity_threshold?: number; // Default: 0.6
}

interface SimilarProtocolsResponse {
  base_protocol: {
    protocol_id: string;
    protocol_name: string;
    category: string;
    risk_level: string;
  };
  similar_protocols: Array<{
    protocol_id: string;
    protocol_name: string;
    similarity_score: number;
    similarity_reasons: string[];
    shared_features: string[];
    key_differences: string[];
    risk_score: number;
    tvl: number;
  }>;
  community_cluster?: string;
}
```

---

### Contextual Search with Preferences

```typescript
// POST /api/v1/graph/search/contextual
interface ContextualSearchRequest {
  query: string;
  user_preferences: {
    risk_tolerance: 'conservative' | 'moderate' | 'aggressive';
    preferred_chains?: string[];
    preferred_categories?: string[];
    min_tvl?: number;
  };
  limit?: number;
}

interface ContextualSearchResponse {
  results: Array<{
    protocol_id: string;
    protocol_name: string;
    relevance_score: number;
    matches_preferences: boolean;
    preference_match_reasons: string[];
    // ... other fields
  }>;
  personalization_applied: boolean;
  filters_applied: string[];
}
```

---

### Save Search Preset

```typescript
// POST /api/v1/search/saved
interface SaveSearchRequest {
  name: string;
  query: string;
  filters: {
    risk_level?: string;
    chains?: string[];
    categories?: string[];
    min_tvl?: number;
  };
}

interface SaveSearchResponse {
  id: string;
  name: string;
  query: string;
  filters: any;
  created_at: string;
}
```

---

### Get Search History

```typescript
// GET /api/v1/search/history?limit=50
interface SearchHistoryResponse {
  searches: Array<{
    id: string;
    query: string;
    filters: any;
    results_count: number;
    created_at: string;
  }>;
  total: number;
}
```

---

### Protocol Comparison

```typescript
// POST /api/v1/protocols/compare
interface CompareProtocolsRequest {
  protocol_ids: string[]; // Max 5
}

interface CompareProtocolsResponse {
  protocols: Array<{
    protocol_id: string;
    protocol_name: string;
    metrics: {
      risk_score: number;
      tvl: number;
      apy?: number;
      audit_count: number;
      age_days: number;
      // ... more metrics
    };
  }>;
  comparison_matrix: {
    [metric: string]: {
      values: number[];
      winner_index: number;
      normalized_values: number[]; // 0-1
    };
  };
  overall_winner?: {
    protocol_id: string;
    protocol_name: string;
    wins_count: number;
  };
}
```

---

## 🎬 Motion Design

```typescript
const searchAnimations = {
  // Search input focus
  searchInputFocus: {
    scale: [1, 1.02, 1],
    boxShadow: [
      '0 0 0 0 rgba(59, 130, 246, 0)',
      '0 0 0 4px rgba(59, 130, 246, 0.2)',
    ],
    transition: { duration: 0.3 }
  },
  
  // Result cards stagger
  resultCardEnter: {
    initial: { y: 20, opacity: 0 },
    animate: { y: 0, opacity: 1 },
    transition: {
      duration: 0.3,
      delay: 'stagger', // 0.05s per card
      ease: [0.4, 0, 0.2, 1]
    }
  },
  
  // Risk badge pulse (high risk)
  highRiskBadge: {
    animate: {
      scale: [1, 1.1, 1],
      transition: {
        duration: 2,
        repeat: Infinity,
        ease: "easeInOut"
      }
    }
  },
  
  // Filter panel slide
  filterPanel: {
    initial: { x: -300, opacity: 0 },
    animate: { x: 0, opacity: 1 },
    exit: { x: -300, opacity: 0 },
    transition: {
      type: "spring",
      stiffness: 300,
      damping: 30
    }
  },
  
  // Similarity score meter
  similarityMeter: {
    initial: { width: 0 },
    animate: { width: 'percentage%' },
    transition: {
      duration: 1,
      ease: [0.4, 0, 0.2, 1]
    }
  },
  
  // Comparison table reveal
  comparisonRow: {
    initial: { height: 0, opacity: 0 },
    animate: { height: 'auto', opacity: 1 },
    transition: {
      duration: 0.4,
      delay: 'stagger'
    }
  },
  
  // Winner badge
  winnerBadge: {
    initial: { scale: 0, rotate: -180 },
    animate: { scale: 1, rotate: 0 },
    transition: {
      type: "spring",
      stiffness: 500,
      damping: 20
    }
  },
  
  // Search result highlight
  resultHighlight: {
    whileHover: {
      scale: 1.02,
      boxShadow: "0 8px 16px rgba(0,0,0,0.1)",
      transition: { duration: 0.2 }
    },
    whileTap: {
      scale: 0.98
    }
  }
};
```

---

## 🎨 Component Specifications

```typescript
// Search input component
interface SearchInputProps {
  value: string;
  onChange: (value: string) => void;
  onSearch: () => void;
  placeholder?: string;
  suggestions?: string[];
  recentSearches?: string[];
}

// Search result card
interface SearchResultCardProps {
  protocol: {
    id: string;
    name: string;
    similarity_score: number;
    risk_score: number;
    risk_level: string;
    tvl: number;
    apy?: number;
    category: string;
    chain: string;
    audit_count: number;
    why_relevant: string;
  };
  onViewDetails: () => void;
  onMoreLikeThis: () => void;
  onAddToCompare: () => void;
  onAction?: (action: string) => void;
}

// Filter panel
interface FilterPanelProps {
  filters: SearchFilters;
  onChange: (filters: SearchFilters) => void;
  onApply: () => void;
  onReset: () => void;
}

interface SearchFilters {
  risk_levels: string[];
  chains: string[];
  categories: string[];
  tvl_range: [number, number];
  min_audits: number;
  age: string[];
}

// Similarity indicator
interface SimilarityIndicatorProps {
  score: number; // 0-1
  showPercentage?: boolean;
  showBar?: boolean;
  color?: string;
}

// Protocol comparison table
interface ComparisonTableProps {
  protocols: Protocol[];
  metrics: string[];
  onRemoveProtocol: (id: string) => void;
  onAddProtocol: () => void;
}

// Search history item
interface SearchHistoryItemProps {
  search: {
    id: string;
    query: string;
    results_count: number;
    created_at: string;
  };
  onRepeat: () => void;
  onDelete?: () => void;
}
```

---

## ⚠️ Error Handling

```typescript
const searchErrors = {
  SEARCH_001: 'Search query too short (minimum 2 characters)',
  SEARCH_002: 'No protocols found matching your criteria',
  SEARCH_003: 'Search service temporarily unavailable',
  SEARCH_004: 'Too many search results - please refine your query',
  SEARCH_005: 'Invalid search filters',
  
  SIMILAR_001: 'Protocol not found',
  SIMILAR_002: 'No similar protocols found',
  
  COMPARE_001: 'Maximum 5 protocols can be compared',
  COMPARE_002: 'At least 2 protocols required for comparison',
  
  HISTORY_001: 'Failed to load search history',
  HISTORY_002: 'Failed to save search',
};
```

---

## 🔒 Security & Privacy

- Search queries not shared publicly
- Search history stored locally + encrypted server-side
- Sensitive filters (portfolio holdings) never logged
- Rate limiting on search API
- Query sanitization
- No tracking of individual protocol views

---

## ♿ Accessibility

- Keyboard navigation for all search controls
- Screen reader support for risk indicators
- ARIA labels for similarity scores
- Focus management in filter panel
- Color-blind friendly risk badges
- Skip to results link

---

*Document Version: 1.0*  
*Last Updated: December 1, 2025*  
*Module: GraphRAG Protocol Search*
