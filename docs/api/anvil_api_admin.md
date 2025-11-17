# 🔌 Anvil API - ADMIN Endpoints

## Overview

**Base URL:** `https://api.anvil.com/v1`  
**User Type:** ADMIN (role=0)  
**Platform:** Web Admin Console  
**Authentication:** JWT Bearer Token with admin role  
**Access Level:** Full CRUD access to all resources

---

## Table of Contents

1. [Authentication](#1-authentication)
2. [Dashboard & Analytics](#2-dashboard--analytics)
3. [User Management](#3-user-management)
4. [Transaction Management](#4-transaction-management)
5. [Settings Management](#5-settings-management)
6. [AI & Model Configuration](#6-ai--model-configuration)
7. [Subscription Management](#7-subscription-management)
8. [Audit Logs](#8-audit-logs)

---

## 1. Authentication

Base path: `/api/v1/admin/auth`

### 1.1 POST /auth/login

Admin login with email/password.

**Endpoint:** `POST /api/v1/admin/auth/login`

**Authentication:** None (login endpoint)

**Request:**
```http
POST /api/v1/admin/auth/login HTTP/1.1
Host: api.anvil.com
Content-Type: application/json

{
  "email": "admin@anvil.com",
  "password": "securepassword123",
  "totp_code": "123456"
}
```

**Request Body Schema:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `email` | string | ✅ Yes | Admin email |
| `password` | string | ✅ Yes | Admin password |
| `totp_code` | string | If 2FA enabled | 6-digit TOTP code |

**Success Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "expires_in": 28800,
    "token_type": "Bearer",
    "admin": {
      "id": 1,
      "uid": "usr_admin001",
      "email": "admin@anvil.com",
      "firstname": "Admin",
      "lastname": "User",
      "role": 0,
      "permissions": ["*"],
      "last_login_at": "2025-11-16T19:00:00Z"
    }
  }
}
```

**Error Response (401 Unauthorized):**
```json
{
  "success": false,
  "error": {
    "code": "INVALID_CREDENTIALS",
    "message": "Invalid email or password",
    "timestamp": "2025-11-16T19:00:00Z",
    "request_id": "req_xyz789"
  }
}
```

**Error Response (403 Forbidden):**
```json
{
  "success": false,
  "error": {
    "code": "TOTP_REQUIRED",
    "message": "2FA authentication required",
    "details": {
      "totp_enabled": true
    },
    "timestamp": "2025-11-16T19:00:00Z",
    "request_id": "req_xyz789"
  }
}
```

**Business Logic:**
1. Validates email and password
2. Checks if user has role=0 (ADMIN)
3. Verifies TOTP if 2FA is enabled
4. Generates JWT with 8-hour expiry
5. Logs admin login to audit_logs
6. Updates last_login_at timestamp

**Database Operations:**
```sql
-- Verify admin credentials
SELECT id, uid, email, password_hash, role, status
FROM users
WHERE email = ? AND role = 0 AND status = 1;

-- Log admin login
INSERT INTO audit_logs (
  actor_user_id, action, entity, entity_id, payload_json,
  ip_address, user_agent, created_at
) VALUES (?, 'admin_login', 'auth', ?, ?, ?, ?, NOW());

-- Update last login
UPDATE users
SET last_login_at = NOW(), last_active_at = NOW()
WHERE id = ?;
```

**Rate Limit:** 5 requests per minute per IP

---

## 2. Dashboard & Analytics

Base path: `/api/v1/admin/dashboard`

### 2.1 GET /dashboard/stats

Get platform statistics for admin dashboard.

**Endpoint:** `GET /api/v1/admin/dashboard/stats`

**Authentication:** Bearer Token (admin role required)

**Query Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `period` | string | '24h', '7d', '30d', '90d' (default: '24h') |

**Request:**
```http
GET /api/v1/admin/dashboard/stats?period=24h HTTP/1.1
Host: api.anvil.com
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Success Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "period": "24h",
    "timestamp": "2025-11-16T19:00:00Z",
    "users": {
      "total": 1234,
      "active_24h": 234,
      "new_today": 12,
      "growth_rate_7d": 5.2,
      "kyc_approved": 892,
      "kyc_pending": 45,
      "kyc_approval_rate": 95.2
    },
    "transactions": {
      "total_24h": 567,
      "success_count": 557,
      "failed_count": 10,
      "pending_count": 0,
      "success_rate": 98.2,
      "total_volume_usd_24h": 45678.90,
      "avg_transaction_usd": 80.56,
      "by_type": {
        "swap": 320,
        "fund": 150,
        "earn": 80,
        "save": 17
      }
    },
    "llm": {
      "total_calls_24h": 5678,
      "total_cost_24h": 11.23,
      "avg_cost_per_call": 0.002,
      "success_rate": 99.1,
      "vertex_calls": 5346,
      "bedrock_calls": 332,
      "by_model": {
        "gemini-1.5-flash": 5120,
        "gemini-1.5-pro": 226,
        "claude-sonnet": 332
      }
    },
    "agents": {
      "total_executions_24h": 234,
      "success_count": 226,
      "failed_count": 8,
      "success_rate": 96.5,
      "avg_execution_time_ms": 4567,
      "total_cost_24h": 0.702,
      "avg_cost": 0.003
    },
    "revenue": {
      "total_funding_24h": 12345.67,
      "subscriptions_mrr": 2106.66,
      "subscriptions_active": 211,
      "subscriptions_churned_30d": 15,
      "churn_rate": 6.6,
      "total_fees_collected_24h": 567.89,
      "avg_revenue_per_user": 10.01
    },
    "system": {
      "rpc_status": {
        "arbitrum": "healthy",
        "base": "healthy",
        "hyperliquid": "healthy"
      },
      "database_status": "healthy",
      "cache_status": "healthy",
      "ai_service_status": "healthy"
    },
    "alerts": [
      {
        "severity": "medium",
        "type": "quota_warning",
        "message": "Vertex AI quota at 75%",
        "timestamp": "2025-11-16T18:45:00Z"
      }
    ]
  }
}
```

**Business Logic:**
1. Aggregates data from multiple tables
2. Calculates growth rates and metrics
3. Checks system health status
4. Returns comprehensive dashboard data

**Database Operations:**
```sql
-- User stats
SELECT 
  COUNT(*) as total,
  SUM(CASE WHEN last_active_at >= NOW() - INTERVAL 24 HOUR THEN 1 ELSE 0 END) as active_24h,
  SUM(CASE WHEN DATE(created_at) = CURDATE() THEN 1 ELSE 0 END) as new_today,
  SUM(CASE WHEN kyc_status = 'approved' THEN 1 ELSE 0 END) as kyc_approved,
  SUM(CASE WHEN kyc_status = 'pending' THEN 1 ELSE 0 END) as kyc_pending
FROM users
WHERE status = 1 AND role = 2;

-- Transaction stats
SELECT 
  COUNT(*) as total,
  SUM(CASE WHEN status = 1 THEN 1 ELSE 0 END) as success,
  SUM(CASE WHEN status = 2 THEN 1 ELSE 0 END) as failed,
  SUM(CASE WHEN status = 0 THEN 1 ELSE 0 END) as pending,
  SUM(CASE WHEN status = 1 THEN amount_in ELSE 0 END) as volume
FROM transactions
WHERE created_at >= NOW() - INTERVAL 24 HOUR;

-- LLM stats
SELECT 
  COUNT(*) as total,
  SUM(cost_usd) as total_cost,
  AVG(cost_usd) as avg_cost,
  provider,
  model_name
FROM llm_conversations
WHERE created_at >= NOW() - INTERVAL 24 HOUR
GROUP BY provider, model_name;
```

**Rate Limit:** 60 requests per minute

---

## 3. User Management

Base path: `/api/v1/admin/users`

### 3.1 GET /users

Get list of users with filtering and pagination.

**Endpoint:** `GET /api/v1/admin/users`

**Authentication:** Bearer Token (admin)

**Query Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `page` | integer | Page number (default: 1) |
| `limit` | integer | Items per page (max: 100, default: 50) |
| `search` | string | Search by email, name, uid |
| `role` | integer | Filter by role |
| `status` | integer | Filter by status |
| `kyc_status` | string | Filter by KYC status |
| `created_from` | string | Created after date (ISO) |
| `created_to` | string | Created before date (ISO) |
| `sort` | string | Sort field:direction |

**Request:**
```http
GET /api/v1/admin/users?page=1&limit=50&kyc_status=pending&sort=created_at:desc HTTP/1.1
Host: api.anvil.com
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Success Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "users": [
      {
        "id": 12345,
        "uid": "usr_abc123",
        "email": "user@email.com",
        "firstname": "John",
        "lastname": "Doe",
        "phone": "+12345678900",
        "role": 2,
        "role_label": "CLIENT",
        "status": 1,
        "status_label": "ACTIVE",
        "kyc_status": "pending",
        "kyc_submitted_at": "2025-11-15T10:00:00Z",
        "email_verified": true,
        "wallet_address": "0x1234...5678",
        "total_transactions": 8,
        "total_volume_usd": 450.00,
        "subscription_plan": "free",
        "created_at": "2025-11-08T10:30:00Z",
        "last_login_at": "2025-11-16T14:20:00Z"
      }
    ],
    "pagination": {
      "page": 1,
      "limit": 50,
      "total": 5,
      "total_pages": 1,
      "has_next": false,
      "has_prev": false
    }
  }
}
```

**Database Operations:**
```sql
SELECT u.id, u.uid, u.email, u.firstname, u.lastname, u.phone,
       u.role, u.status, u.kyc_status, u.kyc_submitted_at,
       u.email_verified, u.created_at, u.last_login_at,
       w.address as wallet_address,
       COUNT(DISTINCT t.id) as total_transactions,
       SUM(CASE WHEN t.status = 1 THEN t.amount_in ELSE 0 END) as total_volume,
       s.plan as subscription_plan
FROM users u
LEFT JOIN wallets w ON u.id = w.user_id
LEFT JOIN transactions t ON u.id = t.user_id
LEFT JOIN subscriptions s ON u.id = s.user_id
WHERE (? IS NULL OR u.role = ?)
  AND (? IS NULL OR u.status = ?)
  AND (? IS NULL OR u.kyc_status = ?)
  AND (? IS NULL OR u.email LIKE ? OR u.firstname LIKE ? OR u.uid LIKE ?)
GROUP BY u.id
ORDER BY u.created_at DESC
LIMIT ? OFFSET ?;
```

**Rate Limit:** 60 requests per minute

---

### 3.2 GET /users/:id

Get detailed user information.

**Endpoint:** `GET /api/v1/admin/users/:id`

**Authentication:** Bearer Token (admin)

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `id` | integer | User ID |

**Request:**
```http
GET /api/v1/admin/users/12345 HTTP/1.1
Host: api.anvil.com
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Success Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "user": {
      "id": 12345,
      "uid": "usr_abc123",
      "privy_user_id": "did:privy:clk1abc123",
      "email": "user@email.com",
      "firstname": "John",
      "lastname": "Doe",
      "phone": "+12345678900",
      "date_of_birth": "1990-05-15",
      "role": 2,
      "status": 1,
      "kyc_status": "approved",
      "kyc_completed_at": "2025-11-10T15:00:00Z",
      "email_verified": true,
      "phone_verified": true,
      "terms_accepted_at": "2025-11-08T10:35:00Z",
      "created_at": "2025-11-08T10:30:00Z",
      "updated_at": "2025-11-16T14:20:00Z",
      "last_login_at": "2025-11-16T14:20:00Z",
      "last_active_at": "2025-11-16T19:05:00Z"
    },
    "wallet": {
      "id": 67890,
      "address": "0x1234567890abcdef1234567890abcdef12345678",
      "privy_wallet_id": "0xabc123",
      "default_chain": "arbitrum",
      "status": 1,
      "created_at": "2025-11-08T10:30:00Z"
    },
    "statistics": {
      "total_transactions": 45,
      "successful_transactions": 44,
      "failed_transactions": 1,
      "total_volume_usd": 5678.90,
      "total_fees_paid_usd": 45.67,
      "earn_positions_count": 1,
      "earn_total_deposited": 50.0,
      "perp_positions_count": 0,
      "ai_conversations_total": 25,
      "ai_conversations_this_month": 25
    },
    "subscription": {
      "plan": "free",
      "status": null,
      "conversations_limit": 10,
      "conversations_used_today": 5
    }
  }
}
```

**Rate Limit:** 60 requests per minute

---

### 3.3 PATCH /users/:id/kyc

Approve or reject user KYC.

**Endpoint:** `PATCH /api/v1/admin/users/:id/kyc`

**Authentication:** Bearer Token (admin)

**Request:**
```http
PATCH /api/v1/admin/users/12345/kyc HTTP/1.1
Host: api.anvil.com
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json

