"""
Global exception handlers for FastAPI application.

This module provides standardized error response handling for all exceptions,
ensuring consistent API responses with error codes, i18n keys, and proper HTTP status codes.

Usage:
    from app.presentation.http.errors.handlers import register_exception_handlers

    app = FastAPI()
    register_exception_handlers(app)
"""

import logging
from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.domain.exceptions.base import ApplicationError, DomainError, DomainFieldError
from app.domain.exceptions.error_codes import ErrorCode

logger = logging.getLogger(__name__)


def create_error_response(
    code: str,
    message: str,
    i18n_key: str,
    http_status: int,
    details: dict[str, Any] | None = None,
    field: str | None = None,
) -> dict[str, Any]:
    """
    Create a standardized error response dict.

    Returns:
        {
            "error": {
                "code": "AUTH_001",
                "message": "Invalid email or password",
                "i18n_key": "errors.auth.invalid_credentials",
                "http_status": 401,
                "details": {...},  // optional
                "field": "..."     // optional
            }
        }
    """
    error_data: dict[str, Any] = {
        "code": code,
        "message": message,
        "i18n_key": i18n_key,
        "http_status": http_status,
    }
    if details:
        error_data["details"] = details
    if field:
        error_data["field"] = field

    return {"error": error_data}


async def application_error_handler(
    request: Request,
    exc: ApplicationError,
) -> JSONResponse:
    """
    Handle all ApplicationError exceptions with standardized responses.

    These exceptions already have error codes and i18n keys defined.
    """
    logger.info(
        "ApplicationError: [%s] %s (path=%s)",
        exc.code,
        exc.message,
        request.url.path,
    )

    return JSONResponse(
        status_code=exc.http_status,
        content={"error": exc.to_dict()},
    )


async def domain_error_handler(
    request: Request,
    exc: DomainError,
) -> JSONResponse:
    """
    Handle legacy DomainError exceptions.

    These are mapped to SYS_001 (internal error) by default.
    Specific subclasses can be handled separately.
    """
    logger.warning(
        "DomainError: %s - %s (path=%s)",
        type(exc).__name__,
        str(exc),
        request.url.path,
    )

    # Map known domain errors to appropriate error codes
    error_code = _map_domain_error_to_code(exc)
    definition = error_code.value

    return JSONResponse(
        status_code=definition.http_status,
        content=create_error_response(
            code=definition.code,
            message=str(exc) if str(exc) else definition.default_message,
            i18n_key=definition.i18n_key,
            http_status=definition.http_status,
        ),
    )


def _map_domain_error_to_code(exc: DomainError) -> ErrorCode:
    """Map legacy DomainError subclasses to ErrorCode."""
    # Import here to avoid circular imports
    from app.domain.exceptions.auth import (
        InsufficientPermissionsError,
        InvalidAuthorizationHeaderError,
        RoleChangeNotAllowedError,
        UnauthorizedAccessError,
    )
    from app.domain.exceptions.user import (
        ActivationChangeNotPermittedError,
        EmailAlreadyExistsError,
        RoleAssignmentNotPermittedError,
        RoleChangeNotPermittedError,
        UserNotFoundByEmailError,
    )

    error_mapping: dict[type, ErrorCode] = {
        # Auth errors
        InvalidAuthorizationHeaderError: ErrorCode.AUTH_TOKEN_INVALID,
        UnauthorizedAccessError: ErrorCode.AUTH_TOKEN_MISSING,
        InsufficientPermissionsError: ErrorCode.AUTH_INSUFFICIENT_PERMISSIONS,
        RoleChangeNotAllowedError: ErrorCode.AUTH_ROLE_CHANGE_NOT_ALLOWED,
        # User errors
        EmailAlreadyExistsError: ErrorCode.USER_EMAIL_EXISTS,
        UserNotFoundByEmailError: ErrorCode.USER_NOT_FOUND,
        ActivationChangeNotPermittedError: ErrorCode.USER_ACTIVATION_NOT_PERMITTED,
        RoleAssignmentNotPermittedError: ErrorCode.USER_ROLE_ASSIGNMENT_NOT_PERMITTED,
        RoleChangeNotPermittedError: ErrorCode.USER_ROLE_CHANGE_NOT_PERMITTED,
        # Field validation
        DomainFieldError: ErrorCode.VAL_INVALID_FORMAT,
    }

    for error_type, error_code in error_mapping.items():
        if isinstance(exc, error_type):
            return error_code

    # Default to internal error
    return ErrorCode.SYS_INTERNAL_ERROR


