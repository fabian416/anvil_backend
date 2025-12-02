# FRONTEND_USER_TRANSACTIONS_HISTORY

## User Transaction History Module

**User Type:** Authenticated User  
**Module:** Transaction History  
**Route:** `/transactions`  
**Platform:** Mobile (React Native) & Web

---

## 📋 Module Overview

### Title
**Transaction History** - Activity Log

### Description
Complete history of all user transactions across chains with filtering, search, and detailed transaction information.

### Key Capabilities
- Full transaction history
- Multi-chain support
- Filter by type/chain/status
- Search transactions
- Transaction details
- Export functionality

---

## 🖼️ Views & Wireframes

### View 1: Transaction List

```
┌─────────────────────────────────────┐
│  [←]     Transactions       [📥]   │
│                                     │
│  ┌─────────────────────────────────┐│
│  │ [All Types ▼] [All Chains ▼]   ││
│  │ [🔍 Search...]                  ││
│  └─────────────────────────────────┘│
│                                     │
│  Today                              │
│  ┌─────────────────────────────────┐│
│  │ 🔄 Swap                  10:33 ││
│  │    0.5 ETH → 1,248.50 USDC     ││
│  │    Ethereum        ✅ Success   ││
│  ├─────────────────────────────────┤│
│  │ 💰 Supply                08:15 ││
│  │    500 USDC to Aave            ││
│  │    Ethereum        ✅ Success   ││
│  └─────────────────────────────────┘│
│                                     │
│  Yesterday                          │
│  ┌─────────────────────────────────┐│
│  │ 🌉 Bridge                15:42 ││
│  │    1.0 ETH → Arbitrum          ││
│  │    Ethereum        ✅ Success   ││
│  ├─────────────────────────────────┤│
│  │ 📤 Send                  12:30 ││
│  │    0.2 ETH to 0x8f2a...        ││
│  │    Arbitrum        ✅ Success   ││
│  ├─────────────────────────────────┤│
│  │ 📥 Receive               09:15 ││
│  │    500 USDC from 0x3c67...     ││
│  │    Ethereum        ✅ Success   ││
│  └─────────────────────────────────┘│
│                                     │
│  November 28                        │
│  ┌─────────────────────────────────┐│
│  │ 🔄 Swap                  14:22 ││
│  │    1,000 USDC → 0.4 ETH        ││
│  │    Ethereum        ✅ Success   ││
│  ├─────────────────────────────────┤│
│  │ 🥩 Stake                 10:05 ││
│  │    2.5 ETH → 2.5 stETH         ││
│  │    Ethereum        ✅ Success   ││
│  └─────────────────────────────────┘│
│                                     │
│  [Load More]                        │
│                                     │
└─────────────────────────────────────┘
```

### View 2: Transaction Detail

```
┌─────────────────────────────────────┐
│  [←]   Transaction Detail          │
│                                     │
│  ┌─────────────────────────────────┐│
│  │                                 ││
│  │         ┌───────┐               ││
│  │         │  🔄   │               ││
│  │         └───────┘               ││
│  │                                 ││
│  │            Swap                 ││
│  │        ✅ Success               ││
│  │                                 ││
│  │      December 1, 2025           ││
│  │         10:33 AM                ││
│  │                                 ││
│  └─────────────────────────────────┘│
│                                     │
│  ┌─────────────────────────────────┐│
│  │  From                           ││
│  │  0.5 ETH ($1,255.00)            ││
│  │                                 ││
│  │           ↓                     ││
│  │                                 ││
│  │  To                             ││
│  │  1,248.50 USDC ($1,248.50)      ││
│  └─────────────────────────────────┘│
│                                     │
│  ┌─────────────────────────────────┐│
│  │  Details                        ││
│  │  ─────────────────────────────  ││
│  │  Network          Ethereum     ││
│  │  Protocol         1inch        ││
│  │  Rate      1 ETH = 2,497 USDC  ││
│  │  Gas Fee              $4.32    ││
│  │  ─────────────────────────────  ││
│  │  Transaction Hash               ││
│  │  0x8f2a...4c3d          [Copy] ││
│  │                                 ││
│  │  [View on Etherscan ↗]         ││
│  └─────────────────────────────────┘│
│                                     │
└─────────────────────────────────────┘
```

---

## 🔌 API Endpoints

```typescript
// GET /api/transactions
interface GetTransactionsRequest {
  page?: number;
  page_size?: number;
  type?: 'swap' | 'send' | 'receive' | 'supply' | 'borrow' | 'bridge' | 'stake';
  chain?: string;
  status?: 'pending' | 'success' | 'failed';
  search?: string;
}

interface GetTransactionsResponse {
  success: true;
  data: {
    transactions: Transaction[];
    pagination: Pagination;
  };
}

interface Transaction {
  id: string;
  type: string;
  status: 'pending' | 'success' | 'failed';
  chain: string;
  protocol?: string;
  tx_hash?: string;
  from?: { token: string; amount: string; value_usd: number };
  to?: { token: string; amount: string; value_usd?: number; address?: string };
  gas_fee_usd?: number;
  created_at: string;
  completed_at?: string;
}
```

---

*Document Version: 1.0*  
*Last Updated: December 2, 2025*  
*Module: Transaction History*
