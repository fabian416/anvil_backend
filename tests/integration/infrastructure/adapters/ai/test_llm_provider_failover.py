"""
Integration tests for LLM Provider Failover.

These tests require valid OpenAI and/or Anthropic API keys.
"""

import pytest
import os
from decimal import Decimal
from unittest.mock import AsyncMock, patch

from app.infrastructure.adapters.ai.llm_provider_failover import (
    LLMProviderFailover,
    ProviderConfig,
    CircuitBreaker,
    CircuitState,
    create_openai_anthropic_failover,
)
from app.infrastructure.adapters.ai.openai_chat_adapter import OpenAIChatAdapter
from app.infrastructure.adapters.ai.anthropic_chat_adapter import AnthropicChatAdapter
from app.domain.value_objects.llm import LLMRequest, LLMMessage
from app.domain.ports.chat_llm_provider import (
    ProviderUnavailableError,
    RateLimitError,
    TimeoutError,
)


@pytest.fixture
def openai_api_key():
    """Get OpenAI API key from environment."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        pytest.skip("OPENAI_API_KEY not set")
    return api_key


@pytest.fixture
def anthropic_api_key():
    """Get Anthropic API key from environment."""
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        pytest.skip("ANTHROPIC_API_KEY not set")
    return api_key


@pytest.fixture
def both_api_keys():
    """Require both API keys."""
    openai_key = os.getenv("OPENAI_API_KEY")
    anthropic_key = os.getenv("ANTHROPIC_API_KEY")

    if not openai_key or not anthropic_key:
        pytest.skip("Both OPENAI_API_KEY and ANTHROPIC_API_KEY required")

    return openai_key, anthropic_key


class TestCircuitBreaker:
    """Unit tests for circuit breaker."""

    def test_initial_state_closed(self):
        """Test circuit starts in closed state."""
        cb = CircuitBreaker(provider_name="test", failure_threshold=3)
        assert cb.state == CircuitState.CLOSED
        assert cb.can_attempt()

    def test_opens_after_threshold(self):
        """Test circuit opens after failure threshold."""
        cb = CircuitBreaker(provider_name="test", failure_threshold=3)

        for _ in range(2):
            cb.record_failure()
            assert cb.state == CircuitState.CLOSED

        cb.record_failure()  # Third failure
        assert cb.state == CircuitState.OPEN
        assert not cb.can_attempt()

    def test_half_open_after_timeout(self):
        """Test circuit goes to half-open after timeout."""
        cb = CircuitBreaker(
            provider_name="test", failure_threshold=2, timeout_seconds=0
        )

        cb.record_failure()
        cb.record_failure()
        assert cb.state == CircuitState.OPEN

        # With 0 timeout, should immediately go to half-open
        assert cb.can_attempt()
        assert cb.state == CircuitState.HALF_OPEN

    def test_closes_after_success_threshold(self):
        """Test circuit closes after success threshold in half-open."""
        cb = CircuitBreaker(
            provider_name="test",
            failure_threshold=2,
            success_threshold=2,
            timeout_seconds=0,
        )

        # Open the circuit
        cb.record_failure()
        cb.record_failure()
        assert cb.state == CircuitState.OPEN

        # Move to half-open
        cb.can_attempt()
        assert cb.state == CircuitState.HALF_OPEN

        # Record successes
        cb.record_success()
        assert cb.state == CircuitState.HALF_OPEN

        cb.record_success()
        assert cb.state == CircuitState.CLOSED

    def test_reopens_on_half_open_failure(self):
        """Test circuit reopens if failure occurs in half-open."""
        cb = CircuitBreaker(
            provider_name="test", failure_threshold=2, timeout_seconds=0
        )

        # Open the circuit
        cb.record_failure()
        cb.record_failure()
        cb.can_attempt()  # Move to half-open

        assert cb.state == CircuitState.HALF_OPEN

        # Fail during testing
        cb.record_failure()
        assert cb.state == CircuitState.OPEN


@pytest.mark.integration
@pytest.mark.asyncio
async def test_factory_function(both_api_keys):
    """Test factory function for creating failover."""
    openai_key, anthropic_key = both_api_keys

    failover = create_openai_anthropic_failover(
        openai_api_key=openai_key,
        anthropic_api_key=anthropic_key,
        primary="openai",
    )

    assert failover is not None
    assert len(failover._providers) == 2


@pytest.mark.integration
@pytest.mark.asyncio
async def test_primary_provider_success(both_api_keys):
    """Test successful completion with primary provider."""
    openai_key, anthropic_key = both_api_keys

    failover = create_openai_anthropic_failover(
        openai_api_key=openai_key,
        anthropic_api_key=anthropic_key,
        primary="openai",
    )

    request = LLMRequest(
        messages=[LLMMessage(role="user", content="Say 'test' and nothing else.")],
        model_id="gpt-3.5-turbo",
        max_tokens=20,
        temperature=Decimal("0.0"),
    )

    response = await failover.complete(request)

    assert response.content
    assert response.provider == "openai"  # Should use primary


@pytest.mark.integration
@pytest.mark.asyncio
async def test_provider_status(both_api_keys):
    """Test getting provider status."""
    openai_key, anthropic_key = both_api_keys

    failover = create_openai_anthropic_failover(
        openai_api_key=openai_key,
        anthropic_api_key=anthropic_key,
        primary="openai",
    )

    status = await failover.get_provider_status()

    assert "openai" in status
    assert "anthropic" in status

    for provider_name, provider_status in status.items():
        assert "priority" in provider_status
        assert "circuit_state" in provider_status
        assert provider_status["circuit_state"] == "closed"
        assert "health" in provider_status


@pytest.mark.integration
@pytest.mark.asyncio
async def test_streaming_with_failover(both_api_keys):
    """Test streaming completion with failover."""
    openai_key, anthropic_key = both_api_keys

    failover = create_openai_anthropic_failover(
        openai_api_key=openai_key,
        anthropic_api_key=anthropic_key,
        primary="openai",
    )

    request = LLMRequest(
        messages=[LLMMessage(role="user", content="Count from 1 to 3.")],
        model_id="gpt-3.5-turbo",
        max_tokens=50,
        temperature=Decimal("0.0"),
        stream=True,
    )

    chunks = []
    async for chunk in failover.complete_stream(request):
        chunks.append(chunk)

    full_response = "".join(chunks)
    assert full_response
    assert len(chunks) > 1


@pytest.mark.integration
@pytest.mark.asyncio
async def test_cost_fallback_model_mapping(both_api_keys):
    """Test that cost fallback uses cheaper models."""
    openai_key, anthropic_key = both_api_keys

    failover = create_openai_anthropic_failover(
        openai_api_key=openai_key,
        anthropic_api_key=anthropic_key,
        primary="openai",
        enable_cost_fallback=True,
    )

    # Check model mappings
    assert failover._get_fallback_model("gpt-4") == "gpt-4o-mini"
    assert failover._get_fallback_model("claude-opus-4-5") == "claude-3-haiku-20240307"
    assert failover._get_fallback_model("unknown-model") == "unknown-model"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_alternating_providers(both_api_keys):
    """Test alternating between providers works."""
    openai_key, anthropic_key = both_api_keys

    # Create with Anthropic as primary
    failover = create_openai_anthropic_failover(
        openai_api_key=openai_key,
        anthropic_api_key=anthropic_key,
        primary="anthropic",
    )

    request = LLMRequest(
        messages=[LLMMessage(role="user", content="Hello")],
        model_id="claude-3-haiku-20240307",
        max_tokens=20,
        temperature=Decimal("0.0"),
    )

    response = await failover.complete(request)
    assert response.content
    assert response.provider == "anthropic"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_failover_on_provider_error():
    """Test failover when primary provider fails (mocked)."""
    # Create mock providers
    failing_provider = AsyncMock()
    failing_provider.provider_name = "failing"
    failing_provider.complete = AsyncMock(
        side_effect=ProviderUnavailableError(
            "Service down", provider="failing", model="test"
        )
    )

    working_provider = AsyncMock()
    working_provider.provider_name = "working"
    from app.domain.value_objects.llm import LLMResponse

    working_provider.complete = AsyncMock(
        return_value=LLMResponse(
            content="Success",
            model_id="test",
            provider="working",
            input_tokens=10,
            output_tokens=5,
            latency_ms=100,
            finish_reason="stop",
        )
    )

    # Create failover with mocked providers
    failover = LLMProviderFailover(
        providers=[
            ProviderConfig(provider=failing_provider, priority=0),
            ProviderConfig(provider=working_provider, priority=1, is_fallback=True),
        ],
        max_retries=1,
    )

    request = LLMRequest(
        messages=[LLMMessage(role="user", content="Hello")],
        model_id="test",
        max_tokens=20,
        temperature=Decimal("0.0"),
    )

    response = await failover.complete(request)

    assert response.content == "Success"
    assert response.provider == "working"

    # Verify failing provider was tried
    failing_provider.complete.assert_called_once()
    # Verify working provider was used
    working_provider.complete.assert_called_once()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_circuit_breaker_prevents_attempts():
    """Test circuit breaker prevents attempts to failing provider."""
    # Create mock provider that always fails
    failing_provider = AsyncMock()
    failing_provider.provider_name = "failing"
    failing_provider.complete = AsyncMock(
        side_effect=ProviderUnavailableError(
            "Service down", provider="failing", model="test"
        )
    )

    working_provider = AsyncMock()
    working_provider.provider_name = "working"
    from app.domain.value_objects.llm import LLMResponse

    working_provider.complete = AsyncMock(
        return_value=LLMResponse(
            content="Success",
            model_id="test",
            provider="working",
            input_tokens=10,
            output_tokens=5,
            latency_ms=100,
            finish_reason="stop",
        )
    )

    failover = LLMProviderFailover(
        providers=[
            ProviderConfig(provider=failing_provider, priority=0),
            ProviderConfig(provider=working_provider, priority=1, is_fallback=True),
        ],
        failure_threshold=2,  # Open after 2 failures
        max_retries=1,
    )

    request = LLMRequest(
        messages=[LLMMessage(role="user", content="Hello")],
        model_id="test",
        max_tokens=20,
        temperature=Decimal("0.0"),
    )

    # First request - fails, tries fallback
    await failover.complete(request)

    # Second request - fails, tries fallback, circuit opens
    await failover.complete(request)

    # Third request - circuit is open, should skip failing provider
    await failover.complete(request)

    # Failing provider should only be called twice (before circuit opened)
    assert failing_provider.complete.call_count == 2

    # Working provider should be called for all 3 requests
    assert working_provider.complete.call_count == 3


@pytest.mark.unit
@pytest.mark.asyncio
async def test_all_providers_fail():
    """Test error when all providers fail."""
    provider1 = AsyncMock()
    provider1.provider_name = "provider1"
    provider1.complete = AsyncMock(
        side_effect=ProviderUnavailableError("Down", provider="provider1", model="test")
    )

    provider2 = AsyncMock()
    provider2.provider_name = "provider2"
    provider2.complete = AsyncMock(
        side_effect=ProviderUnavailableError("Down", provider="provider2", model="test")
    )

    failover = LLMProviderFailover(
        providers=[
            ProviderConfig(provider=provider1, priority=0),
            ProviderConfig(provider=provider2, priority=1),
        ],
        max_retries=1,
    )

    request = LLMRequest(
        messages=[LLMMessage(role="user", content="Hello")],
        model_id="test",
        max_tokens=20,
        temperature=Decimal("0.0"),
    )

    with pytest.raises(ProviderUnavailableError) as exc_info:
        await failover.complete(request)

    assert "All providers exhausted" in str(exc_info.value)
