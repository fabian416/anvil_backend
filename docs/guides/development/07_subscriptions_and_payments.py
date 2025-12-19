"""
Anvil Platform - SQLAlchemy Models
Section 7: Subscription and Payment Models

These models handle subscription management and payment processing via Stripe.
"""

from datetime import datetime
from typing import Optional
from sqlalchemy import (
    Column,
    Integer,
    String,
    Numeric,
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Text,
    Enum as SQLEnum,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from decimal import Decimal
import enum

from .base_and_users import Base


# ============================================================================
# Enums
# ============================================================================

class SubscriptionPlan(str, enum.Enum):
    """Subscription plan types"""
    FREE = "free"
    PRO = "pro"


class SubscriptionStatus(str, enum.Enum):
    """Stripe subscription status"""
    ACTIVE = "active"
    TRIALING = "trialing"
    PAST_DUE = "past_due"
    CANCELLED = "cancelled"
    UNPAID = "unpaid"


class PaymentStatus(str, enum.Enum):
    """Payment status"""
    PENDING = "pending"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    REFUNDED = "refunded"


# ============================================================================
# Subscription Models
# ============================================================================

class Subscription(Base):
    """
    User subscriptions (Stripe)
    
    Tracks premium subscriptions, trial periods, and billing cycles.
    """
    
    __tablename__ = "subscriptions"
    
    # Primary Key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    
    # Foreign Key
    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,  # One subscription per user
        index=True
    )
    
    # Stripe Information
    stripe_subscription_id: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        unique=True,
        index=True,
        comment="Stripe subscription ID (sub_...)"
    )
    stripe_customer_id: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True,
        comment="Stripe customer ID (cus_...)"
    )
    stripe_price_id: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        comment="Stripe price ID (price_...)"
    )
    
    # Plan Details
    plan: Mapped[str] = mapped_column(
        SQLEnum(SubscriptionPlan),
        nullable=False,
        default=SubscriptionPlan.FREE,
        index=True
    )
    status: Mapped[str] = mapped_column(
        SQLEnum(SubscriptionStatus),
        nullable=False,
        default=SubscriptionStatus.ACTIVE,
        index=True
    )
    
    # Pricing
    price_monthly: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        nullable=False,
        default=Decimal("0"),
        comment="Monthly price in USD"
    )
    currency: Mapped[str] = mapped_column(
        String(3),
        nullable=False,
        default="USD",
        comment="ISO 4217 currency code"
    )
    
    # Billing Cycle
    billing_cycle_start: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        comment="Current billing period start"
    )
    billing_cycle_end: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        index=True,
        comment="Current billing period end"
    )
    
    # Trial
    trial_start: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        nullable=True
    )
    trial_end: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        nullable=True,
        index=True
    )
    
    # Cancellation
    cancel_at_period_end: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        comment="Whether subscription cancels at end of current period"
    )
    cancelled_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        nullable=True,
        index=True
    )
    cancellation_reason: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True
    )
    cancellation_feedback: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True
    )
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        server_default=func.now(),
        onupdate=func.now()
    )
    
    # Relationships
    user = relationship("User", back_populates="subscriptions")
    payments = relationship("SubscriptionPayment", back_populates="subscription", lazy="select")
    
    # Indexes
    __table_args__ = (
        Index("idx_subscription_user", "user_id"),
        Index("idx_subscription_stripe", "stripe_subscription_id"),
        Index("idx_subscription_plan_status", "plan", "status"),
        Index("idx_subscription_billing_end", "billing_cycle_end"),
    )
    
    def __repr__(self) -> str:
        return f"<Subscription(id={self.id}, user_id={self.user_id}, plan='{self.plan}', status='{self.status}')>"
    
    @property
    def is_active(self) -> bool:
        """Check if subscription is active"""
        return self.status in [SubscriptionStatus.ACTIVE, SubscriptionStatus.TRIALING]
    
    @property
    def is_trial(self) -> bool:
        """Check if in trial period"""
        return self.status == SubscriptionStatus.TRIALING
    
    @property
    def is_cancelled(self) -> bool:
        """Check if subscription is cancelled"""
        return self.status == SubscriptionStatus.CANCELLED
    
    @property
    def days_until_renewal(self) -> int:
        """Calculate days until next renewal"""
        delta = self.billing_cycle_end - datetime.utcnow()
        return max(0, delta.days)
    
    @property
    def days_in_trial(self) -> Optional[int]:
        """Calculate days remaining in trial"""
        if not self.trial_end:
            return None
        delta = self.trial_end - datetime.utcnow()
        return max(0, delta.days)


