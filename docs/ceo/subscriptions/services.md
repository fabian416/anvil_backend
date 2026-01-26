# Subscriptions & Payments Services Specification

> **Last Updated**: 2026-01-25  
> **Status**: Production  
> **Maintainers**: @backend-engineer @error-detective @code-reviewer

---

## Executive Summary

The Subscriptions & Payments system follows a handler-based architecture pattern with:
- **Handlers**: Business logic for subscription operations
- **Repositories**: Data access layer for persistence
- **Ports**: Protocol interfaces for dependency injection

**Total Service Components**: 10+ Python modules

---

## 1. Handler Services

### 1.1 GetSubscriptionsHandler
**Path**: `src/app/infrastructure/subscription/handlers/get_subscriptions.py`

Retrieves all available subscription plans.

**Dependencies**:
- `SubscriptionRepository`

**Implementation**:
```python
class GetSubscriptionsHandler:
    def __init__(self, subscription_repo: SubscriptionRepository) -> None:
        self._repo = subscription_repo

    async def execute(self) -> list[SubscriptionItem]:
        rows = await self._repo.read_all()
        return [SubscriptionItem(...) for r in rows]
```

**Output Model**:
```python
@dataclass(frozen=True, slots=True)
class SubscriptionItem:
    id: int
    name: str
    price: float
    currency: str
    duration: int
    features: dict | None
    is_active: bool
    stripe_product_id: str | None
    stripe_price_id: str | None
```

---

### 1.2 InitSubscriptionsHandler
**Path**: `src/app/infrastructure/subscription/handlers/init_subscriptions.py`

Initializes default subscription plans (PRO and CORPORATE).

**Dependencies**:
- `SubscriptionRepository`
- `TransactionManager`

**Default Plans**:
```python
definitions = [
    {
        "name": "PRO",
        "price": 9.99,
        "subscription_type": "month",
        "currency": "USD",
        "duration": 30,
        "features": {"users": 1, "storage_gb": 10},
        "is_active": True,
    },
    {
        "name": "CORPORATE",
        "price": 49.99,
        "subscription_type": "month",
        "currency": "USD",
        "duration": 30,
        "features": {"users": 10, "storage_gb": 100},
        "is_active": True,
    },
]
```

**Stripe Integration**:
- Creates Stripe Products via `stripe.Product.create()`
- Creates Stripe Prices via `stripe.Price.create()`
- Updates database with `stripe_product_id` and `stripe_price_id`

---

### 1.3 CreateSubscriptionHandler
**Path**: `src/app/infrastructure/subscription/handlers/customer_subscription.py`

Creates a new subscription for a user with Stripe Checkout integration.

**Dependencies**:
- `CurrentUserService`
- `SubscriptionRepository`
- `SubscriptionUserRepository`
- `PaymentRepository`
- `NotificationRepository`
- `TransactionManager`

**Request Model**:
```python
@dataclass(frozen=True, slots=True)
class CreateSubscriptionRequest:
    subscription_id: int
    callback_base_url: str | None = None
```

**Flow**:
1. Get current authenticated user
2. Validate subscription plan exists
3. Create `subscription_users` record (status: pending)
4. Create `payments` record (status: pending)
5. Create Stripe Checkout Session (if configured)
6. Update records with `checkout_session_id`
7. Commit transaction
8. Return checkout session ID

**Stripe Checkout**:
```python
session = stripe.checkout.Session.create(
    mode="subscription",
    line_items=[{"price": plan["stripe_price_id"], "quantity": 1}],
    success_url=f"{base}/api/v1/subscription/success?session_id={{CHECKOUT_SESSION_ID}}",
    cancel_url=f"{base}/api/v1/subscription/cancel?session_id={{CHECKOUT_SESSION_ID}}",
)
```

---

### 1.4 CancelSubscriptionHandler
**Path**: `src/app/infrastructure/subscription/handlers/cancel_subscription.py`

Cancels an active subscription for the current user.

**Dependencies**:
- `CurrentUserService`
- `SubscriptionUserRepository`
- `PaymentRepository`
- `TransactionManager`

**Request Model**:
```python
@dataclass(frozen=True, slots=True)
class CancelSubscriptionRequest:
    subscription_id: int
```

