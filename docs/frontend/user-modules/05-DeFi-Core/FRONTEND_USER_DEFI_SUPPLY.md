# FRONTEND_USER_DEFI_SUPPLY

> **Enterprise Grade Specification**
> Version: 2.0.0
> Status: **Live**
> Source Validation: `src/app/presentation/http/controllers/defi/aave_router.py` & `aave_schemas.py`

## 1. Module Overview
The **DeFi Supply** module maps to **Aave V3** lending markets. It allows users to supply assets to earn yield (`supply_apy`) and enable borrowing power.

**Base URL**: `/api/v1/aave`

---

## 2. Endpoints

### 2.1 Get Markets (Supply Opportunities)
**GET** `/api/v1/aave/markets`

Lists assets available for supplying.

*   **Query Params**: `chain`, `sort_by` (`supply_apy`, `tvl`), `limit`.

**Response (200 OK):**
```json
{
  "markets": [
    {
      "asset_address": "0x...",
      "symbol": "USDC",
      "supply_apy": "0.052", // 5.2%
      "total_supplied_usd": "1000000000",
      "can_use_as_collateral": true,
      "ltv": "0.80", // 80% Loan-to-Value
      "liquidation_threshold": "0.85"
    }
  ],
  "total_supplied_usd": "5000000000"
}
```

### 2.2 Get User Position
**GET** `/api/v1/aave/positions/{user_address}`

Returns current supplied assets and health.

**Response (200 OK):**
```json
{
  "user_address": "0x...",
  "net_worth_usd": "1500.00",
  "health_factor": "2.5",
  "supplies": [
    {
      "symbol": "ETH",
      "balance": "1.5",
      "balance_usd": "3000.00",
      "apy": "0.03",
      "is_collateral": true
    }
  ]
}
```

### 2.3 Calculate Health Factor Simulation
**POST** `/api/v1/aave/calculate/health-factor`

Simulate impact of new supply on health.

*   **Body**: `{"collateral_usd": 1000, "debt_usd": 500}`.

**Response**:
```json
{
  "value": "1.65",
  "risk_level": "moderate",
  "is_liquidatable": false
}
```

---

## 3. Error Handling

| Status | Code | Meaning |
| :--- | :--- | :--- |
| 404 | `MARKET_NOT_FOUND` | Asset not listed on Aave. |
| 400 | `INVALID_ADDRESS` | User address malformed. |
