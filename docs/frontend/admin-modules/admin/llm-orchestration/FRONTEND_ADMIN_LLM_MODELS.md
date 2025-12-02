# FRONTEND_ADMIN_LLM_MODELS

## Admin LLM Models Management Module

**User Type:** Admin  
**Module:** Models Management  
**Route:** `/admin/llm/models`  
**Access Level:** Full CRUD (Admin) | Read-Only (Operator)

---

## 📋 Module Overview

### Title
**Models Management** - AI Model Configuration & Performance

### Description
Comprehensive interface for managing individual LLM models across all providers. Enables administrators to configure model parameters, view performance metrics, enable/disable models, set cost thresholds, and compare model effectiveness across different agent types.

### Key Capabilities
- View all models grouped by provider with performance metrics
- Configure model-specific parameters (temperature, max_tokens, etc.)
- Enable/disable models for specific agent types
- Set model-level cost and rate limits
- Compare model performance across agents
- View token usage and cost breakdown
- Configure model fallback preferences

---

## 👤 User Stories

### US-ADMIN-MODEL-001: View All Models
**As a** platform administrator  
**I want to** see all configured models across providers  
**So that** I can understand our model landscape and capabilities

**Acceptance Criteria:**
- Models displayed in grouped table (by provider)
- Each model shows: name, provider, status, success rate, avg latency, cost/1K tokens
- Visual indicators for model tier (premium, standard, economy)
- Filter by provider, status, or tier
- Search by model name
- Sort by any column
- Expandable rows for detailed configuration

### US-ADMIN-MODEL-002: Configure Model Parameters
**As a** platform administrator  
**I want to** customize model generation parameters  
**So that** I can optimize output quality for our use cases

**Acceptance Criteria:**
- Edit modal with all configurable parameters
- Temperature slider (0.0-2.0) with recommended ranges
- Max tokens input with model-specific limits
- Top-p and frequency/presence penalty controls
- System prompt prefix option
- Preview changes before saving
- Revert to defaults option

### US-ADMIN-MODEL-003: Enable/Disable Models
**As a** platform administrator  
**I want to** control which models are available for use  
**So that** I can manage costs and ensure quality

**Acceptance Criteria:**
- Toggle switch for global enable/disable
- Agent-specific enable/disable matrix
- Warning when disabling model with high usage
- Bulk enable/disable option
- Disabled models grayed out in UI
- Audit log for status changes

### US-ADMIN-MODEL-004: View Model Performance
**As a** platform administrator  
**I want to** see detailed performance metrics for each model  
**So that** I can make informed decisions about model selection

**Acceptance Criteria:**
- Performance tab with time-series charts
- Success rate over time
- Latency distribution (P50, P95, P99)
- Error breakdown by type
- Cost accumulation chart
- Comparison with other models in same tier
- Export metrics as CSV

### US-ADMIN-MODEL-005: Set Cost Limits
**As a** platform administrator  
**I want to** configure cost thresholds per model  
**So that** I can prevent unexpected spending

**Acceptance Criteria:**
- Daily cost limit input (USD)
- Warning threshold percentage
- Action when limit reached (alert, throttle, disable)
- Current spend vs limit visualization
- Historical cost trend
- Cost projection based on usage

### US-ADMIN-MODEL-006: Compare Models
**As a** platform administrator  
**I want to** compare multiple models side-by-side  
**So that** I can select the best model for each use case

**Acceptance Criteria:**
- Multi-select models for comparison (up to 4)
- Side-by-side metrics table
- Performance overlay charts
- Cost efficiency comparison (quality vs cost)
- Agent-specific performance breakdown
- Export comparison report

---

## 🖼️ Views & Wireframes

