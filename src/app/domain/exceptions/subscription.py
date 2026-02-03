"""
Subscription-specific domain exceptions with standardized error codes.

This module provides all exceptions related to:
- Subscription plans and tiers
- Payment processing
- Subscription lifecycle
"""

from typing import Any
from uuid import UUID

from app.domain.exceptions.base import ApplicationError
from app.domain.exceptions.error_codes import ErrorCode


class SubscriptionNotFoundError(ApplicationError):
    """Raised when a subscription is not found."""

    def __init__(
        self,
        subscription_id: str | UUID | None = None,
        user_id: str | UUID | None = None,
    ) -> None:
        details = {}
        if subscription_id:
            details["subscription_id"] = str(subscription_id)
        if user_id:
            details["user_id"] = str(user_id)
        super().__init__(ErrorCode.SUB_NOT_FOUND, details=details)


class SubscriptionAlreadyActiveError(ApplicationError):
    """Raised when user already has an active subscription."""

    def __init__(
        self,
        current_plan: str | None = None,
        expires_at: str | None = None,
    ) -> None:
        details = {}
        if current_plan:
            details["current_plan"] = current_plan
        if expires_at:
            details["expires_at"] = expires_at
        super().__init__(ErrorCode.SUB_ALREADY_ACTIVE, details=details)


class PaymentFailedError(ApplicationError):
    """Raised when payment processing fails."""

    def __init__(
        self,
        reason: str | None = None,
        payment_method: str | None = None,
        error_code: str | None = None,
    ) -> None:
        details = {}
        if reason:
            details["reason"] = reason
        if payment_method:
            details["payment_method"] = payment_method
        if error_code:
            details["payment_error_code"] = error_code
        super().__init__(ErrorCode.SUB_PAYMENT_FAILED, details=details)


class InvalidPlanError(ApplicationError):
    """Raised when an invalid subscription plan is specified."""

    def __init__(
        self,
        plan_id: str | None = None,
        valid_plans: list[str] | None = None,
    ) -> None:
        details = {}
        if plan_id:
            details["plan_id"] = plan_id
        if valid_plans:
            details["valid_plans"] = valid_plans
        super().__init__(ErrorCode.SUB_INVALID_PLAN, details=details, field="plan_id")


class SubscriptionCancelFailedError(ApplicationError):
    """Raised when subscription cancellation fails."""

    def __init__(
        self,
        subscription_id: str | UUID | None = None,
        reason: str | None = None,
    ) -> None:
        details = {}
        if subscription_id:
            details["subscription_id"] = str(subscription_id)
        if reason:
            details["reason"] = reason
        super().__init__(ErrorCode.SUB_CANCEL_FAILED, details=details)


class FeatureUnavailableError(ApplicationError):
    """Raised when a feature requires a premium subscription."""

    def __init__(
        self,
        feature: str | None = None,
        required_plan: str | None = None,
        current_plan: str | None = None,
    ) -> None:
        details = {}
        if feature:
            details["feature"] = feature
        if required_plan:
            details["required_plan"] = required_plan
        if current_plan:
            details["current_plan"] = current_plan
        super().__init__(ErrorCode.SUB_FEATURE_UNAVAILABLE, details=details)


class InvalidCardError(ApplicationError):
    """Raised when payment card is invalid."""

    def __init__(
        self,
        reason: str | None = None,
        card_last_four: str | None = None,
    ) -> None:
        details = {}
        if reason:
            details["reason"] = reason
        if card_last_four:
            details["card_last_four"] = card_last_four
        super().__init__(ErrorCode.SUB_INVALID_CARD, details=details, field="card")


# Additional subscription-specific exceptions


class SubscriptionExpiredError(ApplicationError):
    """Raised when subscription has expired."""

    def __init__(
        self,
        subscription_id: str | UUID | None = None,
        expired_at: str | None = None,
    ) -> None:
        details = {}
        if subscription_id:
            details["subscription_id"] = str(subscription_id)
        if expired_at:
            details["expired_at"] = expired_at
        super().__init__(
            ErrorCode.SUB_NOT_FOUND,
            details=details,
            override_message="Subscription has expired",
        )


