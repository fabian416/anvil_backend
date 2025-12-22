# Module: Bridge (Axelar)

**Route**: `/defi/bridge`
**Auth Required**: Yes
**Package**: `user/defi`

## 1. Overview
Cross-chain transfers via Axelar Network.

## 2. API Contract

### Estimate
**Endpoint**: `POST /api/v1/user/defi/axelar/quote`
**Body**: `{"source_chain", "destination_chain", "token", "amount"}`
**Response (`TransferEstimateResponse`)**:
| Field | Type | Description |
|---|---|---|
| `standard` | `Object` | { fee_usd, estimated_time_minutes } |
| `express` | `Object?` | Faster option if available |
| `recommendation` | `string` | "STANDARD" or "EXPRESS" |

### Track Transfer
**Endpoint**: `GET /api/v1/user/defi/axelar/transfer/{tx_hash}`
**Response (`TransferTrackingResponse`)**:
| Field | Type | Description |
|---|---|---|
| `status` | `string` | "pending", "executed" |
| `progress_pct` | `integer` | 0-100 |
| `next_step` | `string` | "Waiting for finality on value_source" |

## 3. Implementation Flow
1.  **Quote**: Fetch estimate.
2.  **Send**: Call `axelarGateway.sendToken()` via Privy.
3.  **Log**: Backend tracks automatically via Axelar Scan or manually via `POST /transactions`.
4.  **Poll**: Show progress bar using Tracking endpoint.
