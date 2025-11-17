"""
Stripe subscription ID value object.
"""

from app.domain.value_objects.base import ValueObject


class StripeSubscriptionId(ValueObject[str]):
    """Stripe subscription ID value object."""
