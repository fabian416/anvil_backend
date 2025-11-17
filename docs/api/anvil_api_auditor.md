# 🔌 Anvil API - AUDITOR Endpoints

## Overview

**Base URL:** `https://api.anvil.com/v1`  
**User Type:** AUDITOR (role=1)  
**Platform:** Web Compliance Console  
**Authentication:** JWT Bearer Token with auditor role  
**Access Level:** Read-only access to all data for compliance monitoring

**Important:** All endpoints are READ-ONLY. No POST, PUT, PATCH, or DELETE operations allowed.

---

## Table of Contents

1. [Authentication](#1-authentication)
2. [Dashboard & Compliance Overview](#2-dashboard--compliance-overview)
3. [Audit Logs](#3-audit-logs)
4. [User Data Access](#4-user-data-access)
5. [Transaction Review](#5-transaction-review)
6. [Financial Reporting](#6-financial-reporting)
7. [Export Operations](#7-export-operations)

---

## 1. Authentication

Base path: `/api/v1/admin/auth`

### 1.1 POST /auth/login

Auditor login with email/password.

**Endpoint:** `POST /api/v1/admin/auth/login`

**Authentication:** None (login endpoint)

**Request:**
```http
POST /api/v1/admin/auth/login HTTP/1.1
Host: api.anvil.com
Content-Type: application/json

{
  "email": "auditor@compliance-firm.com",
  "password": "securepassword123",
  "totp_code": "123456"
}
```

**Request Body Schema:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `email` | string | ✅ Yes | Auditor email |
| `password` | string | ✅ Yes | Auditor password |
| `totp_code` | string | If 2FA | 6-digit TOTP code |

**Success Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "expires_in": 28800,
    "token_type": "Bearer",
    "auditor": {
      "id": 2,
      "uid": "usr_auditor001",
      "email": "auditor@compliance-firm.com",
      "firstname": "Jane",
      "lastname": "Auditor",
      "role": 1,
      "permissions": ["read:*"],
      "last_login_at": "2025-11-16T20:00:00Z"
    },
    "access_notice": "READ-ONLY ACCESS - All views are logged for compliance"
  }
}
```

**JWT Payload Structure:**
```json
{
  "sub": "2",
  "user_id": 2,
  "uid": "usr_auditor001",
  "email": "auditor@compliance-firm.com",
  "role": 1,
  "permissions": ["read:*"],
  "iat": 1699876543,
  "exp": 1699905343
}
```

**Business Logic:**
1. Validates email and password
2. Checks if user has role=1 (AUDITOR)
3. Verifies TOTP if 2FA is enabled
4. Generates JWT with 8-hour expiry
5. Logs auditor login to audit_logs
6. Updates last_login_at timestamp

**Database Operations:**
```sql
-- Verify auditor credentials
SELECT id, uid, email, password_hash, role, status
FROM users
WHERE email = ? AND role = 1 AND status = 1;

-- Log auditor login
INSERT INTO audit_logs (
  actor_user_id, action, entity, entity_id, payload_json,
  ip_address, user_agent, created_at
) VALUES (?, 'auditor_login', 'auth', ?, ?, ?, ?, NOW());

-- Update last login
UPDATE users
SET last_login_at = NOW(), last_active_at = NOW()
WHERE id = ?;
```

**Rate Limit:** 5 requests per minute per IP

---

## 2. Dashboard & Compliance Overview

Base path: `/api/v1/admin/dashboard`

### 2.1 GET /dashboard/stats

Get compliance-focused platform statistics.

**Endpoint:** `GET /api/v1/admin/dashboard/stats`

**Authentication:** Bearer Token (auditor role)

**Query Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `period` | string | '24h', '7d', '30d', '90d' (default: '30d') |

**Request:**
```http
GET /api/v1/admin/dashboard/stats?period=30d HTTP/1.1
Host: api.anvil.com
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Success Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "period": "30d",
    "timestamp": "2025-11-16T20:00:00Z",
    "compliance_overview": {
      "total_users": 1234,
      "kyc_approved": 892,
      "kyc_pending": 45,
      "kyc_rejected": 12,
      "kyc_approval_rate": 98.7,
      "avg_kyc_review_time_hours": 4.5
    },
    "transactions": {
      "total": 15234,
      "total_volume_usd": 1245678.90,
      "avg_transaction_usd": 81.75,
      "success_rate": 98.5,
      "flagged_for_review": 12,
      "suspicious_patterns_detected": 0,
      "large_transactions_over_10k": 8
    },
    "aml_compliance": {
      "total_flagged": 12,
      "pending_review": 3,
      "cleared": 9,
      "reported_to_fincen": 8,
      "ofac_matches": 0,
      "rapid_deposits_detected": 1,
      "structuring_patterns": 0
    },
    "financial_summary": {
      "total_deposits": 125678.90,
      "total_withdrawals": 45678.00,
      "net_inflow": 80000.90,
      "fees_collected": 2345.67,
      "subscriptions_revenue": 2106.66
    },
    "system_health": {
      "database_status": "healthy",
      "rpc_status": "healthy",
      "uptime_percent": 99.98,
      "avg_response_time_ms": 120
    },
    "recent_admin_actions": {
      "kyc_approvals_24h": 12,
      "kyc_rejections_24h": 1,
      "user_suspensions_24h": 0,
      "transaction_retries_24h": 2,
      "setting_changes_24h": 1
    }
  }
}
```

**Business Logic:**
1. Aggregates compliance-focused metrics
2. Calculates AML/CTR statistics
3. Summarizes admin activities
4. Returns comprehensive compliance dashboard

**Database Operations:**
```sql
-- User & KYC stats
SELECT 
  COUNT(*) as total,
  SUM(CASE WHEN kyc_status = 'approved' THEN 1 ELSE 0 END) as kyc_approved,
  SUM(CASE WHEN kyc_status = 'pending' THEN 1 ELSE 0 END) as kyc_pending,
  SUM(CASE WHEN kyc_status = 'rejected' THEN 1 ELSE 0 END) as kyc_rejected
FROM users
WHERE role = 2 AND status = 1;

-- Transaction compliance
SELECT 
  COUNT(*) as total,
  SUM(CASE WHEN amount_in > 10000 THEN 1 ELSE 0 END) as over_10k,
  SUM(amount_in) as total_volume
FROM transactions
WHERE created_at >= DATE_SUB(NOW(), INTERVAL 30 DAY)
  AND status = 1;

-- Recent admin actions
SELECT action, COUNT(*) as count
FROM audit_logs
WHERE created_at >= DATE_SUB(NOW(), INTERVAL 24 HOUR)
  AND actor_user_id IN (SELECT id FROM users WHERE role = 0)
GROUP BY action;
```

**Rate Limit:** 60 requests per minute

---

## 3. Audit Logs

Base path: `/api/v1/admin/audit-logs`

### 3.1 GET /audit-logs

Get comprehensive audit trail with advanced filtering.

**Endpoint:** `GET /api/v1/admin/audit-logs`

**Authentication:** Bearer Token (auditor role)

**Query Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `page` | integer | No | Page number (default: 1) |
| `limit` | integer | No | Items per page (max: 100, default: 100) |
| `actor_user_id` | integer | No | Filter by admin user ID |
| `action` | string | No | Filter by action type |
| `entity` | string | No | Filter by entity type |
| `entity_id` | string | No | Filter by entity ID |
| `date_from` | string | No | ISO datetime |
| `date_to` | string | No | ISO datetime |
| `ip_address` | string | No | Filter by IP address |
| `search` | string | No | Full-text search in payload |

**Request:**
```http
GET /api/v1/admin/audit-logs?action=kyc_approved&date_from=2025-11-01T00:00:00Z&date_to=2025-11-30T23:59:59Z&limit=100 HTTP/1.1
Host: api.anvil.com
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

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
        "actor_role": 0,
        "actor_role_label": "ADMIN",
        "action": "kyc_approved",
        "action_category": "user_management",
        "entity": "user",
        "entity_id": "12345",
        "payload_json": {
          "user_email": "john.doe@example.com",
          "admin_email": "admin@anvil.com",
          "notes": "All documents verified. Normal usage pattern.",
          "before": {"kyc_status": "pending"},
          "after": {"kyc_status": "approved"},
          "approval_time": "2025-11-16T14:20:15Z",
          "documents_reviewed": [
            "drivers_license_front",
            "drivers_license_back",
            "selfie_with_id"
          ]
        },
        "ip_address": "192.168.1.100",
        "user_agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)...",
        "created_at": "2025-11-16T14:20:15Z"
      },
      {
        "id": 10024,
        "actor_user_id": 1,
        "actor_email": "admin@anvil.com",
        "actor_role": 0,
        "actor_role_label": "ADMIN",
        "action": "setting_updated",
        "action_category": "configuration",
        "entity": "setting",
        "entity_id": "1",
        "payload_json": {
          "key": "max_daily_trade_limit",
          "before": {"value": "5000"},
          "after": {"value": "10000"},
          "reason": "Increasing limit to accommodate growth...",
          "admin_email": "admin@anvil.com"
        },
        "ip_address": "192.168.1.100",
        "user_agent": "Mozilla/5.0...",
        "created_at": "2025-11-16T15:30:00Z"
      }
    ],
    "pagination": {
      "page": 1,
      "limit": 100,
      "total": 45,
      "total_pages": 1,
      "has_next": false,
      "has_prev": false
    },
    "summary": {
      "total_actions": 45,
      "unique_actors": 2,
      "action_breakdown": {
        "kyc_approved": 12,
        "kyc_rejected": 1,
        "transaction_retried": 2,
        "setting_updated": 1,
        "user_status_changed": 0
      }
    }
  }
}
```

**Database Operations:**
```sql
SELECT al.id, al.actor_user_id, al.action, al.entity, al.entity_id,
       al.payload_json, al.ip_address, al.user_agent, al.created_at,
       u.email as actor_email, u.role as actor_role
