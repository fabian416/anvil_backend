# FRONTEND_ADMIN_BLOCKCHAIN_WALLETS

## Admin Wallet Monitor Module

**User Type:** Admin  
**Module:** Wallet Monitor  
**Route:** `/admin/blockchain/wallets`  
**Access Level:** Read (All) | Manage (Admin+)

---

## 📋 Module Overview

### Title
**Wallet Monitor** - MPC Wallet Management

### Description
Monitoring and management interface for Privy MPC wallets used by platform users. Track wallet health, balances, and operational status across all supported chains.

### Key Capabilities
- MPC wallet status monitoring
- Balance tracking across chains
- Wallet health checks
- Gas funding management
- Wallet recovery tools

---

## 🖼️ Views & Wireframes

### View 1: Wallet Dashboard

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│  👛 Wallet Monitor                                                [⚙️ Settings]     │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                      │
│  ┌─ Wallet Overview ───────────────────────────────────────────────────────────────┐│
│  │                                                                                  ││
│  │  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────┐ ││
│  │  │ 👛 24,567       │  │ 💰 $45.2M       │  │ 🟢 99.8%        │  │ ⚠️ 23       │ ││
│  │  │    Total Wallets│  │    Total Value  │  │    Healthy      │  │    Low Gas  │ ││
│  │  └─────────────────┘  └─────────────────┘  └─────────────────┘  └─────────────┘ ││
│  │                                                                                  ││
│  └─────────────────────────────────────────────────────────────────────────────────┘│
│                                                                                      │
│  MPC SYSTEM STATUS                            CHAIN DISTRIBUTION                    │
│  ┌────────────────────────────────────┐      ┌────────────────────────────────────┐ │
│  │                                    │      │                                    │ │
│  │  Privy MPC: 🟢 Operational        │      │  Ethereum    $25.1M   ████████ 56%│ │
│  │  Last Health Check: 30 sec ago    │      │  Arbitrum    $12.3M   ████     27%│ │
│  │                                    │      │  Polygon     $5.2M    ██       12%│ │
│  │  Key Shards: 3/3 Available        │      │  Base        $2.6M    █         5%│ │
│  │  Recovery: ✅ All backups valid   │      │                                    │ │
│  │                                    │      │                                    │ │
│  │  [Run Health Check] [View Logs]   │      │                                    │ │
│  │                                    │      │                                    │ │
│  └────────────────────────────────────┘      └────────────────────────────────────┘ │
│                                                                                      │
│  WALLETS NEEDING ATTENTION                                                          │
│  ┌─────────────────────────────────────────────────────────────────────────────────┐│
│  │                                                                                  ││
│  │  ⚠️ LOW GAS BALANCE (23 wallets)                                                ││
│  │  ┌───────────────────────────────────────────────────────────────────────────┐  ││
│  │  │ WALLET              │ CHAIN    │ GAS BALANCE │ THRESHOLD │ ACTION        │  ││
│  │  ├─────────────────────┼──────────┼─────────────┼───────────┼───────────────┤  ││
│  │  │ 0x7a23...8f4d       │ Ethereum │ $0.12       │ $1.00     │ [Fund] [Skip] │  ││
│  │  │ 0x9b45...2c1e       │ Arbitrum │ $0.05       │ $0.50     │ [Fund] [Skip] │  ││
│  │  │ 0x3c67...9a2b       │ Polygon  │ $0.02       │ $0.25     │ [Fund] [Skip] │  ││
│  │  └─────────────────────┴──────────┴─────────────┴───────────┴───────────────┘  ││
│  │                                                                                  ││
│  │  [Fund All Low Gas Wallets]                                                     ││
│  │                                                                                  ││
│  └─────────────────────────────────────────────────────────────────────────────────┘│
│                                                                                      │
│  RECENT WALLET ACTIVITY                                                             │
│  ┌─────────────────────────────────────────────────────────────────────────────────┐│
│  │                                                                                  ││
│  │  Today        156 wallets created │ 23 funded │ 0 issues                        ││
│  │  Yesterday    142 wallets created │ 18 funded │ 2 recovery requests             ││
│  │  This Week    892 wallets created │ 156 funded │ 5 issues resolved              ││
│  │                                                                                  ││
│  └─────────────────────────────────────────────────────────────────────────────────┘│
│                                                                                      │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 🔌 API Endpoints

### Get Wallet Dashboard

```typescript
// GET /admin/blockchain/wallets/dashboard
interface GetWalletDashboardResponse {
  success: true;
  data: {
    summary: {
      total_wallets: number;
      total_value_usd: number;
      healthy_percentage: number;
      low_gas_count: number;
    };
    mpc_status: {
      status: 'operational' | 'degraded' | 'down';
      last_health_check: string;
      key_shards_available: number;
      key_shards_total: number;
      recovery_status: 'valid' | 'invalid';
    };
    chain_distribution: Record<string, { value_usd: number; percentage: number }>;
    low_gas_wallets: LowGasWallet[];
    recent_activity: {
      today: { created: number; funded: number; issues: number };
      yesterday: { created: number; funded: number; issues: number };
      week: { created: number; funded: number; issues: number };
    };
  };
}

interface LowGasWallet {
  address: string;
  chain: string;
  gas_balance_usd: number;
  threshold_usd: number;
  user_id: string;
  last_transaction?: string;
}
```

### Fund Wallets

```typescript
// POST /admin/blockchain/wallets/fund
interface FundWalletsRequest {
  wallet_addresses?: string[];
  fund_all_low_gas?: boolean;
  amount_usd?: number;
}
```

---

*Document Version: 1.0*  
*Last Updated: December 1, 2025*  
*Module: Wallet Monitor*
