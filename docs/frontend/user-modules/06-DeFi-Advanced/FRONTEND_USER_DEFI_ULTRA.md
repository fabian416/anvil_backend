# FRONTEND_USER_ULTRA_DEFI

> **Enterprise Grade Specification**
> Version: 2.0.0
> Status: **Live**
> Source Validation: `src/app/presentation/http/controllers/ultra/arbitrage.py` & `flash_loans.py`

## 1. Module Overview
**Ultra** is the advanced DeFi suite for power users. It features **Arbitrage Discovery** (scanning DEXs for price discrepancies) and **Flash Loan Simulation**.

**Base URL**: `/api/v1/user/ultra`

---

## 2. Flash Loans (`/flash-loans`)

### 2.1 Get Protocols
**GET** `/api/v1/user/ultra/flash-loans/protocols`

Lists supported providers (Aave, Balancer) with fee structures.

**Response (200 OK):**
```json
[
  {
    "protocol": "aave_v3",
    "name": "Aave V3",
    "fee_percentage": 0.09,
    "max_loan_usd": "10000000",
    "requires_collateral": false
  }
]
```

### 2.2 Estimate Fees
**GET** `/api/v1/user/ultra/flash-loans/estimate-fees`
*   Query: `protocol`, `amount_usd`.

Calculates gas + protocol fees.

### 2.3 Simulate Loan
**POST** `/api/v1/user/ultra/flash-loans/simulate`

Simulates execution without broadcasting.

**Response (200 OK):**
```json
{
  "status": "success",
  "gas_used": 240000,
  "profit_usd": "495.00",
  "fees_paid": "5.00"
}
```

---

## 3. Arbitrage (`/arbitrage`)

### 3.1 Discover Opportunities
**GET** `/api/v1/user/ultra/arbitrage/discover`

Scans for 2-hop, 3-hop, or triangular arbitrage.

*   **Query Params**: `capital` (default 10000), `type`, `min_profit`.

**Response (200 OK):**
```json
[
  {
    "opportunity_id": "ARB-123",
    "type": "2hop",
    "path": [
      { "dex": "uniswap_v2", "token_in": "WETH", "token_out": "USDC" },
      { "dex": "sushiswap", "token_in": "USDC", "token_out": "WETH" }
    ],
    "expected_profit_usd": "95.50",
    "confidence_score": 0.85
  }
]
```

### 3.2 Simulate Opportunity
**POST** `/api/v1/user/ultra/arbitrage/simulate`

Checks slippage and success probability.

**Response (200 OK):**
```json
{
  "simulated_profit": "94.55",
  "slippage_impact": "0.95",
  "recommendation": "Execute"
}
```
