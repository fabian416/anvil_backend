# DeFi Operations Endpoints Specification

> **Last Updated**: 2026-01-25  
> **Status**: Production  
> **Maintainers**: @backend-engineer @error-detective @code-reviewer

---

## Executive Summary

The DeFi Operations module provides comprehensive REST APIs for:
1. **Lending Protocols** - Aave V3, Morpho (MetaMorpho vaults)
2. **Perpetual Trading** - Hyperliquid (markets, positions, funding)
3. **Liquidity Pools** - Curve Finance (pools, gauges, swaps)
4. **Cross-Chain** - LayerZero (messaging), Axelar (bridging)

**Base Path**: `/api/v1`  
**Authentication**: Public endpoints (no authentication required)

---

## 1. Aave V3 Endpoints

**Base Path**: `/api/v1/aave`  
**Tags**: `DeFi`, `Lending`

### GET /aave/markets

Get all Aave V3 lending markets.

**Query Parameters**:
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `asset` | string | No | - | Filter by asset symbol |
| `chain` | string | No | ethereum | Blockchain (ethereum, polygon, arbitrum, optimism, avalanche, base) |
| `sort_by` | string | No | supply_apy | Sort field (supply_apy, borrow_apy, tvl, utilization) |
| `limit` | int | No | 50 | Max results (1-100) |

**Response**:
```json
{
  "markets": [...],
  "count": 50,
  "chain": "ethereum",
  "total_supplied_usd": "15000000000",
  "total_borrowed_usd": "8000000000"
}
```

---

### GET /aave/markets/{asset}

Get detailed market information for a specific asset.

**Path Parameters**:
| Parameter | Type | Description |
|-----------|------|-------------|
| `asset` | string | Asset symbol (e.g., USDC, WETH) |

---

### GET /aave/positions/{user_address}

Get user's complete lending/borrowing position.

**Path Parameters**:
| Parameter | Type | Description |
|-----------|------|-------------|
| `user_address` | string | User's wallet address |

**Response**:
```json
{
  "user_address": "0x...",
  "chain": "ethereum",
  "total_collateral_usd": "10000",
  "total_debt_usd": "5000",
  "health_factor": "1.65",
  "supplies": [...],
  "borrows": [...]
}
```

---

### GET /aave/positions/{user_address}/health

Get user's health factor with risk analysis.

**Response**:
```json
{
  "health_factor": "1.65",
  "risk_level": "MODERATE",
  "liquidation_threshold": "0.825",
  "is_liquidatable": false,
  "recommendations": [...]
}
```

---

### GET /aave/positions/{user_address}/borrow-capacity/{asset}

Get maximum amount user can borrow of an asset.

---

### GET /aave/stats

Get protocol-wide statistics.

---

### POST /aave/calculate/health-factor

Calculate health factor from collateral and debt amounts.

**Request Body**:
```json
{
  "collateral_usd": 10000,
  "debt_usd": 5000,
  "liquidation_threshold": 0.825
}
```

---

### GET /aave/rates/{asset}

Get supply and borrow rates for an asset.

---

## 2. Morpho Endpoints

**Base Path**: `/api/v1/morpho`  
**Tags**: `DeFi`, `Lending`

### GET /morpho/vaults

Get MetaMorpho vaults with APY and risk data.

**Query Parameters**:
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `asset` | string | No | - | Filter by asset |
| `risk_tier` | string | No | - | Filter by risk (low, medium, high, very_high) |
| `min_apy` | float | No | - | Minimum APY filter |
| `sort_by` | string | No | apy | Sort field (apy, tvl, risk) |
| `chain` | string | No | ethereum | Blockchain (ethereum, base) |
| `limit` | int | No | 50 | Max results (1-100) |

---

### GET /morpho/vaults/{vault_address}

Get detailed vault information with market allocations.

---

### GET /morpho/vaults/{vault_address}/apy

Get detailed APY breakdown with historical data.

---

### GET /morpho/markets

Get Morpho Blue lending markets.

---

### GET /morpho/positions/{user_address}

Get user's vault positions with earnings.

---

### GET /morpho/compare

