# Module: Token Detail

**Route**: `/wallet/token/:symbol`
**Auth Required**: Yes
**Package**: `user/wallet`

## 1. Overview
Deep dive into a specific asset.

## 2. API Contract

### Market Data
**Endpoint**: `GET /api/v1/user/markets/tokens/{symbol}`
**Response**: `TokenMarketData` (Ref: Markets Doc).

### Price History (Chart)
**Endpoint**: `GET /api/v1/user/markets/tokens/{symbol}/history`
**Query**: `timeframe` (1h, 24h, 7d, 30d, 1y).
**Response**: `{"history": Array<{timestamp, price}>}`

### User Balance
**Endpoint**: `GET /api/v1/user/portfolio/me`
*Client-side filtering*: Find token in list where `symbol === :symbol`.

## 3. Implementation Flow
1.  **Parallel Fetch**: `MarketData`, `History`, `Portfolio`.
2.  **Chart Interaction**: Changing pill (e.g., "1W") triggers `history` fetch.
