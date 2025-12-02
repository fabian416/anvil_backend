# FRONTEND_ADMIN_LLM_DASHBOARD

## Admin LLM Orchestration Dashboard Module

**User Type:** Admin / Operator / Viewer  
**Module:** LLM Dashboard  
**Route:** `/admin/llm`  
**Access Level:** View (All) | Configure (Admin)

---

## 📋 Module Overview

### Title
**LLM Orchestration Dashboard** - Real-Time System Intelligence

### Description
The central command center for monitoring and managing the Multi-LLM Orchestration system. Provides real-time visibility into provider health, request performance, cost tracking, and system alerts. Enables quick decision-making through consolidated metrics and one-click actions.

### Key Capabilities
- Real-time provider health monitoring with latency metrics
- Live request throughput and success rate visualization
- Cost tracking against daily/monthly budgets with projections
- Circuit breaker status overview with quick reset actions
- Model ranking performance snapshot by agent type
- Critical alerts timeline with acknowledgment
- Quick action shortcuts for common operations

---

## 👤 User Stories

### US-ADMIN-LLM-DASH-001: View System Health at a Glance
**As a** platform administrator  
**I want to** see the overall health of all LLM providers immediately upon loading  
**So that** I can quickly identify any issues requiring attention

**Acceptance Criteria:**
- Dashboard loads within 2 seconds with all health indicators visible
- Each provider shows status (Healthy/Degraded/Down) with colored indicator
- Provider latency shown in milliseconds with trend arrow
- Clicking a provider card navigates to detailed provider view
- Health data refreshes automatically every 30 seconds
- Manual refresh button available for immediate update

### US-ADMIN-LLM-DASH-002: Monitor Real-Time Request Metrics
**As a** platform operator  
**I want to** view current request throughput and success rates  
**So that** I can ensure the system is performing within acceptable parameters

**Acceptance Criteria:**
- Total requests today displayed with comparison to yesterday
- Success rate shown as percentage with color coding (green >95%, yellow >90%, red <90%)
- Average latency with P50/P95/P99 breakdown on hover
- Active requests gauge showing current in-flight requests
- Retry rate percentage with trend indicator
- Time-series chart showing requests over last 24 hours by provider

### US-ADMIN-LLM-DASH-003: Track Cost Against Budget
**As a** finance-aware administrator  
**I want to** see current spending against configured budgets  
**So that** I can prevent unexpected cost overruns

**Acceptance Criteria:**
- Today's spend shown as absolute value and percentage of daily budget
- Visual progress bar with color zones (green <80%, yellow <95%, red ≥95%)
- Monthly spend with projected month-end total
- Cost breakdown by provider on hover
- Alert indicator when approaching budget threshold
- Click through to detailed budget management

### US-ADMIN-LLM-DASH-004: View Circuit Breaker Status
**As a** system operator  
**I want to** see which circuit breakers are open or tripped  
**So that** I can take immediate action to restore service

**Acceptance Criteria:**
- Count of open circuit breakers prominently displayed
- List of currently open breakers with entity name and time opened
- One-click reset button for each open breaker (Admin only)
- Half-open breakers shown separately with test status
- Historical trip count for last 24 hours
- Link to full circuit breaker management

### US-ADMIN-LLM-DASH-005: View Recent Alerts
**As a** platform administrator  
**I want to** see recent system alerts in chronological order  
**So that** I can track issues and ensure they're being addressed

**Acceptance Criteria:**
- Last 10 alerts displayed with timestamp, severity, and message
- Severity icons (Critical=red, Warning=yellow, Info=blue)
- Unacknowledged alerts highlighted with pulsing indicator
- Click to acknowledge alert (removes highlight)
- Click to navigate to related module/resource
- "View All" link to full alert history

### US-ADMIN-LLM-DASH-006: Access Quick Actions
**As a** platform administrator  
**I want to** perform common operations without navigating away  
**So that** I can respond quickly to situations

**Acceptance Criteria:**
- Quick action panel with 6-8 common operations
- Force health check on all providers
- Recalculate rankings (triggers background job)
- Export today's report (downloads PDF)
- Toggle maintenance mode
- Clear all caches (with confirmation)
- Actions disabled based on user permissions

### US-ADMIN-LLM-DASH-007: View Top Models by Agent
**As a** platform administrator  
**I want to** see which models are performing best for each agent type  
**So that** I can understand the system's optimization choices

