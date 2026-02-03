"""
Admin-specific domain exceptions with standardized error codes.

This module provides all exceptions related to:
- Admin access and permissions
- Resource management
- Admin operations and configurations
"""

from typing import Any
from uuid import UUID

from app.domain.exceptions.base import ApplicationError
from app.domain.exceptions.error_codes import ErrorCode


class AdminAccessDeniedError(ApplicationError):
    """Raised when admin access is denied."""

    def __init__(
        self,
        required_role: str | None = None,
        current_role: str | None = None,
        resource: str | None = None,
    ) -> None:
        details = {}
        if required_role:
            details["required_role"] = required_role
        if current_role:
            details["current_role"] = current_role
        if resource:
            details["resource"] = resource
        super().__init__(ErrorCode.ADM_ACCESS_DENIED, details=details)


class AdminResourceNotFoundError(ApplicationError):
    """Raised when an admin resource is not found."""

    def __init__(
        self,
        resource_type: str | None = None,
        resource_id: str | UUID | None = None,
    ) -> None:
        details = {}
        if resource_type:
            details["resource_type"] = resource_type
        if resource_id:
            details["resource_id"] = str(resource_id)
        super().__init__(ErrorCode.ADM_RESOURCE_NOT_FOUND, details=details)


class AdminResourceConflictError(ApplicationError):
    """Raised when an admin resource already exists."""

    def __init__(
        self,
        resource_type: str | None = None,
        resource_id: str | UUID | None = None,
        conflict_field: str | None = None,
    ) -> None:
        details = {}
        if resource_type:
            details["resource_type"] = resource_type
        if resource_id:
            details["resource_id"] = str(resource_id)
        if conflict_field:
            details["conflict_field"] = conflict_field
        super().__init__(ErrorCode.ADM_RESOURCE_CONFLICT, details=details)


class AdminOperationFailedError(ApplicationError):
    """Raised when an admin operation fails."""

    def __init__(
        self,
        operation: str | None = None,
        reason: str | None = None,
        affected_resources: list[str] | None = None,
    ) -> None:
        details = {}
        if operation:
            details["operation"] = operation
        if reason:
            details["reason"] = reason
        if affected_resources:
            details["affected_resources"] = affected_resources
        super().__init__(ErrorCode.ADM_OPERATION_FAILED, details=details)


class InvalidConfigurationError(ApplicationError):
    """Raised when a configuration is invalid."""

    def __init__(
        self,
        config_key: str | None = None,
        invalid_value: Any | None = None,
        expected_type: str | None = None,
        valid_values: list[str] | None = None,
    ) -> None:
        details = {}
        if config_key:
            details["config_key"] = config_key
        if invalid_value is not None:
            details["invalid_value"] = str(invalid_value)
        if expected_type:
            details["expected_type"] = expected_type
        if valid_values:
            details["valid_values"] = valid_values
        super().__init__(
            ErrorCode.ADM_INVALID_CONFIG, details=details, field=config_key
        )


class AdminServiceUnavailableError(ApplicationError):
    """Raised when admin service is temporarily unavailable."""

    def __init__(
        self,
        service: str | None = None,
        retry_after_seconds: int | None = None,
    ) -> None:
        details = {}
        if service:
            details["service"] = service
        if retry_after_seconds is not None:
            details["retry_after_seconds"] = retry_after_seconds
        super().__init__(ErrorCode.ADM_SERVICE_UNAVAILABLE, details=details)


# Additional admin-specific exceptions


class BulkOperationFailedError(ApplicationError):
    """Raised when a bulk operation fails."""

    def __init__(
        self,
        operation: str | None = None,
        total_items: int | None = None,
        failed_items: int | None = None,
        failed_ids: list[str] | None = None,
    ) -> None:
        details = {}
        if operation:
            details["operation"] = operation
        if total_items is not None:
            details["total_items"] = total_items
        if failed_items is not None:
            details["failed_items"] = failed_items
        if failed_ids:
            details["failed_ids"] = failed_ids
        super().__init__(
            ErrorCode.ADM_OPERATION_FAILED,
            details=details,
            override_message="Bulk operation partially failed",
        )


class ConfigValidationError(ApplicationError):
    """Raised when configuration validation fails."""

    def __init__(
        self,
        validation_errors: dict[str, str] | None = None,
    ) -> None:
        details = {}
        if validation_errors:
            details["validation_errors"] = validation_errors
        super().__init__(
            ErrorCode.ADM_INVALID_CONFIG,
            details=details,
            override_message="Configuration validation failed",
        )


class ProtectedResourceError(ApplicationError):
    """Raised when trying to modify a protected resource."""

    def __init__(
        self,
        resource_type: str | None = None,
        resource_id: str | UUID | None = None,
        reason: str | None = None,
    ) -> None:
        details = {}
        if resource_type:
            details["resource_type"] = resource_type
        if resource_id:
            details["resource_id"] = str(resource_id)
        if reason:
            details["reason"] = reason
        super().__init__(
            ErrorCode.ADM_ACCESS_DENIED,
            details=details,
            override_message="Resource is protected and cannot be modified",
        )


class MaintenanceModeError(ApplicationError):
    """Raised when system is in maintenance mode."""

    def __init__(
        self,
        estimated_end: str | None = None,
        reason: str | None = None,
    ) -> None:
        details = {}
        if estimated_end:
            details["estimated_end"] = estimated_end
        if reason:
            details["reason"] = reason
        super().__init__(
            ErrorCode.ADM_SERVICE_UNAVAILABLE,
            details=details,
            override_message="System is in maintenance mode",
        )


class AuditLogError(ApplicationError):
    """Raised when audit logging fails."""

    def __init__(
        self,
        action: str | None = None,
        reason: str | None = None,
    ) -> None:
        details = {}
        if action:
            details["action"] = action
        if reason:
            details["reason"] = reason
        super().__init__(
            ErrorCode.ADM_OPERATION_FAILED,
            details=details,
            override_message="Failed to create audit log entry",
        )


class DataExportError(ApplicationError):
    """Raised when data export fails."""

    def __init__(
        self,
        export_type: str | None = None,
        reason: str | None = None,
    ) -> None:
        details = {}
        if export_type:
            details["export_type"] = export_type
        if reason:
            details["reason"] = reason
        super().__init__(
            ErrorCode.ADM_OPERATION_FAILED,
            details=details,
            override_message="Data export failed",
        )


class DataImportError(ApplicationError):
    """Raised when data import fails."""

    def __init__(
        self,
        import_type: str | None = None,
        reason: str | None = None,
        row_number: int | None = None,
    ) -> None:
        details = {}
        if import_type:
            details["import_type"] = import_type
        if reason:
            details["reason"] = reason
        if row_number is not None:
            details["row_number"] = row_number
        super().__init__(
            ErrorCode.ADM_OPERATION_FAILED,
            details=details,
            override_message="Data import failed",
        )
