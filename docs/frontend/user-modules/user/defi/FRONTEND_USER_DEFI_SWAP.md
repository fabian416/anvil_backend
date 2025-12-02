# FRONTEND_USER_DEFI_SWAP

## User Swap Module

**User Type:** Authenticated User  
**Module:** Token Swap  
**Route:** `/swap`  
**Platform:** Mobile (React Native) & Web

---

## 📋 Module Overview

### Title
**Swap** - Token Exchange Interface

### Description
Direct interface for swapping tokens using 1inch aggregator, providing best rates across multiple DEXs with slippage protection and gas optimization.

### Key Capabilities
- Token pair selection
- Best rate aggregation (1inch)
- Slippage settings
- Gas price options
- Transaction preview
- Multi-chain support
- Recent swaps history

---

## 🖼️ Views & Wireframes

### View 1: Swap Interface (Mobile)

```
┌─────────────────────────────────────┐
│  [←]         Swap           [⚙️]   │
│                                     │
│  ┌─────────────────────────────────┐│
│  │  You Pay                        ││
│  │  ┌───────────────────────────┐  ││
│  │  │ ┌─────┐                   │  ││
│  │  │ │ Ξ   │ ETH          [▼] │  ││
│  │  │ └─────┘                   │  ││
│  │  │                           │  ││
│  │  │          0.5              │  ││
│  │  │                           │  ││
│  │  │ Balance: 4.52 ETH   [MAX] │  ││
│  │  │ ≈ $1,255.00               │  ││
│  │  └───────────────────────────┘  ││
│  │                                 ││
│  │           ┌───┐                 ││
│  │           │ ↕️ │                 ││
│  │           └───┘                 ││
│  │                                 ││
│  │  You Receive                    ││
│  │  ┌───────────────────────────┐  ││
│  │  │ ┌─────┐                   │  ││
│  │  │ │ $   │ USDC         [▼] │  ││
│  │  │ └─────┘                   │  ││
│  │  │                           │  ││
│  │  │       1,248.50            │  ││
│  │  │                           │  ││
│  │  │ Balance: 12,500 USDC      │  ││
│  │  │ ≈ $1,248.50               │  ││
│  │  └───────────────────────────┘  ││
│  │                                 ││
│  └─────────────────────────────────┘│
│                                     │
│  ┌─────────────────────────────────┐│
│  │  Rate                           ││
│  │  1 ETH = 2,497.00 USDC         ││
│  │                                 ││
│  │  Price Impact        < 0.01%   ││
│  │  Slippage Tolerance     0.5%   ││
│  │  Network Fee           ~$4.50  ││
│  │  Route              via 1inch  ││
│  │                                 ││
│  │  [View Route Details]          ││
│  └─────────────────────────────────┘│
│                                     │
│  ┌─────────────────────────────────┐│
│  │         Review Swap             ││
│  └─────────────────────────────────┘│
│                                     │
├─────────────────────────────────────┤
│  🏠     💼     🤖     📊     👤    │
└─────────────────────────────────────┘
```

### View 2: Token Selector

```
┌─────────────────────────────────────┐
│  [←]    Select Token               │
│                                     │
│  ┌─────────────────────────────────┐│
│  │ [🔍 Search name or paste address]│
│  └─────────────────────────────────┘│
│                                     │
│  Your Tokens                        │
│  ┌─────────────────────────────────┐│
│  │ ┌─────┐                        ││
│  │ │ Ξ   │ ETH         4.52 ETH  ││
│  │ └─────┘             $11,345   ││
│  ├─────────────────────────────────┤│
│  │ ┌─────┐                        ││
│  │ │ $   │ USDC       12,500.00  ││
│  │ └─────┘             $12,500   ││
│  ├─────────────────────────────────┤│
│  │ ┌─────┐                        ││
│  │ │ ◆   │ ARB         5,230.00  ││
│  │ └─────┘              $4,184   ││
│  └─────────────────────────────────┘│
│                                     │
│  Popular Tokens                     │
│  ┌─────────────────────────────────┐│
│  │ ┌─────┐                        ││
│  │ │ ₮   │ USDT                   ││
│  │ └─────┘ Tether USD             ││
│  ├─────────────────────────────────┤│
│  │ ┌─────┐                        ││
│  │ │ ◆   │ WBTC                   ││
│  │ └─────┘ Wrapped Bitcoin        ││
│  ├─────────────────────────────────┤│
│  │ ┌─────┐                        ││
│  │ │ 🔗  │ LINK                   ││
│  │ └─────┘ Chainlink              ││
│  └─────────────────────────────────┘│
│                                     │
└─────────────────────────────────────┘
```

### View 3: Swap Settings

