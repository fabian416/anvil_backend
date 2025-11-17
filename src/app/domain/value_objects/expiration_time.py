"""
Expiration time value object.
"""

from datetime import datetime
from app.domain.value_objects.base import ValueObject


class ExpirationTime(ValueObject[datetime]):
    """Expiration time value object."""
