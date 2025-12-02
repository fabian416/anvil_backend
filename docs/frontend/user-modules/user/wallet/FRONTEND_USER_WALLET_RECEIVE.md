# FRONTEND_USER_WALLET_RECEIVE

## User Receive Module

**User Type:** Authenticated User  
**Module:** Receive  
**Route:** `/wallet/receive`  
**Platform:** Mobile (React Native) & Web

---

## 📋 Module Overview

### Title
**Receive** - Deposit Tokens

### Description
Display wallet address with QR code for receiving tokens, with chain selection and address copying.

---

## 🖼️ Views & Wireframes

### View 1: Receive Screen

```
┌─────────────────────────────────────┐
│  [←]       Receive                 │
│                                     │
│  Select Network                     │
│  ┌─────────────────────────────────┐│
│  │ ◆ Ethereum                  [▼] ││
│  └─────────────────────────────────┘│
│                                     │
│  ┌─────────────────────────────────┐│
│  │                                 ││
│  │    Scan to send tokens         ││
│  │                                 ││
│  │    ┌─────────────────────┐     ││
│  │    │                     │     ││
│  │    │    ▓▓▓▓▓▓▓▓▓▓▓     │     ││
│  │    │    ▓         ▓     │     ││
│  │    │    ▓  QR CODE ▓     │     ││
│  │    │    ▓         ▓     │     ││
│  │    │    ▓▓▓▓▓▓▓▓▓▓▓     │     ││
│  │    │                     │     ││
│  │    └─────────────────────┘     ││
│  │                                 ││
│  │    Your Ethereum Address        ││
│  │                                 ││
│  │  ┌───────────────────────────┐  ││
│  │  │ 0x7a23B8c9D4e5F6a7b8c9   │  ││
│  │  │ d4e5f6a78f4d              │  ││
│  │  └───────────────────────────┘  ││
│  │                                 ││
│  │  [📋 Copy Address]  [📤 Share] ││
│  │                                 ││
│  └─────────────────────────────────┘│
│                                     │
│  ⚠️ Only send ETH or ERC-20 tokens │
│  on Ethereum network to this       │
│  address.                          │
│                                     │
│  Supported Tokens                   │
│  ┌─────────────────────────────────┐│
│  │ ETH  USDC  USDT  DAI  WBTC ... ││
│  └─────────────────────────────────┘│
│                                     │
└─────────────────────────────────────┘
```

---

## 🔌 API Endpoints

```typescript
// GET /api/wallet/address
interface GetWalletAddressResponse {
  success: true;
  data: {
    address: string;
    supported_chains: Array<{
      chain_id: number;
      name: string;
      supported_tokens: string[];
    }>;
  };
}
```

---

*Document Version: 1.0*  
*Last Updated: December 2, 2025*  
*Module: Receive*
