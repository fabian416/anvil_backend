# Subscriptions & Payments Test Specification

> **Last Updated**: 2026-01-25  
> **Status**: Partial Coverage  
> **Maintainers**: @backend-engineer @error-detective @code-reviewer

---

## Executive Summary

The Subscriptions & Payments system has test coverage across multiple test types:
- **Unit Tests**: 1 file with controller tests
- **Integration Tests**: 2 files testing lifecycle and flows
- **E2E Tests**: 1 file testing complete workflows
- **Test Builders**: 1 comprehensive builder for test data

**Total Test Files**: 5 direct files + several related tests

---

## 1. Existing Unit Tests

### 1.1 Subscription Controllers
**Path**: `tests/unit/presentation/subscription/test_subscription_controllers.py`

| Test Class | Tests | Coverage |
|------------|-------|----------|
| `TestListSubscriptionsController` | 3 | Response structure, auth requirement, features |
| `TestCreateSubscriptionController` | 4 | Request/response structure, invalid plan error, auth |
| `TestCancelSubscriptionController` | 3 | Confirmation, nonexistent error, already cancelled |
| `TestSubscriptionSuccessController` | 2 | Request structure, activation |
| `TestPaymentFailureHandling` | 2 | Payment failed, card declined |
| `TestSubscriptionBuilderIntegration` | 4 | Builder functionality |

**Key Tests**:
```python
class TestListSubscriptionsController:
    def test_list_subscriptions_response_structure()
    def test_list_subscriptions_requires_authentication()
    def test_plan_features_included()

class TestCreateSubscriptionController:
    def test_create_subscription_request_structure()
    def test_create_subscription_response_structure()
    def test_create_subscription_invalid_plan_error()
    def test_create_subscription_requires_authentication()

class TestCancelSubscriptionController:
    def test_cancel_subscription_returns_confirmation()
    def test_cancel_nonexistent_subscription_error()
    def test_cancel_already_cancelled_error()
```

---

## 2. Existing Integration Tests

### 2.1 Subscription Lifecycle
**Path**: `tests/integration/subscription/test_subscription_lifecycle.py`

| Test Class | Tests | Coverage |
|------------|-------|----------|
| `TestListSubscriptionPlans` | 3 | List plans, pricing, unauthenticated access |
| `TestCreateSubscription` | 3 | Checkout URL, invalid plan, without auth |
| `TestSubscriptionSuccess` | 2 | Activation, invalid session |
| `TestCancelSubscription` | 3 | Cancel active, nonexistent, without auth |
| `TestPaymentFailure` | 1 | Payment failure handling |
| `TestSubscriptionWebhooks` | 1 | Webhook signature validation (placeholder) |
| `TestSubscriptionPlanUpgrade` | 2 | Upgrade/downgrade (placeholders) |

**Key Tests**:
```python
class TestListSubscriptionPlans:
    def test_list_plans_returns_array(self, client)
    def test_plans_include_pricing(self, client)
    def test_unauthenticated_cannot_list_plans(self, client)

class TestCreateSubscription:
    def test_create_subscription_returns_checkout_url(self, client)
    def test_create_subscription_invalid_plan(self, client)
    def test_create_subscription_without_auth(self, client)

class TestCancelSubscription:
    def test_cancel_active_subscription(self, client)
    def test_cancel_nonexistent_subscription(self, client)
    def test_cancel_without_auth(self, client)
```

---

### 2.2 Subscription Payment Flow
**Path**: `tests/integration/flows/test_subscription_payment_flow.py`

Tests the complete subscription payment flow integration.

---

## 3. Existing E2E Tests

### 3.1 Subscription Workflow
**Path**: `tests/e2e/subscription/test_subscription_workflow.py`

| Test Class | Tests | Coverage |
|------------|-------|----------|
| `TestSubscriptionWorkflow` | 2 | View plans + subscribe, cancel journey |
| `TestSubscriptionAccessControl` | 2 | Free user limits, premium features |
| `TestSubscriptionErrorHandling` | 2 | Invalid plan, unauthenticated denied |

