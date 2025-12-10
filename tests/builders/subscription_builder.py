"""
Builder for creating Subscription test data.

Provides fluent interface for test data creation with support for:
- Different subscription plan tiers
- Various payment statuses
- Subscription lifecycle states

Usage:
    from tests.builders.subscription_builder import SubscriptionBuilder, a_subscription

    # Basic subscription
    sub = a_subscription().for_user(user_id).build_dict()

    # Premium subscription
    sub = (
        a_premium_subscription()
        .for_user(user_id)
        .with_payment_method("card")
        .as_active()
        .build_dict()
    )
"""

from uuid import uuid4, UUID
from datetime import datetime, timedelta
from typing import Literal
from dataclasses import dataclass, field


# Type aliases
PlanTier = Literal["free", "basic", "premium", "enterprise"]
SubscriptionStatus = Literal["active", "cancelled", "expired", "pending", "past_due", "trialing"]
PaymentStatus = Literal["succeeded", "pending", "failed", "refunded"]


@dataclass
class TestSubscription:
    """
    Represents a test subscription.

    Attributes:
        id: Unique subscription identifier
        user_id: Subscriber user ID
        plan_tier: Subscription plan tier
        status: Subscription status
        payment_status: Last payment status
        stripe_subscription_id: Stripe subscription ID
        stripe_customer_id: Stripe customer ID
        current_period_start: Current billing period start
        current_period_end: Current billing period end
        created_at: Subscription creation time
        cancelled_at: Cancellation time (if cancelled)
        metadata: Additional metadata
    """

    id: UUID
    user_id: UUID
    plan_tier: PlanTier
    status: SubscriptionStatus = "active"
    payment_status: PaymentStatus = "succeeded"
    stripe_subscription_id: str | None = None
    stripe_customer_id: str | None = None
    current_period_start: datetime = field(default_factory=datetime.utcnow)
    current_period_end: datetime = field(default_factory=lambda: datetime.utcnow() + timedelta(days=30))
    created_at: datetime = field(default_factory=datetime.utcnow)
    cancelled_at: datetime | None = None
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        """Convert to dictionary representation."""
        result = {
            "id": str(self.id),
            "user_id": str(self.user_id),
            "plan_tier": self.plan_tier,
            "status": self.status,
            "payment_status": self.payment_status,
            "stripe_subscription_id": self.stripe_subscription_id,
            "stripe_customer_id": self.stripe_customer_id,
            "current_period_start": self.current_period_start.isoformat(),
            "current_period_end": self.current_period_end.isoformat(),
            "created_at": self.created_at.isoformat(),
        }
        if self.cancelled_at:
            result["cancelled_at"] = self.cancelled_at.isoformat()
        if self.metadata:
            result["metadata"] = self.metadata
        return result


@dataclass
class TestSubscriptionPlan:
    """
    Represents a subscription plan.

    Attributes:
        id: Plan identifier
        name: Plan display name
        tier: Plan tier
        price: Monthly price in cents
        features: List of included features
        stripe_price_id: Stripe price ID
        is_active: Whether plan is available
    """

    id: str
    name: str
    tier: PlanTier
    price: int  # cents
    features: list[str] = field(default_factory=list)
    stripe_price_id: str | None = None
    is_active: bool = True

    def to_dict(self) -> dict:
        """Convert to dictionary representation."""
        return {
            "id": self.id,
            "name": self.name,
            "tier": self.tier,
            "price": self.price,
            "price_display": f"${self.price / 100:.2f}/month",
            "features": self.features,
            "stripe_price_id": self.stripe_price_id,
            "is_active": self.is_active,
        }


