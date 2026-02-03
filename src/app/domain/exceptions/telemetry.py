"""
Telemetry-specific domain exceptions with standardized error codes.

This module provides all exceptions related to:
- Telemetry access and permissions
- Metrics and monitoring
- Telemetry service availability
"""

from typing import Any
from uuid import UUID

from app.domain.exceptions.base import ApplicationError
from app.domain.exceptions.error_codes import ErrorCode


class TelemetryAccessDeniedError(ApplicationError):
    """Raised when telemetry access is denied."""

    def __init__(
        self,
        required_role: str | None = None,
        resource: str | None = None,
    ) -> None:
        details = {}
        if required_role:
            details["required_role"] = required_role
        if resource:
            details["resource"] = resource
        super().__init__(ErrorCode.TEL_ACCESS_DENIED, details=details)


class InvalidTimeRangeError(ApplicationError):
    """Raised when an invalid time range is specified."""

    def __init__(
        self,
        start_time: str | None = None,
        end_time: str | None = None,
        max_range_hours: int | None = None,
        reason: str | None = None,
    ) -> None:
        details = {}
        if start_time:
            details["start_time"] = start_time
        if end_time:
            details["end_time"] = end_time
        if max_range_hours is not None:
            details["max_range_hours"] = max_range_hours
        if reason:
            details["reason"] = reason
        super().__init__(ErrorCode.TEL_INVALID_TIMERANGE, details=details)


class TelemetryServiceUnavailableError(ApplicationError):
    """Raised when telemetry service is unavailable."""

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
        super().__init__(ErrorCode.TEL_SERVICE_UNAVAILABLE, details=details)


class InvalidMetricError(ApplicationError):
    """Raised when an invalid metric name is specified."""

    def __init__(
        self,
        metric_name: str | None = None,
        valid_metrics: list[str] | None = None,
    ) -> None:
        details = {}
        if metric_name:
            details["metric_name"] = metric_name
        if valid_metrics:
            details["valid_metrics"] = valid_metrics
        super().__init__(ErrorCode.TEL_INVALID_METRIC, details=details, field="metric")


# Additional telemetry-specific exceptions


class MetricNotFoundError(ApplicationError):
    """Raised when a metric is not found."""

    def __init__(
        self,
        metric_name: str | None = None,
        namespace: str | None = None,
    ) -> None:
        details = {}
        if metric_name:
            details["metric_name"] = metric_name
        if namespace:
            details["namespace"] = namespace
        super().__init__(
            ErrorCode.TEL_INVALID_METRIC,
            details=details,
            override_message="Metric not found",
        )


class TelemetryDisabledError(ApplicationError):
    """Raised when telemetry is disabled."""

    def __init__(
        self,
        component: str | None = None,
        reason: str | None = None,
    ) -> None:
        details = {}
        if component:
            details["component"] = component
        if reason:
            details["reason"] = reason
        super().__init__(
            ErrorCode.TEL_SERVICE_UNAVAILABLE,
            details=details,
            override_message="Telemetry is disabled for this component",
        )


class TraceNotFoundError(ApplicationError):
    """Raised when a trace is not found."""

    def __init__(
        self,
        trace_id: str | None = None,
    ) -> None:
        details = {}
        if trace_id:
            details["trace_id"] = trace_id
        super().__init__(
            ErrorCode.TEL_INVALID_METRIC,
            details=details,
            override_message="Trace not found",
        )


class AlertThresholdError(ApplicationError):
    """Raised when alert threshold configuration is invalid."""

    def __init__(
        self,
        threshold_name: str | None = None,
        value: float | None = None,
        valid_range: str | None = None,
    ) -> None:
        details = {}
        if threshold_name:
            details["threshold_name"] = threshold_name
        if value is not None:
            details["value"] = value
        if valid_range:
            details["valid_range"] = valid_range
        super().__init__(
            ErrorCode.TEL_INVALID_METRIC,
            details=details,
            override_message="Invalid alert threshold",
        )


class DashboardNotFoundError(ApplicationError):
    """Raised when a dashboard is not found."""

    def __init__(
        self,
        dashboard_id: str | UUID | None = None,
        dashboard_name: str | None = None,
    ) -> None:
        details = {}
        if dashboard_id:
            details["dashboard_id"] = str(dashboard_id)
        if dashboard_name:
            details["dashboard_name"] = dashboard_name
        super().__init__(
            ErrorCode.TEL_INVALID_METRIC,
            details=details,
            override_message="Dashboard not found",
        )


class QueryExecutionError(ApplicationError):
    """Raised when a telemetry query fails."""

    def __init__(
        self,
        query: str | None = None,
        reason: str | None = None,
    ) -> None:
        details = {}
        if query:
            details["query"] = query
        if reason:
            details["reason"] = reason
        super().__init__(
            ErrorCode.TEL_SERVICE_UNAVAILABLE,
            details=details,
            override_message="Telemetry query execution failed",
        )


class DataRetentionError(ApplicationError):
    """Raised when data is outside retention period."""

    def __init__(
        self,
        requested_date: str | None = None,
        retention_days: int | None = None,
    ) -> None:
        details = {}
        if requested_date:
            details["requested_date"] = requested_date
        if retention_days is not None:
            details["retention_days"] = retention_days
        super().__init__(
            ErrorCode.TEL_INVALID_TIMERANGE,
            details=details,
            override_message="Data is outside retention period",
        )


class ExportLimitError(ApplicationError):
    """Raised when export limit is exceeded."""

    def __init__(
        self,
        requested_rows: int | None = None,
        max_rows: int | None = None,
    ) -> None:
        details = {}
        if requested_rows is not None:
            details["requested_rows"] = requested_rows
        if max_rows is not None:
            details["max_rows"] = max_rows
        super().__init__(
            ErrorCode.TEL_SERVICE_UNAVAILABLE,
            details=details,
            override_message="Export limit exceeded",
        )
