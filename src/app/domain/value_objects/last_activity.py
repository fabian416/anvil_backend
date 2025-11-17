"""
Last activity timestamp value object.
"""

from datetime import datetime
from app.domain.value_objects.base import ValueObject


class LastActivity(ValueObject[datetime]):
    """Last activity timestamp value object."""
