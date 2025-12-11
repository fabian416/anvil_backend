"""
Alert-specific domain exceptions with standardized error codes.

This module provides all exceptions related to:
- Price and market alerts
- Alert conditions and thresholds
- Notification preferences
"""

from typing import Any
from uuid import UUID

from app.domain.exceptions.base import ApplicationError
from app.domain.exceptions.error_codes import ErrorCode


class AlertNotFoundError(ApplicationError):
    """Raised when an alert is not found."""

    def __init__(
        self,
        alert_id: str | UUID | None = None,
        user_id: str | UUID | None = None,
    ) -> None:
        details = {}
        if alert_id:
            details["alert_id"] = str(alert_id)
        if user_id:
            details["user_id"] = str(user_id)
        super().__init__(ErrorCode.ALRT_NOT_FOUND, details=details)


class AlertAlreadyExistsError(ApplicationError):
    """Raised when an alert already exists for the same condition."""

    def __init__(
        self,
        existing_alert_id: str | UUID | None = None,
        asset: str | None = None,
        condition: str | None = None,
    ) -> None:
        details = {}
        if existing_alert_id:
            details["existing_alert_id"] = str(existing_alert_id)
        if asset:
            details["asset"] = asset
        if condition:
            details["condition"] = condition
        super().__init__(ErrorCode.ALRT_ALREADY_EXISTS, details=details)


class InvalidThresholdError(ApplicationError):
    """Raised when an alert threshold value is invalid."""

    def __init__(
        self,
        threshold: float | str | None = None,
        min_value: float | None = None,
        max_value: float | None = None,
        reason: str | None = None,
    ) -> None:
        details = {}
        if threshold is not None:
            details["threshold"] = str(threshold)
        if min_value is not None:
            details["min_value"] = min_value
        if max_value is not None:
            details["max_value"] = max_value
        if reason:
            details["reason"] = reason
        super().__init__(ErrorCode.ALRT_INVALID_THRESHOLD, details=details, field="threshold")


class InvalidAlertConditionError(ApplicationError):
    """Raised when an alert condition is invalid."""

    def __init__(
        self,
        condition: str | None = None,
        valid_conditions: list[str] | None = None,
        reason: str | None = None,
    ) -> None:
        details = {}
        if condition:
            details["condition"] = condition
        if valid_conditions:
            details["valid_conditions"] = valid_conditions
        if reason:
            details["reason"] = reason
        super().__init__(ErrorCode.ALRT_INVALID_CONDITION, details=details, field="condition")


class AlertLimitExceededError(ApplicationError):
    """Raised when user has reached maximum alert limit."""

    def __init__(
        self,
        current_count: int | None = None,
        max_allowed: int | None = None,
        subscription_tier: str | None = None,
    ) -> None:
        details = {}
        if current_count is not None:
            details["current_count"] = current_count
        if max_allowed is not None:
            details["max_allowed"] = max_allowed
        if subscription_tier:
            details["subscription_tier"] = subscription_tier
        super().__init__(ErrorCode.ALRT_LIMIT_EXCEEDED, details=details)


# Additional alert-specific exceptions

class AlertDisabledError(ApplicationError):
    """Raised when trying to modify a disabled alert."""

    def __init__(
        self,
        alert_id: str | UUID | None = None,
        disabled_at: str | None = None,
    ) -> None:
        details = {}
        if alert_id:
            details["alert_id"] = str(alert_id)
        if disabled_at:
            details["disabled_at"] = disabled_at
        super().__init__(
            ErrorCode.ALRT_NOT_FOUND,
            details=details,
            override_message="Alert is disabled",
        )


class AlertExpiredError(ApplicationError):
    """Raised when an alert has expired."""

    def __init__(
        self,
        alert_id: str | UUID | None = None,
        expired_at: str | None = None,
    ) -> None:
        details = {}
        if alert_id:
            details["alert_id"] = str(alert_id)
        if expired_at:
            details["expired_at"] = expired_at
        super().__init__(
            ErrorCode.ALRT_NOT_FOUND,
            details=details,
            override_message="Alert has expired",
        )


class AlertTriggerError(ApplicationError):
    """Raised when an alert fails to trigger."""

    def __init__(
        self,
        alert_id: str | UUID | None = None,
        reason: str | None = None,
    ) -> None:
        details = {}
        if alert_id:
            details["alert_id"] = str(alert_id)
        if reason:
            details["reason"] = reason
        super().__init__(
            ErrorCode.ALRT_INVALID_CONDITION,
            details=details,
            override_message="Alert failed to trigger",
        )


class InvalidAlertTypeError(ApplicationError):
    """Raised when an invalid alert type is specified."""

    def __init__(
        self,
        alert_type: str | None = None,
        valid_types: list[str] | None = None,
    ) -> None:
        details = {}
        if alert_type:
            details["alert_type"] = alert_type
        if valid_types:
            details["valid_types"] = valid_types
        super().__init__(
            ErrorCode.ALRT_INVALID_CONDITION,
            details=details,
            field="alert_type",
            override_message="Invalid alert type",
        )


class AlertNotificationFailedError(ApplicationError):
    """Raised when alert notification fails to send."""

    def __init__(
        self,
        alert_id: str | UUID | None = None,
        channel: str | None = None,
        reason: str | None = None,
    ) -> None:
        details = {}
        if alert_id:
            details["alert_id"] = str(alert_id)
        if channel:
            details["channel"] = channel
        if reason:
            details["reason"] = reason
        super().__init__(
            ErrorCode.ALRT_INVALID_CONDITION,
            details=details,
            override_message="Failed to send alert notification",
        )


class InvalidAlertFrequencyError(ApplicationError):
    """Raised when an invalid alert frequency is specified."""

    def __init__(
        self,
        frequency: str | None = None,
        valid_frequencies: list[str] | None = None,
    ) -> None:
        details = {}
        if frequency:
            details["frequency"] = frequency
        if valid_frequencies:
            details["valid_frequencies"] = valid_frequencies
        super().__init__(
            ErrorCode.ALRT_INVALID_CONDITION,
            details=details,
            field="frequency",
            override_message="Invalid alert frequency",
        )


class AlertCooldownError(ApplicationError):
    """Raised when alert is in cooldown period."""

    def __init__(
        self,
        alert_id: str | UUID | None = None,
        cooldown_remaining_seconds: int | None = None,
    ) -> None:
        details = {}
        if alert_id:
            details["alert_id"] = str(alert_id)
        if cooldown_remaining_seconds is not None:
            details["cooldown_remaining_seconds"] = cooldown_remaining_seconds
        super().__init__(
            ErrorCode.ALRT_ALREADY_EXISTS,
            details=details,
            override_message="Alert is in cooldown period",
        )
