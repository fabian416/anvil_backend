"""
Phone number value object.
"""

import re
from dataclasses import dataclass

from app.domain.exceptions.base import DomainFieldError
from app.domain.value_objects.base import ValueObject


@dataclass(frozen=True, repr=False)
class PhoneNumber(ValueObject[str]):
    """
    Phone number value object with validation.
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
        """Validate phone number length based on database constraints."""
        if len(self.value) > 20:
            raise DomainFieldError("Phone number must not exceed 20 characters.")
    
    def _validate_format(self) -> None:
        """Validate phone number format (basic international format)."""
        # Allow digits, +, -, spaces, parentheses
        phone_pattern = re.compile(r'^[\+]?[0-9\s\-\(\)]{7,20}$')
        if not phone_pattern.match(self.value):
            raise DomainFieldError("Invalid phone number format.")
