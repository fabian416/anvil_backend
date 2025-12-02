# FRONTEND_ADMIN_LLM_BUDGETS

## Admin LLM Budget Management Module

**User Type:** Admin  
**Module:** Budget Management  
**Route:** `/admin/llm/budgets`  
**Access Level:** Full CRUD (Admin) | Read-Only (Operator/Viewer)

---

## 📋 Module Overview

### Title
**Budget Management** - Cost Control & Spend Analytics

### Description
Comprehensive budget management interface for controlling LLM spending across providers, models, and time periods. Enables administrators to set limits, monitor real-time spend, configure alerts, and analyze cost trends to optimize platform economics.

### Key Capabilities
- Create and manage daily, weekly, and monthly budgets
- Real-time spend tracking with visual progress indicators
- Multi-level budgets (global, per-provider, per-model)
- Configurable alert thresholds and actions
- Cost forecasting based on usage patterns
- Detailed spend breakdown analytics
- Budget utilization reports and exports

---

## 👤 User Stories

### US-ADMIN-BUDGET-001: View Budget Overview
**As a** platform administrator  
**I want to** see all budgets with current utilization at a glance  
**So that** I can monitor spending across the platform

**Acceptance Criteria:**
- Dashboard showing all active budgets
- Progress bars with color-coded utilization (green <80%, yellow <95%, red ≥95%)
- Current spend vs budget limit displayed
- Time remaining in period shown
- Projected spend at period end
- Quick filters for budget type and status

### US-ADMIN-BUDGET-002: Create New Budget
**As a** platform administrator  
**I want to** create budgets with custom parameters  
**So that** I can control spending at various levels

**Acceptance Criteria:**
- Budget type selection (daily, weekly, monthly)
- Scope selection (global, provider, model)
- Amount input with currency formatting
- Warning threshold configuration
- Critical threshold configuration
- Action selection (alert, throttle, hard stop)
- Preview projected impact before saving

### US-ADMIN-BUDGET-003: Monitor Real-Time Spend
**As a** platform administrator  
**I want to** see live spend updates  
**So that** I can react quickly to spending anomalies

**Acceptance Criteria:**
- Real-time spend counter updates
- Visual indicator when approaching threshold
- Sound/notification option for alerts
- Spend rate calculation ($/hour, $/minute)
- Trend comparison to historical average
- WebSocket updates for live data

### US-ADMIN-BUDGET-004: Configure Budget Alerts
**As a** platform administrator  
**I want to** set up automated alerts for budget thresholds  
**So that** I'm notified before limits are reached

**Acceptance Criteria:**
- Multiple threshold levels configurable
- Notification channels (email, Slack, in-app)
- Alert frequency settings (once, hourly, always)
- Escalation rules for critical thresholds
- Alert history with acknowledgment status
- Test alert functionality

### US-ADMIN-BUDGET-005: Analyze Cost Trends
**As a** platform administrator  
**I want to** view historical spend patterns  
**So that** I can optimize budgets and predict future costs

**Acceptance Criteria:**
- Time-series chart of spend over time
- Breakdown by provider, model, agent
- Cost per request trending
- Peak usage identification
- Month-over-month comparison
- Export data for external analysis

### US-ADMIN-BUDGET-006: Adjust Budget Limits
**As a** platform administrator  
**I want to** modify budget limits on active budgets  
**So that** I can respond to changing business needs

**Acceptance Criteria:**
- Edit existing budget parameters
- Change takes effect immediately
- Audit log of all changes
- Warning if reducing below current spend
- Bulk edit option for multiple budgets
- Rollback capability for recent changes

---

## 🖼️ Views & Wireframes

