"""
First name value object.
"""

from dataclasses import dataclass

from app.domain.exceptions.base import DomainFieldError
from app.domain.value_objects.base import ValueObject


@dataclass(frozen=True, repr=False)
class FirstName(ValueObject[str]):
    """
    First name value object with validation.
    Based on infrastructure layer constraints: 100 chars max, required.
    """
    
    value: str
    
    def __post_init__(self) -> None:
        """
        :raises DomainFieldError:
        """
        super().__post_init__()
        self._validate_length()
        self._validate_not_empty()
    
    def _validate_length(self) -> None:
        """Validate first name length based on database constraints."""
        if len(self.value) > 100:
            raise DomainFieldError("First name must not exceed 100 characters.")
    
    def _validate_not_empty(self) -> None:
        """Validate first name is not empty."""
        if not self.value.strip():
            raise DomainFieldError("First name cannot be empty.")