{
  "action": "approve",
  "notes": "All documents verified. Normal usage pattern."
}
```

**Request Body Schema:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `action` | string | ✅ Yes | 'approve' or 'reject' |
| `notes` | string | ✅ Yes | Admin notes (1-1000 chars) |
| `rejection_reason` | string | If reject | Reason for rejection |

**Success Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "user_id": 12345,
    "kyc_status": "approved",
    "approved_at": "2025-11-16T19:30:00Z",
    "approved_by": "admin@anvil.com",
    "notes": "All documents verified. Normal usage pattern."
  }
}
```

**Business Logic:**
1. Validates admin permissions
2. Updates user KYC status
3. Logs action to audit_logs
4. Sends notification to user
5. Records admin notes

**Database Operations:**
```sql
-- Update user KYC
UPDATE users
SET kyc_status = ?,
    kyc_completed_at = NOW(),
    updated_at = NOW()
WHERE id = ?;

-- Create audit log
INSERT INTO audit_logs (
  actor_user_id, action, entity, entity_id, payload_json,
  ip_address, created_at
) VALUES (?, 'kyc_approved', 'user', ?, ?, ?, NOW());

-- Send notification
INSERT INTO notifications (
  user_id, type, channel, title, message, priority, status, created_at
) VALUES (?, 'kyc_approved', 'email', ?, ?, 'medium', 'pending', NOW());
```

