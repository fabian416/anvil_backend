# FRONTEND_ADMIN_DISTILLATION_CONFIG

## Admin Distillation Configuration Module

**User Type:** Admin  
**Module:** Distillation Configuration  
**Route:** `/admin/distillation/config`  
**Access Level:** Full CRUD (Admin)

---

## 📋 Module Overview

### Title
**Distillation Configuration** - Intelligent Routing Rules

### Description
Configuration interface for the distillation pass system that intelligently routes requests to the most appropriate handler (reject, cache, static, light LLM, or full LLM) based on intent classification, complexity assessment, and business rules.

### Key Capabilities
- Configure intent classification thresholds
- Define routing rules and priorities
- Set complexity scoring parameters
- Manage rejection patterns
- Configure light vs full LLM boundaries
- Test routing decisions

---

## 👤 User Stories

### US-ADMIN-DISTILL-CFG-001: Configure Intent Thresholds
**As a** platform administrator  
**I want to** set confidence thresholds for intent classification  
**So that** requests are routed appropriately

**Acceptance Criteria:**
- Set minimum confidence for each route type
- Configure fallback behavior for low confidence
- Preview impact of threshold changes
- A/B test different thresholds

### US-ADMIN-DISTILL-CFG-002: Define Routing Rules
**As a** platform administrator  
**I want to** create custom routing rules  
**So that** specific patterns are handled correctly

**Acceptance Criteria:**
- Rule builder with conditions
- Priority ordering
- Enable/disable rules
- Test rules against sample queries
- Rule performance metrics

### US-ADMIN-DISTILL-CFG-003: Configure Rejection Patterns
**As a** platform administrator  
**I want to** define what queries to reject  
**So that** off-topic requests don't consume resources

**Acceptance Criteria:**
- Pattern matching rules
- Intent-based rejection
- Keyword blocklists
- Custom rejection messages
- Review rejected queries

### US-ADMIN-DISTILL-CFG-004: Set Complexity Boundaries
**As a** platform administrator  
**I want to** define complexity thresholds  
**So that** simple queries use light models

**Acceptance Criteria:**
- Complexity score thresholds
- Light LLM vs Full LLM boundary
- Multi-turn detection settings
- Context length considerations

---

## 🖼️ Views & Wireframes

### View 1: Configuration Overview

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│  ⚙️ Distillation Configuration                                   [📊 Test] [Save]   │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                      │
│  [Thresholds]  [Routing Rules]  [Rejection]  [Complexity]  [Advanced]               │
│  ─────────────────────────────────────────────────────────────────────────────────  │
│                                                                                      │
│  CONFIDENCE THRESHOLDS                                                              │
│  ┌─────────────────────────────────────────────────────────────────────────────────┐│
│  │                                                                                  ││
│  │  Route Type              Threshold    Current Traffic                           ││
│  │  ┌────────────────────────────────────────────────────────────────────────────┐ ││
│  │  │                                                                            │ ││
│  │  │  🚫 REJECT             ≥ 95%       ~8% of queries                          │ ││
│  │  │     Off-topic/harmful               ████░░░░░░░░░░░░░░░░░░░░               │ ││
│  │  │     |─────────────────────────────────────────────●|                       │ ││
│  │  │     50%                                          95%                       │ ││
│  │  │                                                                            │ ││
│  │  │  💾 CACHE              ≥ 85%       ~12% of queries                         │ ││
│  │  │     Exact/semantic match            ██████░░░░░░░░░░░░░░░░░                │ ││
│  │  │     |───────────────────────────●───────|                                  │ ││
│  │  │     50%                        85%                                         │ ││
│  │  │                                                                            │ ││
│  │  │  📝 STATIC             ≥ 85%       ~20% of queries                         │ ││
│  │  │     Pre-defined templates           ██████████░░░░░░░░░░░░░                │ ││
│  │  │     |───────────────────────────●───────|                                  │ ││
│  │  │     50%                        85%                                         │ ││
│  │  │                                                                            │ ││
│  │  │  🔵 LIGHT LLM          ≥ 75%       ~35% of queries                         │ ││
│  │  │     Simple queries                  ██████████████░░░░░░░░░░               │ ││
│  │  │     |─────────────────────●─────────────|                                  │ ││
│  │  │     50%                 75%                                                │ ││
│  │  │                                                                            │ ││
│  │  │  🟣 FULL LLM           Fallback    ~25% of queries                         │ ││
│  │  │     Complex/multi-step              ██████████░░░░░░░░░░░░░░               │ ││
│  │  │                                                                            │ ││
│  │  └────────────────────────────────────────────────────────────────────────────┘ ││
│  │                                                                                  ││
│  └─────────────────────────────────────────────────────────────────────────────────┘│
│                                                                                      │
│  ROUTING PRIORITY                                                                   │
│  ┌─────────────────────────────────────────────────────────────────────────────────┐│
│  │                                                                                  ││
│  │  Request → [1. Reject?] → [2. Cache?] → [3. Static?] → [4. Light?] → [5. Full] ││
│  │                                                                                  ││
│  │  ⚡ Evaluation order is fixed. First matching route wins.                       ││
│  │                                                                                  ││
│  └─────────────────────────────────────────────────────────────────────────────────┘│
│                                                                                      │
│  QUICK STATS (Last 24h)                                                             │
│  ┌─────────────────────────────────────────────────────────────────────────────────┐│
│  │  Avg Classification: 42ms │ Cache Hit: 32% │ Static Hit: 22% │ Savings: $86.40 ││
│  └─────────────────────────────────────────────────────────────────────────────────┘│
│                                                                                      │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