**Acceptance Criteria:**
- Grid showing top 3 models for each active agent type
- Model name with provider icon
- Success rate and average latency for each
- Ranking score displayed with trend from last period
- Click model to navigate to model detail
- Agent type tabs for filtering

### US-ADMIN-LLM-DASH-008: Real-Time WebSocket Updates
**As a** platform operator  
**I want to** see metrics update in real-time without refreshing  
**So that** I can monitor the system during critical periods

**Acceptance Criteria:**
- WebSocket connection established on dashboard load
- Connection status indicator (connected/reconnecting/disconnected)
- Metrics animate smoothly when values change
- New alerts slide in from top with sound option
- Circuit breaker changes trigger visual notification
- Graceful fallback to polling if WebSocket fails

---

## 🖼️ Views & Wireframes

### View 1: Main Dashboard (Default View)

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│  🤖 LLM Orchestration                                    🔄 30s │ Admin ▼          │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                      │
│  SYSTEM HEALTH                                                         🟢 HEALTHY   │
│  ┌─────────────────────┐ ┌─────────────────────┐ ┌─────────────────────┐            │
│  │ 🟢 Vertex AI        │ │ 🟢 DeepInfra        │ │ 🟢 AWS Bedrock      │            │
│  │                     │ │                     │ │                     │            │
│  │ Latency: 45ms  ↓    │ │ Latency: 120ms ↑    │ │ Latency: 89ms  →    │            │
│  │ Models: 3 active    │ │ Models: 3 active    │ │ Models: 3 active    │            │
│  │ Priority: 1         │ │ Priority: 2         │ │ Priority: 3         │            │
│  └─────────────────────┘ └─────────────────────┘ └─────────────────────┘            │
│                                                                                      │
│  ┌───────────────────────────────────────────────┐ ┌────────────────────────────────┐│
│  │ TODAY'S METRICS                               │ │ COST TRACKING                  ││
│  │                                               │ │                                ││
│  │  📊 45,231        📈 98.7%        ⏱️ 1,245ms  │ │  Today: $127.45 / $500         ││
│  │  Requests         Success         Avg Latency │ │  [██████████░░░░░░░░] 25%      ││
│  │  +12% vs yesterday +0.3%          -89ms       │ │                                ││
│  │                                               │ │  This Month: $2,847 / $10,000  ││
│  │  🔄 3.2%          ⏳ 0.8%         🚀 23       │ │  [████████░░░░░░░░░░] 28%      ││
│  │  Retry Rate       Timeout Rate   Active Now   │ │  Projected: $3,421             ││
│  │                                               │ │                                ││
│  └───────────────────────────────────────────────┘ └────────────────────────────────┘│
│                                                                                      │
│  ┌─────────────────────────────────────────────────────────────────────────────────┐│
│  │ REQUESTS OVER TIME (24h)                                         By Provider ▼  ││
│  │                                                                                  ││
│  │  5k ┤                              ╭──╮                                         ││
│  │     │      ╭─╮       ╭──╮        ╭╯  ╰╮       ╭─╮                              ││
│  │  3k ┤     ╭╯ ╰──╮   ╭╯  ╰──╮   ╭╯    ╰─────╯ ╰╮                              ││
│  │     │    ╭╯     ╰─╯╯       ╰──╯                ╰─────                          ││
│  │  1k ┤──╯                                                                       ││
│  │     └───────────────────────────────────────────────────────────────────────▶  ││
│  │      00:00    04:00    08:00    12:00    16:00    20:00    Now                 ││
│  │                                                                                  ││
│  │  ■ Vertex AI  ■ DeepInfra  ■ Bedrock                                           ││
│  └─────────────────────────────────────────────────────────────────────────────────┘│
│                                                                                      │
│  ┌─────────────────────────────────┐ ┌─────────────────────────────────────────────┐│
│  │ CIRCUIT BREAKERS                │ │ RECENT ALERTS                               ││
│  │                                 │ │                                             ││
│  │ 🟢 All Closed (9/9)            │ │ ⚠️ 14:32 DeepInfra latency spike (120ms)   ││
│  │                                 │ │    acknowledged                             ││
│  │ No breakers currently open     │ │                                             ││
│  │                                 │ │ ⚠️ 12:15 Budget 80% threshold reached      ││
│  │ Last trip: 2h ago (Recovered)  │ │    acknowledged                             ││
│  │                                 │ │                                             ││
│  │ [View All Breakers →]          │ │ ✅ 10:00 All systems recovered              ││
│  │                                 │ │                                             ││
│  └─────────────────────────────────┘ │ 🔴 08:45 Provider down: DeepInfra          ││
│                                       │    auto-recovered at 08:52                 ││
│                                       │                                             ││
│                                       │ [View All Alerts →]                         ││
│                                       └─────────────────────────────────────────────┘│
│                                                                                      │
│  ┌─────────────────────────────────────────────────────────────────────────────────┐│
│  │ TOP PERFORMING MODELS BY AGENT                                                   ││
│  │                                                                                  ││
│  │ SwapAgent           TradingAgent         PortfolioAgent       Researcher        ││
│  │ ──────────────────  ──────────────────   ──────────────────   ─────────────────││
│  │ 🥇 gemini-1.5-pro   🥇 gemini-1.5-flash  🥇 mixtral-8x22b     🥇 gemini-1.5-pro ││
│  │    98.5% │ 890ms       97.2% │ 450ms        95.8% │ 1,200ms      96.1% │ 980ms  ││
│  │                                                                                  ││
│  │ 🥈 claude-3-sonnet  🥈 llama-3.1-405b    🥈 qwen2-72b         🥈 claude-3-sonnet││
│  │    97.8% │ 1,120ms     96.5% │ 620ms        94.2% │ 890ms        95.4% │ 1,050ms││
│  │                                                                                  ││
│  │ 🥉 llama-3.1-405b   🥉 gemini-1.5-pro    🥉 gemini-1.5-flash  🥉 mixtral-8x22b  ││
│  │    96.2% │ 1,450ms     95.8% │ 520ms        93.5% │ 680ms        94.8% │ 1,350ms││
│  │                                                                                  ││
│  └─────────────────────────────────────────────────────────────────────────────────┘│
│                                                                                      │
│  ┌─────────────────────────────────────────────────────────────────────────────────┐│
│  │ QUICK ACTIONS                                                                    ││
│  │                                                                                  ││
│  │  [🔄 Force Health Check]  [📊 Recalculate Rankings]  [📥 Export Report]         ││
│  │                                                                                  ││
│  │  [⚙️ Provider Config]     [💰 Budget Settings]       [📈 Full Analytics]        ││
│  │                                                                                  ││
│  └─────────────────────────────────────────────────────────────────────────────────┘│
│                                                                                      │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

