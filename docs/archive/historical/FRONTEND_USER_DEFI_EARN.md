# FRONTEND_USER_DEFI_EARN

## User Earn Overview Module

**User Type:** Authenticated User  
**Module:** Earn Overview  
**Route:** `/earn`  
**Platform:** Mobile (React Native) & Web

---

## 📋 Module Overview

### Title
**Earn** - Yield Opportunities Hub

### Description
Centralized dashboard for all earning opportunities including staking, lending, and liquidity provision with APY comparison and position management.

---

## 🖼️ Views & Wireframes

### View 1: Earn Dashboard

```
┌─────────────────────────────────────┐
│  [←]         Earn           [?]    │
│                                     │
│  ┌─────────────────────────────────┐│
│  │  Your Earnings                  ││
│  │                                 ││
│  │  Total Value        $21,505.00 ││
│  │  Total APY               3.6%  ││
│  │  Earned (All Time)     +$892   ││
│  │                                 ││
│  └─────────────────────────────────┘│
│                                     │
│  [Staking]  [Lending]  [Liquidity] │
│                                     │
│  Your Positions                     │
│  ┌─────────────────────────────────┐│
│  │ 🥩 ETH Staking (Lido)          ││
│  │    2.5 stETH ($6,275)          ││
│  │    3.8% APY   +$47 earned      ││
│  │                      [Manage]  ││
│  ├─────────────────────────────────┤│
│  │ 🏦 USDC Supply (Aave)          ││
│  │    10,000 USDC ($10,000)       ││
│  │    4.2% APY   +$35 earned      ││
│  │                      [Manage]  ││
│  ├─────────────────────────────────┤│
│  │ 🏦 ETH Supply (Aave)           ││
│  │    2.1 ETH ($5,230)            ││
│  │    2.1% APY   +$12 earned      ││
│  │                      [Manage]  ││
│  └─────────────────────────────────┘│
│                                     │
│  Opportunities                      │
│  ┌─────────────────────────────────┐│
│  │ TOKEN      TYPE      APY       ││
│  ├─────────────────────────────────┤│
│  │ DAI       Supply     4.5%      ││
│  │                      [Deposit] ││
│  ├─────────────────────────────────┤│
│  │ USDT      Supply     4.1%      ││
│  │                      [Deposit] ││
│  ├─────────────────────────────────┤│
│  │ ETH       Stake      3.8%      ││
│  │                      [Stake]   ││
│  └─────────────────────────────────┘│
│                                     │
├─────────────────────────────────────┤
│  🏠     💼     🤖     📊     👤    │
└─────────────────────────────────────┘
```

---

## 🔌 API Endpoints

```typescript
// GET /api/defi/earn/overview
interface GetEarnOverviewResponse {
  success: true;
  data: {
    summary: {
      total_value_usd: number;
      avg_apy: number;
      total_earned_usd: number;
    };
    positions: Array<{
      id: string;
      type: 'stake' | 'supply' | 'liquidity';
      protocol: string;
      token: TokenInfo;
      amount: string;
      value_usd: number;
      apy: number;
      earned_usd: number;
    }>;
    opportunities: Array<{
      token: TokenInfo;
      type: 'stake' | 'supply' | 'liquidity';
      protocol: string;
      apy: number;
      tvl_usd: number;
    }>;
  };
}
```

---

*Document Version: 1.0*  
*Last Updated: December 2, 2025*  
*Module: Earn Overview*
