# FRONTEND_USER_DEFI_STAKE

> **Enterprise Grade Specification**
> Version: 2.0.0
> Status: **Live**
> Source Validation: `src/app/presentation/http/controllers/defi/curve_router.py`

## 1. Module Overview
The **DeFi Stake** module focuses on staking mechanisms. Currently, it primarily supports **Curve Gauge Staking** (staking LP tokens for rewards).
*Note: Liquid Staking (Lido) is planned for V2.*

**Base URL**: `/api/v1/curve`

---

## 2. Endpoints

### 2.1 Get Staking Gauges
**GET** `/api/v1/curve/gauges`

Lists gauges where users can stake their LP tokens.

*   **Query Params**: `chain`, `sort_by` (`apy`), `min_apy`.

**Response (200 OK):**
```json
{
  "gauges": [
    {
      "address": "0x...",
      "pool_address": "0x...",
      "apy": "15.0",
      "relative_weight": "0.05", // 5% of total emissions
      "total_staked": "5000000"
    }
  ],
  "chain": "ethereum"
}
```

---

## 3. Future Integrations (V2)
*   **Lido**: `POST /lido/stake` (ETH -> stETH).
*   **RocketPool**: `POST /rocketpool/stake` (ETH -> rETH).
