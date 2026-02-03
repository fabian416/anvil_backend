"""
Value object for Privy User ID.
"""

from dataclasses import dataclass

from app.domain.value_objects.base import ValueObject


@dataclass(frozen=True, slots=True)
class PrivyUserId(ValueObject[str]):
    """
    Represents the unique identifier from Privy authentication provider.
    Format: did:privy:xxxxx or similar Privy-specific ID.
    """

    value: str

    def __post_init__(self) -> None:
        if self.value and len(self.value) > 255:
            raise ValueError("Privy user ID must be 255 characters or less")
