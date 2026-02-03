"""
Distillation reason value objects.

Represents the various reasons for distillation decisions.
"""

from enum import Enum


class DistillationReason(str, Enum):
    """
    Reasons for distillation validation decisions.

    These represent the various outcomes of the distillation
    validation process.
    """

    # Success reasons
    VALIDATION_PASSED = "validation_passed"
    """Request passed all validation checks."""

    # Failure reasons
    OUT_OF_SCOPE = "out_of_scope"
    """Request is not related to DeFi/trading/analytics."""

    MALICIOUS = "malicious"
    """Request appears to be a prompt injection or malicious attempt."""

    UNCLEAR_INTENT = "unclear_intent"
    """Request intent is unclear or too vague to process."""

    RATE_LIMITED = "rate_limited"
    """User has exceeded rate limits."""

    SYSTEM_ERROR = "system_error"
    """Distillation system encountered an error."""

    def is_success(self) -> bool:
        """Check if reason indicates success."""
        return self == DistillationReason.VALIDATION_PASSED

    def is_security_issue(self) -> bool:
        """Check if reason indicates a security issue."""
        return self == DistillationReason.MALICIOUS

    def is_user_error(self) -> bool:
        """Check if reason indicates a user error."""
        return self in {
            DistillationReason.OUT_OF_SCOPE,
            DistillationReason.UNCLEAR_INTENT,
        }
