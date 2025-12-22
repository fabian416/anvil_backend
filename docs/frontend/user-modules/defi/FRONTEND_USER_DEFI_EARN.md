# Module: Earn (Yields)

**Route**: `/defi/earn`
**Auth Required**: Yes
**Package**: `user/defi`

## 1. Overview
Discovery of Yield Opportunities (Curve Pools + Aave Supply).

## 2. API Contract

### Aggregated Yields
*Reuse Home Markets Endpoint for consistency.*
**Endpoint**: `GET /api/v1/user/markets/yields`
**Response**: `List<ProtocolYield>`
- `protocol_name`: "Curve", "Aave".
- `total_apy`: Float.
- `risk_score`: Float.

### Curve Specifics
**Endpoint**: `GET /api/v1/user/defi/curve/pools`
**Response**: `PoolsResponse` (`apy`, `tvl_usd`, `volume_24h_usd`).

## 3. Implementation Flow
1.  **Table**: Sort by APY (Desc).
2.  **Filter**: Chain, Risk Score.
3.  **Deposit**: Redirect to `/defi/supply` (Aave) or `/defi/swap` (Curve LP - simplistic).
