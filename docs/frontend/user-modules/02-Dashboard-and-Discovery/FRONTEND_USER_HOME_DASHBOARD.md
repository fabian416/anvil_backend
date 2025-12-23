# Module: Home Dashboard (Portfolio)

**Route**: `/home`
**Auth Required**: Yes
**Package**: `user/home`

## 1. Overview
Displays the user's aggregated financial status across EVM chains.

## 2. API Contract

### Get Portfolio Summary
**Endpoint**: `GET /api/v1/user/portfolio/me`
**Query Params**:
- `chain` (string, optional): `ethereum`, `base`, `arbitrum`, `polygon`, `optimism`.
- `save_snapshot` (bool, default `false`).

#### Response Body (`PortfolioResponse`)
| Field | Type | Description |
|---|---|---|
| `wallet_address` | `string` | |
| `chain` | `string` | The active chain context |
| `total_usd` | `float` | |
| `native_balance` | `float` | ETH balance |
| `native_usd_value` | `float` | |
| `tokens` | `Array<Token>` | See below |

**Token Object (`TokenHoldingResponse`)**:
| Field | Type | Description |
|---|---|---|
| `symbol` | `string` | "USDC" |
| `name` | `string` | "USD Coin" |
| `amount` | `float` | |
| `usd_value` | `float` | |
| `percentage` | `float` | % of total portfolio |
| `token_address` | `string?` | Null for native ETH |

**JSON Example**:
```json
{
  "wallet_address": "0x123...",
  "chain": "ethereum",
  "total_usd": 12500.50,
  "native_balance": 2.5,
  "tokens": [
    {
      "symbol": "USDC",
      "amount": 5000.0,
      "usd_value": 5000.0,
      "percentage": 40.0
    }
  ]
}
```

### Error Codes
| Status | Description | UI Behavior |
|---|---|---|
| `404` | "No wallets found" | Redirect to Wallet Creation |
| `404` | "No EVM wallets found" | Show "Bitcoin-only wallet not supported yet" |
| `400` | Invalid Chain | Reset Chain Filter to Default |
| `500` | Calculation Failed | Show "Failed to load portfolio" + Retry |

## 3. Implementation Flow

1.  **Mount**: Call `usePortfolio()` hook which fetches `/me`.
2.  **Display**:
    - `total_usd` -> Big Number.
    - `native_balance` -> "2.5 ETH".
    - `tokens` -> Truncated list (Top 3).
