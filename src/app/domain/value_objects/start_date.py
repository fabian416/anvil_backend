"""
Start date value object.
"""

from datetime import datetime
from app.domain.value_objects.base import ValueObject


class StartDate(ValueObject[datetime]):
    """Start date value object."""
