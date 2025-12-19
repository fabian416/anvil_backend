# FRONTEND_USER_WALLET_OVERVIEW

## User Wallet Overview Module

**User Type:** Authenticated User  
**Module:** Wallet Overview  
**Route:** `/wallet`  
**Platform:** Mobile (React Native) & Web

---

## 📋 Module Overview

### Title
**Wallet Overview** - Asset Management Hub

### Description
Comprehensive view of all user assets across connected wallets and chains, with filtering, sorting, and quick access to token actions.

### Key Capabilities
- Multi-wallet view
- Chain filtering
- Asset list with balances
- Token search
- Hide small balances
- Quick send/receive/swap

---

## 🖼️ Views & Wireframes

### View 1: Wallet Overview (Mobile)

```
┌─────────────────────────────────────┐
│  [←]      Wallet           [+ Add] │
│                                     │
│  ┌─────────────────────────────────┐│
│  │                                 ││
│  │       Total Balance             ││
│  │      $45,230.42                 ││
│  │                                 ││
│  │  ┌──────────┐  ┌──────────┐    ││
│  │  │   📤     │  │   📥     │    ││
│  │  │   Send   │  │  Receive │    ││
│  │  └──────────┘  └──────────┘    ││
│  │                                 ││
│  └─────────────────────────────────┘│
│                                     │
│  ┌─────────────────────────────────┐│
│  │ [All Chains ▼]     [🔍 Search] ││
│  └─────────────────────────────────┘│
│                                     │
│  ┌─────────────────────────────────┐│
│  │ [✓] Hide small balances (<$1)  ││
│  └─────────────────────────────────┘│
│                                     │
│  Assets                             │
│  ┌─────────────────────────────────┐│
│  │  ◆ ETH                    [>]  ││
│  │  ┌─────┐                       ││
│  │  │ Ξ   │  4.52 ETH             ││
│  │  └─────┘  $11,345.80           ││
│  │           ↑ 2.4% (24h)         ││
│  ├─────────────────────────────────┤│
│  │  ◆ USDC                   [>]  ││
│  │  ┌─────┐                       ││
│  │  │ $   │  12,500.00 USDC       ││
│  │  └─────┘  $12,500.00           ││
│  │           → 0.0% (24h)         ││
│  ├─────────────────────────────────┤│
│  │  ◆ ARB                    [>]  ││
│  │  ┌─────┐                       ││
│  │  │ ◆   │  5,230 ARB            ││
│  │  └─────┘  $4,184.00            ││
│  │           ↓ 1.2% (24h)         ││
│  ├─────────────────────────────────┤│
│  │  ◆ MATIC                  [>]  ││
│  │  ┌─────┐                       ││
│  │  │ ◆   │  2,500 MATIC          ││
│  │  └─────┘  $2,125.00            ││
│  │           ↑ 3.1% (24h)         ││
│  └─────────────────────────────────┘│
│                                     │
├─────────────────────────────────────┤
│  🏠     💼     🤖     📊     👤    │
└─────────────────────────────────────┘
```

### View 2: Chain Filter Expanded

```
┌─────────────────────────────────────┐
│  [←]      Wallet           [+ Add] │
│                                     │
│  ┌─────────────────────────────────┐│
│  │ Select Chain                    ││
│  │                                 ││
│  │ [●] All Chains      $45,230.42 ││
│  │ [ ] ◆ Ethereum      $25,329.00 ││
│  │ [ ] ◆ Arbitrum      $12,670.00 ││
│  │ [ ] ◆ Polygon        $5,431.00 ││
│  │ [ ] ◆ Base           $1,800.42 ││
│  │                                 ││
│  └─────────────────────────────────┘│
│                                     │
...
```

### View 3: Connected Wallets

```
┌─────────────────────────────────────┐
│  [←]    Connected Wallets          │
│                                     │
│  Your Wallets                       │
│  ┌─────────────────────────────────┐│
│  │  🔐 Anvil Wallet (Primary)      ││
│  │  0x7a23...8f4d                  ││
│  │  $42,450.00            [Copy]  ││
│  │                                 ││
│  │  Created via Privy MPC          ││
│  ├─────────────────────────────────┤│
│  │  🦊 MetaMask                    ││
│  │  0x9b12...4c3e                  ││
│  │  $2,780.42             [Copy]  ││
│  │                                 ││
│  │  Connected Nov 15     [Disconnect]│
│  └─────────────────────────────────┘│
│                                     │
│  ┌─────────────────────────────────┐│
│  │  [+ Connect Another Wallet]     ││
│  └─────────────────────────────────┘│
│                                     │
│                                     │
│  ⚠️ Note: Only your Anvil Wallet   │
│  can be used for AI-assisted       │
│  transactions.                      │
│                                     │
└─────────────────────────────────────┘
```

---

## 🔌 API Endpoints

### Get Wallet Overview

```typescript
// GET /api/wallets
interface GetWalletsResponse {
  success: true;
  data: {
    total_balance_usd: number;
    wallets: Wallet[];
    assets: Asset[];
  };
}

interface Wallet {
  id: string;
  address: string;
  type: 'privy_mpc' | 'external';
  name?: string;
  is_primary: boolean;
  balance_usd: number;
  created_at: string;
  provider?: string;
}

interface Asset {
  token_address: string;
  symbol: string;
  name: string;
  logo_url?: string;
  chain: string;
  balance: string;
  balance_usd: number;
  price_usd: number;
  change_24h_percent: number;
  wallet_address: string;
}
```

### Get Assets by Chain

```typescript
// GET /api/wallets/assets?chain={chain}
interface GetAssetsByChainResponse {
  success: true;
  data: {
    chain: string;
    total_balance_usd: number;
    assets: Asset[];
  };
}
```

---

## 🎬 Motion Design

```typescript
const walletAnimations = {
  balanceReveal: {
    opacity: [0, 1],
    y: [10, 0],
    transition: { duration: 0.5 }
  },
  
  assetItem: {
    x: [-20, 0],
    opacity: [0, 1],
    transition: { duration: 0.3, delay: 'index * 0.05' }
  },
  
  chainFilterExpand: {
    height: ['0', 'auto'],
    opacity: [0, 1],
    transition: { duration: 0.2 }
  },
  
  priceChange: {
    color: 'direction === "up" ? "#10B981" : "#EF4444"',
    transition: { duration: 0.3 }
  }
};
```

---

## 🎨 Component Specifications

```typescript
interface AssetRowProps {
  asset: Asset;
  onPress: () => void;
  showChainBadge?: boolean;
}

interface ChainFilterProps {
  chains: Array<{ id: string; name: string; balance: number }>;
  selected: string;
  onSelect: (chainId: string) => void;
}

interface WalletCardProps {
  wallet: Wallet;
  onCopyAddress: () => void;
  onDisconnect?: () => void;
}
```

---

*Document Version: 1.0*  
*Last Updated: December 2, 2025*  
*Module: Wallet Overview*