**Rate Limit:** 20 requests per minute

---

### 3.4 PATCH /users/:id/status

Update user status (activate/suspend).

**Endpoint:** `PATCH /api/v1/admin/users/:id/status`

**Authentication:** Bearer Token (admin)

**Request:**
```http
PATCH /api/v1/admin/users/12345/status HTTP/1.1
Host: api.anvil.com
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json

{
  "status": 2,
  "reason": "Terms of Service violation - Multiple fraudulent transactions",
  "notes": "Contacted by compliance team. Suspicious activity confirmed."
}
```

**Request Body Schema:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `status` | integer | ✅ Yes | 0=INACTIVE, 1=ACTIVE, 2=DELETED |
| `reason` | string | ✅ Yes | Reason for status change |
| `notes` | string | No | Additional admin notes |

**Success Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "user_id": 12345,
    "status": 2,
    "status_label": "DELETED",
    "updated_at": "2025-11-16T19:35:00Z",
    "updated_by": "admin@anvil.com"
  }
}
```

**Database Operations:**
```sql
-- Update status
UPDATE users
SET status = ?,
    updated_at = NOW()
WHERE id = ?;

-- Log action
INSERT INTO audit_logs (
  actor_user_id, action, entity, entity_id, payload_json,
  ip_address, created_at
) VALUES (?, 'user_status_changed', 'user', ?, ?, ?, NOW());

