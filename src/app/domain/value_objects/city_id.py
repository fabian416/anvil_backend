"""
City ID value object.
"""

from dataclasses import dataclass

from app.domain.value_objects.base import ValueObject


@dataclass(frozen=True, repr=False)
class CityId(ValueObject[int]):
    """City ID value object."""
    value: int