### View 1: Models List (Default View)

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│  🧠 LLM Models                                    [+ Add Model] [📊 Compare Mode]   │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                      │
│  ┌─ Filters ───────────────────────────────────────────────────────────────────────┐│
│  │ [🔍 Search models...]    Provider: [All ▼]   Tier: [All ▼]   Status: [All ▼]   ││
│  └─────────────────────────────────────────────────────────────────────────────────┘│
│                                                                                      │
│  ┌─ Summary ───────────────────────────────────────────────────────────────────────┐│
│  │  🧠 9 Models    ✅ 8 Active    📊 45K Requests (24h)    💰 $66.50 Spent (24h)  ││
│  └─────────────────────────────────────────────────────────────────────────────────┘│
│                                                                                      │
│  🔷 VERTEX AI (Google)                                                    [Expand] │
│  ┌─────────────────────────────────────────────────────────────────────────────────┐│
│  │ MODEL               │ TIER     │ STATUS  │ SUCCESS │ LATENCY │ COST/1K │ 24h $  ││
│  ├─────────────────────┼──────────┼─────────┼─────────┼─────────┼─────────┼────────┤│
│  │ gemini-1.5-pro      │ ⭐ Prem  │ 🟢 On   │ 98.5%   │ 890ms   │ $0.0075 │ $45.20 ││
│  │ gemini-1.5-flash    │ 📊 Std   │ 🟢 On   │ 97.8%   │ 420ms   │ $0.0002 │ $12.40 ││
│  │ gemini-2.0-flash    │ 📊 Std   │ 🟢 On   │ 96.2%   │ 380ms   │ $0.0001 │ $8.90  ││
│  └─────────────────────────────────────────────────────────────────────────────────┘│
│                                                                                      │
│  🟣 DEEPINFRA                                                             [Expand] │
│  ┌─────────────────────────────────────────────────────────────────────────────────┐│
│  │ MODEL               │ TIER     │ STATUS  │ SUCCESS │ LATENCY │ COST/1K │ 24h $  ││
│  ├─────────────────────┼──────────┼─────────┼─────────┼─────────┼─────────┼────────┤│
│  │ meta-llama-3.1-405b │ ⭐ Prem  │ 🟢 On   │ 96.5%   │ 1,250ms │ $0.0027 │ $28.50 ││
│  │ mixtral-8x22b       │ 📊 Std   │ 🟢 On   │ 95.2%   │ 680ms   │ $0.0009 │ $15.20 ││
│  │ qwen2-72b           │ 💰 Econ  │ 🟢 On   │ 94.1%   │ 520ms   │ $0.0005 │ $6.80  ││
│  └─────────────────────────────────────────────────────────────────────────────────┘│
│                                                                                      │
│  🟠 AWS BEDROCK                                                           [Expand] │
│  ┌─────────────────────────────────────────────────────────────────────────────────┐│
│  │ MODEL               │ TIER     │ STATUS  │ SUCCESS │ LATENCY │ COST/1K │ 24h $  ││
│  ├─────────────────────┼──────────┼─────────┼─────────┼─────────┼─────────┼────────┤│
│  │ claude-3-sonnet     │ ⭐ Prem  │ 🟢 On   │ 97.8%   │ 1,120ms │ $0.0030 │ $32.40 ││
│  │ claude-3-haiku      │ 💰 Econ  │ 🟢 On   │ 96.5%   │ 450ms   │ $0.0003 │ $4.20  ││
│  │ mistral-7b          │ 💰 Econ  │ 🔴 Off  │ —       │ —       │ $0.0002 │ $0.00  ││
│  └─────────────────────────────────────────────────────────────────────────────────┘│
│                                                                                      │
│  Showing 9 models across 3 providers                                                │
│                                                                                      │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