class SubscriptionSuspendedError(ApplicationError):
    """Raised when subscription is suspended."""

    def __init__(
        self,
        subscription_id: str | UUID | None = None,
        reason: str | None = None,
        suspended_at: str | None = None,
    ) -> None:
        details = {}
        if subscription_id:
            details["subscription_id"] = str(subscription_id)
        if reason:
            details["reason"] = reason
        if suspended_at:
            details["suspended_at"] = suspended_at
        super().__init__(
            ErrorCode.SUB_NOT_FOUND,
            details=details,
            override_message="Subscription is suspended",
        )


class DowngradeNotAllowedError(ApplicationError):
    """Raised when subscription downgrade is not allowed."""

    def __init__(
        self,
        current_plan: str | None = None,
        target_plan: str | None = None,
        reason: str | None = None,
    ) -> None:
        details = {}
        if current_plan:
            details["current_plan"] = current_plan
        if target_plan:
            details["target_plan"] = target_plan
        if reason:
            details["reason"] = reason
        super().__init__(
            ErrorCode.SUB_INVALID_PLAN,
            details=details,
            override_message="Subscription downgrade not allowed",
        )


class TrialAlreadyUsedError(ApplicationError):
    """Raised when user has already used trial."""

    def __init__(
        self,
        trial_used_at: str | None = None,
    ) -> None:
        details = {}
        if trial_used_at:
            details["trial_used_at"] = trial_used_at
        super().__init__(
            ErrorCode.SUB_ALREADY_ACTIVE,
            details=details,
            override_message="Free trial has already been used",
        )


class PaymentMethodRequiredError(ApplicationError):
    """Raised when payment method is required but not provided."""

    def __init__(self) -> None:
        super().__init__(
            ErrorCode.SUB_PAYMENT_FAILED,
            override_message="Payment method is required",
            field="payment_method",
        )


class RefundNotAllowedError(ApplicationError):
    """Raised when refund is not allowed."""

    def __init__(
        self,
        subscription_id: str | UUID | None = None,
        reason: str | None = None,
        days_since_purchase: int | None = None,
    ) -> None:
        details = {}
        if subscription_id:
            details["subscription_id"] = str(subscription_id)
        if reason:
            details["reason"] = reason
        if days_since_purchase is not None:
            details["days_since_purchase"] = days_since_purchase
        super().__init__(
            ErrorCode.SUB_CANCEL_FAILED,
            details=details,
            override_message="Refund is not allowed for this subscription",
        )


class BillingAddressRequiredError(ApplicationError):
    """Raised when billing address is required."""

    def __init__(self) -> None:
        super().__init__(
            ErrorCode.SUB_PAYMENT_FAILED,
            override_message="Billing address is required",
            field="billing_address",
        )


class CouponInvalidError(ApplicationError):
    """Raised when a coupon code is invalid."""

    def __init__(
        self,
        coupon_code: str | None = None,
        reason: str | None = None,
    ) -> None:
        details = {}
        if coupon_code:
            details["coupon_code"] = coupon_code
        if reason:
            details["reason"] = reason
        super().__init__(
            ErrorCode.SUB_INVALID_PLAN,
            details=details,
            field="coupon_code",
            override_message="Invalid or expired coupon code",
        )


class CouponAlreadyUsedError(ApplicationError):
    """Raised when coupon has already been used."""

    def __init__(
        self,
        coupon_code: str | None = None,
    ) -> None:
        details = {}
        if coupon_code:
            details["coupon_code"] = coupon_code
        super().__init__(
            ErrorCode.SUB_ALREADY_ACTIVE,
            details=details,
            field="coupon_code",
            override_message="Coupon has already been used",
        )
