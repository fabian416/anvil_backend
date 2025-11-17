"""
Stripe payment intent ID value object.
"""

from app.domain.value_objects.base import ValueObject


class StripePaymentIntentId(ValueObject[str]):
    """Stripe payment intent ID value object."""
