# Module: Borrow (Aave)

**Route**: `/defi/borrow`
**Auth Required**: Yes
**Package**: `user/defi`

## 1. Overview
Borrowing against collateral on Aave V3.

## 2. API Contract

### Get Borrowable Assets
**Endpoint**: `GET /api/v1/user/defi/aave/markets`
*Filter*: `can_borrow === true`.

### Get Health Factor
**Endpoint**: `GET /api/v1/user/defi/aave/position`
*Critical*: Display `health_factor` prominently.

## 3. Implementation Flow
1.  **Safety Check**: Calculate new HF *before* allowing tx.
    - `POST /api/v1/user/defi/aave/health-calc` (if available) or Client-Side Calc.
2.  **Tx**: `pool.borrow(asset, amount, interestRateMode, 0, onBehalfOf)` via Privy.