Compare yields across protocols for an asset.

**Query Parameters**:
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `asset` | string | Yes | Asset to compare |
| `chain` | string | No | Blockchain |

---

## 3. Hyperliquid Endpoints

**Base Path**: `/api/v1/hyperliquid`  
**Tags**: `DeFi`, `Perpetuals`

### GET /hyperliquid/markets

Get all perpetual markets with pricing and funding data.

**Query Parameters**:
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `sort_by` | string | volume | Sort (volume, open_interest, funding, price_change) |
| `limit` | int | 50 | Max results (1-200) |

---

### GET /hyperliquid/markets/{symbol}/orderbook

Get real-time order book with spread analysis.

**Query Parameters**:
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `depth` | int | 20 | Book depth (1-100) |

---

### GET /hyperliquid/funding

Get funding rates with arbitrage opportunities.

**Query Parameters**:
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `sort_by` | string | absolute | Sort (absolute, positive, negative) |
| `min_rate` | float | - | Minimum absolute rate filter |

---

### GET /hyperliquid/liquidations

Get recent liquidations with market stress analysis.

**Query Parameters**:
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `symbol` | string | - | Filter by symbol |
| `hours` | int | 24 | Lookback hours (1-168) |
| `sort_by` | string | time | Sort (size, time) |

---

### GET /hyperliquid/positions/{address}

Get user's open positions with risk analysis.

---

### POST /hyperliquid/risk/calculate

Calculate risk metrics for a potential position.

**Request Body**:
```json
{
  "entry_price": "3500.00",
  "size": "1.0",
  "leverage": "10",
  "side": "long",
  "account_balance": "10000.00"
}
```

---

## 4. Curve Finance Endpoints

**Base Path**: `/api/v1/curve`  
**Tags**: `DeFi`, `Curve`

### GET /curve/pools

Get all Curve pools with optional sorting and filtering.

**Query Parameters**:
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `chain` | string | ethereum | Blockchain |
| `sort_by` | string | tvl | Sort (tvl, apy, volume) |
| `limit` | int | 50 | Max results (1-200) |
| `min_tvl` | float | - | Minimum TVL filter (USD) |

---

### GET /curve/pools/{pool_address}

Get detailed information for a specific pool.

---

### GET /curve/pools/{pool_address}/apy

Get detailed APY breakdown (base fees, CRV rewards, extra rewards).

---

### POST /curve/quote

Get a swap quote for token exchange with risk analysis.

**Request Body**:
```json
{
  "from_token": "USDC",
  "to_token": "DAI",
  "amount": "1000",
  "chain": "ethereum"
}
```

---

### GET /curve/gauges

Get all Curve gauges with reward data.

**Query Parameters**:
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `chain` | string | ethereum | Blockchain |
| `sort_by` | string | apy | Sort (apy, weight, emissions) |
| `min_apy` | float | - | Minimum APY filter |

---

### GET /curve/tvl

Get total value locked data for Curve.

---

## 5. LayerZero Endpoints

**Base Path**: `/api/v1/layerzero`  
**Tags**: `DeFi`, `Cross-Chain`

### GET /layerzero/message/{tx_hash}

Track cross-chain message status by source transaction hash.

**Response**:
```json
{
  "message": {...},
  "progress_pct": 75,
  "estimated_completion": "2026-01-25T12:30:00Z"
}
```

---

### GET /layerzero/messages/{address}

Get cross-chain message history for an address.

**Query Parameters**:
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `limit` | int | 50 | Max results (1-100) |
| `status_filter` | string | - | Filter (INFLIGHT, DELIVERED, FAILED) |

---

### GET /layerzero/chains

Get list of supported LayerZero chains.

---

### GET /layerzero/fees/estimate

Estimate cross-chain message fees.

**Query Parameters**:
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `source_chain` | string | Yes | Source chain |
| `destination_chain` | string | Yes | Destination chain |
| `payload_size` | int | No | Payload size (1-10000) |

---

### GET /layerzero/oft/{address}

Get OFT (Omnichain Fungible Token) transfer history.

---

## 6. Axelar Endpoints