### View 1: Budget Dashboard (Default View)

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│  💰 Budget Management                                          [+ Create Budget]    │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                      │
│  ┌─ Summary ───────────────────────────────────────────────────────────────────────┐│
│  │  💵 $127.45 Today    📊 $2,847 This Month    📈 $3,421 Projected    ⚠️ 1 Alert ││
│  │     25% of $500         28% of $10,000          34% projected           Warning ││
│  └─────────────────────────────────────────────────────────────────────────────────┘│
│                                                                                      │
│  ┌─ Filters ───────────────────────────────────────────────────────────────────────┐│
│  │ Type: [All ▼]    Scope: [All ▼]    Status: [Active ▼]    [🔍 Search...]        ││
│  └─────────────────────────────────────────────────────────────────────────────────┘│
│                                                                                      │
│  ACTIVE BUDGETS                                                                     │
│                                                                                      │
│  ┌─────────────────────────────────────────────────────────────────────────────────┐│
│  │ 📅 DAILY BUDGETS                                                                ││
│  │                                                                                  ││
│  │ ┌───────────────────────────────────────────────────────────────────────────┐   ││
│  │ │ Global Daily Budget                                    ⚙️ Edit  📊 Details│   ││
│  │ │                                                                           │   ││
│  │ │ $127.45 / $500.00                                                         │   ││
│  │ │ [█████████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░] 25.5%                          │   ││
│  │ │                                                                           │   ││
│  │ │ 🕐 18h 42m remaining    📈 Rate: $7.08/hr    🎯 Projected: $297.50       │   ││
│  │ │ Alerts: ⚠️ 80% (warn) | 🛑 95% (throttle)                                │   ││
│  │ └───────────────────────────────────────────────────────────────────────────┘   ││
│  │                                                                                  ││
│  │ ┌───────────────────────────────────────────────────────────────────────────┐   ││
│  │ │ Vertex AI Daily                                        ⚙️ Edit  📊 Details│   ││
│  │ │                                                                           │   ││
│  │ │ $66.50 / $200.00                                                          │   ││
│  │ │ [██████████████░░░░░░░░░░░░░░░░░░░░░░░░░] 33.3%                          │   ││
│  │ │                                                                           │   ││
│  │ │ 🕐 18h 42m remaining    📈 Rate: $3.69/hr    🎯 Projected: $155.20       │   ││
│  │ └───────────────────────────────────────────────────────────────────────────┘   ││
│  └─────────────────────────────────────────────────────────────────────────────────┘│
│                                                                                      │
│  ┌─────────────────────────────────────────────────────────────────────────────────┐│
│  │ 📆 MONTHLY BUDGETS                                                              ││
│  │                                                                                  ││
│  │ ┌───────────────────────────────────────────────────────────────────────────┐   ││
│  │ │ Global Monthly Budget                                  ⚙️ Edit  📊 Details│   ││
│  │ │                                                                           │   ││
│  │ │ $2,847.50 / $10,000.00                                                    │   ││
│  │ │ [████████████░░░░░░░░░░░░░░░░░░░░░░░░░░░░] 28.5%                         │   ││
│  │ │                                                                           │   ││
│  │ │ 📅 23 days remaining    📈 Avg: $127.45/day    🎯 Projected: $3,421.50   │   ││
│  │ │ Alerts: ⚠️ 75% (warn) | 🛑 90% (alert)                                   │   ││
│  │ └───────────────────────────────────────────────────────────────────────────┘   ││
│  └─────────────────────────────────────────────────────────────────────────────────┘│
│                                                                                      │
│  ┌─────────────────────────────────────────────────────────────────────────────────┐│
│  │ SPEND TREND (Last 7 Days)                                                        ││
│  │                                                                                  ││
│  │  $200 ┤            ╭──╮                                                         ││
│  │       │           ╭╯  ╰╮    ╭──╮                                                ││
│  │  $150 ┤    ╭──╮  ╭╯    ╰────╯  ╰──                                              ││
│  │       │   ╭╯  ╰──╯                                                               ││
│  │  $100 ┤───╯                                              Daily Limit: $500 ----  ││
│  │       │                                                                          ││
│  │   $50 ┤                                                                          ││
│  │       └──────────────────────────────────────────────────────────────────▶      ││
│  │        Mon    Tue    Wed    Thu    Fri    Sat    Sun                            ││
│  │                                                                                  ││
│  │  Avg Daily: $142.35  │  Total: $996.45  │  vs Last Week: +8.2%                  ││
│  └─────────────────────────────────────────────────────────────────────────────────┘│
│                                                                                      │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

### View 2: Create/Edit Budget Modal

