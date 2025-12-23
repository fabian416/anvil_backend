# Intelligence Ops Module Implementation

> **Complete TypeScript/React Implementation for Intelligence Ops Module**  
> **Methodology**: CTO Engineering Framework (First Principles + Design Thinking + Systems Thinking)

## 📖 Module Overview

The **Intelligence Ops** module is the control center for the LLM Gateway. It enables configuration and optimization of the AI infrastructure, including models, budgets, circuit breakers, rankings, telemetry, agents, and distillation.

### Key Capabilities
1. **LLM Configuration**: Enable/disable models, manage providers, configure costs
2. **Budgets**: Set spending limits with alerts and hard/soft limits
3. **Circuit Breakers**: Monitor reliability, reset failed providers
4. **Rankings**: View and manage model rankings per agent with overrides
5. **Telemetry**: Monitor LLM orchestration metrics, costs, and performance
6. **Agent Management**: View and monitor AI agents
7. **Distillation**: Manage static responses and optimization
8. **Distillation Validation**: Review and approve validation responses

### Business Value
- **Cost Control**: Monitor and limit LLM spending
- **Reliability**: Ensure AI services are available and performing
- **Optimization**: Improve model selection and performance
- **Transparency**: Full visibility into AI operations

---

## 🎨 UX/UI Specifications

### Design Principles (First Principles Analysis)

**Essential Problem**: Admins need to configure AI behavior and monitor costs without complexity.

**Root Cause Analysis**:
- **Complexity**: Too many configuration options cause confusion
- **Solution**: Tabbed interface, progressive disclosure, visual feedback, cost impact display

**Design Decisions**:
1. **Visual Feedback**: Use color (Green/Red) heavily for state indicators
2. **Transparency**: Always show estimated cost impact of changes
3. **Progressive Disclosure**: Summary → Configuration → Advanced
4. **Tabbed Interface**: Separate submodules into tabs for organization
5. **Real-time Updates**: WebSocket for live metrics

### Trade-off Analysis (Design Thinking)

**Key Design Decisions with Trade-offs**:

| Decision | Alternative | Trade-off | Rationale |
|----------|------------|-----------|-----------|
| **Tabbed Interface** | Single Page | Organization vs. Navigation | Tabs organize 8 submodules, but require navigation |
| **Cost Impact Display** | Hidden Costs | Transparency vs. Complexity | Showing cost impact improves decision-making, but adds UI complexity |
| **Real-time Updates** | Manual Refresh | Current vs. Performance | Real-time provides current data, but requires WebSocket connections |
| **Ranking Override System** | Fixed Rankings | Flexibility vs. Maintenance | Overrides allow emergency adjustments, but require careful management |

### Visual Design

#### Layout Structure
```
┌─────────────────────────────────────────────────────────┐
│              Intelligence Ops                            │
│  ┌───────────────────────────────────────────────────┐  │
│  │ Tabs: [Models] [Budgets] [Circuit Breakers] ...   │  │
│  └───────────────────────────────────────────────────┘  │
│  ┌───────────────────────────────────────────────────┐  │
│  │ LLM Models                                         │  │
│  │ ┌──────────────┐  ┌──────────────┐               │  │
│  │ │ Model Card   │  │ Model Card   │               │  │
│  │ │ Gemini Pro   │  │ GPT-4        │               │  │
│  │ │ ✅ Enabled   │  │ ✅ Enabled   │               │  │
│  │ │ $0.00125/1k │  │ $0.03/1k     │               │  │
│  │ └──────────────┘  └──────────────┘               │  │
│  └───────────────────────────────────────────────────┘  │
│  ┌───────────────────────────────────────────────────┐  │
│  │ Budgets                                           │  │
│  │ ┌──────────────┐                                  │  │
│  │ │ Daily Budget │                                  │  │
│  │ │ $500.00      │                                  │  │
│  │ │ Used: 25.5%  │                                  │  │
│  │ │ [Progress]   │                                  │  │
│  │ └──────────────┘                                  │  │
│  └───────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
```

#### Color Palette
- **Enabled**: `#10B981` (Green)
- **Disabled**: `#6B7280` (Gray)
- **Circuit Breaker Open**: `#EF4444` (Red)
- **Circuit Breaker Closed**: `#10B981` (Green)
- **Warning**: `#F59E0B` (Amber) - Budget thresholds
- **Critical**: `#EF4444` (Red) - Budget exceeded
- **Info**: `#3B82F6` (Blue) - Neutral status

#### Component Specifications

