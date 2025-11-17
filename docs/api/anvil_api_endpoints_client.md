# 🔌 Anvil API Endpoints - CLIENT Users

## Base Information

**Base URL:** `https://api.anvil.com/v1/user`  
**Authentication:** Bearer JWT Token (from Privy)  
**Content-Type:** `application/json`  
**User Role Required:** `role=2` (CLIENT)

---

## Table of Contents

1. [Authentication](#authentication)
2. [User Profile](#user-profile)
3. [Wallet Management](#wallet-management)
4. [Transactions](#transactions)
5. [Trading (Swaps)](#trading-swaps)
6. [Perpetual Trading](#perpetual-trading)
7. [Earn (Yield Farming)](#earn-yield-farming)
8. [Auto-Save](#auto-save)
9. [Funding](#funding)
10. [Subscriptions](#subscriptions)
11. [AI Chat](#ai-chat)
12. [Notifications](#notifications)

---

## Authentication

### POST `/auth/privy`

**Description:** Exchange Privy authentication token for Anvil JWT token. Creates user account on first login.

**Authentication:** None (public endpoint)

**Request Headers:**
```http
Content-Type: application/json
```

**Request Body:**
```json
{
  "privy_token": "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJwcml2eSIsInN1YiI6ImRpZDpwcml2eTpjbGsxYWJjIiwiaWF0IjoxNzAwMDAwMDAwLCJleHAiOjE3MDAwMDM2MDB9...",
  "privy_user_id": "did:privy:clk1abc123def456"
}
```

**Response 200 OK:**
```json
{
  "success": true,
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NSIsInVzZXJfaWQiOjEyMzQ1LCJ1aWQiOiJ1c3JfYWJjMTIzIiwiZW1haWwiOiJ1c2VyQGV4YW1wbGUuY29tIiwicm9sZSI6MiwicHJpdnlfdXNlcl9pZCI6ImRpZDpwcml2eTpjbGsxYWJjIiwiaWF0IjoxNzAwMDAwMDAwLCJleHAiOjE3MDAwMDM2MDB9.signature",
    "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.refresh_token_payload.signature",
    "expires_in": 3600,
    "token_type": "Bearer",
    "user": {
      "id": 12345,
      "uid": "usr_abc123",
      "email": "user@example.com",
      "firstname": "John",
      "lastname": "Doe",
      "role": 2,
      "status": 1,
      "email_verified": true,
      "kyc_status": "approved",
      "privy_user_id": "did:privy:clk1abc123",
      "created_at": "2025-11-16T10:00:00Z",
      "last_login_at": "2025-11-16T15:30:00Z"
    },
    "wallet": {
      "id": 67890,
      "address": "0x1234567890abcdef1234567890abcdef12345678",
      "privy_wallet_id": "0xprivy123abc",
      "default_chain": "arbitrum",
      "status": 1
    }
  }
}
```

**Response 401 Unauthorized:**
```json
{
  "success": false,
  "error": {
    "code": "INVALID_PRIVY_TOKEN",
    "message": "Privy token is invalid or expired",
    "timestamp": "2025-11-16T15:30:00Z",
    "request_id": "req_xyz789"
  }
}
```

**Response 422 Unprocessable Entity:**
```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Request validation failed",
    "details": [
      {
        "field": "privy_token",
        "message": "privy_token is required"
      }
    ]
  }
}
```

---

### POST `/auth/refresh`

**Description:** Refresh expired access token using refresh token

**Authentication:** None (uses refresh token)

**Request Body:**
```json
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.refresh_payload.signature"
}
```

**Response 200 OK:**
```json
{
  "success": true,
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.new_payload.signature",
    "expires_in": 3600,
    "token_type": "Bearer"
  }
}
```

**Response 401 Unauthorized:**
```json
{
  "success": false,
  "error": {
    "code": "INVALID_REFRESH_TOKEN",
    "message": "Refresh token is invalid or expired"
  }
}
```

---

### POST `/auth/logout`

**Description:** Invalidate current access and refresh tokens

**Authentication:** Required (Bearer token)

**Request Headers:**
```http
Authorization: Bearer {access_token}
```

**Request Body:** None

**Response 200 OK:**
```json
{
  "success": true,
  "message": "Logged out successfully"
}
```

---

## User Profile

### GET `/profile`

**Description:** Get current user's profile information

**Authentication:** Required

**Request Headers:**
```http
Authorization: Bearer {access_token}
```

**Query Parameters:** None

**Response 200 OK:**
```json
{
  "success": true,
  "data": {
    "id": 12345,
    "uid": "usr_abc123",
    "email": "user@example.com",
    "firstname": "John",
    "lastname": "Doe",
    "phone": "+1234567890",
    "role": 2,
    "status": 1,
    "email_verified": true,
    "kyc_status": "approved",
    "kyc_completed_at": "2025-11-16T10:00:00Z",
    "terms_accepted_at": "2025-11-16T10:00:00Z",
    "created_at": "2025-11-16T10:00:00Z",
    "last_login_at": "2025-11-16T15:30:00Z",
    "last_active_at": "2025-11-16T15:45:00Z"
  }
}
```

---

### PATCH `/profile`

**Description:** Update user profile information

**Authentication:** Required

**Request Headers:**
```http
Authorization: Bearer {access_token}
Content-Type: application/json
```

**Request Body:**
```json
{
  "firstname": "John",
  "lastname": "Doe",
  "phone": "+1234567890"
}
```

**Response 200 OK:**
```json
{
  "success": true,
  "data": {
    "id": 12345,
    "firstname": "John",
    "lastname": "Doe",
    "phone": "+1234567890",
    "updated_at": "2025-11-16T15:50:00Z"
  }
}
```

**Response 400 Bad Request:**
```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid phone number format",
    "details": {
      "field": "phone",
      "value": "invalid_phone"
    }
  }
}
```

---

## Wallet Management

### GET `/wallet`

**Description:** Get user's primary wallet information

**Authentication:** Required

**Response 200 OK:**
```json
{
  "success": true,
  "data": {
    "id": 67890,
    "user_id": 12345,
    "address": "0x1234567890abcdef1234567890abcdef12345678",
    "privy_wallet_id": "0xprivy123abc",
    "provider": "privy",
    "default_chain": "arbitrum",
    "status": 1,
    "created_at": "2025-11-16T10:00:00Z"
  }
}
```

---

### GET `/wallet/balances`

**Description:** Get token balances across all supported chains

**Authentication:** Required

**Query Parameters:**
- `chain` (optional): Filter by specific chain (`arbitrum`, `base`, `hyperliquid`)
- `refresh` (optional, boolean): Force refresh from blockchain RPCs

**Response 200 OK:**
```json
{
  "success": true,
  "data": {
    "total_usd": 171.32,
    "last_updated": "2025-11-16T15:45:00Z",
    "chains": [
      {
        "chain": "arbitrum",
        "chain_id": 42161,
        "total_usd": 120.35,
        "balances": [
          {
            "asset": "ETH",
            "symbol": "ETH",
            "contract_address": "0x0000000000000000000000000000000000000000",
            "amount": "0.0204",
            "decimals": 18,
            "usd_value": 50.35,
            "price": 2467.00,
            "change_24h": 56.78,
            "change_24h_percent": 2.3
          },
          {
            "asset": "USDC",
            "symbol": "USDC",
            "contract_address": "0xaf88d065e77c8cC2239327C5EDb3A432268e5831",
            "amount": "70.0",
            "decimals": 6,
            "usd_value": 70.00,
            "price": 1.00,
            "change_24h": 0.0,
            "change_24h_percent": 0.0
          }
        ]
      },
      {
        "chain": "base",
        "chain_id": 8453,
        "total_usd": 0.00,
        "balances": []
      },
      {
        "chain": "hyperliquid",
        "chain_id": null,
        "total_usd": 50.97,
        "balances": [
          {
            "asset": "USDC",
            "symbol": "USDC",
            "amount": "50.97",
            "decimals": 6,
            "usd_value": 50.97,
            "price": 1.00
          }
        ]
      }
    ]
  }
}
```

---

### GET `/wallet/addresses`

**Description:** Get wallet addresses for all supported chains

**Authentication:** Required

**Response 200 OK:**
```json
{
  "success": true,
  "data": [
    {
      "id": 1,
      "chain": "arbitrum",
      "chain_id": 42161,
      "address": "0x1234567890abcdef1234567890abcdef12345678",
      "is_active": true,
      "balance_usd": 120.35,
      "last_balance_update": "2025-11-16T15:45:00Z",
      "created_at": "2025-11-16T10:00:00Z"
    },
    {
      "id": 2,
      "chain": "base",
      "chain_id": 8453,
      "address": "0x1234567890abcdef1234567890abcdef12345678",
      "is_active": true,
      "balance_usd": 0.00,
      "last_balance_update": "2025-11-16T15:45:00Z",
      "created_at": "2025-11-16T10:00:00Z"
    },
    {
      "id": 3,
      "chain": "hyperliquid",
      "chain_id": null,
      "address": "hype1234567890abcdef",
      "is_active": true,
      "balance_usd": 50.97,
      "last_balance_update": "2025-11-16T15:45:00Z",
      "created_at": "2025-11-16T10:00:00Z"
    }
  ]
}
```

---

### POST `/wallet/refresh-balances`

**Description:** Force refresh balances from blockchain RPCs

**Authentication:** Required

**Request Body:**
```json
{
  "chains": ["arbitrum", "base"]
}
```

**Response 200 OK:**
```json
{
  "success": true,
  "data": {
    "refreshed_at": "2025-11-16T15:50:00Z",
    "total_usd": 171.32,
    "chains_refreshed": ["arbitrum", "base"]
  }
}
```

---

## Transactions

### GET `/transactions`

**Description:** Get user's transaction history with filtering and pagination

**Authentication:** Required

**Query Parameters:**
- `page` (default: 1): Page number
- `limit` (default: 20, max: 100): Items per page
- `type` (optional): Filter by type (0=SWAP, 1=FUND, 2=EARN, 3=SAVE, 4=SUBSCRIPTION)
- `status` (optional): Filter by status (0=PENDING, 1=SUCCESS, 2=FAILED)
- `chain` (optional): Filter by chain (`arbitrum`, `base`, `hyperliquid`)
- `date_from` (optional): ISO date string (e.g., `2025-11-01`)
- `date_to` (optional): ISO date string (e.g., `2025-11-30`)

**Response 200 OK:**
```json
{
  "success": true,
  "data": {
    "transactions": [
      {
        "id": 789,
        "type": 0,
        "type_label": "SWAP",
        "chain": "arbitrum",
        "asset_in": "USDC",
        "amount_in": "50.0",
        "asset_out": "ETH",
        "amount_out": "0.0204",
        "fee": "0.00015",
        "fee_usd": 0.37,
        "tx_hash": "0xabc123def456789...",
        "status": 1,
        "status_label": "SUCCESS",
        "dex_aggregator": "1inch",
        "dex_route": {
          "protocol": "1inch",
          "route": [
            {
              "pool": "Uniswap V3",
              "percentage": 100
            }
          ]
        },
        "slippage": 0.5,
        "block_number": 12345678,
        "confirmed_at": "2025-11-16T14:30:00Z",
        "created_at": "2025-11-16T14:29:30Z"
      },
      {
        "id": 788,
        "type": 1,
        "type_label": "FUND",
        "chain": "arbitrum",
        "asset_in": "USD",
        "amount_in": "103.70",
        "asset_out": "USDC",
        "amount_out": "100.0",
        "fee": "0.0005",
        "fee_usd": 0.50,
        "tx_hash": "0xdef456abc123...",
        "status": 1,
        "status_label": "SUCCESS",
        "dex_aggregator": null,
        "confirmed_at": "2025-11-16T13:15:00Z",
        "created_at": "2025-11-16T13:10:00Z"
      }
    ],
    "pagination": {
      "page": 1,
      "limit": 20,
      "total": 45,
      "pages": 3
    },
    "summary": {
      "total_transactions": 45,
      "total_volume_usd": 2345.67,
      "success_rate": 97.8
    }
  }
}
```

---

### GET `/transactions/:id`

**Description:** Get detailed information about a specific transaction

**Authentication:** Required

**Path Parameters:**
- `id`: Transaction ID

**Response 200 OK:**
```json
{
  "success": true,
  "data": {
    "id": 789,
    "type": 0,
    "type_label": "SWAP",
    "chain": "arbitrum",
    "asset_in": "USDC",
    "amount_in": "50.0",
    "asset_out": "ETH",
    "amount_out": "0.0204",
    "fee": "0.00015",
    "fee_usd": 0.37,
    "tx_hash": "0xabc123def456789...",
    "status": 1,
    "status_label": "SUCCESS",
    "dex_aggregator": "1inch",
    "dex_route": {
      "protocol": "1inch",
      "route": [
        {
          "pool": "Uniswap V3",
          "tokenIn": "USDC",
          "tokenOut": "ETH",
          "percentage": 100
        }
      ],
      "estimatedGas": "150000",
      "priceImpact": "0.12"
    },
    "slippage": 0.5,
    "block_number": 12345678,
    "block_explorer_url": "https://arbiscan.io/tx/0xabc123def456789...",
    "confirmed_at": "2025-11-16T14:30:00Z",
    "created_at": "2025-11-16T14:29:30Z",
    "wallet": {
      "address": "0x1234567890abcdef1234567890abcdef12345678"
    }
  }
}
```

**Response 404 Not Found:**
```json
{
  "success": false,
  "error": {
    "code": "TRANSACTION_NOT_FOUND",
    "message": "Transaction not found or does not belong to this user"
  }
}
```

---

## Trading (Swaps)

### POST `/trade/quote`

**Description:** Get a quote for swapping tokens (no execution)

**Authentication:** Required

**Request Body:**
```json
{
  "from_asset": "USDC",
  "from_amount": "50",
  "to_asset": "ETH",
  "chain": "arbitrum",
  "slippage": 0.5
}
```

**Response 200 OK:**
```json
{
  "success": true,
  "data": {
    "quote_id": "quote_abc123",
    "from_asset": "USDC",
    "from_amount": "50.0",
    "to_asset": "ETH",
    "to_amount": "0.0204",
    "to_amount_min": "0.0203",
    "rate": "1 USDC = 0.000408 ETH",
    "price_per_unit": 2450.00,
    "slippage": 0.5,
    "price_impact": 0.12,
    "estimated_gas": "150000",
    "estimated_gas_usd": 0.37,
    "dex_aggregator": "1inch",
    "dex_route": [
      {
        "protocol": "Uniswap V3",
        "pool": "USDC-ETH-0.3%",
        "percentage": 100
      }
    ],
    "expires_at": "2025-11-16T14:35:00Z",
    "created_at": "2025-11-16T14:30:00Z"
  }
}
```

**Response 400 Bad Request:**
```json
{
  "success": false,
  "error": {
    "code": "INSUFFICIENT_BALANCE",
    "message": "Insufficient USDC balance. Required: 50, Available: 30"
  }
}
```

---

### POST `/trade/swap`

**Description:** Execute a token swap

**Authentication:** Required

**Request Body:**
```json
{
  "quote_id": "quote_abc123",
  "from_asset": "USDC",
  "from_amount": "50",
  "to_asset": "ETH",
  "to_amount_min": "0.0203",
  "chain": "arbitrum",
  "slippage": 0.5,
  "dex_aggregator": "1inch"
}
```

**Response 200 OK:**
```json
{
  "success": true,
  "data": {
    "transaction_id": 789,
    "tx_hash": "0xabc123def456789...",
    "status": "pending",
    "from_asset": "USDC",
    "from_amount": "50.0",
    "to_asset": "ETH",
    "to_amount_expected": "0.0204",
    "estimated_time": "30 seconds",
    "created_at": "2025-11-16T14:30:00Z"
  }
}
```

**Response 400 Bad Request:**
```json
{
  "success": false,
  "error": {
    "code": "QUOTE_EXPIRED",
    "message": "Quote has expired. Please request a new quote."
  }
}
```

**Response 422 Unprocessable Entity:**
```json
{
  "success": false,
  "error": {
    "code": "SLIPPAGE_EXCEEDED",
    "message": "Current price would result in 1.2% slippage, which exceeds your 0.5% tolerance. Please adjust slippage or request new quote."
  }
}
```

---

## Perpetual Trading

### GET `/perpetuals/markets`

**Description:** Get available perpetual markets on Hyperliquid

**Authentication:** Required

**Response 200 OK:**
```json
{
  "success": true,
  "data": {
    "markets": [
      {
        "symbol": "ETH-USD",
        "base_asset": "ETH",
        "quote_asset": "USD",
        "mark_price": 2450.00,
        "index_price": 2449.50,
        "funding_rate": 0.01,
        "open_interest": "1234567.89",
        "volume_24h": "98765432.10",
        "change_24h": 2.3,
        "min_order_size": "0.01",
        "max_leverage": 20,
        "is_active": true
      },
      {
        "symbol": "BTC-USD",
        "base_asset": "BTC",
        "quote_asset": "USD",
        "mark_price": 43250.00,
        "index_price": 43245.00,
        "funding_rate": 0.008,
        "open_interest": "9876543.21",
        "volume_24h": "567890123.45",
        "change_24h": 1.8,
        "min_order_size": "0.001",
        "max_leverage": 20,
        "is_active": true
      }
    ]
  }
}
```

---

### POST `/perpetuals/positions/open`

**Description:** Open a new perpetual position

**Authentication:** Required

**Request Body:**
```json
{
  "symbol": "ETH-USD",
  "side": "long",
  "leverage": 5.0,
  "margin": "50",
  "size": "0.102"
}
```

**Response 200 OK:**
```json
{
  "success": true,
  "data": {
    "position_id": 301,
    "symbol": "ETH-USD",
    "side": "long",
    "leverage": 5.0,
    "size": "0.102",
    "entry_price": 2450.50,
    "mark_price": 2450.50,
    "liquidation_price": 1960.40,
    "margin": "50.0",
    "notional_value": "250.00",
    "unrealized_pnl": "0.00",
    "status": "open",
    "hyperliquid_order_id": "hyperliquid_order_123",
    "opened_at": "2025-11-16T15:00:00Z"
  }
}
```

**Response 400 Bad Request:**
```json
{
  "success": false,
  "error": {
    "code": "INSUFFICIENT_MARGIN",
    "message": "Insufficient margin. Required: 50 USDC, Available: 30 USDC"
  }
}
```

---

### GET `/perpetuals/positions`

**Description:** Get user's open and closed perpetual positions

**Authentication:** Required

**Query Parameters:**
- `status` (optional): `open`, `closed`, `liquidated`
- `symbol` (optional): Filter by symbol (e.g., `ETH-USD`)

**Response 200 OK:**
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
        "margin": "50.0",
        "notional_value": "250.92",
        "unrealized_pnl": "0.969",
        "unrealized_pnl_percent": 1.94,
        "funding_rate": 0.01,
        "distance_to_liquidation_percent": 20.31,
        "status": "open",
        "opened_at": "2025-11-16T15:00:00Z"
      }
    ],
    "summary": {
      "total_positions": 1,
      "total_margin": "50.0",
      "total_notional": "250.92",
      "total_unrealized_pnl": "0.969"
    }
  }
}
```

---

### POST `/perpetuals/positions/:id/close`

**Description:** Close a perpetual position

**Authentication:** Required

**Path Parameters:**
- `id`: Position ID

**Request Body:**
```json
{
  "percentage": 100
}
```

**Response 200 OK:**
```json
{
  "success": true,
  "data": {
    "position_id": 301,
    "symbol": "ETH-USD",
    "side": "long",
    "size_closed": "0.102",
    "exit_price": 2465.00,
    "realized_pnl": "1.479",
    "realized_pnl_percent": 2.96,
    "status": "closed",
    "closed_at": "2025-11-16T16:00:00Z"
  }
}
```

---

## Earn (Yield Farming)

### GET `/earn/opportunities`

**Description:** Get available yield farming opportunities

**Authentication:** Required

**Query Parameters:**
- `chain` (optional): Filter by chain
- `protocol` (optional): Filter by protocol
- `min_apy` (optional): Minimum APY filter

**Response 200 OK:**
```json
{
  "success": true,
  "data": {
    "opportunities": [
      {
        "protocol": "aave",
        "protocol_name": "Aave V3",
        "chain": "arbitrum",
        "asset": "USDC",
        "apy": 4.2,
        "apy_30d_avg": 4.0,
        "tvl": "125000000",
        "risk_score": "low",
        "description": "Lend USDC on Aave and earn interest",
        "min_deposit": "0.01",
        "is_active": true
      },
      {
        "protocol": "compound",
        "protocol_name": "Compound V3",
        "chain": "arbitrum",
        "asset": "USDT",
        "apy": 5.8,
        "apy_30d_avg": 5.5,
        "tvl": "89000000",
        "risk_score": "low",
        "description": "Supply USDT to Compound",
        "min_deposit": "0.01",
        "is_active": true
      }
    ]
  }
}
```

---

### POST `/earn/deposit`

**Description:** Deposit assets to earn yield

**Authentication:** Required

**Request Body:**
```json
{
  "protocol": "aave",
  "asset": "USDC",
  "amount": "50",
  "chain": "arbitrum"
}
```

**Response 200 OK:**
```json
{
  "success": true,
  "data": {
    "position_id": 101,
    "protocol": "aave",
    "asset": "USDC",
    "amount_deposited": "50.0",
    "current_value": "50.0",
    "apy": 4.2,
    "estimated_daily_earnings": "0.0057",
    "estimated_annual_earnings": "2.10",
    "tx_hash": "0xearn123abc...",
    "status": "pending",
    "deposited_at": "2025-11-16T15:30:00Z"
  }
}
```

---

### GET `/earn/positions`

**Description:** Get user's active and past earn positions

**Authentication:** Required

**Query Parameters:**
- `status` (optional): `active`, `withdrawn`, `emergency_exit`
- `protocol` (optional): Filter by protocol

**Response 200 OK:**
```json
{
  "success": true,
  "data": {
    "positions": [
      {
        "id": 101,
        "protocol": "aave",
        "chain": "arbitrum",
        "asset": "USDC",
        "amount_deposited": "70.0",
        "current_value": "70.06",
        "apy": 4.2,
        "current_apy": 4.3,
        "rewards_earned": "0.06",
        "rewards_earned_usd": "0.06",
        "status": "active",
        "days_active": 3,
        "estimated_annual_return": "3.01",
        "deposit_tx_hash": "0xearn123...",
        "deposited_at": "2025-11-13T15:30:00Z"
      }
    ],
    "summary": {
      "total_deposited": "70.0",
      "total_current_value": "70.06",
      "total_rewards_earned": "0.06",
      "weighted_avg_apy": 4.3
    }
  }
}
```

---

### POST `/earn/withdraw`

**Description:** Withdraw from an earn position

**Authentication:** Required

**Request Body:**
```json
{
  "position_id": 101,
  "amount": "70.06"
}
```

**Response 200 OK:**
```json
{
  "success": true,
  "data": {
    "position_id": 101,
    "amount_withdrawn": "70.06",
    "rewards_earned": "0.06",
    "tx_hash": "0xwithdraw123...",
    "status": "pending",
    "withdrawn_at": "2025-11-16T16:00:00Z"
  }
}
```

---

## Auto-Save

### POST `/save/schedule`

**Description:** Create a new recurring savings schedule

**Authentication:** Required

**Request Body:**
```json
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

**Response 200 OK:**
```json
{
  "success": true,
  "data": {
    "schedule_id": 201,
    "asset": "USDC",
    "amount": "20",
    "frequency": "weekly",
    "day_of_week": 1,
    "day_of_week_label": "Monday",
    "destination_protocol": "aave",
    "chain": "arbitrum",
    "status": "active",
    "next_execution_at": "2025-11-18T00:00:00Z",
    "total_saved": "0",
    "execution_count": 0,
    "max_executions": null,
    "created_at": "2025-11-16T16:00:00Z"
  }
}
```

---

### GET `/save/schedules`

**Description:** Get user's auto-save schedules

**Authentication:** Required

**Query Parameters:**
- `status` (optional): `active`, `paused`, `completed`, `failed`

**Response 200 OK:**
```json
{
  "success": true,
  "data": {
    "schedules": [
      {
        "id": 201,
        "asset": "USDC",
        "amount": "20",
        "frequency": "weekly",
        "day_of_week": 1,
        "destination_protocol": "aave",
        "chain": "arbitrum",
        "status": "active",
        "next_execution_at": "2025-11-18T00:00:00Z",
        "last_execution_at": null,
        "total_saved": "0",
        "execution_count": 0,
        "max_executions": null,
        "created_at": "2025-11-16T16:00:00Z"
      }
    ],
    "summary": {
      "total_schedules": 1,
      "active_schedules": 1,
      "total_saved_all_time": "0"
    }
  }
}
```

---

### PATCH `/save/schedules/:id`

**Description:** Update or pause a savings schedule

**Authentication:** Required

**Path Parameters:**
- `id`: Schedule ID

**Request Body:**
```json
{
  "status": "paused"
}
```

**Response 200 OK:**
```json
{
  "success": true,
  "data": {
    "schedule_id": 201,
    "status": "paused",
    "updated_at": "2025-11-16T16:10:00Z"
  }
}
```

---

### DELETE `/save/schedules/:id`

**Description:** Delete a savings schedule

**Authentication:** Required

**Path Parameters:**
- `id`: Schedule ID

**Response 200 OK:**
```json
{
  "success": true,
  "message": "Schedule deleted successfully"
}
```

---

## Funding

### POST `/funding/create`

**Description:** Create a funding transaction (fiat to crypto)

**Authentication:** Required

**Request Body:**
```json
{
  "amount_fiat": 103.70,
  "asset": "USDC",
  "chain": "arbitrum",
  "payment_method": "card"
}
```

**Response 200 OK:**
```json
{
  "success": true,
  "data": {
    "funding_transaction_id": 789,
    "stripe_client_secret": "pi_stripe123_secret_abc",
    "amount_fiat": 103.70,
    "expected_crypto": 100.0,
    "asset": "USDC",
    "chain": "arbitrum",
    "fees": {
      "stripe_fee": 3.20,
      "network_fee": 0.50,
      "total_fee": 3.70
    },
    "status": "pending"
  }
}
```

---

### GET `/funding/transactions`

**Description:** Get user's funding transaction history

**Authentication:** Required

**Query Parameters:**
- `page` (default: 1)
- `limit` (default: 20)
- `status` (optional): `pending`, `processing`, `completed`, `failed`, `refunded`

**Response 200 OK:**
```json
{
  "success": true,
  "data": {
    "transactions": [
      {
        "id": 789,
        "stripe_payment_intent_id": "pi_stripe123",
        "amount_fiat": 103.70,
        "amount_crypto": 100.0,
        "asset": "USDC",
        "chain": "arbitrum",
        "payment_method": "card",
        "status": "completed",
        "fee_stripe": 3.20,
        "fee_network": 0.50,
        "transaction_hash": "0xfund123...",
        "completed_at": "2025-11-16T14:00:00Z",
        "created_at": "2025-11-16T13:55:00Z"
      }
    ],
    "pagination": {
      "page": 1,
      "limit": 20,
      "total": 5
    }
  }
}
```

---

## Subscriptions

### GET `/subscription`

**Description:** Get user's subscription details

**Authentication:** Required

**Response 200 OK:**
```json
{
  "success": true,
  "data": {
    "id": 501,
    "stripe_subscription_id": "sub_stripe456",
    "plan": "pro",
    "plan_name": "Anvil Pro",
    "status": "active",
    "price_monthly": 9.99,
    "billing_cycle_start": "2025-11-16T00:00:00Z",
    "billing_cycle_end": "2025-12-16T00:00:00Z",
    "trial_end": null,
    "cancel_at_period_end": false,
    "current_period_end": "2025-12-16T00:00:00Z",
    "created_at": "2025-11-16T10:00:00Z"
  }
}
```

**Response 404 Not Found:**
```json
{
  "success": false,
  "error": {
    "code": "NO_SUBSCRIPTION",
    "message": "User does not have an active subscription"
  }
}
```

---

### POST `/subscription/create-checkout`

**Description:** Create Stripe checkout session for subscription

**Authentication:** Required

**Request Body:**
```json
{
  "plan": "pro",
  "trial_enabled": true
}
```

**Response 200 OK:**
```json
{
  "success": true,
  "data": {
    "subscription_id": 501,
    "stripe_subscription_id": "sub_stripe456",
    "client_secret": "pi_secret_abc123",
    "status": "trialing",
    "trial_end": "2025-11-23T00:00:00Z",
    "plan": "pro",
    "price_monthly": 9.99
  }
}
```

---

### POST `/subscription/cancel`

**Description:** Cancel subscription at end of billing period

**Authentication:** Required

**Request Body:**
```json
{
  "feedback": "Too expensive for my needs"
}
```

**Response 200 OK:**
```json
{
  "success": true,
  "data": {
    "subscription_id": 501,
    "status": "active",
    "cancel_at_period_end": true,
    "canceled_at": "2025-11-16T16:30:00Z",
    "period_end": "2025-12-16T00:00:00Z",
    "message": "Your subscription will remain active until 2025-12-16"
  }
}
```

---

### GET `/subscription/payments`

**Description:** Get subscription payment history

**Authentication:** Required

**Response 200 OK:**
```json
{
  "success": true,
  "data": {
    "payments": [
      {
        "id": 1001,
        "stripe_invoice_id": "inv_stripe789",
        "amount": 9.99,
        "status": "paid",
        "billing_reason": "subscription_cycle",
        "payment_method": "card",
        "paid_at": "2025-11-16T00:00:00Z",
        "created_at": "2025-11-16T00:00:00Z"
      }
    ]
  }
}
```

---

## AI Chat

### POST `/chat/message`

**Description:** Send a message to AI assistant and get response

**Authentication:** Required

**Request Body:**
```json
{
  "message": "Based on my portfolio, what should I invest in next?",
  "session_id": "session_abc123",
  "context": {
    "include_portfolio": true,
    "include_market_data": true
  }
}
```

**Response 200 OK:**
```json
{
  "success": true,
  "data": {
    "conversation_id": 5678,
    "session_id": "session_abc123",
    "ai_response": "Great question! I've analyzed your portfolio and here's what I found:\n\n📊 Current Portfolio:\n• Total value: $171.32\n• ETH exposure: 82% (including perpetual) ⚠️ High!\n...",
    "agent_execution_id": 1234,
    "recommendations": [
      {
        "id": 1,
        "action": "close_position",
        "title": "Close ETH Perpetual",
        "description": "Lock in +$0.97 profit",
        "priority": "high",
        "estimated_outcome": "+$0.97",
        "executable": true
      }
    ],
    "cost_usd": 0.00012,
    "latency_ms": 2340,
    "tokens_used": {
      "input": 1850,
      "output": 650,
      "total": 2500
    },
    "model": {
      "provider": "vertex",
      "model_name": "gemini-1.5-flash"
    },
    "created_at": "2025-11-16T16:00:00Z"
  }
}
```

**Response 429 Too Many Requests:**
```json
{
  "success": false,
  "error": {
    "code": "DAILY_LIMIT_REACHED",
    "message": "You've reached your daily limit of 10 conversations. Upgrade to Pro for unlimited conversations.",
    "current_plan": "free",
    "daily_limit": 10,
    "messages_used": 10,
    "upgrade_url": "/subscription/create-checkout"
  }
}
```

---

### GET `/chat/history`

**Description:** Get chat conversation history

**Authentication:** Required

**Query Parameters:**
- `session_id` (optional): Filter by session
- `limit` (default: 50): Number of messages

**Response 200 OK:**
```json
{
  "success": true,
  "data": {
    "conversations": [
      {
        "id": 5678,
        "session_id": "session_abc123",
        "prompt": "Based on my portfolio, what should I invest in next?",
        "response": "Great question! I've analyzed your portfolio...",
        "cost_usd": 0.00012,
        "created_at": "2025-11-16T16:00:00Z"
      }
    ],
    "summary": {
      "total_conversations": 15,
      "total_cost_usd": 0.0018
    }
  }
}
```

---

## Notifications

### GET `/notifications`

**Description:** Get user's notifications

**Authentication:** Required

**Query Parameters:**
- `status` (optional): `sent`, `read`, `pending`
- `type` (optional): Notification type
- `limit` (default: 50)

**Response 200 OK:**
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
        "sent_at": "2025-11-16T14:30:30Z",
        "read_at": null,
        "created_at": "2025-11-16T14:30:00Z"
      },
      {
        "id": 1002,
        "type": "liquidation_warning",
        "channel": "push",
        "title": "⚠️ LIQUIDATION WARNING",
        "message": "Your ETH-USD position is 6% from liquidation",
        "data": {
          "position_id": 301,
          "symbol": "ETH-USD",
          "distance_percent": 6.0
        },
        "status": "read",
        "priority": "urgent",
        "sent_at": "2025-11-16T15:00:00Z",
        "read_at": "2025-11-16T15:01:00Z",
        "created_at": "2025-11-16T15:00:00Z"
      }
    ],
    "unread_count": 3
  }
}
```

---

### PATCH `/notifications/:id/read`

**Description:** Mark notification as read

**Authentication:** Required

**Path Parameters:**
- `id`: Notification ID

**Response 200 OK:**
```json
{
  "success": true,
  "data": {
    "notification_id": 1001,
    "status": "read",
    "read_at": "2025-11-16T16:30:00Z"
  }
}
```

---

### POST `/notifications/mark-all-read`

**Description:** Mark all notifications as read

**Authentication:** Required

**Response 200 OK:**
```json
{
  "success": true,
  "data": {
    "marked_read": 5,
    "message": "All notifications marked as read"
  }
}
```

---

## Dashboard

### GET `/dashboard`

**Description:** Get complete dashboard data (portfolio, positions, activity)

**Authentication:** Required

**Response 200 OK:**
```json
{
  "success": true,
  "data": {
    "summary": {
      "total_value_usd": 171.32,
      "change_24h_usd": 2.14,
      "change_24h_percent": 1.27,
      "all_time_pnl": 21.32,
      "all_time_pnl_percent": 14.21
    },
    "balances": {
      "arbitrum": {
        "total_usd": 120.35,
        "assets": [
          {
            "asset": "ETH",
            "amount": "0.0204",
            "usd_value": 50.35
          },
          {
            "asset": "USDC",
            "amount": "70.0",
            "usd_value": 70.00
          }
        ]
      },
      "hyperliquid": {
        "total_usd": 50.97,
        "assets": []
      }
    },
    "earn_positions": [
      {
        "protocol": "aave",
        "asset": "USDC",
        "value": 70.06,
        "rewards": 0.06,
        "apy": 4.2
      }
    ],
    "perp_positions": [
      {
        "symbol": "ETH-USD",
        "side": "long",
        "value": 50.97,
        "pnl": 0.97,
        "pnl_percent": 1.94
      }
    ],
    "recent_activity": [
      {
        "type": "position_opened",
        "description": "ETH-USD Long 5x",
        "time": "2 hours ago"
      },
      {
        "type": "earn_deposit",
        "description": "Deposited 50 USDC to Aave",
        "time": "5 hours ago"
      }
    ]
  }
}
```

---

## Error Responses

### Standard Error Format

All errors follow this format:

```json
{
  "success": false,
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable error message",
    "details": {},
    "timestamp": "2025-11-16T16:00:00Z",
    "request_id": "req_xyz789"
  }
}
```

### Common Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `INVALID_TOKEN` | 401 | JWT token is invalid or expired |
| `UNAUTHORIZED` | 401 | User not authenticated |
| `FORBIDDEN` | 403 | User lacks required permissions |
| `NOT_FOUND` | 404 | Resource not found |
| `VALIDATION_ERROR` | 422 | Request validation failed |
| `INSUFFICIENT_BALANCE` | 400 | Insufficient balance for operation |
| `RATE_LIMIT_EXCEEDED` | 429 | Too many requests |
| `INTERNAL_ERROR` | 500 | Internal server error |

---

## Rate Limits

**Per User:**
- General endpoints: 100 requests/minute
- Chat endpoints: 20 messages/minute
- Trading endpoints: 10 trades/minute
- Auth endpoints: 5 attempts/minute per IP

**Headers Returned:**
```http
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1700000060
```

---

## Webhooks (Optional)

Users can configure webhook URLs to receive real-time notifications:

**Events:**
- `transaction.confirmed`
- `transaction.failed`
- `position.liquidation_warning`
- `earn.deposit_completed`
- `subscription.renewed`

**Webhook Payload Format:**
```json
{
  "event": "transaction.confirmed",
  "data": {
    "transaction_id": 789,
    "user_id": 12345,
    "type": "SWAP",
    "amount": "50 USDC → 0.0204 ETH"
  },
  "timestamp": "2025-11-16T14:30:00Z"
}
```

---

**Total CLIENT Endpoints:** 50+  
**Authentication:** JWT Bearer Token  
**API Version:** v1  
**Documentation Status:** Production Ready ✅