### View 2: Routing Rules

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│  📋 Routing Rules                                                   [+ Add Rule]    │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                      │
│  ┌─────────────────────────────────────────────────────────────────────────────────┐│
│  │ PRIORITY │ RULE NAME                │ CONDITIONS            │ ROUTE   │ STATUS  ││
│  ├──────────┼──────────────────────────┼───────────────────────┼─────────┼─────────┤│
│  │ 1        │ Block Competitors        │ mentions: [binance,   │ REJECT  │ 🟢 On   ││
│  │          │                          │  coinbase, kraken]    │         │         ││
│  ├──────────┼──────────────────────────┼───────────────────────┼─────────┼─────────┤│
│  │ 2        │ Price Check Priority     │ intent: price_check   │ STATIC  │ 🟢 On   ││
│  │          │                          │ confidence ≥ 0.9      │         │         ││
│  ├──────────┼──────────────────────────┼───────────────────────┼─────────┼─────────┤│
│  │ 3        │ Simple Balance Queries   │ intent: balance_check │ STATIC  │ 🟢 On   ││
│  │          │                          │ entities ≤ 2          │         │         ││
│  ├──────────┼──────────────────────────┼───────────────────────┼─────────┼─────────┤│
│  │ 4        │ Force Full for Swaps     │ intent: swap_request  │ FULL    │ 🟢 On   ││
│  │          │                          │ amount_usd > 10000    │ LLM     │         ││
│  ├──────────┼──────────────────────────┼───────────────────────┼─────────┼─────────┤│
│  │ 5        │ Greetings Light          │ intent: greeting      │ LIGHT   │ 🟢 On   ││
│  │          │                          │ is_first_message      │ LLM     │         ││
│  └──────────┴──────────────────────────┴───────────────────────┴─────────┴─────────┘│
│                                                                                      │
│  ⚡ Rules are evaluated in priority order. Drag to reorder.                         │
│                                                                                      │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

