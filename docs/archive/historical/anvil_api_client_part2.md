# 🔌 Anvil API - CLIENT Endpoints Part 2

## Overview

**Continuation of CLIENT API endpoints**  
**Base URL:** `https://api.anvil.com/v1`  
**Authentication:** JWT Bearer Token required for all endpoints

---

## Table of Contents - Part 2

5. [Trading & Swaps](#5-trading--swaps)
6. [Earn (Yield Farming)](#6-earn-yield-farming)
7. [Save Schedules](#7-save-schedules)
8. [Perpetuals (Hyperliquid)](#8-perpetuals-hyperliquid)
9. [AI Chat](#9-ai-chat)
10. [Subscriptions](#10-subscriptions)
11. [Notifications](#11-notifications)
12. [Funding](#12-funding)

---

## 5. Trading & Swaps

Base path: `/api/v1/user/trade`

### 5.1 POST /trade/quote

Get a swap quote without executing the trade.

**Endpoint:** `POST /api/v1/user/trade/quote`

**Authentication:** Bearer Token required

**Request:**
```http
POST /api/v1/user/trade/quote HTTP/1.1
Host: api.anvil.com
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json

{
  "from_asset": "USDC",
  "from_amount": "50",
  "to_asset": "ETH",
  "chain": "arbitrum",
  "slippage": 0.5
}
```

**Request Body Schema:**

| Field | Type | Required | Constraints | Description |
|-------|------|----------|-------------|-------------|
| `from_asset` | string | ✅ Yes | Valid token symbol | Asset to swap from |
| `from_amount` | string | ✅ Yes | Positive number | Amount to swap |
| `to_asset` | string | ✅ Yes | Valid token symbol | Asset to receive |
| `chain` | string | ✅ Yes | 'arbitrum', 'base', 'hyperliquid' | Blockchain |
| `slippage` | number | No | 0.1 - 5.0 | Slippage tolerance % (default: 0.5) |

**Success Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "quote_id": "quote_abc123def456",
    "from_asset": "USDC",
    "from_amount": "50.0",
    "to_asset": "ETH",
    "to_amount": "0.0204",
    "to_amount_min": "0.0203",
    "rate": "1 USDC = 0.000408 ETH",
    "inverse_rate": "1 ETH = 2450.00 USDC",
    "price_impact": "0.12%",
    "estimated_gas": "150000",
    "estimated_gas_native": "0.00015 ETH",
    "estimated_gas_usd": 0.37,
    "dex_aggregator": "1inch",
    "dex_route": [
      {
        "protocol": "Uniswap V3",
        "percentage": 100,
        "path": ["USDC", "ETH"],
        "pool": "0xpool123..."
      }
    ],
    "slippage": 0.5,
    "execution_time_estimate": "30 seconds",
    "quote_expires_at": "2025-11-16T16:46:00Z",
    "warnings": []
  }
}
```

**Response with Warnings:**
```json
{
  "success": true,
  "data": {
    "quote_id": "quote_abc123def456",
    "from_asset": "USDC",
    "from_amount": "1000.0",
    "to_asset": "ETH",
    "to_amount": "0.402",
    "to_amount_min": "0.400",
    "rate": "1 USDC = 0.000402 ETH",
    "price_impact": "2.35%",
    "estimated_gas": "180000",
    "estimated_gas_usd": 0.44,
    "dex_aggregator": "1inch",
    "dex_route": [
      {
        "protocol": "Uniswap V3",
        "percentage": 80
      },
      {
        "protocol": "SushiSwap",
        "percentage": 20
      }
    ],
    "slippage": 0.5,
    "quote_expires_at": "2025-11-16T16:46:00Z",
    "warnings": [
      {
        "code": "HIGH_PRICE_IMPACT",
        "message": "Price impact is 2.35%, higher than recommended 1%",
        "severity": "medium"
      }
    ]
  }
}
```

**Error Response (400 Bad Request):**
```json
{
  "success": false,
  "error": {
    "code": "INSUFFICIENT_LIQUIDITY",
    "message": "Insufficient liquidity for this trade size",
    "details": {
      "from_asset": "USDC",
      "from_amount": "1000000",
      "to_asset": "ETH",
      "available_liquidity": "500000",
      "suggestion": "Try reducing the amount"
    },
    "timestamp": "2025-11-16T16:45:00Z",
    "request_id": "req_xyz789"
  }
}
```

**Error Codes:**

| Code | Description |
|------|-------------|
| `INSUFFICIENT_BALANCE` | User doesn't have enough tokens |
| `INSUFFICIENT_LIQUIDITY` | Not enough liquidity in DEX pools |
| `UNSUPPORTED_PAIR` | Trading pair not supported |
| `AMOUNT_TOO_SMALL` | Amount below minimum |
| `AMOUNT_TOO_LARGE` | Amount exceeds maximum |
| `DEX_SERVICE_ERROR` | DEX aggregator API error |

**Business Logic:**
1. Validates user has sufficient balance
2. Calls DEX aggregator (1inch/0x) for quote
3. Calculates gas costs with current prices
4. Applies slippage tolerance
5. Checks price impact
6. Returns quote with 60-second expiry

**Database Operations:**
```sql
-- Check user balance
SELECT balance_usd
FROM chain_addresses
WHERE wallet_id = (SELECT id FROM wallets WHERE user_id = ?)
  AND chain = ?;
```

**External Dependencies:**
- 1inch API (primary DEX aggregator)
- 0x API (fallback aggregator)
- Gas price APIs

**Rate Limit:** 30 requests per minute

---

### 5.2 POST /trade/swap

Execute a token swap based on quote.

**Endpoint:** `POST /api/v1/user/trade/swap`

**Authentication:** Bearer Token required

**Request:**
```http
POST /api/v1/user/trade/swap HTTP/1.1
Host: api.anvil.com
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json

{
  "quote_id": "quote_abc123def456",
  "from_asset": "USDC",
  "from_amount": "50",
  "to_asset": "ETH",
  "to_amount_min": "0.0203",
  "chain": "arbitrum",
  "slippage": 0.5,
  "dex_aggregator": "1inch"
}
```

**Request Body Schema:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `quote_id` | string | No | Quote ID from /trade/quote (recommended) |
| `from_asset` | string | ✅ Yes | Asset to swap from |
| `from_amount` | string | ✅ Yes | Amount to swap |
| `to_asset` | string | ✅ Yes | Asset to receive |
| `to_amount_min` | string | ✅ Yes | Minimum acceptable output |
| `chain` | string | ✅ Yes | Blockchain |
| `slippage` | number | ✅ Yes | Slippage tolerance |
| `dex_aggregator` | string | No | Preferred DEX (default: best) |

**Success Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "transaction_id": 789,
    "tx_hash": "0xswap123def456789abcdef0123456789abcdef0123456789abcdef012345",
    "status": "pending",
    "from_asset": "USDC",
    "from_amount": "50.0",
    "to_asset": "ETH",
    "expected_amount": "0.0204",
    "minimum_amount": "0.0203",
    "estimated_time": "30 seconds",
    "explorer_url": "https://arbiscan.io/tx/0xswap123def456...",
    "created_at": "2025-11-16T16:45:30Z"
  }
}
```

**Error Response (400 Bad Request):**
```json
{
  "success": false,
  "error": {
    "code": "DAILY_LIMIT_EXCEEDED",
    "message": "Daily trade limit exceeded",
    "details": {
      "limit_usd": 5000.00,
      "used_today": 4950.00,
      "requested": 50.00,
      "available": 50.00,
      "reset_at": "2025-11-17T00:00:00Z"
    },
    "timestamp": "2025-11-16T16:45:00Z",
    "request_id": "req_xyz789"
  }
}
```

**Error Codes:**

| Code | Description |
|------|-------------|
| `INSUFFICIENT_BALANCE` | Not enough tokens |
| `SLIPPAGE_EXCEEDED` | Price moved beyond tolerance |
| `QUOTE_EXPIRED` | Quote older than 60 seconds |
| `DAILY_LIMIT_EXCEEDED` | Exceeded daily trade limit |
| `GAS_PRICE_TOO_HIGH` | Network congestion |
| `TRANSACTION_FAILED` | Blockchain submission failed |

**Business Logic:**
1. Validates quote (if provided) hasn't expired
2. Re-checks balance
3. Checks daily trade limit
4. Gets fresh quote if needed
5. Signs transaction with Privy
6. Submits to blockchain
7. Creates transaction record (status=PENDING)
8. Background job monitors confirmation

**Database Operations:**
```sql
-- Check daily limit
SELECT COALESCE(SUM(amount_in), 0) as today_volume
FROM transactions
WHERE user_id = ?
  AND type = 0
  AND status = 1
  AND DATE(created_at) = CURDATE();

-- Create transaction
INSERT INTO transactions (
  user_id, wallet_id, type, chain, asset_in, amount_in,
  asset_out, amount_out, tx_hash, status, dex_aggregator,
  dex_route, slippage, created_at
) VALUES (?, ?, 0, ?, ?, ?, ?, ?, ?, 0, ?, ?, ?, NOW());

-- Update balance (optimistic)
UPDATE chain_addresses
SET balance_usd = balance_usd - ?
WHERE wallet_id = ? AND chain = ?;
```

**External Dependencies:**
- DEX aggregator API
- Privy (transaction signing)
- Blockchain RPC (transaction submission)

**Rate Limit:** 10 requests per minute

---

## 6. Earn (Yield Farming)

Base path: `/api/v1/user/earn`

### 6.1 GET /earn/opportunities

Get available yield farming opportunities.

**Endpoint:** `GET /api/v1/user/earn/opportunities`

**Authentication:** Bearer Token required

**Query Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `chain` | string | Filter by chain |
| `protocol` | string | Filter by protocol: 'aave', 'compound', 'curve' |
| `asset` | string | Filter by asset |
| `min_apy` | number | Minimum APY |
| `risk_score` | string | Filter by risk: 'low', 'medium', 'high' |
| `sort` | string | Sort: 'apy:desc', 'tvl:desc', 'risk:asc' |

**Request:**
```http
GET /api/v1/user/earn/opportunities?chain=arbitrum&min_apy=4&sort=apy:desc HTTP/1.1
Host: api.anvil.com
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Success Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "opportunities": [
      {
        "id": "compound-usdt-arbitrum",
        "protocol": "compound",
        "protocol_name": "Compound V3",
        "protocol_logo": "https://assets.anvil.com/protocols/compound.png",
        "chain": "arbitrum",
        "asset": "USDT",
        "asset_logo": "https://assets.anvil.com/tokens/usdt.png",
        "apy": 5.8,
        "apy_7d_avg": 5.6,
        "apy_30d_avg": 5.5,
        "tvl": "87000000",
        "tvl_change_24h": 2.3,
        "utilization_rate": 72.5,
        "risk_score": "low",
        "risk_factors": [
          {
            "factor": "Smart contract risk",
            "description": "Protocol has been audited by Trail of Bits",
            "severity": "low"
          },
          {
            "factor": "Liquidation risk",
            "description": "None for supply-only positions",
            "severity": "none"
          }
        ],
        "description": "Supply USDT to Compound V3 and earn interest",
        "min_deposit": "1",
        "max_deposit": null,
        "withdrawal_fee": "0",
        "lock_period": "none",
        "auto_compound": true,
        "verified": true,
        "audit_reports": [
          {
            "auditor": "Trail of Bits",
            "date": "2024-05-15",
            "report_url": "https://..."
          }
        ]
      },
      {
        "id": "aave-usdc-arbitrum",
        "protocol": "aave",
        "protocol_name": "Aave V3",
        "protocol_logo": "https://assets.anvil.com/protocols/aave.png",
        "chain": "arbitrum",
        "asset": "USDC",
        "asset_logo": "https://assets.anvil.com/tokens/usdc.png",
        "apy": 4.2,
        "apy_7d_avg": 4.1,
        "apy_30d_avg": 4.0,
        "tvl": "125000000",
        "tvl_change_24h": 1.5,
        "utilization_rate": 75.2,
        "risk_score": "low",
        "risk_factors": [
          {
            "factor": "Smart contract risk",
            "description": "Battle-tested protocol with $5B+ TVL",
            "severity": "low"
          }
        ],
        "description": "Lend USDC and earn interest on Aave",
        "min_deposit": "1",
        "max_deposit": null,
        "withdrawal_fee": "0",
        "lock_period": "none",
        "auto_compound": true,
        "verified": true,
        "audit_reports": [
          {
            "auditor": "OpenZeppelin",
            "date": "2024-03-20",
            "report_url": "https://..."
          }
        ]
      }
    ],
    "count": 2,
    "filters_applied": {
      "chain": "arbitrum",
      "min_apy": 4
    }
  }
}
```

**Business Logic:**
1. Fetches current APYs from protocol APIs
2. Calculates risk scores based on:
   - Protocol age and TVL
   - Audit history
   - Historical exploits
   - Smart contract complexity
3. Filters and sorts based on parameters
4. Returns opportunities with metadata

**External Dependencies:**
- Aave API (APY data)
- Compound API (APY data)
- Curve API (APY data)
- DeFi Llama (TVL data)

**Rate Limit:** 20 requests per minute

---

### 6.2 POST /earn/deposit

Deposit assets to a yield protocol.

**Endpoint:** `POST /api/v1/user/earn/deposit`

**Authentication:** Bearer Token required

**Request:**
```http
POST /api/v1/user/earn/deposit HTTP/1.1
Host: api.anvil.com
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json

{
  "opportunity_id": "aave-usdc-arbitrum",
  "protocol": "aave",
  "asset": "USDC",
  "amount": "50",
  "chain": "arbitrum"
}
```

**Request Body Schema:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `opportunity_id` | string | No | Opportunity ID from /earn/opportunities |
| `protocol` | string | ✅ Yes | 'aave', 'compound', 'curve' |
| `asset` | string | ✅ Yes | Asset to deposit |
| `amount` | string | ✅ Yes | Amount to deposit |
| `chain` | string | ✅ Yes | Blockchain |

**Success Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "position_id": 101,
    "tx_hash": "0xearn123abc456def...",
    "status": "pending",
    "protocol": "aave",
    "asset": "USDC",
    "amount": "50.0",
    "current_apy": 4.2,
    "estimated_daily_earnings": "0.0057",
    "estimated_monthly_earnings": "0.173",
    "estimated_annual_earnings": "2.10",
    "explorer_url": "https://arbiscan.io/tx/0xearn123abc456def...",
    "created_at": "2025-11-16T17:00:00Z"
  }
}
```

**Error Response (400 Bad Request):**
```json
{
  "success": false,
  "error": {
    "code": "BELOW_MINIMUM_DEPOSIT",
    "message": "Amount below minimum deposit requirement",
    "details": {
      "amount": "0.5",
      "minimum": "1",
      "asset": "USDC"
    },
    "timestamp": "2025-11-16T17:00:00Z",
    "request_id": "req_xyz789"
  }
}
```

**Business Logic:**
1. Validates balance
2. Checks minimum deposit
3. Prepares protocol-specific deposit transaction
4. Signs with Privy
5. Submits to blockchain
6. Creates `earn_positions` record
7. Creates `transactions` record
8. Hourly background job updates earnings

**Database Operations:**
```sql
-- Create position
INSERT INTO earn_positions (
  user_id, wallet_id, chain, protocol, asset,
  amount_deposited, current_value, apy, current_apy,
  status, deposit_tx_hash, deposited_at, created_at
) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'active', ?, NOW(), NOW());

-- Create transaction
INSERT INTO transactions (
  user_id, wallet_id, type, chain, asset_in, amount_in,
  tx_hash, status, created_at
) VALUES (?, ?, 2, ?, ?, ?, ?, 0, NOW());

-- Update balance
UPDATE chain_addresses
SET balance_usd = balance_usd - ?
WHERE wallet_id = ? AND chain = ?;
```

**External Dependencies:**
- Protocol smart contracts (Aave, Compound, Curve)
- Privy (signing)
- Blockchain RPC

**Rate Limit:** 10 requests per minute

---

### 6.3 GET /earn/positions

Get user's active earn positions.

**Endpoint:** `GET /api/v1/user/earn/positions`

**Authentication:** Bearer Token required

**Query Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `status` | string | Filter: 'active', 'withdrawn' |
| `protocol` | string | Filter by protocol |
| `chain` | string | Filter by chain |

**Request:**
```http
GET /api/v1/user/earn/positions?status=active HTTP/1.1
Host: api.anvil.com
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Success Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "positions": [
      {
        "id": 101,
        "protocol": "aave",
        "protocol_name": "Aave V3",
        "chain": "arbitrum",
        "asset": "USDC",
        "amount_deposited": "50.0",
        "current_value": "50.06",
        "rewards_earned": "0.06",
        "rewards_earned_usd": 0.06,
        "unrealized_gain": 0.06,
        "unrealized_gain_percent": 0.12,
        "apy": 4.2,
        "current_apy": 4.3,
        "daily_earnings": "0.0057",
        "monthly_earnings_projected": "0.173",
        "annual_earnings_projected": "2.15",
        "status": "active",
        "deposited_at": "2025-11-16T17:00:00Z",
        "last_update": "2025-11-16T18:00:00Z",
        "days_active": 0.04,
        "hours_active": 1
      }
    ],
    "summary": {
      "total_positions": 1,
      "total_deposited_usd": 50.00,
      "total_current_value_usd": 50.06,
      "total_rewards_usd": 0.06,
      "weighted_avg_apy": 4.3,
      "total_daily_earnings_usd": 0.0057,
      "total_monthly_earnings_projected": 0.173,
      "total_annual_earnings_projected": 2.15
    }
  }
}
```

**Database Operations:**
```sql
SELECT ep.*, p.name as protocol_name
FROM earn_positions ep
LEFT JOIN protocols p ON ep.protocol = p.identifier
WHERE ep.user_id = ?
  AND (? IS NULL OR ep.status = ?)
  AND (? IS NULL OR ep.protocol = ?)
  AND (? IS NULL OR ep.chain = ?)
ORDER BY ep.deposited_at DESC;
```

**Rate Limit:** 60 requests per minute

---

### 6.4 POST /earn/positions/:id/withdraw

Withdraw from an earn position.

**Endpoint:** `POST /api/v1/user/earn/positions/:id/withdraw`

**Authentication:** Bearer Token required

**Request:**
```http
POST /api/v1/user/earn/positions/101/withdraw HTTP/1.1
Host: api.anvil.com
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json

{
  "amount": "50.06"
}
```

**Request Body Schema:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `amount` | string | No | Amount to withdraw (all if omitted) |

**Success Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "position_id": 101,
    "tx_hash": "0xwithdraw789abc...",
    "status": "pending",
    "amount_withdrawn": "50.06",
    "rewards_included": "0.06",
    "protocol_fee": "0",
    "net_amount": "50.06",
    "explorer_url": "https://arbiscan.io/tx/0xwithdraw789abc...",
    "estimated_time": "30 seconds"
  }
}
```

**Database Operations:**
```sql
-- Update position
UPDATE earn_positions
SET status = 'withdrawn',
    withdrawn_at = NOW(),
    withdrawal_tx_hash = ?,
    updated_at = NOW()
WHERE id = ? AND user_id = ?;

-- Create transaction
INSERT INTO transactions (
  user_id, wallet_id, type, chain, asset_out, amount_out,
  tx_hash, status, created_at
) VALUES (?, ?, 2, ?, ?, ?, ?, 0, NOW());
```

**Rate Limit:** 10 requests per minute

---

## 7. Save Schedules

Base path: `/api/v1/user/save`

### 7.1 GET /save/schedules

Get recurring save schedules.

**Endpoint:** `GET /api/v1/user/save/schedules`

**Authentication:** Bearer Token required

**Query Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `status` | string | Filter: 'active', 'paused', 'completed' |

**Success Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "schedules": [
      {
        "id": 201,
        "chain": "arbitrum",
        "asset": "USDC",
        "amount": "20.0",
        "frequency": "weekly",
        "frequency_label": "Every week",
        "day_of_week": 1,
        "day_of_week_label": "Monday",
        "day_of_month": null,
        "destination_protocol": "aave",
        "destination_protocol_name": "Aave V3",
        "status": "active",
        "next_execution_at": "2025-11-18T00:00:00Z",
        "last_execution_at": null,
        "total_saved": "0",
        "execution_count": 0,
        "max_executions": null,
        "created_at": "2025-11-16T17:00:00Z"
      }
    ],
    "summary": {
      "total_schedules": 1,
      "active_schedules": 1,
      "paused_schedules": 0,
      "total_saved_all_time": "0"
    }
  }
}
```

**Rate Limit:** 60 requests per minute

---

### 7.2 POST /save/schedule

Create recurring save schedule.

**Endpoint:** `POST /api/v1/user/save/schedule`

**Authentication:** Bearer Token required

**Request:**
```http
POST /api/v1/user/save/schedule HTTP/1.1
Host: api.anvil.com
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json