##### Model Card Component
```typescript
interface ModelCardProps {
  model: Model;
  onToggle: (modelId: string, enabled: boolean) => void;
  onEdit: (modelId: string) => void;
  onViewPerformance: (modelId: string) => void;
}

export const ModelCard: React.FC<ModelCardProps> = ({
  model,
  onToggle,
  onEdit,
  onViewPerformance,
}) => {
  return (
    <div className="bg-white rounded-lg border-2 border-gray-200 p-6 hover:shadow-md transition">
      <div className="flex items-start justify-between mb-4">
        <div>
          <h3 className="text-lg font-semibold">{model.display_name}</h3>
          <p className="text-sm text-gray-500">{model.provider_name}</p>
        </div>
        <ToggleSwitch
          enabled={model.is_enabled}
          onChange={(enabled) => onToggle(model.id, enabled)}
        />
      </div>
      
      <div className="space-y-2 mb-4">
        <div className="flex justify-between text-sm">
          <span className="text-gray-600">Input Cost:</span>
          <span className="font-medium">${model.cost_per_1k_input}/1k</span>
        </div>
        <div className="flex justify-between text-sm">
          <span className="text-gray-600">Output Cost:</span>
          <span className="font-medium">${model.cost_per_1k_output}/1k</span>
        </div>
        <div className="flex justify-between text-sm">
          <span className="text-gray-600">Context Window:</span>
          <span className="font-medium">{model.context_window.toLocaleString()}</span>
        </div>
      </div>

      {model.circuit_breaker_state === 'open' && (
        <div className="mb-4 p-2 bg-red-50 border border-red-200 rounded text-sm text-red-800">
          ⚠️ Circuit breaker is OPEN
        </div>
      )}

      <div className="flex space-x-2">
        <button
          onClick={() => onEdit(model.id)}
          className="flex-1 px-4 py-2 bg-gray-100 hover:bg-gray-200 rounded text-sm"
        >
          Edit
        </button>
        <button
          onClick={() => onViewPerformance(model.id)}
          className="flex-1 px-4 py-2 bg-blue-100 hover:bg-blue-200 rounded text-sm"
        >
          Performance
        </button>
      </div>
    </div>
  );
};
```

##### Budget Card Component
```typescript
interface BudgetCardProps {
  budget: Budget;
  onEdit: (budgetId: string) => void;
  onDelete: (budgetId: string) => void;
}

export const BudgetCard: React.FC<BudgetCardProps> = ({
  budget,
  onEdit,
  onDelete,
}) => {
  const percentageUsed = budget.percentage_used;
  const isWarning = percentageUsed >= budget.warning_threshold_percent;
  const isCritical = percentageUsed >= budget.critical_threshold_percent;

  const progressColor = isCritical
    ? 'bg-red-500'
    : isWarning
    ? 'bg-amber-500'
    : 'bg-blue-500';

  return (
    <div className="bg-white rounded-lg border-2 border-gray-200 p-6">
      <div className="flex items-start justify-between mb-4">
        <div>
          <h3 className="text-lg font-semibold">{budget.name}</h3>
          <p className="text-sm text-gray-500 capitalize">{budget.budget_type} budget</p>
        </div>
        <div className="text-right">
          <div className="text-2xl font-bold">${budget.budget_amount_usd.toFixed(2)}</div>
          <div className="text-sm text-gray-500">
            Used: ${budget.current_spend_usd.toFixed(2)}
          </div>
        </div>
      </div>

      <div className="mb-4">
        <div className="flex justify-between text-sm mb-1">
          <span>{percentageUsed.toFixed(1)}% used</span>
          <span>{budget.is_hard_limit ? 'Hard Limit' : 'Soft Limit'}</span>
        </div>
        <div className="w-full bg-gray-200 rounded-full h-2">
          <div
            className={`h-2 rounded-full transition-all ${progressColor}`}
            style={{ width: `${Math.min(percentageUsed, 100)}%` }}
          />
        </div>
      </div>

      {isCritical && (
        <div className="mb-4 p-2 bg-red-50 border border-red-200 rounded text-sm text-red-800">
          ⚠️ Critical threshold exceeded
        </div>
      )}

      <div className="flex space-x-2">
        <button
          onClick={() => onEdit(budget.id)}
          className="flex-1 px-4 py-2 bg-gray-100 hover:bg-gray-200 rounded text-sm"
        >
          Edit
        </button>
        <button
          onClick={() => onDelete(budget.id)}
          className="px-4 py-2 bg-red-100 hover:bg-red-200 rounded text-sm"
        >
          Delete
        </button>
      </div>
    </div>
  );
};
```

