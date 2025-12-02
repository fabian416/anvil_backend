# FRONTEND_ADMIN_ANALYTICS_PLATFORM

## Admin Platform Analytics Module

**User Type:** Admin  
**Module:** Platform Analytics  
**Route:** `/admin/analytics`  
**Access Level:** Read (All) | Export (Admin+)

---

## 📋 Module Overview

### Title
**Platform Analytics** - Cross-Platform Insights

### Description
Comprehensive analytics dashboard providing insights across all projects, users, and transactions. Enables data-driven decision making with growth metrics, engagement trends, and business KPIs.

### Key Capabilities
- Platform-wide metrics
- Growth and retention analysis
- Cross-project comparisons
- User engagement tracking
- Transaction volume trends
- Custom report generation

---

## 🖼️ Views & Wireframes

### View 1: Platform Analytics Dashboard

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│  📊 Platform Analytics                          [Last 30 Days ▼] [📥 Export Report] │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                      │
│  ┌─ Key Metrics ───────────────────────────────────────────────────────────────────┐│
│  │                                                                                  ││
│  │  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────┐ ││
│  │  │ 👥 24,567       │  │ 💬 89,234       │  │ 💰 $4.5M        │  │ 📈 $127K    │ ││
│  │  │    Total Users  │  │    Conversations│  │    Tx Volume    │  │    Revenue  │ ││
│  │  │    ↑ 12% MoM    │  │    ↑ 23% MoM    │  │    ↑ 45% MoM    │  │    ↑ 18% MoM│ ││
│  │  └─────────────────┘  └─────────────────┘  └─────────────────┘  └─────────────┘ ││
│  │                                                                                  ││
│  └─────────────────────────────────────────────────────────────────────────────────┘│
│                                                                                      │
│  USER GROWTH                                      ENGAGEMENT                        │
│  ┌────────────────────────────────────┐          ┌────────────────────────────────┐ │
│  │                                    │          │                                │ │
│  │  25K ┤                    ╭────    │          │  DAU/MAU Ratio: 34%            │ │
│  │      │              ╭────╯         │          │  [████████████░░░░░░░] Good    │ │
│  │  20K ┤        ╭─────╯              │          │                                │ │
│  │      │   ╭────╯                    │          │  Avg Session: 8.5 min          │ │
│  │  15K ┤───╯                         │          │  [██████████████░░░░] ↑ 12%   │ │
│  │      └────────────────────────▶    │          │                                │ │
│  │       Oct    Nov    Dec            │          │  Messages/Session: 4.2         │ │
│  │                                    │          │  [████████████████░░] ↑ 8%    │ │
│  │  New: 3,456 │ Churned: 892         │          │                                │ │
│  │  Net Growth: +2,564 (+11.6%)       │          │  Tx/Active User: 6.3           │ │
│  │                                    │          │  [████████████░░░░░░] ↑ 15%   │ │
│  └────────────────────────────────────┘          └────────────────────────────────┘ │
│                                                                                      │
│  TRANSACTION VOLUME                               TOP PROJECTS                      │
│  ┌────────────────────────────────────┐          ┌────────────────────────────────┐ │
│  │                                    │          │                                │ │
│  │  $200K ┤         ╭─╮               │          │  By Users                      │ │
│  │        │        ╭╯ ╰╮    ╭─        │          │  1. Aave         8,234  (34%) │ │
│  │  $150K ┤   ╭────╯   ╰────╯         │          │  2. Uniswap      5,123  (21%) │ │
│  │        │ ──╯                       │          │  3. Lido         3,456  (14%) │ │
│  │  $100K ┤                           │          │  4. 1inch        2,890  (12%) │ │
│  │        └────────────────────────▶  │          │  5. General      4,864  (19%) │ │
│  │         Oct    Nov    Dec          │          │                                │ │
│  │                                    │          │  By Volume                     │ │
│  │  Swaps: $2.1M │ Lending: $1.8M     │          │  1. Aave         $1.8M  (40%) │ │
│  │  Staking: $0.6M                    │          │  2. Uniswap      $1.2M  (27%) │ │
│  └────────────────────────────────────┘          └────────────────────────────────┘ │
│                                                                                      │
│  AI PERFORMANCE                                   RETENTION COHORTS                 │
│  ┌────────────────────────────────────┐          ┌────────────────────────────────┐ │
│  │                                    │          │                                │ │
│  │  LLM Requests: 245,678             │          │         D1    D7   D14   D30  │ │
│  │  Avg Latency: 1.2s                 │          │  Oct    82%   56%   45%   38% │ │
│  │  Success Rate: 97.5%               │          │  Nov    85%   58%   47%   -   │ │
│  │                                    │          │  Dec    84%   -     -     -   │ │
│  │  Cost Breakdown:                   │          │                                │ │
│  │  • Full LLM: $8,450 (65%)          │          │  Avg D30: 38% (↑ 3%)          │ │
│  │  • Light LLM: $2,890 (22%)         │          │                                │ │
│  │  • Cached: $0 (13%)                │          │                                │ │
│  │                                    │          │                                │ │
│  │  Savings from Distillation: $4,230 │          │                                │ │
│  │                                    │          │                                │ │
│  └────────────────────────────────────┘          └────────────────────────────────┘ │
│                                                                                      │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 🔌 API Endpoints

### Get Platform Analytics

```typescript
// GET /admin/analytics?period=30d
interface GetPlatformAnalyticsResponse {
  success: true;
  data: {
    period: string;
    key_metrics: {
      total_users: MetricWithChange;
      conversations: MetricWithChange;
      transaction_volume_usd: MetricWithChange;
      revenue_usd: MetricWithChange;
    };
    user_growth: {
      timeseries: TimeSeriesPoint[];
      new_users: number;
      churned_users: number;
      net_growth: number;
      growth_rate: number;
    };
    engagement: {
      dau_mau_ratio: number;
      avg_session_minutes: number;
      messages_per_session: number;
      transactions_per_active_user: number;
    };
    transaction_volume: {
      timeseries: TimeSeriesPoint[];
      by_type: Record<string, number>;
    };
    top_projects: {
      by_users: Array<{ name: string; count: number; percentage: number }>;
      by_volume: Array<{ name: string; volume_usd: number; percentage: number }>;
    };
    ai_performance: {
      total_requests: number;
      avg_latency_ms: number;
      success_rate: number;
      cost_breakdown: Record<string, number>;
      distillation_savings_usd: number;
    };
    retention_cohorts: RetentionCohort[];
  };
}

interface MetricWithChange {
  value: number;
  change_pct: number;
  change_direction: 'up' | 'down' | 'flat';
}

interface RetentionCohort {
  cohort: string;
  d1: number;
  d7: number;
  d14: number;
  d30: number;
}
```

---

*Document Version: 1.0*  
*Last Updated: December 1, 2025*  
*Module: Platform Analytics*
