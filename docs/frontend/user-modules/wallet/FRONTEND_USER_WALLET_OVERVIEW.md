# Module: Wallet Overview

**Route**: `/wallet`
**Auth Required**: Yes
**Package**: `user/wallet`

## 1. Overview
Aggregated view of all user assets defined by the Portfolio service.

## 2. API Contract

### Primary Data Source (Balances)
**Endpoint**: `GET /api/v1/user/portfolio/me`
*Ref: Home Dashboard Documentation for full schema.*

### Wallet Management (Account Selection)
**Endpoint**: `GET /api/v1/wallet/me`
**Response Body (`MyWalletsResponseModel`)**
| Field | Type | Description |
|---|---|---|
| `user_id` | `integer` | |
| `privy_connected` | `boolean` | True if Privy syncing works |
| `primary_wallet_address` | `string` | |
| `wallets` | `Array<Wallet>` | |

**Wallet Object (`WalletResponseModel`)**:
| Field | Type | Description |
|---|---|---|
| `wallet_id` | `string` | |
| `address` | `string` | |
| `chain_type` | `string` | "ethereum", "solana" |
| `wallet_type` | `string` | "embedded", "external" |
| `source` | `string` | "privy", "local" |

### Sync Wallets
**Endpoint**: `POST /api/v1/wallet/sync`
**Body (`SyncWalletsRequest`)**:
```json
{
  "wallets": [
    {
      "address": "0x123...",
      "chain_type": "ethereum",
      "wallet_type": "embedded"
    }
  ]
}
```

## 3. Implementation Flow

1.  **Mount**:
    - Fetch `GET /wallet/me`.
    - If `privy_connected` is false, try to sync from `privy.wallets` via `POST /sync`.
    - Fetch `GET /portfolio/me` using the `primary_wallet_address`.
2.  **Network Filter**:
    - Filter the `portfolio.tokens` list client-side or re-fetch portfolio with `?chain=base`.
