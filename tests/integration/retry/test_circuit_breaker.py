"""
Integration tests for CircuitBreaker.

Tests state machine transitions, Redis integration, and telemetry tracking.
"""

import asyncio
import pytest
from unittest.mock import MagicMock, AsyncMock
from datetime import datetime, timedelta

from app.domain.services.retry.circuit_breaker import (
    CircuitBreaker,
    CircuitBreakerManager,
    CircuitBreakerConfig,
    CircuitState,
    CircuitBreakerOpenError,
)


class MockRedis:
    """Mock Redis client for testing."""
    
    def __init__(self):
        self.data = {}
    
    def get(self, key):
        value = self.data.get(key)
        if value is None:
            return None
        return value.encode() if isinstance(value, str) else str(value).encode()
    
    def set(self, key, value):
        self.data[key] = value
    
    def delete(self, key):
        if key in self.data:
            del self.data[key]
    
    def incr(self, key):
        current = int(self.data.get(key, 0))
        self.data[key] = current + 1
        return self.data[key]
    
    def ttl(self, key):
        # Simplified: always return -1 (no expiration)
        return -1
    
    def keys(self, pattern):
        # Simplified: return all keys
        return [k.encode() if isinstance(k, str) else k for k in self.data.keys()]


class TestCircuitBreaker:
    """Test CircuitBreaker."""
    
    def test_initial_state_is_closed(self):
        """Test circuit breaker starts in CLOSED state."""
        # Arrange
        redis = MockRedis()
        config = CircuitBreakerConfig(failure_threshold=3)
        cb = CircuitBreaker(redis, config)
        
        # Act
        is_open = cb.is_open("test_service")
        
        # Assert
        assert not is_open
        assert cb._get_state("test_service") == CircuitState.CLOSED
    
    def test_record_success_in_closed_state(self):
        """Test recording success in CLOSED state."""
        # Arrange
        redis = MockRedis()
        cb = CircuitBreaker(redis)
        
        # Simulate some failures first
        redis.set("circuit:test_service:failures", 2)
        
        # Act
        cb.record_success("test_service")
        
        # Assert
        failures = cb._get_counter("circuit:test_service:failures")
        assert failures == 0  # Should reset failure counter
    
    def test_transition_to_open_on_failure_threshold(self):
        """Test circuit opens when failure threshold exceeded."""
        # Arrange
        redis = MockRedis()
        config = CircuitBreakerConfig(failure_threshold=3)
        cb = CircuitBreaker(redis, config)
        
        # Act - Record 3 failures
        for i in range(3):
            cb.record_failure("test_service")
        
        # Assert
        state = cb._get_state("test_service")
        assert state == CircuitState.OPEN
        assert cb.is_open("test_service")
    
    def test_circuit_stays_closed_below_threshold(self):
        """Test circuit stays closed below failure threshold."""
        # Arrange
        redis = MockRedis()
        config = CircuitBreakerConfig(failure_threshold=5)
        cb = CircuitBreaker(redis, config)
        
        # Act - Record 4 failures (below threshold)
        for i in range(4):
            cb.record_failure("test_service")
        
        # Assert
        state = cb._get_state("test_service")
        assert state == CircuitState.CLOSED
        assert not cb.is_open("test_service")
    
    def test_transition_to_half_open_after_timeout(self):
        """Test circuit transitions to HALF_OPEN after timeout."""
        # Arrange
        redis = MockRedis()
        config = CircuitBreakerConfig(
            failure_threshold=2,
            timeout_seconds=60,
        )
        cb = CircuitBreaker(redis, config)
        
        # Open the circuit
        cb.record_failure("test_service")
        cb.record_failure("test_service")
        assert cb._get_state("test_service") == CircuitState.OPEN
        
        # Simulate timeout expired
        past_time = (datetime.utcnow() - timedelta(seconds=61)).isoformat()
        redis.set("circuit:test_service:opened_at", past_time)
        
        # Act
        is_open = cb.is_open("test_service")
        
        # Assert
        assert not is_open  # Returns False because it transitions to HALF_OPEN
        assert cb._get_state("test_service") == CircuitState.HALF_OPEN
    
    def test_success_in_half_open_closes_circuit(self):
        """Test successes in HALF_OPEN state close circuit."""
        # Arrange
        redis = MockRedis()
        config = CircuitBreakerConfig(success_threshold=2)
        cb = CircuitBreaker(redis, config)
        
        # Set to HALF_OPEN
        redis.set("circuit:test_service:state", CircuitState.HALF_OPEN.value)
        
        # Act - Record 2 successes
        cb.record_success("test_service")
        cb.record_success("test_service")
        
        # Assert
        assert cb._get_state("test_service") == CircuitState.CLOSED
    
    def test_failure_in_half_open_reopens_circuit(self):
        """Test failure in HALF_OPEN immediately reopens circuit."""
        # Arrange
        redis = MockRedis()
        cb = CircuitBreaker(redis)
        
        # Set to HALF_OPEN
        redis.set("circuit:test_service:state", CircuitState.HALF_OPEN.value)
        
        # Act
        cb.record_failure("test_service")
        
        # Assert
        assert cb._get_state("test_service") == CircuitState.OPEN
    
    def test_manual_reset(self):
        """Test manual reset of circuit breaker."""
        # Arrange
        redis = MockRedis()
        config = CircuitBreakerConfig(failure_threshold=2)
        cb = CircuitBreaker(redis, config)
        
        # Open the circuit
        cb.record_failure("test_service")
        cb.record_failure("test_service")
        assert cb._get_state("test_service") == CircuitState.OPEN
        
        # Act
        cb.reset("test_service")
        
        # Assert
        assert cb._get_state("test_service") == CircuitState.CLOSED
        assert cb._get_counter("circuit:test_service:failures") == 0
    
    def test_get_status(self):
        """Test getting circuit breaker status."""
        # Arrange
        redis = MockRedis()
        config = CircuitBreakerConfig(
            failure_threshold=5,
            success_threshold=2,
            timeout_seconds=60,
        )
        cb = CircuitBreaker(redis, config)
        
        # Set some state
        redis.set("circuit:test_service:state", CircuitState.OPEN.value)
        redis.set("circuit:test_service:failures", 5)
        redis.set("circuit:test_service:opened_at", datetime.utcnow().isoformat())
        
        # Act
        status = cb.get_status("test_service")
        
        # Assert
        assert status["service_name"] == "test_service"
        assert status["state"] == "open"
        assert status["failure_count"] == 5
        assert status["opened_at"] is not None
        assert status["config"]["failure_threshold"] == 5
        assert status["config"]["success_threshold"] == 2
        assert status["config"]["timeout_seconds"] == 60
    
    @pytest.mark.asyncio
    async def test_telemetry_on_state_transitions(self):
        """Test telemetry is recorded on state transitions."""
        # Arrange
        redis = MockRedis()
        config = CircuitBreakerConfig(failure_threshold=2)
        mock_telemetry = AsyncMock()

        cb = CircuitBreaker(redis, config, telemetry=mock_telemetry)

        # Act - Transition to OPEN
        cb.record_failure("test_service")
        cb.record_failure("test_service")

        # Give async tasks time to complete
        await asyncio.sleep(0.1)

        # Assert
        mock_telemetry.record_circuit_breaker_event.assert_called_once()
        call_args = mock_telemetry.record_circuit_breaker_event.call_args
        assert call_args[0][0] == "test_service"
        assert call_args[0][1] == "opened"
        assert call_args[0][2]["reason"] == "failure_threshold_exceeded"


