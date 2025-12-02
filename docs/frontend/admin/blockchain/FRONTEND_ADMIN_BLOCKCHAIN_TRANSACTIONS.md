# FRONTEND_ADMIN_BLOCKCHAIN_TRANSACTIONS

## Admin Transaction Monitor Module

**User Type:** Admin  
**Module:** Transaction Monitor  
**Route:** `/admin/blockchain/transactions`  
**Access Level:** Read (All) | Manage (Admin+)

---

## 📋 Module Overview

### Title
**Transaction Monitor** - On-Chain Activity Tracking

### Description
Real-time monitoring of all on-chain transactions executed through the Anvil platform. Track swaps, lending operations, bridges, and other DeFi activities across supported chains.

### Key Capabilities
- Real-time transaction feed
- Multi-chain monitoring
- Transaction status tracking
- Gas optimization insights
- Failed transaction analysis
- Volume and trends analytics

---

## 🖼️ Views & Wireframes

### View 1: Transaction Monitor

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│  ⛓️ Transaction Monitor                                         [📊 Analytics]      │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                      │
│  ┌─ Live Stats ────────────────────────────────────────────────────────────────────┐│
│  │                                                                                  ││
│  │  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────┐ ││
│  │  │ 📊 2,456        │  │ 💰 $1.2M        │  │ ✅ 98.2%        │  │ ⛽ $2.45    │ ││
│  │  │    Transactions │  │    Volume (24h) │  │    Success Rate │  │    Avg Gas  │ ││
│  │  │    +156 (1h)    │  │    +$45K (1h)   │  │                 │  │             │ ││
│  │  └─────────────────┘  └─────────────────┘  └─────────────────┘  └─────────────┘ ││
│  │                                                                                  ││
│  └─────────────────────────────────────────────────────────────────────────────────┘│
│                                                                                      │
│  ┌─ Filters ───────────────────────────────────────────────────────────────────────┐│
│  │ Chain: [All ▼]  Type: [All ▼]  Status: [All ▼]  Amount: [All ▼]  [🔍 Search]  ││
│  └─────────────────────────────────────────────────────────────────────────────────┘│
│                                                                                      │
│  ┌─────────────────────────────────────────────────────────────────────────────────┐│
│  │ TIME     │ TYPE  │ CHAIN    │ USER           │ DETAILS          │ AMOUNT│STATUS││
│  ├──────────┼───────┼──────────┼────────────────┼──────────────────┼───────┼──────┤│
│  │ 14:32:45 │ 🔄 Swap│ Arbitrum │ 0x7a23...8f4d │ ETH → USDC       │ $2,890│ ✅   ││
│  │          │       │          │                │ via 1inch        │       │      ││
│  ├──────────┼───────┼──────────┼────────────────┼──────────────────┼───────┼──────┤│
│  │ 14:32:12 │ 📥 Sup│ Ethereum │ 0x9b45...2c1e │ 5,000 USDC       │ $5,000│ ✅   ││
│  │          │       │          │                │ to Aave          │       │      ││
│  ├──────────┼───────┼──────────┼────────────────┼──────────────────┼───────┼──────┤│
│  │ 14:31:58 │ 🔄 Swap│ Polygon  │ 0x3c67...9a2b │ MATIC → USDT     │ $450  │ ⏳   ││
│  │          │       │          │                │ Pending confirm  │       │      ││
│  ├──────────┼───────┼──────────┼────────────────┼──────────────────┼───────┼──────┤│
│  │ 14:31:30 │ 📤 Bor│ Ethereum │ 0x1d89...4e5f │ 2,500 USDC       │ $2,500│ ✅   ││
│  │          │       │          │                │ from Aave        │       │      ││
│  ├──────────┼───────┼──────────┼────────────────┼──────────────────┼───────┼──────┤│
│  │ 14:30:45 │ 🌉 Bri│ ETH→ARB  │ 0x5e2f...7b3c │ 2 ETH bridged    │ $4,500│ ❌   ││
│  │          │       │          │                │ Failed: Low gas  │       │      ││
│  ├──────────┼───────┼──────────┼────────────────┼──────────────────┼───────┼──────┤│
│  │ 14:30:12 │ 🥩 Stk│ Ethereum │ 0x8a1b...3d4e │ 10 ETH staked    │$22,500│ ✅   ││
│  │          │       │          │                │ to Lido          │       │      ││
│  └──────────┴───────┴──────────┴────────────────┴──────────────────┴───────┴──────┘│
│                                                                                      │
│  ● Live updating (4.2 tx/min)                                    [Load More]        │
│                                                                                      │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