### View 2: Provider Health Expanded (On Hover/Click)

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│  🟢 Vertex AI                                                         [View Details]│
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                      │
│  Status: HEALTHY                Last Check: 30s ago                                 │
│                                                                                      │
│  ┌────────────────────────┬────────────────────────┬────────────────────────┐       │
│  │ LATENCY                │ REQUESTS (24h)         │ SUCCESS RATE           │       │
│  │                        │                        │                        │       │
│  │ Current: 45ms          │ Total: 18,500          │ Current: 99.2%         │       │
│  │ P50: 42ms              │ Success: 18,352        │ 24h Avg: 99.1%         │       │
│  │ P95: 78ms              │ Failed: 148            │ 7d Avg: 99.0%          │       │
│  │ P99: 125ms             │ Retried: 520           │                        │       │
│  └────────────────────────┴────────────────────────┴────────────────────────┘       │
│                                                                                      │
│  MODELS                                                                             │
│  ┌──────────────────────────────────────────────────────────────────────────────┐   │
│  │ gemini-1.5-pro      │ 🟢 Active │ 8,500 requests │ 98.5% success │ $45.20    │   │
│  │ gemini-1.5-flash    │ 🟢 Active │ 6,200 requests │ 97.8% success │ $12.40    │   │
│  │ gemini-2.0-flash    │ 🟢 Active │ 3,800 requests │ 96.2% success │ $8.90     │   │
│  └──────────────────────────────────────────────────────────────────────────────┘   │
│                                                                                      │
│  [🔄 Force Health Check]  [⚙️ Configure]  [📊 View Telemetry]                       │
│                                                                                      │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

### View 3: Mobile Responsive Dashboard

