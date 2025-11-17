"""
Currency value object.
"""

from app.domain.value_objects.base import ValueObject


class Currency(ValueObject[str]):
    """Currency value object."""
