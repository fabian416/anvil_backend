"""
Read status value object.
"""

from app.domain.value_objects.base import ValueObject


class ReadStatus(ValueObject[bool]):
    """Read status value object."""