{
  "asset": "USDC",
  "amount": "20",
  "frequency": "weekly",
  "day_of_week": 1,
  "destination_protocol": "aave",
  "chain": "arbitrum",
  "max_executions": null
}
```

**Request Body Schema:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `asset` | string | ✅ Yes | Asset to save |
| `amount` | string | ✅ Yes | Amount per execution |
| `frequency` | string | ✅ Yes | 'daily', 'weekly', 'biweekly', 'monthly' |
| `day_of_week` | integer | If weekly | 0=Sunday, 1=Monday, ... |
| `day_of_month` | integer | If monthly | 1-31 |
| `destination_protocol` | string | ✅ Yes | 'aave', 'compound', 'wallet' |
| `chain` | string | ✅ Yes | Blockchain |
| `max_executions` | integer | No | Max runs (null = infinite) |

**Success Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "schedule_id": 201,
    "status": "active",
    "next_execution": "2025-11-18T00:00:00Z",
    "projections": {
      "week_1": {"principal": 20.00, "interest": 0.02, "total": 20.02},
      "month_1": {"principal": 80.00, "interest": 0.28, "total": 80.28},
      "month_6": {"principal": 480.00, "interest": 5.04, "total": 485.04},
      "year_1": {"principal": 1040.00, "interest": 21.84, "total": 1061.84},
      "year_5": {"principal": 5200.00, "interest": 547.20, "total": 5747.20}
    }
  }
}
```

