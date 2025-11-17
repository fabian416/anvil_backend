"""
Language value object.
"""

from dataclasses import dataclass

from app.domain.exceptions.base import DomainFieldError
from app.domain.value_objects.base import ValueObject


@dataclass(frozen=True, repr=False)
class Language(ValueObject[str]):
    """
    Language value object with validation.
    Based on infrastructure layer constraints: 10 chars max, default "en".
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
        """Validate language code length based on database constraints."""
        if len(self.value) > 10:
            raise DomainFieldError("Language code must not exceed 10 characters.")
        if len(self.value) < 2:
            raise DomainFieldError("Language code must be at least 2 characters.")
    
    def _validate_format(self) -> None:
        """Validate language code format (ISO 639-1 or similar)."""
        # Allow letters and hyphens for language codes like "en", "en-US", "zh-CN"
        if not self.value.replace('-', '').replace('_', '').isalpha():
            raise DomainFieldError("Language code must contain only letters, hyphens, and underscores.")
