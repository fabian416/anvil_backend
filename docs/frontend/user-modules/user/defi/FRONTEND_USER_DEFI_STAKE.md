# FRONTEND_USER_DEFI_STAKE

## User Stake Module

**User Type:** Authenticated User  
**Module:** Stake  
**Route:** `/earn/stake`  
**Platform:** Mobile (React Native) & Web

---

## 📋 Module Overview

### Title
**Stake** - Liquid Staking

### Description
Interface for staking ETH via Lido to earn staking rewards while maintaining liquidity with stETH.

### Key Capabilities
- ETH staking via Lido
- stETH balance tracking
- APY display
- Reward tracking
- Unstaking flow
- Staking rewards history

---

## 🖼️ Views & Wireframes

### View 1: Stake Dashboard

```
┌─────────────────────────────────────┐
│  [←]        Stake           [?]    │
│                                     │
│  ┌─────────────────────────────────┐│
│  │  ETH Staking via Lido           ││
│  │                                 ││
│  │         ┌───────┐               ││
│  │         │ stETH │               ││
│  │         └───────┘               ││
│  │                                 ││
│  │  Your Staked ETH                ││
│  │  2.5 stETH ($6,275)             ││
│  │                                 ││
│  │  Current APY     3.8%           ││
│  │  Rewards Earned  +0.024 ETH     ││
│  │                  (+$60.24)      ││
│  │                                 ││
│  └─────────────────────────────────┘│
│                                     │
│  ┌─────────────────────────────────┐│
│  │                                 ││
│  │  Amount to Stake                ││
│  │  ┌───────────────────────────┐  ││
│  │  │                           │  ││
│  │  │        1.0                │  ││
│  │  │                           │  ││
│  │  │ Available: 2.02 ETH [MAX] │  ││
│  │  │ ≈ $2,510.00               │  ││
│  │  └───────────────────────────┘  ││
│  │                                 ││
│  │  You will receive               ││
│  │  ~0.998 stETH                   ││
│  │                                 ││
│  └─────────────────────────────────┘│
│                                     │
│  ┌─────────────────────────────────┐│
│  │  APY                      3.8% ││
│  │  Est. Yearly Rewards     $95   ││
│  │  Protocol                Lido  ││
│  └─────────────────────────────────┘│
│                                     │
│  ┌─────────────────────────────────┐│
│  │          Stake ETH              ││
│  └─────────────────────────────────┘│
│                                     │
│  [Unstake stETH →]                  │
│                                     │
└─────────────────────────────────────┘
```

---

## 🔌 API Endpoints

```typescript
// GET /api/defi/stake/dashboard
interface GetStakeDashboardResponse {
  success: true;
  data: {
    staked_position?: {
      staked_amount: string;
      staked_usd: number;
      rewards_earned: string;
      rewards_earned_usd: number;
    };
    current_apy: number;
    steth_rate: number;
    available_to_stake: string;
    available_to_stake_usd: number;
  };
}

// POST /api/defi/stake
interface StakeRequest {
  amount: string;
}

// POST /api/defi/stake/unstake
interface UnstakeRequest {
  amount: string;
}
```

---

*Document Version: 1.0*  
*Last Updated: December 2, 2025*  
*Module: Stake*
