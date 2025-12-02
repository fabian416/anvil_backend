# FRONTEND_ADMIN_PROJECTS_ANALYTICS

## Admin Project Analytics Module

**User Type:** Admin  
**Module:** Project Analytics  
**Route:** `/admin/projects/:id/analytics`  
**Access Level:** Read (All) | Export (Admin)

---

## 📋 Module Overview

### Title
**Project Analytics** - Usage & Performance Insights

### Description
Comprehensive analytics dashboard for individual projects, providing insights into user engagement, conversation quality, transaction volume, agent performance, and business metrics.

### Key Capabilities
- User engagement metrics
- Conversation analytics
- Transaction volume and value tracking
- Agent performance metrics
- Funnel analysis
- Custom date range analysis
- Export capabilities

---

## 👤 User Stories

### US-ADMIN-ANALYTICS-001: View Engagement Overview
**As a** platform administrator  
**I want to** see user engagement metrics  
**So that** I understand project popularity

### US-ADMIN-ANALYTICS-002: Analyze Conversations
**As a** platform administrator  
**I want to** see conversation metrics  
**So that** I understand user interaction patterns

### US-ADMIN-ANALYTICS-003: Track Transactions
**As a** platform administrator  
**I want to** see transaction volume and value  
**So that** I understand business impact

### US-ADMIN-ANALYTICS-004: Monitor Agent Performance
**As a** platform administrator  
**I want to** see agent success rates  
**So that** I can improve AI quality

### US-ADMIN-ANALYTICS-005: Export Reports
**As a** platform administrator  
**I want to** export analytics data  
**So that** I can share with stakeholders

---

## 🖼️ Views & Wireframes

### View 1: Analytics Dashboard

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│  📊 Analytics: Aave                                     [Last 30 Days ▼] [📥 Export]│
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                      │
│  [Overview]  [Users]  [Conversations]  [Transactions]  [Agent]                      │
│  ─────────────────────────────────────────────────────────────────────────────────  │
│                                                                                      │
│  ┌─ Key Metrics ───────────────────────────────────────────────────────────────────┐│
│  │  ┌────────────────┐  ┌────────────────┐  ┌────────────────┐  ┌────────────────┐ ││
│  │  │ 👥 Users       │  │ 💬 Conversations│  │ 💰 Tx Volume   │  │ ⭐ Satisfaction│ ││
│  │  │ 2,456          │  │ 8,920          │  │ $1.2M          │  │ 4.6/5          │ ││
│  │  │ ↑ 12%          │  │ ↑ 23%          │  │ ↑ 45%          │  │ ↑ 0.2          │ ││
│  │  └────────────────┘  └────────────────┘  └────────────────┘  └────────────────┘ ││
│  └─────────────────────────────────────────────────────────────────────────────────┘│
│                                                                                      │
│  USER ACTIVITY                                    CONVERSATION VOLUME               │
│  ┌────────────────────────────────────┐          ┌────────────────────────────────┐ │
│  │                                    │          │                                │ │
│  │  500 ┤            ╭──╮             │          │  400 ┤         ╭─╮             │ │
│  │      │           ╭╯  ╰╮    ╭─      │          │      │        ╭╯ ╰╮   ╭──      │ │
│  │  300 ┤     ╭─────╯    ╰────╯       │          │  200 ┤   ╭────╯   ╰───╯        │ │
│  │      │ ────╯                       │          │      │ ──╯                     │ │
│  │  100 ┤                             │          │    0 └────────────────────▶    │ │
│  │      └────────────────────────▶    │          │       Week 1  2   3   4        │ │
│  │       Week 1  2   3   4            │          │                                │ │
│  │                                    │          │  Daily avg: 297                │ │
│  │  DAU: 245 │ WAU: 890 │ MAU: 2,456  │          └────────────────────────────────┘ │
│  └────────────────────────────────────┘                                             │
│                                                                                      │
│  TOP USER INTENTS                                 TRANSACTION BREAKDOWN             │
│  ┌────────────────────────────────────┐          ┌────────────────────────────────┐ │
│  │                                    │          │                                │ │
│  │  1. balance_check     ████████ 28% │          │  Supply     █████████████ 45% │ │
│  │  2. supply_request    ██████   22% │          │             $540,000           │ │
│  │  3. borrow_request    █████    18% │          │                                │ │
│  │  4. health_factor     ████     14% │          │  Borrow     ████████     32%  │ │
│  │  5. rate_check        ███      10% │          │             $384,000           │ │
│  │  6. other             ██        8% │          │                                │ │
│  │                                    │          │  Repay      █████        18%  │ │
│  │  [View All Intents →]              │          │             $216,000           │ │
│  └────────────────────────────────────┘          │                                │ │
│                                                   │  Withdraw   ██           5%   │ │
│                                                   │             $60,000            │ │
│                                                   └────────────────────────────────┘ │
│                                                                                      │
│  AGENT PERFORMANCE                                                                  │
│  ┌─────────────────────────────────────────────────────────────────────────────────┐│
│  │                                                                                  ││
│  │  Success Rate        Task Completion      Avg Response Time    User Rating     ││
│  │  ┌────────────┐     ┌────────────┐       ┌────────────┐       ┌────────────┐   ││
│  │  │   96.2%    │     │   89.5%    │       │   1.2s     │       │   4.6★     │   ││
│  │  │   ↑ 1.2%   │     │   ↑ 3.4%   │       │   ↓ 0.3s   │       │   ↑ 0.2    │   ││
│  │  └────────────┘     └────────────┘       └────────────┘       └────────────┘   ││
│  │                                                                                  ││
│  └─────────────────────────────────────────────────────────────────────────────────┘│
│                                                                                      │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

