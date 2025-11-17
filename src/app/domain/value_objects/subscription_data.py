"""
Subscription data value object.
"""

from typing import Dict, Any
from app.domain.value_objects.base import ValueObject


class SubscriptionData(ValueObject[Dict[str, Any]]):
    """Subscription data value object."""
