# FRONTEND_USER_HOME_MARKETS

## User Markets Module

**User Type:** Authenticated User  
**Module:** Markets  
**Route:** `/markets`  
**Platform:** Mobile (React Native) & Web

---

## 📋 Module Overview

### Title
**Markets** - Token Prices & Trends

### Description
Market overview showing token prices, trends, and market data across supported chains.

---

## 🖼️ Views & Wireframes

### View 1: Markets Screen

```
┌─────────────────────────────────────┐
│  [←]       Markets          [🔍]   │
│                                     │
│  ┌─────────────────────────────────┐│
│  │ [Trending] [Top Gainers] [Losers]│
│  └─────────────────────────────────┘│
│                                     │
│  Trending                           │
│  ┌─────────────────────────────────┐│
│  │ ┌─────┐ ETH                     ││
│  │ │ Ξ   │ Ethereum       $2,510  ││
│  │ └─────┘        ↑ 2.4%   [View] ││
│  ├─────────────────────────────────┤│
│  │ ┌─────┐ BTC                     ││
│  │ │ ₿   │ Bitcoin       $43,250  ││
│  │ └─────┘        ↑ 1.8%   [View] ││
│  ├─────────────────────────────────┤│
│  │ ┌─────┐ ARB                     ││
│  │ │ ◆   │ Arbitrum         $0.80 ││
│  │ └─────┘        ↑ 5.2%   [View] ││
│  ├─────────────────────────────────┤│
│  │ ┌─────┐ MATIC                   ││
│  │ │ ◆   │ Polygon          $0.85 ││
│  │ └─────┘        ↓ 1.2%   [View] ││
│  ├─────────────────────────────────┤│
│  │ ┌─────┐ LINK                    ││
│  │ │ 🔗  │ Chainlink       $14.50 ││
│  │ └─────┘        ↑ 3.8%   [View] ││
│  └─────────────────────────────────┘│
│                                     │
│  DeFi Yields                        │
│  ┌─────────────────────────────────┐│
│  │ 🏦 USDC Supply (Aave)     4.2% ││
│  │ 🥩 ETH Staking (Lido)     3.8% ││
│  │ 💰 DAI Supply (Aave)      4.5% ││
│  └─────────────────────────────────┘│
│                                     │
├─────────────────────────────────────┤
│  🏠     💼     🤖     📊     👤    │
└─────────────────────────────────────┘
```

---

## 🔌 API Endpoints

```typescript
// GET /api/markets
interface GetMarketsResponse {
  success: true;
  data: {
    trending: TokenPrice[];
    top_gainers: TokenPrice[];
    top_losers: TokenPrice[];
    defi_yields: Array<{
      protocol: string;
      asset: string;
      apy: number;
    }>;
  };
}

interface TokenPrice {
  symbol: string;
  name: string;
  logo_url?: string;
  price_usd: number;
  change_24h_percent: number;
  volume_24h_usd: number;
  market_cap_usd: number;
}
```

---

*Document Version: 1.0*  
*Last Updated: December 2, 2025*  
*Module: Markets*
