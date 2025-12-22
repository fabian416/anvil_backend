# FRONTEND_USER_SETTINGS_SUBSCRIPTION

> **Enterprise Grade Specification**
> Version: 2.0.0
> Status: **Live**
> Source Validation: `src/app/presentation/http/controllers/subscription/router.py`

## 1. Module Overview
The **Subscription** module manages user access tiers (Free vs Pro). It integrates with Stripe for payment processing.

**Base URL**: `/api/v1/subscription`

---

## 2. Endpoints

### 2.1 List Available Plans
**GET** `/api/v1/subscription/`

Lists active subscription tiers and their features.

**Response (200 OK):**
```json
[
  {
    "id": 1,
    "name": "Pro Plan",
    "price_usd": 29.99,
    "features": ["Unlimited Chat", "Advanced Risk Analysis"]
  }
]
```

### 2.2 Initialize Checkout
**POST** `/api/v1/subscription/{subscription_id}/subscribe`

Create a checkout session (e.g., Stripe) for a new subscription.

**Response (200 OK):**
```json
{
  "checkout_url": "https://checkout.stripe.com/...",
  "session_id": "cs_test_..."
}
```

### 2.3 Cancel Subscription
**POST** `/api/v1/subscription/{subscription_id}/cancel`

Cancels auto-renewal at end of period.

**Response (200 OK):**
```json
{
  "status": "cancelled",
  "expires_at": "2024-02-01T00:00:00Z"
}
```

---

## 3. Webhooks
*   **Success**: `GET /api/v1/subscription/success` (Stripe redirect target).
*   **Cancel**: `GET /api/v1/subscription/cancel`.
