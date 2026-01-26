# Subscriptions & Payments Endpoints Specification

> **Last Updated**: 2026-01-25  
> **Status**: Production  
> **Maintainers**: @backend-engineer @error-detective @code-reviewer

---

## Executive Summary

The Subscriptions & Payments system provides endpoints for:
1. **Subscription Management** - Plan listing, subscription creation, cancellation
2. **Payment Processing** - Transaction management, payment history
3. **Stripe Integration** - Checkout sessions, webhook handling

**Base Path**: `/api/v1`  
**Authentication**: Bearer JWT Token (all endpoints require authentication)

---

## 1. Subscription Endpoints

**Base Path**: `/api/v1/subscription`  
**Tag**: `Subscription`

### GET /subscription

List all available subscription plans.

**Authentication**: Required (Bearer Token)

**Response Schema**:
```json
[
  {
    "id": 1,
    "name": "PRO",
    "price": 9.99,
    "currency": "USD",
    "duration": 30,
    "features": {"users": 1, "storage_gb": 10},
    "is_active": true,
    "stripe_product_id": "prod_xxx",
    "stripe_price_id": "price_xxx"
  },
  {
    "id": 2,
    "name": "CORPORATE",
    "price": 49.99,
    "currency": "USD",
    "duration": 30,
    "features": {"users": 10, "storage_gb": 100},
    "is_active": true,
    "stripe_product_id": "prod_yyy",
    "stripe_price_id": "price_yyy"
  }
]
```

**Error Responses**:
| Status | Code | Description |
|--------|------|-------------|
| 401 | Unauthorized | Invalid or missing token |
| 503 | Service Unavailable | Database connection error |

**Source File**: `src/app/presentation/http/controllers/subscription/router.py`

---

### POST /subscription/init

Initialize default subscription plans (PRO and CORPORATE).

**Authentication**: Required (Bearer Token, Admin recommended)

**Description**: Creates default subscription plans in the database and optionally creates corresponding Stripe products/prices if Stripe API key is configured.

**Default Plans**:
| Plan | Price | Duration | Features |
|------|-------|----------|----------|
| PRO | $9.99/month | 30 days | 1 user, 10 GB storage |
| CORPORATE | $49.99/month | 30 days | 10 users, 100 GB storage |

**Response Schema**:
```json
[
  {
    "id": 1,
    "name": "PRO",
    "price": 9.99,
    "currency": "USD",
    "stripe_product_id": "prod_xxx",
    "stripe_price_id": "price_xxx",
    "created": true
  },
  {
    "id": 2,
    "name": "CORPORATE",
    "price": 49.99,
    "currency": "USD",
    "stripe_product_id": "prod_yyy",
    "stripe_price_id": "price_yyy",
    "created": false
  }
]
```

**Notes**:
- If subscription already exists, returns existing record with `"created": false`
- Stripe products/prices are only created if `STRIPE_API_KEY` is configured
- Idempotent operation - safe to call multiple times

**Source File**: `src/app/infrastructure/subscription/handlers/init_subscriptions.py`

---

### POST /subscription/{subscription_id}/subscribe

Create a subscription for the current user.

**Authentication**: Required (Bearer Token)

**Path Parameters**:
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `subscription_id` | int | Yes | Subscription plan ID |

**Query Parameters**:
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `request_host` | string | No | Callback base URL for Stripe redirect |

**Response Schema**:
```json
{
  "status": "success",
  "subscription_user_id": 123,
  "payment_id": 456,
  "checkout_session_id": "cs_test_xxx"
}
```

**Flow**:
1. Creates `subscription_users` record with status `pending`
2. Creates `payments` record with status `pending`
3. Creates Stripe Checkout Session (if configured)
4. Returns checkout session ID for frontend redirect

**Error Responses**:
| Status | Code | Description |
|--------|------|-------------|
| 400 | Bad Request | Invalid request or Stripe error |
| 401 | Unauthorized | Invalid or missing token |
| 404 | Not Found | Subscription plan not found |
| 503 | Service Unavailable | Database connection error |

**Source File**: `src/app/infrastructure/subscription/handlers/customer_subscription.py`

---

### POST /subscription/{subscription_id}/cancel

Cancel an active subscription.

**Authentication**: Required (Bearer Token)

**Path Parameters**:
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `subscription_id` | int | Yes | Subscription plan ID |

**Response Schema**:
```json
{
  "status": "success",
  "message": "Subscription and all associated payments cancelled",
  "subscription_id": 123,
  "cancelled_payments": 2
}
```

**Flow**:
1. Finds active subscription for user
2. Cancels subscription in Stripe (if configured)
3. Updates `subscription_users.status` to `cancelled`
4. Updates all related `payments.status` to `cancelled`

**Error Responses**:
| Status | Code | Description |
|--------|------|-------------|
| 401 | Unauthorized | Invalid or missing token |
| 404 | Not Found | Active subscription not found |
| 503 | Service Unavailable | Database connection error |

**Source File**: `src/app/infrastructure/subscription/handlers/cancel_subscription.py`

---

### GET /subscription/success

Handle successful subscription payment callback from Stripe.

**Authentication**: None (Stripe callback)

**Query Parameters**:
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `session_id` | string | Yes | Stripe Checkout Session ID |

