"""
Retry count value object.
"""

from dataclasses import dataclass

from app.domain.value_objects.base import ValueObject


@dataclass(frozen=True, repr=False)
class RetryCount(ValueObject[int]):
    """Retry count value object."""
    value: int
