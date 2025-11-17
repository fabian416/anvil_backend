"""
Postal code value object.
"""

from dataclasses import dataclass

from app.domain.exceptions.base import DomainFieldError
from app.domain.value_objects.base import ValueObject


@dataclass(frozen=True, repr=False)
class PostalCode(ValueObject[str]):
    """
    Postal code value object with validation.
    Based on infrastructure layer constraints: 20 chars max, optional.
    """
    
    value: str
    
    def __post_init__(self) -> None:
        """
        :raises DomainFieldError:
        """
        super().__post_init__()
        self._validate_length()
        self._validate_format()
    
    def _validate_length(self) -> None:
        """Validate postal code length based on database constraints."""
        if len(self.value) > 20:
            raise DomainFieldError("Postal code must not exceed 20 characters.")
    
    def _validate_format(self) -> None:
        """Validate postal code format (alphanumeric with spaces and hyphens)."""
        # Allow letters, digits, spaces, and hyphens for various postal code formats
        if not all(c.isalnum() or c in ' -' for c in self.value):
            raise DomainFieldError("Postal code must contain only letters, digits, spaces, and hyphens.")
