# Module: Markets & Discovery

**Route**: `/markets`
**Auth Required**: Yes
**Package**: `user/home`

## 1. Overview
Enterprise-grade market data aggregation with ML risk scores and protocol yields.

## 2. API Contract

### Get Market Overview
**Endpoint**: `GET /api/v1/user/markets/overview`
**Query Params**:
- `chains` (comma-separated string): e.g., "ethereum,base"
- `risk_filter` (comma-separated string): e.g., "LOW,MEDIUM"

#### Response Body (Aggregate)
| Field | Type | Description |
|---|---|---|
| `top_tokens` | `Array<TokenMarketData>` | |
| `trending_protocols` | `Array<Object>` | |
| `market_trends` | `Array<MarketTrend>` | |

**TokenMarketData Object**:
| Field | Type | Description |
|---|---|---|
| `token_symbol` | `string` | |
| `price_usd` | `float` | |
| `price_change_24h` | `float` | |
| `risk_level` | `string` | "LOW", "MEDIUM", "HIGH", "CRITICAL" |
| `risk_score` | `float` | 0-10 Scale |
| `risk_confidence` | `float` | 0-1 Scale |

**JSON Example**:
```json
{
  "top_tokens": [
    {
      "token_symbol": "ETH",
      "price_usd": 2250.50,
      "risk_level": "LOW",
      "risk_score": 2.1
    }
  ]
}
```

### Get Yields
**Endpoint**: `GET /api/v1/user/markets/yields`
**Query Params**: `min_apy` (float), `max_risk` (float)

#### Response Body
```json
{
  "yields": [
    {
      "protocol_name": "Aave V3",
      "chain": "ethereum",
      "total_apy": 5.3,
      "risk_score": 2.1,
      "category": "lending",
      "risk_adjusted_apy": 2.52
    }
  ]
}
```

## 3. Implementation Flow

1.  **Overview Tab**:
    - Fetch `/overview`.
    - Render `top_tokens` in a Virtual List.
    - Show `risk_score` as a color-coded badge (Green < 3, Yellow < 7, Red > 7).
2.  **Yields Tab**:
    - Fetch `/yields`.
    - Allow client-side sorting by `total_apy` or `risk_adjusted_apy`.