```
┌─────────────────────────────────────────────────────────────────┐
│  Create New Budget                                       [✕]   │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  BUDGET CONFIGURATION                                           │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │                                                           │  │
│  │  Budget Name                                              │  │
│  │  ┌─────────────────────────────────────────────────────┐  │  │
│  │  │ Premium Models Daily Limit                          │  │  │
│  │  └─────────────────────────────────────────────────────┘  │  │
│  │                                                           │  │
│  │  Budget Type                                              │  │
│  │  ┌─────────────────────────────────────────────────────┐  │  │
│  │  │ [●] Daily  [ ] Weekly  [ ] Monthly                  │  │  │
│  │  └─────────────────────────────────────────────────────┘  │  │
│  │                                                           │  │
│  │  Scope                                                    │  │
│  │  ┌─────────────────────────────────────────────────────┐  │  │
│  │  │ [ ] Global (all providers)                          │  │  │
│  │  │ [ ] Provider: [Select Provider ▼]                   │  │  │
│  │  │ [●] Model Tier: [Premium ▼]                         │  │  │
│  │  └─────────────────────────────────────────────────────┘  │  │
│  │                                                           │  │
│  │  Budget Amount (USD)                                      │  │
│  │  ┌─────────────────────────────────────────────────────┐  │  │
│  │  │ [$] [250.00                                       ] │  │  │
│  │  └─────────────────────────────────────────────────────┘  │  │
│  │                                                           │  │
│  └───────────────────────────────────────────────────────────┘  │
│                                                                 │
│  ALERT THRESHOLDS                                               │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │                                                           │  │
│  │  Warning Threshold                                        │  │
│  │  ┌─────────────────────────────────────────────────────┐  │  │
│  │  │     |───────────────●──────────────|                │  │  │
│  │  │     0%             80%           100%               │  │  │
│  │  │                                                     │  │  │
│  │  │  At $200.00 → Send notification                     │  │  │
│  │  └─────────────────────────────────────────────────────┘  │  │
│  │                                                           │  │
│  │  Critical Threshold                                       │  │
│  │  ┌─────────────────────────────────────────────────────┐  │  │
│  │  │     |─────────────────────────●──|                  │  │  │
│  │  │     0%                       95%  100%              │  │  │
│  │  │                                                     │  │  │
│  │  │  At $237.50 → Action:                               │  │  │
│  │  │  [ ] Alert only  [●] Throttle requests  [ ] Stop    │  │  │
│  │  └─────────────────────────────────────────────────────┘  │  │
│  │                                                           │  │
│  └───────────────────────────────────────────────────────────┘  │
│                                                                 │
│  NOTIFICATIONS                                                  │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │                                                           │  │
│  │  [✓] Email alerts to: admin@company.com                  │  │
│  │  [✓] Slack notification to: #llm-alerts                  │  │
│  │  [✓] In-app dashboard alert                              │  │
│  │                                                           │  │
│  └───────────────────────────────────────────────────────────┘  │
│                                                                 │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │ 💡 IMPACT PREVIEW                                         │  │
│  │                                                           │  │
│  │ Based on last 7 days:                                     │  │
│  │ • Average daily spend for premium models: $185.40        │  │
│  │ • You would hit warning (80%) ~4h before period end      │  │
│  │ • Likelihood of hitting limit: Medium (65%)              │  │
│  └───────────────────────────────────────────────────────────┘  │
│                                                                 │
│  ─────────────────────────────────────────────────────────────  │
│                                                                 │
│  [Cancel]                                   [Create Budget]     │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### View 3: Budget Detail View

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│  💰 Global Daily Budget                                [✏️ Edit] [⏸️ Pause] [🗑️]   │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                      │
│  [Overview]  [Spend History]  [Alerts]  [Audit Log]                                 │
│  ─────────────────────────────────────────────────────────────────────────────────  │
│                                                                                      │
│  CURRENT PERIOD                                                                     │
│  ┌─────────────────────────────────────────────────────────────────────────────────┐│
│  │                                                                                  ││
│  │                        $127.45 / $500.00                                        ││
│  │                                                                                  ││
│  │  [██████████████████████████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░] 25.5%   ││
│  │                                                                                  ││
│  │  ⚠️ Warning at $400 (80%)            🛑 Throttle at $475 (95%)                  ││
│  │  |────────────────────────────────────●─────────────●────|                      ││
│  │  $0                                  $400          $475  $500                   ││
│  │                                                                                  ││
│  │  ┌────────────────┬────────────────┬────────────────┬────────────────┐          ││
│  │  │ Time Remaining │ Current Rate   │ Projected EOD  │ vs Yesterday   │          ││
│  │  │ 18h 42m        │ $7.08/hr       │ $297.50        │ +$12.30 (+11%) │          ││
│  │  └────────────────┴────────────────┴────────────────┴────────────────┘          ││
│  │                                                                                  ││
│  └─────────────────────────────────────────────────────────────────────────────────┘│
│                                                                                      │
│  SPEND BREAKDOWN                                                                    │
│  ┌─────────────────────────────────────────────────────────────────────────────────┐│
│  │                                                                                  ││
│  │  By Provider                              By Model Tier                         ││
│  │  ┌───────────────────────────────┐       ┌───────────────────────────────┐      ││
│  │  │ Vertex AI    ████████████ 52% │       │ Premium  ████████████████ 68% │      ││
│  │  │              $66.50           │       │          $86.50               │      ││
│  │  │ DeepInfra    ████████    35%  │       │ Standard ████████       28%   │      ││
│  │  │              $44.40           │       │          $35.60               │      ││
│  │  │ Bedrock      ███         13%  │       │ Economy  ██             4%    │      ││
│  │  │              $16.55           │       │          $5.35                │      ││
│  │  └───────────────────────────────┘       └───────────────────────────────┘      ││
│  │                                                                                  ││
│  │  By Agent                                 By Model (Top 5)                      ││
│  │  ┌───────────────────────────────┐       ┌───────────────────────────────┐      ││
│  │  │ SwapAgent    ██████████   42% │       │ gemini-1.5-pro  ████████ 35%  │      ││
│  │  │ Researcher   ███████      28% │       │ llama-3.1-405b  ██████   22%  │      ││
│  │  │ Trading      █████        18% │       │ claude-3-sonnet █████    18%  │      ││
│  │  │ Portfolio    ███          12% │       │ gemini-flash    ████     15%  │      ││
│  │  │                               │       │ mixtral-8x22b   ███      10%  │      ││
│  │  └───────────────────────────────┘       └───────────────────────────────┘      ││
│  │                                                                                  ││
│  └─────────────────────────────────────────────────────────────────────────────────┘│
│                                                                                      │
│  TODAY'S HOURLY SPEND                                                               │
│  ┌─────────────────────────────────────────────────────────────────────────────────┐│
│  │  $15 ┤     ╭──╮       ╭──╮                                                      ││
│  │      │    ╭╯  ╰╮    ╭╯  ╰╮                                                      ││
│  │  $10 ┤  ╭╭╯    ╰────╯    ╰──╮                                                   ││
│  │      │ ╭╯                   ╰───                                                 ││
│  │   $5 ┤╭╯                                                                        ││
│  │      ├╯                                                         Avg: $8.50/hr   ││
│  │   $0 └──────────────────────────────────────────────────────────────────▶       ││
│  │       00  02  04  06  08  10  12  14  16  Now                                   ││
│  └─────────────────────────────────────────────────────────────────────────────────┘│
│                                                                                      │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 🔌 API Endpoints

### List Budgets

```typescript
// GET /admin/llm/budgets
// Get all budgets with current status