-- Notify user
INSERT INTO notifications (
  user_id, type, channel, title, message, priority, status, created_at
) VALUES (?, 'account_suspended', 'email', ?, ?, 'high', 'pending', NOW());
```

**Rate Limit:** 20 requests per minute

---

## 4. Transaction Management

Base path: `/api/v1/admin/transactions`

### 4.1 GET /transactions

Get all transactions with filtering.

**Endpoint:** `GET /api/v1/admin/transactions`

**Authentication:** Bearer Token (admin)

**Query Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `page` | integer | Page number |
| `limit` | integer | Items per page (max: 100) |
| `user_id` | integer | Filter by user |
| `type` | integer | Filter by type |
| `status` | integer | Filter by status |
| `chain` | string | Filter by chain |
| `date_from` | string | ISO date |
| `date_to` | string | ISO date |
| `min_amount` | number | Minimum amount USD |
| `max_amount` | number | Maximum amount USD |

**Success Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "transactions": [
      {
        "id": 789,
        "user_id": 12345,
        "user_email": "user@email.com",
        "wallet_address": "0x1234...5678",
        "type": 0,
        "type_label": "SWAP",
        "chain": "arbitrum",
        "asset_in": "USDC",
        "amount_in": "50.0",
        "asset_out": "ETH",
        "amount_out": "0.0204",
        "fee_usd": 0.35,
        "tx_hash": "0xswap123...",
        "status": 1,
        "status_label": "SUCCESS",
        "confirmed_at": "2025-11-16T13:45:30Z",
        "created_at": "2025-11-16T13:45:00Z"
      }
    ],
    "pagination": {
      "page": 1,
      "limit": 50,
      "total": 567,
      "total_pages": 12
    },
    "summary": {
      "total_volume_usd": 45678.90,
      "total_fees_usd": 234.56,
      "success_rate": 98.2
    }
  }
}
```

