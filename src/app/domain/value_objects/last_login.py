"""
Last login value object.
"""

from dataclasses import dataclass
from datetime import datetime

from app.domain.value_objects.base import ValueObject


@dataclass(frozen=True, repr=False)
class LastLogin(ValueObject[datetime]):
    """Last login value object."""
    value: datetime
