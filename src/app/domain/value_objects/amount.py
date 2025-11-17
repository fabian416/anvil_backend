"""
Amount value object.
"""

from app.domain.value_objects.base import ValueObject


class Amount(ValueObject[float]):
    """Amount value object."""