class SubscriptionPayment(Base):
    """
    Subscription payment history
    
    Tracks individual payment attempts and outcomes for subscriptions.
    """
    
    __tablename__ = "subscription_payments"
    
    # Primary Key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    
    # Foreign Key
    subscription_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("subscriptions.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # Stripe Information
    stripe_invoice_id: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        unique=True,
        index=True,
        comment="Stripe invoice ID (in_...)"
    )
    stripe_payment_intent_id: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        unique=True,
        index=True,
        comment="Stripe payment intent ID (pi_...)"
    )
    stripe_charge_id: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        unique=True,
        index=True,
        comment="Stripe charge ID (ch_...)"
    )
    
    # Payment Details
    amount: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        nullable=False,
        comment="Payment amount"
    )
    currency: Mapped[str] = mapped_column(
        String(3),
        nullable=False,
        default="USD"
    )
    
    # Status
    status: Mapped[str] = mapped_column(
        SQLEnum(PaymentStatus),
        nullable=False,
        default=PaymentStatus.PENDING,
        index=True
    )
    
    # Billing Period
    period_start: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        comment="Billing period start"
    )
    period_end: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        comment="Billing period end"
    )
    
    # Payment Method
    payment_method_type: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        comment="'card', 'bank_account', etc."
    )
    payment_method_last4: Mapped[Optional[str]] = mapped_column(
        String(4),
        nullable=True,
        comment="Last 4 digits of payment method"
    )
    
    # Failure Information
    failure_code: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True
    )
    failure_message: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True
    )
    
    # Refund Information
    refunded_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        nullable=True
    )
    refund_amount: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(10, 2),
        nullable=True
    )
    refund_reason: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True
    )
    
    # Timestamps
    paid_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        nullable=True,
        index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        server_default=func.now(),
        index=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        server_default=func.now(),
        onupdate=func.now()
    )
    
    # Relationships
    subscription = relationship("Subscription", back_populates="payments")
    
    # Indexes
    __table_args__ = (
        Index("idx_payment_subscription", "subscription_id", "status"),
        Index("idx_payment_created", "created_at"),
        Index("idx_payment_paid", "paid_at"),
    )
    
    def __repr__(self) -> str:
        return f"<SubscriptionPayment(id={self.id}, amount={self.amount}, status='{self.status}')>"
    
    @property
    def is_paid(self) -> bool:
        """Check if payment succeeded"""
        return self.status == PaymentStatus.SUCCEEDED
    
    @property
    def is_failed(self) -> bool:
        """Check if payment failed"""
        return self.status == PaymentStatus.FAILED
    
    @property
    def is_refunded(self) -> bool:
        """Check if payment was refunded"""
        return self.status == PaymentStatus.REFUNDED
    
    @property
    def net_amount(self) -> Decimal:
        """Calculate net amount after refunds"""
        if self.refund_amount:
            return self.amount - self.refund_amount
        return self.amount


# ============================================================================
# Usage Example
# ============================================================================

if __name__ == "__main__":
    from sqlalchemy import create_engine
    from .base_and_users import Base
    
    DATABASE_URL = "mysql+pymysql://user:password@localhost:3306/anvil"
    engine = create_engine(DATABASE_URL)
    
    # Create all tables
    Base.metadata.create_all(engine)
    
    print("✅ Subscription and Payment tables created successfully!")
    print("\nTables created:")
    print("- subscriptions")
    print("- subscription_payments")