FROM audit_logs al
INNER JOIN users u ON al.actor_user_id = u.id
WHERE (? IS NULL OR al.actor_user_id = ?)
  AND (? IS NULL OR al.action = ?)
  AND (? IS NULL OR al.entity = ?)
  AND (? IS NULL OR al.entity_id = ?)
  AND (? IS NULL OR al.created_at >= ?)
  AND (? IS NULL OR al.created_at <= ?)
  AND (? IS NULL OR al.ip_address = ?)
ORDER BY al.created_at DESC
LIMIT ? OFFSET ?;
```

**Rate Limit:** 60 requests per minute

---

### 3.2 GET /audit-logs/:id

Get detailed audit log entry.

**Endpoint:** `GET /api/v1/admin/audit-logs/:id`

**Authentication:** Bearer Token (auditor role)

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `id` | integer | Audit log ID |

**Success Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "id": 10025,
    "actor_user_id": 1,
    "actor_email": "admin@anvil.com",
    "actor_role": 0,
    "actor_firstname": "Admin",
    "actor_lastname": "User",
    "action": "kyc_approved",
    "action_category": "user_management",
    "entity": "user",
    "entity_id": "12345",
    "payload_json": {
      "user_email": "john.doe@example.com",
      "admin_email": "admin@anvil.com",
      "notes": "All documents verified. Normal usage pattern.",
      "before": {"kyc_status": "pending"},
      "after": {"kyc_status": "approved"},
      "approval_time": "2025-11-16T14:20:15Z",
      "documents_reviewed": [
        "drivers_license_front",
        "drivers_license_back",
        "selfie_with_id"
      ],
      "verification_checks": {
        "face_match": 98,
        "liveness_check": true,
        "document_authentic": true
      }
    },
    "ip_address": "192.168.1.100",
    "geolocation": {
      "city": "San Francisco",
      "region": "California",
      "country": "US"
    },
    "user_agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36...",
    "browser": "Chrome 119.0",
    "os": "macOS 10.15.7",
    "created_at": "2025-11-16T14:20:15Z"
  }
}
```

