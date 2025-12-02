# FRONTEND_ADMIN_BILLING_PAYMENTS

## Admin Payment Methods Module

**User Type:** Admin  
**Module:** Payment Methods  
**Route:** `/admin/billing/payments`  
**Access Level:** Read (Finance+) | Manage (Admin+)

---

## 📋 Module Overview

### Title
**Payment Methods** - Payment Configuration & Processing

### Description
Management of supported payment methods including traditional cards, crypto payments, and payment processor integrations.

### Key Capabilities
- Payment method configuration
- Processor integration status
- Transaction monitoring
- Failed payment recovery
- Crypto payment settings
- Fee management

---

## 🖼️ Views & Wireframes

### View 1: Payment Methods Dashboard

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│  💳 Payment Methods                                                 [⚙️ Settings]   │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                      │
│  ┌─ Payment Volume (30d) ──────────────────────────────────────────────────────────┐│
│  │                                                                                  ││
│  │  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────┐ ││
│  │  │ 💳 $127,450     │  │ 🪙 $23,400      │  │ 📊 94.2%        │  │ 💸 $3,245   │ ││
│  │  │    Card Volume  │  │    Crypto Volume│  │    Success Rate │  │    Fees     │ ││
│  │  └─────────────────┘  └─────────────────┘  └─────────────────┘  └─────────────┘ ││
│  │                                                                                  ││
│  └─────────────────────────────────────────────────────────────────────────────────┘│
│                                                                                      │
│  PAYMENT PROCESSORS                                                                 │
│  ┌─────────────────────────────────────────────────────────────────────────────────┐│
│  │                                                                                  ││
│  │  ┌───────────────────────────────────────────────────────────────────────────┐  ││
│  │  │ 💳 STRIPE                                                    🟢 Connected │  ││
│  │  │                                                                           │  ││
│  │  │ Volume: $127,450 (30d) │ Transactions: 2,456 │ Success: 94.2%            │  ││
│  │  │ Fees: 2.9% + $0.30 │ Total Fees: $3,245                                  │  ││
│  │  │                                                                           │  ││
│  │  │ Supported: Visa, Mastercard, Amex, Discover                              │  ││
│  │  │ Last Payout: Nov 30 ($45,230) │ Next Payout: Dec 2 (~$32,100)            │  ││
│  │  │                                                                           │  ││
│  │  │ [View Transactions] [Configure] [Test Mode]                              │  ││
│  │  │                                                                           │  ││
│  │  └───────────────────────────────────────────────────────────────────────────┘  ││
│  │                                                                                  ││
│  │  ┌───────────────────────────────────────────────────────────────────────────┐  ││
│  │  │ 🪙 CRYPTO PAYMENTS                                           🟢 Enabled  │  ││
│  │  │                                                                           │  ││
│  │  │ Volume: $23,400 (30d) │ Transactions: 312 │ Success: 99.1%               │  ││
│  │  │ Fees: 1.0% │ Total Fees: $234                                            │  ││
│  │  │                                                                           │  ││
│  │  │ Supported: ETH, USDC, USDT, DAI                                          │  ││
│  │  │ Chains: Ethereum, Arbitrum, Polygon, Base                                │  ││
│  │  │                                                                           │  ││
│  │  │ [View Transactions] [Configure] [Add Token]                              │  ││
│  │  │                                                                           │  ││
│  │  └───────────────────────────────────────────────────────────────────────────┘  ││
│  │                                                                                  ││
│  └─────────────────────────────────────────────────────────────────────────────────┘│
│                                                                                      │
│  PAYMENT METHOD BREAKDOWN                     FAILED PAYMENT RECOVERY              │
│  ┌────────────────────────────────────┐      ┌────────────────────────────────────┐ │
│  │                                    │      │                                    │ │
│  │  💳 Credit Card    ████████   72%  │      │  ❌ Failed Payments: 156           │ │
│  │  🪙 USDC          ████       18%  │      │  🔄 Recovery Attempts: 89          │ │
│  │  Ξ  ETH           ██          6%  │      │  ✅ Recovered: 67 ($4,230)         │ │
│  │  💵 Other Crypto  █           4%  │      │  📧 Dunning Emails Sent: 234       │ │
│  │                                    │      │                                    │ │
│  │                                    │      │  [View Failed Payments]            │ │
│  │                                    │      │  [Configure Dunning]               │ │
│  │                                    │      │                                    │ │
│  └────────────────────────────────────┘      └────────────────────────────────────┘ │
│                                                                                      │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 🔌 API Endpoints

```typescript
// GET /admin/billing/payments
interface GetPaymentMethodsResponse {
  success: true;
  data: {
    volume_30d: {
      card: number;
      crypto: number;
      success_rate: number;
      total_fees: number;
    };
    processors: PaymentProcessor[];
    method_breakdown: Record<string, number>;
    failed_recovery: {
      failed_count: number;
      recovery_attempts: number;
      recovered_count: number;
      recovered_amount: number;
      dunning_sent: number;
    };
  };
}

interface PaymentProcessor {
  id: string;
  name: string;
  type: 'card' | 'crypto' | 'bank';
  status: 'connected' | 'disconnected' | 'error';
  volume_30d: number;
  transaction_count: number;
  success_rate: number;
  fee_structure: string;
  total_fees: number;
  supported_methods: string[];
  last_payout?: {
    date: string;
    amount: number;
  };
  next_payout?: {
    date: string;
    estimated_amount: number;
  };
}

// POST /admin/billing/payments/processors/{id}/configure
interface ConfigureProcessorRequest {
  enabled: boolean;
  test_mode?: boolean;
  api_key?: string;
  webhook_secret?: string;
}
```

---

*Document Version: 1.0*  
*Last Updated: December 2, 2025*  
*Module: Payment Methods*
