"""
Stripe product ID value object.
"""

from app.domain.value_objects.base import ValueObject


class StripeProductId(ValueObject[str]):
    """Stripe product ID value object."""