### View 2: Model Detail (Expanded Row)

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│  🧠 gemini-1.5-pro                                         [✏️ Edit] [📊 Compare]   │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                      │
│  [Overview]  [Configuration]  [Agent Matrix]  [Performance]  [Costs]                │
│  ─────────────────────────────────────────────────────────────────────────────────  │
│                                                                                      │
│  OVERVIEW                                                                           │
│  ┌────────────────────┬────────────────────┬────────────────────┬─────────────────┐ │
│  │ PROVIDER           │ TIER               │ CONTEXT WINDOW     │ OUTPUT LIMIT    │ │
│  │ 🔷 Vertex AI       │ ⭐ Premium         │ 1,000,000 tokens   │ 8,192 tokens    │ │
│  └────────────────────┴────────────────────┴────────────────────┴─────────────────┘ │
│                                                                                      │
│  ┌────────────────────┬────────────────────┬────────────────────┬─────────────────┐ │
│  │ REQUESTS (24h)     │ SUCCESS RATE       │ AVG LATENCY        │ TOTAL COST      │ │
│  │ 8,500              │ 98.5%              │ 890ms              │ $45.20          │ │
│  │ +12% vs yesterday  │ ↑ 0.3%             │ ↓ 52ms             │ ↑ $8.40         │ │
│  └────────────────────┴────────────────────┴────────────────────┴─────────────────┘ │
│                                                                                      │
│  CAPABILITIES                                                                       │
│  ┌─────────────────────────────────────────────────────────────────────────────────┐│
│  │ ✅ Text Generation   ✅ Code Generation   ✅ Function Calling                   ││
│  │ ✅ Vision            ✅ Long Context      ✅ JSON Mode                          ││
│  │ ❌ Audio             ❌ Fine-tuning       ❌ Embeddings                         ││
│  └─────────────────────────────────────────────────────────────────────────────────┘│
│                                                                                      │
│  AGENT USAGE (24h)                                                                  │
│  ┌──────────────────────────────────────────────────────────────────────────────┐   │
│  │ Agent              │ Requests │ Success │ Avg Latency │ Ranking Score        │   │
│  │ ─────────────────────────────────────────────────────────────────────────────│   │
│  │ SwapAgent          │ 3,200    │ 99.1%   │ 820ms       │ 🥇 #1 (92.5)        │   │
│  │ Researcher         │ 2,800    │ 98.2%   │ 1,050ms     │ 🥇 #1 (91.2)        │   │
│  │ PortfolioAgent     │ 1,500    │ 97.8%   │ 920ms       │ 🥈 #2 (88.7)        │   │
│  │ TradingAgent       │ 1,000    │ 98.5%   │ 780ms       │ 🥉 #3 (85.4)        │   │
│  └──────────────────────────────────────────────────────────────────────────────┘   │
│                                                                                      │
│  CURRENT CONFIGURATION                                                              │
│  ┌──────────────────────────────────────────────────────────────────────────────┐   │
│  │ Temperature: 0.7    │ Max Tokens: 4,096  │ Top-P: 1.0    │ Freq Penalty: 0   │   │
│  └──────────────────────────────────────────────────────────────────────────────┘   │
│                                                                                      │
│  [🔴 Disable Model]                                             Status: ✅ Enabled  │
│                                                                                      │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

### View 3: Model Configuration Editor (Slide-over)

