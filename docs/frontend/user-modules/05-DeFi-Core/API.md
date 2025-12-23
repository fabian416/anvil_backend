# DeFi Core API Documentation

> **Complete API Documentation**  
> **Methodology**: CTO Engineering Framework (First Principles + Design Thinking + Systems Thinking)  
> **Base URL**: `/api/v1/defi/aave` and `/api/v1/defi/curve`

---

## 📋 Table of Contents

1. [Aave Lending Endpoints](#aave-lending-endpoints)
2. [Curve Swap Endpoints](#curve-swap-endpoints)
3. [Morpho Lending Endpoints](#morpho-lending-endpoints)
4. [Axelar Bridge Endpoints](#axelar-bridge-endpoints)
5. [LayerZero Cross-Chain Endpoints](#layerzero-cross-chain-endpoints)
6. [Hyperliquid Perpetuals Endpoints](#hyperliquid-perpetuals-endpoints)
7. [Request/Response Schemas](#requestresponse-schemas)
8. [Error Handling](#error-handling)

---

## 🔌 Aave Lending Endpoints

### 1. Get Aave Markets

**Method**: `GET`  
**Endpoint**: `/api/v1/defi/aave/markets`  
**Auth Required**: Yes (Bearer Token)

#### Request

##### Query Parameters
| Parameter | Type | Required | Description | Default |
|----------|------|----------|-------------|---------|
| `asset` | `string` | No | Filter by asset symbol | All assets |
| `chain` | `string` | No | Blockchain | `ethereum` |
| `sort_by` | `string` | No | Sort field | `supply_apy` |
| `limit` | `number` | No | Max results | `50` |

**Valid Chain Values**: `ethereum`, `polygon`, `arbitrum`, `optimism`, `avalanche`, `base`  
**Valid Sort Values**: `supply_apy`, `borrow_apy`, `tvl`, `utilization`

#### Response

##### Success Response (200 OK)
```typescript
interface AaveMarketsResponse {
  markets: AaveMarket[];
  count: number;
  chain: string;
  total_supplied_usd: string;
  total_borrowed_usd: string;
}

interface AaveMarket {
  asset_address: string;
  symbol: string;
  name: string;
  chain: string;
  supply_apy: string;            // Decimal (e.g., "0.052" = 5.2%)
  total_supplied: string;
  total_supplied_usd: string;
  borrow_apy_variable: string;
  borrow_apy_stable: string;
  total_borrowed: string;
  total_borrowed_usd: string;
  utilization_rate: string;      // Percentage (e.g., "0.45" = 45%)
  liquidity_available: string;
  ltv: string;                    // Loan-to-value (e.g., "0.80" = 80%)
  liquidation_threshold: string;
  liquidation_bonus: string;
  is_active: boolean;
  can_use_as_collateral: boolean;
  can_borrow: boolean;
  price_usd: string;
}
```

**JSON Example**:
```json
{
  "markets": [
    {
      "asset_address": "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
      "symbol": "USDC",
      "name": "USD Coin",
      "chain": "ethereum",
      "supply_apy": "0.052",
      "total_supplied": "1000000000",
      "total_supplied_usd": "1000000000",
      "borrow_apy_variable": "0.04",
      "borrow_apy_stable": "0.06",
      "total_borrowed": "450000000",
      "total_borrowed_usd": "450000000",
      "utilization_rate": "0.45",
      "liquidity_available": "550000000",
      "ltv": "0.80",
      "liquidation_threshold": "0.85",
      "liquidation_bonus": "0.05",
      "is_active": true,
      "can_use_as_collateral": true,
      "can_borrow": true,
      "price_usd": "1.00"
    }
  ],
  "count": 1,
  "chain": "ethereum",
  "total_supplied_usd": "5000000000",
  "total_borrowed_usd": "2250000000"
}
```

##### Error Responses

| Status | Error Code | Description | UI Behavior |
|--------|------------|-------------|-------------|
| `400` | `UnsupportedChainError` | Invalid chain parameter | Reset to default chain, show error toast |
| `404` | `MarketNotFoundError` | Asset not listed | Show error: "Asset not available on this chain" |
| `502` | `AaveAPIError` | Aave API unavailable | Show error: "Aave service temporarily unavailable" + Retry |
| `500` | `AaveError` | Internal error | Show error: "Failed to load markets" + Retry |

---

### 2. Get Market Details

**Method**: `GET`  
**Endpoint**: `/api/v1/defi/aave/markets/{asset}`  
**Auth Required**: Yes (Bearer Token)

#### Request

##### Path Parameters
| Parameter | Type | Required | Description |
|----------|------|----------|-------------|
| `asset` | `string` | Yes | Asset symbol (e.g., "USDC") |

##### Query Parameters
| Parameter | Type | Required | Description | Default |
|----------|------|----------|-------------|---------|
| `chain` | `string` | No | Blockchain | `ethereum` |

#### Response

##### Success Response (200 OK)
Returns `AaveMarket` (single market object)

##### Error Responses

| Status | Error Code | Description | UI Behavior |
|--------|------------|-------------|-------------|
| `404` | `MarketNotFoundError` | Asset not found | Show error: "Market not found" |
| `502` | `AaveAPIError` | Aave API unavailable | Show error + Retry |

---

### 3. Get User Position

**Method**: `GET`  
**Endpoint**: `/api/v1/defi/aave/positions/{user_address}`  
**Auth Required**: Yes (Bearer Token)

#### Request

##### Path Parameters
| Parameter | Type | Required | Description |
|----------|------|----------|-------------|
| `user_address` | `string` | Yes | User wallet address (0x...) |

##### Query Parameters
| Parameter | Type | Required | Description | Default |
|----------|------|----------|-------------|---------|
| `chain` | `string` | No | Blockchain | `ethereum` |

#### Response

##### Success Response (200 OK)
```typescript
interface AavePositionResponse {
  user_address: string;
  chain: string;
  total_collateral_usd: string;
  total_debt_usd: string;
  available_borrow_usd: string;
  net_worth_usd: string;
  health_factor: string;         // "∞" if no debt
  current_ltv: string;
  is_healthy: boolean;
  is_at_risk: boolean;           // True if 1 < HF < 1.5
  is_liquidatable: boolean;      // True if HF < 1
  supplies: AaveSupplyPosition[];
  borrows: AaveBorrowPosition[];
}

interface AaveSupplyPosition {
  asset_address: string;
  symbol: string;
  balance: string;
  balance_usd: string;
  apy: string;
  is_collateral: boolean;
}

interface AaveBorrowPosition {
  asset_address: string;
  symbol: string;
  balance: string;
  balance_usd: string;
  apy: string;
  borrow_type: string;           // "variable" or "stable"
}
```

**JSON Example**:
```json
{
  "user_address": "0x1234567890abcdef1234567890abcdef12345678",
  "chain": "ethereum",
  "total_collateral_usd": "3000.00",
  "total_debt_usd": "1200.00",
  "available_borrow_usd": "1275.00",
  "net_worth_usd": "1800.00",
  "health_factor": "2.0625",
  "current_ltv": "0.40",
  "is_healthy": true,
  "is_at_risk": false,
  "is_liquidatable": false,
  "supplies": [
    {
      "asset_address": "0x...",
      "symbol": "ETH",
      "balance": "1.5",
      "balance_usd": "3000.00",
      "apy": "0.03",
      "is_collateral": true
    }
  ],
  "borrows": [
    {
      "asset_address": "0x...",
      "symbol": "USDC",
      "balance": "1200.00",
      "balance_usd": "1200.00",
      "apy": "0.04",
      "borrow_type": "variable"
    }
  ]
}
```

##### Error Responses

| Status | Error Code | Description | UI Behavior |
|--------|------------|-------------|-------------|
| `400` | `InvalidAddressError` | Invalid user address | Show error: "Invalid wallet address" |
| `404` | `PositionNotFoundError` | User has no position | Show empty state: "No active positions" |
| `502` | `AaveAPIError` | Aave API unavailable | Show error: "Unable to load position" + Retry |

---

### 4. Get Health Factor

**Method**: `GET`  
**Endpoint**: `/api/v1/defi/aave/positions/{user_address}/health`  
**Auth Required**: Yes (Bearer Token)

#### Response

##### Success Response (200 OK)
```typescript
interface HealthFactorResponse {
  value: string;                  // "∞" if no debt
  collateral_usd: string;
  debt_usd: string;
  risk_level: string;             // "safe" | "moderate" | "high" | "critical" | "liquidatable"
  is_liquidatable: boolean;
  distance_to_liquidation: string; // Percentage above threshold
  max_withdrawable_pct: string;
  max_borrowable_pct: string;
}
```

---

### 5. Calculate Health Factor (Simulation)

**Method**: `POST`  
**Endpoint**: `/api/v1/defi/aave/calculate/health-factor`  
**Auth Required**: Yes (Bearer Token)

#### Request

##### Request Body
```typescript
interface CalculateHealthFactorRequest {
  collateral_usd: number;         // Required: > 0
  debt_usd: number;               // Required: >= 0
  liquidation_threshold?: number; // Optional: Default 0.825 (82.5%)
}
```

**Request Schema**:
| Field | Type | Required | Description | Validation |
|-------|------|----------|-------------|------------|
| `collateral_usd` | `number` | **Yes** | Total collateral in USD | > 0 |
| `debt_usd` | `number` | **Yes** | Total debt in USD | >= 0 |
| `liquidation_threshold` | `number` | No | Liquidation threshold | 0 < value <= 1, default 0.825 |

#### Response

##### Success Response (200 OK)
Returns `HealthFactorResponse` (same as GET /health)

---

### 6. Get Available to Borrow

**Method**: `GET`  
**Endpoint**: `/api/v1/defi/aave/positions/{user_address}/borrow-capacity/{asset}`  
**Auth Required**: Yes (Bearer Token)

#### Request

##### Path Parameters
| Parameter | Type | Required | Description |
|----------|------|----------|-------------|
| `user_address` | `string` | Yes | User wallet address |
| `asset` | `string` | Yes | Asset symbol (e.g., "USDC") |

##### Query Parameters
| Parameter | Type | Required | Description | Default |
|----------|------|----------|-------------|---------|
| `chain` | `string` | No | Blockchain | `ethereum` |

#### Response

##### Success Response (200 OK)
```typescript
interface AvailableToBorrowResponse {
  asset: string;
  chain: string;
  max_borrowable: string;
  max_borrowable_usd: string;
  current_debt: string;
  collateral_usd: string;
  health_factor_after_max_borrow: string;
}
```

**JSON Example**:
```json
{
  "asset": "USDC",
  "chain": "ethereum",
  "max_borrowable": "1000.00",
  "max_borrowable_usd": "1000.00",
  "current_debt": "0",
  "collateral_usd": "3000.00",
  "health_factor_after_max_borrow": "2.475"
}
```

---

### 7. Get Protocol Stats

**Method**: `GET`  
**Endpoint**: `/api/v1/defi/aave/stats`  
**Auth Required**: Yes (Bearer Token)

#### Response

##### Success Response (200 OK)
```typescript
interface ProtocolStatsResponse {
  chain: string;
  total_tvl_usd: string;
  total_supplied_usd: string;
  total_borrowed_usd: string;
  num_markets: number;
}
```

---

## 🔌 Curve Swap Endpoints

### 8. Get Swap Quote

**Method**: `POST`  
**Endpoint**: `/api/v1/defi/curve/quote`  
**Auth Required**: Yes (Bearer Token)

#### Request

##### Request Body
```typescript
interface SwapQuoteRequest {
  from_token: string;             // Required: Token address or symbol
  to_token: string;               // Required: Token address or symbol
  amount: string;                 // Required: Amount in smallest unit (wei)
  chain: string;                  // Required: Blockchain name
}
```

**Request Schema**:
| Field | Type | Required | Description | Validation |
|-------|------|----------|-------------|------------|
| `from_token` | `string` | **Yes** | Source token address or symbol | Valid address or symbol |
| `to_token` | `string` | **Yes** | Destination token address or symbol | Valid address or symbol |
| `amount` | `string` | **Yes** | Amount in smallest unit | Valid number string |
| `chain` | `string` | **Yes** | Blockchain name | Valid chain name |

**JSON Example**:
```json
{
  "from_token": "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
  "to_token": "0xdAC17F958D2ee523a2206206994597C13D831ec7",
  "amount": "1000000000",
  "chain": "ethereum"
}
```

#### Response

##### Success Response (200 OK)
```typescript
interface SwapQuoteResponse {
  from_token: string;
  to_token: string;
  amount_in: string;
  amount_out: string;
  price_impact: string;           // Percentage (e.g., "0.5" = 0.5%)
  route: SwapRoute[];
  gas_estimate: string;
  risk_warnings: string[];
  min_amount_out: string;         // For slippage protection
}

interface SwapRoute {
  pool_address: string;
  pool_name: string;
  token_in: string;
  token_out: string;
}
```

**JSON Example**:
```json
{
  "from_token": "USDC",
  "to_token": "USDT",
  "amount_in": "1000000000",
  "amount_out": "999500000",
  "price_impact": "0.05",
  "route": [
    {
      "pool_address": "0x...",
      "pool_name": "3pool",
      "token_in": "USDC",
      "token_out": "USDT"
    }
  ],
  "gas_estimate": "150000",
  "risk_warnings": [],
  "min_amount_out": "995000000"
}
```

##### Error Responses

| Status | Error Code | Description | UI Behavior |
|--------|------------|-------------|-------------|
| `400` | `InvalidTokenError` | Invalid token | Show error: "Invalid token" |
| `400` | `NoRouteFoundError` | No swap route found | Show error: "No swap route available" |
| `404` | `PoolNotFoundError` | Pool not found | Show error: "Pool not available" |
| `502` | `CurveAPIError` | Curve API unavailable | Show error: "Swap service unavailable" + Retry |

---

### 9. Get Curve Pools

**Method**: `GET`  
**Endpoint**: `/api/v1/defi/curve/pools`  
**Auth Required**: Yes (Bearer Token)

#### Request

##### Query Parameters
| Parameter | Type | Required | Description | Default |
|----------|------|----------|-------------|---------|
| `chain` | `string` | No | Blockchain | `ethereum` |
| `sort_by` | `string` | No | Sort field | `tvl` |
| `limit` | `number` | No | Max results | `50` |
| `min_tvl` | `number` | No | Minimum TVL filter (USD) | None |

**Valid Sort Values**: `tvl`, `apy`, `volume`

#### Response

##### Success Response (200 OK)
```typescript
interface PoolsResponse {
  pools: Pool[];
  count: number;
  chain: string;
}

interface Pool {
  id: string;
  name: string;
  address: string;
  chain: string;
  tvl_usd: number;
  apy: number;
  volume_24h_usd: number;
  tokens: string[];
}
```

---

## 🔌 Morpho Lending Endpoints

### 10. Get Morpho Vaults

**Method**: `GET`  
**Endpoint**: `/api/v1/defi/morpho/vaults`  
**Auth Required**: Yes (Bearer Token)

#### Request

##### Query Parameters
| Parameter | Type | Required | Description | Default |
|----------|------|----------|-------------|---------|
| `asset` | `string` | No | Filter by asset | All assets |
| `risk_tier` | `string` | No | Filter by risk tier | All tiers |
| `min_apy` | `number` | No | Minimum APY filter | None |
| `sort_by` | `string` | No | Sort field | `apy` |
| `chain` | `string` | No | Blockchain | `ethereum` |
| `limit` | `number` | No | Max results | `50` |

**Valid Risk Tiers**: `low`, `medium`, `high`, `very_high`  
**Valid Sort Values**: `apy`, `tvl`, `risk`

#### Response

##### Success Response (200 OK)
```typescript
interface MorphoVaultsResponse {
  vaults: MorphoVault[];
  top_opportunities: VaultOpportunity[];
  total_count: number;
}

interface MorphoVault {
  vault_address: string;
  vault_name: string;
  asset: string;
  apy: string;
  tvl: string;
  risk_tier: string;
  chain: string;
}
```

---

### 11. Get Morpho Markets

**Method**: `GET`  
**Endpoint**: `/api/v1/defi/morpho/markets`  
**Auth Required**: Yes (Bearer Token)

#### Request

##### Query Parameters
| Parameter | Type | Required | Description | Default |
|----------|------|----------|-------------|---------|
| `collateral_asset` | `string` | No | Filter by collateral asset | All |
| `loan_asset` | `string` | No | Filter by loan asset | All |
| `sort_by` | `string` | No | Sort field | `supply_apy` |
| `chain` | `string` | No | Blockchain | `ethereum` |
| `limit` | `number` | No | Max results | `50` |

#### Response

##### Success Response (200 OK)
```typescript
interface MorphoMarketsResponse {
  markets: MorphoMarket[];
  count: number;
}

interface MorphoMarket {
  market_id: string;
  collateral_asset: string;
  loan_asset: string;
  supply_apy: string;
  borrow_apy: string;
  tvl: string;
  utilization: string;
}
```

---

## 🔌 Axelar Bridge Endpoints

### 12. Get Bridge Routes

**Method**: `GET`  
**Endpoint**: `/api/v1/defi/axelar/routes`  
**Auth Required**: Yes (Bearer Token)

#### Request

##### Query Parameters
| Parameter | Type | Required | Description |
|----------|------|----------|-------------|
| `source_chain` | `string` | **Yes** | Source chain name |
| `destination_chain` | `string` | **Yes** | Destination chain name |
| `token` | `string` | No | Token to bridge | `USDC` |

#### Response

##### Success Response (200 OK)
```typescript
interface BridgeRoutesResponse {
  routes: BridgeRoute[];
  count: number;
}

interface BridgeRoute {
  source_chain: string;
  destination_chain: string;
  token: string;
  route_type: string;             // "standard" | "express"
  estimated_time: number;          // Minutes
  fee_percentage: string;
}
```

---

### 13. Estimate Transfer

**Method**: `GET`  
**Endpoint**: `/api/v1/defi/axelar/estimate`  
**Auth Required**: Yes (Bearer Token)

#### Request

##### Query Parameters
| Parameter | Type | Required | Description |
|----------|------|----------|-------------|
| `source_chain` | `string` | **Yes** | Source chain |
| `destination_chain` | `string` | **Yes** | Destination chain |
| `token` | `string` | **Yes** | Token symbol |
| `amount` | `string` | **Yes** | Amount to bridge |
| `include_express` | `boolean` | No | Include express estimate | `true` |

#### Response

##### Success Response (200 OK)
```typescript
interface TransferEstimateResponse {
  standard: TransferEstimate;
  express?: TransferEstimate;
  recommendation: string;          // "standard" | "express"
}

interface TransferEstimate {
  fee_usd: string;
  fee_percentage: string;
  estimated_time_minutes: number;
  route: string[];
}
```

---

### 14. Track Transfer

**Method**: `GET`  
**Endpoint**: `/api/v1/defi/axelar/transfer/{tx_hash}`  
**Auth Required**: Yes (Bearer Token)

#### Request

##### Path Parameters
| Parameter | Type | Required | Description |
|----------|------|----------|-------------|
| `tx_hash` | `string` | Yes | Source transaction hash |

#### Response

##### Success Response (200 OK)
```typescript
interface TransferTrackingResponse {
  transfer: Transfer;
  progress_pct: number;            // 0-100
  next_step: string;
  estimated_completion: string | null; // ISO 8601
}

interface Transfer {
  tx_hash: string;
  source_chain: string;
  destination_chain: string;
  status: string;                 // "pending" | "in_progress" | "completed" | "failed"
  amount: string;
  token: string;
}
```

---

## 🔌 LayerZero Cross-Chain Endpoints

### 15. Track Message

**Method**: `GET`  
**Endpoint**: `/api/v1/defi/layerzero/message/{tx_hash}`  
**Auth Required**: Yes (Bearer Token)

#### Request

##### Path Parameters
| Parameter | Type | Required | Description |
|----------|------|----------|-------------|
| `tx_hash` | `string` | Yes | Source transaction hash |

#### Response

##### Success Response (200 OK)
```typescript
interface MessageTrackingResponse {
  message: LZMessage;
  progress_pct: number;            // 0-100
  estimated_completion: string | null; // ISO 8601
}

interface LZMessage {
  src_tx_hash: string;
  dst_tx_hash: string | null;
  src_chain: string;
  dst_chain: string;
  status: string;                 // "INFLIGHT" | "DELIVERED" | "FAILED"
}
```

---

### 16. Get Message History

**Method**: `GET`  
**Endpoint**: `/api/v1/defi/layerzero/messages/{address}`  
**Auth Required**: Yes (Bearer Token)

#### Request

##### Path Parameters
| Parameter | Type | Required | Description |
|----------|------|----------|-------------|
| `address` | `string` | Yes | Wallet address |

##### Query Parameters
| Parameter | Type | Required | Description | Default |
|----------|------|----------|-------------|---------|
| `limit` | `number` | No | Max results | `50` |
| `status_filter` | `string` | No | Filter by status | All |

#### Response

##### Success Response (200 OK)
```typescript
interface MessageHistoryResponse {
  messages: LZMessage[];
  total_count: number;
  pending_count: number;
  delivered_count: number;
}
```

---

## 🔌 Hyperliquid Perpetuals Endpoints

### 17. Get Perpetual Markets

**Method**: `GET`  
**Endpoint**: `/api/v1/defi/hyperliquid/markets`  
**Auth Required**: Yes (Bearer Token)

#### Request

##### Query Parameters
| Parameter | Type | Required | Description | Default |
|----------|------|----------|-------------|---------|
| `sort_by` | `string` | No | Sort field | `volume` |
| `limit` | `number` | No | Max results | `50` |

**Valid Sort Values**: `volume`, `open_interest`, `funding`, `price_change`

#### Response

##### Success Response (200 OK)
```typescript
interface PerpetualMarketsResponse {
  markets: PerpetualMarket[];
  count: number;
}

interface PerpetualMarket {
  symbol: string;
  price: string;
  volume_24h: number;
  open_interest: number;
  funding_rate: string;
  price_change_24h: number;
}
```

---

### 18. Get Funding Rates

**Method**: `GET`  
**Endpoint**: `/api/v1/defi/hyperliquid/funding`  
**Auth Required**: Yes (Bearer Token)

#### Request

##### Query Parameters
| Parameter | Type | Required | Description | Default |
|----------|------|----------|-------------|---------|
| `sort_by` | `string` | No | Sort field | `absolute` |
| `min_rate` | `number` | No | Minimum absolute rate | None |

**Valid Sort Values**: `absolute`, `positive`, `negative`

#### Response

##### Success Response (200 OK)
```typescript
interface FundingRatesResponse {
  rates: FundingRate[];
  opportunities: FundingOpportunity[];
  count: number;
}

interface FundingRate {
  symbol: string;
  rate: string;                   // Funding rate (e.g., "0.0001" = 0.01%)
  annualized: string;             // Annualized rate
}

interface FundingOpportunity {
  symbol: string;
  rate: string;
  annualized_return: string;
  direction: string;              // "long" | "short"
  strategy: string;               // Strategy description
}
```

---

### 19. Get Positions

**Method**: `GET`  
**Endpoint**: `/api/v1/defi/hyperliquid/positions/{address}`  
**Auth Required**: Yes (Bearer Token)

#### Request

##### Path Parameters
| Parameter | Type | Required | Description |
|----------|------|----------|-------------|
| `address` | `string` | Yes | User wallet address |

#### Response

##### Success Response (200 OK)
```typescript
interface PositionsResponse {
  positions: PerpetualPosition[];
  summary: PositionsSummary;
}

interface PerpetualPosition {
  symbol: string;
  side: string;                   // "long" | "short"
  size: string;
  entry_price: string;
  mark_price: string;
  pnl: string;
  pnl_percentage: string;
  leverage: number;
  liquidation_price: string;
}

interface PositionsSummary {
  total_pnl: string;
  total_pnl_percentage: string;
  total_notional: string;
  total_collateral: string;
}
```

---

## 📊 Error Handling Summary

### Common Error Patterns

1. **Authentication Errors (401)**
   - Invalid or expired token
   - **Action**: Refresh token, if fails → redirect to login

2. **Validation Errors (400)**
   - Invalid request data
   - **Action**: Show inline field errors

3. **Not Found Errors (404)**
   - Market, position, or pool not found
   - **Action**: Show error message

4. **Service Unavailable (502/503)**
   - External API (Aave, Curve) unavailable
   - **Action**: Show error message + Retry button

### Error Response Format

```json
{
  "detail": "Error message description"
}
```

---

## 🔗 Related Documentation

- **Backend Controller**: `src/app/presentation/http/controllers/defi/aave_router.py`
- **Backend Controller**: `src/app/presentation/http/controllers/defi/curve_router.py`
- **Backend Schemas**: `src/app/presentation/http/controllers/defi/aave_schemas.py`
- **Backend Schemas**: `src/app/presentation/http/controllers/defi/curve_schemas.py`
- **Domain Entities**: `src/app/domain/entities/lending/aave_market.py`
- **Application Interactors**: `src/app/application/commands/curve/get_swap_quote.py`
- **Frontend Implementation**: `05-DeFi-Core/IMPLEMENTATION.md`

---

**Last Updated**: 2024-01-01  
**API Version**: v1  
**Status**: Production Ready
