# Module: Supply (Aave)

**Route**: `/defi/supply`
**Auth Required**: Yes
**Package**: `user/defi`

## 1. Overview
Lending assets on Aave V3.

## 2. API Contract

### Get Markets
**Endpoint**: `GET /api/v1/user/defi/aave/markets`
**Response**: `AaveMarketsResponse` (List of assets with `supply_apy`).

### Get User Position
**Endpoint**: `GET /api/v1/user/defi/aave/position`
**Response**: `AavePositionResponse`
| Field | Type | Description |
|---|---|---|
| `health_factor` | `string` | User Health (> 1.0 is safe) |
| `supplies` | `Array` | Active deposits |

## 3. Implementation Flow
1.  **List**: Show Assets + APY.
2.  **Action**: "Supply" button.
3.  **Tx**: `pool.supply(asset, amount, onBehalfOf, 0)` via Privy.
4.  **Refresh**: Re-fetch `position`.