**Database Operations:**
```sql
INSERT INTO save_schedules (
  user_id, wallet_id, chain, asset, amount, frequency,
  day_of_week, day_of_month, destination_protocol, status,
  next_execution_at, total_saved, execution_count, max_executions,
  created_at
) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'active', ?, 0, 0, ?, NOW());
```

**Rate Limit:** 20 requests per minute

---

### 7.3 PATCH /save/schedules/:id

Update/pause save schedule.

**Endpoint:** `PATCH /api/v1/user/save/schedules/:id`

**Request:**
```http
PATCH /api/v1/user/save/schedules/201 HTTP/1.1
Host: api.anvil.com
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json

{
  "status": "paused"
}
```

**Success Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "schedule_id": 201,
    "status": "paused",
    "paused_at": "2025-11-16T17:30:00Z",
    "updated_at": "2025-11-16T17:30:00Z"
  }
}
```

**Rate Limit:** 20 requests per minute

---

### 7.4 DELETE /save/schedules/:id

Delete save schedule.

**Endpoint:** `DELETE /api/v1/user/save/schedules/:id`

**Success Response (200 OK):**
```json
{
  "success": true,
  "message": "Schedule deleted successfully",
  "data": {
    "schedule_id": 201,
    "deleted_at": "2025-11-16T17:35:00Z"
  }
}
```

**Rate Limit:** 20 requests per minute

---

## 8. Perpetuals (Hyperliquid)

Base path: `/api/v1/user/perpetuals`

### 8.1 POST /perpetuals/open

Open perpetual position.

**Endpoint:** `POST /api/v1/user/perpetuals/open`

**Request:**
```http
POST /api/v1/user/perpetuals/open HTTP/1.1
Host: api.anvil.com
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json

