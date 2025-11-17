"""
Verification token value object.
"""

from app.domain.value_objects.base import ValueObject


class VerificationToken(ValueObject[str]):
    """Verification token value object."""
