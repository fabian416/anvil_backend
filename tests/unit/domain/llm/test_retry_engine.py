"""
Unit tests for Retry Engine.
"""

import pytest
import asyncio
from unittest.mock import AsyncMock

from app.domain.services.llm.retry_engine import (
    RetryEngine,
    AllProvidersExhaustedException,
)
from app.domain.value_objects.llm import RetryConfig
from app.domain.ports.llm_provider_port import (
    RetryableError,
    NonRetryableError,
)


class TestRetryEngine:
    """Test RetryEngine functionality."""

    def test_calculate_backoff(self):
        """Test backoff calculation."""
        config = RetryConfig(
            initial_delay_ms=100,
            max_delay_ms=5000,
            backoff_multiplier=2.0,
            jitter=False,  # Disable jitter for predictable testing
        )

        engine = RetryEngine(config=config)

        # Attempt 0: 100ms
        assert engine.calculate_backoff(0) == pytest.approx(0.1, rel=0.1)

        # Attempt 1: 200ms
        assert engine.calculate_backoff(1) == pytest.approx(0.2, rel=0.1)

        # Attempt 2: 400ms
        assert engine.calculate_backoff(2) == pytest.approx(0.4, rel=0.1)

        # Attempt 3: 800ms
        assert engine.calculate_backoff(3) == pytest.approx(0.8, rel=0.1)

        # High attempt: capped at max_delay_ms
        assert engine.calculate_backoff(10) <= 5.0

    def test_should_retry_retryable_error(self):
        """Test should_retry returns True for RetryableError."""
        engine = RetryEngine()

        assert engine.should_retry(RetryableError("test"))

    def test_should_not_retry_non_retryable_error(self):
        """Test should_retry returns False for NonRetryableError."""
        engine = RetryEngine()

        assert not engine.should_retry(NonRetryableError("test"))

    def test_classify_error(self):
        """Test error classification."""
        engine = RetryEngine()

        assert engine.classify_error(Exception("rate limit exceeded")) == "rate_limit"
        assert engine.classify_error(Exception("request timed out")) == "timeout"
        assert engine.classify_error(Exception("503 service unavailable")) == "service_unavailable"
        assert engine.classify_error(Exception("authentication failed")) == "authentication_error"
        assert engine.classify_error(Exception("400 invalid request")) == "invalid_request"
        assert engine.classify_error(Exception("unknown error")) == "internal_error"

    @pytest.mark.asyncio
    async def test_execute_with_retry_success_first_attempt(self):
        """Test successful execution on first attempt."""
        engine = RetryEngine()

        # Mock function that succeeds
        async def mock_func(model):
            return "success"

        models = [{"model_id": "model1", "provider": "test"}]

        result = await engine.execute_with_retry(func=mock_func, models=models)

        assert result == "success"

    @pytest.mark.asyncio
    async def test_execute_with_retry_success_after_retry(self):
        """Test successful execution after retry."""
        config = RetryConfig(max_retries_per_provider=3, initial_delay_ms=10, jitter=False)
        engine = RetryEngine(config=config)

        # Mock function that fails twice then succeeds
        call_count = 0

        async def mock_func(model):
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise RetryableError("temporary failure")
            return "success"

        models = [{"model_id": "model1", "provider": "test"}]

        result = await engine.execute_with_retry(func=mock_func, models=models)

        assert result == "success"
        assert call_count == 3

    @pytest.mark.asyncio
    async def test_execute_with_retry_carousel_fallback(self):
        """Test carousel fallback to next model."""
        config = RetryConfig(max_retries_per_provider=2, initial_delay_ms=10, jitter=False)
        engine = RetryEngine(config=config)

        # Mock function that fails on first model, succeeds on second
        async def mock_func(model):
            if model["model_id"] == "model1":
                raise RetryableError("model1 failed")
            return f"success with {model['model_id']}"

        models = [
            {"model_id": "model1", "provider": "provider1"},
            {"model_id": "model2", "provider": "provider2"},
        ]

        result = await engine.execute_with_retry(func=mock_func, models=models)

        assert result == "success with model2"

    @pytest.mark.asyncio
    async def test_execute_with_retry_all_exhausted(self):
        """Test all retries exhausted raises exception."""
        config = RetryConfig(max_retries_per_provider=2, max_total_retries=4, initial_delay_ms=10)
        engine = RetryEngine(config=config)

        # Mock function that always fails
        async def mock_func(model):
            raise RetryableError("always fails")

        models = [
            {"model_id": "model1", "provider": "provider1"},
            {"model_id": "model2", "provider": "provider2"},
        ]

        with pytest.raises(AllProvidersExhaustedException):
            await engine.execute_with_retry(func=mock_func, models=models)

    @pytest.mark.asyncio
    async def test_execute_with_retry_non_retryable_error(self):
        """Test non-retryable error stops retries."""
        engine = RetryEngine()

        # Mock function that raises non-retryable error
        async def mock_func(model):
            raise NonRetryableError("invalid request")

        models = [
            {"model_id": "model1", "provider": "provider1"},
            {"model_id": "model2", "provider": "provider2"},
        ]

        # Should raise after first model (skip to next)
        with pytest.raises(AllProvidersExhaustedException):
            await engine.execute_with_retry(func=mock_func, models=models)

    @pytest.mark.asyncio
    async def test_on_attempt_callback(self):
        """Test on_attempt callback is called."""
        engine = RetryEngine()

        attempts = []

        async def on_attempt(attempt, model, is_retry):
            attempts.append((attempt, model["model_id"], is_retry))

        async def mock_func(model):
            return "success"

        models = [{"model_id": "model1", "provider": "test"}]

        await engine.execute_with_retry(
            func=mock_func, models=models, on_attempt=on_attempt
        )

        assert len(attempts) == 1
        assert attempts[0][0] == 1  # Attempt 1
        assert attempts[0][1] == "model1"
        assert attempts[0][2] is False  # Not a retry


class TestCircuitBreakerManager:
    """Test CircuitBreakerManager functionality."""

    def test_create_and_retrieve(self):
        """Test creating and retrieving circuit breakers."""
        manager = CircuitBreakerManager()

        entity_id = uuid4()
        breaker = manager.get_or_create(
            entity_id=entity_id, entity_name="test", entity_type="model"
        )

        assert breaker is not None
        assert breaker.entity_id == entity_id

        # Get same breaker
        breaker2 = manager.get_or_create(
            entity_id=entity_id, entity_name="test", entity_type="model"
        )

        assert breaker is breaker2

    def test_count_statistics(self):
        """Test counting circuit breakers."""
        manager = CircuitBreakerManager()

        # Create 3 breakers, open 2
        config = CircuitBreakerConfig(failure_threshold=1)

        id1 = uuid4()
        id2 = uuid4()
        id3 = uuid4()

        manager.get_or_create(id1, "test1", "model", config)
        manager.get_or_create(id2, "test2", "model", config)
        manager.get_or_create(id3, "test3", "model", config)

        # Open first two
        manager.record_failure(id1)
        manager.record_failure(id2)

        assert manager.count_total() == 3
        assert manager.count_open() == 2
