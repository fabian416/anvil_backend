# FRONTEND_USER_TRANSACTIONS_HISTORY

> **Enterprise Grade Specification**
> Version: 2.0.0
> Status: **Live**
> Source Validation: `src/app/presentation/http/controllers/transaction/router.py`

## 1. Module Overview
The **Transactions History** module tracks on-chain activity.
*   **Logging**: The frontend reports transactions immediately after signing (via Privy).
*   **History**: The backend serves a paginated list of unified history.

**Base URL**: `/api/v1/user/transactions`

---

## 2. Endpoints

### 2.1 Log Transaction
**POST** `/api/v1/user/transactions`

Report a transaction to the backend.

**Request Body (`LogTransactionRequest`):**
| Field | Type | Required | Description |
| :--- | :--- | :--- | :--- |
| `tx_hash` | `string` | **Yes** | 66-char hex string. |
| `chain_id` | `int` | **Yes** | E.g., `1` (Mainnet). |
| `from_address` | `string` | **Yes** | User wallet. |
| `to_address` | `string` | No | Null for contract deploy. |
| `value` | `string` | **Yes** | Value in wei. |
| `tx_type` | `string` | No | `send`, `swap`, `approve`. |
| `asset_symbol` | `string` | No | E.g., `USDC`. |

**Response (201 Created):**
```json
{
  "id": 123,
  "tx_hash": "0x...",
  "status": "pending",
  "created_at": "..."
}
```

### 2.2 Get History
**GET** `/api/v1/user/transactions`

**Query Params**:
*   `limit` (default 50)
*   `offset` (default 0)
*   `chain` (optional filter)
*   `status` (optional `pending`, `success`, `failed`)
*   `tx_type` (optional filter)

**Response (200 OK):**
```json
{
  "user_id": 123,
  "transactions": [
    {
      "id": 1,
      "tx_hash": "0x...",
      "type": "swap",
      "chain": "ethereum",
      "status": "success",
      "asset_in": "ETH",
      "amount_in": "1.0",
      "asset_out": "USDC",
      "amount_out": "3000.0",
      "fee_usd": "5.20",
      "explorer_url": "https://etherscan.io/tx/...",
      "confirmed_at": "..."
    }
  ],
  "total": 45,
  "limit": 50,
  "offset": 0
}
```

---

## 3. Error Handling

| Status | Code | Meaning |
| :--- | :--- | :--- |
| 400 | `WALLET_NOT_FOUND` | User does not own this wallet. |
| 503 | `DATA_MAPPER_ERROR` | Database unavailable. |
