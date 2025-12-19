# FRONTEND_ADMIN_BILLING_INVOICES

## Admin Invoices Module

**User Type:** Admin  
**Module:** Invoices  
**Route:** `/admin/billing/invoices`  
**Access Level:** Read (Finance+) | Manage (Admin+)

---

## 📋 Module Overview

### Title
**Invoices** - Invoice Management & History

### Description
Complete invoice management system for viewing, generating, and managing user invoices, including payment tracking, refunds, and invoice customization.

### Key Capabilities
- Invoice listing & search
- Invoice generation
- Payment status tracking
- Refund processing
- Invoice PDF generation
- Bulk operations

---

## 🖼️ Views & Wireframes

### View 1: Invoices List

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│  🧾 Invoices                                              [+ Generate] [📥 Export]  │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                      │
│  ┌─ Summary (30d) ─────────────────────────────────────────────────────────────────┐│
│  │                                                                                  ││
│  │  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────┐ ││
│  │  │ 🧾 2,456        │  │ 💰 $127,450     │  │ ✅ 94.2%        │  │ ⏳ $7,230    │ ││
│  │  │    Invoices     │  │    Revenue      │  │    Paid Rate    │  │    Outstanding││
│  │  │    This Month   │  │                 │  │                 │  │             │ ││
│  │  └─────────────────┘  └─────────────────┘  └─────────────────┘  └─────────────┘ ││
│  │                                                                                  ││
│  └─────────────────────────────────────────────────────────────────────────────────┘│
│                                                                                      │
│  Status: [All ▼]  Date: [This Month ▼]  Amount: [All ▼]  [🔍 Search invoice...]    │
│                                                                                      │
│  ┌─────────────────────────────────────────────────────────────────────────────────┐│
│  │ INVOICE #     │ USER              │ DATE     │ AMOUNT  │ STATUS  │ ACTIONS    ││
│  ├───────────────┼───────────────────┼──────────┼─────────┼─────────┼────────────┤│
│  │ INV-2024-2456 │ alice@defi.co     │ Dec 1    │ $79.00  │ ✅ Paid │ [👁️] [📄] ││
│  │ INV-2024-2455 │ bob@crypto.com    │ Dec 1    │ $290.00 │ ✅ Paid │ [👁️] [📄] ││
│  │ INV-2024-2454 │ carol@eth.org     │ Nov 30   │ $79.00  │ ⏳ Pending│ [👁️] [📄] ││
│  │ INV-2024-2453 │ dave@web3.io      │ Nov 30   │ $29.00  │ ❌ Failed│ [👁️] [📄] ││
│  │ INV-2024-2452 │ eve@blockchain.io │ Nov 29   │ $79.00  │ 🔄 Refund│ [👁️] [📄] ││
│  │ INV-2024-2451 │ frank@nft.com     │ Nov 29   │ $790.00 │ ✅ Paid │ [👁️] [📄] ││
│  └───────────────┴───────────────────┴──────────┴─────────┴─────────┴────────────┘│
│                                                                                      │
│  Showing 1-50 of 2,456                                             [1] [2] ... [50] │
│                                                                                      │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

