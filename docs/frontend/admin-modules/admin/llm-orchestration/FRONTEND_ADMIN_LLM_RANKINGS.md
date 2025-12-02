# FRONTEND_ADMIN_LLM_RANKINGS

## Admin LLM Rankings Module

**User Type:** Admin  
**Module:** Model Rankings  
**Route:** `/admin/llm/rankings`  
**Access Level:** Full CRUD (Admin) | Read-Only (Operator)

---

## 📋 Module Overview

### Title
**Model Rankings** - Adaptive Model Selection Intelligence

### Description
Management interface for the adaptive model ranking system that automatically selects the best-performing models for each agent type. Displays ranking scores, performance factors, and allows manual overrides when needed.

### Key Capabilities
- View current rankings per agent type
- Understand ranking factors and weights
- Manual ranking overrides with expiration
- Historical ranking trends
- A/B test ranking algorithms
- Configure ranking calculation parameters

---

## 👤 User Stories

### US-ADMIN-RANK-001: View Current Rankings
**As a** platform administrator  
**I want to** see model rankings for each agent type  
**So that** I understand which models are being selected

**Acceptance Criteria:**
- Rankings displayed per agent type
- Score breakdown showing contributing factors
- Visual comparison of top models
- Last calculation timestamp
- Filter by agent type

### US-ADMIN-RANK-002: Understand Ranking Factors
**As a** platform administrator  
**I want to** see how rankings are calculated  
**So that** I can understand model selection logic

**Acceptance Criteria:**
- Factor weights displayed (latency, success, cost)
- Individual factor scores per model
- Explanation of score calculation
- Impact visualization of each factor

### US-ADMIN-RANK-003: Override Rankings
**As a** platform administrator  
**I want to** manually override rankings when needed  
**So that** I can force specific model selection

**Acceptance Criteria:**
- Pin model to specific rank position
- Set override expiration (hours/days/permanent)
- Reason field for audit trail
- Clear visual indicator of overridden rankings
- One-click remove override

### US-ADMIN-RANK-004: Trigger Recalculation
**As a** platform administrator  
**I want to** manually trigger ranking recalculation  
**So that** rankings reflect recent performance

**Acceptance Criteria:**
- Recalculate for single agent or all agents
- Progress indicator during calculation
- Show before/after comparison
- Schedule automatic recalculations

### US-ADMIN-RANK-005: View Ranking History
**As a** platform administrator  
**I want to** see how rankings changed over time  
**So that** I can identify performance trends

**Acceptance Criteria:**
- Time-series chart of ranking positions
- Identify when models gained/lost positions
- Correlate with performance events
- Export historical data

---

## 🖼️ Views & Wireframes