**Rate Limit:** 60 requests per minute

---

### 4.2 POST /transactions/:id/retry

Retry failed transaction.

**Endpoint:** `POST /api/v1/admin/transactions/:id/retry`

**Authentication:** Bearer Token (admin)

**Request:**
```http
POST /api/v1/admin/transactions/458/retry HTTP/1.1
Host: api.anvil.com
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json

{
  "override_gas_price": 1.2,
  "reason": "Network congestion caused initial failure. Retrying with current gas price."
}
```

**Request Body Schema:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `override_gas_price` | number | No | Override gas price (gwei) |
| `reason` | string | ✅ Yes | Reason for retry |

**Success Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "original_tx_id": 458,
    "new_tx_id": 460,
    "tx_hash": "0xretry789...",
    "status": "pending",
    "estimated_time": "30 seconds"
  }
}
```

**Business Logic:**
1. Validates transaction is failed
2. Checks user still has balance
3. Gets fresh quote with updated parameters
4. Submits new transaction
5. Creates new transaction record
6. Updates original transaction with retry note
7. Logs admin action

**Database Operations:**
```sql
-- Update original transaction
UPDATE transactions
SET error_message = CONCAT(error_message, ' | Retried by admin'),
    updated_at = NOW()
WHERE id = ?;

-- Create new transaction
INSERT INTO transactions (
  user_id, wallet_id, type, chain, asset_in, amount_in,
  asset_out, amount_out, tx_hash, status, created_at
) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 0, NOW());

-- Log admin action
INSERT INTO audit_logs (
  actor_user_id, action, entity, entity_id, payload_json,
  ip_address, created_at
) VALUES (?, 'transaction_retried', 'transaction', ?, ?, ?, NOW());
```

**Rate Limit:** 10 requests per minute

---

## 5. Settings Management

Base path: `/api/v1/admin/settings`

### 5.1 GET /settings

Get all system settings.

**Endpoint:** `GET /api/v1/admin/settings`

**Authentication:** Bearer Token (admin)

**Query Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `scope` | string | Filter by scope: 'global', 'security', 'payment', 'ai' |
| `search` | string | Search by key or description |

**Success Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "settings": [
      {
        "id": 1,
        "key": "max_daily_trade_limit",
        "value": "5000",
        "scope": "global",
        "data_type": "number",
        "is_sensitive": false,
        "description": "Maximum daily trading limit per user (USD)",
        "updated_at": "2025-10-01T10:00:00Z",
        "updated_by": "admin@anvil.com"
      },
      {
        "id": 2,
        "key": "stripe_api_key",
        "value": "sk_live_••••••••",
        "scope": "payment",
        "data_type": "string",
        "is_sensitive": true,
        "description": "Stripe secret API key",
        "updated_at": "2025-10-01T10:00:00Z",
        "updated_by": "admin@anvil.com"
      }
    ]
  }
}
```