```
┌───────────────────────────────┐
│ 🤖 LLM Dashboard    🔄 Admin ▼│
├───────────────────────────────┤
│                               │
│ SYSTEM: 🟢 HEALTHY            │
│                               │
│ ┌─────────┐┌─────────┐┌─────┐│
│ │🟢 Vertex││🟢 Deep  ││🟢 AWS││
│ │  45ms   ││  120ms  ││ 89ms ││
│ └─────────┘└─────────┘└─────┘│
│                               │
│ TODAY                         │
│ ┌─────────────────────────────┐
│ │ 45,231     98.7%    1,245ms│
│ │ Requests   Success  Latency│
│ └─────────────────────────────┘
│                               │
│ BUDGET                        │
│ ┌─────────────────────────────┐
│ │ $127.45 / $500              │
│ │ [██████████░░░░░░░░] 25%    │
│ └─────────────────────────────┘
│                               │
│ ALERTS (2 new)                │
│ ┌─────────────────────────────┐
│ │ ⚠️ 14:32 Latency spike     │
│ │ ⚠️ 12:15 Budget 80%        │
│ └─────────────────────────────┘
│                               │
│ [📊 Analytics] [⚙️ Settings]  │
│                               │
└───────────────────────────────┘
```

---

## 🔌 API Endpoints

### Provider Health

```typescript
// GET /admin/llm/providers
// Get all providers with health status

interface GetProvidersResponse {
  success: true;
  data: {
    providers: Provider[];
    system_status: 'healthy' | 'degraded' | 'down';
  };
}

interface Provider {
  id: string;                    // UUID
  name: string;                  // "vertex_ai"
  display_name: string;          // "Google Vertex AI"
  priority: number;              // 1-3
  is_enabled: boolean;
  health_status: 'healthy' | 'degraded' | 'down';
  health_check_latency_ms: number;
  last_health_check: string;     // ISO datetime
  config: Record<string, any>;
  models_count: number;
  active_models_count: number;
  created_at: string;
  updated_at: string;
}

// Error Responses
interface ErrorResponse {
  success: false;
  error: {
    code: 'LLM_001' | 'LLM_002' | 'LLM_003';
    message: string;
  };
}
```

### Telemetry Overview

```typescript
// GET /admin/llm/telemetry/overview?period=24h
// Get dashboard metrics overview

interface GetTelemetryOverviewRequest {
  period: '1h' | '24h' | '7d' | '30d';
}

interface GetTelemetryOverviewResponse {
  success: true;
  data: {
    period: string;
    total_requests: number;
    successful_requests: number;
    failed_requests: number;
    success_rate: number;
    
    latency: {
      avg_ms: number;
      p50_ms: number;
      p95_ms: number;
      p99_ms: number;
    };
    
    retries: {
      total: number;
      rate: number;
    };
    
    timeouts: {
      total: number;
      rate: number;
    };
    
    active_requests: number;
    
    cost: {
      total_usd: number;
      by_provider: Record<string, number>;
    };
    
    comparison: {
      requests_change_pct: number;
      success_change_pct: number;
      latency_change_ms: number;
    };
  };
}
```

### Budget Status

```typescript
// GET /admin/llm/budgets
// Get all budgets with current status

interface GetBudgetsResponse {
  success: true;
  data: {
    budgets: Budget[];
    today_spend: number;
    month_spend: number;
    projected_month_spend: number;
  };
}

interface Budget {
  id: string;
  name: string;
  budget_type: 'daily' | 'weekly' | 'monthly';
  budget_amount_usd: number;
  current_spend_usd: number;
  utilization_pct: number;
  warning_threshold_pct: number;
  critical_threshold_pct: number;
  is_hard_limit: boolean;
  is_active: boolean;
  period_start: string;
  period_end: string;
}
```

### Circuit Breakers

```typescript
// GET /admin/llm/circuit-breakers
// Get all circuit breaker states

interface GetCircuitBreakersResponse {
  success: true;
  data: {
    breakers: CircuitBreaker[];
    open_count: number;
    half_open_count: number;
    total_count: number;
  };
}

interface CircuitBreaker {
  id: string;
  entity_type: 'provider' | 'model';
  entity_id: string;
  entity_name: string;
  state: 'closed' | 'open' | 'half_open';
  failure_count: number;
  last_failure_at: string | null;
  opened_at: string | null;
  config: {
    failure_threshold: number;
    recovery_timeout_seconds: number;
    half_open_max_requests: number;
  };
}

// POST /admin/llm/circuit-breakers/{id}/reset
// Reset a circuit breaker

interface ResetCircuitBreakerResponse {
  success: true;
  data: {
    breaker_id: string;
    previous_state: string;
    new_state: 'closed';
    reset_at: string;
  };
}
```

