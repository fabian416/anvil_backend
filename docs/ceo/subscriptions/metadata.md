# Subscriptions & Payments Metadata & Architecture

> **Last Updated**: 2026-01-25  
> **Status**: Production (Basic)  
> **Maintainers**: @backend-engineer @error-detective @code-reviewer

---

## Executive Summary

The Anvil Subscriptions & Payments system provides Stripe-integrated subscription management for user premium features. It supports multiple subscription tiers, payment processing, and subscription lifecycle management.

---

## 1. Module Status

| Component | Status | Health | Notes |
|-----------|--------|--------|-------|
| Subscription Plans | ✅ Production | Healthy | PRO and CORPORATE tiers |
| Stripe Checkout | ✅ Production | Healthy | Session-based checkout |
| Subscription Cancel | ✅ Production | Healthy | Full cancellation flow |
| Payment History | ✅ Production | Healthy | Paginated retrieval |
| Webhooks | ⚠️ Partial | Limited | Callback-based only |
| Celery Tasks | ❌ Not Implemented | N/A | Recommended for production |
| Analytics | ❌ Not Implemented | N/A | No MRR/churn tracking |

---

## 2. File Reference Index

### 2.1 Presentation Layer

```
src/app/presentation/http/controllers/
├── subscription/
│   ├── router.py                    # Subscription endpoints
│   └── init.py
└── payment/
    └── router.py                    # Payment endpoints
```

### 2.2 Infrastructure Layer (Handlers)

```
src/app/infrastructure/subscription/handlers/
├── get_subscriptions.py             # List plans handler
├── init_subscriptions.py            # Initialize plans handler
├── customer_subscription.py         # Create subscription handler
├── cancel_subscription.py           # Cancel subscription handler
└── success_subscription.py          # Success callback handler
```

### 2.3 Application Layer (Ports)

```
src/app/application/subscription/
└── ports.py                         # Repository protocols
    ├── SubscriptionRepository       # Plan data access
    ├── SubscriptionUserRepository   # User subscription data access
    └── PaymentRepository            # Payment data access
```

### 2.4 Infrastructure Layer (Repositories)

```
src/app/infrastructure/adapters/
├── subscription_repository_sqla.py      # Plan repository
├── subscription_user_repository_sqla.py # User subscription repository
└── payment_repository_sqla.py           # Payment repository
```

### 2.5 Persistence Layer (Mappings)

```
src/app/infrastructure/persistence_sqla/mappings/
├── subscription.py                  # subscriptions table
├── subscription_user.py             # subscription_users table
└── payment.py                       # payments table
```

### 2.6 Test Files

```
tests/
├── unit/
│   └── presentation/subscription/
│       └── test_subscription_controllers.py
├── integration/
│   ├── subscription/
│   │   └── test_subscription_lifecycle.py
│   └── flows/
│       └── test_subscription_payment_flow.py
├── e2e/
│   └── subscription/
│       └── test_subscription_workflow.py
└── builders/
    └── subscription_builder.py
```

---

## 3. Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              CLIENT LAYER                                    │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                         │
│  │   Web App   │  │ Mobile App  │  │Stripe Hosted│                         │
│  │             │  │             │  │  Checkout   │                         │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘                         │
└─────────┼────────────────┼────────────────┼─────────────────────────────────┘
          │                │                │
          ▼                ▼                ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           PRESENTATION LAYER                                 │