{
  "symbol": "ETH-USD",
  "side": "long",
  "leverage": 5.0,
  "margin": "50",
  "size": "0.102"
}
```

**Request Body Schema:**

| Field | Type | Required | Constraints | Description |
|-------|------|----------|-------------|-------------|
| `symbol` | string | ✅ Yes | Valid pair | 'ETH-USD', 'BTC-USD', 'SOL-USD' |
| `side` | string | ✅ Yes | 'long', 'short' | Position direction |
| `leverage` | number | ✅ Yes | 1.0 - 20.0 | Leverage multiplier |
| `margin` | string | ✅ Yes | Positive number | Collateral in USDC |
| `size` | string | ✅ Yes | Positive number | Position size in base asset |

**Success Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "position_id": 301,
    "status": "open",
    "symbol": "ETH-USD",
    "side": "long",
    "leverage": 5.0,
    "size": "0.102",
    "entry_price": 2450.50,
    "mark_price": 2450.50,
    "liquidation_price": 1960.40,
    "liquidation_distance_percent": 20.0,
    "margin": "50.0",
    "notional_value": "250.05",
    "unrealized_pnl": "0.00",
    "unrealized_pnl_percent": 0.00,
    "funding_rate": 0.01,
    "next_funding": "2025-11-16T19:00:00Z",
    "opened_at": "2025-11-16T18:00:00Z",
    "warnings": [
      {
        "code": "HIGH_LEVERAGE",
        "message": "5x leverage. Liquidation at 20% price drop.",
        "severity": "high"
      }
    ]
  }
}
```