### View 1: Rankings Dashboard

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│  🏆 Model Rankings                              [⚙️ Configure] [🔄 Recalculate All] │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                      │
│  ┌─ Summary ───────────────────────────────────────────────────────────────────────┐│
│  │  🤖 6 Agent Types    🏆 9 Models Ranked    ⏱️ Last Updated: 15 min ago         ││
│  │     All configured      Across providers     Next: in 45 min                    ││
│  └─────────────────────────────────────────────────────────────────────────────────┘│
│                                                                                      │
│  Agent Type: [All Agents ▼]                                                         │
│                                                                                      │
│  ┌─────────────────────────────────────────────────────────────────────────────────┐│
│  │ 🔄 SWAP AGENT                                    [📊 History] [🔄 Recalculate] ││
│  │                                                                                  ││
│  │ ┌──────┬─────────────────────────┬─────────┬─────────┬─────────┬──────────────┐ ││
│  │ │ RANK │ MODEL                   │ SCORE   │ SUCCESS │ LATENCY │ COST EFF     │ ││
│  │ ├──────┼─────────────────────────┼─────────┼─────────┼─────────┼──────────────┤ ││
│  │ │ 🥇 1 │ gemini-1.5-pro          │ 92.5    │ 99.1%   │ 820ms   │ 85.2         │ ││
│  │ │      │ 🔷 Vertex AI            │ ████████│ ████████│ ███████ │ ████████     │ ││
│  │ ├──────┼─────────────────────────┼─────────┼─────────┼─────────┼──────────────┤ ││
│  │ │ 🥈 2 │ claude-3-sonnet         │ 88.1    │ 97.2%   │ 980ms   │ 82.1         │ ││
│  │ │      │ 🟠 AWS Bedrock          │ ███████ │ ███████ │ ██████  │ ███████      │ ││
│  │ ├──────┼─────────────────────────┼─────────┼─────────┼─────────┼──────────────┤ ││
│  │ │ 🥉 3 │ llama-3.1-405b          │ 84.3    │ 95.8%   │ 1,100ms │ 88.5         │ ││
│  │ │      │ 🟣 DeepInfra            │ ██████  │ ██████  │ █████   │ █████████    │ ││
│  │ ├──────┼─────────────────────────┼─────────┼─────────┼─────────┼──────────────┤ ││
│  │ │   4  │ mixtral-8x22b           │ 78.2    │ 94.1%   │ 680ms   │ 91.2         │ ││
│  │ │      │ 🟣 DeepInfra            │ █████   │ █████   │ ████████│ ██████████   │ ││
│  │ └──────┴─────────────────────────┴─────────┴─────────┴─────────┴──────────────┘ ││
│  │                                                                                  ││
│  │ Ranking Formula: 0.4×Success + 0.35×Latency + 0.25×CostEfficiency              ││
│  └─────────────────────────────────────────────────────────────────────────────────┘│
│                                                                                      │
│  ┌─────────────────────────────────────────────────────────────────────────────────┐│
│  │ 📊 RESEARCHER AGENT                              [📊 History] [🔄 Recalculate] ││
│  │                                                                                  ││
│  │ ┌──────┬─────────────────────────┬─────────┬─────────┬─────────┬──────────────┐ ││
│  │ │ RANK │ MODEL                   │ SCORE   │ SUCCESS │ LATENCY │ COST EFF     │ ││
│  │ ├──────┼─────────────────────────┼─────────┼─────────┼─────────┼──────────────┤ ││
│  │ │ 🥇 1 │ gemini-1.5-pro          │ 91.2    │ 98.2%   │ 1,050ms │ 82.1         │ ││
│  │ │  📌  │ 🔷 Vertex AI  [PINNED]  │         │         │         │              │ ││
│  │ ├──────┼─────────────────────────┼─────────┼─────────┼─────────┼──────────────┤ ││
│  │ │ 🥈 2 │ llama-3.1-405b          │ 87.5    │ 96.5%   │ 1,350ms │ 86.2         │ ││
│  │ │      │ 🟣 DeepInfra            │         │         │         │              │ ││
│  │ └──────┴─────────────────────────┴─────────┴─────────┴─────────┴──────────────┘ ││
│  │                                                                                  ││
│  │ ⚠️ Manual override active: gemini-1.5-pro pinned to #1 (expires in 22h)        ││
│  └─────────────────────────────────────────────────────────────────────────────────┘│
│                                                                                      │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

### View 2: Ranking Configuration

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│  ⚙️ Ranking Configuration                                                   [✕]     │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                      │
│  FACTOR WEIGHTS                                                                     │
│  ┌───────────────────────────────────────────────────────────────────────────────┐  │
│  │                                                                               │  │
│  │  Success Rate Weight                                                          │  │
│  │  ┌─────────────────────────────────────────────────────────────────────────┐  │  │
│  │  │     |────────────────●──────────────────|           40%                 │  │  │
│  │  └─────────────────────────────────────────────────────────────────────────┘  │  │
│  │  Higher success rate = higher ranking                                        │  │
│  │                                                                               │  │
│  │  Latency Weight                                                               │  │
│  │  ┌─────────────────────────────────────────────────────────────────────────┐  │  │
│  │  │     |──────────────●────────────────────|           35%                 │  │  │
│  │  └─────────────────────────────────────────────────────────────────────────┘  │  │
│  │  Lower latency = higher ranking                                              │  │
│  │                                                                               │  │
│  │  Cost Efficiency Weight                                                       │  │
│  │  ┌─────────────────────────────────────────────────────────────────────────┐  │  │
│  │  │     |──────────●────────────────────────|           25%                 │  │  │
│  │  └─────────────────────────────────────────────────────────────────────────┘  │  │
│  │  Lower cost per successful request = higher ranking                          │  │
│  │                                                                               │  │
│  │  Total: 100% ✓                                                               │  │
│  │                                                                               │  │
│  └───────────────────────────────────────────────────────────────────────────────┘  │
│                                                                                      │
│  CALCULATION SETTINGS                                                               │
│  ┌───────────────────────────────────────────────────────────────────────────────┐  │
│  │                                                                               │  │
│  │  Lookback Period                   Minimum Requests                          │  │
│  │  ┌─────────────────────────┐      ┌─────────────────────────┐                │  │
│  │  │ [24 hours ▼]           │      │ [100                   ]│                │  │
│  │  └─────────────────────────┘      └─────────────────────────┘                │  │
│  │  Time window for metrics          Required samples to rank                   │  │
│  │                                                                               │  │
│  │  Recalculation Interval            Smoothing Factor                          │  │
│  │  ┌─────────────────────────┐      ┌─────────────────────────┐                │  │
│  │  │ [1 hour ▼]             │      │ [0.3                   ]│                │  │
│  │  └─────────────────────────┘      └─────────────────────────┘                │  │
│  │  How often to recalculate         EMA smoothing (0-1)                        │  │
│  │                                                                               │  │
│  └───────────────────────────────────────────────────────────────────────────────┘  │
│                                                                                      │
│  ─────────────────────────────────────────────────────────────────────────────────  │
│                                                                                      │
│  [Reset to Defaults]                               [Cancel]        [Save Changes]   │
│                                                                                      │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

