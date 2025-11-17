"""
Profile picture value object.
"""

from dataclasses import dataclass

from app.domain.value_objects.base import ValueObject


@dataclass(frozen=True, repr=False)
class ProfilePicture(ValueObject[str]):
    """Profile picture value object."""
    value: str
