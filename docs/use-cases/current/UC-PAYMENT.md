# UC-PAYMENT: Subscription & Payment

**Version:** 1.0.0  
**Status:** ✅ LIVE (Production)  
**Category:** Core Platform  
**Total Use Cases:** 6

---

## 📊 **OVERVIEW**

Complete Stripe-based subscription and payment system enabling multiple subscription tiers, payment processing, and subscription management.

### **Business Value**
- Monetization infrastructure
- Multiple subscription tiers
- Secure payment processing
- Subscription lifecycle management
- Webhook handling

### **Technical Stack**
- **Payment Provider:** Stripe
- **Integration:** Stripe Python SDK
- **Webhooks:** Signature verification
- **Database:** Subscription and payment tables
- **Security:** HTTPS, webhook signatures

---

## 🎯 **USE CASES**

### **UC-PAY-1: Subscription Plans**

**Overview:**
- **Status:** ✅ LIVE
- **Tier:** Free (view plans)
- **Priority:** HIGH
- **API Endpoint:** `GET /api/v1/subscription`

**Business Value:**
```
User Story: As a user, I want to view available subscription plans 
           so that I can choose the right tier for my needs.

Value Proposition: Transparent pricing and feature comparison

Success Metrics:
  • Plan view rate > 80% of users
  • Time to decision < 5 minutes
  • Plan comparison rate > 60%
```

**Technical Specification:**
```python
# Application Layer
- Handler: GetSubscriptionsHandler

# Infrastructure Layer
- Repository: SubscriptionRepository
- Adapter: SubscriptionRepositorySqla

# Database Schema:
{
    "id": UUID,
    "name": str,  # "Free", "Premium", "Ultra Premium"
    "price_monthly": Decimal,
    "price_yearly": Decimal,
    "stripe_price_id": str,
    "features": JSONB,
    "max_api_calls": int,
    "is_active": bool
}
```

**Subscription Tiers:**
```json
{
  "free": {
    "price": 0,
    "features": [
      "Basic agent interactions",
      "MCP data access",
      "Basic dashboard",
      "Community support"
    ],
    "limits": {
      "api_calls_per_day": 100,
      "agents": ["research", "basic_trading"]
    }
  },
  "premium": {
    "price": 49,
    "features": [
      "All Free features",
      "Advanced AI agents",
      "Real-time alerts",
      "Priority support",
      "Historical data"
    ],
    "limits": {
      "api_calls_per_day": 1000,
      "agents": ["all_except_arbitrage"]
    }
  },
  "ultra_premium": {
    "price": 199,
    "features": [
      "All Premium features",
      "Arbitrage bot",
      "Flash loan execution",
      "MEV protection",
      "Dedicated support",
      "Custom integrations"
    ],
    "limits": {
      "api_calls_per_day": "unlimited",
      "agents": ["all"]
    }
  }
}
```

**Configuration:**
```toml
[subscription]
enable_free_tier = true
enable_premium_tier = true
enable_ultra_premium_tier = false  # Coming soon
trial_period_days = 14
```

---

### **UC-PAY-2: Create Subscription**

**Overview:**
- **Status:** ✅ LIVE
- **Tier:** Premium/Ultra Premium
- **Priority:** HIGH
- **API Endpoint:** `POST /api/v1/subscription`

**Business Value:**
```
User Story: As a user, I want to subscribe to a paid plan 
           so that I can access premium features.

Value Proposition: Revenue generation, premium access

Success Metrics:
  • Subscription success rate > 95%
  • Average checkout time < 3 minutes
  • Payment failure rate < 2%
```

**Technical Specification:**
```python
# Application Layer
- Handler: CreateSubscriptionHandler
- Port: SubscriptionCommandGateway

# Infrastructure Layer
- Stripe Integration: stripe.Subscription.create()
- Payment Method: stripe.PaymentMethod.attach()

# Presentation Layer
- Controller: POST /api/v1/subscription
- Request: CreateSubscriptionRequest
  {
    "price_id": str,  # Stripe price ID
    "payment_method_id": str,  # From Stripe.js
    "billing_cycle": "monthly" | "yearly"
  }
- Response: CreateSubscriptionResponse
  {
    "subscription_id": str,
    "status": str,
    "current_period_end": datetime,
    "client_secret": str  # For 3D Secure
  }
```

