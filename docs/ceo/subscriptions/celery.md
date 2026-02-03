# Subscriptions & Payments Celery Tasks Specification

> **Last Updated**: 2026-01-25  
> **Status**: Not Implemented  
> **Maintainers**: @backend-engineer @error-detective @code-reviewer

---

## Executive Summary

The Subscriptions & Payments module currently **does not have dedicated Celery tasks**. All subscription operations are handled synchronously within the request lifecycle.

This document outlines recommended Celery tasks that should be implemented for production readiness.

---

## 1. Current State

**Status**: No Celery tasks implemented

**Current Implementation**:
- Subscription creation: Synchronous (blocks until Stripe responds)
- Payment processing: Synchronous
- Subscription cancellation: Synchronous
- Success callback: Synchronous

**Limitations**:
- Stripe API calls block HTTP requests
- No retry logic for failed operations
- No scheduled maintenance tasks
- No subscription expiration handling

---

## 2. Recommended Celery Tasks

### 2.1 Process Subscription Webhook

**Task Name**: `process_subscription_webhook`  
**Priority**: HIGH  
**Schedule**: On-demand (triggered by webhook)

**Purpose**: Handle Stripe webhook events asynchronously to avoid blocking.

**Implementation Recommendation**:
```python
@celery_app.task(name="process_subscription_webhook", bind=True, max_retries=3)
def process_subscription_webhook(self, event_type: str, event_data: dict):
    """
    Process Stripe webhook events asynchronously.
    
    Events handled:
    - checkout.session.completed
    - invoice.paid
    - invoice.payment_failed
    - customer.subscription.deleted
    - customer.subscription.updated
    """
    async def runner(container):
        from app.infrastructure.subscription.handlers.webhook_handler import WebhookHandler
        
        handler = await container.get(WebhookHandler)
        await handler.process_event(event_type, event_data)
    
    try:
        asyncio.run(_run_task(runner))
    except Exception as e:
        self.retry(exc=e, countdown=60)
```

---

### 2.2 Check Expiring Subscriptions

**Task Name**: `check_expiring_subscriptions`  
**Priority**: HIGH  
**Schedule**: Daily at 00:00 UTC

**Purpose**: Notify users about subscriptions expiring soon.

**Implementation Recommendation**:
```python
@celery_app.task(name="check_expiring_subscriptions")
def check_expiring_subscriptions():
    """
    Check for subscriptions expiring within 7 days.
    Send reminder notifications to users.
    
    Runs daily at midnight.
    """
    async def runner(container):
        from datetime import datetime, UTC, timedelta
        from app.application.subscription.ports import SubscriptionUserRepository
        from app.application.notification.ports import NotificationRepository
        
        subs_repo = await container.get(SubscriptionUserRepository)
        notif_repo = await container.get(NotificationRepository)
        
        expiring_soon = datetime.now(UTC) + timedelta(days=7)
        
        subscriptions = await subs_repo.read_expiring_before(expiring_soon)
        
        for sub in subscriptions:
            await notif_repo.create_expiration_reminder(
                user_id=sub["user_id"],
                subscription_id=sub["id"],
                expires_at=sub["end_date"],
            )
        
        print(f"Sent {len(subscriptions)} expiration reminders")
    
    asyncio.run(_run_task(runner))
```

**Beat Schedule**:
```python
"check-expiring-subscriptions": {
    "task": "check_expiring_subscriptions",
    "schedule": crontab(hour=0, minute=0),
},
```

---

### 2.3 Process Expired Subscriptions

**Task Name**: `process_expired_subscriptions`  
**Priority**: HIGH  
**Schedule**: Hourly

**Purpose**: Mark expired subscriptions as inactive.

**Implementation Recommendation**:
```python
@celery_app.task(name="process_expired_subscriptions")
def process_expired_subscriptions():
    """
    Find and process expired subscriptions.
    
    - Updates status to 'expired'
    - Downgrades user access
    - Sends expiration notification
    
    Runs hourly.
    """
    async def runner(container):
        from datetime import datetime, UTC
        from app.application.subscription.ports import SubscriptionUserRepository
        
        subs_repo = await container.get(SubscriptionUserRepository)
        
        now = datetime.now(UTC)
        expired = await subs_repo.read_active_expired_before(now)
        
        for sub in expired:
            await subs_repo.update_status(id_=sub["id"], status="expired")
        
        print(f"Processed {len(expired)} expired subscriptions")
    
    asyncio.run(_run_task(runner))
```

**Beat Schedule**:
```python
"process-expired-subscriptions": {
    "task": "process_expired_subscriptions",
    "schedule": crontab(minute=0),  # Every hour
},
```

---

### 2.4 Sync Subscription Status with Stripe

**Task Name**: `sync_subscription_status`  
**Priority**: MEDIUM  
**Schedule**: Every 6 hours

**Purpose**: Reconcile local subscription status with Stripe.

**Implementation Recommendation**:
```python
@celery_app.task(name="sync_subscription_status")
def sync_subscription_status():
    """
    Sync subscription status with Stripe to handle missed webhooks.
    
    - Fetches active subscriptions from Stripe
    - Updates local status if different
    - Logs discrepancies for investigation
    
    Runs every 6 hours.
    """
    async def runner(container):
        import stripe
        from app.setup.config.settings import load_settings
        from app.application.subscription.ports import SubscriptionUserRepository
        
        settings = load_settings()
        stripe.api_key = settings.stripe.STRIPE_API_KEY
        
        subs_repo = await container.get(SubscriptionUserRepository)
        local_subs = await subs_repo.read_all_with_stripe_id()
        
        synced = 0
        for sub in local_subs:
            try:
                stripe_sub = stripe.Subscription.retrieve(sub["stripe_subscription_id"])
                if stripe_sub.status != sub["status"]:
                    await subs_repo.update_status(
                        id_=sub["id"], 
                        status=stripe_sub.status
                    )
                    synced += 1
            except stripe.error.StripeError:
                continue
        
        print(f"Synced {synced} subscriptions with Stripe")
    
    asyncio.run(_run_task(runner))
```