### View 2: User Analytics Tab

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│  📊 Analytics: Aave - Users                             [Last 30 Days ▼] [📥 Export]│
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                      │
│  [Overview]  [Users]  [Conversations]  [Transactions]  [Agent]                      │
│  ─────────────────────────────────────────────────────────────────────────────────  │
│                                                                                      │
│  USER GROWTH                                                                        │
│  ┌─────────────────────────────────────────────────────────────────────────────────┐│
│  │                                                                                  ││
│  │  2500 ┤                                                        ────────────     ││
│  │       │                                              ────────────                ││
│  │  2000 ┤                                    ────────────                          ││
│  │       │                          ────────────                                    ││
│  │  1500 ┤                ────────────                               ── Total      ││
│  │       │      ────────────                                         ── Active     ││
│  │  1000 ┤────────                                                                 ││
│  │       └────────────────────────────────────────────────────────────────▶        ││
│  │        Nov 1        Nov 8        Nov 15       Nov 22       Nov 29               ││
│  │                                                                                  ││
│  │  Total: 2,456 │ New (30d): 456 │ Churned: 89 │ Net Growth: +367                ││
│  └─────────────────────────────────────────────────────────────────────────────────┘│
│                                                                                      │
│  USER SEGMENTS                                    RETENTION COHORTS                 │
│  ┌────────────────────────────────────┐          ┌────────────────────────────────┐ │
│  │                                    │          │       D1    D7   D14   D30     │ │
│  │  By Activity Level                 │          │ Nov W1  78%  52%  41%  32%     │ │
│  │  • Power (10+ tx)    ████    12%   │          │ Nov W2  81%  55%  44%   -      │ │
│  │  • Regular (3-9 tx)  ████████ 28%  │          │ Nov W3  76%  49%   -    -      │ │
│  │  • Casual (1-2 tx)   ██████████ 35%│          │ Nov W4  79%   -    -    -      │ │
│  │  • Inactive (0 tx)   ████████ 25%  │          │                                │ │
│  │                                    │          │ Avg D30 Retention: 32%         │ │
│  │  By Chain                          │          └────────────────────────────────┘ │
│  │  • Ethereum          ████████ 45%  │                                             │
│  │  • Arbitrum          ██████   32%  │          USER ACQUISITION                   │
│  │  • Polygon           ████     18%  │          ┌────────────────────────────────┐ │
│  │  • Base              ██        5%  │          │ Direct         ████████ 45%    │ │
│  │                                    │          │ Referral       █████    28%    │ │
│  └────────────────────────────────────┘          │ Social         ███      15%    │ │
│                                                   │ Partner        ██       12%    │ │
│                                                   └────────────────────────────────┘ │
│                                                                                      │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