interface GetBudgetsResponse {
  success: true;
  data: {
    budgets: Budget[];
    summary: {
      today_spend: number;
      month_spend: number;
      projected_month_spend: number;
      active_alerts_count: number;
    };
  };
}

interface Budget {
  id: string;
  name: string;
  budget_type: 'daily' | 'weekly' | 'monthly';
  scope_type: 'global' | 'provider' | 'model' | 'tier';
  scope_id?: string;
  scope_name?: string;
  budget_amount_usd: number;
  current_spend_usd: number;
  utilization_pct: number;
  warning_threshold_pct: number;
  critical_threshold_pct: number;
  action_on_critical: 'alert' | 'throttle' | 'stop';
  is_hard_limit: boolean;
  is_active: boolean;
  period_start: string;
  period_end: string;
  time_remaining_seconds: number;
  projected_spend_usd: number;
  spend_rate_per_hour: number;
  notifications: {
    email: boolean;
    slack: boolean;
    in_app: boolean;
  };
  created_at: string;
  updated_at: string;
}
```

### Create Budget

```typescript
// POST /admin/llm/budgets
// Create new budget

interface CreateBudgetRequest {
  name: string;
  budget_type: 'daily' | 'weekly' | 'monthly';
  scope_type: 'global' | 'provider' | 'model' | 'tier';
  scope_id?: string;
  budget_amount_usd: number;
  warning_threshold_pct: number;
  critical_threshold_pct: number;
  action_on_critical: 'alert' | 'throttle' | 'stop';
  is_hard_limit?: boolean;
  notifications: {
    email?: boolean;
    slack?: boolean;
    in_app?: boolean;
  };
}

