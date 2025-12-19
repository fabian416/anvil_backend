# FRONTEND_ADMIN_DISTILLATION_STATIC

## Admin Distillation Static Responses Module

**User Type:** Admin  
**Module:** Static Responses Management  
**Route:** `/admin/distillation/static`  
**Access Level:** Full CRUD (Admin) | Read-Only (Operator)

---

## 📋 Module Overview

### Title
**Static Responses** - Pre-Defined Response Library

### Description
Management interface for static response templates that can answer common queries without invoking the LLM pipeline. Enables administrators to create, edit, and optimize templated responses for frequently asked questions, price checks, status inquiries, and other predictable queries to reduce costs and improve response times.

### Key Capabilities
- Create and manage static response templates
- Configure intent-to-template mappings
- Support dynamic variable injection (prices, balances, etc.)
- A/B test response variants
- Track template usage analytics
- Manage response conditions and triggers
- Preview rendered responses with live data

---

## 👤 User Stories

### US-ADMIN-STATIC-001: View All Static Responses
**As a** platform administrator  
**I want to** see all static response templates  
**So that** I can understand what queries can be answered without LLM

**Acceptance Criteria:**
- List of all templates grouped by intent category
- Usage statistics (hit count, last used)
- Template status (active, draft, disabled)
- Search by intent or content
- Filter by category or status
- Preview rendered template

### US-ADMIN-STATIC-002: Create Static Response
**As a** platform administrator  
**I want to** create new static response templates  
**So that** common queries are answered instantly

**Acceptance Criteria:**
- Rich text editor with markdown support
- Variable insertion ({{price}}, {{balance}}, etc.)
- Intent mapping with confidence threshold
- Condition configuration (time-based, user-based)
- Preview with sample data injection
- Test against example queries

### US-ADMIN-STATIC-003: Configure Response Variants
**As a** platform administrator  
**I want to** create multiple variants of a response  
**So that** I can A/B test effectiveness

**Acceptance Criteria:**
- Add multiple variants per template
- Set traffic allocation percentages
- Track variant performance metrics
- Statistical significance indicator
- Automatic winner selection option
- Pause underperforming variants

### US-ADMIN-STATIC-004: Set Response Conditions
**As a** platform administrator  
**I want to** configure when templates are used  
**So that** responses are contextually appropriate

**Acceptance Criteria:**
- Time-based conditions (business hours, weekends)
- User-based conditions (new user, premium user)
- Context conditions (project, agent type)
- Fallback hierarchy when conditions not met
- Condition preview and testing

### US-ADMIN-STATIC-005: Test Template Matching
**As a** platform administrator  
**I want to** test if queries match templates  
**So that** I can verify correct template selection

**Acceptance Criteria:**
- Query input field
- Show matched template with confidence score
- Display injected variables
- Show rendered final response
- Explain why template matched/didn't match
- Suggest improvements if no match

### US-ADMIN-STATIC-006: Analyze Template Performance
**As a** platform administrator  
**I want to** see template usage analytics  
**So that** I can optimize the static response library

**Acceptance Criteria:**
- Usage count over time
- Cost savings calculated
- User follow-up rate (did they need more help?)
- Average confidence at trigger
- Top triggering queries
- Coverage gaps identified

---

## 🖼️ Views & Wireframes