**Key Tests**:
```python
class TestSubscriptionWorkflow:
    def test_view_plans_and_subscribe_journey(self, client):
        """
        Test subscription journey:
        1. Login
        2. View available plans
        3. Create subscription
        4. Check subscription status
        """
        
    def test_cancel_subscription_journey(self, client):
        """
        Test subscription cancellation:
        1. Login (user with subscription)
        2. Cancel subscription
        3. Verify cancellation
        """

class TestSubscriptionAccessControl:
    def test_free_user_access_limitations(self, client)
    def test_premium_features_require_subscription(self, client)
```

---

## 4. Test Builders

### 4.1 SubscriptionBuilder
**Path**: `tests/builders/subscription_builder.py`

Comprehensive builder for creating subscription test data.

**Features**:
- Plan tiers: free, basic, premium, enterprise
- Statuses: active, cancelled, expired, pending, past_due, trialing
- Payment statuses: succeeded, pending, failed, refunded
- Stripe ID generation

**Usage**:
```python
from tests.builders.subscription_builder import a_subscription

# Basic subscription
sub = a_subscription().for_user(user_id).build_dict()

# Premium active subscription
sub = (
    a_premium_subscription()
    .for_user(user_id)
    .as_active()
    .build_dict()
)

# Cancelled subscription
sub = a_cancelled_subscription().for_user(user_id).build()

# Failed payment subscription
sub = a_failed_payment_subscription().build()
```

**Builder Methods**:
```python
class SubscriptionBuilder:
    # Identity
    def with_id(self, id_: UUID)
    def for_user(self, user_id: UUID)
    
    # Plan
    def with_plan(self, tier: PlanTier)
    def as_free()
    def as_basic()
    def as_premium()
    def as_enterprise()
    
    # Status
    def with_status(self, status: SubscriptionStatus)
    def as_active()
    def as_cancelled(cancelled_at=None)
    def as_expired()
    def as_pending()
    def as_past_due()
    def as_trialing(days=14)
    
    # Payment
    def with_payment_status(self, status: PaymentStatus)
    def with_failed_payment(reason="card_declined")
    def with_refunded_payment()
    
    # Stripe
    def with_stripe_ids(subscription_id, customer_id)
    
    # Build
    def build_dict() -> dict
    def build_entity() -> TestSubscription
    def build_api_response() -> dict
```

---

## 5. Related Test Files

These files contain subscription/payment related tests:

| File | Relevance |
|------|-----------|
| `tests/conftest.py` | May include subscription fixtures |
| `tests/integration/advanced/test_complex_business_scenarios.py` | Complex subscription scenarios |
| `tests/integration/errors/test_error_scenarios.py` | Payment error handling |
| `tests/edge_cases/test_boundary_conditions.py` | Edge cases |

---

## 6. Missing Tests (Gaps Analysis)

### 6.1 Critical Missing Tests

| Area | Missing Test | Priority | Description |
|------|-------------|----------|-------------|
| **Handlers** | Unit tests | HIGH | Handler business logic |
| **Repositories** | Unit tests | HIGH | Repository methods |
| **Stripe Integration** | Mocked tests | HIGH | Stripe API calls |
| **Webhooks** | Integration tests | HIGH | Webhook event handling |
| **Concurrent Access** | Integration tests | MEDIUM | Race conditions |

### 6.2 Missing Unit Tests

```python
# 1. tests/unit/infrastructure/subscription/test_get_subscriptions_handler.py
class TestGetSubscriptionsHandler:
    def test_returns_all_active_subscriptions()
    def test_transforms_to_subscription_items()
    def test_handles_empty_result()
    def test_handles_repository_error()

# 2. tests/unit/infrastructure/subscription/test_create_subscription_handler.py
class TestCreateSubscriptionHandler:
    def test_creates_subscription_user_record()
    def test_creates_payment_record()
    def test_creates_stripe_checkout_session()
    def test_handles_subscription_not_found()
    def test_handles_stripe_error()
    def test_commits_transaction_on_success()
    def test_rollback_on_failure()

# 3. tests/unit/infrastructure/subscription/test_cancel_subscription_handler.py
class TestCancelSubscriptionHandler:
    def test_cancels_stripe_subscription()
    def test_updates_subscription_user_status()
    def test_cancels_all_related_payments()
    def test_handles_no_active_subscription()
    def test_handles_stripe_cancellation_failure()

# 4. tests/unit/infrastructure/subscription/test_success_subscription_handler.py
class TestSubscriptionSuccessHandler:
    def test_activates_subscription()
    def test_stores_stripe_subscription_id()
    def test_completes_pending_payment()
    def test_handles_invalid_session()
    def test_handles_subscription_not_found()

# 5. tests/unit/infrastructure/adapters/test_subscription_repository.py
class TestSqlaSubscriptionRepository:
    def test_read_by_name()
    def test_read_all()
    def test_read_by_id()
    def test_add()
    def test_update_stripe_ids()

# 6. tests/unit/infrastructure/adapters/test_payment_repository.py
class TestSqlaPaymentRepository:
    def test_add()
    def test_find_pending_for_subscription_user()
    def test_update_status()
    def test_list_by_subscription_user()
    def test_read_by_user_paginated()
    def test_find_or_create_transaction()
```