```
┌────────────────────────────────────────────────────────────────┐
│  Configure: gemini-1.5-pro                             [✕]    │
├────────────────────────────────────────────────────────────────┤
│                                                                │
│  GENERATION PARAMETERS                                         │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                                                          │  │
│  │  Temperature                                             │  │
│  │  ┌────────────────────────────────────────────────────┐  │  │
│  │  │     |──────────────●─────────────────|             │  │  │
│  │  │     0.0          0.7                 2.0           │  │  │
│  │  │                                                    │  │  │
│  │  │  Current: 0.7  │  Recommended: 0.5-0.9 for DeFi   │  │  │
│  │  └────────────────────────────────────────────────────┘  │  │
│  │  Lower = more deterministic, Higher = more creative      │  │
│  │                                                          │  │
│  │  Max Output Tokens                                       │  │
│  │  ┌────────────────────────────────────────────────────┐  │  │
│  │  │ [4,096                              ] / 8,192      │  │  │
│  │  └────────────────────────────────────────────────────┘  │  │
│  │  Model maximum: 8,192 tokens                            │  │
│  │                                                          │  │
│  │  Top-P (Nucleus Sampling)                               │  │
│  │  ┌────────────────────────────────────────────────────┐  │  │
│  │  │     |─────────────────────────────────●|           │  │  │
│  │  │     0.0                               1.0          │  │  │
│  │  │  Current: 1.0 (disabled)                           │  │  │
│  │  └────────────────────────────────────────────────────┘  │  │
│  │                                                          │  │
│  │  Frequency Penalty                                       │  │
│  │  ┌────────────────────────────────────────────────────┐  │  │
│  │  │     |●────────────────────────────────|            │  │  │
│  │  │    -2.0            0.0               2.0           │  │  │
│  │  │  Current: 0.0                                      │  │  │
│  │  └────────────────────────────────────────────────────┘  │  │
│  │                                                          │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                │
│  COST LIMITS                                                   │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                                                          │  │
│  │  Daily Cost Limit (USD)                                 │  │
│  │  ┌────────────────────────────────────────────────────┐  │  │
│  │  │ [$] [100                               ]           │  │  │
│  │  └────────────────────────────────────────────────────┘  │  │
│  │  Current spend: $45.20 (45.2%)                          │  │
│  │                                                          │  │
│  │  When limit reached:                                    │  │
│  │  [●] Alert only  [ ] Throttle requests  [ ] Disable    │  │
│  │                                                          │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                │
│  AGENT AVAILABILITY                                            │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                                                          │  │
│  │  [✓] SwapAgent         [✓] TradingAgent                 │  │
│  │  [✓] Researcher        [✓] PortfolioAgent               │  │
│  │  [✓] StakingAgent      [ ] BridgeAgent (disabled)       │  │
│  │                                                          │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                │
│  ────────────────────────────────────────────────────────────  │
│                                                                │
│  [Reset to Defaults]         [Cancel]         [Save Changes]   │
│                                                                │
└────────────────────────────────────────────────────────────────┘
```

### View 4: Model Comparison View

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│  📊 Model Comparison                                           [Export] [✕ Clear]   │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                      │
│  Comparing: gemini-1.5-pro vs meta-llama-3.1-405b vs claude-3-sonnet                │
│                                                                                      │
│  ┌─────────────────────────────────────────────────────────────────────────────────┐│
│  │ METRIC              │ gemini-1.5-pro   │ llama-3.1-405b   │ claude-3-sonnet   ││
│  ├─────────────────────┼──────────────────┼──────────────────┼───────────────────┤│
│  │ Provider            │ 🔷 Vertex AI     │ 🟣 DeepInfra     │ 🟠 AWS Bedrock    ││
│  │ Tier                │ ⭐ Premium       │ ⭐ Premium       │ ⭐ Premium        ││
│  │ Requests (24h)      │ 8,500            │ 4,200            │ 3,800             ││
│  │ Success Rate        │ 98.5% 🏆         │ 96.5%            │ 97.8%             ││
│  │ Avg Latency         │ 890ms            │ 1,250ms          │ 1,120ms           ││
│  │ P95 Latency         │ 1,450ms          │ 2,100ms          │ 1,850ms           ││
│  │ Cost/1K Tokens      │ $0.0075          │ $0.0027 🏆       │ $0.0030           ││
│  │ 24h Cost            │ $45.20           │ $28.50 🏆        │ $32.40            ││
│  │ Context Window      │ 1M tokens 🏆     │ 128K tokens      │ 200K tokens       ││
│  │ Output Limit        │ 8,192            │ 4,096            │ 4,096             ││
│  └─────────────────────────────────────────────────────────────────────────────────┘│
│                                                                                      │
│  PERFORMANCE BY AGENT                                                               │
│  ┌─────────────────────────────────────────────────────────────────────────────────┐│
│  │                                                                                  ││
│  │  SwapAgent                                                                      ││
│  │  gemini-1.5-pro   ████████████████████████████  99.1% │ 820ms  │ Score: 92.5   ││
│  │  claude-3-sonnet  █████████████████████████     97.2% │ 980ms  │ Score: 88.1   ││
│  │  llama-3.1-405b   ███████████████████████       95.8% │ 1,100ms│ Score: 84.3   ││
│  │                                                                                  ││
│  │  Researcher                                                                      ││
│  │  gemini-1.5-pro   ████████████████████████████  98.2% │ 1,050ms│ Score: 91.2   ││
│  │  llama-3.1-405b   █████████████████████████     96.5% │ 1,350ms│ Score: 87.5   ││
│  │  claude-3-sonnet  ████████████████████████      96.1% │ 1,250ms│ Score: 86.8   ││
│  │                                                                                  ││
│  └─────────────────────────────────────────────────────────────────────────────────┘│
│                                                                                      │
│  RECOMMENDATION                                                                     │
│  ┌─────────────────────────────────────────────────────────────────────────────────┐│
│  │ 💡 gemini-1.5-pro offers the best overall performance but highest cost.         ││
│  │    For cost-sensitive workloads, llama-3.1-405b provides 80% of the quality    ││
│  │    at 36% of the cost.                                                          ││
│  └─────────────────────────────────────────────────────────────────────────────────┘│
│                                                                                      │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 🔌 API Endpoints

