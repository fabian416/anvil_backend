"""
Validation-specific domain exceptions with standardized error codes.

This module provides all exceptions related to:
- Field validation errors
- Format and type validation
- Range and constraint validation
"""

from typing import Any

from app.domain.exceptions.base import ApplicationError
from app.domain.exceptions.error_codes import ErrorCode


class RequiredFieldError(ApplicationError):
    """Raised when a required field is missing."""

    def __init__(
        self,
        field_name: str | None = None,
    ) -> None:
        details = {}
        if field_name:
            details["field"] = field_name
        super().__init__(ErrorCode.VAL_REQUIRED, details=details, field=field_name)


class MinLengthError(ApplicationError):
    """Raised when a value is below minimum length."""

    def __init__(
        self,
        field_name: str | None = None,
        min_length: int | None = None,
        actual_length: int | None = None,
    ) -> None:
        details = {}
        if field_name:
            details["field"] = field_name
        if min_length is not None:
            details["min"] = min_length
        if actual_length is not None:
            details["actual"] = actual_length
        super().__init__(ErrorCode.VAL_MIN_LENGTH, details=details, field=field_name)


class MaxLengthError(ApplicationError):
    """Raised when a value exceeds maximum length."""

    def __init__(
        self,
        field_name: str | None = None,
        max_length: int | None = None,
        actual_length: int | None = None,
    ) -> None:
        details = {}
        if field_name:
            details["field"] = field_name
        if max_length is not None:
            details["max"] = max_length
        if actual_length is not None:
            details["actual"] = actual_length
        super().__init__(ErrorCode.VAL_MAX_LENGTH, details=details, field=field_name)


class InvalidFormatError(ApplicationError):
    """Raised when a value has invalid format."""

    def __init__(
        self,
        field_name: str | None = None,
        expected_format: str | None = None,
        example: str | None = None,
    ) -> None:
        details = {}
        if field_name:
            details["field"] = field_name
        if expected_format:
            details["expected_format"] = expected_format
        if example:
            details["example"] = example
        super().__init__(ErrorCode.VAL_INVALID_FORMAT, details=details, field=field_name)


class InvalidEmailFormatError(ApplicationError):
    """Raised when an email has invalid format."""

    def __init__(
        self,
        email: str | None = None,
    ) -> None:
        details = {}
        if email:
            details["value"] = email
        super().__init__(ErrorCode.VAL_INVALID_EMAIL, details=details, field="email")


class InvalidUUIDError(ApplicationError):
    """Raised when a UUID has invalid format."""

    def __init__(
        self,
        field_name: str | None = None,
        value: str | None = None,
    ) -> None:
        details = {}
        if field_name:
            details["field"] = field_name
        if value:
            details["value"] = value
        super().__init__(ErrorCode.VAL_INVALID_UUID, details=details, field=field_name)


class InvalidDateError(ApplicationError):
    """Raised when a date has invalid format."""

    def __init__(
        self,
        field_name: str | None = None,
        value: str | None = None,
        expected_format: str | None = None,
    ) -> None:
        details = {}
        if field_name:
            details["field"] = field_name
        if value:
            details["value"] = value
        if expected_format:
            details["expected_format"] = expected_format
        super().__init__(ErrorCode.VAL_INVALID_DATE, details=details, field=field_name)


class OutOfRangeError(ApplicationError):
    """Raised when a value is outside valid range."""

    def __init__(
        self,
        field_name: str | None = None,
        value: float | int | None = None,
        min_value: float | int | None = None,
        max_value: float | int | None = None,
    ) -> None:
        details = {}
        if field_name:
            details["field"] = field_name
        if value is not None:
            details["value"] = value
        if min_value is not None:
            details["min"] = min_value
        if max_value is not None:
            details["max"] = max_value
        super().__init__(ErrorCode.VAL_OUT_OF_RANGE, details=details, field=field_name)


class InvalidEnumError(ApplicationError):
    """Raised when a value is not a valid enum option."""

    def __init__(
        self,
        field_name: str | None = None,
        value: str | None = None,
        valid_options: list[str] | None = None,
    ) -> None:
        details = {}
        if field_name:
            details["field"] = field_name
        if value:
            details["value"] = value
        if valid_options:
            details["valid_options"] = valid_options
        super().__init__(ErrorCode.VAL_INVALID_ENUM, details=details, field=field_name)