**Rate Limit:** 60 requests per minute

---

## 4. User Data Access

Base path: `/api/v1/admin/users`

### 4.1 GET /users

Get list of all users (read-only).

**Endpoint:** `GET /api/v1/admin/users`

**Authentication:** Bearer Token (auditor role)

**Query Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `page` | integer | Page number |
| `limit` | integer | Items per page (max: 100) |
| `search` | string | Search email, name, uid |
| `role` | integer | Filter by role |
| `status` | integer | Filter by status |
| `kyc_status` | string | Filter by KYC status |
| `created_from` | string | ISO date |
| `created_to` | string | ISO date |
| `sort` | string | Sort field:direction |

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
        "kyc_status": "approved",
        "kyc_completed_at": "2025-11-10T15:00:00Z",
        "email_verified": true,
        "wallet_address": "0x1234...5678",
        "total_transactions": 45,
        "total_volume_usd": 5678.90,
        "subscription_plan": "free",
        "created_at": "2025-11-08T10:30:00Z",
        "last_login_at": "2025-11-16T14:20:00Z"
      }
    ],
    "pagination": {
      "page": 1,
      "limit": 50,
      "total": 1234,
      "total_pages": 25
    }
  }
}
```

**Rate Limit:** 60 requests per minute

---

### 4.2 GET /users/:id

Get detailed user information (read-only).

**Endpoint:** `GET /api/v1/admin/users/:id`

**Authentication:** Bearer Token (auditor role)

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
      "created_at": "2025-11-08T10:30:00Z",
      "last_login_at": "2025-11-16T14:20:00Z"
    },
    "wallet": {
      "address": "0x1234567890abcdef1234567890abcdef12345678",
      "balance_usd": 1234.56
    },
    "statistics": {
      "total_transactions": 45,
      "total_volume_usd": 5678.90,
      "total_fees_paid_usd": 45.67
    },
    "compliance_notes": "No flags or concerns"
  }
}
```