### View 3: Transaction Analytics Tab

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│  📊 Analytics: Aave - Transactions                      [Last 30 Days ▼] [📥 Export]│
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                      │
│  [Overview]  [Users]  [Conversations]  [Transactions]  [Agent]                      │
│  ─────────────────────────────────────────────────────────────────────────────────  │
│                                                                                      │
│  TRANSACTION VOLUME                                                                 │
│  ┌─────────────────────────────────────────────────────────────────────────────────┐│
│  │                                                                                  ││
│  │  $60K ┤                    ╭──╮                                                  ││
│  │       │                   ╭╯  ╰╮     ╭─╮                                         ││
│  │  $40K ┤      ╭────────────╯    ╰─────╯ ╰────                                    ││
│  │       │ ─────╯                                                                   ││
│  │  $20K ┤                                                                          ││
│  │       └────────────────────────────────────────────────────────────────▶        ││
│  │        Nov 1        Nov 8        Nov 15       Nov 22       Nov 29               ││
│  │                                                                                  ││
│  │  Total: $1.2M │ Avg Daily: $40K │ Peak: $62K (Nov 12)                           ││
│  └─────────────────────────────────────────────────────────────────────────────────┘│
│                                                                                      │
│  TRANSACTION BREAKDOWN                            TOP TOKENS BY VOLUME              │
│  ┌────────────────────────────────────┐          ┌────────────────────────────────┐ │
│  │                                    │          │                                │ │
│  │  BY TYPE                           │          │  1. USDC       ████████ $480K  │ │
│  │  ┌────────────────────────────┐    │          │  2. ETH        ██████   $360K  │ │
│  │  │ Supply   │████████████│45% │    │          │  3. WBTC       ████     $192K  │ │
│  │  │ Borrow   │████████    │32% │    │          │  4. DAI        ███      $120K  │ │
│  │  │ Repay    │█████       │18% │    │          │  5. USDT       ██       $48K   │ │
│  │  │ Withdraw │██          │ 5% │    │          │                                │ │
│  │  └────────────────────────────┘    │          └────────────────────────────────┘ │
│  │                                    │                                             │
│  │  BY CHAIN                          │          TRANSACTION SUCCESS               │
│  │  ┌────────────────────────────┐    │          ┌────────────────────────────────┐ │
│  │  │ Ethereum │███████████ │52% │    │          │                                │ │
│  │  │ Arbitrum │██████      │32% │    │          │  ✅ Successful    2,890  94.2% │ │
│  │  │ Polygon  │███         │12% │    │          │  ❌ Failed          145   4.7% │ │
│  │  │ Base     │█           │ 4% │    │          │  ⏱️ Pending          35   1.1% │ │
│  │  └────────────────────────────┘    │          │                                │ │
│  │                                    │          │  Avg Gas: $2.45                │ │
│  └────────────────────────────────────┘          │  Total Gas: $7,520             │ │
│                                                   └────────────────────────────────┘ │
│                                                                                      │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 🔌 API Endpoints

### Get Project Analytics

```typescript
// GET /admin/projects/{id}/analytics?period=30d
interface GetProjectAnalyticsResponse {
  success: true;
  data: {
    period: string;
    summary: {
      users: MetricWithChange;
      conversations: MetricWithChange;
      transaction_volume_usd: MetricWithChange;
      satisfaction_score: MetricWithChange;
    };
    users: {
      total: number;
      active: number;
      new: number;
      churned: number;
      growth_timeseries: TimeSeriesPoint[];
      segments: Record<string, number>;
      acquisition_sources: Record<string, number>;
      retention_cohorts: RetentionCohort[];
    };
    conversations: {
      total: number;
      avg_daily: number;
      avg_length: number;
      timeseries: TimeSeriesPoint[];
      intent_distribution: Record<string, number>;
      satisfaction_distribution: Record<number, number>;
    };
    transactions: {
      total_count: number;
      total_volume_usd: number;
      avg_daily_volume_usd: number;
      by_type: Record<string, TransactionStats>;
      by_chain: Record<string, TransactionStats>;
      by_token: Record<string, TransactionStats>;
      success_rate: number;
      timeseries: TimeSeriesPoint[];
    };
    agent: {
      success_rate: number;
      task_completion_rate: number;
      avg_response_time_ms: number;
      user_rating: number;
      error_distribution: Record<string, number>;
    };
  };
}

interface MetricWithChange {
  value: number;
  change_pct: number;
  change_direction: 'up' | 'down' | 'flat';
}

interface RetentionCohort {
  week: string;
  d1: number;
  d7: number;
  d14: number;
  d30: number;
}

interface TransactionStats {
  count: number;
  volume_usd: number;
  percentage: number;
}
```

### Export Analytics

```typescript
// POST /admin/projects/{id}/analytics/export
interface ExportAnalyticsRequest {
  period: string;
  sections: string[];  // ['users', 'conversations', 'transactions', 'agent']
  format: 'csv' | 'pdf' | 'json';
}

interface ExportAnalyticsResponse {
  success: true;
  data: {
    export_id: string;
    download_url: string;
    expires_at: string;
  };
}
```

---

## 🎬 Motion Design

```typescript
const analyticsAnimations = {
  chartDraw: {
    pathLength: [0, 1],
    transition: { duration: 1.2, ease: 'easeOut' }
  },
  
  metricCounter: {
    opacity: [0, 1],
    y: [20, 0],
    transition: { duration: 0.5, delay: 0.2 }
  },
  
  barGrow: {
    width: '100%',
    transition: { duration: 0.8, ease: 'easeOut' }
  },
  
  tabSwitch: {
    opacity: [0, 1],
    x: [10, 0],
    transition: { duration: 0.2 }
  }
};
```

---

*Document Version: 1.0*  
*Last Updated: December 1, 2025*  
*Module: Project Analytics*