### View 2: Transaction Detail

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│  ⛓️ Transaction: 0x3f8a...7b2c                                              [✕]     │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                      │
│  TRANSACTION DETAILS                                                                │
│  ┌───────────────────────────────────────────────────────────────────────────────┐  │
│  │                                                                               │  │
│  │  Status: ✅ Success                                                          │  │
│  │  Type: Swap │ Chain: Arbitrum │ Protocol: 1inch                              │  │
│  │                                                                               │  │
│  │  ┌─────────────────────────────────────────────────────────────────────────┐  │  │
│  │  │  INPUT                           OUTPUT                                 │  │  │
│  │  │  1.5 ETH                   →     2,890.45 USDC                         │  │  │
│  │  │  $2,892.30                       $2,890.45                              │  │  │
│  │  └─────────────────────────────────────────────────────────────────────────┘  │  │
│  │                                                                               │  │
│  │  Price Impact: 0.06% │ Slippage: 0.12% │ Route: ETH → WETH → USDC          │  │
│  │                                                                               │  │
│  └───────────────────────────────────────────────────────────────────────────────┘  │
│                                                                                      │
│  USER & WALLET                                                                      │
│  ┌───────────────────────────────────────────────────────────────────────────────┐  │
│  │                                                                               │  │
│  │  User: alice@defi.co                                                         │  │
│  │  Wallet: 0x7a23b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1                         │  │
│  │  [View User Profile →]                                                       │  │
│  │                                                                               │  │
│  └───────────────────────────────────────────────────────────────────────────────┘  │
│                                                                                      │
│  GAS & TIMING                                                                       │
│  ┌───────────────────────────────────────────────────────────────────────────────┐  │
│  │                                                                               │  │
│  │  Gas Used: 185,432 │ Gas Price: 0.15 gwei │ Gas Cost: $0.42                 │  │
│  │  Block: 142,567,890 │ Timestamp: Dec 1, 14:32:45 UTC                         │  │
│  │  Confirmation Time: 12 seconds                                                │  │
│  │                                                                               │  │
│  └───────────────────────────────────────────────────────────────────────────────┘  │
│                                                                                      │
│  ─────────────────────────────────────────────────────────────────────────────────  │
│                                                                                      │
│  [View on Arbiscan ↗]                                                    [Close]    │
│                                                                                      │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 🔌 API Endpoints

### Get Transactions

```typescript
// GET /admin/blockchain/transactions
interface GetTransactionsResponse {
  success: true;
  data: {
    transactions: BlockchainTransaction[];
    stats: {
      total_24h: number;
      volume_24h_usd: number;
      success_rate: number;
      avg_gas_usd: number;
    };
    pagination: Pagination;
  };
}

interface BlockchainTransaction {
  id: string;
  tx_hash: string;
  type: 'swap' | 'supply' | 'borrow' | 'repay' | 'withdraw' | 'bridge' | 'stake' | 'unstake';
  chain: string;
  protocol: string;
  user_id: string;
  wallet_address: string;
  status: 'pending' | 'success' | 'failed';
  amount_usd: number;
  input: { token: string; amount: string; value_usd: number };
  output?: { token: string; amount: string; value_usd: number };
  gas_used?: number;
  gas_price_gwei?: number;
  gas_cost_usd?: number;
  block_number?: number;
  timestamp: string;
  error_message?: string;
}
```

---

*Document Version: 1.0*  
*Last Updated: December 1, 2025*  
*Module: Transaction Monitor*
