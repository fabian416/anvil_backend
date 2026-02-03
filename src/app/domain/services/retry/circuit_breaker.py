"""
Circuit Breaker with Redis-backed state.

Prevents cascade failures by tracking failure rates and temporarily
blocking requests to failing services.

Pattern: CLOSED → OPEN → HALF_OPEN → CLOSED
"""

import logging
from enum import Enum
from typing import Dict, Optional, Any
from datetime import datetime, timedelta, UTC
from dataclasses import dataclass
import json

logger = logging.getLogger(__name__)


class CircuitState(Enum):
    """Circuit breaker states."""

    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


@dataclass
class CircuitBreakerConfig:
    """Circuit breaker configuration."""

    failure_threshold: int = 5  # Failures before opening
    success_threshold: int = 2  # Successes in half-open to close
    timeout_seconds: int = 60  # Time before trying half-open
    half_open_max_calls: int = 3  # Max calls in half-open state


class CircuitBreakerOpenError(Exception):
    """Raised when circuit breaker is open."""

    pass


class CircuitBreaker:
    """
    Circuit breaker with Redis-backed state.

    Prevents cascading failures by:
    - Tracking failure rates per service
    - Opening circuit when threshold exceeded
    - Automatically testing recovery
    - Recording state changes in telemetry

    States:
    - CLOSED: Normal operation, requests allowed
    - OPEN: Failures exceeded threshold, requests blocked
    - HALF_OPEN: Testing recovery, limited requests allowed

    Usage:
        cb = CircuitBreaker(redis_client, config, telemetry)

        if cb.is_open("my_service"):
            raise CircuitBreakerOpenError("Service unavailable")

        try:
            result = await make_api_call()
            cb.record_success("my_service")
        except Exception:
            cb.record_failure("my_service")
    """

    def __init__(
        self,
        redis_client: Any,
        config: Optional[CircuitBreakerConfig] = None,
        telemetry: Optional[Any] = None,
    ):
        """
        Initialize circuit breaker.

        Args:
            redis_client: Redis client for state storage
            config: Configuration
            telemetry: Telemetry collector (optional)
        """
        self.redis = redis_client
        self.config = config or CircuitBreakerConfig()
        self.telemetry = telemetry

    def is_open(self, service_name: str) -> bool:
        """
        Check if circuit is open for service.

        Args:
            service_name: Service name

        Returns:
            True if circuit is open
        """
        state = self._get_state(service_name)

        if state == CircuitState.OPEN:
            # Check if timeout expired (transition to half-open)
            if self._should_attempt_reset(service_name):
                self._transition_to_half_open(service_name)
                return False
            return True

        return False

    def is_half_open(self, service_name: str) -> bool:
        """
        Check if circuit is half-open for service.

        Args:
            service_name: Service name

        Returns:
            True if circuit is half-open
        """
        return self._get_state(service_name) == CircuitState.HALF_OPEN

    def record_success(self, service_name: str):
        """
        Record successful call.

        Args:
            service_name: Service name
        """
        state = self._get_state(service_name)

        if state == CircuitState.HALF_OPEN:
            # Increment success counter
            successes = self._increment_counter(
                f"circuit:{service_name}:half_open_successes"
            )

            logger.debug(
                f"Circuit breaker for {service_name}: "
                f"{successes}/{self.config.success_threshold} successes in HALF_OPEN"
            )

            # Close circuit if threshold met
            if successes >= self.config.success_threshold:
                self._transition_to_closed(service_name)

        elif state == CircuitState.CLOSED:
            # Reset failure counter on success
            self._reset_counter(f"circuit:{service_name}:failures")

    def record_failure(self, service_name: str):
        """
        Record failed call.

        Args:
            service_name: Service name
        """
        state = self._get_state(service_name)

        if state == CircuitState.HALF_OPEN:
            # Failure in half-open immediately opens circuit
            logger.warning(
                f"Circuit breaker for {service_name}: "
                f"Failed during HALF_OPEN testing, reopening circuit"
            )
            self._transition_to_open(service_name)

        elif state == CircuitState.CLOSED:
            # Increment failure counter
            failures = self._increment_counter(f"circuit:{service_name}:failures")

            logger.debug(
                f"Circuit breaker for {service_name}: "
                f"{failures}/{self.config.failure_threshold} failures"
            )

            # Open circuit if threshold exceeded
            if failures >= self.config.failure_threshold:
                self._transition_to_open(service_name)

    def reset(self, service_name: str):
        """
        Manually reset circuit breaker to closed state.

        Args:
            service_name: Service name
        """
        self._transition_to_closed(service_name)
        logger.info(f"Circuit breaker MANUALLY RESET for {service_name}")

    def get_status(self, service_name: str) -> Dict[str, Any]:
        """
        Get circuit breaker status for service.

        Args:
            service_name: Service name

        Returns:
            Status dictionary
        """
        state = self._get_state(service_name)
        failures = self._get_counter(f"circuit:{service_name}:failures")
        successes = self._get_counter(f"circuit:{service_name}:half_open_successes")
        opened_at_str = self.redis.get(f"circuit:{service_name}:opened_at")

        opened_at = None
        if opened_at_str:
            try:
                opened_at = datetime.fromisoformat(opened_at_str.decode())
            except (ValueError, AttributeError):
                pass

        return {
            "service_name": service_name,
            "state": state.value,
            "failure_count": failures,
            "success_count": successes,
            "opened_at": opened_at.isoformat() if opened_at else None,
            "config": {
                "failure_threshold": self.config.failure_threshold,
                "success_threshold": self.config.success_threshold,
                "timeout_seconds": self.config.timeout_seconds,
            },
        }

    # Private methods

    def _transition_to_open(self, service_name: str):
        """Transition circuit to OPEN state."""
        self._set_state(service_name, CircuitState.OPEN)
        self._set_open_timestamp(service_name)

        logger.warning(
            f"Circuit breaker OPENED for {service_name} "
            f"(failure threshold exceeded: {self.config.failure_threshold})"
        )

        # Record telemetry
        if self.telemetry:
            import asyncio

            failure_count = self._get_counter(f"circuit:{service_name}:failures")
            asyncio.create_task(
                self.telemetry.record_circuit_state_change(
                    service_name=service_name,
                    from_state="CLOSED",
                    to_state="OPEN",
                    reason="failure_threshold_exceeded",
                    failure_count=failure_count,
                )
            )

    def _transition_to_half_open(self, service_name: str):
        """Transition circuit to HALF_OPEN state."""
        self._set_state(service_name, CircuitState.HALF_OPEN)
        self._reset_counter(f"circuit:{service_name}:half_open_successes")

        logger.info(
            f"Circuit breaker HALF_OPEN for {service_name} "
            f"(testing recovery after {self.config.timeout_seconds}s timeout)"
        )

        # Record telemetry
        if self.telemetry:
            import asyncio

            asyncio.create_task(
                self.telemetry.record_circuit_state_change(
                    service_name=service_name,
                    from_state="OPEN",
                    to_state="HALF_OPEN",
                    reason="timeout_expired",
                )
            )

    def _transition_to_closed(self, service_name: str):
        """Transition circuit to CLOSED state."""
        self._set_state(service_name, CircuitState.CLOSED)
        self._reset_counter(f"circuit:{service_name}:failures")
        self._reset_counter(f"circuit:{service_name}:half_open_successes")
        self.redis.delete(f"circuit:{service_name}:opened_at")

        logger.info(
            f"Circuit breaker CLOSED for {service_name} "
            f"(success threshold met: {self.config.success_threshold})"
        )

        # Record telemetry
        if self.telemetry:
            import asyncio

            success_count = self._get_counter(
                f"circuit:{service_name}:half_open_successes"
            )
            asyncio.create_task(
                self.telemetry.record_circuit_state_change(
                    service_name=service_name,
                    from_state="HALF_OPEN",
                    to_state="CLOSED",
                    reason="success_threshold_met",
                    success_count=success_count,
                )
            )

    def _should_attempt_reset(self, service_name: str) -> bool:
        """Check if timeout has passed and circuit should attempt reset."""
        opened_at_str = self.redis.get(f"circuit:{service_name}:opened_at")
        if not opened_at_str:
            return True

        try:
            opened_at = datetime.fromisoformat(opened_at_str.decode())
            timeout_threshold = opened_at + timedelta(
                seconds=self.config.timeout_seconds
            )
            return datetime.now(UTC) >= timeout_threshold
        except (ValueError, AttributeError):
            return True

    # Redis helpers

    def _get_state(self, service_name: str) -> CircuitState:
        """Get circuit state from Redis."""
        state = self.redis.get(f"circuit:{service_name}:state")
        if state is None:
            return CircuitState.CLOSED
        try:
            return CircuitState(state.decode())
        except (ValueError, AttributeError):
            return CircuitState.CLOSED

    def _set_state(self, service_name: str, state: CircuitState):
        """Set circuit state in Redis."""
        self.redis.set(f"circuit:{service_name}:state", state.value)

    def _get_counter(self, key: str) -> int:
        """Get counter value from Redis."""
        value = self.redis.get(key)
        if value is None:
            return 0
        try:
            return int(value.decode())
        except (ValueError, AttributeError):
            return 0

    def _increment_counter(self, key: str) -> int:
        """Increment counter in Redis and return new value."""
        return self.redis.incr(key)

    def _reset_counter(self, key: str):
        """Reset counter in Redis."""
        self.redis.set(key, 0)

    def _set_open_timestamp(self, service_name: str):
        """Set opened timestamp in Redis."""
        self.redis.set(
            f"circuit:{service_name}:opened_at",
            datetime.now(UTC).isoformat(),
        )


