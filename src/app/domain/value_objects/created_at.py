"""
Created at timestamp value object.
"""

from dataclasses import dataclass
from datetime import datetime

from app.domain.value_objects.base import ValueObject


@dataclass(frozen=True, repr=False)
class CreatedAt(ValueObject[datetime]):
    """Created at timestamp value object."""
    value: datetime
