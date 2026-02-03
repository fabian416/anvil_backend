"""
Retry telemetry collector.

Tracks retry attempts, circuit breaker state changes, and service overrides.
"""

from typing import Dict, Any, Optional
from uuid import UUID
from datetime import datetime
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class RetryEventType(Enum):
    """Types of retry events."""

    ATTEMPT_START = "attempt_start"
    ATTEMPT_SUCCESS = "attempt_success"
    ATTEMPT_FAILURE = "attempt_failure"
    CIRCUIT_STATE_CHANGE = "circuit_state_change"
    SERVICE_OVERRIDE = "service_override"


class RetryTelemetryCollector:
    """
    Telemetry collector for retry system.

    Tracks:
    - Retry attempts and outcomes
    - Circuit breaker state changes
    - Service overrides
    - Performance metrics
    """

    def __init__(self, repository: Optional[Any] = None):
        """
        Initialize telemetry collector.

        Args:
            repository: Repository for persisting telemetry data (optional)
        """
        self.repository = repository
        self.enabled = repository is not None

    async def record_attempt_start(
        self,
        service_name: str,
        attempt_number: int,
        context: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Record the start of a retry attempt.

        Args:
            service_name: Name of the service
            attempt_number: Attempt number (0 = first attempt)
            context: Additional context (user_id, conversation_id, etc.)
        """
        if not self.enabled:
            return

        try:
            await self.repository.create_attempt(
                service_name=service_name,
                attempt_number=attempt_number,
                request_context=context or {},
                success=None,  # Not yet determined
            )
        except Exception as e:
            logger.error(f"Failed to record attempt start: {e}")

    async def record_success(
        self,
        service_name: str,
        attempt_number: int,
        latency_ms: int,
        context: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Record a successful attempt.

        Args:
            service_name: Name of the service
            attempt_number: Attempt number
            latency_ms: Request latency in milliseconds
            context: Additional context
        """
        if not self.enabled:
            return

        try:
            await self.repository.create_attempt(
                service_name=service_name,
                attempt_number=attempt_number,
                latency_ms=latency_ms,
                request_context=context or {},
                success=True,
            )

            # Update daily aggregate
            await self.repository.increment_success(service_name, latency_ms)
        except Exception as e:
            logger.error(f"Failed to record success: {e}")

    async def record_failure(
        self,
        service_name: str,
        attempt_number: int,
        error_type: str,
        error_message: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Record a failed attempt.

        Args:
            service_name: Name of the service
            attempt_number: Attempt number
            error_type: Type of error (rate_limit, timeout, etc.)
            error_message: Error message
            context: Additional context
        """
        if not self.enabled:
            return

        try:
            await self.repository.create_attempt(
                service_name=service_name,
                attempt_number=attempt_number,
                error_type=error_type,
                error_message=error_message,
                request_context=context or {},
                success=False,
            )

            # Update daily aggregate
            await self.repository.increment_failure(service_name)
        except Exception as e:
            logger.error(f"Failed to record failure: {e}")

    async def record_circuit_state_change(
        self,
        service_name: str,
        from_state: str,
        to_state: str,
        reason: str,
        failure_count: int = 0,
        success_count: int = 0,
    ) -> None:
        """
        Record a circuit breaker state change.

        Args:
            service_name: Name of the service
            from_state: Previous state (CLOSED, OPEN, HALF_OPEN)
            to_state: New state
            reason: Reason for state change
            failure_count: Number of failures
            success_count: Number of successes
        """
        if not self.enabled:
            return

        try:
            await self.repository.create_circuit_event(
                service_name=service_name,
                from_state=from_state,
                to_state=to_state,
                reason=reason,
                failure_count=failure_count,
                success_count=success_count,
            )

            # If opening circuit, increment aggregate
            if to_state == "OPEN":
                await self.repository.increment_circuit_open(service_name)
        except Exception as e:
            logger.error(f"Failed to record circuit state change: {e}")

    async def record_service_override(
        self,
        service_name: str,
        action: str,  # 'enable' or 'disable'
        user_id: UUID,
        reason: str,
        duration_minutes: Optional[int] = None,
    ) -> None:
        """
        Record a manual service override.

        Args:
            service_name: Name of the service
            action: 'enable' or 'disable'
            user_id: User who performed the action
            reason: Reason for override
            duration_minutes: Duration of override (None = permanent)
        """
        if not self.enabled:
            return

        try:
            await self.repository.create_override_event(
                service_name=service_name,
                action=action,
                user_id=user_id,
                reason=reason,
                duration_minutes=duration_minutes,
            )
        except Exception as e:
            logger.error(f"Failed to record service override: {e}")

    async def get_service_metrics(
        self,
        service_name: str,
        days: int = 7,
    ) -> Dict[str, Any]:
        """
        Get aggregated metrics for a service.

        Args:
            service_name: Name of the service
            days: Number of days to retrieve

        Returns:
            Dictionary with metrics
        """
        if not self.enabled:
            return {}

        try:
            return await self.repository.get_aggregated_metrics(
                service_name=service_name,
                days=days,
            )
        except Exception as e:
            logger.error(f"Failed to get service metrics: {e}")
            return {}


# Singleton instance
_retry_telemetry_collector: Optional[RetryTelemetryCollector] = None


def get_retry_telemetry_collector() -> Optional[RetryTelemetryCollector]:
    """Get the global retry telemetry collector."""
    return _retry_telemetry_collector


def set_retry_telemetry_collector(collector: RetryTelemetryCollector) -> None:
    """Set the global retry telemetry collector."""
    global _retry_telemetry_collector
    _retry_telemetry_collector = collector