### View 1: Static Responses List

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│  📝 Static Responses                                   [+ New Response] [📊 Stats]  │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                      │
│  ┌─ Summary ───────────────────────────────────────────────────────────────────────┐│
│  │  📝 24 Templates    ✅ 18 Active    🎯 9,042 Hits (24h)    💰 $78.50 Saved      ││
│  │     6 categories        75%            20% of queries          vs Full LLM       ││
│  └─────────────────────────────────────────────────────────────────────────────────┘│
│                                                                                      │
│  ┌─ Filters ───────────────────────────────────────────────────────────────────────┐│
│  │ [🔍 Search templates...]    Category: [All ▼]    Status: [Active ▼]            ││
│  └─────────────────────────────────────────────────────────────────────────────────┘│
│                                                                                      │
│  📊 INFORMATIONAL (8 templates)                                                     │
│  ┌─────────────────────────────────────────────────────────────────────────────────┐│
│  │                                                                                  ││
│  │ ┌─────────────────────────────────────────────────────────────────────────────┐ ││
│  │ │ 🏷️ Price Check                                           🟢 Active         │ ││
│  │ │ Intent: price_check │ Confidence: ≥85%                                      │ ││
│  │ │                                                                             │ ││
│  │ │ "The current price of {{token}} is ${{price}} ({{change_24h}}% 24h)."      │ ││
│  │ │                                                                             │ ││
│  │ │ 📊 5,420 hits (60%) │ 💰 $45.20 saved │ 📈 +12% vs yesterday               │ ││
│  │ │ Data source: CoinGecko API │ TTL: 60s                                       │ ││
│  │ │                                                            [✏️] [👁️] [⋮]   │ ││
│  │ └─────────────────────────────────────────────────────────────────────────────┘ ││
│  │                                                                                  ││
│  │ ┌─────────────────────────────────────────────────────────────────────────────┐ ││
│  │ │ ⛽ Gas Price Check                                        🟢 Active         │ ││
│  │ │ Intent: gas_check │ Confidence: ≥90%                                        │ ││
│  │ │                                                                             │ ││
│  │ │ "Current {{chain}} gas: {{gas_low}} (slow) / {{gas_avg}} (normal) /        │ ││
│  │ │  {{gas_high}} (fast) gwei."                                                 │ ││
│  │ │                                                                             │ ││
│  │ │ 📊 890 hits (10%) │ 💰 $8.90 saved │ 📈 +5% vs yesterday                   │ ││
│  │ │                                                            [✏️] [👁️] [⋮]   │ ││
│  │ └─────────────────────────────────────────────────────────────────────────────┘ ││
│  │                                                                                  ││
│  │ ┌─────────────────────────────────────────────────────────────────────────────┐ ││
│  │ │ 💰 Balance Check                                          🟢 Active         │ ││
│  │ │ Intent: balance_check │ Confidence: ≥85%                                    │ ││
│  │ │                                                                             │ ││
│  │ │ "Your {{chain}} wallet balance: {{balance}} {{token}} (~${{usd_value}})"   │ ││
│  │ │                                                                             │ ││
│  │ │ 📊 540 hits (6%) │ 💰 $5.40 saved │ 📉 -3% vs yesterday                    │ ││
│  │ │                                                            [✏️] [👁️] [⋮]   │ ││
│  │ └─────────────────────────────────────────────────────────────────────────────┘ ││
│  │                                                                                  ││
│  └─────────────────────────────────────────────────────────────────────────────────┘│
│                                                                                      │
│  👋 GREETING & SMALL TALK (4 templates)                                             │
│  ┌─────────────────────────────────────────────────────────────────────────────────┐│
│  │                                                                                  ││
│  │ ┌─────────────────────────────────────────────────────────────────────────────┐ ││
│  │ │ 👋 Greeting (Default)                                     🟢 Active         │ ││
│  │ │ Intent: greeting │ Confidence: ≥80%                                         │ ││
│  │ │                                                                             │ ││
│  │ │ "Hello! I'm Anvil, your DeFi assistant. I can help you with swaps,         │ ││
│  │ │  lending, staking, and more. What would you like to do today?"             │ ││
│  │ │                                                                             │ ││
│  │ │ 📊 2,150 hits (24%) │ 💰 $12.50 saved │ Variants: 3 (A/B testing)          │ ││
│  │ │                                                            [✏️] [👁️] [⋮]   │ ││
│  │ └─────────────────────────────────────────────────────────────────────────────┘ ││
│  │                                                                                  ││
│  └─────────────────────────────────────────────────────────────────────────────────┘│
│                                                                                      │
│  🚫 OFF-TOPIC (2 templates)                                                         │
│  [Collapsed - Click to expand]                                                      │
│                                                                                      │
│  Showing 24 templates across 6 categories                                           │
│                                                                                      │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