**Stripe Integration Flow:**
```
1. Frontend: Collect payment method via Stripe.js
2. Backend: Create Stripe Customer
3. Backend: Attach payment method to customer
4. Backend: Create subscription with payment method
5. Backend: Handle 3D Secure if required
6. Backend: Store subscription in database
7. Backend: Activate premium features
8. Frontend: Redirect to success page
```

**Configuration:**
```toml
[stripe]
secret_key = "${STRIPE_SECRET_KEY}"
public_key = "${STRIPE_PUBLIC_KEY}"
webhook_secret = "${STRIPE_WEBHOOK_SECRET}"

[stripe.subscription]
trial_period_days = 14
proration_behavior = "create_prorations"
collection_method = "charge_automatically"
```

**Security:**
- ✅ Stripe.js for PCI compliance
- ✅ HTTPS required
- ✅ Payment method validation
- ✅ 3D Secure support
- ✅ Webhook signature verification

---

### **UC-PAY-3: Cancel Subscription**

**Overview:**
- **Status:** ✅ LIVE
- **Tier:** Premium/Ultra Premium
- **Priority:** MEDIUM
- **API Endpoint:** `POST /api/v1/subscription/cancel`

**Business Value:**
```
User Story: As a subscriber, I want to cancel my subscription 
           so that I can stop recurring payments.

Value Proposition: User control, reduce churn disputes

Success Metrics:
  • Cancellation success rate > 99%
  • Average cancellation time < 1 minute
  • Immediate access until period end
```

**Technical Specification:**
```python
# Application Layer
- Handler: CancelSubscriptionHandler

# Infrastructure Layer
- Stripe Integration: stripe.Subscription.modify(cancel_at_period_end=True)

# Presentation Layer
- Controller: POST /api/v1/subscription/cancel
- Request: CancelSubscriptionRequest
  {
    "reason": str,  # Optional feedback
    "immediate": bool  # Cancel now or at period end
  }
- Response: CancelSubscriptionResponse
  {
    "canceled_at": datetime,
    "access_until": datetime,
    "refund_amount": Decimal | null
  }
```

**Cancellation Policy:**
```
• Default: Cancel at period end (no refund)
• Immediate: Cancel now (prorated refund)
• Trial cancellation: No charge
• Access retained until period end
```

**Configuration:**
```toml
[stripe.cancellation]
allow_immediate_cancellation = true
prorate_refunds = true
retain_access_until_period_end = true
collect_feedback = true
```

---

### **UC-PAY-4: Payment Processing**

**Overview:**
- **Status:** ✅ LIVE
- **Tier:** Premium/Ultra Premium
- **Priority:** HIGH
- **API Endpoint:** `POST /api/v1/payment`

**Business Value:**
```
User Story: As a user, I want to make secure payments 
           so that I can access premium features.

Value Proposition: Secure revenue collection

Success Metrics:
  • Payment success rate > 98%
  • Average processing time < 5 seconds
  • Failed payment rate < 2%
```

**Technical Specification:**
```python
# Application Layer
- Handler: ProcessPaymentHandler

# Infrastructure Layer
- Stripe Integration: stripe.PaymentIntent.create()
- Payment Methods: Card, ACH, Apple Pay, Google Pay

# Presentation Layer
- Controller: POST /api/v1/payment
- Request: ProcessPaymentRequest
  {
    "amount": Decimal,
    "currency": str,
    "payment_method_id": str,
    "description": str
  }
- Response: ProcessPaymentResponse
  {
    "payment_id": str,
    "status": str,
    "amount": Decimal,
    "receipt_url": str
  }
```

**Payment Flow:**
```
1. Create PaymentIntent on backend
2. Return client_secret to frontend
3. Frontend confirms payment with Stripe.js
4. Stripe processes payment
5. Webhook confirms payment success
6. Backend activates features
7. Send receipt email
```

**Supported Payment Methods:**
- ✅ Credit/Debit Cards (Visa, Mastercard, Amex)
- ✅ ACH Direct Debit
- ✅ Apple Pay
- ✅ Google Pay
- ✅ SEPA Direct Debit (Europe)

**Configuration:**
```toml
[stripe.payment]
supported_currencies = ["usd", "eur", "gbp"]
capture_method = "automatic"
confirm = false
setup_future_usage = "off_session"
```

---

### **UC-PAY-5: Subscription Success Handling**

**Overview:**
- **Status:** ✅ LIVE
- **Tier:** Premium/Ultra Premium
- **Priority:** HIGH
- **API Endpoint:** `POST /api/v1/subscription/success`

