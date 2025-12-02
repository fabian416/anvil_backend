# FRONTEND_ADMIN_BILLING_SUBSCRIPTIONS

## Admin Subscriptions Module

**User Type:** Admin  
**Module:** Subscriptions  
**Route:** `/admin/billing/subscriptions`  
**Access Level:** Read (Finance+) | Manage (Admin+)

---

## 📋 Module Overview

### Title
**Subscriptions** - Plan & Subscription Management

### Description
Management interface for user subscriptions, plan configurations, upgrade/downgrade processing, and subscription lifecycle management.

### Key Capabilities
- View all subscriptions
- Plan management
- Upgrade/downgrade processing
- Cancellation handling
- Trial management
- Proration calculations

---

## 🖼️ Views & Wireframes

### View 1: Subscriptions List

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│  💳 Subscriptions                                        [⚙️ Plans] [+ Add]         │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                      │
│  ┌─ Summary ───────────────────────────────────────────────────────────────────────┐│
│  │  💳 2,847 Active    🆕 156 New (30d)    📉 67 Canceled (30d)    🔄 234 Renewals ││
│  └─────────────────────────────────────────────────────────────────────────────────┘│
│                                                                                      │
│  Plan: [All ▼]  Status: [All ▼]  Billing: [All ▼]  [🔍 Search user...]             │
│                                                                                      │
│  ┌─────────────────────────────────────────────────────────────────────────────────┐│
│  │ USER              │ PLAN      │ STATUS  │ BILLING │ NEXT RENEWAL│ MRR   │      ││
│  ├───────────────────┼───────────┼─────────┼─────────┼─────────────┼───────┼──────┤│
│  │ alice@defi.co     │ 💎 Elite  │ 🟢 Active│ Monthly │ Dec 15      │ $79   │ [•••]││
│  │ bob@crypto.com    │ ⭐ Pro    │ 🟢 Active│ Annual  │ Mar 28      │ $25   │ [•••]││
│  │ carol@eth.org     │ 💎 Elite  │ 🟡 Trial │ -       │ Dec 8       │ -     │ [•••]││
│  │ dave@web3.io      │ ⭐ Pro    │ 🔴 Cancel│ Monthly │ Dec 20      │ $29   │ [•••]││
│  │ eve@blockchain.io │ 💎 Elite  │ ⚠️ Past  │ Monthly │ Nov 28      │ $79   │ [•••]││
│  └───────────────────┴───────────┴─────────┴─────────┴─────────────┴───────┴──────┘│
│                                                                                      │
│  Showing 1-50 of 2,847                                             [1] [2] ... [57] │
│                                                                                      │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

### View 2: Plan Configuration

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│  ⚙️ Plan Configuration                                                     [✕]      │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                      │
│  AVAILABLE PLANS                                                                    │
│  ┌─────────────────────────────────────────────────────────────────────────────────┐│
│  │                                                                                  ││
│  │  ┌───────────────────┐  ┌───────────────────┐  ┌───────────────────┐            ││
│  │  │ 🆓 FREE           │  │ ⭐ PRO             │  │ 💎 ELITE          │            ││
│  │  │                   │  │                   │  │                   │            ││
│  │  │ $0/month          │  │ $29/month         │  │ $79/month         │            ││
│  │  │                   │  │ $290/year (17%↓)  │  │ $790/year (17%↓)  │            ││
│  │  │ • 10 tx/day       │  │ • 100 tx/day      │  │ • Unlimited tx    │            ││
│  │  │ • Basic AI        │  │ • Advanced AI     │  │ • Premium AI      │            ││
│  │  │ • 1 chain         │  │ • 3 chains        │  │ • All chains      │            ││
│  │  │                   │  │ • Priority support│  │ • Dedicated support│           ││
│  │  │ Users: 21,720     │  │ Users: 1,632      │  │ Users: 892        │            ││
│  │  │                   │  │                   │  │                   │            ││
│  │  │ [Edit Plan]       │  │ [Edit Plan]       │  │ [Edit Plan]       │            ││
│  │  │                   │  │                   │  │                   │            ││
│  │  └───────────────────┘  └───────────────────┘  └───────────────────┘            ││
│  │                                                                                  ││
│  └─────────────────────────────────────────────────────────────────────────────────┘│
│                                                                                      │
│  TRIAL SETTINGS                                                                     │
│  ┌───────────────────────────────────────────────────────────────────────────────┐  │
│  │  Trial Duration: [14 days ▼]    Trial Plan: [Elite ▼]    Require Card: [✓]   │  │
│  └───────────────────────────────────────────────────────────────────────────────┘  │
│                                                                                      │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 🔌 API Endpoints

```typescript
// GET /admin/billing/subscriptions
interface GetSubscriptionsResponse {
  success: true;
  data: {
    subscriptions: Subscription[];
    summary: {
      active: number;
      new_30d: number;
      canceled_30d: number;
      renewals_upcoming: number;
    };
    pagination: Pagination;
  };
}

interface Subscription {
  id: string;
  user_id: string;
  email: string;
  plan: 'free' | 'pro' | 'elite';
  status: 'active' | 'trial' | 'canceled' | 'past_due' | 'paused';
  billing_period: 'monthly' | 'annual';
  mrr_contribution: number;
  current_period_start: string;
  current_period_end: string;
  cancel_at_period_end: boolean;
  trial_end?: string;
  created_at: string;
}
```

---

*Document Version: 1.0*  
*Last Updated: December 1, 2025*  
*Module: Subscriptions*