**Rate Limit:** 60 requests per minute

---

### 4.3 GET /users/:id/activity

Get user activity history.

**Endpoint:** `GET /api/v1/admin/users/:id/activity`

**Authentication:** Bearer Token (auditor role)

**Query Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `limit` | integer | Max results (max: 100) |
| `date_from` | string | ISO date |
| `date_to` | string | ISO date |

**Success Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "user_id": 12345,
    "activity": [
      {
        "type": "transaction",
        "action": "swap",
        "details": "Swapped 50 USDC for 0.0204 ETH",
        "amount_usd": 50.00,
        "timestamp": "2025-11-16T13:45:00Z"
      },
      {
        "type": "login",
        "action": "user_login",
        "ip_address": "203.0.113.1",
        "location": "San Francisco, CA, US",
        "timestamp": "2025-11-16T14:20:00Z"
      }
    ],
    "summary": {
      "logins_30d": 15,
      "transactions_30d": 45,
      "avg_transaction_size": 126.20
    }
  }
}
```

**Rate Limit:** 60 requests per minute

---

## 5. Transaction Review

Base path: `/api/v1/admin/transactions`

### 5.1 GET /transactions

Get all transactions (read-only).

**Endpoint:** `GET /api/v1/admin/transactions`

**Authentication:** Bearer Token (auditor role)

**Query Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `page` | integer | Page number |
| `limit` | integer | Items per page (max: 100) |
| `user_id` | integer | Filter by user |
| `type` | integer | Filter by type |
| `status` | integer | Filter by status |
| `chain` | string | Filter by chain |
| `min_amount` | number | Min USD amount |
| `max_amount` | number | Max USD amount |
| `date_from` | string | ISO date |
| `date_to` | string | ISO date |
| `flagged` | boolean | Show flagged only |

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
        "type": 0,
        "type_label": "SWAP",
        "chain": "arbitrum",
        "asset_in": "USDC",
        "amount_in": "50.0",
        "asset_out": "ETH",
        "amount_out": "0.0204",
        "amount_usd": 50.00,
        "fee_usd": 0.35,
        "tx_hash": "0xswap123...",
        "status": 1,
        "status_label": "SUCCESS",
        "compliance_flag": null,
        "confirmed_at": "2025-11-16T13:45:30Z",
        "created_at": "2025-11-16T13:45:00Z"
      },
      {
        "id": 790,
        "user_id": 12346,
        "user_email": "another@email.com",
        "type": 1,
        "type_label": "FUND",
        "chain": "arbitrum",
        "asset_in": "USD",
        "amount_in": "12500.0",
        "asset_out": "USDC",
        "amount_out": "12500.0",
        "amount_usd": 12500.00,
        "fee_usd": 362.50,
        "tx_hash": "0xfund456...",
        "status": 1,
        "status_label": "SUCCESS",
        "compliance_flag": "OVER_10K_CTR",
        "confirmed_at": "2025-11-16T15:30:00Z",
        "created_at": "2025-11-16T15:28:00Z"
      }
    ],
    "pagination": {
      "page": 1,
      "limit": 50,
      "total": 15234
    },
    "summary": {
      "total_volume_usd": 1245678.90,
      "flagged_count": 12,
      "over_10k_count": 8
    }
  }
}
```