**Business Value:**
```
User Story: As a system, I want to handle successful subscriptions 
           so that users get immediate access.

Value Proposition: Instant feature activation

Success Metrics:
  • Activation time < 10 seconds
  • Activation success rate > 99.9%
  • Email delivery rate > 99%
```

**Technical Specification:**
```python
# Application Layer
- Handler: SubscriptionSuccessHandler

# Infrastructure Layer
- Database: Update user subscription status
- Cache: Invalidate user permissions cache
- Email: Send welcome email

# Webhook Events:
- customer.subscription.created
- customer.subscription.updated
- invoice.paid
- payment_intent.succeeded
```

**Success Flow:**
```
1. Receive Stripe webhook
2. Verify webhook signature
3. Parse event data
4. Update user subscription
5. Activate premium features
6. Invalidate permission cache
7. Send confirmation email
8. Log event for analytics
```

**Configuration:**
```toml
[stripe.webhooks]
verify_signatures = true
retry_failed_webhooks = true
max_retries = 3
email_on_success = true
```

---

### **UC-PAY-6: Initialize Subscriptions**

**Overview:**
- **Status:** ✅ LIVE
- **Tier:** Admin
- **Priority:** LOW
- **API Endpoint:** `POST /api/v1/subscription/init`

**Business Value:**
```
User Story: As an admin, I want to initialize subscription plans 
           so that they're available for users.

Value Proposition: Subscription setup automation

Success Metrics:
  • Initialization success rate > 99%
  • Plan sync time < 30 seconds
```

**Technical Specification:**
```python
# Application Layer
- Handler: InitSubscriptionsHandler

# Infrastructure Layer
- Stripe Sync: Fetch products and prices from Stripe
- Database: Insert/update subscription plans

# Presentation Layer
- Controller: POST /api/v1/subscription/init
- Request: InitSubscriptionsRequest (empty)
- Response: InitSubscriptionsResponse
  {
    "plans_created": int,
    "plans_updated": int,
    "stripe_products": list[str]
  }
```

**Initialization Steps:**
```
1. Fetch Stripe products
2. Fetch Stripe prices
3. Create subscription plans in database
4. Map features from product metadata
5. Set API limits
6. Activate plans
7. Return summary
```

---

## 🏗️ **ARCHITECTURE**

### **Hexagonal Architecture Placement**

```
Domain Layer:
  └─ (No domain logic - infrastructure concern)

Application Layer:
  └─ (Minimal - delegates to infrastructure)

Infrastructure Layer (src/app/infrastructure/subscription/):
  ├─ handlers/
  │  ├─ get_subscriptions.py
  │  ├─ create_subscription.py
  │  ├─ cancel_subscription.py
  │  └─ subscription_success.py
  ├─ stripe_client.py
  └─ webhooks.py

Presentation Layer (src/app/presentation/http/controllers/):
  ├─ subscription/router.py
  └─ payment/router.py
```

---

## 🔒 **SECURITY CONSIDERATIONS**

### **PCI Compliance**
- ✅ Stripe.js for card data (no backend handling)
- ✅ HTTPS required for all endpoints
- ✅ No card data storage
- ✅ Tokenized payment methods

### **Webhook Security**
- ✅ Signature verification (Stripe-Signature header)
- ✅ Replay attack prevention
- ✅ HTTPS only
- ✅ Idempotency keys

### **Authorization**
- ✅ User can only manage own subscriptions
- ✅ Admin access for initialization
- ✅ Bearer token authentication

---

## 📊 **SUCCESS METRICS**

### **Performance**
- Subscription creation: < 3s
- Payment processing: < 5s
- Cancellation: < 1s
- Webhook processing: < 2s

### **Reliability**
- Subscription success rate: > 95%
- Payment success rate: > 98%
- Webhook delivery rate: > 99%
- Email delivery rate: > 99%

### **Revenue**
- Current MRR: $0 (no subscribers yet)
- Target MRR: $18,000 (300 subscribers)
- Churn rate target: < 5%

---

## 📚 **RELATED DOCUMENTATION**

- [Subscription Router](../../../src/app/presentation/http/controllers/subscription/router.py)
- [Payment Router](../../../src/app/presentation/http/controllers/payment/router.py)
- [Stripe Config](../../../src/app/setup/config/stripe.py)
- [Subscription Rules](../../../.cursor/rules/project-rules/subscription.mdc)

---

**Status:** ✅ 100% Complete (6/6 use cases live)  
**Last Updated:** December 2, 2025  
**Next Review:** Ongoing maintenance
