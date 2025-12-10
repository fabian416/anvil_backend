"""
Circuit Breaker pattern implementation.

Prevents cascade failures by tracking failure rates and temporarily
blocking requests to failing providers/models.
"""

import logging
from typing import Any, Dict, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass
from uuid import UUID

logger = logging.getLogger(__name__)


@dataclass
class CircuitBreakerConfig:
    """Circuit breaker configuration."""

    failure_threshold: int = 5
    success_threshold: int = 3
    timeout_seconds: int = 60
    half_open_max_requests: int = 3


class CircuitBreakerState:
    """State of a single circuit breaker."""

    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


class CircuitBreaker:
    """
    Circuit breaker for a single entity (provider or model).

    States:
    - CLOSED: Normal operation, requests allowed
    - OPEN: Failures exceeded threshold, requests blocked
    - HALF_OPEN: Testing recovery, limited requests allowed
    """

    def __init__(
        self,
        entity_id: UUID,
        entity_name: str,
        entity_type: str,
        config: CircuitBreakerConfig = None,
    ):
        """
        Initialize circuit breaker.

        Args:
            entity_id: ID of entity (provider/model)
            entity_name: Display name
            entity_type: Type (provider, model)
            config: Configuration
        """
        self.entity_id = entity_id
        self.entity_name = entity_name
        self.entity_type = entity_type
        self.config = config or CircuitBreakerConfig()

        # State
        self.state = CircuitBreakerState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.consecutive_failures = 0

        # Timestamps
        self.last_failure_at: Optional[datetime] = None
        self.last_success_at: Optional[datetime] = None
        self.opened_at: Optional[datetime] = None
        self.half_open_at: Optional[datetime] = None

    def is_open(self) -> bool:
        """Check if circuit breaker is open."""
        if self.state == CircuitBreakerState.OPEN:
            # Check if timeout has passed
            if self.opened_at:
                timeout_passed = datetime.utcnow() >= self.opened_at + timedelta(
                    seconds=self.config.timeout_seconds
                )

                if timeout_passed:
                    # Move to half-open state
                    self._transition_to_half_open()
                    return False

            return True

        return False

    def is_half_open(self) -> bool:
        """Check if circuit breaker is half-open."""
        return self.state == CircuitBreakerState.HALF_OPEN

    def record_success(self):
        """Record successful request."""
        self.last_success_at = datetime.utcnow()
        self.consecutive_failures = 0

        if self.state == CircuitBreakerState.HALF_OPEN:
            self.success_count += 1

            if self.success_count >= self.config.success_threshold:
                # Recovery confirmed, close circuit
                self._transition_to_closed()
                logger.info(
                    f"Circuit breaker CLOSED for {self.entity_type} {self.entity_name} "
                    f"after {self.success_count} successful requests"
                )

    def record_failure(self):
        """Record failed request."""
        self.failure_count += 1
        self.consecutive_failures += 1
        self.last_failure_at = datetime.utcnow()

        if self.state == CircuitBreakerState.CLOSED:
            if self.consecutive_failures >= self.config.failure_threshold:
                # Open circuit breaker
                self._transition_to_open()
                logger.warning(
                    f"Circuit breaker OPENED for {self.entity_type} {self.entity_name} "
                    f"after {self.consecutive_failures} consecutive failures"
                )

        elif self.state == CircuitBreakerState.HALF_OPEN:
            # Failed during testing, reopen circuit
            self._transition_to_open()
            logger.warning(
                f"Circuit breaker REOPENED for {self.entity_type} {self.entity_name} "
                f"(failed during half-open testing)"
            )

    def reset(self):
        """Manually reset circuit breaker to closed state."""
        self._transition_to_closed()
        logger.info(f"Circuit breaker RESET for {self.entity_type} {self.entity_name}")

    def _transition_to_closed(self):
        """Transition to closed state."""
        self.state = CircuitBreakerState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.consecutive_failures = 0
        self.opened_at = None
        self.half_open_at = None

    def _transition_to_open(self):
        """Transition to open state."""
        self.state = CircuitBreakerState.OPEN
        self.opened_at = datetime.utcnow()
        self.success_count = 0

    def _transition_to_half_open(self):
        """Transition to half-open state."""
        self.state = CircuitBreakerState.HALF_OPEN
        self.half_open_at = datetime.utcnow()
        self.success_count = 0
        logger.info(
            f"Circuit breaker HALF-OPEN for {self.entity_type} {self.entity_name} "
            f"(testing recovery)"
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "entity_id": str(self.entity_id),
            "entity_name": self.entity_name,
            "entity_type": self.entity_type,
            "state": self.state,
            "failure_count": self.failure_count,
            "success_count": self.success_count,
            "consecutive_failures": self.consecutive_failures,
            "last_failure_at": self.last_failure_at.isoformat() if self.last_failure_at else None,
            "last_success_at": self.last_success_at.isoformat() if self.last_success_at else None,
            "opened_at": self.opened_at.isoformat() if self.opened_at else None,
            "config": {
                "failure_threshold": self.config.failure_threshold,
                "success_threshold": self.config.success_threshold,
                "timeout_seconds": self.config.timeout_seconds,
            },
        }


class CircuitBreakerManager:
    """
    Manages circuit breakers for all providers and models.

    Provides centralized access to circuit breaker state.
    """

    def __init__(self):
        """Initialize circuit breaker manager."""
        self._breakers: Dict[UUID, CircuitBreaker] = {}

    def get_or_create(
        self,
        entity_id: UUID,
        entity_name: str,
        entity_type: str,
        config: CircuitBreakerConfig = None,
    ) -> CircuitBreaker:
        """
        Get or create circuit breaker for entity.

        Args:
            entity_id: Entity ID
            entity_name: Entity name
            entity_type: Entity type (provider, model)
            config: Configuration

        Returns:
            Circuit breaker
        """
        if entity_id not in self._breakers:
            self._breakers[entity_id] = CircuitBreaker(
                entity_id=entity_id,
                entity_name=entity_name,
                entity_type=entity_type,
                config=config,
            )

        return self._breakers[entity_id]

    def is_open(self, entity_id: UUID) -> bool:
        """
        Check if circuit breaker is open.

        Args:
            entity_id: Entity ID

        Returns:
            True if circuit is open
        """
        breaker = self._breakers.get(entity_id)
        if breaker:
            return breaker.is_open()
        return False

    def record_success(self, entity_id: UUID):
        """
        Record successful request.

        Args:
            entity_id: Entity ID
        """
        breaker = self._breakers.get(entity_id)
        if breaker:
            breaker.record_success()

    def record_failure(self, entity_id: UUID):
        """
        Record failed request.

        Args:
            entity_id: Entity ID
        """
        breaker = self._breakers.get(entity_id)
        if breaker:
            breaker.record_failure()

    def reset(self, entity_id: UUID):
        """
        Manually reset circuit breaker.

        Args:
            entity_id: Entity ID
        """
        breaker = self._breakers.get(entity_id)
        if breaker:
            breaker.reset()

    def count_open(self) -> int:
        """Count open circuit breakers."""
        return sum(1 for breaker in self._breakers.values() if breaker.state == CircuitBreakerState.OPEN)

    def count_total(self) -> int:
        """Count total circuit breakers."""
        return len(self._breakers)

    def get_all_states(self) -> Dict[UUID, Dict[str, Any]]:
        """
        Get state of all circuit breakers.

        Returns:
            Dictionary of entity_id -> state dict
        """
        return {entity_id: breaker.to_dict() for entity_id, breaker in self._breakers.items()}
