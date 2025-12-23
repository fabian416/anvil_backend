# FRONTEND_USER_DEFI_BORROW

> **Enterprise Grade Specification**
> Version: 2.0.0
> Status: **Live**
> Source Validation: `src/app/presentation/http/controllers/defi/aave_router.py` & `aave_schemas.py`

## 1. Module Overview
The **DeFi Borrow** module allows users to borrow assets against their supplied collateral via **Aave V3**. It enforces strict health factor checks to prevent liquidation.

**Base URL**: `/api/v1/aave`

---

## 2. Endpoints

### 2.1 Get Borrow Markets
**GET** `/api/v1/aave/markets?sort_by=borrow_apy`

Lists assets available for borrowing.

**Response**: Similar to Supply, but focus on `borrow_apy_variable` and `borrow_apy_stable`.

### 2.2 Get Available Borrow Capacity
**GET** `/api/v1/aave/positions/{user_address}/borrow-capacity/{asset}`

Calculates how much of a specific asset can be borrowed safely.

**Response (200 OK):**
```json
{
  "asset": "USDC",
  "max_borrowable": "1000.00",
  "max_borrowable_usd": "1000.00",
  "current_debt": "0",
  "health_factor_after_max_borrow": "1.01" // Borderline liquidation
}
```

### 2.3 Get Asset Rates
**GET** `/api/v1/aave/rates/{asset}`

Detailed rate breakdown.

**Response (200 OK):**
```json
{
  "asset": "USDC",
  "borrow_apy_variable": "0.04",
  "borrow_apy_stable": "0.06",
  "liquidation_threshold": "0.85"
}
```

---

## 3. Risks & Errors

*   **Liquidation Risk**: If `Health Factor < 1.0`, assets are liquidated. Use `GET /health` to monitor.
*   **Errors**:
    *   `POSITION_NOT_FOUND`: User has no collateral (cannot borrow).
    *   `LIQUIDITY_UNAVAILABLE`: Market utilization > 99%.
