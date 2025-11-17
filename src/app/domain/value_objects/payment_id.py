"""
Payment ID value object.
"""

from app.domain.value_objects.base import ValueObject


class PaymentId(ValueObject[int]):
    """Payment ID value object."""