│                                                                              │
│  ┌────────────────────────────┐  ┌────────────────────────────┐            │
│  │    Subscription Router     │  │      Payment Router        │            │
│  │   /api/v1/subscription     │  │    /api/v1/payments        │            │
│  │                            │  │                            │            │
│  │  GET  /                    │  │  GET  /user                │            │
│  │  POST /init                │  │  POST /transaction         │            │
│  │  POST /{id}/subscribe      │  │                            │            │
│  │  POST /{id}/cancel         │  │                            │            │
│  │  GET  /success             │  │                            │            │
│  │  GET  /cancel              │  │                            │            │
│  └────────────────────────────┘  └────────────────────────────┘            │
└─────────────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           HANDLER LAYER                                      │
│                                                                              │
│  ┌───────────────────┐  ┌───────────────────┐  ┌───────────────────┐       │
│  │GetSubscriptionsHdlr│  │InitSubscriptionsHdlr│  │CreateSubscriptionHdlr│  │
│  └───────────────────┘  └───────────────────┘  └───────────────────┘       │
│                                                                              │
│  ┌───────────────────┐  ┌───────────────────┐                              │
│  │CancelSubscriptionHdlr│  │SuccessSubscriptionHdlr│                        │
│  └───────────────────┘  └───────────────────┘                              │
└─────────────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           REPOSITORY LAYER                                   │
│                                                                              │
│  ┌───────────────────┐  ┌───────────────────┐  ┌───────────────────┐       │
│  │SubscriptionRepo   │  │SubscriptionUserRepo│  │   PaymentRepo     │       │
│  │   (SQLAlchemy)    │  │    (SQLAlchemy)    │  │   (SQLAlchemy)    │       │
│  └───────────────────┘  └───────────────────┘  └───────────────────┘       │
└─────────────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                          DATA LAYER (PostgreSQL)                             │
│                                                                              │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │                         subscriptions                                 │  │
│  │  id │ name │ price │ currency │ duration │ features │ stripe_ids    │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                              │                                              │
│                              ▼                                              │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │                       subscription_users                              │  │
│  │  id │ user_id │ subscription_id │ status │ stripe_subscription_id   │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                              │                                              │
│                              ▼                                              │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │                          payments                                     │  │
│  │  id │ user_id │ subscription_user_id │ amount │ status │ stripe_id  │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                        EXTERNAL SERVICES                                     │
│                                                                              │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │                         Stripe API                                    │  │
│  │                                                                        │  │
│  │  ┌────────────┐  ┌────────────┐  ┌────────────┐  ┌────────────┐      │  │
│  │  │  Products  │  │   Prices   │  │  Checkout  │  │Subscriptions│     │  │
│  │  └────────────┘  └────────────┘  └────────────┘  └────────────┘      │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 4. Database Schema

### 4.1 Subscriptions Table

