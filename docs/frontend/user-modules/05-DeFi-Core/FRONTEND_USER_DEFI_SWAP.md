# FRONTEND_USER_DEFI_SWAP

> **Enterprise Grade Specification**
> Version: 2.0.0
> Status: **Live**
> Source Validation: `src/app/presentation/http/controllers/defi/curve_router.py` & `curve_schemas.py`

## 1. Module Overview
The **DeFi Swap** module uses **Curve Finance** logic to provide efficient stablecoin and crypto asset swaps with low slippage. It includes risk analysis warnings and detailed price impact calculations.

**Base URL**: `/api/v1/curve`

---

## 2. Endpoints

### 2.1 Get Swap Quote
**POST** `/api/v1/curve/quote`

Calculates the best swap rate, including fees and price impact.

**Request Body (`SwapQuoteRequestModel`):**
| Field | Type | Required | Description |
| :--- | :--- | :--- | :--- |
| `from_token` | `string` | **Yes** | Source token address (e.g., `0x...`). |
| `to_token` | `string` | **Yes** | Destination token address. |
| `amount` | `string` | **Yes** | Amount in smallest unit (wei). |
| `chain` | `string` | No | Default `ethereum`. |

**Response (200 OK):**
```json
{
  "from_token": "0x...",
  "to_token": "0x...",
  "amount_in": "1000000000000000000",
  "amount_out": "998500000",
  "price_impact": "0.15",
  "fee_amount": "1500000",
  "exchange_rate": "0.9985",
  "pool_address": "0x...",
  "warnings": [
    "High price impact detected (>1%)"
  ]
}
```

### 2.2 List Pools (Discovery)
**GET** `/api/v1/curve/pools`

Finds pools for routing or exploration.

*   **Query Params**:
    *   `chain`: `ethereum` (default)
    *   `sort_by`: `tvl` | `apy` | `volume`
    *   `min_tvl`: `float` (optional USD filter)
    *   `limit`: `int` (default 50)

**Response (200 OK):**
```json
{
  "pools": [
    {
      "id": "0x...",
      "name": "3pool",
      "symbol": "3Crv",
      "chain": "ethereum",
      "coins": ["0x...", "0x..."],
      "coin_names": ["DAI", "USDC", "USDT"],
      "tvl_usd": "500000000.0",
      "apy": "4.5",
      "volume_24h_usd": "12000000.0",
      "fee_percentage": "0.04"
    }
  ],
  "count": 1,
  "chain": "ethereum"
}
```

## 3. Error Handling

| Status | Code | Meaning |
| :--- | :--- | :--- |
| 400 | `NO_ROUTE_FOUND` | No valid path between tokens. |
| 400 | `INVALID_TOKEN` | Token address malformed. |
| 404 | `POOL_NOT_FOUND` | Pool not found on chain. |
| 502 | `CURVE_API_ERROR` | Upstream Curve provider failed. |