// Validation
const createBudgetValidation = {
  name: { required: true, minLength: 2, maxLength: 100 },
  budget_amount_usd: { required: true, min: 1, max: 1000000 },
  warning_threshold_pct: { required: true, min: 1, max: 100 },
  critical_threshold_pct: { required: true, min: 1, max: 100 }
};

interface CreateBudgetResponse {
  success: true;
  data: {
    budget: Budget;
  };
}
```

### Get Budget Details

```typescript
// GET /admin/llm/budgets/{id}
// Get detailed budget information

interface GetBudgetDetailsResponse {
  success: true;
  data: {
    budget: Budget;
    spend_breakdown: {
      by_provider: Record<string, number>;
      by_model: Record<string, number>;
      by_tier: Record<string, number>;
      by_agent: Record<string, number>;
    };
    hourly_spend: TimeSeriesPoint[];
    alerts_history: BudgetAlert[];
  };
}

interface BudgetAlert {
  id: string;
  threshold_type: 'warning' | 'critical';
  threshold_pct: number;
  amount_at_trigger: number;
  triggered_at: string;
  acknowledged: boolean;
  acknowledged_at?: string;
  acknowledged_by?: string;
}
```

### Get Spend History

```typescript
// GET /admin/llm/budgets/{id}/history?period=7d
// Get historical spend data

interface GetSpendHistoryResponse {
  success: true;
  data: {
    budget_id: string;
    period: string;
    daily_spend: Array<{
      date: string;
      spend_usd: number;
      limit_usd: number;
      utilization_pct: number;
    }>;
    total_spend: number;
    average_daily_spend: number;
    peak_day: {
      date: string;
      spend: number;
    };
    trend: {
      direction: 'up' | 'down' | 'stable';
      change_pct: number;
    };
  };
}
```

---

## 📊 Data Structures

### Module State

```typescript
interface BudgetsModuleState {
  // Data
  budgets: Budget[];
  summary: BudgetsSummary | null;
  selectedBudget: Budget | null;
  budgetDetails: GetBudgetDetailsResponse['data'] | null;
  
  // UI State
  loading: {
    list: boolean;
    details: boolean;
    create: boolean;
    update: boolean;
  };
  
  errors: {
    list: Error | null;
    create: Error | null;
    update: Error | null;
  };
  
  // Filters
  filters: {
    type: 'all' | 'daily' | 'weekly' | 'monthly';
    scope: 'all' | 'global' | 'provider' | 'model' | 'tier';
    status: 'all' | 'active' | 'paused';
  };
  
  // Create/Edit Modal
  modalOpen: boolean;
  modalMode: 'create' | 'edit';
  formData: Partial<CreateBudgetRequest>;
  
  // Spend History
  historyPeriod: '7d' | '30d' | '90d';
  historyData: GetSpendHistoryResponse['data'] | null;
  
