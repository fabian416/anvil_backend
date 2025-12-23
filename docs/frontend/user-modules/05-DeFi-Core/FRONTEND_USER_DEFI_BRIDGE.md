# FRONTEND_USER_DEFI_BRIDGE

> **Enterprise Grade Specification**
> Version: 2.0.0
> Status: **Live**
> Source Validation: `src/app/presentation/http/controllers/defi/axelar_router.py` & `axelar_schemas.py`

## 1. Module Overview
The **DeFi Bridge** module leverages **Axelar Network** for secure cross-chain asset transfers. It supports both **Standard** (General Message Passing) and **Express** (faster, slightly higher fee) bridging options.

**Base URL**: `/api/v1/axelar`

---

## 2. Endpoints

### 2.1 Get Bridge Routes
**GET** `/api/v1/axelar/routes`

Finds available paths between chains.

*   **Query Params**: `source_chain`, `destination_chain`, `token` (symbol).

**Response (200 OK):**
```json
{
  "routes": [
    {
      "source_chain": "ethereum",
      "destination_chain": "arbitrum",
      "token": "USDC",
      "estimated_time_minutes": 15,
      "fee_usd": "12.50",
      "is_express": true,
      "security_score": 98
    }
  ],
  "count": 1
}
```

### 2.2 Estimate Transfer Costs
**GET** `/api/v1/axelar/estimate`

Calculates precise gas and bridge fees.

*   **Query Params**: `source_chain`, `destination_chain`, `token`, `amount`, `include_express` (bool).

**Response (200 OK):**
```json
{
  "standard": {
    "fee_usd": "5.00",
    "total_cost_usd": "8.50",
    "estimated_time_minutes": 20,
    "is_express": false
  },
  "express": {
    "fee_usd": "8.00",
    "total_cost_usd": "11.50",
    "estimated_time_minutes": 2,
    "is_express": true
  },
  "recommendation": "EXPRESS"
}
```

### 2.3 Track Transfer Status
**GET** `/api/v1/axelar/transfer/{tx_hash}`

Real-time status of a cross-chain transaction.

**Response (200 OK):**
```json
{
  "transfer": {
    "tx_hash": "0x...",
    "source_chain": "ethereum",
    "destination_chain": "optimism",
    "status": "in_progress",
    "source_tx_hash": "0x...",
    "destination_tx_hash": null,
    "created_at": "...",
    "is_express": true
  },
  "progress_pct": 65,
  "next_step": "Waiting for destination confirmation",
  "estimated_completion": "2024-01-01T12:05:00Z"
}
```

### 2.4 Get Supported Chains & Tokens
*   **GET** `/chains` -> List of IDs (`ethereum`, `binance`, etc.).
*   **GET** `/tokens/{chain}` -> List of symbols (`USDC`, `axlUSDC`).

---

## 3. Error Handling

| Status | Code | Meaning |
| :--- | :--- | :--- |
| 400 | `UNSUPPORTED_CHAIN` | Chain not configured. |
| 400 | `UNSUPPORTED_TOKEN` | Token not bridgable on this route. |
| 404 | `TRANSFER_NOT_FOUND` | Hash invalid or not indexed yet. |
| 502 | `AXELAR_API_ERROR` | Bridge provider unreachable. |