### Time Series Data

```typescript
// GET /admin/llm/telemetry/timeseries?metric=requests&period=24h&group_by=provider
// Get time series data for charts

interface GetTimeSeriesRequest {
  metric: 'requests' | 'latency' | 'cost' | 'errors';
  period: '1h' | '24h' | '7d' | '30d';
  group_by?: 'provider' | 'model' | 'agent';
  interval?: 'minute' | 'hour' | 'day';
}

interface GetTimeSeriesResponse {
  success: true;
  data: {
    metric: string;
    period: string;
    interval: string;
    series: TimeSeriesPoint[];
  };
}

interface TimeSeriesPoint {
  timestamp: string;          // ISO datetime
  value: number;
  breakdown?: Record<string, number>;
}
```

### Quick Actions

```typescript
// POST /admin/llm/providers/{id}/health-check
// Force health check on provider

interface ForceHealthCheckResponse {
  success: true;
  data: {
    provider_id: string;
    status: 'healthy' | 'degraded' | 'down';
    latency_ms: number;
    checked_at: string;
  };
}

// POST /admin/llm/rankings/recalculate
// Trigger ranking recalculation

interface RecalculateRankingsResponse {
  success: true;
  data: {
    job_id: string;
    status: 'queued';
    estimated_duration_seconds: number;
  };
}
```

---

## 📊 Data Structures

### Module State

```typescript
interface LLMDashboardState {
  // Provider Data
  providers: Provider[];
  systemStatus: 'healthy' | 'degraded' | 'down';
  
  // Metrics Data
  overview: TelemetryOverview | null;
  timeSeries: TimeSeriesPoint[];
  
  // Budget Data
  budgets: Budget[];
  todaySpend: number;
  monthSpend: number;
  projectedSpend: number;
  
  // Circuit Breakers
  circuitBreakers: CircuitBreaker[];
  openBreakersCount: number;
  
  // Alerts
  alerts: Alert[];
  unacknowledgedCount: number;
  
  // Rankings
  topModelsByAgent: Record<string, RankedModel[]>;
  
  // UI State
  loading: {
    providers: boolean;
    overview: boolean;
    timeSeries: boolean;
    budgets: boolean;
    breakers: boolean;
    alerts: boolean;
  };
  
  errors: {
    providers: Error | null;
    overview: Error | null;
    timeSeries: Error | null;
  };
  
  // Real-time
  wsConnected: boolean;
  lastUpdate: string | null;
  
  // Filters
  timeSeriesPeriod: '1h' | '24h' | '7d' | '30d';
  timeSeriesGroupBy: 'provider' | 'model' | 'agent';
  
  // Actions
  pendingActions: string[];
}
```

### Alert Entity

```typescript
interface Alert {
  id: string;
  severity: 'critical' | 'warning' | 'info';
  title: string;
  message: string;
  source: string;                // Module/component that generated
  resource_type?: string;        // 'provider', 'model', 'budget'
  resource_id?: string;
  acknowledged: boolean;
  acknowledged_by?: string;
  acknowledged_at?: string;
  created_at: string;
  expires_at?: string;
}
```

### Ranked Model Entity

```typescript
interface RankedModel {
  model_id: string;
  model_name: string;
  provider_name: string;
  provider_icon: string;
  ranking_score: number;
  success_rate: number;
  avg_latency_ms: number;
  total_requests: number;
  trend: 'up' | 'down' | 'stable';
}
```

---

## 🎨 Component Specifications

### ProviderHealthCard

```typescript
interface ProviderHealthCardProps {
  provider: Provider;
  onViewDetails: (id: string) => void;
  onForceHealthCheck: (id: string) => void;
  loading?: boolean;
  expanded?: boolean;
}

// Usage
<ProviderHealthCard
  provider={vertexAI}
  onViewDetails={handleViewDetails}
  onForceHealthCheck={handleHealthCheck}
  expanded={selectedProvider === vertexAI.id}
/>
```

