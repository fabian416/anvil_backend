# FRONTEND_USER_SETTINGS_SUBSCRIPTION

## User Subscription Module

**User Type:** Authenticated User  
**Module:** Subscription  
**Route:** `/settings/subscription`  
**Platform:** Mobile (React Native) & Web

---

## 📋 Module Overview

### Title
**Subscription** - Plan Management

### Description
Subscription management for users to view, upgrade, downgrade, or cancel their plan.

---

## 🖼️ Views & Wireframes

### View 1: Current Plan

```
┌─────────────────────────────────────┐
│  [←]     Subscription              │
│                                     │
│  Current Plan                       │
│  ┌─────────────────────────────────┐│
│  │         💎 Elite                ││
│  │                                 ││
│  │  $79/month                      ││
│  │                                 ││
│  │  ✓ Unlimited transactions       ││
│  │  ✓ Premium AI assistant         ││
│  │  ✓ All chains supported         ││
│  │  ✓ Priority support             ││
│  │  ✓ Advanced analytics           ││
│  │                                 ││
│  │  Next billing: Dec 15, 2025     ││
│  │  Payment: Visa •••• 4242        ││
│  │                                 ││
│  └─────────────────────────────────┘│
│                                     │
│  ┌─────────────────────────────────┐│
│  │  [Change Plan]                  ││
│  │  [Update Payment Method]        ││
│  │  [View Billing History]         ││
│  │  [Cancel Subscription]          ││
│  └─────────────────────────────────┘│
│                                     │
└─────────────────────────────────────┘
```

### View 2: Plan Selection

```
┌─────────────────────────────────────┐
│  [←]     Choose Plan               │
│                                     │
│  ┌─────────────────────────────────┐│
│  │  🆓 Free                        ││
│  │  $0/month                       ││
│  │                                 ││
│  │  • 10 transactions/day          ││
│  │  • Basic AI assistant           ││
│  │  • 1 chain (Ethereum)           ││
│  │                                 ││
│  │            [Current]            ││
│  └─────────────────────────────────┘│
│                                     │
│  ┌─────────────────────────────────┐│
│  │  ⭐ Pro                POPULAR  ││
│  │  $29/month                      ││
│  │                                 ││
│  │  • 100 transactions/day         ││
│  │  • Advanced AI assistant        ││
│  │  • 3 chains                     ││
│  │  • Priority support             ││
│  │                                 ││
│  │           [Upgrade]             ││
│  └─────────────────────────────────┘│
│                                     │
│  ┌─────────────────────────────────┐│
│  │  💎 Elite                       ││
│  │  $79/month                      ││
│  │                                 ││
│  │  • Unlimited transactions       ││
│  │  • Premium AI assistant         ││
│  │  • All chains                   ││
│  │  • Dedicated support            ││
│  │  • Advanced analytics           ││
│  │                                 ││
│  │           [Upgrade]             ││
│  └─────────────────────────────────┘│
│                                     │
│  💡 Save 17% with annual billing   │
│                                     │
└─────────────────────────────────────┘
```

---

## 🔌 API Endpoints

```typescript
// GET /api/users/me/subscription
interface GetSubscriptionResponse {
  success: true;
  data: {
    plan: 'free' | 'pro' | 'elite';
    status: 'active' | 'canceled' | 'past_due';
    price: number;
    billing_period: 'monthly' | 'annual';
    next_billing_date?: string;
    cancel_at_period_end?: boolean;
    features: string[];
    payment_method?: {
      type: string;
      last4: string;
    };
  };
}

// POST /api/users/me/subscription/change
interface ChangeSubscriptionRequest {
  plan: 'free' | 'pro' | 'elite';
  billing_period?: 'monthly' | 'annual';
}

// POST /api/users/me/subscription/cancel
interface CancelSubscriptionResponse {
  success: true;
  data: {
    cancel_at_period_end: true;
    end_date: string;
  };
}
```

---

*Document Version: 1.0*  
*Last Updated: December 2, 2025*  
*Module: Subscription*