**Base Path**: `/api/v1/axelar`  
**Tags**: `DeFi`, `Bridge`

### GET /axelar/routes

Get available bridge routes including express options.

**Query Parameters**:
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `source_chain` | string | Yes | - | Source chain |
| `destination_chain` | string | Yes | - | Destination chain |
| `token` | string | No | USDC | Token to bridge |

---

### GET /axelar/estimate

Estimate transfer costs with standard and express options.

**Query Parameters**:
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `source_chain` | string | Yes | Source chain |
| `destination_chain` | string | Yes | Destination chain |
| `token` | string | Yes | Token symbol |
| `amount` | string | Yes | Amount to bridge |
| `include_express` | bool | No | Include express estimate |

---

### GET /axelar/transfer/{tx_hash}

Track transfer status with progress and next steps.

---

### GET /axelar/chains

Get list of supported Axelar chains.

---

### GET /axelar/tokens/{chain}

Get supported tokens for a chain.

---

## 7. Error Handling

### Standard Error Response

```json
{
  "error": {
    "code": "DEFI_001",
    "message": "Market not found",
    "details": {...}
  }
}
```

### Error Codes by Protocol

| Protocol | Code | HTTP Status | Description |
|----------|------|-------------|-------------|
| Aave | `AAVE_001` | 404 | Market not found |
| Aave | `AAVE_002` | 404 | Position not found |
| Aave | `AAVE_003` | 400 | Invalid address |
| Aave | `AAVE_004` | 400 | Unsupported chain |
| Morpho | `MORPHO_001` | 404 | Vault not found |
| Morpho | `MORPHO_002` | 400 | Invalid vault address |
| Hyperliquid | `HL_001` | 404 | Symbol not found |
| Hyperliquid | `HL_002` | 400 | Invalid address |
| Curve | `CURVE_001` | 404 | Pool not found |
| Curve | `CURVE_002` | 400 | Invalid token |
| Curve | `CURVE_003` | 400 | No route found |
| LayerZero | `LZ_001` | 404 | Message not found |
| LayerZero | `LZ_002` | 400 | Invalid tx hash |
| Axelar | `AXL_001` | 404 | Transfer not found |
| Axelar | `AXL_002` | 400 | Unsupported chain |
| Axelar | `AXL_003` | 400 | Unsupported token |

---

## 8. API Client Examples

### Get Aave Markets
```bash
curl -X GET "http://localhost:8000/api/v1/aave/markets?chain=ethereum&sort_by=supply_apy&limit=10"
```

### Get User Position (Aave)
```bash
curl -X GET "http://localhost:8000/api/v1/aave/positions/0x742d35Cc6634C0532925a3b844Bc9e7595f2bD21?chain=ethereum"
```

### Get Hyperliquid Funding Rates
```bash
curl -X GET "http://localhost:8000/api/v1/hyperliquid/funding?sort_by=absolute&min_rate=0.001"
```

### Calculate Position Risk
```bash
curl -X POST "http://localhost:8000/api/v1/hyperliquid/risk/calculate" \
  -H "Content-Type: application/json" \
  -d '{"entry_price": "3500.00", "size": "1.0", "leverage": "10", "side": "long"}'
```

### Track LayerZero Message
```bash
curl -X GET "http://localhost:8000/api/v1/layerzero/message/0x1234567890abcdef..."
```

### Estimate Axelar Bridge Transfer
```bash
curl -X GET "http://localhost:8000/api/v1/axelar/estimate?source_chain=ethereum&destination_chain=polygon&token=USDC&amount=1000"
```

---

## References

- **Aave Router**: `src/app/presentation/http/controllers/defi/aave_router.py`
- **Morpho Router**: `src/app/presentation/http/controllers/defi/morpho_router.py`
- **Hyperliquid Router**: `src/app/presentation/http/controllers/defi/hyperliquid_router.py`
- **Curve Router**: `src/app/presentation/http/controllers/defi/curve_router.py`
- **LayerZero Router**: `src/app/presentation/http/controllers/defi/layerzero_router.py`
- **Axelar Router**: `src/app/presentation/http/controllers/defi/axelar_router.py`