##### Toggle Switch Component
```typescript
interface ToggleSwitchProps {
  enabled: boolean;
  onChange: (enabled: boolean) => void;
  label?: string;
  disabled?: boolean;
}

export const ToggleSwitch: React.FC<ToggleSwitchProps> = ({
  enabled,
  onChange,
  label,
  disabled = false,
}) => {
  return (
    <label className="flex items-center cursor-pointer">
      {label && <span className="mr-3 text-sm text-gray-700">{label}</span>}
      <div className="relative">
        <input
          type="checkbox"
          checked={enabled}
          onChange={(e) => onChange(e.target.checked)}
          disabled={disabled}
          className="sr-only"
        />
        <div
          className={`
            w-14 h-8 rounded-full transition-colors
            ${enabled ? 'bg-green-500' : 'bg-gray-300'}
            ${disabled ? 'opacity-50 cursor-not-allowed' : ''}
          `}
        >
          <div
            className={`
              absolute top-1 left-1 w-6 h-6 bg-white rounded-full transition-transform
              ${enabled ? 'transform translate-x-6' : ''}
            `}
          />
        </div>
      </div>
    </label>
  );
};
```

##### Cost Impact Component
```typescript
interface CostImpactProps {
  currentCost: number;
  projectedCost: number;
  changePercent: number;
}

export const CostImpact: React.FC<CostImpactProps> = ({
  currentCost,
  projectedCost,
  changePercent,
}) => {
  const isIncrease = changePercent > 0;
  const isDecrease = changePercent < 0;

  return (
    <div className="p-4 bg-blue-50 border border-blue-200 rounded-lg">
      <h4 className="text-sm font-medium text-blue-900 mb-2">Cost Impact</h4>
      <div className="space-y-1">
        <div className="flex justify-between text-sm">
          <span className="text-blue-700">Current:</span>
          <span className="font-medium">${currentCost.toFixed(2)}</span>
        </div>
        <div className="flex justify-between text-sm">
          <span className="text-blue-700">Projected:</span>
          <span className={`font-medium ${isIncrease ? 'text-red-600' : isDecrease ? 'text-green-600' : ''}`}>
            ${projectedCost.toFixed(2)}
          </span>
        </div>
        <div className="flex justify-between text-sm">
          <span className="text-blue-700">Change:</span>
          <span className={`font-medium ${isIncrease ? 'text-red-600' : isDecrease ? 'text-green-600' : ''}`}>
            {isIncrease ? '+' : ''}{changePercent.toFixed(1)}%
          </span>
        </div>
      </div>
    </div>
  );
};
```

### Responsive Breakpoints

**Mobile** (< 640px):
- Single column layout
- Stacked model/budget cards
- Bottom sheet for actions
- Tab navigation at bottom

**Tablet** (640px - 1024px):
- Two-column card grid
- Side panel for details
- Tab navigation at top

**Desktop** (> 1024px):
- Three-column card grid
- Sidebar for filters
- Tab navigation at top
- Modal for detailed views

### Accessibility Requirements

1. **Screen Readers**:
   - Announce model status changes
   - Describe cost impact
   - Label all toggle switches
   - Announce budget threshold warnings

2. **Keyboard Navigation**:
   - Tab through all cards
   - Enter to toggle/enable
   - Escape to close modals
   - Arrow keys for tab navigation

3. **Color Contrast**:
   - All text: 4.5:1 minimum
   - Status indicators: 3:1 minimum
   - Progress bars: 3:1 minimum

---

## 🔌 API Endpoints

See `03-Intelligence-Ops/API.md` for complete API documentation.

### Key Endpoints Summary

1. **LLM Models**: `GET /api/admin/llm/models`, `PUT /api/admin/llm/models/{model_id}`
2. **Budgets**: `GET /api/admin/llm/budgets`, `POST /api/admin/llm/budgets`
3. **Circuit Breakers**: `GET /api/admin/llm/circuit-breakers`, `POST /api/admin/llm/circuit-breakers/{breaker_id}/reset`
4. **Rankings**: `GET /api/admin/llm/rankings`, `PUT /api/admin/llm/rankings/weights`
5. **Telemetry**: `GET /api/admin/llm/telemetry/overview`, `GET /api/admin/llm/telemetry/timeseries`
6. **Agents**: `GET /api/admin/agents/`
7. **Distillation**: `GET /api/admin/distillation/static-responses`, `POST /api/admin/distillation/static-responses`
8. **Distillation Validation**: `GET /api/admin/distillation/validation/responses`, `PATCH /api/admin/distillation/validation/responses/{response_id}/approve`

---

## 🔄 User Flows & Use Cases

### Use Case 1: Configure LLM Model

**Actor**: Admin User  
**Goal**: Enable/disable model or update configuration  
**Preconditions**: User is authenticated and has admin role

#### Flow Steps

1. **Entry Point**: User navigates to Intelligence Ops → Models tab
2. **Initial State**: 
   - Models list loads
   - Show loading skeleton
   - Call `GET /api/admin/llm/models`
3. **System Response**:
   - Display model cards in grid
   - Show enabled/disabled status
   - Show cost information
   - Show circuit breaker status
4. **User Action**: User toggles model enabled/disabled
5. **System Response**:
   - Show confirmation modal with cost impact
   - Display projected cost change
