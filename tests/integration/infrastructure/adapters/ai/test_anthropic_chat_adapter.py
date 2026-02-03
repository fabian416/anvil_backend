"""
Integration tests for Anthropic Chat Adapter.

These tests require a valid Anthropic API key in environment.
"""

import pytest
import os
from decimal import Decimal

from app.infrastructure.adapters.ai.anthropic_chat_adapter import AnthropicChatAdapter
from app.domain.value_objects.llm import LLMRequest, LLMMessage
from app.domain.ports.chat_llm_provider import (
    AuthenticationError,
    InvalidRequestError,
    RateLimitError,
)


@pytest.fixture
def anthropic_adapter():
    """Create Anthropic adapter with API key from environment."""
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        pytest.skip("ANTHROPIC_API_KEY not set")

    return AnthropicChatAdapter(api_key=api_key, timeout=30)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_simple_completion(anthropic_adapter):
    """Test simple non-streaming completion."""
    request = LLMRequest(
        messages=[
            LLMMessage(role="user", content="Say 'Hello, World!' and nothing else.")
        ],
        model_id="claude-3-haiku-20240307",
        max_tokens=50,
        temperature=Decimal("0.0"),
    )

    response = await anthropic_adapter.complete(request)

    assert response.content
    assert "hello" in response.content.lower()
    assert response.provider == "anthropic"
    assert response.model_id.startswith("claude")
    assert response.input_tokens > 0
    assert response.output_tokens > 0
    assert response.latency_ms > 0
    assert response.cost_usd > 0
    assert response.finish_reason in ["stop", "end_turn"]


@pytest.mark.integration
@pytest.mark.asyncio
async def test_streaming_completion(anthropic_adapter):
    """Test streaming completion."""
    request = LLMRequest(
        messages=[LLMMessage(role="user", content="Count from 1 to 5.")],
        model_id="claude-3-haiku-20240307",
        max_tokens=100,
        temperature=Decimal("0.0"),
        stream=True,
    )

    chunks = []
    async for chunk in anthropic_adapter.complete_stream(request):
        chunks.append(chunk)

    full_response = "".join(chunks)
    assert full_response
    assert len(chunks) > 1  # Should have multiple chunks
    assert any(str(i) in full_response for i in range(1, 6))


@pytest.mark.integration
@pytest.mark.asyncio
async def test_conversation_with_system_message(anthropic_adapter):
    """Test conversation with system message."""
    request = LLMRequest(
        messages=[
            LLMMessage(
                role="system",
                content="You are a helpful assistant that responds in JSON format.",
            ),
            LLMMessage(role="user", content="What is 2+2? Respond with {result: X}"),
        ],
        model_id="claude-3-haiku-20240307",
        max_tokens=50,
        temperature=Decimal("0.0"),
    )

    response = await anthropic_adapter.complete(request)

    assert response.content
    assert "4" in response.content or "four" in response.content.lower()


@pytest.mark.integration
@pytest.mark.asyncio
async def test_cost_estimation(anthropic_adapter):
    """Test cost estimation."""
    cost = await anthropic_adapter.estimate_cost(
        input_tokens=1000, output_tokens=500, model="claude-3-haiku-20240307"
    )

    assert isinstance(cost, Decimal)
    assert cost > 0
    # Haiku is cheap
    assert cost < Decimal("0.01")


@pytest.mark.integration
@pytest.mark.asyncio
async def test_different_models(anthropic_adapter):
    """Test different model support."""
    # Test with the cheapest model that should be available
    request = LLMRequest(
        messages=[LLMMessage(role="user", content="Hello")],
        model_id="claude-3-haiku-20240307",
        max_tokens=20,
        temperature=Decimal("0.0"),
    )

    response = await anthropic_adapter.complete(request)
    assert response.content
    assert response.provider == "anthropic"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_max_tokens_limit(anthropic_adapter):
    """Test max_tokens limit is respected."""
    request = LLMRequest(
        messages=[LLMMessage(role="user", content="Write a long essay about Python.")],
        model_id="claude-3-haiku-20240307",
        max_tokens=10,  # Very low limit
        temperature=Decimal("0.5"),
    )

    response = await anthropic_adapter.complete(request)

    assert response.output_tokens <= 12  # Allow small margin
    assert response.finish_reason == "length"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_temperature_zero_deterministic(anthropic_adapter):
    """Test that temperature=0 gives deterministic results."""
    request = LLMRequest(
        messages=[LLMMessage(role="user", content="Say exactly: 'Test response'")],
        model_id="claude-3-haiku-20240307",
        max_tokens=20,
        temperature=Decimal("0.0"),
    )

    # Make same request twice
    response1 = await anthropic_adapter.complete(request)
    response2 = await anthropic_adapter.complete(request)

    # Responses should be very similar
    assert response1.content
    assert response2.content
    # At least some overlap in tokens
    assert (
        response1.output_tokens == response2.output_tokens
        or abs(response1.output_tokens - response2.output_tokens) <= 2
    )


@pytest.mark.integration
@pytest.mark.asyncio
async def test_health_check(anthropic_adapter):
    """Test health check endpoint."""
    health = await anthropic_adapter.health_check()

    assert health["status"] in ["healthy", "degraded", "down"]
    assert health["latency_ms"] > 0

    if health["status"] == "healthy":
        assert "available_models" in health
        assert len(health["available_models"]) > 0


@pytest.mark.integration
@pytest.mark.asyncio
async def test_multiline_response(anthropic_adapter):
    """Test handling of multiline responses."""
    request = LLMRequest(
        messages=[
            LLMMessage(
                role="user",
                content="Write a haiku about coding. Use proper formatting.",
            )
        ],
        model_id="claude-3-haiku-20240307",
        max_tokens=100,
        temperature=Decimal("0.7"),
    )

    response = await anthropic_adapter.complete(request)

    assert response.content
    # Haiku should have line breaks
    assert "\n" in response.content or len(response.content.split()) >= 10


@pytest.mark.integration
@pytest.mark.asyncio
async def test_context_manager(anthropic_adapter):
    """Test async context manager."""
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        pytest.skip("ANTHROPIC_API_KEY not set")

    async with AnthropicChatAdapter(api_key=api_key) as adapter:
        request = LLMRequest(
            messages=[LLMMessage(role="user", content="Hello")],
            model_id="claude-3-haiku-20240307",
            max_tokens=20,
            temperature=Decimal("0.0"),
        )

        response = await adapter.complete(request)
        assert response.content


@pytest.mark.integration
@pytest.mark.asyncio
async def test_provider_name_and_models(anthropic_adapter):
    """Test provider metadata."""
    assert anthropic_adapter.provider_name == "anthropic"
    assert len(anthropic_adapter.supported_models) > 0
    assert "claude-3-haiku-20240307" in anthropic_adapter.supported_models


@pytest.mark.integration
@pytest.mark.asyncio
async def test_long_conversation(anthropic_adapter):
    """Test multi-turn conversation."""
    request = LLMRequest(
        messages=[
            LLMMessage(role="user", content="What is 5 + 3?"),
            LLMMessage(role="assistant", content="5 + 3 equals 8."),
            LLMMessage(role="user", content="Now multiply that by 2."),
        ],
        model_id="claude-3-haiku-20240307",
        max_tokens=50,
        temperature=Decimal("0.0"),
    )

    response = await anthropic_adapter.complete(request)

    assert response.content
    assert "16" in response.content or "sixteen" in response.content.lower()
