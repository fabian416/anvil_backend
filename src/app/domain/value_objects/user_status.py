"""
User status value objects.
"""

from dataclasses import dataclass

from app.domain.value_objects.base import ValueObject


@dataclass(frozen=True, repr=False)
class UserActive(ValueObject[bool]):
    """User active status value object."""
    value: bool


@dataclass(frozen=True, repr=False)
class UserBlocked(ValueObject[bool]):
    """User blocked status value object."""
    value: bool


@dataclass(frozen=True, repr=False)
class UserVerified(ValueObject[bool]):
    """User verified status value object."""
    value: bool