6. **User Action**: User confirms change
7. **System Response**:
   - Call `PUT /api/admin/llm/models/{model_id}`
   - Optimistically update UI
   - Show success toast
8. **Success Path**:
   - Model status updates
   - Cost impact is visible
   - UI reflects new state

#### Success Criteria
- [ ] Model configuration updates successfully
- [ ] Cost impact is clearly displayed
- [ ] Confirmation prevents mistakes
- [ ] Error handling works

---

### Use Case 2: Create Budget

**Actor**: Admin User  
**Goal**: Set spending limit with alerts  
**Preconditions**: User is authenticated and has admin role

#### Flow Steps

1. **Entry Point**: User navigates to Intelligence Ops → Budgets tab
2. **Initial State**: 
   - Budgets list loads
   - Show "Create Budget" button
3. **User Action**: User clicks "Create Budget"
4. **System Response**:
   - Open create budget modal
   - Show form fields
5. **User Action**: User fills form (name, type, amount, thresholds)
6. **System Response**:
   - Validate form
   - Show cost impact preview
7. **User Action**: User submits form
8. **System Response**:
   - Call `POST /api/admin/llm/budgets`
   - Show loading state
9. **System Response**:
   - On success: Add budget to list, show success toast
   - On error: Show error message

#### Success Criteria
- [ ] Budget is created successfully
- [ ] Form validation works
- [ ] Cost impact is displayed
- [ ] Error handling works

---

### Use Case 3: Monitor Telemetry

**Actor**: Admin User  
**Goal**: View LLM usage metrics and costs  
**Preconditions**: User is authenticated and has admin role

#### Flow Steps

1. **Entry Point**: User navigates to Intelligence Ops → Telemetry tab
2. **Initial State**: 
   - Telemetry overview loads
   - Call `GET /api/admin/llm/telemetry/overview`
3. **System Response**:
   - Display overview metrics
   - Show cost breakdown
   - Show provider performance
   - Show agent usage
4. **User Action**: User selects time period (24h, 7d, 30d)
5. **System Response**:
   - Update time period filter
   - Refetch data
   - Update charts and metrics
6. **User Action**: User clicks "View Time Series"
7. **System Response**:
   - Load `GET /api/admin/llm/telemetry/timeseries`
   - Display time series chart
   - Show trends

#### Success Criteria
- [ ] Telemetry loads quickly
- [ ] Time period selection works
- [ ] Charts display correctly
- [ ] Real-time updates work

---

## 📁 File Structure

```
src/modules/admin/intelligence-ops/
├── IntelligenceOps.tsx
├── IntelligenceOps.types.ts
├── IntelligenceOps.hooks.ts
├── IntelligenceOps.service.ts
├── components/
│   ├── ModelCard.tsx
│   ├── BudgetCard.tsx
│   ├── ToggleSwitch.tsx
│   ├── CostImpact.tsx
│   ├── CircuitBreakerStatus.tsx
│   ├── RankingTable.tsx
│   ├── TelemetryChart.tsx
│   ├── AgentList.tsx
│   ├── DistillationConfig.tsx
│   └── ValidationQueue.tsx
├── tabs/
│   ├── ModelsTab.tsx
│   ├── BudgetsTab.tsx
│   ├── CircuitBreakersTab.tsx
│   ├── RankingsTab.tsx
│   ├── TelemetryTab.tsx
│   ├── AgentsTab.tsx
│   ├── DistillationTab.tsx
│   └── ValidationTab.tsx
├── hooks/
│   ├── useModels.ts
│   ├── useBudgets.ts
│   ├── useCircuitBreakers.ts
│   ├── useRankings.ts
│   ├── useTelemetry.ts
│   ├── useAgents.ts
│   ├── useDistillation.ts
│   ├── useValidation.ts
│   └── useIntelligenceOpsWebSocket.ts
├── services/
│   ├── llm.service.ts
│   ├── budget.service.ts
│   ├── circuitBreaker.service.ts
│   ├── ranking.service.ts
│   ├── telemetry.service.ts
│   ├── agent.service.ts
│   ├── distillation.service.ts
│   └── validation.service.ts
└── __tests__/
    ├── IntelligenceOps.test.tsx
    ├── ModelCard.test.tsx
    └── services.test.ts
```

## 🔑 Key Implementation Files

### 1. Intelligence Ops Module