### MetricCard

```typescript
interface MetricCardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  icon?: React.ReactNode;
  trend?: {
    value: number;
    direction: 'up' | 'down' | 'stable';
    label: string;
  };
  status?: 'success' | 'warning' | 'error' | 'neutral';
  loading?: boolean;
  onClick?: () => void;
}

// Usage
<MetricCard
  title="Success Rate"
  value="98.7%"
  icon={<CheckCircle />}
  trend={{ value: 0.3, direction: 'up', label: 'vs yesterday' }}
  status="success"
/>
```

### BudgetProgressCard

```typescript
interface BudgetProgressCardProps {
  title: string;
  current: number;
  limit: number;
  projected?: number;
  variant: 'daily' | 'monthly';
  onManage?: () => void;
}

// Usage
<BudgetProgressCard
  title="Today's Spend"
  current={127.45}
  limit={500}
  variant="daily"
  onManage={handleManageBudget}
/>
```

### TimeSeriesChart

```typescript
interface TimeSeriesChartProps {
  data: TimeSeriesPoint[];
  metric: string;
  period: string;
  groupBy?: string;
  height?: number;
  showLegend?: boolean;
  interactive?: boolean;
  onPointClick?: (point: TimeSeriesPoint) => void;
}

// Usage
<TimeSeriesChart
  data={requestTimeSeries}
  metric="requests"
  period="24h"
  groupBy="provider"
  height={250}
  showLegend
  interactive
/>
```

### CircuitBreakerStatus

```typescript
interface CircuitBreakerStatusProps {
  breakers: CircuitBreaker[];
  openCount: number;
  onReset: (id: string) => void;
  onViewAll: () => void;
  loading?: boolean;
}

// Usage
<CircuitBreakerStatus
  breakers={circuitBreakers}
  openCount={openBreakersCount}
  onReset={handleResetBreaker}
  onViewAll={navigateToBreakers}
/>
```

### AlertTimeline

```typescript
interface AlertTimelineProps {
  alerts: Alert[];
  maxItems?: number;
  onAcknowledge: (id: string) => void;
  onViewAlert: (alert: Alert) => void;
  onViewAll: () => void;
}

// Usage
<AlertTimeline
  alerts={recentAlerts}
  maxItems={5}
  onAcknowledge={handleAcknowledge}
  onViewAlert={handleViewAlert}
  onViewAll={navigateToAlerts}
/>
```

### QuickActionPanel

```typescript
interface QuickAction {
  id: string;
  label: string;
  icon: React.ReactNode;
  onClick: () => void;
  loading?: boolean;
  disabled?: boolean;
  permission?: string;
}

interface QuickActionPanelProps {
  actions: QuickAction[];
  columns?: 2 | 3 | 4;
}

// Usage
<QuickActionPanel
  actions={[
    { id: 'health', label: 'Force Health Check', icon: <RefreshCw />, onClick: handleHealthCheck },
    { id: 'rankings', label: 'Recalculate Rankings', icon: <BarChart />, onClick: handleRecalculate },
    { id: 'export', label: 'Export Report', icon: <Download />, onClick: handleExport },
  ]}
  columns={3}
/>
```

---

## 🎬 Motion Design

