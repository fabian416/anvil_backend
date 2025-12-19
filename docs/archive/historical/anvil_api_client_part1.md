# 🔌 Anvil API - CLIENT Endpoints Part 1

## Overview

**Base URL:** `https://api.anvil.com/v1`  
**User Type:** CLIENT (role=2)  
**Platform:** Mobile App (iOS/Android)  
**Authentication:** JWT Bearer Token  
**Content-Type:** `application/json`  
**API Version:** v1.0

---

## Table of Contents - Part 1

1. [Authentication](#1-authentication)
2. [User Profile](#2-user-profile)
3. [Wallet Operations](#3-wallet-operations)
4. [Transactions](#4-transactions)

---

## 1. Authentication

Base path: `/api/v1/user/auth`

### 1.1 POST /auth/privy

Exchange Privy authentication token for Anvil JWT.

**Endpoint:** `POST /api/v1/user/auth/privy`

**Authentication:** None (public endpoint)

**Request:**
```http
POST /api/v1/user/auth/privy HTTP/1.1
Host: api.anvil.com
Content-Type: application/json

{
  "privy_token": "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJkaWQ6cHJpdnk6Y2xrMWFiYzEyMyIsImVtYWlsIjoidXNlckBlbWFpbC5jb20iLCJpYXQiOjE2OTk4NzY1NDMsImV4cCI6MTY5OTg4MDE0M30.signature",
  "privy_user_id": "did:privy:clk1abc123def456"
}
```

**Request Body Schema:**

| Field | Type | Required | Constraints | Description |
|-------|------|----------|-------------|-------------|
| `privy_token` | string | ✅ Yes | Valid JWT | Privy authentication token |
| `privy_user_id` | string | ✅ Yes | DID format | Privy user identifier starting with "did:privy:" |

**Success Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NSIsInVzZXJfaWQiOjEyMzQ1LCJ1aWQiOiJ1c3JfYWJjMTIzIiwiZW1haWwiOiJ1c2VyQGVtYWlsLmNvbSIsInJvbGUiOjIsInByaXZ5X3VzZXJfaWQiOiJkaWQ6cHJpdnk6Y2xrMSIsImlhdCI6MTY5OTg3NjU0MywiZXhwIjoxNjk5ODgwMTQzfQ.signature",
    "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NSIsInR5cGUiOiJyZWZyZXNoIiwiaWF0IjoxNjk5ODc2NTQzLCJleHAiOjE3MDI0Njg1NDN9.signature",
    "expires_in": 3600,
    "token_type": "Bearer",
    "user": {
      "id": 12345,
      "uid": "usr_abc123def456",
      "email": "user@email.com",
      "firstname": "John",
      "lastname": "Doe",
      "role": 2,
      "status": 1,
      "privy_user_id": "did:privy:clk1abc123",
      "email_verified": true,
      "kyc_status": "none",
      "created_at": "2025-01-15T10:30:00Z",
      "last_login_at": "2025-11-16T14:20:00Z"
    },
    "wallet": {
      "id": 67890,
      "address": "0x1234567890abcdef1234567890abcdef12345678",
      "privy_wallet_id": "0xabc123def456",
      "default_chain": "arbitrum",
      "status": 1,
      "created_at": "2025-01-15T10:30:00Z"
    }
  }
}
```

**Response Fields:**

| Field | Type | Description |
|-------|------|-------------|
| `access_token` | string | JWT token for API requests (expires in 1 hour) |
| `refresh_token` | string | Token to obtain new access token (expires in 30 days) |
| `expires_in` | integer | Access token TTL in seconds (3600) |
| `token_type` | string | Always "Bearer" |
| `user.id` | integer | Internal user ID |
| `user.uid` | string | External UUID for user |
| `user.email` | string | User's email address |
| `user.role` | integer | Always 2 for CLIENT users |
| `user.status` | integer | 0=INACTIVE, 1=ACTIVE, 2=DELETED |
| `user.kyc_status` | string | 'none', 'pending', 'approved', 'rejected' |
| `wallet.address` | string | Ethereum-compatible wallet address |
| `wallet.default_chain` | string | Default blockchain for operations |

**Error Response (401 Unauthorized):**
```json
{
  "success": false,
  "error": {
    "code": "INVALID_PRIVY_TOKEN",
    "message": "Privy token is invalid or expired",
    "details": {
      "token_expired": true,
      "expired_at": "2025-11-16T13:00:00Z"
    },
    "timestamp": "2025-11-16T14:20:00Z",
    "request_id": "req_xyz789abc123"
  }
}
```

**Error Response (403 Forbidden):**
```json
{
  "success": false,
  "error": {
    "code": "ACCOUNT_SUSPENDED",
    "message": "This account has been suspended. Please contact support.",
    "details": {
      "suspension_reason": "Terms of Service violation",
      "suspended_at": "2025-11-15T10:00:00Z",
      "support_email": "support@anvil.com"
    },
    "timestamp": "2025-11-16T14:20:00Z",
    "request_id": "req_xyz789abc123"
  }
}
```

**Error Codes:**

| Code | HTTP Status | Description | Retry |
|------|-------------|-------------|-------|
| `INVALID_PRIVY_TOKEN` | 401 | Token invalid/expired/malformed | No |
| `PRIVY_USER_NOT_FOUND` | 404 | Privy user ID doesn't exist | No |
| `ACCOUNT_SUSPENDED` | 403 | User account suspended | No |
| `PRIVY_SERVICE_ERROR` | 503 | Privy API unavailable | Yes (backoff) |
| `SERVER_ERROR` | 500 | Internal server error | Yes (backoff) |

**Business Logic:**
1. Validates Privy token signature and expiry
2. Calls Privy API to verify user and get wallet details
3. Checks if user exists in Anvil database
4. **If first login:**
   - Creates user record (status=0, INACTIVE initially)
   - Creates wallet record via Privy embedded wallet
   - Creates 3 chain_addresses (Arbitrum, Base, Hyperliquid)
   - Sets user status to 1 (ACTIVE)
5. **If existing user:**
   - Updates `last_login_at` timestamp
6. Generates Anvil JWT with 1-hour expiry
7. Generates refresh token with 30-day expiry
8. Returns user profile and wallet info

**Database Operations:**
```sql
-- Check existing user
SELECT id, status FROM users WHERE privy_user_id = ?;

-- First login: Create user
INSERT INTO users (uid, privy_user_id, email, role, status, created_at)
VALUES (UUID(), ?, ?, 2, 0, NOW());

-- Create wallet
INSERT INTO wallets (user_id, privy_wallet_id, address, default_chain, status, created_at)
VALUES (?, ?, ?, 'arbitrum', 1, NOW());

-- Create chain addresses
INSERT INTO chain_addresses (wallet_id, chain, address, is_active, created_at)
VALUES 
  (?, 'arbitrum', ?, TRUE, NOW()),
  (?, 'base', ?, TRUE, NOW()),
  (?, 'hyperliquid', ?, TRUE, NOW());

-- Update user to active
UPDATE users SET status = 1 WHERE id = ?;

-- Subsequent logins: Update timestamp
UPDATE users SET last_login_at = NOW(), last_active_at = NOW() WHERE id = ?;
```

**External Dependencies:**
- **Privy API:** Token validation, wallet creation
- **Database:** User and wallet creation/retrieval

**Rate Limits:**
- 5 requests per minute per IP address
- 10 requests per minute per Privy user ID

**JWT Payload Structure:**
```json
{
  "sub": "12345",
  "user_id": 12345,
  "uid": "usr_abc123def456",
  "email": "user@email.com",
  "role": 2,
  "privy_user_id": "did:privy:clk1abc123",
  "iat": 1699876543,
  "exp": 1699880143
}
```

---

### 1.2 POST /auth/refresh

Refresh expired access token using refresh token.

**Endpoint:** `POST /api/v1/user/auth/refresh`

**Authentication:** None (uses refresh token)

**Request:**
```http
POST /api/v1/user/auth/refresh HTTP/1.1
Host: api.anvil.com
Content-Type: application/json

{
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NSIsInR5cGUiOiJyZWZyZXNoIiwiaWF0IjoxNjk5ODc2NTQzLCJleHAiOjE3MDI0Njg1NDN9.signature"
}
```

**Request Body Schema:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `refresh_token` | string | ✅ Yes | Valid refresh token from login |

**Success Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "expires_in": 3600,
    "token_type": "Bearer"
  }
}
```

**Error Response (401 Unauthorized):**
```json
{
  "success": false,
  "error": {
    "code": "INVALID_REFRESH_TOKEN",
    "message": "Refresh token is invalid or expired",
    "timestamp": "2025-11-16T14:20:00Z",
    "request_id": "req_abc123"
  }
}
```

**Business Logic:**
1. Validates refresh token signature
2. Checks if token is expired or revoked
3. Generates new access token (1-hour expiry)
4. Returns new access token (refresh token unchanged)

**Rate Limit:** 10 requests per minute per user

---

### 1.3 POST /auth/logout

Invalidate current tokens and end session.

**Endpoint:** `POST /api/v1/user/auth/logout`

**Authentication:** Bearer Token required

**Request:**
```http
POST /api/v1/user/auth/logout HTTP/1.1
Host: api.anvil.com
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json
```

**Request Body:** None

**Success Response (200 OK):**
```json
{
  "success": true,
  "message": "Logged out successfully"
}
```

**Business Logic:**
1. Adds access token to blacklist (Redis)
2. Revokes refresh token
3. Returns success

**Database Operations:**
```sql
-- Blacklist token (Redis)
SETEX token_blacklist:${token_jti} 3600 "1"

-- Update user last_active
UPDATE users SET last_active_at = NOW() WHERE id = ?;
```

**Rate Limit:** 10 requests per minute

---

## 2. User Profile

Base path: `/api/v1/user/profile`

### 2.1 GET /profile

Get current user's complete profile information.

**Endpoint:** `GET /api/v1/user/profile`

**Authentication:** Bearer Token required

**Request:**
```http
GET /api/v1/user/profile HTTP/1.1
Host: api.anvil.com
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Success Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "id": 12345,
    "uid": "usr_abc123def456",
    "email": "user@email.com",
    "firstname": "John",
    "lastname": "Doe",
    "phone": "+12345678900",
    "date_of_birth": "1990-05-15",
    "role": 2,
    "status": 1,
    "status_label": "ACTIVE",
    "email_verified": true,
    "phone_verified": true,
    "kyc_status": "approved",
    "kyc_completed_at": "2025-02-01T10:00:00Z",
    "terms_accepted_at": "2025-01-15T10:35:00Z",
    "created_at": "2025-01-15T10:30:00Z",
    "updated_at": "2025-11-16T14:20:00Z",
    "last_login_at": "2025-11-16T14:20:00Z",
    "last_active_at": "2025-11-16T16:25:00Z"
  }
}
```

**Response Fields:**

| Field | Type | Nullable | Description |
|-------|------|----------|-------------|
| `id` | integer | No | Internal user ID |
| `uid` | string | No | External UUID |
| `email` | string | No | User email |
| `firstname` | string | Yes | First name |
| `lastname` | string | Yes | Last name |
| `phone` | string | Yes | Phone in E.164 format |
| `date_of_birth` | string | Yes | ISO date (YYYY-MM-DD) |
| `role` | integer | No | Always 2 for CLIENT |
| `status` | integer | No | 0=INACTIVE, 1=ACTIVE, 2=DELETED |
| `email_verified` | boolean | No | Email verification status |
| `phone_verified` | boolean | No | Phone verification status |
| `kyc_status` | string | No | KYC verification status |
| `kyc_completed_at` | string | Yes | KYC completion timestamp |
| `terms_accepted_at` | string | Yes | Terms acceptance timestamp |
| `created_at` | string | No | Account creation |
| `last_login_at` | string | Yes | Last login timestamp |
| `last_active_at` | string | Yes | Last activity timestamp |

**Database Operations:**
```sql
SELECT id, uid, email, firstname, lastname, phone, date_of_birth,
       role, status, email_verified, phone_verified, kyc_status,
       kyc_completed_at, terms_accepted_at, created_at, updated_at,
       last_login_at, last_active_at
FROM users
WHERE id = ? AND status != 2;
```

**Rate Limit:** 60 requests per minute

---

### 2.2 PATCH /profile

Update user profile information.

**Endpoint:** `PATCH /api/v1/user/profile`

**Authentication:** Bearer Token required

**Request:**
```http
PATCH /api/v1/user/profile HTTP/1.1
Host: api.anvil.com
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json

{
  "firstname": "John",
  "lastname": "Doe",
  "phone": "+12345678900",
  "date_of_birth": "1990-05-15"
}
```

**Request Body Schema:**

| Field | Type | Required | Validation | Description |
|-------|------|----------|------------|-------------|
| `firstname` | string | No | 1-50 chars, letters only | First name |
| `lastname` | string | No | 1-50 chars, letters only | Last name |
| `phone` | string | No | E.164 format | Phone number |
| `date_of_birth` | string | No | YYYY-MM-DD, age >= 18 | Date of birth |

**Success Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "id": 12345,
    "uid": "usr_abc123def456",
    "firstname": "John",
    "lastname": "Doe",
    "phone": "+12345678900",
    "date_of_birth": "1990-05-15",
    "updated_at": "2025-11-16T16:30:00Z"
  }
}
```

**Error Response (400 Bad Request):**
```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid phone number format",
    "details": {
      "field": "phone",
      "value": "123456",
      "constraint": "Must be in E.164 format (e.g., +12345678900)",
      "example": "+12345678900"
    },
    "timestamp": "2025-11-16T16:30:00Z",
    "request_id": "req_xyz789"
  }
}
```

**Validation Rules:**

```javascript
// Firstname/Lastname
/^[a-zA-Z\s'-]{1,50}$/

// Phone (E.164)
/^\+[1-9]\d{1,14}$/

// Date of Birth
- Must be valid ISO date (YYYY-MM-DD)
- User must be >= 18 years old
- Cannot be future date
```

**Database Operations:**
```sql
UPDATE users
SET firstname = ?,
    lastname = ?,
    phone = ?,
    date_of_birth = ?,
    updated_at = NOW()
WHERE id = ? AND status = 1;
```

**Business Logic:**
1. Validates all input fields
2. Checks if phone is unique (if changed)
3. Verifies age requirement (18+)
4. Updates only provided fields
5. Updates `updated_at` timestamp

**Rate Limit:** 20 requests per minute

---

## 3. Wallet Operations

Base path: `/api/v1/user/wallet`

### 3.1 GET /wallet

Get user's primary wallet information.

**Endpoint:** `GET /api/v1/user/wallet`

**Authentication:** Bearer Token required

**Request:**
```http
GET /api/v1/user/wallet HTTP/1.1
Host: api.anvil.com
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Success Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "id": 67890,
    "user_id": 12345,
    "address": "0x1234567890abcdef1234567890abcdef12345678",
    "privy_wallet_id": "0xabc123def456",
    "provider": "privy",
    "default_chain": "arbitrum",
    "status": 1,
    "status_label": "ACTIVE",
    "created_at": "2025-01-15T10:30:00Z",
    "updated_at": "2025-01-15T10:30:00Z"
  }
}
```

**Database Operations:**
```sql
SELECT id, user_id, address, privy_wallet_id, provider, 
       default_chain, status, created_at, updated_at
