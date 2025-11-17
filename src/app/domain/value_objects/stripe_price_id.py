"""
Stripe price ID value object.
"""

from app.domain.value_objects.base import ValueObject


class StripePriceId(ValueObject[str]):
    """Stripe price ID value object."""