### View 3: Rule Editor

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│  📝 Edit Rule: Price Check Priority                                         [✕]     │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                      │
│  BASIC INFO                                                                         │
│  ┌───────────────────────────────────────────────────────────────────────────────┐  │
│  │  Rule Name                                                                    │  │
│  │  ┌─────────────────────────────────────────────────────────────────────────┐  │  │
│  │  │ Price Check Priority                                                    │  │  │
│  │  └─────────────────────────────────────────────────────────────────────────┘  │  │
│  │                                                                               │  │
│  │  Description                                                                  │  │
│  │  ┌─────────────────────────────────────────────────────────────────────────┐  │  │
│  │  │ Route high-confidence price checks to static responses                  │  │  │
│  │  └─────────────────────────────────────────────────────────────────────────┘  │  │
│  └───────────────────────────────────────────────────────────────────────────────┘  │
│                                                                                      │
│  CONDITIONS (ALL must match)                                                        │
│  ┌───────────────────────────────────────────────────────────────────────────────┐  │
│  │                                                                               │  │
│  │  ┌─────────────────────────────────────────────────────────────────────────┐  │  │
│  │  │ [Intent ▼]         [equals ▼]        [price_check ▼]          [🗑️]    │  │  │
│  │  └─────────────────────────────────────────────────────────────────────────┘  │  │
│  │                                                                               │  │
│  │  AND                                                                         │  │
│  │                                                                               │  │
│  │  ┌─────────────────────────────────────────────────────────────────────────┐  │  │
│  │  │ [Confidence ▼]     [≥ ▼]             [0.90        ]            [🗑️]    │  │  │
│  │  └─────────────────────────────────────────────────────────────────────────┘  │  │
│  │                                                                               │  │
│  │  [+ Add Condition]                                                           │  │
│  │                                                                               │  │
│  └───────────────────────────────────────────────────────────────────────────────┘  │
│                                                                                      │
│  ACTION                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────────────┐  │
│  │                                                                               │  │
│  │  Route To                                                                    │  │
│  │  ┌─────────────────────────────────────────────────────────────────────────┐  │  │
│  │  │ [●] REJECT  [ ] CACHE  [●] STATIC  [ ] LIGHT_LLM  [ ] FULL_LLM         │  │  │
│  │  └─────────────────────────────────────────────────────────────────────────┘  │  │
│  │                                                                               │  │
│  │  Static Template (required for STATIC route)                                 │  │
│  │  ┌─────────────────────────────────────────────────────────────────────────┐  │  │
│  │  │ [Price Check Template ▼]                                                │  │  │
│  │  └─────────────────────────────────────────────────────────────────────────┘  │  │
│  │                                                                               │  │
│  └───────────────────────────────────────────────────────────────────────────────┘  │
│                                                                                      │
│  TEST RULE                                                                          │
│  ┌───────────────────────────────────────────────────────────────────────────────┐  │
│  │  Query: [What's the price of ETH?                               ] [Test →]   │  │
│  │                                                                               │  │
│  │  Result: ✅ Rule matches                                                     │  │
│  │  Intent: price_check (0.94)  │  Route: STATIC  │  Template: Price Check      │  │
│  └───────────────────────────────────────────────────────────────────────────────┘  │
│                                                                                      │
│  ─────────────────────────────────────────────────────────────────────────────────  │
│                                                                                      │
│  [Delete Rule]                                       [Cancel]        [Save Rule]    │
│                                                                                      │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 🔌 API Endpoints

### Get Distillation Config

```typescript
// GET /admin/distillation/config
// Get current configuration

interface GetDistillationConfigResponse {
  success: true;
  data: {
    thresholds: {
      reject_confidence: number;
      cache_confidence: number;
      static_confidence: number;
      light_llm_confidence: number;
    };
    complexity: {
      light_llm_max_score: number;
      multi_turn_threshold: number;
      context_length_threshold: number;
    };
    rejection: {
      enabled: boolean;
      blocked_keywords: string[];
      blocked_intents: string[];
      custom_message: string;
    };
    classification: {
      model: string;
      max_latency_ms: number;
      fallback_route: string;
    };
    rules: RoutingRule[];
  };
}

interface RoutingRule {
  id: string;
  name: string;
  description?: string;
  priority: number;
  conditions: RuleCondition[];
  action: {
    route: 'reject' | 'cache' | 'static' | 'light_llm' | 'full_llm';
    static_template_id?: string;
    rejection_message?: string;
  };
  is_enabled: boolean;
  stats: {
    matches_24h: number;
    last_matched?: string;
  };
}

interface RuleCondition {
  field: 'intent' | 'confidence' | 'complexity' | 'entities' | 'keywords' | 'context_length';
  operator: 'equals' | 'not_equals' | 'contains' | 'gt' | 'gte' | 'lt' | 'lte' | 'in';
  value: any;
}
```

### Update Thresholds

```typescript
// PUT /admin/distillation/config/thresholds
// Update confidence thresholds

interface UpdateThresholdsRequest {
  reject_confidence?: number;
  cache_confidence?: number;
  static_confidence?: number;
  light_llm_confidence?: number;
}
```

### Create Routing Rule

```typescript
// POST /admin/distillation/config/rules
// Create new routing rule

interface CreateRoutingRuleRequest {
  name: string;
  description?: string;
  conditions: RuleCondition[];
  action: {
    route: string;
    static_template_id?: string;
    rejection_message?: string;
  };
}
```

### Test Routing Decision

```typescript
// POST /admin/distillation/test
// Test routing decision for query

interface TestRoutingRequest {
  query: string;
  context?: {
    user_id?: string;
    project_id?: string;
    is_first_message?: boolean;
  };
}

interface TestRoutingResponse {
  success: true;
  data: {
    query: string;
    classification: {
      intent: string;
      confidence: number;
      complexity_score: number;
      entities: string[];
    };
    matched_rule?: {
      id: string;
      name: string;
    };
    final_route: string;
    route_reason: string;
    latency_ms: number;
  };
}
```

---

## 📊 Data Structures

### Module State

```typescript
interface DistillationConfigState {
  config: DistillationConfig | null;
  rules: RoutingRule[];
  
  loading: {
    config: boolean;
    rules: boolean;
    save: boolean;
    test: boolean;
  };
  
  activeTab: 'thresholds' | 'rules' | 'rejection' | 'complexity' | 'advanced';
  
  ruleEditorOpen: boolean;
  editingRule: RoutingRule | null;
  
  testQuery: string;
  testResult: TestRoutingResponse['data'] | null;
  
  unsavedChanges: boolean;
}
```

---

## 🎨 Component Specifications

### ThresholdSlider

```typescript
interface ThresholdSliderProps {
  label: string;
  value: number;
  onChange: (value: number) => void;
  min?: number;
  max?: number;
  step?: number;
  trafficPercentage?: number;
  description?: string;
}
```

### RuleBuilder

```typescript
interface RuleBuilderProps {
  rule?: RoutingRule;
  onSave: (rule: RoutingRule) => void;
  onCancel: () => void;
  onTest: (query: string) => void;
  testResult?: TestRoutingResponse['data'];
  loading?: boolean;
}
```

### RoutingTestPanel

```typescript
interface RoutingTestPanelProps {
  onTest: (query: string, context?: any) => void;
  result?: TestRoutingResponse['data'];
  loading?: boolean;
}
```

---

## 🎬 Motion Design

```typescript
const distillationConfigAnimations = {
  sliderThumb: {
    scale: 1.2,
    transition: { duration: 0.15 }
  },
  
  ruleReorder: {
    y: 0,
    transition: { type: 'spring', stiffness: 300 }
  },
  
  testResultAppear: {
    opacity: [0, 1],
    y: [10, 0],
    transition: { duration: 0.3 }
  },
  
  routeHighlight: {
    backgroundColor: ['transparent', 'rgba(59, 130, 246, 0.2)', 'transparent'],
    transition: { duration: 0.5 }
  }
};
```

---

## ⌨️ Keyboard Shortcuts

```typescript
const distillationConfigShortcuts = {
  'mod+s': 'Save changes',
  'mod+n': 'Add new rule',
  'mod+t': 'Open test panel',
  'escape': 'Cancel editing',
};
```

---

## ⚠️ Error Handling

```typescript
const distillationConfigErrorCodes = {
  DIST_CFG_001: 'Invalid threshold value',
  DIST_CFG_002: 'Rule conditions invalid',
  DIST_CFG_003: 'Static template required for STATIC route',
  DIST_CFG_004: 'Failed to save configuration',
  DIST_CFG_005: 'Test query failed',
};
```

---

*Document Version: 1.0*  
*Last Updated: December 1, 2025*  
*Module: Distillation Configuration*
