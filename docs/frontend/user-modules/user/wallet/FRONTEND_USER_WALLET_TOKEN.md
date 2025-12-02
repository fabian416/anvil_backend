# FRONTEND_USER_WALLET_TOKEN

## User Token Detail Module

**User Type:** Authenticated User  
**Module:** Token Detail  
**Route:** `/wallet/token/:symbol`  
**Platform:** Mobile (React Native) & Web

---

## 📋 Module Overview

### Title
**Token Detail** - Individual Asset View

### Description
Detailed view of a specific token showing balance, price history, recent transactions, and quick actions for that asset.

### Key Capabilities
- Token balance & value
- Price chart (24h/7d/30d/1y)
- Recent token transactions
- Quick actions (send/swap/stake)
- Token information
- Holdings breakdown by chain

---

## 🖼️ Views & Wireframes

### View 1: Token Detail (Mobile)

```
┌─────────────────────────────────────┐
│  [←]         ETH           [★]     │
│                                     │
│  ┌─────────────────────────────────┐│
│  │         ┌───────┐               ││
│  │         │   Ξ   │               ││
│  │         └───────┘               ││
│  │                                 ││
│  │         4.52 ETH                ││
│  │        $11,345.80               ││
│  │                                 ││
│  │    ↑ $267.45 (+2.4%) today     ││
│  │                                 ││
│  └─────────────────────────────────┘│
│                                     │
│  ┌───────┐ ┌───────┐ ┌───────┐     │
│  │  📤   │ │  🔄   │ │  📥   │     │
│  │ Send  │ │ Swap  │ │Receive│     │
│  └───────┘ └───────┘ └───────┘     │
│                                     │
│  Price Chart                        │
│  [24H] [7D] [30D] [1Y]             │
│  ┌─────────────────────────────────┐│
│  │ $2,550 ┤          ╭────        ││
│  │        │    ╭─────╯            ││
│  │ $2,500 ┤────╯                  ││
│  │        │                       ││
│  │ $2,450 ┼─────────────────────▶ ││
│  │                                 ││
│  │  High: $2,567  Low: $2,445     ││
│  └─────────────────────────────────┘│
│                                     │
│  Holdings by Chain                  │
│  ┌─────────────────────────────────┐│
│  │ ◆ Ethereum      3.2 ETH $8,032 ││
│  │ ◆ Arbitrum      1.1 ETH $2,761 ││
│  │ ◆ Base          0.22 ETH $552  ││
│  └─────────────────────────────────┘│
│                                     │
│  Recent Transactions                │
│  ┌─────────────────────────────────┐│
│  │ 📤 Sent             2 hours ago││
│  │    -0.5 ETH to 0x8f2a...       ││
│  ├─────────────────────────────────┤│
│  │ 🔄 Swapped         Yesterday   ││
│  │    +0.8 ETH from 2,000 USDC    ││
│  ├─────────────────────────────────┤│
│  │ 📥 Received            Nov 28  ││
│  │    +1.0 ETH from 0x3c67...     ││
│  │                                 ││
│  │         [View All →]            ││
│  └─────────────────────────────────┘│
│                                     │
│  About ETH                          │
│  ┌─────────────────────────────────┐│
│  │ Ethereum is a decentralized    ││
│  │ platform for smart contracts...││
│  │                    [Read More] ││
│  └─────────────────────────────────┘│
│                                     │
└─────────────────────────────────────┘
```

---

## 🔌 API Endpoints

### Get Token Detail

```typescript
// GET /api/wallets/tokens/:symbol
interface GetTokenDetailResponse {
  success: true;
  data: {
    token: {
      symbol: string;
      name: string;
      logo_url?: string;
      description?: string;
      website?: string;
      contract_addresses: Record<string, string>;
    };
    balance: {
      total: string;
      total_usd: number;
      by_chain: Array<{
        chain: string;
        balance: string;
        balance_usd: number;
      }>;
    };
    price: {
      current_usd: number;
      change_24h: number;
      change_24h_percent: number;
      high_24h: number;
      low_24h: number;
    };
    chart_data: {
      period: string;
      points: TimeSeriesPoint[];
    };
    recent_transactions: Transaction[];
  };
}
```

---

## 🎬 Motion Design

```typescript
const tokenAnimations = {
  priceUpdate: {
    scale: [1, 1.05, 1],
    color: ['current', 'highlight', 'current'],
    transition: { duration: 0.3 }
  },
  
  chartDraw: {
    pathLength: [0, 1],
    transition: { duration: 1, ease: 'easeInOut' }
  },
  
  holdingBar: {
    width: ['0%', 'percentage%'],
    transition: { duration: 0.5 }
  }
};
```

---

*Document Version: 1.0*  
*Last Updated: December 2, 2025*  
*Module: Token Detail*