```typescript
const llmDashboardAnimations = {
  // Page entry
  pageEnter: {
    initial: { opacity: 0 },
    animate: { opacity: 1 },
    transition: { duration: 0.3 }
  },
  
  // Staggered card entry
  staggerContainer: {
    animate: {
      transition: {
        staggerChildren: 0.05
      }
    }
  },
  
  staggerItem: {
    initial: { opacity: 0, y: 20 },
    animate: { opacity: 1, y: 0 },
    transition: { duration: 0.3 }
  },
  
  // Provider card hover
  providerCardHover: {
    scale: 1.02,
    boxShadow: '0 8px 30px rgba(59, 130, 246, 0.15)',
    transition: { duration: 0.2 }
  },
  
  // Metric value update
  metricUpdate: {
    scale: [1, 1.05, 1],
    color: ['inherit', '#10B981', 'inherit'],
    transition: { duration: 0.3 }
  },
  
  // Status indicator pulse
  statusPulse: {
    scale: [1, 1.2, 1],
    opacity: [1, 0.8, 1],
    transition: { duration: 1.5, repeat: Infinity }
  },
  
  // Alert slide in
  alertEnter: {
    initial: { opacity: 0, x: 50, height: 0 },
    animate: { opacity: 1, x: 0, height: 'auto' },
    exit: { opacity: 0, x: -50, height: 0 },
    transition: { duration: 0.3 }
  },
  
  // Progress bar fill
  progressFill: {
    initial: { width: 0 },
    animate: { width: '100%' },
    transition: { duration: 0.5, ease: 'easeOut' }
  },
  
  // Chart line draw
  chartLineDraw: {
    initial: { pathLength: 0 },
    animate: { pathLength: 1 },
    transition: { duration: 1, ease: 'easeInOut' }
  },
  
  // Button click feedback
  buttonTap: {
    scale: 0.95,
    transition: { duration: 0.1 }
  },
  
  // Loading skeleton
  skeleton: {
    opacity: [0.5, 1, 0.5],
    transition: { duration: 1.5, repeat: Infinity }
  },
  
  // WebSocket connected indicator
  wsConnected: {
    scale: [1, 1.2, 1],
    backgroundColor: ['#10B981', '#34D399', '#10B981'],
    transition: { duration: 2, repeat: Infinity }
  }
};
```

---

## ⌨️ Keyboard Shortcuts

```typescript
const llmDashboardShortcuts = {
  'mod+r': 'Refresh all data',
  'mod+h': 'Force health check',
  'mod+e': 'Export report',
  '1': 'Focus Vertex AI card',
  '2': 'Focus DeepInfra card',
  '3': 'Focus Bedrock card',
  'a': 'View all alerts',
  'b': 'View all breakers',
  't': 'Toggle time period (1h/24h/7d)',
  '?': 'Show keyboard shortcuts',
};
```

---

## ⚠️ Error Handling

```typescript
const errorCodes = {
  // API Errors
  LLM_DASH_001: 'Failed to fetch provider health data',
  LLM_DASH_002: 'Failed to fetch telemetry overview',
  LLM_DASH_003: 'Failed to fetch budget information',
  LLM_DASH_004: 'Failed to fetch circuit breaker status',
  LLM_DASH_005: 'Failed to fetch alerts',
  LLM_DASH_006: 'Failed to fetch time series data',
  
  // WebSocket Errors
  LLM_DASH_WS_001: 'WebSocket connection failed',
  LLM_DASH_WS_002: 'WebSocket disconnected unexpectedly',
  
  // Action Errors
  LLM_DASH_ACT_001: 'Failed to force health check',
  LLM_DASH_ACT_002: 'Failed to reset circuit breaker',
  LLM_DASH_ACT_003: 'Failed to acknowledge alert',
  LLM_DASH_ACT_004: 'Failed to trigger ranking recalculation',
  
  // Permission Errors
  LLM_DASH_PERM_001: 'Insufficient permissions for this action',
};

// Error display component
interface DashboardErrorProps {
  error: Error;
  section: string;
  onRetry: () => void;
}
```

---

## 📋 Field Requirements Summary

| Endpoint | Field | Type | Required | Validation |
|----------|-------|------|----------|------------|
| GET /telemetry/overview | period | enum | Yes | 1h, 24h, 7d, 30d |
| GET /telemetry/timeseries | metric | enum | Yes | requests, latency, cost, errors |
| GET /telemetry/timeseries | period | enum | Yes | 1h, 24h, 7d, 30d |
| GET /telemetry/timeseries | group_by | enum | No | provider, model, agent |
| POST /circuit-breakers/{id}/reset | id | uuid | Yes | Valid UUID |

---

## 🔒 Security Considerations

1. **Authentication:** JWT token required for all API calls, token refresh handled automatically
2. **Authorization:** Quick actions disabled for non-admin users, UI elements hidden based on permissions
3. **Data Sanitization:** All displayed values sanitized to prevent XSS
4. **Rate Limiting:** Dashboard respects API rate limits, shows warning if limit approached
5. **Audit Logging:** All admin actions logged with user ID, timestamp, and action details
6. **Session Timeout:** Auto-logout after 30 minutes of inactivity with warning modal

---

*Document Version: 1.0*  
*Last Updated: December 1, 2025*  
*Module: LLM Dashboard*  
*User Type: Admin / Operator / Viewer*
