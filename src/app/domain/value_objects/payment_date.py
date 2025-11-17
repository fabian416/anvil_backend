"""
Payment date value object.
"""

from datetime import datetime
from app.domain.value_objects.base import ValueObject


class PaymentDate(ValueObject[datetime]):
    """Payment date value object."""