### View 2: Invoice Detail

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│  🧾 Invoice INV-2024-2456                                                   [✕]     │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                      │
│  ┌─ Invoice ───────────────────────────────────────────────────────────────────────┐│
│  │                                                                                  ││
│  │  ┌─────────────────────────────────────────────────────────────────────────────┐││
│  │  │                                                                             │││
│  │  │  ANVIL                                          Invoice #: INV-2024-2456   │││
│  │  │  DeFi Intelligence Platform                     Date: December 1, 2025     │││
│  │  │                                                 Due: December 1, 2025      │││
│  │  │                                                 Status: ✅ PAID            │││
│  │  │  ─────────────────────────────────────────────────────────────────────────  │││
│  │  │                                                                             │││
│  │  │  Bill To:                                                                   │││
│  │  │  Alice Johnson                                                              │││
│  │  │  alice@defi.co                                                              │││
│  │  │  123 Main Street                                                            │││
│  │  │  San Francisco, CA 94102                                                    │││
│  │  │                                                                             │││
│  │  │  ─────────────────────────────────────────────────────────────────────────  │││
│  │  │                                                                             │││
│  │  │  DESCRIPTION                                              AMOUNT            │││
│  │  │  ──────────────────────────────────────────────────────────────────────     │││
│  │  │  Elite Plan - Monthly Subscription                        $79.00            │││
│  │  │  Period: Dec 1 - Dec 31, 2025                                               │││
│  │  │                                                                             │││
│  │  │  ──────────────────────────────────────────────────────────────────────     │││
│  │  │                                                 Subtotal:  $79.00           │││
│  │  │                                                 Tax (0%):  $0.00            │││
│  │  │                                                 ────────────────            │││
│  │  │                                                 TOTAL:     $79.00           │││
│  │  │                                                                             │││
│  │  └─────────────────────────────────────────────────────────────────────────────┘││
│  │                                                                                  ││
│  └─────────────────────────────────────────────────────────────────────────────────┘│
│                                                                                      │
│  PAYMENT DETAILS                                                                    │
│  ┌───────────────────────────────────────────────────────────────────────────────┐  │
│  │  Payment Method: Visa •••• 4242                                              │  │
│  │  Payment Date: December 1, 2025 at 10:32 AM                                  │  │
│  │  Transaction ID: ch_3OxHJ2CZ6qsJgndJ0vGF7HKr                                 │  │
│  └───────────────────────────────────────────────────────────────────────────────┘  │
│                                                                                      │
│  ─────────────────────────────────────────────────────────────────────────────────  │
│                                                                                      │
│  [📧 Email Invoice]    [📄 Download PDF]    [🔄 Issue Refund]    [❌ Void Invoice] │
│                                                                                      │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 🔌 API Endpoints

```typescript
// GET /admin/billing/invoices
interface GetInvoicesRequest {
  page?: number;
  page_size?: number;
  status?: 'paid' | 'pending' | 'failed' | 'refunded' | 'void';
  date_from?: string;
  date_to?: string;
  amount_min?: number;
  amount_max?: number;
  search?: string;
}

interface GetInvoicesResponse {
  success: true;
  data: {
    invoices: Invoice[];
    summary: {
      total_invoices: number;
      total_revenue: number;
      paid_rate: number;
      outstanding: number;
    };
    pagination: Pagination;
  };
}

interface Invoice {
  id: string;
  invoice_number: string;
  user_id: string;
  email: string;
  name?: string;
  status: 'paid' | 'pending' | 'failed' | 'refunded' | 'void';
  amount: number;
  currency: string;
  tax: number;
  total: number;
  line_items: Array<{
    description: string;
    amount: number;
    period_start?: string;
    period_end?: string;
  }>;
  billing_address?: {
    line1: string;
    line2?: string;
    city: string;
    state: string;
    postal_code: string;
    country: string;
  };
  payment?: {
    method: string;
    last4?: string;
    transaction_id: string;
    paid_at: string;
  };
  created_at: string;
  due_at: string;
  paid_at?: string;
}

// POST /admin/billing/invoices/{id}/refund
interface RefundInvoiceRequest {
  amount?: number; // partial refund, full if not specified
  reason: string;
}

// POST /admin/billing/invoices/{id}/void
interface VoidInvoiceRequest {
  reason: string;
}

// POST /admin/billing/invoices/{id}/send
interface SendInvoiceRequest {
  email?: string; // override default email
}
```

---

## ⌨️ Keyboard Shortcuts

```typescript
const invoiceShortcuts = {
  'n': 'New invoice',
  'e': 'Export invoices',
  'd': 'Download PDF',
  '/': 'Search invoices',
};
```

---

*Document Version: 1.0*  
*Last Updated: December 2, 2025*  
*Module: Invoices*