**Error Response (400 Bad Request):**
```json
{
  "success": false,
  "error": {
    "code": "LEVERAGE_TOO_HIGH",
    "message": "Leverage exceeds maximum allowed",
    "details": {
      "requested": 25.0,
      "maximum": 20.0,
      "symbol": "ETH-USD"
    },
    "timestamp": "2025-11-16T18:00:00Z",
    "request_id": "req_xyz789"
  }
}
```

**Database Operations:**
```sql
INSERT INTO hyperliquid_positions (
  user_id, wallet_id, symbol, side, leverage, size,
  entry_price, mark_price, liquidation_price, unrealized_pnl,
  realized_pnl, margin, funding_rate, status, hyperliquid_order_id,
  opened_at, created_at
) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 0, 0, ?, ?, 'open', ?, NOW(), NOW());
```

**External Dependencies:**
- Hyperliquid API

**Rate Limit:** 10 requests per minute

---

### 8.2 GET /perpetuals/positions

Get open perpetual positions.

**Endpoint:** `GET /api/v1/user/perpetuals/positions`

**Query Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `status` | string | Filter: 'open', 'closed', 'liquidated' |
| `symbol` | string | Filter by symbol |

**Success Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "positions": [
      {
        "id": 301,
        "symbol": "ETH-USD",
        "side": "long",
        "leverage": 5.0,
        "size": "0.102",
        "entry_price": 2450.50,
        "mark_price": 2460.00,
        "liquidation_price": 1960.40,
        "liquidation_distance_percent": 20.31,
        "margin": "50.0",
        "notional_value": "250.92",
        "unrealized_pnl": "0.969",
        "unrealized_pnl_percent": 1.94,
        "funding_rate": 0.01,
        "last_funding_payment": "-0.025",
        "total_funding_paid": "-0.050",
        "status": "open",
        "opened_at": "2025-11-16T18:00:00Z",
        "last_update": "2025-11-16T18:05:00Z"
      }
    ],
    "summary": {
      "total_positions": 1,
      "total_margin": "50.0",
      "total_notional": "250.92",
      "total_unrealized_pnl": "0.969",
      "total_unrealized_pnl_percent": 1.94
    }
  }
}
```

**Rate Limit:** 60 requests per minute

---

### 8.3 POST /perpetuals/positions/:id/close

Close perpetual position.

**Endpoint:** `POST /api/v1/user/perpetuals/positions/:id/close`

**Request:**
```http
POST /api/v1/user/perpetuals/positions/301/close HTTP/1.1
Host: api.anvil.com
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json