class ArrayTooLongError(ApplicationError):
    """Raised when an array has too many items."""

    def __init__(
        self,
        field_name: str | None = None,
        actual_count: int | None = None,
        max_count: int | None = None,
    ) -> None:
        details = {}
        if field_name:
            details["field"] = field_name
        if actual_count is not None:
            details["actual"] = actual_count
        if max_count is not None:
            details["max"] = max_count
        super().__init__(ErrorCode.VAL_ARRAY_TOO_LONG, details=details, field=field_name)


# Additional validation-specific exceptions

class InvalidPhoneNumberError(ApplicationError):
    """Raised when a phone number is invalid."""

    def __init__(
        self,
        value: str | None = None,
        country_code: str | None = None,
    ) -> None:
        details = {}
        if value:
            details["value"] = value
        if country_code:
            details["country_code"] = country_code
        super().__init__(
            ErrorCode.VAL_INVALID_FORMAT,
            details=details,
            field="phone",
            override_message="Invalid phone number format",
        )


class InvalidURLError(ApplicationError):
    """Raised when a URL is invalid."""

    def __init__(
        self,
        field_name: str | None = None,
        value: str | None = None,
    ) -> None:
        details = {}
        if field_name:
            details["field"] = field_name
        if value:
            details["value"] = value
        super().__init__(
            ErrorCode.VAL_INVALID_FORMAT,
            details=details,
            field=field_name,
            override_message="Invalid URL format",
        )


class InvalidJSONError(ApplicationError):
    """Raised when JSON is invalid."""

    def __init__(
        self,
        field_name: str | None = None,
        error_position: int | None = None,
    ) -> None:
        details = {}
        if field_name:
            details["field"] = field_name
        if error_position is not None:
            details["error_position"] = error_position
        super().__init__(
            ErrorCode.VAL_INVALID_FORMAT,
            details=details,
            field=field_name,
            override_message="Invalid JSON format",
        )


class InvalidCurrencyError(ApplicationError):
    """Raised when a currency code is invalid."""

    def __init__(
        self,
        value: str | None = None,
        valid_currencies: list[str] | None = None,
    ) -> None:
        details = {}
        if value:
            details["value"] = value
        if valid_currencies:
            details["valid_currencies"] = valid_currencies
        super().__init__(
            ErrorCode.VAL_INVALID_ENUM,
            details=details,
            field="currency",
            override_message="Invalid currency code",
        )


class InvalidTimezoneError(ApplicationError):
    """Raised when a timezone is invalid."""

    def __init__(
        self,
        value: str | None = None,
    ) -> None:
        details = {}
        if value:
            details["value"] = value
        super().__init__(
            ErrorCode.VAL_INVALID_ENUM,
            details=details,
            field="timezone",
            override_message="Invalid timezone",
        )


class InvalidLocaleError(ApplicationError):
    """Raised when a locale is invalid."""

    def __init__(
        self,
        value: str | None = None,
        valid_locales: list[str] | None = None,
    ) -> None:
        details = {}
        if value:
            details["value"] = value
        if valid_locales:
            details["valid_locales"] = valid_locales
        super().__init__(
            ErrorCode.VAL_INVALID_ENUM,
            details=details,
            field="locale",
            override_message="Invalid locale",
        )


class DuplicateValueError(ApplicationError):
    """Raised when a unique constraint is violated."""

    def __init__(
        self,
        field_name: str | None = None,
        value: str | None = None,
    ) -> None:
        details = {}
        if field_name:
            details["field"] = field_name
        if value:
            details["value"] = value
        super().__init__(
            ErrorCode.VAL_INVALID_FORMAT,
            details=details,
            field=field_name,
            override_message="Value already exists",
        )


class InvalidRegexError(ApplicationError):
    """Raised when a value doesn't match required pattern."""

    def __init__(
        self,
        field_name: str | None = None,
        pattern: str | None = None,
        value: str | None = None,
    ) -> None:
        details = {}
        if field_name:
            details["field"] = field_name
        if pattern:
            details["pattern"] = pattern
        if value:
            details["value"] = value
        super().__init__(
            ErrorCode.VAL_INVALID_FORMAT,
            details=details,
            field=field_name,
            override_message="Value doesn't match required pattern",
        )
