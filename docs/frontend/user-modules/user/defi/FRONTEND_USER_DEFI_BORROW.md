# FRONTEND_USER_DEFI_BORROW

## User Borrow Module

**User Type:** Authenticated User  
**Module:** Borrow  
**Route:** `/earn/borrow`  
**Platform:** Mobile (React Native) & Web

---

## 📋 Module Overview

### Title
**Borrow** - Collateralized Lending

### Description
Interface for borrowing assets against supplied collateral on Aave, with health factor monitoring and liquidation protection.

### Key Capabilities
- Borrow against collateral
- Health factor monitoring
- Interest rate display
- Repayment interface
- Liquidation warnings
- Borrow limit calculation

---

## 🖼️ Views & Wireframes

### View 1: Borrow Dashboard

```
┌─────────────────────────────────────┐
│  [←]       Borrow           [?]    │
│                                     │
│  ┌─────────────────────────────────┐│
│  │  Your Borrows                   ││
│  │                                 ││
│  │  Total Borrowed      $5,000.00 ││
│  │  Borrow APY               5.8% ││
│  │  Available to Borrow  $7,500   ││
│  │                                 ││
│  │  Health Factor                  ││
│  │  [████████████████░░░░] 1.85   ││
│  │  🟢 Safe                        ││
│  │                                 ││
│  └─────────────────────────────────┘│
│                                     │
│  Your Loans                         │
│  ┌─────────────────────────────────┐│
│  │ ┌─────┐ USDC Loan              ││
│  │ │ $   │ $5,000 borrowed        ││
│  │ └─────┘ 5.8% APY               ││
│  │         Accrued: $12.50        ││
│  │                      [Repay]   ││
│  └─────────────────────────────────┘│
│                                     │
│  Borrow More                        │
│  ┌─────────────────────────────────┐│
│  │ ASSET     BORROW APY   MAX     ││
│  ├─────────────────────────────────┤│
│  │ USDC        5.8%      $7,500   ││
│  │                      [Borrow]  ││
│  ├─────────────────────────────────┤│
│  │ ETH         3.4%      3.0 ETH  ││
│  │                      [Borrow]  ││
│  └─────────────────────────────────┘│
│                                     │
│  ⚠️ Borrowing reduces your health  │
│  factor. Keep it above 1.0 to      │
│  avoid liquidation.                │
│                                     │
└─────────────────────────────────────┘
```

---

## 🔌 API Endpoints

```typescript
// GET /api/defi/borrow/dashboard
interface GetBorrowDashboardResponse {
  success: true;
  data: {
    summary: {
      total_borrowed_usd: number;
      avg_borrow_apy: number;
      available_to_borrow_usd: number;
      health_factor: number;
      health_status: 'safe' | 'moderate' | 'risky' | 'danger';
    };
    loans: BorrowPosition[];
    available_to_borrow: BorrowMarket[];
  };
}

interface BorrowPosition {
  id: string;
  token: TokenInfo;
  protocol: string;
  chain: string;
  borrowed_amount: string;
  borrowed_usd: number;
  apy: number;
  accrued_interest_usd: number;
}

// POST /api/defi/borrow
interface BorrowRequest {
  token: string;
  amount: string;
  chain: string;
}

// POST /api/defi/borrow/{id}/repay
interface RepayRequest {
  amount: string;
  repay_full?: boolean;
}
```

---

*Document Version: 1.0*  
*Last Updated: December 2, 2025*  
*Module: Borrow*