{
  "size": "0.102"
}
```

**Success Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "position_id": 301,
    "status": "closed",
    "size_closed": "0.102",
    "entry_price": 2450.50,
    "exit_price": 2460.00,
    "realized_pnl": "0.969",
    "realized_pnl_percent": 1.94,
    "margin_returned": "50.969",
    "total_fees": "0.125",
    "net_pnl": "0.844",
    "closed_at": "2025-11-16T18:10:00Z"
  }
}
```

**Rate Limit:** 10 requests per minute

---

## 9. AI Chat

Base path: `/api/v1/user/chat`

### 9.1 POST /chat/message

Send message to AI assistant.

**Endpoint:** `POST /api/v1/user/chat/message`

**Request:**
```http
POST /api/v1/user/chat/message HTTP/1.1
Host: api.anvil.com
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json

{
  "message": "What's my portfolio performance?",
  "session_id": "session_abc123",
  "context": {
    "include_portfolio": true,
    "include_market_data": false
  }
}
```

**Request Body Schema:**

| Field | Type | Required | Constraints | Description |
|-------|------|----------|-------------|-------------|
| `message` | string | ✅ Yes | 1-2000 chars | User's message |
| `session_id` | string | ✅ Yes | UUID | Session for continuity |
| `context.include_portfolio` | boolean | No | - | Include user portfolio |
| `context.include_market_data` | boolean | No | - | Include market prices |