**Rate Limit:** 60 requests per minute

---

### 5.2 GET /transactions/:id/compliance

Get compliance analysis for transaction.

**Endpoint:** `GET /api/v1/admin/transactions/:id/compliance`

**Authentication:** Bearer Token (auditor role)

**Success Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "transaction_id": 790,
    "amount_usd": 12500.00,
    "compliance_checks": {
      "ctr_required": true,
      "ctr_threshold": 10000,
      "ofac_check": "passed",
      "wallet_screening": "clean",
      "rapid_deposit_check": "passed",
      "structuring_check": "passed"
    },
    "risk_assessment": "low-medium",
    "risk_factors": [
      {
        "factor": "Large single transaction",
        "severity": "medium",
        "description": "Amount exceeds $10,000 CTR threshold"
      }
    ],
    "recommendations": [
      "File CTR with FinCEN",
      "Document business purpose if contacted",
      "Monitor user for next 30 days"
    ],
    "user_context": {
      "account_age_days": 8,
      "kyc_status": "approved",
      "previous_large_transactions": 0,
      "total_deposits_30d": 12500.00
    }
  }
}
```

**Rate Limit:** 60 requests per minute

---

## 6. Financial Reporting

Base path: `/api/v1/admin/reports`

### 6.1 POST /reports/financial

Generate financial report.

**Endpoint:** `POST /api/v1/admin/reports/financial`

**Authentication:** Bearer Token (auditor role)

**Request:**
```http
POST /api/v1/admin/reports/financial HTTP/1.1
Host: api.anvil.com
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json

