"""
Notification data value object.
"""

from typing import Dict, Any
from app.domain.value_objects.base import ValueObject


class NotificationData(ValueObject[Dict[str, Any]]):
    """Notification data value object."""