**Flow**:
1. Get current authenticated user
2. Find active subscription for user
3. Cancel in Stripe (if `stripe_subscription_id` exists)
4. Update subscription_user status to `cancelled`
5. Update all related payments status to `cancelled`
6. Commit transaction

---

### 1.5 SubscriptionSuccessHandler
**Path**: `src/app/infrastructure/subscription/handlers/success_subscription.py`

Handles successful payment callback from Stripe.

**Dependencies**:
- `SubscriptionUserRepository`
- `PaymentRepository`
- `TransactionManager`

**Request Model**:
```python
@dataclass(frozen=True, slots=True)
class SubscriptionSuccessRequest:
    session_id: str
```

**Flow**:
1. Retrieve Checkout Session from Stripe
2. Find subscription_user by `checkout_session_id`
3. Update status to `active`
4. Store `stripe_subscription_id`
5. Update pending payment to `completed`
6. Store payment details in `data_json`
7. Commit transaction

---

## 2. Repository Ports (Interfaces)

**Path**: `src/app/application/subscription/ports.py`

### 2.1 SubscriptionRepository Protocol

```python
class SubscriptionRepository(Protocol):
    async def read_by_name(self, name: str) -> dict | None
    async def read_all(self) -> list[dict]
    async def read_by_id(self, id_: int) -> dict | None
    async def add(
        self,
        *,
        name: str,
        price: float,
        subscription_type: str,
        currency: str,
        duration: int,
        features: dict | None,
        is_active: bool,
        stripe_price_id: str | None,
        stripe_product_id: str | None,
        created_at: datetime,
        updated_at: datetime,
    ) -> int
    async def update_stripe_ids(
        self, *, id_: int, stripe_price_id: str, stripe_product_id: str
    ) -> None
```

---

### 2.2 SubscriptionUserRepository Protocol

```python
class SubscriptionUserRepository(Protocol):
    async def add(
        self,
        *,
        user_id: int,
        subscription_id: int,
        status: str,
        data_json: dict | None,
    ) -> int
    async def read_for_user_by_id(self, *, id_: int, user_id: int) -> dict | None
    async def update_status(self, *, id_: int, status: str) -> None
    async def update_stripe_subscription_id(
        self, *, id_: int, stripe_subscription_id: str
    ) -> None
    async def read_by_checkout_session_id(self, *, session_id: str) -> dict | None
    async def update_data_json(self, *, id_: int, data_json: dict) -> None
    async def read_active_for_user_and_subscription(
        self, *, user_id: int, subscription_id: int
    ) -> dict | None
```

---

### 2.3 PaymentRepository Protocol

```python
class PaymentRepository(Protocol):
    async def add(
        self,
        *,
        user_id: int,
        subscription_id: int | None,
        subscription_user_id: int | None,
        amount: float | None,
        currency: str,
        status: str,
        stripe_payment_intent_id: str | None,
        data_json: dict | None,
    ) -> int
    async def find_pending_for_subscription_user(
        self, *, subscription_user_id: int
    ) -> dict | None
    async def update_status(self, *, id_: int, status: str) -> None
    async def list_by_subscription_user(
        self, *, subscription_user_id: int
    ) -> list[dict]
    async def update_data_json(self, *, id_: int, data_json: dict) -> None
    async def read_by_user_paginated(
        self, *, user_id: int, offset: int, limit: int
    ) -> list[dict]
    async def find_or_create_transaction(
        self,
        *,
        user_id: int,
        amount: float,
        currency: str,
        description: str,
    ) -> dict
```

---

## 3. Repository Implementations

### 3.1 SqlaSubscriptionRepository
**Path**: `src/app/infrastructure/adapters/subscription_repository_sqla.py`

SQLAlchemy implementation of `SubscriptionRepository`.

**Table**: `subscriptions`

---

### 3.2 SqlaSubscriptionUserRepository
**Path**: `src/app/infrastructure/adapters/subscription_user_repository_sqla.py`

SQLAlchemy implementation of `SubscriptionUserRepository`.

**Table**: `subscription_users`

---

### 3.3 SqlaPaymentRepository
**Path**: `src/app/infrastructure/adapters/payment_repository_sqla.py`

