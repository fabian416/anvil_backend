# FRONTEND_ADMIN_ANALYTICS_REVENUE

## Admin Revenue Analytics Module

**User Type:** Admin  
**Module:** Revenue Analytics  
**Route:** `/admin/analytics/revenue`  
**Access Level:** Read (Finance+) | Manage (Admin+)

---

## 📋 Module Overview

### Title
**Revenue Analytics** - Financial Performance Insights

### Description
Comprehensive revenue analytics dashboard with cohort analysis, LTV calculations, revenue forecasting, and financial health metrics.

### Key Capabilities
- Revenue trends & forecasting
- Cohort analysis
- LTV/CAC metrics
- Churn revenue analysis
- Revenue by segment
- Financial projections

---

## 🖼️ Views & Wireframes

### View 1: Revenue Analytics Dashboard

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│  📈 Revenue Analytics                                     [📥 Export] [📊 Report]   │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                      │
│  Period: [Last 12 Months ▼]    Compare: [Previous Period ▼]                         │
│                                                                                      │
│  ┌─ Key Metrics ───────────────────────────────────────────────────────────────────┐│
│  │                                                                                  ││
│  │  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────┐ ││
│  │  │ 💰 $1.52M       │  │ 📈 $127,450     │  │ 👤 $534         │  │ 💎 $4,230   │ ││
│  │  │    ARR          │  │    MRR          │  │    ARPU         │  │    LTV      │ ││
│  │  │    ↑ 42% YoY    │  │    ↑ 12% MoM    │  │    ↑ 8% MoM     │  │    ↑ 15%    │ ││
│  │  └─────────────────┘  └─────────────────┘  └─────────────────┘  └─────────────┘ ││
│  │                                                                                  ││
│  │  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────┐ ││
│  │  │ 📉 2.3%         │  │ 💸 $2,890       │  │ 🎯 3.2x         │  │ ⏱️ 8.2 mo   │ ││
│  │  │    Churn Rate   │  │    Churned MRR  │  │    LTV:CAC      │  │    Payback  │ ││
│  │  │    ↓ 0.5% MoM   │  │    ↓ 12% MoM    │  │    ↑ 0.4x       │  │    ↓ 1.1 mo │ ││
│  │  └─────────────────┘  └─────────────────┘  └─────────────────┘  └─────────────┘ ││
│  │                                                                                  ││
│  └─────────────────────────────────────────────────────────────────────────────────┘│
│                                                                                      │
│  MRR TREND                                                                          │
│  ┌─────────────────────────────────────────────────────────────────────────────────┐│
│  │                                                                                  ││
│  │  $150K ┤                                                   ╭────────            ││
│  │        │                                            ╭──────╯                    ││
│  │  $100K ┤                                     ╭──────╯                           ││
│  │        │                              ╭──────╯                                  ││
│  │   $50K ┤                       ╭──────╯                                         ││
│  │        │    ───────────────────╯                                                ││
│  │     $0 ┼──────────────────────────────────────────────────────────────────▶    ││
│  │         Jan   Feb   Mar   Apr   May   Jun   Jul   Aug   Sep   Oct   Nov   Dec  ││
│  │                                                                                  ││
│  │  ── Total MRR    ── New MRR    ── Expansion    ── Churned                       ││
│  │                                                                                  ││
│  └─────────────────────────────────────────────────────────────────────────────────┘│
│                                                                                      │
│  MRR BREAKDOWN                                REVENUE BY PLAN                       │
│  ┌────────────────────────────────────┐      ┌────────────────────────────────────┐ │
│  │                                    │      │                                    │ │
│  │  🆕 New MRR        $18,450   14.5% │      │  💎 Elite                          │ │
│  │  📈 Expansion      $8,230     6.5% │      │  $67,230 (52.7%) │ 892 users       │ │
│  │  🔄 Contraction   -$1,890    -1.5% │      │  ████████████████████              │ │
│  │  📉 Churned       -$2,890    -2.3% │      │                                    │ │
│  │  ────────────────────────────────  │      │  ⭐ Pro                            │ │
│  │  📊 Net New        $21,900   17.2% │      │  $48,960 (38.4%) │ 1,632 users     │ │
│  │                                    │      │  ███████████████                   │ │
│  │  Total MRR:       $127,450         │      │                                    │ │
│  │                                    │      │  🆓 Free+                          │ │
│  │                                    │      │  $11,260 (8.8%) │ 323 users        │ │
│  │                                    │      │  ███                               │ │
│  │                                    │      │                                    │ │
│  └────────────────────────────────────┘      └────────────────────────────────────┘ │
│                                                                                      │
│  COHORT RETENTION                                                                   │
│  ┌─────────────────────────────────────────────────────────────────────────────────┐│
│  │                                                                                  ││
│  │  COHORT    │ M0    │ M1    │ M2    │ M3    │ M4    │ M5    │ M6               ││
│  │  ──────────┼───────┼───────┼───────┼───────┼───────┼───────┼───────            ││
│  │  Jun 2025  │ 100%  │ 92%   │ 88%   │ 85%   │ 82%   │ 80%   │ 78%              ││
│  │  Jul 2025  │ 100%  │ 94%   │ 90%   │ 87%   │ 84%   │ 82%   │ -                ││
│  │  Aug 2025  │ 100%  │ 93%   │ 89%   │ 86%   │ 83%   │ -     │ -                ││
│  │  Sep 2025  │ 100%  │ 95%   │ 91%   │ 88%   │ -     │ -     │ -                ││
│  │  Oct 2025  │ 100%  │ 94%   │ 90%   │ -     │ -     │ -     │ -                ││
│  │  Nov 2025  │ 100%  │ 95%   │ -     │ -     │ -     │ -     │ -                ││
│  │  Dec 2025  │ 100%  │ -     │ -     │ -     │ -     │ -     │ -                ││
│  │                                                                                  ││
│  │  Legend: ████ >90%  ███ 80-90%  ██ 70-80%  █ <70%                              ││
│  │                                                                                  ││
│  └─────────────────────────────────────────────────────────────────────────────────┘│
│                                                                                      │
│  REVENUE FORECAST                                                                   │
│  ┌─────────────────────────────────────────────────────────────────────────────────┐│
│  │                                                                                  ││
│  │  Based on current trends, projected revenue for next 12 months:                 ││
│  │                                                                                  ││
│  │  $200K ┤                                                          ╱╱╱╱         ││
│  │        │                                                    ╱╱╱╱╱╱              ││
│  │  $150K ┤                                              ╱╱╱╱╱╱──────              ││
│  │        │                                        ╱╱╱╱╱╱                          ││
│  │  $100K ┤─────────────────────────────────╱╱╱╱╱╱                                ││
│  │        │                                                                        ││
│  │   $50K ┤                                                                        ││
│  │        └────────────────────────────────────────────────────────────────▶      ││
│  │         Dec   Jan   Feb   Mar   Apr   May   Jun   Jul   Aug   Sep   Oct   Nov  ││
│  │                                                                                  ││
│  │  ── Projected MRR    ╱╱ Confidence Range (80%)                                  ││
│  │                                                                                  ││
│  │  Projected ARR (Dec 2026): $2.15M (+42%)                                        ││
│  │                                                                                  ││
│  └─────────────────────────────────────────────────────────────────────────────────┘│
│                                                                                      │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 🔌 API Endpoints

