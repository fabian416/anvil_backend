"""
Payment data value object.
"""

from typing import Dict, Any
from app.domain.value_objects.base import ValueObject


class PaymentData(ValueObject[Dict[str, Any]]):
    """Payment data value object."""
