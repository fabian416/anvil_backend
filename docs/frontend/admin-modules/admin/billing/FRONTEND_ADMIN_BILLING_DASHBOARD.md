# FRONTEND_ADMIN_BILLING_DASHBOARD

## Admin Billing Dashboard Module

**User Type:** Admin  
**Module:** Billing Dashboard  
**Route:** `/admin/billing`  
**Access Level:** Read (Finance+) | Manage (Admin+)

---

## 📋 Module Overview

### Title
**Billing Dashboard** - Revenue & Financial Overview

### Description
Comprehensive financial dashboard providing visibility into platform revenue, subscription metrics, payment processing, and financial KPIs.

### Key Capabilities
- Revenue tracking (MRR, ARR)
- Subscription analytics
- Payment processing status
- Churn analysis
- Financial reporting
- Revenue forecasting

---

## 🖼️ Views & Wireframes

### View 1: Billing Dashboard

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│  💰 Billing Dashboard                                    [📥 Export] [📊 Reports]   │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                      │
│  ┌─ Key Metrics ───────────────────────────────────────────────────────────────────┐│
│  │                                                                                  ││
│  │  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────┐ ││
│  │  │ 💵 $127,450     │  │ 📈 $1.52M       │  │ 👥 2,847        │  │ 📉 2.3%     │ ││
│  │  │    MRR          │  │    ARR          │  │    Paid Users   │  │    Churn    │ ││
│  │  │    ↑ 12% MoM    │  │    ↑ 18% YoY    │  │    ↑ 156 new    │  │    ↓ 0.5%   │ ││
│  │  └─────────────────┘  └─────────────────┘  └─────────────────┘  └─────────────┘ ││
│  │                                                                                  ││
│  └─────────────────────────────────────────────────────────────────────────────────┘│
│                                                                                      │
│  REVENUE TREND                                                                      │
│  ┌─────────────────────────────────────────────────────────────────────────────────┐│
│  │                                                                                  ││
│  │  $150K ┤                                                      ╭────            ││
│  │        │                                               ╭──────╯                 ││
│  │  $100K ┤                                    ╭──────────╯                        ││
│  │        │                         ╭──────────╯                                   ││
│  │   $50K ┤              ╭──────────╯                                              ││
│  │        │    ──────────╯                                                         ││
│  │     $0 ┼──────────────────────────────────────────────────────────────────▶    ││
│  │         Jun    Jul    Aug    Sep    Oct    Nov    Dec                          ││
│  │                                                                                  ││
│  │  ── MRR    ── New Revenue    ── Churned Revenue                                 ││
│  │                                                                                  ││
│  └─────────────────────────────────────────────────────────────────────────────────┘│
│                                                                                      │
│  REVENUE BY PLAN                              PAYMENT STATUS                        │
│  ┌────────────────────────────────────┐      ┌────────────────────────────────────┐ │
│  │                                    │      │                                    │ │
│  │  💎 Elite    $67,230  ████████ 53% │      │  ✅ Successful   ████████████ 94.2%│ │
│  │              892 users             │      │     2,682 payments                 │ │
│  │                                    │      │                                    │ │
│  │  ⭐ Pro      $48,960  ██████   38% │      │  ⏳ Pending      ██            3.8% │ │
│  │              1,632 users           │      │     108 payments                   │ │
│  │                                    │      │                                    │ │
│  │  🆓 Free+    $11,260  ██       9%  │      │  ❌ Failed       █             2.0% │ │
│  │              323 users             │      │     57 payments                    │ │
│  │                                    │      │                                    │ │
│  └────────────────────────────────────┘      └────────────────────────────────────┘ │
│                                                                                      │
│  RECENT TRANSACTIONS                                                                │
│  ┌─────────────────────────────────────────────────────────────────────────────────┐│
│  │  TIME      │ USER              │ TYPE        │ AMOUNT  │ STATUS │ METHOD      ││
│  ├────────────┼───────────────────┼─────────────┼─────────┼────────┼─────────────┤│
│  │  14:32     │ alice@defi.co     │ Subscription│ $79.00  │ ✅     │ Visa •••4242││
│  │  14:28     │ bob@crypto.com    │ Upgrade     │ $49.00  │ ✅     │ USDC        ││
│  │  14:15     │ carol@eth.org     │ Subscription│ $29.00  │ ❌     │ Visa •••1234││
│  │  13:58     │ dave@web3.io      │ Subscription│ $79.00  │ ✅     │ ETH         ││
│  └────────────┴───────────────────┴─────────────┴─────────┴────────┴─────────────┘│
│                                                                                      │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 🔌 API Endpoints

### Get Billing Dashboard

```typescript
// GET /admin/billing/dashboard
interface GetBillingDashboardResponse {
  success: true;
  data: {
    metrics: {
      mrr: MetricWithChange;
      arr: MetricWithChange;
      paid_users: MetricWithChange;
      churn_rate: MetricWithChange;
    };
    revenue_trend: TimeSeriesPoint[];
    revenue_by_plan: Array<{
      plan: string;
      amount: number;
      users: number;
      percentage: number;
    }>;
    payment_status: {
      successful: { count: number; percentage: number };
      pending: { count: number; percentage: number };
      failed: { count: number; percentage: number };
    };
    recent_transactions: BillingTransaction[];
  };
}

interface BillingTransaction {
  id: string;
  user_id: string;
  email: string;
  type: 'subscription' | 'upgrade' | 'downgrade' | 'refund';
  amount_usd: number;
  status: 'success' | 'pending' | 'failed';
  payment_method: string;
  created_at: string;
}

interface MetricWithChange {
  value: number;
  change_percent: number;
  change_direction: 'up' | 'down' | 'flat';
}
```

---

*Document Version: 1.0*  
*Last Updated: December 1, 2025*  
*Module: Billing Dashboard*