### View 2: Create/Edit Static Response

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│  📝 Create Static Response                                                  [✕]     │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                      │
│  BASIC CONFIGURATION                                                                │
│  ┌───────────────────────────────────────────────────────────────────────────────┐  │
│  │                                                                               │  │
│  │  Template Name                                                                │  │
│  │  ┌─────────────────────────────────────────────────────────────────────────┐  │  │
│  │  │ APY Rate Check                                                          │  │  │
│  │  └─────────────────────────────────────────────────────────────────────────┘  │  │
│  │                                                                               │  │
│  │  Category                              Intent Mapping                        │  │
│  │  ┌─────────────────────────┐          ┌─────────────────────────────────┐    │  │
│  │  │ [📊 Informational ▼]   │          │ [apy_check ▼]                   │    │  │
│  │  └─────────────────────────┘          └─────────────────────────────────┘    │  │
│  │                                                                               │  │
│  │  Minimum Confidence                                                          │  │
│  │  ┌─────────────────────────────────────────────────────────────────────────┐  │  │
│  │  │     |───────────────────●─────────|                                     │  │  │
│  │  │     50%                85%       100%                                   │  │  │
│  │  │                                                                         │  │  │
│  │  │  Template triggers when intent confidence ≥ 85%                         │  │  │
│  │  └─────────────────────────────────────────────────────────────────────────┘  │  │
│  │                                                                               │  │
│  └───────────────────────────────────────────────────────────────────────────────┘  │
│                                                                                      │
│  RESPONSE TEMPLATE                                                                  │
│  ┌───────────────────────────────────────────────────────────────────────────────┐  │
│  │                                                                               │  │
│  │  Template Content                                      [Insert Variable ▼]   │  │
│  │  ┌─────────────────────────────────────────────────────────────────────────┐  │  │
│  │  │ Current APY rates for {{protocol}} on {{chain}}:                        │  │  │
│  │  │                                                                         │  │  │
│  │  │ **Supply APY:**                                                         │  │  │
│  │  │ {{#each supply_rates}}                                                  │  │  │
│  │  │ • {{token}}: {{apy}}%                                                   │  │  │
│  │  │ {{/each}}                                                               │  │  │
│  │  │                                                                         │  │  │
│  │  │ **Borrow APY:**                                                         │  │  │
│  │  │ {{#each borrow_rates}}                                                  │  │  │
│  │  │ • {{token}}: {{apy}}% (variable)                                        │  │  │
│  │  │ {{/each}}                                                               │  │  │
│  │  │                                                                         │  │  │
│  │  │ _Data from DeFi Llama, updated every 5 minutes._                        │  │  │
│  │  │                                                                         │  │  │
│  │  └─────────────────────────────────────────────────────────────────────────┘  │  │
│  │                                                                               │  │
│  │  Available Variables:                                                        │  │
│  │  ┌─────────────────────────────────────────────────────────────────────────┐  │  │
│  │  │ {{protocol}} │ {{chain}} │ {{supply_rates}} │ {{borrow_rates}}         │  │  │
│  │  │ {{tvl}} │ {{last_updated}} │ {{user_name}}                             │  │  │
│  │  └─────────────────────────────────────────────────────────────────────────┘  │  │
│  │                                                                               │  │
│  └───────────────────────────────────────────────────────────────────────────────┘  │
│                                                                                      │
│  DATA SOURCE                                                                        │
│  ┌───────────────────────────────────────────────────────────────────────────────┐  │
│  │                                                                               │  │
│  │  Source Type                                                                 │  │
│  │  ┌─────────────────────────────────────────────────────────────────────────┐  │  │
│  │  │ [●] API (DeFi Llama)  [ ] Static  [ ] User Context  [ ] Blockchain     │  │  │
│  │  └─────────────────────────────────────────────────────────────────────────┘  │  │
│  │                                                                               │  │
│  │  Cache TTL                                                                   │  │
│  │  ┌─────────────────────────────────────────────────────────────────────────┐  │  │
│  │  │ [300] seconds (5 minutes)                                               │  │  │
│  │  └─────────────────────────────────────────────────────────────────────────┘  │  │
│  │                                                                               │  │
│  └───────────────────────────────────────────────────────────────────────────────┘  │
│                                                                                      │
│  PREVIEW                                                                            │
│  ┌───────────────────────────────────────────────────────────────────────────────┐  │
│  │                                                                               │  │
│  │  Sample Query: "What are the APY rates on Aave?"                            │  │
│  │                                                                               │  │
│  │  ┌─────────────────────────────────────────────────────────────────────────┐  │  │
│  │  │ Current APY rates for Aave on Ethereum:                                 │  │  │
│  │  │                                                                         │  │  │
│  │  │ **Supply APY:**                                                         │  │  │
│  │  │ • USDC: 4.2%                                                            │  │  │
│  │  │ • ETH: 2.1%                                                             │  │  │
│  │  │ • DAI: 3.8%                                                             │  │  │
│  │  │                                                                         │  │  │
│  │  │ **Borrow APY:**                                                         │  │  │
│  │  │ • USDC: 5.1% (variable)                                                 │  │  │
│  │  │ • ETH: 2.8% (variable)                                                  │  │  │
│  │  │ • DAI: 4.5% (variable)                                                  │  │  │
│  │  │                                                                         │  │  │
│  │  │ _Data from DeFi Llama, updated every 5 minutes._                        │  │  │
│  │  └─────────────────────────────────────────────────────────────────────────┘  │  │
│  │                                                                               │  │
│  │  [🔄 Refresh Preview]                                                        │  │
│  │                                                                               │  │
│  └───────────────────────────────────────────────────────────────────────────────┘  │
│                                                                                      │
│  ─────────────────────────────────────────────────────────────────────────────────  │
│                                                                                      │
│  [Cancel]                               [Save as Draft]     [Save & Activate →]     │
│                                                                                      │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

### View 3: Template Testing

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│  🧪 Test Template Matching                                                  [✕]     │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                      │
│  Enter queries to test template matching:                                           │
│                                                                                      │
│  ┌─────────────────────────────────────────────────────────────────────────────────┐│
│  │ what's the current eth price                                                     ││
│  └─────────────────────────────────────────────────────────────────────────────────┘│
│  [🔍 Test Match]                                                                     │
│                                                                                      │
│  MATCHING RESULT                                                                    │
│  ┌─────────────────────────────────────────────────────────────────────────────────┐│
│  │                                                                                  ││
│  │  ✅ TEMPLATE MATCHED                                                            ││
│  │                                                                                  ││
│  │  ┌───────────────────────────────────────────────────────────────────────────┐  ││
│  │  │ Template: Price Check                                                     │  ││
│  │  │ Intent: price_check                                                       │  ││
│  │  │ Confidence: 94.2% (threshold: 85%)                                       │  ││
│  │  │ Match reason: Query contains "price" + recognized token "ETH"            │  ││
│  │  └───────────────────────────────────────────────────────────────────────────┘  ││
│  │                                                                                  ││
│  │  EXTRACTED VARIABLES                                                            ││
│  │  ┌───────────────────────────────────────────────────────────────────────────┐  ││
│  │  │ {{token}}       → ETH                                                     │  ││
│  │  │ {{price}}       → 2,145.32 (from CoinGecko)                              │  ││
│  │  │ {{change_24h}}  → +2.3                                                    │  ││
│  │  │ {{chain}}       → Ethereum (default)                                      │  ││
│  │  └───────────────────────────────────────────────────────────────────────────┘  ││
│  │                                                                                  ││
│  │  RENDERED RESPONSE                                                              ││
│  │  ┌───────────────────────────────────────────────────────────────────────────┐  ││
│  │  │ The current price of ETH is $2,145.32 (+2.3% 24h).                        │  ││
│  │  └───────────────────────────────────────────────────────────────────────────┘  ││
│  │                                                                                  ││
│  │  PERFORMANCE                                                                    ││
│  │  ┌───────────────────────────────────────────────────────────────────────────┐  ││
│  │  │ Classification: 8ms │ Data fetch: 45ms │ Render: 2ms │ Total: 55ms       │  ││
│  │  │ Estimated cost: $0.00 (vs $0.008 for full LLM)                           │  ││
│  │  └───────────────────────────────────────────────────────────────────────────┘  ││
│  │                                                                                  ││
│  └─────────────────────────────────────────────────────────────────────────────────┘│
│                                                                                      │
│  TEST HISTORY                                                                       │
│  ┌─────────────────────────────────────────────────────────────────────────────────┐│
│  │ Query                              │ Result    │ Template          │ Conf    ││
│  │ ─────────────────────────────────────────────────────────────────────────────  ││
│  │ "what's the current eth price"     │ ✅ Matched │ Price Check       │ 94.2%   ││
│  │ "hi there"                         │ ✅ Matched │ Greeting          │ 89.5%   ││
│  │ "explain aave liquidations"        │ ❌ No Match│ —                 │ 72.1%   ││
│  │ "gas fees on arbitrum"             │ ✅ Matched │ Gas Price Check   │ 91.8%   ││
│  └─────────────────────────────────────────────────────────────────────────────────┘│
│                                                                                      │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 🔌 API Endpoints

### List Static Responses

```typescript
// GET /admin/distillation/static-responses
// Get all static response templates

interface GetStaticResponsesResponse {
  success: true;
  data: {
    templates: StaticResponse[];
    categories: Array<{
      name: string;
      count: number;
    }>;
    summary: {
      total: number;
      active: number;
      hits_24h: number;
      cost_saved_24h: number;
    };
  };
}

interface StaticResponse {
  id: string;
  name: string;
  category: string;
  intent: string;
  min_confidence: number;
  template_content: string;
  variables: string[];
  data_source: 'static' | 'api' | 'user_context' | 'blockchain';
  data_config?: {
    api_endpoint?: string;
    cache_ttl_seconds?: number;
  };
  conditions?: ResponseCondition[];
  variants?: ResponseVariant[];
  is_active: boolean;
  stats: {
    hits_24h: number;
    hits_total: number;
    avg_confidence: number;
    follow_up_rate: number;
    cost_saved_24h: number;
  };
  created_at: string;
  updated_at: string;
}

interface ResponseCondition {
  type: 'time' | 'user' | 'context';
  operator: 'equals' | 'contains' | 'between' | 'in';
  field: string;
  value: any;
}

interface ResponseVariant {
  id: string;
  name: string;
  content: string;
  traffic_percentage: number;
  is_active: boolean;
  stats: {
    hits: number;
    follow_up_rate: number;
  };
}
```

### Create Static Response

```typescript
// POST /admin/distillation/static-responses
// Create new static response

interface CreateStaticResponseRequest {
  name: string;
  category: string;
  intent: string;
  min_confidence: number;
  template_content: string;
  data_source: 'static' | 'api' | 'user_context' | 'blockchain';
  data_config?: {
    api_endpoint?: string;
    cache_ttl_seconds?: number;
  };
  conditions?: ResponseCondition[];
  is_active?: boolean;
}

// Validation
const createStaticResponseValidation = {
  name: { required: true, minLength: 2, maxLength: 100 },
  intent: { required: true, enum: VALID_INTENTS },
  min_confidence: { required: true, min: 0.5, max: 1.0 },
  template_content: { required: true, minLength: 10, maxLength: 5000 },
  'data_config.cache_ttl_seconds': { min: 10, max: 86400 }
};
```

### Test Template Match

```typescript
// POST /admin/distillation/static-responses/test
// Test template matching

interface TestTemplateMatchRequest {
  query: string;
}

interface TestTemplateMatchResponse {
  success: true;
  data: {
    query: string;
    matched: boolean;
    template?: {
      id: string;
      name: string;
      intent: string;
    };
    confidence: number;
    threshold: number;
    match_reason?: string;
    variables_extracted?: Record<string, any>;
    rendered_response?: string;
    performance: {
      classification_ms: number;
      data_fetch_ms: number;
      render_ms: number;
      total_ms: number;
    };
    estimated_cost_saved: number;
  };
}
```

---

## 📊 Data Structures

### Module State

```typescript
interface StaticResponsesState {
  // Data
  templates: StaticResponse[];
  categories: string[];
  summary: ResponsesSummary;
  selectedTemplate: StaticResponse | null;
  
  // UI State
  loading: {
    list: boolean;
    template: boolean;
    test: boolean;
    save: boolean;
  };
  
  errors: {
    list: Error | null;
    save: Error | null;
    test: Error | null;
  };
  
  // Filters
  filters: {
    search: string;
    category: string | null;
    status: 'all' | 'active' | 'draft' | 'disabled';
  };
  
  // Editor
  editorOpen: boolean;
  editorMode: 'create' | 'edit';
  editorForm: Partial<CreateStaticResponseRequest>;
  previewData: RenderedPreview | null;
  
  // Testing
  testPanelOpen: boolean;
  testQuery: string;
  testResult: TestTemplateMatchResponse['data'] | null;
  testHistory: TestResult[];
  
  // Variants
  variantsOpen: boolean;
  variants: ResponseVariant[];
  
  // Expanded Categories
  expandedCategories: string[];
}
```

---

## 🎨 Component Specifications

### TemplateCard

```typescript
interface TemplateCardProps {
  template: StaticResponse;
  onEdit: (id: string) => void;
  onPreview: (id: string) => void;
  onToggleActive: (id: string, active: boolean) => void;
  onViewVariants: (id: string) => void;
  expanded?: boolean;
}
```

### TemplateEditor

```typescript
interface TemplateEditorProps {
  template?: StaticResponse;
  mode: 'create' | 'edit';
  onSave: (data: CreateStaticResponseRequest) => void;
  onCancel: () => void;
  onPreview: (content: string) => void;
  previewData?: RenderedPreview;
  loading?: boolean;
}
```

### VariableInserter

```typescript
interface VariableInserterProps {
  availableVariables: Array<{
    name: string;
    description: string;
    source: string;
    example: any;
  }>;
  onInsert: (variable: string) => void;
}
```

### TemplateTestPanel

```typescript
interface TemplateTestPanelProps {
  open: boolean;
  onClose: () => void;
  onTest: (query: string) => void;
  result: TestTemplateMatchResponse['data'] | null;
  history: TestResult[];
  loading?: boolean;
}
```

---

## 🎬 Motion Design

```typescript
const staticResponseAnimations = {
  // Category expand
  categoryExpand: {
    initial: { height: 0 },
    animate: { height: 'auto' },
    transition: { duration: 0.3 }
  },
  
  // Template card hover
  templateHover: {
    backgroundColor: 'rgba(59, 130, 246, 0.05)',
    transition: { duration: 0.15 }
  },
  
  // Variable chip insert
  variableInsert: {
    initial: { scale: 0, opacity: 0 },
    animate: { scale: 1, opacity: 1 },
    transition: { type: 'spring', stiffness: 400 }
  },
  
  // Preview render
  previewRender: {
    initial: { opacity: 0 },
    animate: { opacity: 1 },
    transition: { duration: 0.3 }
  },
  
  // Test result
  testResult: {
    initial: { opacity: 0, y: 20 },
    animate: { opacity: 1, y: 0 },
    transition: { duration: 0.3 }
  },
  
  // Match success pulse
  matchSuccess: {
    backgroundColor: ['transparent', 'rgba(16, 185, 129, 0.2)', 'transparent'],
    transition: { duration: 0.5 }
  },
  
  // Stats counter
  statsCount: {
    opacity: [0, 1],
    y: [10, 0],
    transition: { duration: 0.5 }
  }
};
```

---

## ⌨️ Keyboard Shortcuts

```typescript
const staticResponseShortcuts = {
  'mod+n': 'Create new template',
  'mod+e': 'Edit selected template',
  'mod+t': 'Open test panel',
  'mod+p': 'Preview template',
  'mod+s': 'Save template',
  'escape': 'Close editor/panel',
  '{': 'Insert variable',
};
```

---

## ⚠️ Error Handling

```typescript
const staticResponseErrorCodes = {
  // Validation
  STATIC_VAL_001: 'Template name is required',
  STATIC_VAL_002: 'Template content is required',
  STATIC_VAL_003: 'Invalid intent mapping',
  STATIC_VAL_004: 'Confidence threshold out of range',
  
  // Variables
  STATIC_VAR_001: 'Unknown variable in template',
  STATIC_VAR_002: 'Variable data source not available',
  STATIC_VAR_003: 'Failed to fetch variable data',
  
  // Testing
  STATIC_TEST_001: 'Template matching failed',
  STATIC_TEST_002: 'Preview render failed',
  
  // System
  STATIC_SYS_001: 'Failed to load templates',
  STATIC_SYS_002: 'Failed to save template',
};
```

---

## 📋 Field Requirements Summary

| Endpoint | Field | Type | Required | Validation |
|----------|-------|------|----------|------------|
| POST /static-responses | name | string | Yes | 2-100 chars |
| POST /static-responses | intent | string | Yes | Valid intent |
| POST /static-responses | min_confidence | number | Yes | 0.5-1.0 |
| POST /static-responses | template_content | string | Yes | 10-5000 chars |
| POST /test | query | string | Yes | 1-500 chars |

---

## 🔒 Security Considerations

1. **Template Injection:** All variable values sanitized before injection
2. **Data Source Security:** API endpoints validated and rate-limited
3. **Content Moderation:** Templates reviewed for inappropriate content
4. **Audit Trail:** All template changes logged
5. **A/B Test Privacy:** Variant assignment not linked to user identity

---

*Document Version: 1.0*  
*Last Updated: December 1, 2025*  
*Module: Static Responses*  
*User Type: Admin*
