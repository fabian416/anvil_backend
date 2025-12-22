# Module: Swap (Curve)

**Route**: `/defi/swap`
**Auth Required**: Yes
**Package**: `user/defi`

## 1. Overview
Token exchange powered by Curve Finance.

## 2. API Contract

### Get Quote
**Endpoint**: `POST /api/v1/user/defi/curve/quote`
**Body (`SwapQuoteRequestModel`)**:
```json
{
  "from_token": "0x...",
  "to_token": "0x...",
  "amount": "1000000000000000000",
  "chain": "ethereum"
}
```
**Response (`SwapQuoteResponse`)**:
| Field | Type | Description |
|---|---|---|
| `amount_out` | `string` | Expected output (wei) |
| `price_impact` | `string` | % Impact |
| `fee_amount` | `string` | Protocol Fee |
| `pool_address` | `string` | The Curve Pool to interact with |

### Execute
**Client-Side**:
1.  Use `pool_address` from Quote.
2.  Call `exchange(i, j, dx, min_dy)` on Curve Contract via Privy.

## 3. Implementation Flow
1.  User enters Amount.
2.  Debounce -> Call `POST /quote`.
3.  Display `amount_out` and `price_impact`.
4.  "Swap" -> Privy Transaction -> `POST /user/transactions` (Log).