FROM wallets
WHERE user_id = ? AND status = 1;
```

**Rate Limit:** 60 requests per minute

---

### 3.2 GET /wallet/balances

Get token balances across all supported chains.

**Endpoint:** `GET /api/v1/user/wallet/balances`

**Authentication:** Bearer Token required

**Query Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `chain` | string | No | all | Filter by chain: 'arbitrum', 'base', 'hyperliquid' |
| `refresh` | boolean | No | false | Force refresh from blockchain RPCs |

**Request:**
```http
GET /api/v1/user/wallet/balances?chain=arbitrum&refresh=false HTTP/1.1
Host: api.anvil.com
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Success Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "total_usd": 1234.56,
    "last_updated": "2025-11-16T16:30:00Z",
    "refresh_mode": "cached",
    "chains": [
      {
        "chain": "arbitrum",
        "chain_id": 42161,
        "total_usd": 1225.00,
        "rpc_status": "healthy",
        "balances": [
          {
            "asset": "ETH",
            "symbol": "ETH",
            "name": "Ethereum",
            "amount": "0.5",
            "amount_raw": "500000000000000000",
            "decimals": 18,
            "usd_value": 1225.00,
            "price": 2450.00,
            "price_source": "chainlink",
            "change_24h": 56.35,
            "change_24h_percent": 2.3,
            "contract_address": "0x0000000000000000000000000000000000000000",
            "is_native": true,
            "logo_url": "https://assets.anvil.com/tokens/eth.png"
          },
          {
            "asset": "USDC",
            "symbol": "USDC",
            "name": "USD Coin",
            "amount": "100.0",
            "amount_raw": "100000000",
            "decimals": 6,
            "usd_value": 100.00,
            "price": 1.00,
            "price_source": "chainlink",
            "change_24h": 0.0,
            "change_24h_percent": 0.0,
            "contract_address": "0xaf88d065e77c8cC2239327C5EDb3A432268e5831",
            "is_native": false,
            "logo_url": "https://assets.anvil.com/tokens/usdc.png"
          }
        ]
      },
      {
        "chain": "base",
        "chain_id": 8453,
        "total_usd": 9.56,
        "rpc_status": "healthy",
        "balances": [
          {
            "asset": "ETH",
            "symbol": "ETH",
            "name": "Ethereum",
            "amount": "0.0039",
            "amount_raw": "3900000000000000",
            "decimals": 18,
            "usd_value": 9.56,
            "price": 2450.00,
            "price_source": "chainlink",
            "change_24h": 0.22,
            "change_24h_percent": 2.3,
            "contract_address": "0x0000000000000000000000000000000000000000",
            "is_native": true,
            "logo_url": "https://assets.anvil.com/tokens/eth.png"
          }
        ]
      },
      {
        "chain": "hyperliquid",
        "chain_id": null,
        "total_usd": 0.00,
        "rpc_status": "healthy",
        "balances": []
      }
    ]
  }
}
```

**Response Fields:**

| Field | Type | Description |
|-------|------|-------------|
| `total_usd` | number | Total portfolio value across all chains |
| `last_updated` | string | Last balance update timestamp |
| `refresh_mode` | string | 'cached' or 'live' |
| `chains[].chain` | string | Chain identifier |
| `chains[].chain_id` | integer | EVM chain ID (null for non-EVM) |
| `chains[].total_usd` | number | Total value on this chain |
| `chains[].rpc_status` | string | RPC health status |
| `balances[].amount` | string | Human-readable amount |
| `balances[].amount_raw` | string | Raw amount in smallest unit |
| `balances[].decimals` | integer | Token decimals |
| `balances[].usd_value` | number | USD value |
| `balances[].price` | number | Current token price |
| `balances[].contract_address` | string | Token contract (0x0 for native) |
| `balances[].is_native` | boolean | Is native chain token |

**Business Logic:**
1. **If `refresh=false` (default):**
   - Returns cached balances from database
   - Fast response (~50ms)
2. **If `refresh=true`:**
   - Fetches real-time balances from blockchain RPCs
   - Updates database cache
   - Slower response (~2-5 seconds)
3. Fetches current prices from Chainlink/CoinGecko
4. Calculates USD values
5. Aggregates total portfolio value

**Database Operations:**
```sql
-- Cached mode
SELECT ca.chain, ca.address, ca.balance_usd, ca.last_balance_update,
       w.address as wallet_address
