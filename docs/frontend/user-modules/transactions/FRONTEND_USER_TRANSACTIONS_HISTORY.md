# Module: Transaction History

**Route**: `/transactions`
**Auth Required**: Yes
**Package**: `user/transactions`

## 1. Overview
Log of all user activities (Send, Swap, Bridge).

## 2. API Contract

### Get History
**Endpoint**: `GET /api/v1/user/transactions`
**Query**: `limit` (50), `offset` (0), `chain`, `status`, `tx_type`.

#### Response Body (`TransactionHistoryResponse`)
| Field | Type | Description |
|---|---|---|
| `transactions` | `Array` | List of items |
| `total` | `integer` | |

**Transaction Item (`TransactionHistoryItemResponse`)**:
| Field | Type | Description |
|---|---|---|
| `tx_hash` | `string` | |
| `type` | `string` | "send", "swap", "approve" |
| `status` | `string` | "success", "pending", "failed" |
| `asset_in` | `string?` | |
| `amount_in` | `string?` | |
| `asset_out` | `string?` | |
| `amount_out` | `string?` | |
| `fee_usd` | `string?` | |
| `created_at` | `string` | ISO Date |

## 3. Implementation Flow
1.  **Infinite Scroll**: Fetch page 1 -> Wait for bottom -> Fetch page 2.
2.  **Status Polling**: If any item is "pending", poll every 5s until resolved.