### 6.3 Missing Integration Tests

```python
# 1. tests/integration/subscription/test_stripe_integration.py
class TestStripeIntegration:
    def test_checkout_session_creation()
    def test_checkout_session_completion()
    def test_subscription_cancellation_in_stripe()
    def test_handles_stripe_api_errors()

# 2. tests/integration/subscription/test_webhook_handling.py
class TestWebhookHandling:
    def test_checkout_session_completed_event()
    def test_invoice_paid_event()
    def test_invoice_payment_failed_event()
    def test_customer_subscription_deleted_event()
    def test_rejects_invalid_signature()

# 3. tests/integration/subscription/test_concurrent_subscription.py
class TestConcurrentSubscription:
    def test_prevents_duplicate_subscription()
    def test_handles_race_condition_on_cancel()
    def test_handles_concurrent_payment_updates()

# 4. tests/integration/payment/test_payment_history.py
class TestPaymentHistory:
    def test_paginated_payment_retrieval()
    def test_filters_by_user()
    def test_orders_by_created_at()
```

### 6.4 Missing E2E Tests

```python
# 1. tests/e2e/subscription/test_complete_subscription_flow.py
class TestCompleteSubscriptionFlow:
    def test_signup_to_subscription_to_cancellation()
    def test_subscription_upgrade_flow()
    def test_subscription_downgrade_flow()
    def test_payment_retry_flow()

# 2. tests/e2e/subscription/test_subscription_access.py
class TestSubscriptionAccess:
    def test_free_tier_rate_limits()
    def test_premium_tier_unlimited_access()
    def test_expired_subscription_downgrades_access()
```

---

## 7. Test Commands

### Run All Subscription Tests

```bash
# All subscription tests
pytest tests/ -k "subscription" -v

# Unit tests only
pytest tests/unit/presentation/subscription/ -v

# Integration tests only
pytest tests/integration/subscription/ -v

# E2E tests only
pytest tests/e2e/subscription/ -v
```

### Run with Coverage

```bash
# Coverage for subscription module
pytest tests/ -k "subscription" \
  --cov=src/app/infrastructure/subscription \
  --cov=src/app/presentation/http/controllers/subscription \
  --cov-report=html
```

---

## 8. Test Coverage Goals

| Layer | Current | Target | Gap |
|-------|---------|--------|-----|
| Handlers | ~20% | 80% | 60% |
| Repositories | ~10% | 70% | 60% |
| Controllers | ~40% | 75% | 35% |
| Integration | ~30% | 70% | 40% |

---

## 9. Test Fixtures

### Required Fixtures

```python
@pytest.fixture
def subscription_repo_mock():
    """Mock SubscriptionRepository."""
    repo = AsyncMock(spec=SubscriptionRepository)
    repo.read_all.return_value = [
        {"id": 1, "name": "PRO", "price": 9.99, ...},
        {"id": 2, "name": "CORPORATE", "price": 49.99, ...},
    ]
    return repo

@pytest.fixture
def stripe_mock(mocker):
    """Mock Stripe API."""
    mock = mocker.patch("stripe.checkout.Session.create")
    mock.return_value = {"id": "cs_test_xxx", "url": "https://..."}
    return mock

@pytest.fixture
def authenticated_user(test_client):
    """Create authenticated user with token."""
    user, token = AuthHelper.create_test_user()
    return user, {"Authorization": f"Bearer {token}"}
```

---

## References

- **Unit Tests**: `tests/unit/presentation/subscription/`
- **Integration Tests**: `tests/integration/subscription/`
- **E2E Tests**: `tests/e2e/subscription/`
- **Test Builders**: `tests/builders/subscription_builder.py`
- **Pytest Config**: `pyproject.toml`