### List Models

```typescript
// GET /admin/llm/models
// Get all models with optional filters

interface GetModelsRequest {
  provider_id?: string;
  tier?: 'premium' | 'standard' | 'economy';
  is_enabled?: boolean;
}

interface GetModelsResponse {
  success: true;
  data: {
    models: Model[];
    total: number;
    by_provider: Record<string, number>;
    by_tier: Record<string, number>;
  };
}

interface Model {
  id: string;
  provider_id: string;
  provider_name: string;
  name: string;                     // "gemini-1.5-pro"
  display_name: string;             // "Gemini 1.5 Pro"
  tier: 'premium' | 'standard' | 'economy';
  is_enabled: boolean;
  
  capabilities: {
    text_generation: boolean;
    code_generation: boolean;
    function_calling: boolean;
    vision: boolean;
    long_context: boolean;
    json_mode: boolean;
  };
  
  limits: {
    context_window: number;
    max_output_tokens: number;
  };
  
  pricing: {
    input_per_1k_tokens: number;
    output_per_1k_tokens: number;
    cached_input_per_1k_tokens?: number;
  };
  
  config: ModelConfig;
  
  stats_24h: {
    requests: number;
    success_rate: number;
    avg_latency_ms: number;
    p95_latency_ms: number;
    total_cost_usd: number;
  };
  
  agent_usage: Array<{
    agent_type: string;
    requests: number;
    success_rate: number;
    ranking_position: number;
    ranking_score: number;
  }>;
  
  created_at: string;
  updated_at: string;
}

interface ModelConfig {
  temperature: number;
  max_tokens: number;
  top_p: number;
  frequency_penalty: number;
  presence_penalty: number;
  system_prompt_prefix?: string;
}
```

### Update Model

```typescript
// PUT /admin/llm/models/{id}
// Update model configuration

interface UpdateModelRequest {
  is_enabled?: boolean;
  tier?: 'premium' | 'standard' | 'economy';
  config?: Partial<ModelConfig>;
  cost_limits?: {
    daily_limit_usd?: number;
    action_on_limit?: 'alert' | 'throttle' | 'disable';
  };
  enabled_for_agents?: string[];
}

// Validation
const updateModelValidation = {
  'config.temperature': { min: 0, max: 2 },
  'config.max_tokens': { min: 1, max: 128000 },
  'config.top_p': { min: 0, max: 1 },
  'config.frequency_penalty': { min: -2, max: 2 },
  'cost_limits.daily_limit_usd': { min: 0, max: 10000 }
};

interface UpdateModelResponse {
  success: true;
  data: {
    model: Model;
    changes: Array<{
      field: string;
      old_value: any;
      new_value: any;
    }>;
  };
}
```

### Get Model Performance

```typescript
// GET /admin/llm/models/{id}/performance?period=24h
// Get detailed model performance

interface GetModelPerformanceResponse {
  success: true;
  data: {
    model_id: string;
    period: string;
    summary: {
      total_requests: number;
      successful_requests: number;
      failed_requests: number;
      success_rate: number;
      total_input_tokens: number;
      total_output_tokens: number;
      total_cost_usd: number;
      avg_latency_ms: number;
    };
    latency_percentiles: {
      p50: number;
      p75: number;
      p90: number;
      p95: number;
      p99: number;
    };
    error_breakdown: Record<string, number>;
    agent_breakdown: Array<{
      agent_type: string;
      requests: number;
      success_rate: number;
      avg_latency_ms: number;
      total_cost_usd: number;
      ranking_score: number;
    }>;
    timeseries: {
      requests: TimeSeriesPoint[];
      latency: TimeSeriesPoint[];
      cost: TimeSeriesPoint[];
    };
  };
}
```