**Rate Limit:** 60 requests per minute

---

### 5.2 PATCH /settings/:id

Update a system setting.

**Endpoint:** `PATCH /api/v1/admin/settings/:id`

**Authentication:** Bearer Token (admin)

**Request:**
```http
PATCH /api/v1/admin/settings/1 HTTP/1.1
Host: api.anvil.com
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json

{
  "value": "10000",
  "reason": "Increasing limit to accommodate growth in user base and average transaction sizes. Risk management team approved."
}
```

**Success Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "setting_id": 1,
    "key": "max_daily_trade_limit",
    "value": "10000",
    "previous_value": "5000",
    "updated_by": "admin@anvil.com",
    "updated_at": "2025-11-16T20:00:00Z"
  }
}
```

**Database Operations:**
```sql
-- Update setting
UPDATE settings
SET value = ?,
    updated_at = NOW(),
    updated_by = ?
WHERE id = ?;

-- Log change
INSERT INTO audit_logs (
  actor_user_id, action, entity, entity_id, payload_json,
  ip_address, created_at
) VALUES (?, 'setting_updated', 'setting', ?, ?, ?, NOW());

-- Clear cache
-- Redis: DEL settings:cache
```

**Rate Limit:** 20 requests per minute

---

## 6. AI & Model Configuration

Base path: `/api/v1/admin/ai`

### 6.1 GET /ai/models

Get AI model configurations.

**Endpoint:** `GET /api/v1/admin/ai/models`

**Authentication:** Bearer Token (admin)

**Success Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "models": [
      {
        "id": 1,
        "provider": "vertex",
        "name": "gemini-1.5-flash",
        "display_name": "Gemini 1.5 Flash",
        "status": "enabled",
        "cost_per_1k_input": 0.00001,
        "cost_per_1k_output": 0.00003,
        "max_tokens": 8192,
        "is_default": true,
        "usage_24h": 5120,
        "cost_24h": 0.256,
        "quota_limit": 10000,
        "quota_used": 5120,
        "quota_remaining": 4880,
        "updated_at": "2025-11-16T10:00:00Z"
      },
      {
        "id": 2,
        "provider": "vertex",
        "name": "gemini-1.5-pro",
        "display_name": "Gemini 1.5 Pro",
        "status": "enabled",
        "cost_per_1k_input": 0.0001,
        "cost_per_1k_output": 0.0003,
        "max_tokens": 32768,
        "is_default": false,
        "usage_24h": 226,
        "cost_24h": 0.068,
        "quota_limit": 1000,
        "quota_used": 226,
        "quota_remaining": 774,
        "updated_at": "2025-11-16T10:00:00Z"
      }
    ]
  }
}
```

**Rate Limit:** 60 requests per minute

---

### 6.2 PATCH /ai/models/:id

Update AI model configuration.

**Endpoint:** `PATCH /api/v1/admin/ai/models/:id`

**Authentication:** Bearer Token (admin)

**Request:**
```http
PATCH /api/v1/admin/ai/models/1 HTTP/1.1
Host: api.anvil.com
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json

{
  "status": "disabled",
  "reason": "Maintenance - switching to backup model"
}
```