```typescript
// GET /admin/analytics/revenue
interface GetRevenueAnalyticsRequest {
  period?: '30d' | '90d' | '12m' | 'ytd' | 'all';
  compare?: 'previous_period' | 'previous_year' | 'none';
}

interface GetRevenueAnalyticsResponse {
  success: true;
  data: {
    key_metrics: {
      arr: MetricWithChange;
      mrr: MetricWithChange;
      arpu: MetricWithChange;
      ltv: MetricWithChange;
      churn_rate: MetricWithChange;
      churned_mrr: MetricWithChange;
      ltv_cac_ratio: MetricWithChange;
      payback_months: MetricWithChange;
    };
    mrr_trend: TimeSeriesPoint[];
    mrr_breakdown: {
      new: number;
      expansion: number;
      contraction: number;
      churned: number;
      net_new: number;
      total: number;
    };
    revenue_by_plan: Array<{
      plan: string;
      amount: number;
      percentage: number;
      user_count: number;
    }>;
    cohort_retention: Array<{
      cohort: string;
      months: Record<string, number>;
    }>;
    forecast: {
      projected_mrr: TimeSeriesPoint[];
      confidence_low: TimeSeriesPoint[];
      confidence_high: TimeSeriesPoint[];
      projected_arr_12m: number;
      projected_growth_percent: number;
    };
  };
}

interface MetricWithChange {
  value: number;
  change_percent: number;
  change_direction: 'up' | 'down' | 'flat';
  period_comparison: string;
}
```

---

## 🎬 Motion Design

```typescript
const revenueAnimations = {
  metricCounter: {
    textContent: { from: 0, to: 'value' },
    transition: { duration: 1, ease: 'easeOut' }
  },
  
  chartDraw: {
    pathLength: [0, 1],
    transition: { duration: 1.5, ease: 'easeInOut' }
  },
  
  cohortCell: {
    opacity: [0, 1],
    transition: { duration: 0.3, delay: 'stagger' }
  }
};
```

---

## ⌨️ Keyboard Shortcuts

```typescript
const revenueShortcuts = {
  'r': 'Refresh data',
  'e': 'Export report',
  '1': 'View 30 days',
  '2': 'View 90 days',
  '3': 'View 12 months',
};
```

---

*Document Version: 1.0*  
*Last Updated: December 2, 2025*  
*Module: Revenue Analytics*