**Response Schema**:
```json
{
  "status": "success",
  "message": "Subscription activated successfully",
  "subscription_id": 123
}
```

**Flow**:
1. Retrieves Checkout Session from Stripe
2. Finds subscription_user by checkout_session_id
3. Updates subscription_user status to `active`
4. Stores Stripe subscription ID
5. Updates payment status to `completed`

**Error Responses**:
| Status | Code | Description |
|--------|------|-------------|
| 400 | Bad Request | Invalid request |
| 404 | Not Found | Subscription not found |
| 503 | Service Unavailable | Stripe not configured |

**Source File**: `src/app/infrastructure/subscription/handlers/success_subscription.py`

---

### GET /subscription/cancel

Handle cancelled subscription payment callback from Stripe.

**Authentication**: None (Stripe callback)

**Query Parameters**:
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `session_id` | string | Yes | Stripe Checkout Session ID |

**Response Schema**:
```json
{
  "status": "success",
  "message": "Subscription and all associated payments cancelled",
  "subscription_id": 123,
  "cancelled_payments": 1
}
```

**Source File**: `src/app/presentation/http/controllers/subscription/router.py`

---

## 2. Payment Endpoints

**Base Path**: `/api/v1/payments`  
**Tag**: `payments`

### GET /payments/user

Get paginated list of user's payment history.

**Authentication**: Required (Bearer Token)

**Query Parameters**:
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `page` | int | No | 1 | Page number (≥1) |
| `per_page` | int | No | 10 | Items per page (1-100) |

**Response Schema**:
```json
{
  "items": [
    {
      "id": 1,
      "user_id": 123,
      "subscription_id": 1,
      "subscription_user_id": 456,
      "amount": 9.99,
      "currency": "USD",
      "status": "completed",
      "stripe_payment_intent_id": "pi_xxx",
      "created_at": "2026-01-25T10:00:00Z",
      "data_json": {...}
    }
  ],
  "page": 1,
  "per_page": 10
}
```

**Payment Statuses**:
- `pending` - Awaiting payment
- `completed` - Payment successful
- `cancelled` - Payment cancelled
- `failed` - Payment failed

**Source File**: `src/app/presentation/http/controllers/payment/router.py`

---

### POST /payments/transaction

Create a new payment transaction.

**Authentication**: Required (Bearer Token)

**Request Body**:
```json
{
  "amount": 100.00,
  "currency": "USD",
  "description": "One-time purchase"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `amount` | float | Yes | Payment amount |
| `currency` | string | Yes | Currency code (e.g., USD) |
| `description` | string | Yes | Payment description |

**Response Schema**:
```json
{
  "status": "success",
  "payment": {
    "id": 789,
    "user_id": 123,
    "amount": 100.00,
    "currency": "USD",
    "status": "pending",
    "data_json": {"description": "One-time purchase"},
    "created_at": "2026-01-25T10:00:00Z"
  }
}
```

**Source File**: `src/app/presentation/http/controllers/payment/router.py`

---

## 3. Stripe Webhook Endpoints

> **Note**: Stripe webhooks are typically configured at a separate endpoint (e.g., `/webhooks/stripe`) and handle events like:
> - `checkout.session.completed`
> - `invoice.paid`
> - `invoice.payment_failed`
> - `customer.subscription.deleted`

Currently, webhook handling is done through the success/cancel callback endpoints.

---

## 4. Error Handling

### Standard Error Response

```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Human readable message",
    "details": {...}
  }
}
```

### Subscription Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `SUB_001` | 404 | Subscription not found |
| `SUB_002` | 402 | Payment processing failed |
| `SUB_003` | 400 | Invalid subscription plan |
| `SUB_004` | 400 | Subscription already cancelled |

---

## 5. Configuration

### Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `STRIPE_API_KEY` | No | Stripe secret key for API calls |
| `STRIPE_WEBHOOK_SECRET` | No | Stripe webhook signing secret |

**Configuration Location**: `config/{env}/.secrets.toml`

```toml
[stripe]
STRIPE_API_KEY = "sk_test_xxx"
STRIPE_WEBHOOK_SECRET = "whsec_xxx"
```

---

## 6. API Client Examples

### List Plans
```bash
curl -X GET "http://localhost:8000/api/v1/subscription" \
  -H "Authorization: Bearer $TOKEN"
```

### Create Subscription
```bash
curl -X POST "http://localhost:8000/api/v1/subscription/1/subscribe" \
  -H "Authorization: Bearer $TOKEN"
```

### Cancel Subscription
```bash
curl -X POST "http://localhost:8000/api/v1/subscription/1/cancel" \
  -H "Authorization: Bearer $TOKEN"
```

### Get Payment History
```bash
curl -X GET "http://localhost:8000/api/v1/payments/user?page=1&per_page=10" \
  -H "Authorization: Bearer $TOKEN"
```

---

## References

- **Subscription Router**: `src/app/presentation/http/controllers/subscription/router.py`
- **Payment Router**: `src/app/presentation/http/controllers/payment/router.py`
- **Subscription Handlers**: `src/app/infrastructure/subscription/handlers/`
- **Stripe Config**: `src/app/setup/config/stripe.py`
