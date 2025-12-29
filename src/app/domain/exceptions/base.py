from typing import Any
from app.domain.exceptions.error_codes import ErrorCode


class ApplicationError(Exception):
    """
    Base exception for application-layer errors with standardized error codes.

    These exceptions have proper HTTP status code mappings and i18n support.
    They are caught by global exception handlers and converted to API responses.
    """

    def __init__(
        self,
        error_code: ErrorCode,
        details: dict[str, Any] | None = None,
        field: str | None = None,
    ):
        self.error_code = error_code
        self.definition = error_code.value
        self.code = self.definition.code
        self.message = self.definition.default_message
        self.i18n_key = self.definition.i18n_key
        self.http_status = self.definition.http_status
        self.details = details or {}
        self.field = field
        super().__init__(self.message)

    def to_dict(self) -> dict[str, Any]:
        """Convert to API response format."""
        return self.definition.to_dict(details=self.details, field=self.field)


class DomainError(Exception):
    """
    Exception for violations of fundamental domain rules, such as attempts to change
    the immutable `id` of an Entity, as well as for complex business rule violations.

    Not for:
    - Single attribute validation (use `DomainFieldError` instead).
    - Application, infrastructure, or system errors.
    """


class DomainFieldError(DomainError):
    """
    Exception for validation errors in Value Objects and Entity field values.

    Use cases:
    1. Violations of Value Object invariants during creation.
    2. Single-field validation errors in Entities.

    Not for:
    - Complex business rule violations (use `DomainError` instead).
    - Input validation at application boundaries.
    """