### Compare Models

```typescript
// POST /admin/llm/models/compare
// Compare multiple models

interface CompareModelsRequest {
  model_ids: string[];           // 2-4 models
  period?: '1h' | '24h' | '7d' | '30d';
  agent_type?: string;
}

interface CompareModelsResponse {
  success: true;
  data: {
    models: Array<{
      model_id: string;
      model_name: string;
      provider_name: string;
      tier: string;
      metrics: {
        requests: number;
        success_rate: number;
        avg_latency_ms: number;
        p95_latency_ms: number;
        cost_per_1k: number;
        total_cost: number;
        context_window: number;
      };
      agent_performance: Record<string, {
        success_rate: number;
        avg_latency_ms: number;
        ranking_score: number;
      }>;
    }>;
    recommendation: {
      best_quality: string;
      best_value: string;
      best_speed: string;
      summary: string;
    };
  };
}
```

---

## 📊 Data Structures

### Module State

```typescript
interface ModelsModuleState {
  // Data
  models: Model[];
  modelsByProvider: Record<string, Model[]>;
  selectedModel: Model | null;
  
  // UI State
  loading: {
    list: boolean;
    details: boolean;
    performance: boolean;
    comparison: boolean;
    save: boolean;
  };
  
  errors: {
    list: Error | null;
    save: Error | null;
  };
  
  // Filters
  filters: {
    search: string;
    provider: string | null;
    tier: 'all' | 'premium' | 'standard' | 'economy';
    status: 'all' | 'enabled' | 'disabled';
  };
  
  // Sorting
  sortBy: 'name' | 'success_rate' | 'latency' | 'cost' | 'requests';
  sortOrder: 'asc' | 'desc';
  
  // Edit Mode
  editMode: boolean;
  editForm: Partial<UpdateModelRequest> | null;
  
  // Performance View
  performancePeriod: '1h' | '24h' | '7d' | '30d';
  performanceData: GetModelPerformanceResponse['data'] | null;
  
  // Comparison
  comparisonMode: boolean;
  selectedForComparison: string[];
  comparisonResult: CompareModelsResponse['data'] | null;
  
  // Expanded Providers
  expandedProviders: string[];
}
```

---

## 🎨 Component Specifications

### ModelTable

```typescript
interface ModelTableProps {
  models: Model[];
  groupBy: 'provider' | 'tier' | 'none';
  expandedGroups: string[];
  onToggleGroup: (group: string) => void;
  onSelectModel: (model: Model) => void;
  onToggleEnabled: (id: string, enabled: boolean) => void;
  selectedId?: string;
  comparisonMode?: boolean;
  selectedForComparison?: string[];
  onToggleComparison?: (id: string) => void;
  loading?: boolean;
}
```

### ModelDetailPanel

```typescript
interface ModelDetailPanelProps {
  model: Model;
  activeTab: 'overview' | 'configuration' | 'agents' | 'performance' | 'costs';
  onTabChange: (tab: string) => void;
  onEdit: () => void;
  onToggleEnabled: (enabled: boolean) => void;
  performanceData?: GetModelPerformanceResponse['data'];
  loading?: boolean;
}
```

### ModelConfigEditor

```typescript
interface ModelConfigEditorProps {
  model: Model;
  onSave: (data: UpdateModelRequest) => void;
  onCancel: () => void;
  loading?: boolean;
}
```

### ModelComparisonPanel

```typescript
interface ModelComparisonPanelProps {
  modelIds: string[];
  data: CompareModelsResponse['data'] | null;
  onRemoveModel: (id: string) => void;
  onClearAll: () => void;
  onExport: () => void;
  loading?: boolean;
}
```

### TierBadge