class TestCircuitBreakerManager:
    """Test CircuitBreakerManager."""
    
    def test_get_or_create_breaker(self):
        """Test get or create circuit breaker."""
        # Arrange
        redis = MockRedis()
        manager = CircuitBreakerManager(redis)
        
        # Act
        breaker1 = manager.get_or_create("service1")
        breaker2 = manager.get_or_create("service1")
        breaker3 = manager.get_or_create("service2")
        
        # Assert
        assert breaker1 is breaker2  # Same instance
        assert breaker1 is not breaker3  # Different instance
    
    def test_is_open_delegates_to_breaker(self):
        """Test is_open delegates to circuit breaker."""
        # Arrange
        redis = MockRedis()
        config = CircuitBreakerConfig(failure_threshold=2)
        manager = CircuitBreakerManager(redis, config)
        
        # Open the circuit
        manager.record_failure("test_service")
        manager.record_failure("test_service")
        
        # Act
        is_open = manager.is_open("test_service")
        
        # Assert
        assert is_open
    
    def test_record_success_delegates_to_breaker(self):
        """Test record_success delegates to circuit breaker."""
        # Arrange
        redis = MockRedis()
        manager = CircuitBreakerManager(redis)
        
        # Act
        manager.record_success("test_service")
        
        # Assert
        breaker = manager.get_or_create("test_service")
        failures = breaker._get_counter("circuit:test_service:failures")
        assert failures == 0
    
    def test_record_failure_delegates_to_breaker(self):
        """Test record_failure delegates to circuit breaker."""
        # Arrange
        redis = MockRedis()
        manager = CircuitBreakerManager(redis)
        
        # Act
        manager.record_failure("test_service")
        
        # Assert
        breaker = manager.get_or_create("test_service")
        failures = breaker._get_counter("circuit:test_service:failures")
        assert failures == 1
    
    def test_reset_delegates_to_breaker(self):
        """Test reset delegates to circuit breaker."""
        # Arrange
        redis = MockRedis()
        config = CircuitBreakerConfig(failure_threshold=2)
        manager = CircuitBreakerManager(redis, config)
        
        # Open the circuit
        manager.record_failure("test_service")
        manager.record_failure("test_service")
        
        # Act
        manager.reset("test_service")
        
        # Assert
        assert not manager.is_open("test_service")
    
    def test_get_all_statuses(self):
        """Test getting all circuit breaker statuses."""
        # Arrange
        redis = MockRedis()
        config = CircuitBreakerConfig(failure_threshold=2)
        manager = CircuitBreakerManager(redis, config)
        
        # Create some breakers with different states
        manager.record_failure("service1")
        manager.record_failure("service1")  # OPEN
        
        manager.record_failure("service2")  # CLOSED (below threshold)
        
        redis.set("circuit:service3:state", CircuitState.HALF_OPEN.value)
        
        # Act
        statuses = manager.get_all_statuses()
        
        # Assert
        assert len(statuses) >= 2  # At least service1 and service2
        assert "service1" in statuses
        assert statuses["service1"]["state"] == "open"
    
    def test_count_open_breakers(self):
        """Test counting open circuit breakers."""
        # Arrange
        redis = MockRedis()
        config = CircuitBreakerConfig(failure_threshold=2)
        manager = CircuitBreakerManager(redis, config)
        
        # Create some breakers
        manager.record_failure("service1")
        manager.record_failure("service1")  # OPEN
        
        manager.record_failure("service2")
        manager.record_failure("service2")  # OPEN
        
        manager.record_failure("service3")  # CLOSED
        
        # Act
        open_count = manager.count_open()
        
        # Assert
        assert open_count == 2
    
    def test_multiple_services_independent_state(self):
        """Test multiple services maintain independent state."""
        # Arrange
        redis = MockRedis()
        config = CircuitBreakerConfig(failure_threshold=2)
        manager = CircuitBreakerManager(redis, config)
        
        # Act
        # Open service1
        manager.record_failure("service1")
        manager.record_failure("service1")
        
        # service2 stays closed
        manager.record_failure("service2")
        
        # Assert
        assert manager.is_open("service1")
        assert not manager.is_open("service2")
