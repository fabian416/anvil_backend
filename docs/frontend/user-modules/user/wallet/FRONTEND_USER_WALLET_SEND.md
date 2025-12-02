# FRONTEND_USER_WALLET_SEND

## User Send Module

**User Type:** Authenticated User  
**Module:** Send  
**Route:** `/wallet/send`  
**Platform:** Mobile (React Native) & Web

---

## 📋 Module Overview

### Title
**Send** - Transfer Tokens

### Description
Interface for sending tokens to other wallets with address validation, recent recipients, and transaction confirmation.

---

## 🖼️ Views & Wireframes

### View 1: Send Screen

```
┌─────────────────────────────────────┐
│  [←]         Send                  │
│                                     │
│  To                                 │
│  ┌─────────────────────────────────┐│
│  │ [Wallet address or ENS... ] [📷]││
│  │                                 ││
│  │ Recent                          ││
│  │ ┌─────────────────────────────┐ ││
│  │ │ 0x8f2a...4c3d    Yesterday │ ││
│  │ │ 0x3c67...9a2b      Nov 28  │ ││
│  │ └─────────────────────────────┘ ││
│  └─────────────────────────────────┘│
│                                     │
│  Asset                              │
│  ┌─────────────────────────────────┐│
│  │ ┌─────┐                        ││
│  │ │ Ξ   │ ETH              [▼]  ││
│  │ └─────┘ Balance: 4.52 ETH      ││
│  └─────────────────────────────────┘│
│                                     │
│  Amount                             │
│  ┌─────────────────────────────────┐│
│  │                                 ││
│  │          0.5                    ││
│  │                                 ││
│  │        ≈ $1,255.00        [MAX] ││
│  │                                 ││
│  └─────────────────────────────────┘│
│                                     │
│  Network                            │
│  ┌─────────────────────────────────┐│
│  │ ◆ Ethereum                  [▼] ││
│  │   Est. fee: ~$2.50              ││
│  └─────────────────────────────────┘│
│                                     │
│  ┌─────────────────────────────────┐│
│  │         Review Send             ││
│  └─────────────────────────────────┘│
│                                     │
└─────────────────────────────────────┘
```

### View 2: Review Send

```
┌─────────────────────────────────────┐
│  [←]     Review Send               │
│                                     │
│  ┌─────────────────────────────────┐│
│  │                                 ││
│  │  Sending                        ││
│  │  ┌─────┐                       ││
│  │  │ Ξ   │ 0.5 ETH              ││
│  │  └─────┘ $1,255.00             ││
│  │                                 ││
│  │           ↓                     ││
│  │                                 ││
│  │  To                             ││
│  │  0x8f2a...4c3d                  ││
│  │                                 ││
│  └─────────────────────────────────┘│
│                                     │
│  ┌─────────────────────────────────┐│
│  │  Network          Ethereum     ││
│  │  Network Fee          $2.50    ││
│  │  ─────────────────────────────  ││
│  │  Total           0.5 ETH       ││
│  │                  + $2.50 fee   ││
│  └─────────────────────────────────┘│
│                                     │
│  ⚠️ Double-check the recipient     │
│  address. Transactions cannot be   │
│  reversed.                          │
│                                     │
│  ┌─────────────────────────────────┐│
│  │       Confirm & Send            ││
│  └─────────────────────────────────┘│
│                                     │
└─────────────────────────────────────┘
```

---

## 🔌 API Endpoints

```typescript
// POST /api/wallet/send
interface SendRequest {
  to_address: string;
  token: string;
  amount: string;
  chain: string;
}

interface SendResponse {
  success: true;
  data: {
    transaction_id: string;
    tx_hash: string;
    status: 'pending' | 'submitted';
  };
}

// GET /api/wallet/send/estimate
interface EstimateSendRequest {
  to_address: string;
  token: string;
  amount: string;
  chain: string;
}

interface EstimateSendResponse {
  success: true;
  data: {
    gas_estimate_usd: number;
    gas_estimate_native: string;
  };
}
```

---

*Document Version: 1.0*  
*Last Updated: December 2, 2025*  
*Module: Send*