#### `IntelligenceOps.service.ts`
```typescript
import { apiClient } from '@/api/client';
import type {
  ModelListResponse,
  BudgetResponse,
  CircuitBreakerResponse,
  RankingResponse,
  TelemetryResponse,
} from './IntelligenceOps.types';

export const intelligenceOpsService = {
  // LLM Models
  async listModels(params?: {
    provider_id?: string;
    is_enabled?: boolean;
    tier?: string;
  }): Promise<ModelListResponse> {
    const response = await apiClient.get<ModelListResponse>(
      '/api/admin/llm/models',
      { params }
    );
    return response.data;
  },

  async updateModel(
    modelId: string,
    data: UpdateModelRequest
  ): Promise<ModelListResponse> {
    const response = await apiClient.put<ModelListResponse>(
      `/api/admin/llm/models/${modelId}`,
      data
    );
    return response.data;
  },

  // Budgets
  async listBudgets(): Promise<BudgetResponse> {
    const response = await apiClient.get<BudgetResponse>(
      '/api/admin/llm/budgets'
    );
    return response.data;
  },

  async createBudget(data: CreateBudgetRequest): Promise<BudgetResponse> {
    const response = await apiClient.post<BudgetResponse>(
      '/api/admin/llm/budgets',
      data
    );
    return response.data;
  },

  async updateBudget(
    budgetId: string,
    data: UpdateBudgetRequest
  ): Promise<BudgetResponse> {
    const response = await apiClient.put<BudgetResponse>(
      `/api/admin/llm/budgets/${budgetId}`,
      data
    );
    return response.data;
  },

  async deleteBudget(budgetId: string): Promise<void> {
    await apiClient.delete(`/api/admin/llm/budgets/${budgetId}`);
  },

  // Circuit Breakers
  async listCircuitBreakers(): Promise<CircuitBreakerResponse> {
    const response = await apiClient.get<CircuitBreakerResponse>(
      '/api/admin/llm/circuit-breakers'
    );
    return response.data;
  },

  async resetCircuitBreaker(breakerId: string): Promise<CircuitBreakerResponse> {
    const response = await apiClient.post<CircuitBreakerResponse>(
      `/api/admin/llm/circuit-breakers/${breakerId}/reset`
    );
    return response.data;
  },

  // Rankings
  async getRankings(agentType?: string): Promise<RankingResponse> {
    const params = agentType ? { agent_type: agentType } : {};
    const response = await apiClient.get<RankingResponse>(
      '/api/admin/llm/rankings',
      { params }
    );
    return response.data;
  },

  async updateRankingWeights(data: UpdateWeightsRequest): Promise<RankingResponse> {
    const response = await apiClient.put<RankingResponse>(
      '/api/admin/llm/rankings/weights',
      data
    );
    return response.data;
  },

  async recalculateRankings(agentType?: string): Promise<RankingResponse> {
    const response = await apiClient.post<RankingResponse>(
      '/api/admin/llm/rankings/recalculate',
      agentType ? { agent_type: agentType } : {}
    );
    return response.data;
  },

  // Telemetry
  async getTelemetryOverview(period?: string): Promise<TelemetryResponse> {
    const params = period ? { period } : {};
    const response = await apiClient.get<TelemetryResponse>(
      '/api/admin/llm/telemetry/overview',
      { params }
    );
    return response.data;
  },

  async getTelemetryTimeSeries(params: {
    metric?: string;
    period?: string;
    group_by?: string;
    interval?: string;
  }): Promise<TelemetryResponse> {
    const response = await apiClient.get<TelemetryResponse>(
      '/api/admin/llm/telemetry/timeseries',
      { params }
    );
    return response.data;
  },

  async getCostAnalysis(period?: string): Promise<TelemetryResponse> {
    const params = period ? { period } : {};
    const response = await apiClient.get<TelemetryResponse>(
      '/api/admin/llm/telemetry/cost',
      { params }
    );
    return response.data;
  },

  // Agents
  async listAgents(): Promise<AgentRead[]> {
    const response = await apiClient.get<AgentRead[]>(
      '/api/admin/agents/'
    );
    return response.data;
  },

  // Distillation
  async listStaticResponses(params?: {
    intent?: string;
    is_active?: boolean;
  }): Promise<StaticResponseResponse[]> {
    const response = await apiClient.get<StaticResponseResponse[]>(
      '/api/admin/distillation/static-responses',
      { params }
    );
    return response.data;
  },

  async createStaticResponse(
    data: StaticResponseCreate
  ): Promise<StaticResponseResponse> {
    const response = await apiClient.post<StaticResponseResponse>(
      '/api/admin/distillation/static-responses',
      data
    );
    return response.data;
  },

  // Distillation Validation
  async listValidationResponses(params?: {
    status?: string;
    intent?: string;
    limit?: number;
    offset?: number;
  }): Promise<ValidationResponse[]> {
    const response = await apiClient.get<ValidationResponse[]>(
      '/api/admin/distillation/validation/responses',
      { params }
    );
    return response.data;
  },

  async approveValidationResponse(
    responseId: string,
    notes?: string
  ): Promise<void> {
    await apiClient.patch(
      `/api/admin/distillation/validation/responses/${responseId}/approve`,
      notes ? { notes } : {}
    );
  },

  async rejectValidationResponse(
    responseId: string,
    reason: string,
    notes?: string
  ): Promise<void> {
    await apiClient.patch(
      `/api/admin/distillation/validation/responses/${responseId}/reject`,
      { reason, notes }
    );
  },
};
```