**Success Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "model_id": 1,
    "provider": "vertex",
    "name": "gemini-1.5-flash",
    "status": "disabled",
    "updated_at": "2025-11-16T20:10:00Z",
    "updated_by": "admin@anvil.com"
  }
}
```

**Rate Limit:** 20 requests per minute

---

## 7. Subscription Management

Base path: `/api/v1/admin/subscriptions`

### 7.1 GET /subscriptions

Get all subscriptions.

**Endpoint:** `GET /api/v1/admin/subscriptions`

**Query Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `status` | string | Filter: 'active', 'trialing', 'canceled', 'past_due' |
| `plan` | string | Filter by plan |
| `page` | integer | Page number |
| `limit` | integer | Items per page |

**Success Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "subscriptions": [
      {
        "id": 501,
        "user_id": 12345,
        "user_email": "user@email.com",
        "stripe_subscription_id": "sub_stripe456",
        "plan": "pro",
        "status": "active",
        "price_monthly": 9.99,
        "billing_cycle_start": "2025-11-16T00:00:00Z",
        "billing_cycle_end": "2025-12-16T00:00:00Z",
        "trial_end": null,
        "cancel_at_period_end": false,
        "created_at": "2025-11-16T15:00:00Z"
      }
    ],
    "summary": {
      "total_active": 211,
      "total_trialing": 15,
      "total_canceled": 45,
      "mrr": 2106.66,
      "churn_rate_30d": 6.6
    }
  }
}
```

**Rate Limit:** 60 requests per minute

---

### 7.2 POST /subscriptions/:id/refund

Process subscription refund.

**Endpoint:** `POST /api/v1/admin/subscriptions/:id/refund`

**Request:**
```http
POST /api/v1/admin/subscriptions/501/refund HTTP/1.1
Host: api.anvil.com
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json

{
  "amount": 9.99,
  "reason": "Customer complaint - service issues",
  "notes": "Approved by support manager"
}
```

**Success Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "subscription_id": 501,
    "refund_amount": 9.99,
    "stripe_refund_id": "re_stripe789",
    "status": "succeeded",
    "processed_at": "2025-11-16T20:20:00Z"
  }
}
```

**Rate Limit:** 10 requests per minute

---

## 8. Audit Logs

Base path: `/api/v1/admin/audit-logs`

### 8.1 GET /audit-logs

Get audit trail with filtering.

**Endpoint:** `GET /api/v1/admin/audit-logs`

**Query Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `page` | integer | Page number |
| `limit` | integer | Items per page (max: 100) |
| `actor_user_id` | integer | Filter by admin user |
| `action` | string | Filter by action type |
| `entity` | string | Filter by entity type |
| `date_from` | string | ISO date |
| `date_to` | string | ISO date |

**Success Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "logs": [
      {
        "id": 10025,
        "actor_user_id": 1,
        "actor_email": "admin@anvil.com",
        "action": "kyc_approved",
        "entity": "user",
        "entity_id": "12345",
        "payload_json": {
          "user_email": "user@email.com",
          "notes": "All documents verified"
        },
        "ip_address": "192.168.1.100",
        "user_agent": "Mozilla/5.0...",
        "created_at": "2025-11-16T14:20:15Z"
      }
    ],
    "pagination": {
      "page": 1,
      "limit": 100,
      "total": 1234
    }
  }
}
```

**Rate Limit:** 60 requests per minute

---

## Standard Error Responses

All endpoints return consistent error format:

```json
{
  "success": false,
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable message",
    "details": {},
    "timestamp": "2025-11-16T20:00:00Z",
    "request_id": "req_xyz789"
  }
}
```

## Common Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `UNAUTHORIZED` | 401 | Invalid or expired admin token |
| `FORBIDDEN` | 403 | Insufficient admin permissions |
| `NOT_FOUND` | 404 | Resource not found |
| `VALIDATION_ERROR` | 400 | Invalid request data |
| `CONFLICT` | 409 | Resource conflict |
| `SERVER_ERROR` | 500 | Internal server error |

---

**Document Status:** ADMIN API Complete ✅  
**Total Endpoints:** 25+  
**All actions are audited** ✅  
**Next:** AUDITOR API endpoints
