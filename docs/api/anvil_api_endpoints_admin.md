# 🔌 Anvil API Endpoints - ADMIN Users

## Base Information

**Base URL:** `https://api.anvil.com/v1/admin`  
**Authentication:** Bearer JWT Token (Admin role)  
**Content-Type:** `application/json`  
**User Role Required:** `role=0` (ADMIN)  
**Access Level:** Full CRUD operations on all resources

---

## Table of Contents

1. [Authentication](#authentication)
2. [User Management](#user-management)
3. [KYC Management](#kyc-management)
4. [Transaction Management](#transaction-management)
5. [Wallet Management](#wallet-management)
6. [Perpetual Positions](#perpetual-positions)
7. [Earn Positions](#earn-positions)
8. [System Settings](#system-settings)
9. [AI Models](#ai-models)
10. [Subscriptions](#subscriptions)
11. [Audit Logs](#audit-logs)
12. [Analytics](#analytics)

---

## Authentication

### POST `/auth/login`

**Description:** Admin login with email and password

**Authentication:** None (public endpoint)

**Request Body:**
```json
{
  "email": "admin@anvil.com",
  "password": "secure_password",
  "totp_code": "123456"
}
```

**Response 200 OK:**
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
      "permissions": ["*"]
    }
  }
}
```

**Response 401 Unauthorized:**
```json
{
  "success": false,
  "error": {
    "code": "INVALID_CREDENTIALS",
    "message": "Invalid email or password"
  }
}
```

**Response 403 Forbidden:**
```json
{
  "success": false,
  "error": {
    "code": "2FA_REQUIRED",
    "message": "Two-factor authentication code required"
  }
}
```

---

## User Management

### GET `/users`

**Description:** Get all users with filtering and pagination

**Authentication:** Required (Admin)

**Query Parameters:**
- `page` (default: 1): Page number
- `limit` (default: 50, max: 100): Items per page
- `role` (optional): Filter by role (0=ADMIN, 1=AUDITOR, 2=CLIENT)
- `status` (optional): Filter by status (0=INACTIVE, 1=ACTIVE, 2=DELETED)
- `kyc_status` (optional): Filter by KYC status
- `search` (optional): Search by email, name, or UID
- `sort` (optional): Sort field and direction (e.g., `created_at:desc`)

**Response 200 OK:**
```json
{
  "success": true,
  "data": {
    "users": [
      {
        "id": 12345,
        "uid": "usr_abc123",
        "email": "john.doe@example.com",
        "firstname": "John",
        "lastname": "Doe",
        "phone": "+1234567890",
        "role": 2,
        "role_label": "CLIENT",
        "status": 1,
        "status_label": "ACTIVE",
        "email_verified": true,
        "kyc_status": "approved",
        "kyc_completed_at": "2025-11-16T10:00:00Z",
        "created_at": "2025-11-16T10:00:00Z",
        "last_login_at": "2025-11-16T15:30:00Z",
        "wallet": {
          "address": "0x1234...5678",
          "balance_usd": 171.32
        },
        "stats": {
          "transaction_count": 45,
          "total_volume_usd": 2345.67
        }
      }
    ],
    "pagination": {
      "page": 1,
      "limit": 50,
      "total": 1234,
      "pages": 25
    },
    "summary": {
      "total_users": 1234,
      "active_users": 892,
      "pending_kyc": 45
    }
  }
}
```

---

### GET `/users/:id`

**Description:** Get detailed user information

**Authentication:** Required (Admin)

**Path Parameters:**
- `id`: User ID or UID

**Response 200 OK:**
```json
{
  "success": true,
  "data": {
    "user": {
      "id": 12345,
      "uid": "usr_abc123",
      "privy_user_id": "did:privy:clk1abc",
      "email": "john.doe@example.com",
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
    },
    "wallet": {
      "id": 67890,
      "address": "0x1234567890abcdef1234567890abcdef12345678",
      "privy_wallet_id": "0xprivy123",
      "default_chain": "arbitrum",
      "total_balance_usd": 171.32
    },
    "subscription": {
      "plan": "pro",
      "status": "active",
      "monthly_cost": 9.99
    },
    "stats": {
      "total_transactions": 45,
      "total_volume_usd": 2345.67,
      "total_fees_paid_usd": 45.67,
      "avg_transaction_size_usd": 52.13,
      "success_rate_percent": 97.8,
      "ai_conversations": 123,
      "ai_cost_usd": 0.45
    }
  }
}
```

---

### PATCH `/users/:id`

**Description:** Update user information or status

**Authentication:** Required (Admin)

**Request Body:**
```json
{
  "status": 1,
  "kyc_status": "approved",
  "notes": "Manual verification completed"
}
```

**Response 200 OK:**
```json
{
  "success": true,
  "data": {
    "user_id": 12345,
    "status": 1,
    "kyc_status": "approved",
    "updated_at": "2025-11-16T16:00:00Z",
    "updated_by": "admin@anvil.com"
  },
  "audit_log_id": 10001
}
```

---

### DELETE `/users/:id`

**Description:** Soft delete user (sets status to DELETED)

**Authentication:** Required (Admin)

**Path Parameters:**
- `id`: User ID

**Request Body:**
```json
{
  "reason": "User requested account deletion"
}
```

**Response 200 OK:**
```json
{
  "success": true,
  "data": {
    "user_id": 12345,
    "status": 2,
    "deleted_at": "2025-11-16T16:00:00Z"
  },
  "audit_log_id": 10002
}
```

---

## KYC Management

### GET `/users/:id/kyc`

**Description:** Get user's KYC documents and verification status

**Authentication:** Required (Admin)

**Response 200 OK:**
```json
{
  "success": true,
  "data": {
    "user_id": 12345,
    "kyc_status": "pending",
    "submitted_at": "2025-11-15T10:00:00Z",
    "personal_info": {
      "firstname": "John",
      "lastname": "Doe",
      "date_of_birth": "1990-05-15",
      "address": "123 Main St, New York, NY 10001",
      "country": "United States",
      "phone": "+1234567890"
    },
    "documents": [
      {
        "type": "drivers_license_front",
        "url": "https://storage.anvil.com/kyc/12345/dl_front.jpg",
        "uploaded_at": "2025-11-15T10:00:00Z",
        "verification": {
          "authentic": true,
          "expiry_date": "2028-05-15",
          "name_match": true,
          "dob_match": true
        }
      },
      {
        "type": "drivers_license_back",
        "url": "https://storage.anvil.com/kyc/12345/dl_back.jpg",
        "uploaded_at": "2025-11-15T10:00:00Z",
        "verification": {
          "barcode_scan": true
        }
      },
      {
        "type": "selfie_with_id",
        "url": "https://storage.anvil.com/kyc/12345/selfie.jpg",
        "uploaded_at": "2025-11-15T10:00:00Z",
        "verification": {
          "face_match": 98,
          "liveness_check": true
        }
      }
    ],
    "verification_checks": {
      "identity_verified": true,
      "address_verified": true,
      "sanctions_check": "clear",
      "risk_score": "low"
    }
  }
}
```

---

### PATCH `/users/:id/kyc`

**Description:** Approve or reject KYC application

**Authentication:** Required (Admin)

**Request Body:**
```json
{
  "action": "approve",
  "notes": "All documents verified. Normal usage pattern."
}
```

**Response 200 OK:**
```json
{
  "success": true,
  "data": {
    "user_id": 12345,
    "kyc_status": "approved",
    "approved_at": "2025-11-16T16:00:00Z",
    "approved_by": "admin@anvil.com"
  },
  "audit_log_id": 10003
}
```

---

## Transaction Management

### GET `/transactions`

**Description:** Get all transactions with filtering

**Authentication:** Required (Admin)

**Query Parameters:**
- `page` (default: 1)
- `limit` (default: 100)
- `user_id` (optional): Filter by user
- `type` (optional): Filter by transaction type
- `status` (optional): Filter by status
- `chain` (optional): Filter by chain
- `date_from` (optional): Start date
- `date_to` (optional): End date
- `min_amount` (optional): Minimum amount filter
- `max_amount` (optional): Maximum amount filter

**Response 200 OK:**
```json
{
  "success": true,
  "data": {
    "transactions": [
      {
        "id": 789,
        "user_id": 12345,
        "user_email": "john.doe@example.com",
        "type": 0,
        "type_label": "SWAP",
        "chain": "arbitrum",
        "asset_in": "USDC",
        "amount_in": "50.0",
        "asset_out": "ETH",
        "amount_out": "0.0204",
        "fee_usd": 0.37,
        "tx_hash": "0xabc123...",
        "status": 1,
        "status_label": "SUCCESS",
        "created_at": "2025-11-16T14:30:00Z",
        "confirmed_at": "2025-11-16T14:31:00Z"
      }
    ],
    "pagination": {
      "page": 1,
      "limit": 100,
      "total": 15234
    },
    "summary": {
      "total_volume_usd": 1245678.90,
      "total_fees_usd": 12456.78,
      "success_rate": 98.5
    }
  }
}
```

---

### GET `/transactions/:id`

**Description:** Get detailed transaction information

**Authentication:** Required (Admin)

**Response 200 OK:**
```json
{
  "success": true,
  "data": {
    "transaction": {
      "id": 789,
      "user_id": 12345,
      "wallet_id": 67890,
      "type": 0,
      "chain": "arbitrum",
      "asset_in": "USDC",
      "amount_in": "50.0",
      "asset_out": "ETH",
      "amount_out": "0.0204",
      "fee": "0.00015",
      "fee_usd": 0.37,
      "tx_hash": "0xabc123def456...",
      "status": 1,
      "dex_aggregator": "1inch",
      "dex_route": {},
      "slippage": 0.5,
      "block_number": 12345678,
      "confirmed_at": "2025-11-16T14:31:00Z",
      "created_at": "2025-11-16T14:30:00Z"
    },
    "user": {
      "email": "john.doe@example.com",
      "kyc_status": "approved"
    },
    "wallet": {
      "address": "0x1234...5678"
    }
  }
}
```

---

### POST `/transactions/:id/retry`

**Description:** Retry a failed transaction

**Authentication:** Required (Admin)

**Path Parameters:**
- `id`: Transaction ID

**Request Body:**
```json
{
  "override_gas_price": 1.2,
  "reason": "Network congestion caused initial failure"
}
```

**Response 200 OK:**
```json
{
  "success": true,
  "data": {
    "original_tx_id": 458,
    "new_tx_id": 460,
    "tx_hash": "0xretry789...",
    "status": "pending",
    "created_at": "2025-11-16T16:00:00Z"
  },
  "audit_log_id": 10004
}
```

---

## Wallet Management

### GET `/wallets`

**Description:** Get all wallets with balances

**Authentication:** Required (Admin)

**Query Parameters:**
- `page` (default: 1)
- `limit` (default: 100)
- `chain` (optional): Filter by chain
- `min_balance` (optional): Minimum balance filter

**Response 200 OK:**
```json
{
  "success": true,
  "data": {
    "wallets": [
      {
        "id": 67890,
        "user_id": 12345,
        "user_email": "john.doe@example.com",
        "address": "0x1234...5678",
        "default_chain": "arbitrum",
        "total_balance_usd": 171.32,
        "chains": [
          {
            "chain": "arbitrum",
            "balance_usd": 120.35
          },
          {
            "chain": "hyperliquid",
            "balance_usd": 50.97
          }
        ],
        "created_at": "2025-11-16T10:00:00Z"
      }
    ],
    "pagination": {
      "page": 1,
      "total": 1234
    },
    "summary": {
      "total_wallets": 1234,
      "total_value_usd": 5678901.23
    }
  }
}
```

---

## Perpetual Positions

### GET `/perpetuals/positions`

**Description:** Get all perpetual positions across all users

**Authentication:** Required (Admin)

**Query Parameters:**
- `page` (default: 1)
- `limit` (default: 100)
- `status` (optional): `open`, `closed`, `liquidated`
- `symbol` (optional): Filter by trading pair
- `user_id` (optional): Filter by user

**Response 200 OK:**
```json
{
  "success": true,
  "data": {
    "positions": [
      {
        "id": 301,
        "user_id": 12345,
        "user_email": "john.doe@example.com",
        "symbol": "ETH-USD",
        "side": "long",
        "leverage": 5.0,
        "size": "0.102",
        "entry_price": 2450.50,
        "mark_price": 2460.00,
        "liquidation_price": 1960.40,
        "unrealized_pnl": "0.969",
        "margin": "50.0",
        "status": "open",
        "distance_to_liquidation_percent": 20.31,
        "opened_at": "2025-11-16T15:00:00Z"
      }
    ],
    "pagination": {
      "page": 1,
      "total": 234
    },
    "summary": {
      "total_positions": 234,
      "open_positions": 189,
      "total_notional_usd": 567890.12,
      "total_margin_usd": 123456.78
    }
  }
}
```

---

### POST `/perpetuals/positions/:id/force-close`

**Description:** Force close a position (emergency)

**Authentication:** Required (Admin)

**Request Body:**
```json
{
  "reason": "Risk management - user approaching liquidation"
}
```

**Response 200 OK:**
```json
{
  "success": true,
  "data": {
    "position_id": 301,
    "symbol": "ETH-USD",
    "status": "closed",
    "exit_price": 2465.00,
    "realized_pnl": "1.479",
    "closed_at": "2025-11-16T16:00:00Z"
  },
  "audit_log_id": 10005
}
```

---

## Earn Positions

### GET `/earn/positions`

**Description:** Get all earn positions across all users

**Authentication:** Required (Admin)

**Query Parameters:**
- `page` (default: 1)
- `limit` (default: 100)
- `status` (optional): `active`, `withdrawn`, `emergency_exit`
- `protocol` (optional): Filter by protocol
- `chain` (optional): Filter by chain

**Response 200 OK:**
```json
{
  "success": true,
  "data": {
    "positions": [
      {
        "id": 101,
        "user_id": 12345,
        "user_email": "john.doe@example.com",
        "protocol": "aave",
        "chain": "arbitrum",
        "asset": "USDC",
        "amount_deposited": "70.0",
        "current_value": "70.06",
        "rewards_earned": "0.06",
        "apy": 4.2,
        "status": "active",
        "deposited_at": "2025-11-13T15:30:00Z"
      }
    ],
    "pagination": {
      "page": 1,
      "total": 456
    },
    "summary": {
      "total_tvl_usd": 456789.12,
      "total_rewards_usd": 5678.90,
      "avg_apy": 4.3
    }
  }
}
```

---

### POST `/earn/positions/:id/emergency-withdraw`

**Description:** Emergency withdraw from compromised protocol

**Authentication:** Required (Admin)

**Request Body:**
```json
{
  "reason": "Protocol exploit detected - emergency withdrawal"
}
```

**Response 200 OK:**
```json
{
  "success": true,
  "data": {
    "position_id": 101,
    "status": "emergency_exit",
    "amount_withdrawn": "70.06",
    "tx_hash": "0xemergency123...",
    "withdrawn_at": "2025-11-16T16:00:00Z"
  },
  "audit_log_id": 10006
}
```

---

## System Settings

### GET `/settings`

**Description:** Get all system settings

**Authentication:** Required (Admin)

**Response 200 OK:**
```json
{
  "success": true,
  "data": [
    {
      "id": 1,
      "key": "max_daily_trade_limit",
      "value": "10000",
      "scope": 0,
      "scope_label": "GLOBAL",
      "is_sensitive": false,
      "description": "Maximum daily trading limit per user (USD)",
      "updated_at": "2025-11-16T16:00:00Z",
      "updated_by": "admin@anvil.com"
    },
    {
      "id": 2,
      "key": "stripe_api_key",
      "value": "sk_live_••••••••",
      "scope": 2,
      "scope_label": "PAYMENTS",
      "is_sensitive": true,
      "description": "Stripe API key for payment processing",
      "updated_at": "2025-10-01T10:00:00Z",
      "updated_by": "admin@anvil.com"
    }
  ]
}
```

---

### PATCH `/settings/:id`

**Description:** Update a system setting

**Authentication:** Required (Admin)

**Request Body:**
```json
{
  "value": "15000",
  "reason": "Increasing limit based on user feedback"
}
```

**Response 200 OK:**
```json
{
  "success": true,
  "data": {
    "setting_id": 1,
    "key": "max_daily_trade_limit",
    "value": "15000",
    "previous_value": "10000",
    "updated_at": "2025-11-16T16:00:00Z",
    "updated_by": "admin@anvil.com"
  },
  "audit_log_id": 10007
}
```

---

## AI Models

### GET `/models`

**Description:** Get AI model configuration and statistics

**Authentication:** Required (Admin)

**Response 200 OK:**
```json
{
  "success": true,
  "data": [
    {
      "id": 1,
      "provider": "vertex",
      "model_name": "gemini-1.5-flash",
      "label": "Gemini Flash (Fast & Cheap)",
      "is_default": true,
      "is_available": true,
      "cost_per_1k_input_tokens": 0.00002,
      "cost_per_1k_output_tokens": 0.00006,
      "max_tokens": 1000000,
      "status": 1,
      "request_count": 10234,
      "total_cost_usd": 123.45,
      "avg_latency_ms": 850,
      "success_rate": 99.1
    },
    {
      "id": 2,
      "provider": "bedrock",
      "model_name": "anthropic.claude-3-5-sonnet-20241022-v2:0",
      "label": "Claude 3.5 Sonnet v2",
      "is_default": true,
      "is_available": true,
      "cost_per_1k_input_tokens": 0.00300,
      "cost_per_1k_output_tokens": 0.01500,
      "max_tokens": 200000,
      "status": 1,
      "request_count": 332,
      "total_cost_usd": 45.67,
      "avg_latency_ms": 1240,
      "success_rate": 98.5
    }
  ]
}
```

---

### PATCH `/models/:id`

**Description:** Update model configuration

**Authentication:** Required (Admin)

**Request Body:**
```json
{
  "is_available": false,
  "reason": "Model maintenance scheduled"
}
```

**Response 200 OK:**
```json
{
  "success": true,
  "data": {
    "model_id": 1,
    "is_available": false,
    "updated_at": "2025-11-16T16:00:00Z"
  },
  "audit_log_id": 10008
}
```

---

## Subscriptions

### GET `/subscriptions`

**Description:** Get all user subscriptions

**Authentication:** Required (Admin)

**Query Parameters:**
- `page` (default: 1)
- `limit` (default: 100)
- `plan` (optional): Filter by plan
- `status` (optional): Filter by status

**Response 200 OK:**
```json
{
  "success": true,
  "data": {
    "subscriptions": [
      {
        "id": 501,
        "user_id": 12345,
        "user_email": "john.doe@example.com",
        "stripe_subscription_id": "sub_stripe456",
        "plan": "pro",
        "status": "active",
        "price_monthly": 9.99,
        "billing_cycle_start": "2025-11-16T00:00:00Z",
        "billing_cycle_end": "2025-12-16T00:00:00Z",
        "created_at": "2025-11-16T10:00:00Z"
      }
    ],
    "pagination": {
      "page": 1,
      "total": 456
    },
    "summary": {
      "total_subscriptions": 456,
      "active_subscriptions": 412,
      "mrr": 4107.88,
      "churn_rate": 2.5
    }
  }
}
```

---

### POST `/subscriptions/:id/refund`

**Description:** Process subscription refund

**Authentication:** Required (Admin)

**Request Body:**
```json
{
  "amount": 9.99,
  "reason": "Customer requested refund - service issue"
}
```

**Response 200 OK:**
```json
{
  "success": true,
  "data": {
    "subscription_id": 501,
    "refund_id": "re_stripe123",
    "amount": 9.99,
    "status": "succeeded",
    "refunded_at": "2025-11-16T16:00:00Z"
  },
  "audit_log_id": 10009
}
```

---

## Audit Logs

### GET `/audit-logs`

**Description:** Get audit trail of all admin actions

**Authentication:** Required (Admin)

**Query Parameters:**
- `page` (default: 1)
- `limit` (default: 100)
- `actor_user_id` (optional): Filter by admin who performed action
- `action` (optional): Filter by action type
- `entity` (optional): Filter by entity type
- `date_from` (optional): Start date
- `date_to` (optional): End date

**Response 200 OK:**
```json
{
  "success": true,
  "data": {
    "logs": [
      {
        "id": 10001,
        "actor_user_id": 1,
        "actor_email": "admin@anvil.com",
        "action": "kyc_approved",
        "entity": "user",
        "entity_id": "12345",
        "summary": "Approved KYC for john.doe@example.com",
        "ip_address": "192.168.1.100",
        "created_at": "2025-11-16T16:00:00Z"
      }
    ],
    "pagination": {
      "page": 1,
      "total": 5432
    }
  }
}
```

---

### GET `/audit-logs/:id`

**Description:** Get detailed audit log with full payload

**Authentication:** Required (Admin)

**Response 200 OK:**
```json
{
  "success": true,
  "data": {
    "log": {
      "id": 10001,
      "actor_user_id": 1,
      "actor_email": "admin@anvil.com",
      "action": "kyc_approved",
      "entity": "user",
      "entity_id": "12345",
      "payload_json": {
        "user_email": "john.doe@example.com",
        "notes": "All documents verified",
        "before": {"kyc_status": "pending"},
        "after": {"kyc_status": "approved"}
      },
      "ip_address": "192.168.1.100",
      "user_agent": "Mozilla/5.0...",
      "created_at": "2025-11-16T16:00:00Z"
    }
  }
}
```

---

## Analytics

### GET `/dashboard/stats`

**Description:** Get dashboard statistics and metrics

**Authentication:** Required (Admin)

**Response 200 OK:**
```json
{
  "success": true,
  "data": {
    "users": {
      "total": 1234,
      "active_24h": 234,
      "new_today": 12,
      "growth_rate_7d": 5.2
    },
    "transactions": {
      "total_24h": 567,
      "success_rate": 98.2,
      "total_volume_usd_24h": 45678.90,
      "avg_transaction_usd": 80.56
    },
    "llm": {
      "total_calls_24h": 5678,
      "total_cost_24h": 11.23,
      "avg_cost_per_call": 0.002,
      "success_rate": 99.1,
      "vertex_calls": 5346,
      "bedrock_calls": 332
    },
    "agents": {
      "total_executions_24h": 234,
      "success_rate": 96.5,
      "avg_execution_time_ms": 4567,
      "avg_cost": 0.003
    },
    "revenue": {
      "total_funding_24h": 12345.67,
      "subscriptions_mrr": 2106.66,
      "total_fees_collected_24h": 567.89
    },
    "system_health": {
      "database_connections": 45,
      "api_response_time_ms": 123,
      "uptime_percent": 99.98
    },
    "timestamp": "2025-11-16T16:00:00Z"
  }
}
```

---

### GET `/analytics/users`

**Description:** Get user analytics and trends

**Authentication:** Required (Admin)

**Query Parameters:**
- `period` (default: 7d): Time period (1d, 7d, 30d, 90d, 1y)
- `group_by` (default: day): Group by (hour, day, week, month)

**Response 200 OK:**
```json
{
  "success": true,
  "data": {
    "period": "7d",
    "group_by": "day",
    "metrics": [
      {
        "date": "2025-11-16",
        "new_users": 12,
        "active_users": 234,
        "kyc_approved": 5,
        "total_users": 1234
      },
      {
        "date": "2025-11-15",
        "new_users": 15,
        "active_users": 218,
        "kyc_approved": 8,
        "total_users": 1222
      }
    ],
    "summary": {
      "total_new_users": 89,
      "avg_daily_active": 225,
      "growth_rate": 5.2
    }
  }
}
```

---

### GET `/analytics/transactions`

**Description:** Get transaction analytics

**Authentication:** Required (Admin)

**Query Parameters:**
- `period` (default: 7d)
- `group_by` (default: day)
- `type` (optional): Filter by transaction type

**Response 200 OK:**
```json
{
  "success": true,
  "data": {
    "metrics": [
      {
        "date": "2025-11-16",
        "total_transactions": 567,
        "total_volume_usd": 45678.90,
        "success_count": 557,
        "failed_count": 10,
        "success_rate": 98.2
      }
    ],
    "summary": {
      "total_transactions": 3456,
      "total_volume_usd": 234567.89,
      "avg_daily_volume": 33509.70,
      "success_rate": 98.5
    }
  }
}
```

---

### GET `/analytics/revenue`

**Description:** Get revenue analytics

**Authentication:** Required (Admin)

**Response 200 OK:**
```json
{
  "success": true,
  "data": {
    "metrics": [
      {
        "date": "2025-11-16",
        "funding_revenue": 185.55,
        "subscription_revenue": 329.67,
        "trading_fees": 52.67,
        "total_revenue": 567.89
      }
    ],
    "summary": {
      "total_revenue_7d": 3456.78,
      "mrr": 2106.66,
      "arr": 25279.92,
      "avg_daily_revenue": 493.83
    }
  }
}
```

---

## Rate Limits

**Per Admin:**
- General endpoints: 200 requests/minute
- Write operations: 50/minute
- Analytics endpoints: 100/minute

**Headers Returned:**
```http
X-RateLimit-Limit: 200
X-RateLimit-Remaining: 195
X-RateLimit-Reset: 1700000060
```

---

## Audit Trail

**All admin actions automatically logged:**
- User modifications
- KYC approvals/rejections
- Transaction retries
- Settings changes
- Model updates
- Emergency actions
- Subscription refunds

**Audit Log Format:**
```json
{
  "id": 10001,
  "actor_user_id": 1,
  "action": "action_name",
  "entity": "entity_type",
  "entity_id": "id",
  "payload_json": {
    "before": {},
    "after": {},
    "reason": "explanation"
  },
  "ip_address": "192.168.1.100",
  "created_at": "2025-11-16T16:00:00Z"
}
```

---

**Total ADMIN Endpoints:** 35+  
**Authentication:** JWT Bearer Token (Admin role)  
**Audit Trail:** All actions logged  
**API Version:** v1  
**Documentation Status:** Production Ready ✅
