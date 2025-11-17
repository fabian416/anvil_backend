"""
Payment method value object.
"""

from app.domain.value_objects.base import ValueObject


class PaymentMethod(ValueObject[str]):
    """Payment method value object."""
