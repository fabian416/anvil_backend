# FRONTEND_USER_DEFI_EARN

> **Enterprise Grade Specification**
> Version: 2.0.0
> Status: **Live**
> Source Validation: `aave_router.py` (Lending) & `curve_router.py` (Liquidity)

## 1. Module Overview
The **DeFi Earn** module is an aggregator of yield opportunities. It combines **Lending Yields** (Aave) and **Liquidity Provision Yields** (Curve) into a single discovery interface.

---

## 2. Endpoints

### 2.1 Get Lending Yields (Aave)
**GET** `/api/v1/aave/markets?sort_by=supply_apy`

Returns single-sided lending opportunities (lower risk).

### 2.2 Get Liquidity Yields (Curve)
**GET** `/api/v1/curve/pools?sort_by=apy`

Returns liquidity pool opportunities (higher risk, potential impermanent loss).

**Response (from Curve Pools):**
```json
{
  "pools": [
    {
      "name": "tricrypto",
      "apy": "12.5", // 12.5% APY
      "tvl_usd": "200000000"
    }
  ]
}
```

### 2.3 Get Detailed APY Breakdown (Curve)
**GET** `/api/v1/curve/pools/{pool_address}/apy`

**Response (200 OK):**
```json
{
  "base_apy": "2.5", // Trading fees
  "crv_apy": "4.0", // Inflationary rewards
  "reward_apy": "1.5", // Other tokens (e.g. LDO)
  "total_apy": "8.0",
  "boost_max": "20.0" // Max yield with veCRV
}
```

---

## 3. Strategy
The frontend should combine these two data sources:
1.  **Stable Earnings**: Filter Aave markets + Curve Stable pools.
2.  **High Yield**: Filter Curve Crypto pools.