```
┌─────────────────────────────────────┐
│  [←]    Swap Settings              │
│                                     │
│  Slippage Tolerance                 │
│  ┌─────────────────────────────────┐│
│  │  [0.1%]  [0.5%]  [1.0%]  [Custom]│
│  │             ↑                    ││
│  │          Selected               ││
│  │                                 ││
│  │  ⚠️ Your transaction may fail  ││
│  │  if price moves more than this ││
│  └─────────────────────────────────┘│
│                                     │
│  Transaction Deadline               │
│  ┌─────────────────────────────────┐│
│  │  Transaction will revert if     ││
│  │  pending for more than:         ││
│  │                                 ││
│  │  [    20    ] minutes           ││
│  └─────────────────────────────────┘│
│                                     │
│  Gas Price                          │
│  ┌─────────────────────────────────┐│
│  │  [ ] 🐢 Slow      ~$3.20  5min ││
│  │  [●] 🚶 Standard  ~$4.50  2min ││
│  │  [ ] 🏃 Fast      ~$6.80  30s  ││
│  └─────────────────────────────────┘│
│                                     │
│  Expert Mode                        │
│  ┌─────────────────────────────────┐│
│  │  Allow high slippage trades    ││
│  │  and skip confirmation modal   ││
│  │                                 ││
│  │  [○ Off]                  [●]  ││
│  └─────────────────────────────────┘│
│                                     │
└─────────────────────────────────────┘
```

### View 4: Review Swap

```
┌─────────────────────────────────────┐
│  [←]    Review Swap                │
│                                     │
│  ┌─────────────────────────────────┐│
│  │                                 ││
│  │  You Pay                        ││
│  │  ┌─────┐                       ││
│  │  │ Ξ   │ 0.5 ETH              ││
│  │  └─────┘ $1,255.00             ││
│  │                                 ││
│  │           ↓                     ││
│  │                                 ││
│  │  You Receive                    ││
│  │  ┌─────┐                       ││
│  │  │ $   │ 1,248.50 USDC        ││
│  │  └─────┘ $1,248.50             ││
│  │                                 ││
│  └─────────────────────────────────┘│
│                                     │
│  ┌─────────────────────────────────┐│
│  │  Transaction Details            ││
│  │  ─────────────────────────────  ││
│  │  Rate          1 ETH = 2,497 USDC│
│  │  Price Impact           < 0.01% ││
│  │  Min. Received     1,242.26 USDC││
│  │  Network              Ethereum  ││
│  │  Network Fee             $4.50  ││
│  │  Route      Uniswap → 1inch    ││
│  │  ─────────────────────────────  ││
│  │  Total Cost             $1,259.50│
│  └─────────────────────────────────┘│
│                                     │
│  ⚠️ Output is estimated. You will  │
│  receive at least 1,242.26 USDC or │
│  the transaction will revert.      │
│                                     │
│  ┌─────────────────────────────────┐│
│  │         Confirm Swap            ││
│  └─────────────────────────────────┘│
│                                     │
└─────────────────────────────────────┘
```

---

## 🔌 API Endpoints

### Get Swap Quote

```typescript
// POST /api/defi/swap/quote
interface GetSwapQuoteRequest {
  from_token: string;
  to_token: string;
  amount: string;
  chain: string;
  slippage?: number;
}

interface GetSwapQuoteResponse {
  success: true;
  data: {
    quote_id: string;
    from_token: TokenInfo;
    to_token: TokenInfo;
    from_amount: string;
    to_amount: string;
    to_amount_min: string;
    rate: string;
    price_impact: number;
    gas_estimate_usd: number;
    route: SwapRoute[];
    expires_at: string;
  };
}

interface SwapRoute {
  protocol: string;
  from_token: string;
  to_token: string;
  percentage: number;
}
```

### Execute Swap

```typescript
// POST /api/defi/swap/execute
interface ExecuteSwapRequest {
  quote_id: string;
}

interface ExecuteSwapResponse {
  success: true;
  data: {
    transaction_id: string;
    tx_hash: string;
    status: 'pending' | 'submitted';
  };
}
```

---

## 🎬 Motion Design

```typescript
const swapAnimations = {
  switchTokens: {
    rotate: [0, 180],
    transition: { duration: 0.3 }
  },
  
  amountUpdate: {
    opacity: [0.5, 1],
    y: [5, 0],
    transition: { duration: 0.2 }
  },
  
  quoteRefresh: {
    opacity: [0.7, 1],
    transition: { duration: 0.3 }
  },
  
  reviewSlide: {
    y: ['100%', '0%'],
    transition: { duration: 0.3, ease: 'easeOut' }
  }
};
```

---

*Document Version: 1.0*  
*Last Updated: December 2, 2025*  
*Module: Token Swap*
