"""
Email value object.
"""

import re
from dataclasses import dataclass

from app.domain.exceptions.base import DomainFieldError
from app.domain.value_objects.base import ValueObject


@dataclass(frozen=True, repr=False)
class Email(ValueObject[str]):
    """
    Email value object with validation.
    Based on infrastructure layer constraints: 255 chars max, unique, indexed.
    """
    
    value: str
    
    def __post_init__(self) -> None:
        """
        :raises DomainFieldError:
        """
        super().__post_init__()
        self._validate_email_format()
        self._validate_email_length()
    
    def _validate_email_format(self) -> None:
        """Validate email format using regex."""
        email_pattern = re.compile(
            r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        )
        if not email_pattern.match(self.value):
            raise DomainFieldError("Invalid email format.")
    
    def _validate_email_length(self) -> None:
        """Validate email length based on database constraints."""
        if len(self.value) > 255:
            raise DomainFieldError("Email must not exceed 255 characters.")
        if len(self.value) < 5:  # Minimum reasonable email: a@b.c
            raise DomainFieldError("Email must be at least 5 characters.")