  // Real-time
  wsConnected: boolean;
  lastUpdate: string | null;
}
```

---

## 🎨 Component Specifications

### BudgetCard

```typescript
interface BudgetCardProps {
  budget: Budget;
  onEdit: (id: string) => void;
  onViewDetails: (id: string) => void;
  onPause: (id: string) => void;
  onDelete: (id: string) => void;
  animated?: boolean;
}
```

### BudgetProgressBar

```typescript
interface BudgetProgressBarProps {
  current: number;
  limit: number;
  warningThreshold: number;
  criticalThreshold: number;
  showMarkers?: boolean;
  animated?: boolean;
  size?: 'sm' | 'md' | 'lg';
}
```

### SpendBreakdownChart

```typescript
interface SpendBreakdownChartProps {
  data: Record<string, number>;
  type: 'pie' | 'bar';
  title: string;
  showPercentages?: boolean;
  showValues?: boolean;
  onSegmentClick?: (key: string) => void;
}
```

### BudgetForm

```typescript
interface BudgetFormProps {
  initialData?: Partial<CreateBudgetRequest>;
  mode: 'create' | 'edit';
  onSubmit: (data: CreateBudgetRequest) => void;
  onCancel: () => void;
  loading?: boolean;
}
```

### ImpactPreview

```typescript
interface ImpactPreviewProps {
  budgetAmount: number;
  budgetType: 'daily' | 'weekly' | 'monthly';
  scope: string;
  historicalAverage: number;
}
```

---

## 🎬 Motion Design

```typescript
const budgetsAnimations = {
  // Progress bar fill
  progressFill: {
    initial: { width: 0 },
    animate: { width: '100%' },
    transition: { duration: 1, ease: 'easeOut' }
  },
  
  // Threshold marker pulse
  thresholdPulse: {
    scale: [1, 1.3, 1],
    opacity: [1, 0.7, 1],
    transition: { duration: 1.5, repeat: Infinity }
  },
  
  // Spend counter increment
  spendIncrement: {
    scale: [1, 1.1, 1],
    color: ['#fff', '#F59E0B', '#fff'],
    transition: { duration: 0.3 }
  },
  
  // Alert badge bounce
  alertBounce: {
    y: [0, -5, 0],
    transition: { duration: 0.5, repeat: Infinity }
  },
  
  // Chart segment hover
  chartSegmentHover: {
    scale: 1.05,
    opacity: 1,
    transition: { duration: 0.2 }
  },
  
  // Card expand
  cardExpand: {
    height: 'auto',
    opacity: 1,
    transition: { duration: 0.3 }
  },
  
  // Warning state
  warningState: {
    borderColor: ['#334155', '#F59E0B', '#334155'],
    transition: { duration: 1, repeat: Infinity }
  },
  
  // Critical state
  criticalState: {
    borderColor: ['#334155', '#EF4444', '#334155'],
    boxShadow: ['none', '0 0 20px rgba(239, 68, 68, 0.3)', 'none'],
    transition: { duration: 0.5, repeat: Infinity }
  }
};
```

---

## ⌨️ Keyboard Shortcuts

```typescript
const budgetsShortcuts = {
  'mod+n': 'Create new budget',
  'mod+e': 'Edit selected budget',
  'mod+r': 'Refresh data',
  'd': 'View details',
  'h': 'View history',
  'escape': 'Close modal',
  '1/2/3': 'Filter by type (daily/weekly/monthly)',
};
```

---

## ⚠️ Error Handling

```typescript
const budgetErrorCodes = {
  // Validation
  BUD_VAL_001: 'Budget name is required',
  BUD_VAL_002: 'Budget amount must be positive',
  BUD_VAL_003: 'Warning threshold must be less than critical',
  BUD_VAL_004: 'Invalid scope configuration',
  
  // Business Logic
  BUD_BUS_001: 'Cannot reduce budget below current spend',
  BUD_BUS_002: 'Duplicate budget scope exists',
  BUD_BUS_003: 'Cannot delete budget with active alerts',
  
  // System
  BUD_SYS_001: 'Failed to load budgets',
  BUD_SYS_002: 'Failed to create budget',
  BUD_SYS_003: 'Failed to update budget',
  BUD_SYS_004: 'Real-time updates unavailable',
};
```

---

## 📋 Field Requirements Summary

| Endpoint | Field | Type | Required | Validation |
|----------|-------|------|----------|------------|
| POST /budgets | name | string | Yes | 2-100 chars |
| POST /budgets | budget_type | enum | Yes | daily, weekly, monthly |
| POST /budgets | budget_amount_usd | number | Yes | 1-1000000 |
| POST /budgets | warning_threshold_pct | number | Yes | 1-100, < critical |
| POST /budgets | critical_threshold_pct | number | Yes | 1-100, > warning |

---

## 🔒 Security Considerations

1. **Budget Enforcement:** Limits enforced at API layer, not just UI
2. **Audit Trail:** All budget changes logged with full history
3. **Permission Levels:** Create/Edit/Delete requires Admin, View available to Operator
4. **Rate Limiting:** Budget creation limited to prevent abuse
5. **Notifications:** Verify notification endpoints before enabling

---

*Document Version: 1.0*  
*Last Updated: December 1, 2025*  
*Module: Budget Management*  
*User Type: Admin*