{
  "report_type": "monthly",
  "period": "2025-11",
  "include": [
    "revenue",
    "volume",
    "users",
    "fees",
    "subscriptions",
    "costs"
  ],
  "format": "json"
}
```

**Request Body Schema:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `report_type` | string | ✅ Yes | 'daily', 'weekly', 'monthly', 'quarterly', 'annual', 'custom' |
| `period` | string | ✅ Yes | Period identifier (e.g., '2025-11', 'Q4-2025') |
| `date_from` | string | If custom | ISO date |
| `date_to` | string | If custom | ISO date |
| `include` | array | ✅ Yes | Report sections to include |
| `format` | string | No | 'json', 'csv', 'xlsx' (default: 'json') |

**Success Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "report_id": "report_nov2025_abc123",
    "report_type": "monthly",
    "period": "2025-11",
    "generated_at": "2025-11-16T20:30:00Z",
    "generated_by": "auditor@compliance-firm.com",
    "data": {
      "summary": {
        "period_label": "November 2025",
        "start_date": "2025-11-01T00:00:00Z",
        "end_date": "2025-11-30T23:59:59Z",
        "days_in_period": 30
      },
      "revenue": {
        "total_funding": 125678.90,
        "subscriptions": 2106.66,
        "fees_collected": 2345.67,
        "total_revenue": 130131.23
      },
      "volume": {
        "total_transactions": 15234,
        "total_volume_usd": 1245678.90,
        "by_type": {
          "swap": 890456.00,
          "fund": 125678.90,
          "earn": 189543.00,
          "save": 40001.00
        }
      },
      "users": {
        "total_active": 1234,
        "new_users": 156,
        "churned_users": 23,
        "net_growth": 133,
        "growth_rate": 12.1
      },
      "fees": {
        "stripe_fees": 3650.27,
        "network_fees": 1234.56,
        "total_fees": 4884.83
      },
      "subscriptions": {
        "active_count": 211,
        "new_subscriptions": 28,
        "canceled": 12,
        "mrr": 2106.66,
        "churn_rate": 5.4
      },
      "costs": {
        "ai_costs": 345.67,
        "infrastructure": 1200.00,
        "total_costs": 1545.67
      },
      "profitability": {
        "gross_revenue": 130131.23,
        "total_costs": 6430.50,
        "net_revenue": 123700.73,
        "profit_margin": 95.06
      }
    }
  }
}
```

**Business Logic:**
1. Validates date range
2. Aggregates financial data from multiple tables
3. Calculates metrics and ratios
4. Returns comprehensive financial report

**Database Operations:**
```sql
-- Revenue from funding
SELECT 
  SUM(amount_fiat) as total_funding,
  SUM(fee_stripe + fee_network) as total_fees
FROM funding_transactions
WHERE status = 'completed'
  AND DATE(completed_at) BETWEEN '2025-11-01' AND '2025-11-30';

-- Subscriptions
SELECT 
  COUNT(*) as active_subscriptions,
  SUM(price_monthly) as mrr
FROM subscriptions
WHERE status = 'active'
  AND DATE(created_at) <= '2025-11-30';

-- User growth
SELECT 
  COUNT(*) as new_users
FROM users
WHERE DATE(created_at) BETWEEN '2025-11-01' AND '2025-11-30';

-- AI costs
SELECT 
  SUM(cost_usd) as total_ai_cost
FROM llm_conversations
WHERE DATE(created_at) BETWEEN '2025-11-01' AND '2025-11-30';
```

**Rate Limit:** 10 requests per minute

---

## 7. Export Operations

Base path: `/api/v1/admin/export`

### 7.1 POST /export/audit-logs

Export audit logs to file.

**Endpoint:** `POST /api/v1/admin/export/audit-logs`

**Authentication:** Bearer Token (auditor role)

**Request:**
```http
POST /api/v1/admin/export/audit-logs HTTP/1.1
Host: api.anvil.com
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json

{
  "date_from": "2025-11-01T00:00:00Z",
  "date_to": "2025-11-30T23:59:59Z",
  "format": "csv",
  "filters": {
    "action": "kyc_approved"
  }
}
```

**Success Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "export_id": "export_abc123",
    "format": "csv",
    "status": "completed",
    "file_url": "https://exports.anvil.com/audit-logs-nov2025-abc123.csv",
    "file_size_bytes": 245678,
    "record_count": 45,
    "generated_at": "2025-11-16T20:35:00Z",
    "expires_at": "2025-11-17T20:35:00Z"
  }
}
```

**Rate Limit:** 5 requests per minute

---

### 7.2 POST /export/transactions

Export transaction data.

**Endpoint:** `POST /api/v1/admin/export/transactions`

**Authentication:** Bearer Token (auditor role)

**Request:**
```http
POST /api/v1/admin/export/transactions HTTP/1.1
Host: api.anvil.com
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json

