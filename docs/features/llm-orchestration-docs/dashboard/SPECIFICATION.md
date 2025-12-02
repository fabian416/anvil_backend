# Business Control Panel Specification

## Overview

The Business Control Panel provides non-technical stakeholders with visibility and control over the LLM orchestration system.

---

## Dashboard Layout

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    LLM ORCHESTRATION CONTROL PANEL                           │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │  SYSTEM HEALTH                                           🟢 HEALTHY  │    │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐                          │    │
│  │  │ Vertex   │  │ DeepInfra│  │ Bedrock  │                          │    │
│  │  │   🟢     │  │    🟢    │  │   🟢     │                          │    │
│  │  │ 45ms avg │  │ 120ms avg│  │ 89ms avg │                          │    │
│  │  └──────────┘  └──────────┘  └──────────┘                          │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  ┌───────────────────────────┐  ┌───────────────────────────────────────┐   │
│  │  TODAY'S METRICS          │  │  COST TRACKING                        │   │
│  │                           │  │                                       │   │
│  │  Requests: 45,231         │  │  Today: $127.45 / $500 budget        │   │
│  │  Success Rate: 98.7%      │  │  [█████████░░░░░░░░░░] 25%            │   │
│  │  Avg Latency: 1,245ms     │  │                                       │   │
│  │  Retries: 3.2%            │  │  This Month: $2,847 / $10,000        │   │
│  │  Timeouts: 0.8%           │  │  [████████░░░░░░░░░░░] 28%            │   │
│  │                           │  │                                       │   │
│  └───────────────────────────┘  └───────────────────────────────────────┘   │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │  REQUESTS OVER TIME (24h)                                           │    │
│  │  5k ┤                         ╭──╮                                  │    │
│  │     │    ╭─╮     ╭──╮       ╭╯  ╰╮      ╭─╮                        │    │
│  │  3k ┤   ╭╯ ╰──╮ ╭╯  ╰──╮  ╭╯    ╰─────╯ ╰╮                        │    │
│  │     │  ╭╯     ╰─╯      ╰──╯               ╰─────                    │    │
│  │  1k ┤──╯                                                            │    │
│  │     └───────────────────────────────────────────────────────────▶  │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │  TOP PERFORMING MODELS BY AGENT                                     │    │
│  │                                                                     │    │
│  │  SwapAgent:                                                         │    │
│  │    1. 🥇 gemini-1.5-pro (98.5% success, 890ms avg)                 │    │
│  │    2. 🥈 claude-3-5-sonnet (97.8% success, 1,120ms avg)            │    │
│  │    3. 🥉 llama-3.1-405b (96.2% success, 1,450ms avg)               │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  ┌───────────────────────────────┐  ┌───────────────────────────────────┐   │
│  │  CIRCUIT BREAKERS            │  │  RECENT ALERTS                     │   │
│  │                              │  │                                    │   │
│  │  Vertex AI    │ 🟢 Closed    │  │  ⚠️ 14:32 DeepInfra latency spike │   │
│  │  DeepInfra    │ 🟢 Closed    │  │  ⚠️ 12:15 Budget 80% threshold    │   │
│  │  Bedrock      │ 🟢 Closed    │  │  ✅ 10:00 All systems recovered   │   │
│  └───────────────────────────────┘  └───────────────────────────────────┘   │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Key Features

### 1. System Health Overview
- Real-time provider status
- Health check latency
- Circuit breaker states
- Overall system status indicator

### 2. Metrics Dashboard
- Request volume (total, by status)
- Success/failure rates
- Latency percentiles
- Retry and timeout rates

### 3. Cost Management
- Daily/weekly/monthly spend
- Budget utilization bars
- Cost projections
- Per-provider/model breakdown

### 4. Model Rankings
- Top models per agent
- Performance metrics
- Manual override controls
- A/B test results

### 5. Alert Management
- Active alerts list
- Alert history
- Alert configuration
- Notification settings

---

## React Component Structure

```typescript
// Dashboard component hierarchy
<DashboardLayout>
  <Header>
    <SystemHealthBadge />
    <DateRangePicker />
    <RefreshButton />
  </Header>
  
  <MainContent>
    <Row>
      <ProviderHealthCards />
    </Row>
    
    <Row>
      <MetricsSummaryCard />
      <CostTrackingCard />
    </Row>
    
    <Row>
      <RequestsTimeSeriesChart />
    </Row>
    
    <Row>
      <ModelRankingsTable />
    </Row>
    
    <Row>
      <CircuitBreakerStatus />
      <RecentAlerts />
    </Row>
  </MainContent>
  
  <QuickActions>
    <ForceHealthCheckButton />
    <ExportReportButton />
    <ProviderConfigButton />
    <BudgetSettingsButton />
  </QuickActions>
</DashboardLayout>
```

---

## API Integration

### Real-time Updates

```typescript
// WebSocket connection for live updates
const ws = new WebSocket('wss://api.anvil.finance/admin/llm/stream');

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  
  switch (data.type) {
    case 'metrics.update':
      updateMetrics(data.payload);
      break;
    case 'health.change':
      updateProviderHealth(data.payload);
      break;
    case 'alert.new':
      addAlert(data.payload);
      break;
    case 'circuit_breaker.change':
      updateCircuitBreaker(data.payload);
      break;
  }
};
```

### Data Fetching

```typescript
// Dashboard data hooks
const useDashboardData = (period: string) => {
  const { data: overview } = useQuery(
    ['llm-overview', period],
    () => fetch(`/admin/llm/telemetry/overview?period=${period}`)
  );
  
  const { data: rankings } = useQuery(
    ['llm-rankings'],
    () => fetch('/admin/llm/rankings')
  );
  
  const { data: budgets } = useQuery(
    ['llm-budgets'],
    () => fetch('/admin/llm/budgets')
  );
  
  return { overview, rankings, budgets };
};
```

---

## User Permissions

| Role | View | Configure | Admin |
|------|------|-----------|-------|
| Viewer | ✅ | ❌ | ❌ |
| Operator | ✅ | ✅ | ❌ |
| Admin | ✅ | ✅ | ✅ |

---

## Mobile Responsiveness

The dashboard is fully responsive with breakpoints:
- **Desktop**: Full layout (>1200px)
- **Tablet**: Stacked cards (768-1200px)
- **Mobile**: Single column (<768px)