#### `IntelligenceOps.types.ts`
```typescript
export interface Model {
  id: string;                            // UUID
  provider_id: string;                   // UUID
  provider_name: string;
  model_id: string;
  display_name: string;
  model_family: string;
  capabilities: string[];
  context_window: number;
  cost_per_1k_input: number;
  cost_per_1k_output: number;
  carousel_position: number;
  tier: string;
  is_enabled: boolean;
  circuit_breaker_state: string | null;
}

export interface Budget {
  id: string;                             // UUID
  name: string;
  budget_type: 'daily' | 'weekly' | 'monthly';
  budget_amount_usd: number;
  current_spend_usd: number;
  percentage_used: number;                // 0-100
  warning_threshold_percent: number;
  critical_threshold_percent: number;
  is_hard_limit: boolean;
  period_start: string;                   // ISO 8601
  period_end: string;                    // ISO 8601
}

export interface CircuitBreaker {
  id: string;                             // UUID
  entity_type: string;
  entity_id: string;                      // UUID
  entity_name: string;
  state: 'closed' | 'open' | 'half_open';
  failure_count: number;
  consecutive_failures: number;
  last_failure_at: string | null;         // ISO 8601
  config: {
    failure_threshold: number;
    success_threshold: number;
    timeout_seconds: number;
  };
}

export interface AgentRead {
  type: AgentType;
  name: string;
  description: string;
  is_active: boolean;
}

type AgentType = 'TRADING' | 'RESEARCH' | 'YIELD_FARMING' | 'RISK_ANALYSIS' | 'PORTFOLIO';
```

#### `IntelligenceOps.hooks.ts`
```typescript
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { intelligenceOpsService } from './IntelligenceOps.service';
import { useIntelligenceOpsWebSocket } from './hooks/useIntelligenceOpsWebSocket';

export function useModels(params?: {
  provider_id?: string;
  is_enabled?: boolean;
  tier?: string;
}) {
  return useQuery({
    queryKey: ['admin', 'llm', 'models', params],
    queryFn: () => intelligenceOpsService.listModels(params),
    staleTime: 60000, // 1 minute
  });
}

export function useUpdateModel() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      modelId,
      data,
    }: {
      modelId: string;
      data: UpdateModelRequest;
    }) => intelligenceOpsService.updateModel(modelId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin', 'llm', 'models'] });
    },
  });
}

export function useBudgets() {
  return useQuery({
    queryKey: ['admin', 'llm', 'budgets'],
    queryFn: () => intelligenceOpsService.listBudgets(),
    staleTime: 30000, // 30 seconds
  });
}

export function useCreateBudget() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: CreateBudgetRequest) =>
      intelligenceOpsService.createBudget(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin', 'llm', 'budgets'] });
    },
  });
}

export function useTelemetryOverview(period?: string) {
  return useQuery({
    queryKey: ['admin', 'llm', 'telemetry', 'overview', period],
    queryFn: () => intelligenceOpsService.getTelemetryOverview(period),
    staleTime: 30000, // 30 seconds
  });
}

export function useIntelligenceOpsRealTimeUpdates() {
  return useIntelligenceOpsWebSocket({
    onMetricsUpdate: (data) => {
      // Update React Query cache
    },
    onBudgetAlert: (alert) => {
      // Show alert
    },
  });
}
```

