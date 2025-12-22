# Module: Send Crypto

**Route**: `/wallet/send`
**Auth Required**: Yes
**Package**: `user/wallet`

## 1. Overview
Transfers assets. **Execution is Client-Side** (Privy), but **History is Server-Logged**.

## 2. API Contract

### Step 1: Execute (Client-Side)
Use `privy.wallets[0].sendTransaction(request)`.

### Step 2: Log Transaction (Backend)
**Endpoint**: `POST /api/v1/user/transactions`
**Body (`LogTransactionRequest`)**:
| Field | Type | Required | Description |
|---|---|---|---|
| `tx_hash` | `string` | **Yes** | 66 chars (0x...) |
| `from_address` | `string` | **Yes** | |
| `to_address` | `string` | No | Null for contract creation |
| `value` | `string` | **Yes** | Wei amount (as string) |
| `chain_id` | `integer` | **Yes** | |
| `tx_type` | `string` | No | Default "send" |
| `asset_symbol` | `string` | No | "ETH", "USDC" |

**JSON Example**:
```json
{
  "tx_hash": "0xabc...",
  "from_address": "0x123...",
  "to_address": "0x456...",
  "value": "1000000000000000000",
  "chain_id": 8453,
  "tx_type": "send",
  "asset_symbol": "ETH"
}
```

## 3. Implementation Flow
1.  **Draft**: User inputs Amount/Address.
2.  **Sign**: Privy prompts wallet signature.
3.  **Broadcast**: Wallet returns `txHash`.
4.  **Log**: Frontend immediately calls `POST /user/transactions` to ensure history appears in the app.
5.  **Redirect**: To Receipt/History page.