**Beat Schedule**:
```python
"sync-subscription-status": {
    "task": "sync_subscription_status",
    "schedule": crontab(hour="*/6", minute=30),
},
```

---

### 2.5 Generate Subscription Analytics

**Task Name**: `generate_subscription_analytics`  
**Priority**: LOW  
**Schedule**: Daily at 02:00 UTC

**Purpose**: Generate daily subscription metrics and MRR reports.

**Implementation Recommendation**:
```python
@celery_app.task(name="generate_subscription_analytics")
def generate_subscription_analytics():
    """
    Generate subscription analytics.
    
    Metrics:
    - Active subscriptions by plan
    - Monthly Recurring Revenue (MRR)
    - Churn rate
    - New subscriptions
    - Cancelled subscriptions
    
    Runs daily at 2 AM.
    """
    async def runner(container):
        from datetime import datetime, UTC, timedelta
        from app.application.analytics.subscription_analytics import SubscriptionAnalytics
        
        analytics = await container.get(SubscriptionAnalytics)
        
        yesterday = datetime.now(UTC) - timedelta(days=1)
        
        metrics = await analytics.generate_daily_report(date=yesterday)
        
        print(f"Generated analytics: MRR=${metrics['mrr']:.2f}, "
              f"Active={metrics['active_count']}, "
              f"Churn={metrics['churn_rate']:.2%}")
    
    asyncio.run(_run_task(runner))
```

**Beat Schedule**:
```python
"generate-subscription-analytics": {
    "task": "generate_subscription_analytics",
    "schedule": crontab(hour=2, minute=0),
},
```

---

### 2.6 Retry Failed Payments

**Task Name**: `retry_failed_payments`  
**Priority**: HIGH  
**Schedule**: Every 4 hours

**Purpose**: Retry failed payments for subscriptions in grace period.

**Implementation Recommendation**:
```python
@celery_app.task(name="retry_failed_payments", bind=True, max_retries=3)
def retry_failed_payments(self):
    """
    Retry failed payments for subscriptions in dunning.
    
    - Finds subscriptions with failed payments
    - Attempts to charge saved payment method
    - Updates status on success/failure
    
    Runs every 4 hours.
    """
    async def runner(container):
        import stripe
        from app.application.subscription.ports import (
            SubscriptionUserRepository,
            PaymentRepository,
        )
        
        subs_repo = await container.get(SubscriptionUserRepository)
        payment_repo = await container.get(PaymentRepository)
        
        failed = await subs_repo.read_with_failed_payments()
        
        retried = 0
        for sub in failed:
            try:
                # Attempt payment via Stripe
                invoice = stripe.Invoice.pay(sub["latest_invoice_id"])
                if invoice.status == "paid":
                    await subs_repo.update_status(id_=sub["id"], status="active")
                    retried += 1
            except stripe.error.CardError:
                continue
        
        print(f"Retried {retried} failed payments")
    
    asyncio.run(_run_task(runner))
```

**Beat Schedule**:
```python
"retry-failed-payments": {
    "task": "retry_failed_payments",
    "schedule": crontab(hour="*/4", minute=15),
},
```

---

## 3. Recommended Beat Schedule

```python
celery_app.conf.beat_schedule.update({
    # Subscription tasks (to be implemented)
    "check-expiring-subscriptions": {
        "task": "check_expiring_subscriptions",
        "schedule": crontab(hour=0, minute=0),  # Daily midnight
    },
    "process-expired-subscriptions": {
        "task": "process_expired_subscriptions",
        "schedule": crontab(minute=0),  # Every hour
    },
    "sync-subscription-status": {
        "task": "sync_subscription_status",
        "schedule": crontab(hour="*/6", minute=30),  # Every 6 hours
    },
    "generate-subscription-analytics": {
        "task": "generate_subscription_analytics",
        "schedule": crontab(hour=2, minute=0),  # Daily 2 AM
    },
    "retry-failed-payments": {
        "task": "retry_failed_payments",
        "schedule": crontab(hour="*/4", minute=15),  # Every 4 hours
    },
})
```

---

## 4. Implementation Priority

| Task | Priority | Effort | Business Impact |
|------|----------|--------|-----------------|
| process_subscription_webhook | HIGH | Medium | Critical for Stripe integration |
| process_expired_subscriptions | HIGH | Low | Revenue protection |
| check_expiring_subscriptions | HIGH | Low | User retention |
| retry_failed_payments | HIGH | Medium | Revenue recovery |
| sync_subscription_status | MEDIUM | Medium | Data integrity |
| generate_subscription_analytics | LOW | Medium | Business insights |

---

## 5. Related Existing Tasks

While there are no subscription-specific tasks, these existing tasks interact with subscription data:

| Task | Relevance |
|------|-----------|
| `cleanup_expired_sessions` | May affect subscription user sessions |
| `update_user_context` | User context includes subscription tier |

---

## References

- **Celery App**: `src/app/infrastructure/celery/app.py`
- **Main Tasks**: `src/app/infrastructure/celery/tasks.py`
- **Subscription Handlers**: `src/app/infrastructure/subscription/handlers/`
