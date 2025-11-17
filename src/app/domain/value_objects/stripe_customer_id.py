"""
Stripe customer ID value object.
"""

from app.domain.value_objects.base import ValueObject


class StripeCustomerId(ValueObject[str]):
    """Stripe customer ID value object."""