#### `IntelligenceOps.tsx`
```typescript
'use client';

import React, { useState } from 'react';
import { ModelsTab } from './tabs/ModelsTab';
import { BudgetsTab } from './tabs/BudgetsTab';
import { CircuitBreakersTab } from './tabs/CircuitBreakersTab';
import { RankingsTab } from './tabs/RankingsTab';
import { TelemetryTab } from './tabs/TelemetryTab';
import { AgentsTab } from './tabs/AgentsTab';
import { DistillationTab } from './tabs/DistillationTab';
import { ValidationTab } from './tabs/ValidationTab';

type Tab = 'models' | 'budgets' | 'circuit-breakers' | 'rankings' | 'telemetry' | 'agents' | 'distillation' | 'validation';

export const IntelligenceOps: React.FC = () => {
  const [activeTab, setActiveTab] = useState<Tab>('models');

  const tabs = [
    { id: 'models' as Tab, label: 'Models' },
    { id: 'budgets' as Tab, label: 'Budgets' },
    { id: 'circuit-breakers' as Tab, label: 'Circuit Breakers' },
    { id: 'rankings' as Tab, label: 'Rankings' },
    { id: 'telemetry' as Tab, label: 'Telemetry' },
    { id: 'agents' as Tab, label: 'Agents' },
    { id: 'distillation' as Tab, label: 'Distillation' },
    { id: 'validation' as Tab, label: 'Validation' },
  ];

  const renderTabContent = () => {
    switch (activeTab) {
      case 'models':
        return <ModelsTab />;
      case 'budgets':
        return <BudgetTab />;
      case 'circuit-breakers':
        return <CircuitBreakersTab />;
      case 'rankings':
        return <RankingsTab />;
      case 'telemetry':
        return <TelemetryTab />;
      case 'agents':
        return <AgentsTab />;
      case 'distillation':
        return <DistillationTab />;
      case 'validation':
        return <ValidationTab />;
      default:
        return <ModelsTab />;
    }
  };

  return (
    <div className="intelligence-ops-container p-6">
      <h1 className="text-3xl font-bold mb-6">Intelligence Ops</h1>

      {/* Tab Navigation */}
      <div className="border-b border-gray-200 mb-6">
        <nav className="flex space-x-8">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`
                py-4 px-1 border-b-2 font-medium text-sm
                ${
                  activeTab === tab.id
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }
              `}
            >
              {tab.label}
            </button>
          ))}
        </nav>
      </div>

      {/* Tab Content */}
      {renderTabContent()}
    </div>
  );
};
```

## 📝 Complete File List

### Intelligence Ops Module
- [ ] `IntelligenceOps.tsx` - Main component
- [ ] `IntelligenceOps.types.ts` - TypeScript interfaces
- [ ] `IntelligenceOps.hooks.ts` - React hooks
- [ ] `IntelligenceOps.service.ts` - API service
- [ ] `components/ModelCard.tsx` - Model card component
- [ ] `components/BudgetCard.tsx` - Budget card component
- [ ] `components/ToggleSwitch.tsx` - Toggle switch component
- [ ] `components/CostImpact.tsx` - Cost impact display
- [ ] `components/CircuitBreakerStatus.tsx` - Circuit breaker status
- [ ] `components/RankingTable.tsx` - Ranking table
- [ ] `components/TelemetryChart.tsx` - Telemetry chart
- [ ] `components/AgentList.tsx` - Agent list
- [ ] `components/DistillationConfig.tsx` - Distillation config
- [ ] `components/ValidationQueue.tsx` - Validation queue
- [ ] `tabs/ModelsTab.tsx` - Models tab
- [ ] `tabs/BudgetsTab.tsx` - Budgets tab
- [ ] `tabs/CircuitBreakersTab.tsx` - Circuit breakers tab
- [ ] `tabs/RankingsTab.tsx` - Rankings tab
- [ ] `tabs/TelemetryTab.tsx` - Telemetry tab
- [ ] `tabs/AgentsTab.tsx` - Agents tab
- [ ] `tabs/DistillationTab.tsx` - Distillation tab
- [ ] `tabs/ValidationTab.tsx` - Validation tab
- [ ] `hooks/useModels.ts` - Models hook
- [ ] `hooks/useBudgets.ts` - Budgets hook
- [ ] `hooks/useCircuitBreakers.ts` - Circuit breakers hook
- [ ] `hooks/useRankings.ts` - Rankings hook
- [ ] `hooks/useTelemetry.ts` - Telemetry hook
- [ ] `hooks/useAgents.ts` - Agents hook
- [ ] `hooks/useDistillation.ts` - Distillation hook
- [ ] `hooks/useValidation.ts` - Validation hook
- [ ] `hooks/useIntelligenceOpsWebSocket.ts` - WebSocket hook
- [ ] `services/llm.service.ts` - LLM service
- [ ] `services/budget.service.ts` - Budget service
- [ ] `services/circuitBreaker.service.ts` - Circuit breaker service
- [ ] `services/ranking.service.ts` - Ranking service
- [ ] `services/telemetry.service.ts` - Telemetry service
- [ ] `services/agent.service.ts` - Agent service
- [ ] `services/distillation.service.ts` - Distillation service
- [ ] `services/validation.service.ts` - Validation service
- [ ] `__tests__/IntelligenceOps.test.tsx` - Component tests
- [ ] `__tests__/ModelCard.test.tsx` - Component tests
- [ ] `__tests__/services.test.ts` - Service tests

---

## 🧪 Testing Requirements

### Unit Tests

**Intelligence Ops Component**:
- [ ] Renders tab navigation correctly
- [ ] Switches tabs correctly
- [ ] Displays tab content
- [ ] Handles loading states
- [ ] Displays error states

**Model Card Component**:
- [ ] Renders model information correctly
- [ ] Displays toggle switch
- [ ] Shows cost information
- [ ] Handles circuit breaker status
- [ ] Triggers actions correctly