class SubscriptionBuilder:
    """
    Fluent builder for Subscription test data.

    Supports building subscriptions with different plans, statuses,
    and payment configurations.
    """

    # Plan configurations
    PLANS = {
        "free": {"name": "Free", "price": 0, "features": ["Basic chat", "5 messages/day"]},
        "basic": {"name": "Basic", "price": 999, "features": ["Unlimited chat", "Basic analytics"]},
        "premium": {
            "name": "Premium",
            "price": 2999,
            "features": ["Unlimited chat", "Advanced analytics", "Priority support", "API access"],
        },
        "enterprise": {
            "name": "Enterprise",
            "price": 9999,
            "features": ["Everything in Premium", "Custom integrations", "Dedicated support", "SLA"],
        },
    }

    def __init__(self):
        """Initialize with default values."""
        self._id: UUID = uuid4()
        self._user_id: UUID = uuid4()
        self._plan_tier: PlanTier = "basic"
        self._status: SubscriptionStatus = "active"
        self._payment_status: PaymentStatus = "succeeded"
        self._stripe_subscription_id: str | None = f"sub_{uuid4().hex[:24]}"
        self._stripe_customer_id: str | None = f"cus_{uuid4().hex[:24]}"
        self._payment_method: str | None = "card"
        self._current_period_start: datetime = datetime.utcnow()
        self._current_period_end: datetime = datetime.utcnow() + timedelta(days=30)
        self._created_at: datetime = datetime.utcnow()
        self._cancelled_at: datetime | None = None
        self._metadata: dict = {}

    def with_id(self, id_: UUID) -> "SubscriptionBuilder":
        """Set subscription ID."""
        self._id = id_
        return self

    def for_user(self, user_id: UUID) -> "SubscriptionBuilder":
        """Set user ID."""
        self._user_id = user_id
        return self

    def with_plan(self, tier: PlanTier) -> "SubscriptionBuilder":
        """Set subscription plan tier."""
        self._plan_tier = tier
        return self

    def with_status(self, status: SubscriptionStatus) -> "SubscriptionBuilder":
        """Set subscription status."""
        self._status = status
        return self

    def with_payment_status(self, status: PaymentStatus) -> "SubscriptionBuilder":
        """Set payment status."""
        self._payment_status = status
        return self

    def with_stripe_ids(
        self,
        subscription_id: str | None = None,
        customer_id: str | None = None,
    ) -> "SubscriptionBuilder":
        """Set Stripe IDs."""
        if subscription_id:
            self._stripe_subscription_id = subscription_id
        if customer_id:
            self._stripe_customer_id = customer_id
        return self

    def with_payment_method(self, method: str) -> "SubscriptionBuilder":
        """Set payment method."""
        self._payment_method = method
        return self

    def with_period(
        self,
        start: datetime,
        end: datetime | None = None,
    ) -> "SubscriptionBuilder":
        """Set billing period."""
        self._current_period_start = start
        self._current_period_end = end or (start + timedelta(days=30))
        return self

    def with_metadata(self, metadata: dict) -> "SubscriptionBuilder":
        """Set subscription metadata."""
        self._metadata = metadata
        return self

    # Status convenience methods
    def as_active(self) -> "SubscriptionBuilder":
        """Configure as active subscription."""
        self._status = "active"
        self._payment_status = "succeeded"
        return self

    def as_cancelled(self, cancelled_at: datetime | None = None) -> "SubscriptionBuilder":
        """Configure as cancelled subscription."""
        self._status = "cancelled"
        self._cancelled_at = cancelled_at or datetime.utcnow()
        return self

    def as_expired(self) -> "SubscriptionBuilder":
        """Configure as expired subscription."""
        self._status = "expired"
        self._current_period_end = datetime.utcnow() - timedelta(days=1)
        return self

    def as_pending(self) -> "SubscriptionBuilder":
        """Configure as pending subscription."""
        self._status = "pending"
        self._payment_status = "pending"
        return self

    def as_past_due(self) -> "SubscriptionBuilder":
        """Configure as past due subscription."""
        self._status = "past_due"
        self._payment_status = "failed"
        return self

    def as_trialing(self, days: int = 14) -> "SubscriptionBuilder":
        """Configure as trialing subscription."""
        self._status = "trialing"
        self._current_period_end = datetime.utcnow() + timedelta(days=days)
        return self

    # Plan convenience methods
    def as_free(self) -> "SubscriptionBuilder":
        """Configure as free plan."""
        return self.with_plan("free")

    def as_basic(self) -> "SubscriptionBuilder":
        """Configure as basic plan."""
        return self.with_plan("basic")

    def as_premium(self) -> "SubscriptionBuilder":
        """Configure as premium plan."""
        return self.with_plan("premium")

    def as_enterprise(self) -> "SubscriptionBuilder":
        """Configure as enterprise plan."""
        return self.with_plan("enterprise")

    # Payment failure scenarios
    def with_failed_payment(self, reason: str = "card_declined") -> "SubscriptionBuilder":
        """Configure with failed payment."""
        self._payment_status = "failed"
        self._metadata["payment_failure_reason"] = reason
        return self

    def with_refunded_payment(self) -> "SubscriptionBuilder":
        """Configure with refunded payment."""
        self._payment_status = "refunded"
        return self

    def build_dict(self) -> dict:
        """Build as dictionary."""
        result = {
            "id": str(self._id),
            "user_id": str(self._user_id),
            "plan_tier": self._plan_tier,
            "plan_name": self.PLANS[self._plan_tier]["name"],
            "status": self._status,
            "payment_status": self._payment_status,
            "stripe_subscription_id": self._stripe_subscription_id,
            "stripe_customer_id": self._stripe_customer_id,
            "payment_method": self._payment_method,
            "current_period_start": self._current_period_start.isoformat(),
            "current_period_end": self._current_period_end.isoformat(),
            "created_at": self._created_at.isoformat(),
        }
        if self._cancelled_at:
            result["cancelled_at"] = self._cancelled_at.isoformat()
        if self._metadata:
            result["metadata"] = self._metadata
        return result

    def build_entity(self) -> TestSubscription:
        """Build as TestSubscription dataclass."""
        return TestSubscription(
            id=self._id,
            user_id=self._user_id,
            plan_tier=self._plan_tier,
            status=self._status,
            payment_status=self._payment_status,
            stripe_subscription_id=self._stripe_subscription_id,
            stripe_customer_id=self._stripe_customer_id,
            current_period_start=self._current_period_start,
            current_period_end=self._current_period_end,
            created_at=self._created_at,
            cancelled_at=self._cancelled_at,
            metadata=self._metadata,
        )

    def build_api_response(self) -> dict:
        """Build as API response format."""
        plan = self.PLANS[self._plan_tier]
        return {
            "id": str(self._id),
            "plan": {
                "tier": self._plan_tier,
                "name": plan["name"],
                "price": plan["price"],
                "features": plan["features"],
            },
            "status": self._status,
            "current_period_end": self._current_period_end.isoformat(),
            "is_active": self._status == "active",
        }

    def build(self) -> "TestSubscription":
        """Build as TestSubscription dataclass. Alias for build_entity."""
        return self.build_entity()

    @classmethod
    def a_subscription(cls) -> "SubscriptionBuilder":
        """Start building a subscription."""
        return cls()

    @classmethod
    def a_free_subscription(cls) -> "SubscriptionBuilder":
        """Build a free subscription."""
        return cls().as_free()

    @classmethod
    def a_premium_subscription(cls) -> "SubscriptionBuilder":
        """Build a premium subscription."""
        return cls().as_premium()

    @classmethod
    def build_plan(cls, tier: PlanTier) -> TestSubscriptionPlan:
        """Build a subscription plan."""
        plan = cls.PLANS[tier]
        return TestSubscriptionPlan(
            id=f"plan_{tier}",
            name=plan["name"],
            tier=tier,
            price=plan["price"],
            features=plan["features"],
            stripe_price_id=f"price_{uuid4().hex[:24]}",
        )

    @classmethod
    def build_all_plans(cls) -> list[TestSubscriptionPlan]:
        """Build all subscription plans."""
        return [cls.build_plan(tier) for tier in ["free", "basic", "premium", "enterprise"]]


# Convenience functions
def a_subscription() -> SubscriptionBuilder:
    """Start building a subscription."""
    return SubscriptionBuilder()


def a_free_subscription() -> SubscriptionBuilder:
    """Build a free subscription."""
    return SubscriptionBuilder().as_free()


def a_basic_subscription() -> SubscriptionBuilder:
    """Build a basic subscription."""
    return SubscriptionBuilder().as_basic()


def a_premium_subscription() -> SubscriptionBuilder:
    """Build a premium subscription."""
    return SubscriptionBuilder().as_premium()


def an_enterprise_subscription() -> SubscriptionBuilder:
    """Build an enterprise subscription."""
    return SubscriptionBuilder().as_enterprise()


def a_cancelled_subscription() -> SubscriptionBuilder:
    """Build a cancelled subscription."""
    return SubscriptionBuilder().as_cancelled()


def a_failed_payment_subscription() -> SubscriptionBuilder:
    """Build a subscription with failed payment."""
    return SubscriptionBuilder().with_failed_payment()
