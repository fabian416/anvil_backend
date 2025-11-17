"""
End date value object.
"""

from datetime import datetime
from app.domain.value_objects.base import ValueObject


class EndDate(ValueObject[datetime]):
    """End date value object."""
