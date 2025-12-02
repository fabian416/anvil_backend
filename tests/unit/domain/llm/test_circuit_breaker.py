"""
Unit tests for Circuit Breaker.
"""

import pytest
from datetime import datetime, timedelta
from uuid import uuid4

from app.domain.services.llm.circuit_breaker import (
    CircuitBreaker,
    CircuitBreakerManager,
    CircuitBreakerConfig,
    CircuitBreakerState,
)


class TestCircuitBreaker:
    """Test CircuitBreaker functionality."""

    def test_initial_state_is_closed(self):
        """Test circuit breaker starts in closed state."""
        breaker = CircuitBreaker(
            entity_id=uuid4(),
            entity_name="test-model",
            entity_type="model",
        )

        assert breaker.state == CircuitBreakerState.CLOSED
        assert not breaker.is_open()

    def test_opens_after_threshold_failures(self):
        """Test circuit opens after failure threshold."""
        config = CircuitBreakerConfig(failure_threshold=3)
        breaker = CircuitBreaker(
            entity_id=uuid4(),
            entity_name="test-model",
            entity_type="model",
            config=config,
        )

        # Record failures
        breaker.record_failure()
        assert not breaker.is_open()

        breaker.record_failure()
        assert not breaker.is_open()

        breaker.record_failure()
        assert breaker.is_open()  # Should open now

    def test_success_resets_consecutive_failures(self):
        """Test success resets consecutive failure count."""
        config = CircuitBreakerConfig(failure_threshold=3)
        breaker = CircuitBreaker(
            entity_id=uuid4(),
            entity_name="test-model",
            entity_type="model",
            config=config,
        )

        # Record failures
        breaker.record_failure()
        breaker.record_failure()

        # Success resets count
        breaker.record_success()
        assert breaker.consecutive_failures == 0

        # Need 3 more failures to open
        breaker.record_failure()
        breaker.record_failure()
        assert not breaker.is_open()

        breaker.record_failure()
        assert breaker.is_open()

    def test_half_open_after_timeout(self):
        """Test circuit transitions to half-open after timeout."""
        config = CircuitBreakerConfig(
            failure_threshold=2, timeout_seconds=1  # 1 second timeout
        )
        breaker = CircuitBreaker(
            entity_id=uuid4(),
            entity_name="test-model",
            entity_type="model",
            config=config,
        )

        # Open circuit
        breaker.record_failure()
        breaker.record_failure()
        assert breaker.is_open()

        # Simulate timeout by modifying opened_at
        breaker.opened_at = datetime.utcnow() - timedelta(seconds=2)

        # Should transition to half-open
        assert not breaker.is_open()  # Checks timeout
        assert breaker.is_half_open()

    def test_half_open_closes_after_successes(self):
        """Test half-open circuit closes after success threshold."""
        config = CircuitBreakerConfig(success_threshold=2)
        breaker = CircuitBreaker(
            entity_id=uuid4(),
            entity_name="test-model",
            entity_type="model",
            config=config,
        )

        # Force half-open state
        breaker.state = CircuitBreakerState.HALF_OPEN

        # Record successes
        breaker.record_success()
        assert breaker.is_half_open()

        breaker.record_success()
        assert not breaker.is_half_open()
        assert breaker.state == CircuitBreakerState.CLOSED

    def test_half_open_reopens_on_failure(self):
        """Test half-open circuit reopens on failure."""
        config = CircuitBreakerConfig(failure_threshold=2)
        breaker = CircuitBreaker(
            entity_id=uuid4(),
            entity_name="test-model",
            entity_type="model",
            config=config,
        )

        # Force half-open state
        breaker.state = CircuitBreakerState.HALF_OPEN

        # Failure during testing
        breaker.record_failure()

        # Should reopen
        assert breaker.state == CircuitBreakerState.OPEN

    def test_manual_reset(self):
        """Test manual circuit breaker reset."""
        config = CircuitBreakerConfig(failure_threshold=2)
        breaker = CircuitBreaker(
            entity_id=uuid4(),
            entity_name="test-model",
            entity_type="model",
            config=config,
        )

        # Open circuit
        breaker.record_failure()
        breaker.record_failure()
        assert breaker.is_open()

        # Manual reset
        breaker.reset()
        assert not breaker.is_open()
        assert breaker.state == CircuitBreakerState.CLOSED
        assert breaker.consecutive_failures == 0


class TestCircuitBreakerManager:
    """Test CircuitBreakerManager functionality."""

    def test_get_or_create(self):
        """Test get or create circuit breaker."""
        manager = CircuitBreakerManager()

        entity_id = uuid4()

        # Create new
        breaker1 = manager.get_or_create(
            entity_id=entity_id, entity_name="test", entity_type="model"
        )

        assert breaker1 is not None

        # Get existing
        breaker2 = manager.get_or_create(
            entity_id=entity_id, entity_name="test", entity_type="model"
        )

        assert breaker1 is breaker2

    def test_is_open(self):
        """Test checking if circuit is open."""
        manager = CircuitBreakerManager()

        entity_id = uuid4()
        breaker = manager.get_or_create(
            entity_id=entity_id,
            entity_name="test",
            entity_type="model",
            config=CircuitBreakerConfig(failure_threshold=2),
        )

        assert not manager.is_open(entity_id)

        # Open circuit
        breaker.record_failure()
        breaker.record_failure()

        assert manager.is_open(entity_id)

    def test_record_success(self):
        """Test recording success."""
        manager = CircuitBreakerManager()

        entity_id = uuid4()
        manager.get_or_create(
            entity_id=entity_id, entity_name="test", entity_type="model"
        )

        manager.record_success(entity_id)

        breaker = manager._breakers[entity_id]
        assert breaker.last_success_at is not None

    def test_record_failure(self):
        """Test recording failure."""
        manager = CircuitBreakerManager()

        entity_id = uuid4()
        manager.get_or_create(
            entity_id=entity_id, entity_name="test", entity_type="model"
        )

        manager.record_failure(entity_id)

        breaker = manager._breakers[entity_id]
        assert breaker.failure_count == 1

    def test_count_open(self):
        """Test counting open circuits."""
        manager = CircuitBreakerManager()

        # Create multiple breakers
        id1 = uuid4()
        id2 = uuid4()
        id3 = uuid4()

        config = CircuitBreakerConfig(failure_threshold=2)

        manager.get_or_create(id1, "test1", "model", config)
        manager.get_or_create(id2, "test2", "model", config)
        manager.get_or_create(id3, "test3", "model", config)

        # Open first two
        manager._breakers[id1].record_failure()
        manager._breakers[id1].record_failure()

        manager._breakers[id2].record_failure()
        manager._breakers[id2].record_failure()

        assert manager.count_open() == 2
        assert manager.count_total() == 3