**Budget Card Component**:
- [ ] Renders budget information correctly
- [ ] Displays progress bar
- [ ] Shows threshold warnings
- [ ] Handles hard/soft limits
- [ ] Triggers edit/delete actions

**Services**:
- [ ] Calls correct API endpoints
- [ ] Handles query parameters
- [ ] Parses response correctly
- [ ] Handles errors (401, 403, 404, 500, 503)

### Integration Tests

**Intelligence Ops Flow**:
- [ ] Load models list
- [ ] Toggle model enabled/disabled
- [ ] Create budget
- [ ] Update budget
- [ ] Reset circuit breaker
- [ ] View rankings
- [ ] View telemetry
- [ ] Approve/reject validation response

**WebSocket Integration**:
- [ ] Connect to WebSocket
- [ ] Receive real-time updates
- [ ] Handle connection errors
- [ ] Reconnect on disconnect

### E2E Tests

**Intelligence Ops Journey**:
- [ ] Login as admin → View Intelligence Ops
- [ ] Configure model
- [ ] Create budget
- [ ] Monitor telemetry
- [ ] Handle errors gracefully

### Performance Tests

- [ ] Models list loads in < 2 seconds
- [ ] Budget operations complete in < 1 second
- [ ] Telemetry charts render in < 1 second
- [ ] WebSocket connection in < 1 second
- [ ] Real-time updates < 500ms latency

### Accessibility Tests

- [ ] Screen reader announces status changes
- [ ] Keyboard navigation works
- [ ] Color contrast meets WCAG 2.1 AA
- [ ] All interactive elements are focusable
- [ ] Toggle switches are accessible

---

## 🔍 Risk Assessment (CTO Methodology)

### Cognitive Limitation Analysis

**Areas Where Analysis May Overlook Factors**:

1. **Configuration Complexity**
   - **Risk**: Too many options cause confusion
   - **Mitigation**: Progressive disclosure, tabbed interface, clear defaults
   - **Validation**: User testing with admins

2. **Cost Impact Understanding**
   - **Risk**: Admins don't understand cost implications
   - **Mitigation**: Always show cost impact, use clear visualizations
   - **Validation**: Test cost impact displays

3. **Real-time Update Complexity**
   - **Risk**: WebSocket connection management is complex
   - **Mitigation**: Robust reconnection logic, fallback to polling
   - **Validation**: Test connection failures and recovery

### Technical Debt Assessment

**Rapid Implementation Compromises to Avoid**:

1. **No Cost Calculation**
   - **Debt**: Cannot show cost impact
   - **Cost**: Poor decision-making
   - **Prevention**: Implement cost calculation service

2. **No Ranking Override Management**
   - **Debt**: Cannot adjust rankings in emergencies
   - **Cost**: Limited flexibility
   - **Prevention**: Implement override system with expiration

3. **No Budget Enforcement**
   - **Debt**: Budgets are advisory only
   - **Cost**: Cost overruns
   - **Prevention**: Implement hard limit enforcement

### Validation & Testing Strategy

**Module-Specific Success Criteria**:
- ✅ Models list loads in < 2 seconds (p95)
- ✅ Budget operations complete in < 1 second
- ✅ Telemetry loads in < 2 seconds
- ✅ Real-time updates latency < 500ms (WebSocket)
- ✅ Cost calculations are accurate (> 99%)
- ✅ Error recovery rate > 95%
- ✅ Accessibility score: 100/100 (WCAG 2.1 AA)

**Module-Specific Test Requirements**:
- **Unit Tests**: Component rendering, state management, service functions, cost calculations
- **Integration Tests**: API integration, WebSocket connection, budget enforcement
- **E2E Tests**: Complete configuration flow, budget management, telemetry monitoring
- **Performance Tests**: Load with 50+ models, 10+ budgets, large telemetry datasets
- **Accessibility Tests**: Screen reader navigation, keyboard shortcuts, color contrast

**Failure Detection & Monitoring**:
- Monitor API response times (alert if p95 > 2s)
- Track error rates (alert if > 1%)
- Alert on budget threshold breaches
- Monitor circuit breaker state changes
- Track cost calculation accuracy
- Log all configuration changes for audit trail

---

## 📚 References

- **Backend Controllers**: `src/app/presentation/http/controllers/admin/llm/`
- **Backend Controllers**: `src/app/presentation/http/controllers/admin/agents/`
- **Backend Controllers**: `src/app/presentation/http/controllers/admin/distillation/`
- **Response Schemas**: `src/app/presentation/http/schemas/`
- **API Documentation**: `03-Intelligence-Ops/API.md`
- **UI/UX Design**: `03-Intelligence-Ops/UI_UX.md`
- **Related Modules**: 
  - Admin Overview (cost summaries)
  - System Health (circuit breaker metrics)

---

**Note**: These are implementation file structures. Actual files should be created in the frontend codebase repository.