**Success Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "message_id": 5678,
    "session_id": "session_abc123",
    "ai_response": "Your portfolio is performing well! Here's a summary:\n\n📊 Total Value: $120.35 (+1.27% today)\n\n💰 Your Holdings:\n• 50 USDC in Aave (earning 4.2% APY)\n• 0.0204 ETH ($50.35)\n• ETH-USD Long 5x ($50.97, +1.94% P&L)\n\nWould you like any specific recommendations?",
    "ai_metadata": {
      "model": "gemini-1.5-flash",
      "provider": "vertex",
      "tokens_input": 520,
      "tokens_output": 300,
      "tokens_total": 820,
      "cost_usd": 0.00005,
      "latency_ms": 1240
    },
    "recommendations": [
      {
        "id": 1,
        "action": "close_position",
        "title": "Take Profit on ETH Position",
        "description": "Lock in +$0.97 profit",
        "priority": "medium",
        "executable": true
      }
    ],
    "timestamp": "2025-11-16T18:15:00Z"
  }
}
```

**Error Response (429 Too Many Requests):**
```json
{
  "success": false,
  "error": {
    "code": "DAILY_LIMIT_REACHED",
    "message": "You've reached your daily limit of 10 conversations",
    "details": {
      "plan": "free",
      "limit": 10,
      "used": 10,
      "reset_at": "2025-11-17T00:00:00Z",
      "upgrade_available": true
    },
    "timestamp": "2025-11-16T18:15:00Z",
    "request_id": "req_xyz789"
  }
}
```

**Database Operations:**
```sql
-- Check daily limit
SELECT COUNT(*) as today_count
FROM llm_conversations
WHERE user_id = ? AND DATE(created_at) = CURDATE();

-- Log conversation
INSERT INTO llm_conversations (
  user_id, session_id, provider, model_name, prompt_text,
  response_text, input_tokens, output_tokens, cost_usd,
  latency_ms, status, created_at
) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'success', NOW());

-- Create agent execution
INSERT INTO agent_executions (
  user_id, conversation_id, agent_type, workflow_type, status,
  input_params, output_result, execution_time_ms, total_cost_usd,
  created_at
) VALUES (?, ?, 'research', 'analysis', 'completed', ?, ?, ?, ?, NOW());
```

**External Dependencies:**
- Vertex AI (primary LLM)
- AWS Bedrock (fallback)

**Rate Limit:**
- Free: 10 messages per day
- Pro: 20 messages per minute

---

### 9.2 GET /chat/history

Get chat conversation history.

**Endpoint:** `GET /api/v1/user/chat/history`

**Query Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `session_id` | string | Filter by session |
| `limit` | integer | Max messages (max: 100) |
| `date_from` | string | ISO date |
| `date_to` | string | ISO date |

**Success Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "conversations": [
      {
        "id": 5678,
        "session_id": "session_abc123",
        "user_message": "What's my portfolio performance?",
        "ai_response": "Your portfolio is performing well...",
        "timestamp": "2025-11-16T18:15:00Z"
      }
    ],
    "total": 1,
    "usage_summary": {
      "total_conversations_today": 5,
      "remaining_today": 5,
      "total_cost_today": 0.00025
    }
  }
}
```

**Rate Limit:** 60 requests per minute

---

## 10. Subscriptions

Base path: `/api/v1/user/subscription`

### 10.1 GET /subscription

Get subscription status.

**Endpoint:** `GET /api/v1/user/subscription`

**Success Response (200 OK) - Pro User:**
```json
{
  "success": true,
  "data": {
    "id": 501,
    "stripe_subscription_id": "sub_stripe456",
    "stripe_customer_id": "cus_stripe123",
    "plan": "pro",
    "status": "active",
    "price_monthly": 9.99,
    "billing_cycle_start": "2025-11-16T00:00:00Z",
    "billing_cycle_end": "2025-12-16T00:00:00Z",
    "trial_end": null,
    "cancel_at_period_end": false,
    "features": {
      "unlimited_conversations": true,
      "priority_support": true,
      "advanced_analytics": true,
      "early_access": true
    },
    "usage": {
      "conversations_today": 25,
      "conversations_this_month": 450
    },
    "next_billing_date": "2025-12-16T00:00:00Z",
    "next_billing_amount": 9.99
  }
}
```

**Success Response (200 OK) - Free User:**
```json
{
  "success": true,
  "data": {
    "plan": "free",
    "status": "active",
    "features": {
      "conversations_per_day": 10,
      "priority_support": false,
      "advanced_analytics": false
    },
    "usage": {
      "conversations_today": 5,
      "remaining_today": 5
    },
    "upgrade_available": true,
    "upgrade_benefits": [
      "Unlimited AI conversations",
      "Priority support",
      "Advanced analytics"
    ]
  }
}
```