```sql
CREATE TABLE subscriptions (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    price FLOAT NOT NULL,
    subscription_type VARCHAR(100) NOT NULL DEFAULT 'month',
    currency VARCHAR(3) DEFAULT 'USD',
    duration INTEGER NOT NULL,  -- Duration in days
    features JSON,
    is_active BOOLEAN DEFAULT TRUE,
    stripe_price_id VARCHAR(255),
    stripe_product_id VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 4.2 Subscription Users Table

```sql
CREATE TABLE subscription_users (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    subscription_id INTEGER NOT NULL REFERENCES subscriptions(id),
    status VARCHAR(50) NOT NULL DEFAULT 'pending',  -- pending, active, cancelled
    start_date TIMESTAMPTZ,
    end_date TIMESTAMPTZ,
    stripe_subscription_id VARCHAR(255),
    stripe_customer_id VARCHAR(255),
    client_secret VARCHAR(255),
    subscription_data JSON,
    data_json JSON DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ
);
```

### 4.3 Payments Table

```sql
CREATE TABLE payments (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    subscription_id INTEGER REFERENCES subscriptions(id) ON DELETE SET NULL,
    subscription_user_id INTEGER REFERENCES subscription_users(id) ON DELETE SET NULL,
    amount FLOAT,
    currency VARCHAR(3) DEFAULT 'USD',
    status VARCHAR(50) NOT NULL DEFAULT 'pending',  -- pending, completed, cancelled, failed
    stripe_payment_intent_id VARCHAR(255),
    stripe_customer_id VARCHAR(255),
    payment_data JSON,
    payment_method VARCHAR(50),
    payment_type VARCHAR(50),
    date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    data_json JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 4.4 Entity Relationship Diagram

```
┌─────────────────┐
│     users       │
│─────────────────│
│ id (PK)         │
│ email           │
│ ...             │
└────────┬────────┘
         │
         │ 1:N
         ▼
┌─────────────────┐          ┌─────────────────┐
│subscription_users│◄────────│  subscriptions  │
│─────────────────│    N:1   │─────────────────│
│ id (PK)         │          │ id (PK)         │
│ user_id (FK)    │          │ name            │
│ subscription_id │──────────│ price           │
│ status          │          │ features        │
│ stripe_sub_id   │          │ stripe_price_id │
└────────┬────────┘          └─────────────────┘
         │
         │ 1:N
         ▼
┌─────────────────┐
│    payments     │
│─────────────────│
│ id (PK)         │
│ user_id (FK)    │
│ sub_user_id (FK)│
│ amount          │
│ status          │
│ stripe_intent_id│
└─────────────────┘
```

---

## 5. Subscription Flow Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        SUBSCRIPTION CREATION FLOW                            │
└─────────────────────────────────────────────────────────────────────────────┘

User                    Backend                     Stripe
 │                         │                          │
 │ 1. POST /subscribe      │                          │
 │────────────────────────>│                          │
 │                         │ 2. Create subscription_user (pending)
 │                         │ 3. Create payment (pending)
 │                         │                          │
 │                         │ 4. Create Checkout Session│
 │                         │─────────────────────────>│
 │                         │                          │
 │                         │<─────────────────────────│
 │                         │ 5. Return session_id     │
 │                         │                          │
 │<────────────────────────│                          │
 │ 6. Redirect to Checkout │                          │
 │                         │                          │
 │────────────────────────────────────────────────────>│
 │ 7. User completes payment                          │
 │                         │                          │
 │                         │<─────────────────────────│
 │                         │ 8. Success callback      │
 │                         │    (GET /success)        │
 │                         │                          │
 │                         │ 9. Retrieve session      │
 │                         │─────────────────────────>│
 │                         │<─────────────────────────│
 │                         │                          │
 │                         │ 10. Update subscription_user (active)
 │                         │ 11. Update payment (completed)
 │                         │                          │
 │<────────────────────────│                          │
 │ 12. Subscription active │                          │
 │                         │                          │
```

---

## 6. Improvements Roadmap

### 6.1 High Priority

| Improvement | Description | Effort | Impact |
|-------------|-------------|--------|--------|
| **Webhook Handler** | Proper Stripe webhook integration | Medium | Critical for reliability |
| **Celery Tasks** | Background subscription processing | Medium | Performance |
| **Expiration Handling** | Auto-expire subscriptions | Low | Revenue protection |
| **Unit Tests** | Handler unit tests | Medium | Code quality |

### 6.2 Medium Priority

| Improvement | Description | Effort | Impact |
|-------------|-------------|--------|--------|
| **Plan Upgrades** | Upgrade/downgrade support | High | Feature completeness |
| **Proration** | Prorated billing for changes | Medium | User experience |
| **Trial Periods** | Free trial support | Medium | Acquisition |
| **Invoice History** | Detailed invoice records | Low | Compliance |

### 6.3 Low Priority

| Improvement | Description | Effort | Impact |
|-------------|-------------|--------|--------|
| **Analytics Dashboard** | MRR/churn visualization | High | Business insights |
| **Coupon Support** | Discount codes | Medium | Marketing |
| **Multi-currency** | Currency conversion | High | Global expansion |
| **Tax Calculation** | Automatic tax handling | High | Compliance |

---

## 7. Security Considerations

### 7.1 Implemented

- ✅ JWT authentication for all endpoints
- ✅ User-scoped data access
- ✅ Stripe API key in secrets config

### 7.2 Recommendations

- ⚠️ Implement webhook signature verification
- ⚠️ Add rate limiting for subscription endpoints
- ⚠️ Implement idempotency keys for payments
- ⚠️ Add audit logging for payment events
- ⚠️ PCI DSS compliance review

---

## 8. Configuration

### 8.1 Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `STRIPE_API_KEY` | Yes* | Stripe secret key |
| `STRIPE_WEBHOOK_SECRET` | No | Webhook signing secret |

*Required for Stripe integration; system works without but creates no Stripe resources.

### 8.2 Default Plans

| Plan | Price | Duration | Features |
|------|-------|----------|----------|
| PRO | $9.99/month | 30 days | 1 user, 10 GB storage |
| CORPORATE | $49.99/month | 30 days | 10 users, 100 GB storage |

---

## 9. Performance Metrics

### 9.1 Current Performance

| Metric | Value | Target |
|--------|-------|--------|
| Plan listing latency | ~100ms | <200ms |
| Subscription creation | ~2s | <3s (includes Stripe) |
| Payment history | ~150ms | <300ms |

### 9.2 Scaling Considerations

- **Database**: Read replicas for payment queries
- **Stripe**: API rate limits (100 req/s default)
- **Webhooks**: Queue-based processing for high volume

---

## References

- **Endpoints Spec**: `docs/ceo/subscriptions/endpoints.md`
- **Services Spec**: `docs/ceo/subscriptions/services.md`
- **Celery Spec**: `docs/ceo/subscriptions/celery.md`
- **Test Spec**: `docs/ceo/subscriptions/test.md`
- **Stripe Docs**: https://stripe.com/docs/billing/subscriptions
