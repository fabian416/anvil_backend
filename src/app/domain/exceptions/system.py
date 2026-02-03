"""
System-specific domain exceptions with standardized error codes.

This module provides all exceptions related to:
- Internal system errors
- External service errors
- Infrastructure issues
"""

from typing import Any

from app.domain.exceptions.base import ApplicationError
from app.domain.exceptions.error_codes import ErrorCode


class InternalError(ApplicationError):
    """Raised when an unexpected internal error occurs."""

    def __init__(
        self,
        message: str | None = None,
        error_id: str | None = None,
    ) -> None:
        details = {}
        if error_id:
            details["error_id"] = error_id
        super().__init__(
            ErrorCode.SYS_INTERNAL_ERROR,
            details=details,
            override_message=message,
        )


class ExternalServiceError(ApplicationError):
    """Raised when an external service fails."""

    def __init__(
        self,
        service: str | None = None,
        reason: str | None = None,
        status_code: int | None = None,
    ) -> None:
        details = {}
        if service:
            details["service"] = service
        if reason:
            details["reason"] = reason
        if status_code is not None:
            details["status_code"] = status_code
        super().__init__(ErrorCode.SYS_EXTERNAL_SERVICE, details=details)


class MaintenanceError(ApplicationError):
    """Raised when system is under maintenance."""

    def __init__(
        self,
        estimated_end: str | None = None,
        maintenance_type: str | None = None,
    ) -> None:
        details = {}
        if estimated_end:
            details["estimated_end"] = estimated_end
        if maintenance_type:
            details["maintenance_type"] = maintenance_type
        super().__init__(ErrorCode.SYS_MAINTENANCE, details=details)


class SystemOverloadedError(ApplicationError):
    """Raised when system is overloaded."""

    def __init__(
        self,
        retry_after_seconds: int | None = None,
        queue_position: int | None = None,
    ) -> None:
        details = {}
        if retry_after_seconds is not None:
            details["retry_after_seconds"] = retry_after_seconds
        if queue_position is not None:
            details["queue_position"] = queue_position
        super().__init__(ErrorCode.SYS_OVERLOADED, details=details)


class TimeoutError(ApplicationError):
    """Raised when a request times out."""

    def __init__(
        self,
        operation: str | None = None,
        timeout_seconds: int | None = None,
    ) -> None:
        details = {}
        if operation:
            details["operation"] = operation
        if timeout_seconds is not None:
            details["timeout_seconds"] = timeout_seconds
        super().__init__(ErrorCode.SYS_TIMEOUT, details=details)


class DatabaseError(ApplicationError):
    """Raised when a database error occurs."""

    def __init__(
        self,
        operation: str | None = None,
        reason: str | None = None,
    ) -> None:
        details = {}
        if operation:
            details["operation"] = operation
        if reason:
            details["reason"] = reason
        super().__init__(ErrorCode.SYS_DATABASE_ERROR, details=details)


class CacheError(ApplicationError):
    """Raised when a cache error occurs."""

    def __init__(
        self,
        operation: str | None = None,
        cache_key: str | None = None,
    ) -> None:
        details = {}
        if operation:
            details["operation"] = operation
        if cache_key:
            details["cache_key"] = cache_key
        super().__init__(ErrorCode.SYS_CACHE_ERROR, details=details)


# Additional system-specific exceptions


class ConnectionError(ApplicationError):
    """Raised when a connection fails."""

    def __init__(
        self,
        service: str | None = None,
        host: str | None = None,
        port: int | None = None,
    ) -> None:
        details = {}
        if service:
            details["service"] = service
        if host:
            details["host"] = host
        if port is not None:
            details["port"] = port
        super().__init__(
            ErrorCode.SYS_EXTERNAL_SERVICE,
            details=details,
            override_message="Connection failed",
        )


class ConfigurationError(ApplicationError):
    """Raised when configuration is invalid or missing."""

    def __init__(
        self,
        config_key: str | None = None,
        reason: str | None = None,
    ) -> None:
        details = {}
        if config_key:
            details["config_key"] = config_key
        if reason:
            details["reason"] = reason
        super().__init__(
            ErrorCode.SYS_INTERNAL_ERROR,
            details=details,
            override_message="Configuration error",
        )


class ResourceExhaustedError(ApplicationError):
    """Raised when system resources are exhausted."""

    def __init__(
        self,
        resource: str | None = None,
        limit: str | None = None,
    ) -> None:
        details = {}
        if resource:
            details["resource"] = resource
        if limit:
            details["limit"] = limit
        super().__init__(
            ErrorCode.SYS_OVERLOADED,
            details=details,
            override_message="System resource exhausted",
        )


class CircuitBreakerError(ApplicationError):
    """Raised when circuit breaker is open."""

    def __init__(
        self,
        service: str | None = None,
        reset_at: str | None = None,
    ) -> None:
        details = {}
        if service:
            details["service"] = service
        if reset_at:
            details["reset_at"] = reset_at
        super().__init__(
            ErrorCode.SYS_EXTERNAL_SERVICE,
            details=details,
            override_message="Service circuit breaker is open",
        )


class RetryExhaustedError(ApplicationError):
    """Raised when all retry attempts are exhausted."""

    def __init__(
        self,
        operation: str | None = None,
        attempts: int | None = None,
        last_error: str | None = None,
    ) -> None:
        details = {}
        if operation:
            details["operation"] = operation
        if attempts is not None:
            details["attempts"] = attempts
        if last_error:
            details["last_error"] = last_error
        super().__init__(
            ErrorCode.SYS_EXTERNAL_SERVICE,
            details=details,
            override_message="All retry attempts exhausted",
        )


class HealthCheckError(ApplicationError):
    """Raised when health check fails."""

    def __init__(
        self,
        component: str | None = None,
        status: str | None = None,
    ) -> None:
        details = {}
        if component:
            details["component"] = component
        if status:
            details["status"] = status
        super().__init__(
            ErrorCode.SYS_MAINTENANCE,
            details=details,
            override_message="Health check failed",
        )


class TaskQueueError(ApplicationError):
    """Raised when task queue operation fails."""

    def __init__(
        self,
        queue: str | None = None,
        task_id: str | None = None,
        reason: str | None = None,
    ) -> None:
        details = {}
        if queue:
            details["queue"] = queue
        if task_id:
            details["task_id"] = task_id
        if reason:
            details["reason"] = reason
        super().__init__(
            ErrorCode.SYS_INTERNAL_ERROR,
            details=details,
            override_message="Task queue operation failed",
        )


class FileStorageError(ApplicationError):
    """Raised when file storage operation fails."""

    def __init__(
        self,
        operation: str | None = None,
        path: str | None = None,
        reason: str | None = None,
    ) -> None:
        details = {}
        if operation:
            details["operation"] = operation
        if path:
            details["path"] = path
        if reason:
            details["reason"] = reason
        super().__init__(
            ErrorCode.SYS_INTERNAL_ERROR,
            details=details,
            override_message="File storage operation failed",
        )


class EncryptionError(ApplicationError):
    """Raised when encryption/decryption fails."""

    def __init__(
        self,
        operation: str | None = None,
        reason: str | None = None,
    ) -> None:
        details = {}
        if operation:
            details["operation"] = operation
        if reason:
            details["reason"] = reason
        super().__init__(
            ErrorCode.SYS_INTERNAL_ERROR,
            details=details,
            override_message="Encryption operation failed",
        )