FROM chain_addresses ca
INNER JOIN wallets w ON ca.wallet_id = w.id
WHERE w.user_id = ? AND ca.is_active = TRUE;

-- Refresh mode: Updates after RPC fetch
UPDATE chain_addresses
SET balance_usd = ?,
    last_balance_update = NOW()
WHERE wallet_id = ? AND chain = ?;
```

**External Dependencies:**
- **Arbitrum RPC:** Balance queries (if refresh)
- **Base RPC:** Balance queries (if refresh)
- **Hyperliquid API:** Balance queries (if refresh)
- **Chainlink:** Price feeds
- **CoinGecko API:** Fallback prices

**Rate Limits:**
- Without refresh: 60 requests per minute
- With refresh: 5 requests per minute (expensive operation)

**Error Response (503 Service Unavailable):**
```json
{
  "success": false,
  "error": {
    "code": "RPC_UNAVAILABLE",
    "message": "Unable to fetch balances from Arbitrum RPC",
    "details": {
      "chain": "arbitrum",
      "rpc_error": "Connection timeout",
      "using_cached_data": true,
      "cache_age_seconds": 300
    },
    "timestamp": "2025-11-16T16:30:00Z"
  }
}
```

---

### 3.3 GET /wallet/addresses

Get wallet addresses for all supported chains.

**Endpoint:** `GET /api/v1/user/wallet/addresses`

**Authentication:** Bearer Token required

**Request:**
```http
GET /api/v1/user/wallet/addresses HTTP/1.1
Host: api.anvil.com
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Success Response (200 OK):**
```json
{
  "success": true,
  "data": [
    {
      "id": 1,
      "wallet_id": 67890,
      "chain": "arbitrum",
      "chain_id": 42161,
      "address": "0x1234567890abcdef1234567890abcdef12345678",
      "is_active": true,
      "balance_usd": 1325.00,
      "last_balance_update": "2025-11-16T16:30:00Z",
      "explorer_url": "https://arbiscan.io/address/0x1234567890abcdef1234567890abcdef12345678",
      "created_at": "2025-01-15T10:30:00Z"
    },
    {
      "id": 2,
      "wallet_id": 67890,
      "chain": "base",
      "chain_id": 8453,
      "address": "0x1234567890abcdef1234567890abcdef12345678",
      "is_active": true,
      "balance_usd": 9.56,
      "last_balance_update": "2025-11-16T16:30:00Z",
      "explorer_url": "https://basescan.org/address/0x1234567890abcdef1234567890abcdef12345678",
      "created_at": "2025-01-15T10:30:00Z"
    },
    {
      "id": 3,
      "wallet_id": 67890,
      "chain": "hyperliquid",
      "chain_id": null,
      "address": "hype1234567890abcdef",
      "is_active": true,
      "balance_usd": 0.00,
      "last_balance_update": "2025-11-16T16:30:00Z",
      "explorer_url": "https://hyperliquid.xyz/address/hype1234567890abcdef",
      "created_at": "2025-01-15T10:30:00Z"
    }
  ]
}
```