{
  "date_from": "2025-11-01T00:00:00Z",
  "date_to": "2025-11-30T23:59:59Z",
  "format": "xlsx",
  "filters": {
    "min_amount": 10000
  }
}
```

**Success Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "export_id": "export_def456",
    "format": "xlsx",
    "status": "completed",
    "file_url": "https://exports.anvil.com/transactions-nov2025-def456.xlsx",
    "file_size_bytes": 1567890,
    "record_count": 8,
    "generated_at": "2025-11-16T20:40:00Z",
    "expires_at": "2025-11-17T20:40:00Z"
  }
}
```

**Rate Limit:** 5 requests per minute

---

### 7.3 POST /export/users

Export user data (GDPR compliant).

**Endpoint:** `POST /api/v1/admin/export/users`

**Authentication:** Bearer Token (auditor role)

**Request:**
```http
POST /api/v1/admin/export/users HTTP/1.1
Host: api.anvil.com
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json

{
  "user_ids": [12345, 12346],
  "format": "json",
  "include_pii": true,
  "reason": "Regulatory audit request"
}
```

**Success Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "export_id": "export_ghi789",
    "format": "json",
    "status": "completed",
    "file_url": "https://exports.anvil.com/users-ghi789.json",
    "file_size_bytes": 45678,
    "record_count": 2,
    "generated_at": "2025-11-16T20:45:00Z",
    "expires_at": "2025-11-17T20:45:00Z"
  }
}
```

**Business Logic:**
1. Validates auditor permissions
2. Logs export request to audit_logs
3. Generates export file
4. Uploads to secure temporary storage
5. Returns download URL (24-hour expiry)
6. All export requests are logged for compliance

**Database Operations:**
```sql
-- Log export request
INSERT INTO audit_logs (
  actor_user_id, action, entity, entity_id, payload_json,
  ip_address, created_at
) VALUES (?, 'data_exported', 'export', ?, ?, ?, NOW());

-- Export data (example for users)
SELECT *
FROM users
WHERE id IN (?, ?)
  AND status != 2;
```

**Rate Limit:** 5 requests per minute

---

## Standard Response Format

All endpoints return consistent format:

**Success:**
```json
{
  "success": true,
  "data": { ... },
  "read_only_notice": "This is a read-only view"
}
```

**Error:**
```json
{
  "success": false,
  "error": {
    "code": "ERROR_CODE",
    "message": "Description",
    "timestamp": "2025-11-16T20:00:00Z",
    "request_id": "req_xyz789"
  }
}
```

---

## Common Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `UNAUTHORIZED` | 401 | Invalid or expired auditor token |
| `FORBIDDEN` | 403 | Insufficient auditor permissions |
| `READ_ONLY_ACCESS` | 403 | Attempted write operation (not allowed) |
| `NOT_FOUND` | 404 | Resource not found |
| `RATE_LIMIT_EXCEEDED` | 429 | Too many requests |
| `SERVER_ERROR` | 500 | Internal server error |

---

## Key Differences from ADMIN API

| Feature | ADMIN | AUDITOR |
|---------|-------|---------|
| **HTTP Methods** | GET, POST, PATCH, DELETE | GET, POST (exports only) |
| **Modify Data** | ✅ Yes | ❌ No |
| **Approve KYC** | ✅ Yes | ❌ No (view only) |
| **Retry Transactions** | ✅ Yes | ❌ No (view only) |
| **Update Settings** | ✅ Yes | ❌ No (view only) |
| **View Audit Logs** | ✅ Yes | ✅ Yes |
| **Export Data** | ✅ Yes | ✅ Yes |
| **Generate Reports** | ✅ Yes | ✅ Yes |
| **All Actions Logged** | ✅ Yes | ✅ Yes |

---

## Compliance Features

1. **Complete Audit Trail:** All view access is logged
2. **Data Export:** GDPR-compliant data export
3. **Time-Limited URLs:** Export URLs expire after 24 hours
4. **Read-Only Guarantee:** No write operations possible
5. **Comprehensive Logging:** Every query is logged with user, timestamp, and IP

---

**Document Status:** AUDITOR API Complete ✅  
**Total Endpoints:** 20+  
**Access Level:** Read-only for compliance ✅  
**All API documentation complete!** 🎉
