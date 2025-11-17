"""
Country ID value object.
"""

from dataclasses import dataclass

from app.domain.value_objects.base import ValueObject


@dataclass(frozen=True, repr=False)
class CountryId(ValueObject[int]):
    """Country ID value object."""
    value: int
