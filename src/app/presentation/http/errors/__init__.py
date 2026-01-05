"""
Error handling system for Anvil Backend API.

This module provides a comprehensive error handling system following CTO methodology:
- Problem Decomposition: Organized by error types and layers
- Solution Generation: Unified error response format with i18n support
- Risk Assessment: Comprehensive coverage with fallback handlers

Architecture:
    ┌─────────────────────────────────────────────────────────────┐
    │                    Error Handling Layers                     │
    └─────────────────────────────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
        ▼                     ▼                     ▼
    ┌─────────┐         ┌─────────┐         ┌─────────┐
    │ Domain  │         │Application│      │Infrastructure│
    │ Errors  │         │  Errors  │       │   Errors    │
    └─────────┘         └─────────┘       └─────────┘
        │                     │                     │
        └─────────────────────┼─────────────────────┘
                              │
                              ▼
                    ┌─────────────────┐
                    │ Error Handlers  │
                    │  (Global + Route)│
                    └─────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
        ▼                     ▼                     ▼
    ┌─────────┐         ┌─────────┐         ┌─────────┐
    │Translators│      │Callbacks│      │Error Codes│
    │(i18n)    │      │(logging)│      │(standard) │
    └─────────┘         └─────────┘       └─────────┘
                              │
                              ▼
                    ┌─────────────────┐
                    │  API Response   │
                    │  (Standardized) │
                    └─────────────────┘

Usage:
    # In route handlers (using fastapi-error-map):
    from fastapi_error_map import ErrorAwareRouter, rule
    from app.presentation.http.errors.translators import ServiceUnavailableTranslator
    from app.presentation.http.errors.callbacks import log_error

    router = ErrorAwareRouter()

    @router.post(
        "/endpoint",
        error_map={
            DataMapperError: rule(
                status=503,
                translator=ServiceUnavailableTranslator(),
                on_error=log_error,
            ),
        },
    )
    async def endpoint(...):
        ...

    # In application layer (raising ApplicationError):
    from app.domain.exceptions.base import ApplicationError
    from app.domain.exceptions.error_codes import ErrorCode

    raise ApplicationError(
        error_code=ErrorCode.USER_NOT_FOUND,
        details={"user_id": user_id},
    )

    # In domain layer (raising DomainError):
    from app.domain.exceptions.user import UserNotFoundByEmailError
    raise UserNotFoundByEmailError(email=email)
"""

from app.presentation.http.errors.callbacks import log_error, log_info
from app.presentation.http.errors.handlers import (
    application_error_handler,
    authentication_error_handler,
    authorization_error_handler,
    create_error_response,
    domain_error_handler,
    domain_field_error_handler,
    http_exception_handler,
    register_exception_handlers,
    unhandled_exception_handler,
    validation_error_handler,
)
from app.presentation.http.errors.translators import (
    BadRequestTranslator,
    ConflictTranslator,
    ForbiddenTranslator,
    NotFoundErrorTranslator,
    NotFoundTranslator,
    ServiceUnavailableTranslator,
    StandardizedErrorTranslator,
    UnauthorizedTranslator,
    ValidationErrorTranslator,
)

__all__ = [
    # Handlers
    "register_exception_handlers",
    "application_error_handler",
    "domain_error_handler",
    "domain_field_error_handler",
    "authentication_error_handler",
    "authorization_error_handler",
    "validation_error_handler",
    "http_exception_handler",
    "unhandled_exception_handler",
    "create_error_response",
    # Translators
    "BadRequestTranslator",
    "NotFoundTranslator",
    "NotFoundErrorTranslator",
    "ServiceUnavailableTranslator",
    "ValidationErrorTranslator",
    "StandardizedErrorTranslator",
    "ConflictTranslator",
    "UnauthorizedTranslator",
    "ForbiddenTranslator",
    # Callbacks
    "log_error",
    "log_info",
]