SQLAlchemy implementation of `PaymentRepository`.

**Table**: `payments`

**Key Methods**:
```python
async def add(...) -> int:
    # Insert payment record
    
async def find_pending_for_subscription_user(...) -> dict | None:
    # Find pending payment by subscription_user_id
    
async def update_status(...) -> None:
    # Update payment status
    
async def read_by_user_paginated(...) -> list[dict]:
    # Paginated payment history for user
    
async def find_or_create_transaction(...) -> dict:
    # Create standalone payment transaction
```

---

## 4. Common Services

### 4.1 CurrentUserService
**Path**: `src/app/application/common/services/current_user.py`

Provides access to the currently authenticated user.

**Usage**:
```python
user = await self._current_user_service.get_current_user()
user_id = user.id_.value
```

---

### 4.2 TransactionManager
**Path**: `src/app/application/common/ports/transaction_manager.py`

Manages database transactions.

**Usage**:
```python
await self._tx.commit()
```

---

## 5. Stripe Integration

### 5.1 Configuration Loading
```python
from app.setup.config.settings import load_settings

settings = load_settings()
stripe_cfg = getattr(settings, "stripe", None)
api_key = getattr(stripe_cfg, "STRIPE_API_KEY", None)
```

### 5.2 Stripe API Calls

| Operation | API Call |
|-----------|----------|
| Create Product | `stripe.Product.create(name=...)` |
| Create Price | `stripe.Price.create(unit_amount=..., currency=..., recurring=...)` |
| Create Checkout | `stripe.checkout.Session.create(mode="subscription", ...)` |
| Retrieve Session | `stripe.checkout.Session.retrieve(session_id)` |
| Cancel Subscription | `stripe.Subscription.delete(subscription_id)` |

---

## 6. Service Dependencies Graph

```
┌─────────────────────────────────────────────────────────────────┐
│                      Presentation Layer                          │
│  (subscription/router.py, payment/router.py)                    │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                       Handler Layer                              │
│                                                                  │
│  ┌────────────────────┐  ┌────────────────────┐                │
│  │GetSubscriptionsHdlr│  │CreateSubscriptionHdlr│               │
│  └────────────────────┘  └────────────────────┘                │
│                                                                  │
│  ┌────────────────────┐  ┌────────────────────┐                │
│  │InitSubscriptionsHdlr│  │CancelSubscriptionHdlr│              │
│  └────────────────────┘  └────────────────────┘                │
│                                                                  │
│  ┌────────────────────┐                                        │
│  │SubscriptionSuccessHdlr│                                     │
│  └────────────────────┘                                        │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Common Services                             │
│                                                                  │
│  ┌────────────────────┐  ┌────────────────────┐                │
│  │  CurrentUserService│  │ TransactionManager │                │
│  └────────────────────┘  └────────────────────┘                │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                     Repository Layer                             │
│                                                                  │
│  ┌────────────────────┐  ┌────────────────────┐                │
│  │SubscriptionRepo    │  │SubscriptionUserRepo│                │
│  └────────────────────┘  └────────────────────┘                │
│                                                                  │
│  ┌────────────────────┐  ┌────────────────────┐                │
│  │   PaymentRepo      │  │ NotificationRepo   │                │
│  └────────────────────┘  └────────────────────┘                │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                     External Services                            │
│                                                                  │
│  ┌────────────────────────────────────────────────────────┐    │
│  │                    Stripe API                            │    │
│  │  Products • Prices • Checkout Sessions • Subscriptions  │    │
│  └────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
```

---

## 7. Dependency Injection

Handlers are registered in the IoC container for automatic injection.

**Registration** (example):
```python
from dishka import Provider, provide

class SubscriptionProvider(Provider):
    @provide
    def get_subscriptions_handler(
        self, subscription_repo: SubscriptionRepository
    ) -> GetSubscriptionsHandler:
        return GetSubscriptionsHandler(subscription_repo)
```

---

## References

- **Handlers**: `src/app/infrastructure/subscription/handlers/`
- **Ports**: `src/app/application/subscription/ports.py`
- **Repositories**: `src/app/infrastructure/adapters/*_repository_sqla.py`
- **Routers**: `src/app/presentation/http/controllers/subscription/router.py`