async def domain_field_error_handler(
    request: Request,
    exc: DomainFieldError,
) -> JSONResponse:
    """
    Handle DomainFieldError exceptions (validation errors).
    """
    logger.info(
        "DomainFieldError: %s (path=%s)",
        str(exc),
        request.url.path,
    )

    definition = ErrorCode.VAL_INVALID_FORMAT.value

    return JSONResponse(
        status_code=definition.http_status,
        content=create_error_response(
            code=definition.code,
            message=str(exc) if str(exc) else definition.default_message,
            i18n_key=definition.i18n_key,
            http_status=definition.http_status,
        ),
    )


async def validation_error_handler(
    request: Request,
    exc: RequestValidationError,
) -> JSONResponse:
    """
    Handle Pydantic validation errors from request parsing.
    """
    errors = exc.errors()
    logger.info(
        "ValidationError: %d errors (path=%s)",
        len(errors),
        request.url.path,
    )

    # Convert Pydantic errors to our format
    details: list[dict[str, Any]] = []
    for error in errors:
        loc = error.get("loc", [])
        field = ".".join(str(l) for l in loc[1:]) if len(loc) > 1 else "body"
        details.append(
            {
                "field": field,
                "message": error.get("msg", "Invalid value"),
                "type": error.get("type", "value_error"),
            }
        )

    definition = ErrorCode.VAL_INVALID_FORMAT.value

    return JSONResponse(
        status_code=422,
        content=create_error_response(
            code="VAL_004",
            message="Validation error",
            i18n_key="errors.validation.invalid_format",
            http_status=422,
            details={"errors": details},
        ),
    )


async def http_exception_handler(
    request: Request,
    exc: StarletteHTTPException,
) -> JSONResponse:
    """
    Handle Starlette/FastAPI HTTP exceptions.
    """
    logger.info(
        "HTTPException: %d - %s (path=%s)",
        exc.status_code,
        exc.detail,
        request.url.path,
    )

    # Map common HTTP status codes to error codes
    status_to_code: dict[int, ErrorCode] = {
        400: ErrorCode.VAL_INVALID_FORMAT,
        401: ErrorCode.AUTH_TOKEN_MISSING,
        403: ErrorCode.AUTH_INSUFFICIENT_PERMISSIONS,
        404: ErrorCode.ADM_RESOURCE_NOT_FOUND,
        405: ErrorCode.VAL_INVALID_FORMAT,
        409: ErrorCode.ADM_RESOURCE_CONFLICT,
        422: ErrorCode.VAL_INVALID_FORMAT,
        429: ErrorCode.AUTH_TOO_MANY_ATTEMPTS,
        500: ErrorCode.SYS_INTERNAL_ERROR,
        502: ErrorCode.SYS_EXTERNAL_SERVICE,
        503: ErrorCode.SYS_MAINTENANCE,
        504: ErrorCode.SYS_TIMEOUT,
    }

    error_code = status_to_code.get(exc.status_code, ErrorCode.SYS_INTERNAL_ERROR)
    definition = error_code.value

    return JSONResponse(
        status_code=exc.status_code,
        content=create_error_response(
            code=definition.code,
            message=str(exc.detail) if exc.detail else definition.default_message,
            i18n_key=definition.i18n_key,
            http_status=exc.status_code,
        ),
    )


async def unhandled_exception_handler(
    request: Request,
    exc: Exception,
) -> JSONResponse:
    """
    Handle all unhandled exceptions.

    This is the catch-all handler for any exception that isn't
    explicitly handled elsewhere.
    """
    logger.exception(
        "Unhandled exception: %s - %s (path=%s)",
        type(exc).__name__,
        str(exc),
        request.url.path,
    )

    definition = ErrorCode.SYS_INTERNAL_ERROR.value

    return JSONResponse(
        status_code=500,
        content=create_error_response(
            code=definition.code,
            message=definition.default_message,
            i18n_key=definition.i18n_key,
            http_status=500,
        ),
    )


def register_exception_handlers(app: FastAPI) -> None:
    """
    Register all exception handlers with the FastAPI application.

    This should be called during application startup.

    Example:
        app = FastAPI()
        register_exception_handlers(app)
    """
    # ApplicationError (our standardized errors)
    app.add_exception_handler(ApplicationError, application_error_handler)

    # DomainFieldError (validation errors)
    app.add_exception_handler(DomainFieldError, domain_field_error_handler)

    # DomainError (legacy domain errors)
    app.add_exception_handler(DomainError, domain_error_handler)

    # Pydantic validation errors
    app.add_exception_handler(RequestValidationError, validation_error_handler)

    # Starlette HTTP exceptions
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)

    # Catch-all for unhandled exceptions
    app.add_exception_handler(Exception, unhandled_exception_handler)

    logger.info("Registered global exception handlers with i18n support")