**Database Operations:**
```sql
SELECT ca.id, ca.wallet_id, ca.chain, ca.address, ca.is_active,
       ca.balance_usd, ca.last_balance_update, ca.created_at
FROM chain_addresses ca
INNER JOIN wallets w ON ca.wallet_id = w.id
WHERE w.user_id = ?
ORDER BY ca.chain;
```

**Rate Limit:** 60 requests per minute

---

### 3.4 POST /wallet/refresh-balances

Force refresh balances from blockchain RPCs.

**Endpoint:** `POST /api/v1/user/wallet/refresh-balances`

**Authentication:** Bearer Token required

**Request:**
```http
POST /api/v1/user/wallet/refresh-balances HTTP/1.1
Host: api.anvil.com
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json

{
  "chains": ["arbitrum", "base"]
}
```

**Request Body Schema:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `chains` | array | No | Chains to refresh (all if omitted) |

**Success Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "refreshed_at": "2025-11-16T16:35:00Z",
    "total_usd": 1234.56,
    "chains_refreshed": ["arbitrum", "base"],
    "refresh_duration_ms": 2340,
    "balances": {
      "arbitrum": {
        "total_usd": 1225.00,
        "tokens_found": 2
      },
      "base": {
        "total_usd": 9.56,
        "tokens_found": 1
      }
    }
  }
}
```

**Business Logic:**
1. Validates requested chains
2. Fetches real-time balances from RPCs in parallel
3. Updates `chain_addresses` table
4. Recalculates USD values with current prices
5. Returns updated totals

**External Dependencies:**
- Blockchain RPCs (Arbitrum, Base, Hyperliquid)
- Price feed APIs

**Rate Limit:** 5 requests per minute (expensive operation)

---

## 4. Transactions

Base path: `/api/v1/user/transactions`

### 4.1 GET /transactions

Get user's transaction history with filtering and pagination.

**Endpoint:** `GET /api/v1/user/transactions`

**Authentication:** Bearer Token required

**Query Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `page` | integer | No | 1 | Page number (min: 1) |
| `limit` | integer | No | 20 | Items per page (max: 100) |
| `type` | integer | No | - | Filter by type: 0=SWAP, 1=FUND, 2=EARN, 3=SAVE, 4=SUBSCRIPTION |
| `status` | integer | No | - | Filter by status: 0=PENDING, 1=SUCCESS, 2=FAILED |
| `chain` | string | No | - | Filter by chain |
| `date_from` | string | No | - | ISO date (YYYY-MM-DD) |
| `date_to` | string | No | - | ISO date (YYYY-MM-DD) |
| `asset` | string | No | - | Filter by asset (in or out) |
| `sort` | string | No | created_at:desc | Sort field:direction |

**Request:**
```http
GET /api/v1/user/transactions?page=1&limit=20&type=0&status=1&chain=arbitrum&sort=created_at:desc HTTP/1.1
Host: api.anvil.com
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Success Response (200 OK):**
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
        "fee_usd": 0.35,
        "tx_hash": "0xswap123def456...",
        "status": 1,
        "status_label": "SUCCESS",
        "dex_aggregator": "1inch",
        "dex_route": {
          "protocol": "1inch",
          "route": ["Uniswap V3"],
          "hops": 1
        },
        "slippage": 0.5,
        "block_number": 12345680,
        "confirmations": 15,
        "explorer_url": "https://arbiscan.io/tx/0xswap123def456...",
        "confirmed_at": "2025-11-16T13:45:30Z",
        "created_at": "2025-11-16T13:45:00Z"
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
        "tx_hash": "0xfund456abc...",
        "status": 1,
        "status_label": "SUCCESS",
        "dex_aggregator": null,
        "dex_route": null,
        "slippage": null,
        "block_number": 12345650,
        "confirmations": 45,
        "explorer_url": "https://arbiscan.io/tx/0xfund456abc...",
        "confirmed_at": "2025-11-16T10:30:45Z",
        "created_at": "2025-11-16T10:30:00Z"
      }
    ],
    "pagination": {
      "page": 1,
      "limit": 20,
      "total": 45,
      "total_pages": 3,
      "has_next": true,
      "has_prev": false
    },
    "summary": {
      "total_volume_usd": 1234.56,
      "total_transactions": 45,
      "success_count": 44,
      "failed_count": 1,
      "pending_count": 0,
      "success_rate": 97.8,
      "total_fees_usd": 23.45
    }
  }
}
```

**Database Operations:**
```sql
SELECT t.id, t.type, t.chain, t.asset_in, t.amount_in, t.asset_out,
       t.amount_out, t.fee, t.fee_usd, t.tx_hash, t.status,
       t.dex_aggregator, t.dex_route, t.slippage, t.error_message,
       t.block_number, t.confirmed_at, t.created_at