```typescript
interface TierBadgeProps {
  tier: 'premium' | 'standard' | 'economy';
  size?: 'sm' | 'md' | 'lg';
}

// Renders:
// ⭐ Premium (gold)
// 📊 Standard (blue)
// 💰 Economy (green)
```

---

## 🎬 Motion Design

```typescript
const modelsAnimations = {
  // Provider group expand
  groupExpand: {
    initial: { height: 0, opacity: 0 },
    animate: { height: 'auto', opacity: 1 },
    exit: { height: 0, opacity: 0 },
    transition: { duration: 0.3 }
  },
  
  // Model row hover
  rowHover: {
    backgroundColor: 'rgba(59, 130, 246, 0.05)',
    transition: { duration: 0.15 }
  },
  
  // Status toggle
  statusToggle: {
    scale: [1, 1.2, 1],
    transition: { duration: 0.3 }
  },
  
  // Comparison select
  comparisonSelect: {
    scale: [1, 1.05, 1],
    borderColor: ['#334155', '#3B82F6', '#3B82F6'],
    transition: { duration: 0.2 }
  },
  
  // Slider thumb
  sliderThumb: {
    scale: 1.2,
    boxShadow: '0 0 0 4px rgba(59, 130, 246, 0.2)',
    transition: { duration: 0.15 }
  },
  
  // Comparison panel
  comparisonPanel: {
    initial: { opacity: 0, y: 20 },
    animate: { opacity: 1, y: 0 },
    exit: { opacity: 0, y: 20 },
    transition: { duration: 0.3 }
  },
  
  // Winner badge
  winnerBadge: {
    scale: [0, 1.2, 1],
    rotate: [0, 10, 0],
    transition: { duration: 0.5, type: 'spring' }
  }
};
```

---

## ⌨️ Keyboard Shortcuts

```typescript
const modelsShortcuts = {
  'mod+f': 'Focus search',
  'mod+n': 'Add new model',
  'mod+e': 'Edit selected model',
  'c': 'Toggle comparison mode',
  'space': 'Toggle model in comparison',
  'up/down': 'Navigate models',
  'enter': 'Expand/select model',
  'escape': 'Exit comparison/close panel',
  '1/2/3': 'Switch tabs (overview/config/performance)',
};
```

---

## ⚠️ Error Handling

```typescript
const modelErrorCodes = {
  // Validation
  MODEL_VAL_001: 'Temperature must be between 0 and 2',
  MODEL_VAL_002: 'Max tokens exceeds model limit',
  MODEL_VAL_003: 'Invalid top-p value',
  MODEL_VAL_004: 'Cost limit must be positive',
  
  // Business Logic
  MODEL_BUS_001: 'Cannot disable last enabled model for agent',
  MODEL_BUS_002: 'Model not available for this provider',
  MODEL_BUS_003: 'Cost limit exceeded',
  
  // System
  MODEL_SYS_001: 'Failed to load models',
  MODEL_SYS_002: 'Failed to update model configuration',
  MODEL_SYS_003: 'Failed to load performance data',
};
```

---

## 📋 Field Requirements Summary

| Endpoint | Field | Type | Required | Validation |
|----------|-------|------|----------|------------|
| PUT /models/{id} | config.temperature | number | No | 0-2 |
| PUT /models/{id} | config.max_tokens | number | No | 1-model max |
| PUT /models/{id} | config.top_p | number | No | 0-1 |
| PUT /models/{id} | config.frequency_penalty | number | No | -2 to 2 |
| PUT /models/{id} | cost_limits.daily_limit_usd | number | No | 0-10000 |
| POST /models/compare | model_ids | array | Yes | 2-4 valid UUIDs |

---

## 🔒 Security Considerations

1. **Configuration Changes:** All changes logged with full audit trail
2. **Cost Limits:** Enforced at API level, not just UI
3. **Model Access:** Provider credentials never exposed to frontend
4. **Comparison Data:** Cached to prevent repeated expensive queries
5. **Permission Checks:** Edit operations require Admin role

---

*Document Version: 1.0*  
*Last Updated: December 1, 2025*  
*Module: Models Management*  
*User Type: Admin*
