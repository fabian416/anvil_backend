"""
Address value object.
"""

from dataclasses import dataclass

from app.domain.value_objects.base import ValueObject


@dataclass(frozen=True, repr=False)
class Address(ValueObject[str]):
    """Address value object."""
    value: str