class CircuitBreakerManager:
    """
    Manages circuit breakers for all services.

    Provides centralized access to circuit breaker state.
    """

    def __init__(
        self,
        redis_client: Any,
        config: Optional[CircuitBreakerConfig] = None,
        telemetry: Optional[Any] = None,
    ):
        """
        Initialize circuit breaker manager.

        Args:
            redis_client: Redis client
            config: Default configuration
            telemetry: Telemetry collector
        """
        self.redis = redis_client
        self.config = config or CircuitBreakerConfig()
        self.telemetry = telemetry
        self._breakers: Dict[str, CircuitBreaker] = {}

    def get_or_create(self, service_name: str) -> CircuitBreaker:
        """
        Get or create circuit breaker for service.

        Args:
            service_name: Service name

        Returns:
            Circuit breaker
        """
        if service_name not in self._breakers:
            self._breakers[service_name] = CircuitBreaker(
                redis_client=self.redis,
                config=self.config,
                telemetry=self.telemetry,
            )

        return self._breakers[service_name]

    def is_open(self, service_name: str) -> bool:
        """Check if circuit breaker is open."""
        breaker = self.get_or_create(service_name)
        return breaker.is_open(service_name)

    def record_success(self, service_name: str):
        """Record successful request."""
        breaker = self.get_or_create(service_name)
        breaker.record_success(service_name)

    def record_failure(self, service_name: str):
        """Record failed request."""
        breaker = self.get_or_create(service_name)
        breaker.record_failure(service_name)

    def reset(self, service_name: str):
        """Manually reset circuit breaker."""
        breaker = self.get_or_create(service_name)
        breaker.reset(service_name)

    def get_all_statuses(self) -> Dict[str, Dict[str, Any]]:
        """
        Get status of all circuit breakers.

        Returns:
            Dictionary of service_name -> status dict
        """
        # Get all circuit breaker keys from Redis
        pattern = "circuit:*:state"
        keys = self.redis.keys(pattern)

        statuses = {}
        for key in keys:
            # Extract service name from key (circuit:SERVICE_NAME:state)
            service_name = key.decode().split(":")[1]
            breaker = self.get_or_create(service_name)
            statuses[service_name] = breaker.get_status(service_name)

        return statuses

    def count_open(self) -> int:
        """Count open circuit breakers."""
        statuses = self.get_all_statuses()
        return sum(1 for status in statuses.values() if status["state"] == "open")

    def count_total(self) -> int:
        """Count total circuit breakers."""
        return len(self.get_all_statuses())