### View 3: Override Ranking Modal

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│  📌 Override Ranking: SwapAgent                                             [✕]     │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                      │
│  Current Rankings (Auto-calculated)                                                 │
│  ┌───────────────────────────────────────────────────────────────────────────────┐  │
│  │  🥇 gemini-1.5-pro (92.5)  →  🥈 claude-3-sonnet (88.1)  →  🥉 llama-3.1    │  │
│  └───────────────────────────────────────────────────────────────────────────────┘  │
│                                                                                      │
│  SELECT MODEL TO PIN                                                                │
│  ┌───────────────────────────────────────────────────────────────────────────────┐  │
│  │                                                                               │  │
│  │  Model                              Pin to Position                          │  │
│  │  ┌─────────────────────────────┐   ┌─────────────────────────┐               │  │
│  │  │ [claude-3-sonnet ▼]        │   │ [🥇 #1 ▼]              │               │  │
│  │  └─────────────────────────────┘   └─────────────────────────┘               │  │
│  │                                                                               │  │
│  │  Override Duration                                                           │  │
│  │  ┌─────────────────────────────────────────────────────────────────────────┐  │  │
│  │  │ [ ] 1 hour   [ ] 6 hours   [●] 24 hours   [ ] 7 days   [ ] Permanent   │  │  │
│  │  └─────────────────────────────────────────────────────────────────────────┘  │  │
│  │                                                                               │  │
│  │  Reason for Override *                                                       │  │
│  │  ┌─────────────────────────────────────────────────────────────────────────┐  │  │
│  │  │ Testing claude-3-sonnet for swap quality improvement                    │  │  │
│  │  └─────────────────────────────────────────────────────────────────────────┘  │  │
│  │                                                                               │  │
│  └───────────────────────────────────────────────────────────────────────────────┘  │
│                                                                                      │
│  ⚠️ WARNING: Manual overrides bypass the adaptive ranking system. The pinned       │
│     model will be used regardless of performance until the override expires.        │
│                                                                                      │
│  ─────────────────────────────────────────────────────────────────────────────────  │
│                                                                                      │
│  [Cancel]                                                    [Apply Override]       │
│                                                                                      │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 🔌 API Endpoints

### Get Rankings

```typescript
// GET /admin/llm/rankings?agent_type=swap_agent
// Get current rankings

interface GetRankingsResponse {
  success: true;
  data: {
    rankings: AgentRanking[];
    config: RankingConfig;
    last_calculated_at: string;
    next_calculation_at: string;
  };
}

interface AgentRanking {
  agent_type: string;
  agent_display_name: string;
  models: RankedModel[];
  override_active: boolean;
  override_expires_at?: string;
}

interface RankedModel {
  model_id: string;
  model_name: string;
  provider_name: string;
  rank: number;
  score: number;
  factors: {
    success_rate: number;
    success_score: number;
    latency_ms: number;
    latency_score: number;
    cost_efficiency: number;
    cost_score: number;
  };
  is_pinned: boolean;
  pin_reason?: string;
  pin_expires_at?: string;
  request_count: number;
}

interface RankingConfig {
  weights: {
    success: number;
    latency: number;
    cost: number;
  };
  lookback_hours: number;
  min_requests: number;
  recalculation_interval_minutes: number;
  smoothing_factor: number;
}
```

### Update Ranking Config

```typescript
// PUT /admin/llm/rankings/config
// Update ranking configuration

interface UpdateRankingConfigRequest {
  weights?: {
    success?: number;
    latency?: number;
    cost?: number;
  };
  lookback_hours?: number;
  min_requests?: number;
  recalculation_interval_minutes?: number;
  smoothing_factor?: number;
}
```

### Create Override

```typescript
// POST /admin/llm/rankings/override
// Create ranking override

interface CreateOverrideRequest {
  agent_type: string;
  model_id: string;
  pin_position: number;
  duration_hours: number | null;  // null = permanent
  reason: string;
}

interface CreateOverrideResponse {
  success: true;
  data: {
    override_id: string;
    expires_at: string | null;
    previous_ranking: RankedModel[];
    new_ranking: RankedModel[];
  };
}
```

### Trigger Recalculation

```typescript
// POST /admin/llm/rankings/recalculate
// Trigger ranking recalculation

interface RecalculateRequest {
  agent_types?: string[];  // Empty = all
}

interface RecalculateResponse {
  success: true;
  data: {
    job_id: string;
    agents_to_process: number;
    estimated_seconds: number;
  };
}
```

---

## 📊 Data Structures

### Module State

```typescript
interface RankingsModuleState {
  rankings: AgentRanking[];
  config: RankingConfig | null;
  selectedAgent: string | null;
  
  loading: {
    rankings: boolean;
    config: boolean;
    recalculate: boolean;
    override: boolean;
  };
  
  configModalOpen: boolean;
  overrideModalOpen: boolean;
  overrideForm: Partial<CreateOverrideRequest>;
  
  historyModalOpen: boolean;
  historyData: RankingHistory | null;
  
  filters: {
    agentType: string | null;
  };
}
```

---

## 🎨 Component Specifications

### RankingTable

```typescript
interface RankingTableProps {
  ranking: AgentRanking;
  onViewHistory: () => void;
  onRecalculate: () => void;
  onOverride: (modelId: string) => void;
  onRemoveOverride: (modelId: string) => void;
}
```

### RankingBar

```typescript
interface RankingBarProps {
  score: number;
  maxScore: number;
  color?: string;
  showLabel?: boolean;
}
```

### OverrideModal

```typescript
interface OverrideModalProps {
  agentType: string;
  currentRankings: RankedModel[];
  onSubmit: (data: CreateOverrideRequest) => void;
  onCancel: () => void;
  loading?: boolean;
}
```

---

## 🎬 Motion Design

```typescript
const rankingsAnimations = {
  rankChange: {
    y: [0, -10, 0],
    transition: { duration: 0.3 }
  },
  
  pinIndicator: {
    scale: [1, 1.2, 1],
    rotate: [0, 10, 0],
    transition: { duration: 0.5 }
  },
  
  scoreBarFill: {
    width: '100%',
    transition: { duration: 0.8, ease: 'easeOut' }
  },
  
  recalculateSpinner: {
    rotate: 360,
    transition: { duration: 1, repeat: Infinity, ease: 'linear' }
  }
};
```

---

## ⌨️ Keyboard Shortcuts

```typescript
const rankingsShortcuts = {
  'mod+r': 'Recalculate all rankings',
  'mod+o': 'Create override',
  'mod+c': 'Open configuration',
  'h': 'View history',
  '1-6': 'Filter by agent type',
};
```

---

## ⚠️ Error Handling

```typescript
const rankingsErrorCodes = {
  RANK_VAL_001: 'Weights must sum to 100%',
  RANK_VAL_002: 'Override reason is required',
  RANK_VAL_003: 'Invalid pin position',
  RANK_BUS_001: 'Model has insufficient data for ranking',
  RANK_BUS_002: 'Override conflicts with existing override',
  RANK_SYS_001: 'Recalculation job failed',
};
```

---

*Document Version: 1.0*  
*Last Updated: December 1, 2025*  
*Module: Model Rankings*