**Rate Limit:** 60 requests per minute

---

### 10.2 POST /subscription/create-checkout

Create subscription checkout.

**Endpoint:** `POST /api/v1/user/subscription/create-checkout`

**Request:**
```http
POST /api/v1/user/subscription/create-checkout HTTP/1.1
Host: api.anvil.com
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json

{
  "plan": "pro",
  "trial_enabled": true
}
```

**Success Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "subscription_id": 501,
    "stripe_subscription_id": "sub_stripe456",
    "client_secret": "pi_secret_abc123",
    "status": "trialing",
    "trial_end": "2025-11-23T18:30:00Z",
    "trial_days": 7
  }
}
```

**External Dependencies:**
- Stripe API

**Rate Limit:** 10 requests per minute

---

### 10.3 POST /subscription/cancel

Cancel subscription.

**Endpoint:** `POST /api/v1/user/subscription/cancel`

**Request:**
```http
POST /api/v1/user/subscription/cancel HTTP/1.1
Host: api.anvil.com
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json

{
  "reason": "Too expensive",
  "feedback": "Would consider at $5/month"
}
```

**Success Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "subscription_id": 501,
    "status": "active",
    "cancel_at_period_end": true,
    "cancels_at": "2025-12-16T00:00:00Z",
    "access_until": "2025-12-16T00:00:00Z",
    "message": "Your subscription will remain active until December 16, 2025"
  }
}
```

**Rate Limit:** 10 requests per minute

---

## 11. Notifications

Base path: `/api/v1/user/notifications`

### 11.1 GET /notifications

Get user notifications.

**Endpoint:** `GET /api/v1/user/notifications`

**Query Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `unread_only` | boolean | Show only unread |
| `type` | string | Filter by type |
| `limit` | integer | Max results (max: 100) |
| `page` | integer | Page number |

**Success Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "notifications": [
      {
        "id": 1001,
        "type": "transaction_confirmed",
        "channel": "push",
        "title": "Swap Complete! ✅",
        "message": "You received 0.0204 ETH",
        "data": {
          "transaction_id": 789,
          "amount": "0.0204 ETH"
        },
        "status": "sent",
        "priority": "medium",
        "sent_at": "2025-11-16T18:30:00Z",
        "read_at": null,
        "created_at": "2025-11-16T18:30:00Z"
      }
    ],
    "unread_count": 1,
    "total": 1,
    "pagination": {
      "page": 1,
      "limit": 20,
      "total": 1,
      "has_next": false
    }
  }
}
```

**Rate Limit:** 60 requests per minute

---

### 11.2 POST /notifications/:id/read

Mark notification as read.

**Endpoint:** `POST /api/v1/user/notifications/:id/read`

**Success Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "notification_id": 1001,
    "read_at": "2025-11-16T18:35:00Z"
  }
}
```

**Rate Limit:** 60 requests per minute

---

### 11.3 POST /notifications/read-all

Mark all as read.

**Endpoint:** `POST /api/v1/user/notifications/read-all`

**Success Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "count": 5,
    "read_at": "2025-11-16T18:40:00Z"
  }
}
```

**Rate Limit:** 20 requests per minute

---

## 12. Funding

Base path: `/api/v1/user/funding`

### 12.1 POST /funding/create

Create funding transaction.

**Endpoint:** `POST /api/v1/user/funding/create`

**Request:**
```http
POST /api/v1/user/funding/create HTTP/1.1
Host: api.anvil.com
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json

{
  "amount_fiat": 103.70,
  "asset": "USDC",
  "chain": "arbitrum",
  "payment_method": "card"
}
```

**Success Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "funding_transaction_id": 789,
    "stripe_client_secret": "pi_stripe123_secret_abc",
    "amount_fiat": 103.70,
    "expected_crypto": 100.0,
    "asset": "USDC",
    "fees": {
      "stripe_fee": 3.20,
      "network_fee": 0.50,
      "total_fee": 3.70
    }
  }
}
```

**External Dependencies:**
- Stripe API

**Rate Limit:** 10 requests per minute

---

### 12.2 GET /funding/history

Get funding history.

**Endpoint:** `GET /api/v1/user/funding/history`

**Success Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "transactions": [
      {
        "id": 789,
        "amount_fiat": 103.70,
        "amount_crypto": 100.0,
        "asset": "USDC",
        "chain": "arbitrum",
        "payment_method": "card",
        "status": "completed",
        "transaction_hash": "0xabc123...",
        "completed_at": "2025-11-16T10:31:00Z",
        "created_at": "2025-11-16T10:30:00Z"
      }
    ],
    "summary": {
      "total_funded_usd": 103.70,
      "total_crypto_received": 100.0,
      "total_fees_paid": 3.70
    }
  }
}
```

**Rate Limit:** 60 requests per minute

---

**Document Status:** CLIENT API Complete (Part 1 + Part 2) ✅  
**Total Endpoints Documented:** 50+  
**Next:** ADMIN and AUDITOR API endpoints