FROM transactions t
WHERE t.user_id = ?
  AND (? IS NULL OR t.type = ?)
  AND (? IS NULL OR t.status = ?)
  AND (? IS NULL OR t.chain = ?)
  AND (? IS NULL OR DATE(t.created_at) >= ?)
  AND (? IS NULL OR DATE(t.created_at) <= ?)
  AND (? IS NULL OR t.asset_in = ? OR t.asset_out = ?)
ORDER BY t.created_at DESC
LIMIT ? OFFSET ?;

-- Summary query
SELECT 
  COUNT(*) as total,
  SUM(CASE WHEN status = 1 THEN 1 ELSE 0 END) as success_count,
  SUM(CASE WHEN status = 2 THEN 1 ELSE 0 END) as failed_count,
  SUM(CASE WHEN status = 0 THEN 1 ELSE 0 END) as pending_count,
  SUM(CASE WHEN status = 1 THEN COALESCE(amount_in, 0) ELSE 0 END) as volume,
  SUM(COALESCE(fee_usd, 0)) as total_fees
FROM transactions
WHERE user_id = ?;
```

**Rate Limit:** 60 requests per minute

---

### 4.2 GET /transactions/:id

Get detailed information about a specific transaction.

**Endpoint:** `GET /api/v1/user/transactions/:id`

**Authentication:** Bearer Token required

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `id` | integer | Transaction ID |

**Request:**
```http
GET /api/v1/user/transactions/789 HTTP/1.1
Host: api.anvil.com
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Success Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "id": 789,
    "type": 0,
    "type_label": "SWAP",
    "chain": "arbitrum",
    "chain_id": 42161,
    "asset_in": "USDC",
    "amount_in": "50.0",
    "asset_out": "ETH",
    "amount_out": "0.0204",
    "fee": "0.00015",
    "fee_usd": 0.35,
    "gas_used": "145000",
    "gas_price": "0.1 gwei",
    "tx_hash": "0xswap123def456789abcdef0123456789abcdef0123456789abcdef012345",
    "status": 1,
    "status_label": "SUCCESS",
    "dex_aggregator": "1inch",
    "dex_route": {
      "protocol": "1inch",
      "route": ["Uniswap V3"],
      "hops": 1,
      "pools": [
        {
          "name": "USDC/ETH",
          "pool_address": "0xpool123...",
          "fee_tier": "0.3%",
          "liquidity": "5000000"
        }
      ]
    },
    "slippage": 0.5,
    "price_impact": "0.12%",
    "rate": "1 USDC = 0.000408 ETH",
    "error_message": null,
    "block_number": 12345680,
    "block_timestamp": "2025-11-16T13:45:25Z",
    "confirmations": 15,
    "from_address": "0x1234567890abcdef1234567890abcdef12345678",
    "to_address": "0x1inch_router...",
    "nonce": 42,
    "explorer_url": "https://arbiscan.io/tx/0xswap123def456...",
    "confirmed_at": "2025-11-16T13:45:30Z",
    "created_at": "2025-11-16T13:45:00Z",
    "updated_at": "2025-11-16T13:45:30Z"
  }
}
```

**Error Response (404 Not Found):**
```json
{
  "success": false,
  "error": {
    "code": "TRANSACTION_NOT_FOUND",
    "message": "Transaction not found or does not belong to this user",
    "timestamp": "2025-11-16T16:40:00Z",
    "request_id": "req_abc123"
  }
}
```

**Database Operations:**
```sql
SELECT *
FROM transactions
WHERE id = ? AND user_id = ?;
```

**Rate Limit:** 60 requests per minute

---

## Standard Response Formats

### Success Response
```json
{
  "success": true,
  "data": { ... }
}
```

### Error Response
```json
{
  "success": false,
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable message",
    "details": { ... },
    "timestamp": "2025-11-16T16:00:00Z",
    "request_id": "req_xyz789"
  }
}
```

### Pagination Format
```json
{
  "pagination": {
    "page": 1,
    "limit": 20,
    "total": 100,
    "total_pages": 5,
    "has_next": true,
    "has_prev": false
  }
}
```

---

## Rate Limit Headers

All responses include rate limit headers:

```http
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 45
X-RateLimit-Reset: 1700000000
```

---

**Document Status:** Part 1 of 2 Complete ✅  
**Next:** Part 2 (Trading, Earn, Save, Perpetuals, AI, Subscriptions, Notifications, Funding)
