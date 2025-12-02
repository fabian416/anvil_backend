# FRONTEND_USER_DEFI_SUPPLY

## User Supply/Lend Module

**User Type:** Authenticated User  
**Module:** Supply (Lending)  
**Route:** `/earn/supply`  
**Platform:** Mobile (React Native) & Web

---

## 📋 Module Overview

### Title
**Supply** - Earn Yield by Lending

### Description
Interface for supplying assets to lending protocols like Aave to earn interest, with position management and APY tracking.

### Key Capabilities
- Supply assets to earn APY
- View current positions
- APY comparison
- Withdraw positions
- Health factor monitoring
- Collateral management

---

## 🖼️ Views & Wireframes

### View 1: Supply Markets

```
┌─────────────────────────────────────┐
│  [←]        Earn            [?]    │
│                                     │
│  ┌─────────────────────────────────┐│
│  │  Your Supplies                  ││
│  │                                 ││
│  │  Total Supplied    $15,230.00  ││
│  │  Avg APY                 4.2%  ││
│  │  Earned (All Time)     +$234   ││
│  │                                 ││
│  └─────────────────────────────────┘│
│                                     │
│  Your Positions                     │
│  ┌─────────────────────────────────┐│
│  │ ┌─────┐ USDC on Aave           ││
│  │ │ $   │ $10,000 supplied       ││
│  │ └─────┘ 4.2% APY  +$35 earned  ││
│  │                    [Withdraw]  ││
│  ├─────────────────────────────────┤│
│  │ ┌─────┐ ETH on Aave            ││
│  │ │ Ξ   │ $5,230 supplied        ││
│  │ └─────┘ 2.1% APY  +$12 earned  ││
│  │                    [Withdraw]  ││
│  └─────────────────────────────────┘│
│                                     │
│  Supply More                        │
│  ┌─────────────────────────────────┐│
│  │ ASSET        APY      AVAILABLE ││
│  ├─────────────────────────────────┤│
│  │ USDC        4.2%     2,500.00  ││
│  │                       [Supply] ││
│  ├─────────────────────────────────┤│
│  │ ETH         2.1%         1.52  ││
│  │                       [Supply] ││
│  ├─────────────────────────────────┤│
│  │ DAI         4.5%        500.00 ││
│  │                       [Supply] ││
│  └─────────────────────────────────┘│
│                                     │
└─────────────────────────────────────┘
```

### View 2: Supply Asset

```
┌─────────────────────────────────────┐
│  [←]     Supply USDC               │
│                                     │
│  ┌─────────────────────────────────┐│
│  │                                 ││
│  │  Amount to Supply               ││
│  │  ┌───────────────────────────┐  ││
│  │  │                           │  ││
│  │  │        1,000              │  ││
│  │  │                           │  ││
│  │  │ Balance: 2,500 USDC [MAX] │  ││
│  │  │ ≈ $1,000.00               │  ││
│  │  └───────────────────────────┘  ││
│  │                                 ││
│  └─────────────────────────────────┘│
│                                     │
│  ┌─────────────────────────────────┐│
│  │  Supply APY              4.2%  ││
│  │  Protocol               Aave   ││
│  │  Network            Ethereum   ││
│  │  ─────────────────────────────  ││
│  │  Est. Yearly Earnings    $42   ││
│  │  Est. Monthly Earnings  $3.50  ││
│  └─────────────────────────────────┘│
│                                     │
│  ┌─────────────────────────────────┐│
│  │  [✓] Use as collateral         ││
│  │      Enable borrowing against  ││
│  │      this deposit              ││
│  └─────────────────────────────────┘│
│                                     │
│  ┌─────────────────────────────────┐│
│  │       Confirm Supply            ││
│  └─────────────────────────────────┘│
│                                     │
└─────────────────────────────────────┘
```

---

## 🔌 API Endpoints

```typescript
// GET /api/defi/supply/markets
interface GetSupplyMarketsResponse {
  success: true;
  data: {
    user_summary: {
      total_supplied_usd: number;
      avg_apy: number;
      total_earned_usd: number;
    };
    positions: SupplyPosition[];
    available_markets: SupplyMarket[];
  };
}

interface SupplyPosition {
  id: string;
  token: TokenInfo;
  protocol: string;
  chain: string;
  supplied_amount: string;
  supplied_usd: number;
  apy: number;
  earned_usd: number;
  is_collateral: boolean;
}

interface SupplyMarket {
  token: TokenInfo;
  protocol: string;
  chain: string;
  apy: number;
  total_supplied_usd: number;
  available_balance: string;
  available_balance_usd: number;
}

// POST /api/defi/supply
interface SupplyRequest {
  token: string;
  amount: string;
  chain: string;
  use_as_collateral: boolean;
}
```

---

*Document Version: 1.0*  
*Last Updated: December 2, 2025*  
*Module: Supply/Lend*
