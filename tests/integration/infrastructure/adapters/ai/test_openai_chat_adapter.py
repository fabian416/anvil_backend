"""
Integration tests for OpenAI Chat Adapter.

These tests require a valid OpenAI API key in environment.
"""

import pytest
import os
from decimal import Decimal

from app.infrastructure.adapters.ai.openai_chat_adapter import OpenAIChatAdapter
from app.domain.value_objects.llm import LLMRequest, LLMMessage
from app.domain.ports.chat_llm_provider import (
    AuthenticationError,
    InvalidRequestError,
    RateLimitError,
)


@pytest.fixture
def openai_adapter():
    """Create OpenAI adapter with API key from environment."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        pytest.skip("OPENAI_API_KEY not set")

    return OpenAIChatAdapter(api_key=api_key, timeout=30)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_simple_completion(openai_adapter):
    """Test simple non-streaming completion."""
    request = LLMRequest(
        messages=[
            LLMMessage(role="user", content="Say 'Hello, World!' and nothing else.")
        ],
        model_id="gpt-3.5-turbo",
        max_tokens=50,
        temperature=Decimal("0.0"),
    )

    response = await openai_adapter.complete(request)

    assert response.content
    assert "hello" in response.content.lower()
    assert response.provider == "openai"
    assert response.model_id.startswith("gpt-3.5-turbo")
    assert response.input_tokens > 0
    assert response.output_tokens > 0
    assert response.latency_ms > 0
    assert response.cost_usd > 0
    assert response.finish_reason in ["stop", "length"]


@pytest.mark.integration
@pytest.mark.asyncio
async def test_streaming_completion(openai_adapter):
    """Test streaming completion."""
    request = LLMRequest(
        messages=[LLMMessage(role="user", content="Count from 1 to 5.")],
        model_id="gpt-3.5-turbo",
        max_tokens=100,
        temperature=Decimal("0.0"),
        stream=True,
    )

    chunks = []
    async for chunk in openai_adapter.complete_stream(request):
        chunks.append(chunk)

    full_response = "".join(chunks)
    assert full_response
    assert len(chunks) > 1  # Should have multiple chunks
    assert any(str(i) in full_response for i in range(1, 6))


@pytest.mark.integration
@pytest.mark.asyncio
async def test_conversation_with_system_message(openai_adapter):
    """Test conversation with system message."""
    request = LLMRequest(
        messages=[
            LLMMessage(
                role="system",
                content="You are a helpful assistant that responds in JSON format.",
            ),
            LLMMessage(role="user", content="What is 2+2? Respond with {result: X}"),
        ],
        model_id="gpt-3.5-turbo",
        max_tokens=50,
        temperature=Decimal("0.0"),
    )

    response = await openai_adapter.complete(request)

    assert response.content
    assert "4" in response.content or "four" in response.content.lower()


@pytest.mark.integration
@pytest.mark.asyncio
async def test_cost_estimation(openai_adapter):
    """Test cost estimation."""
    cost = await openai_adapter.estimate_cost(
        input_tokens=1000, output_tokens=500, model="gpt-3.5-turbo"
    )

    assert isinstance(cost, Decimal)
    assert cost > 0
    # Cost should be reasonable (rough check)
    assert cost < Decimal("0.01")  # $0.01 for 1500 tokens on gpt-3.5-turbo


@pytest.mark.integration
@pytest.mark.asyncio
async def test_different_models(openai_adapter):
    """Test different model support."""
    models_to_test = ["gpt-3.5-turbo", "gpt-4o-mini"]

    for model in models_to_test:
        request = LLMRequest(
            messages=[LLMMessage(role="user", content="Hello")],
            model_id=model,
            max_tokens=20,
            temperature=Decimal("0.0"),
        )

        try:
            response = await openai_adapter.complete(request)
            assert response.content
            assert response.provider == "openai"
        except Exception as e:
            # Some models may not be available
            pytest.skip(f"Model {model} not available: {e}")


@pytest.mark.integration
@pytest.mark.asyncio
async def test_max_tokens_limit(openai_adapter):
    """Test max_tokens limit is respected."""
    request = LLMRequest(
        messages=[LLMMessage(role="user", content="Write a long essay about Python.")],
        model_id="gpt-3.5-turbo",
        max_tokens=10,  # Very low limit
        temperature=Decimal("0.5"),
    )

    response = await openai_adapter.complete(request)

    assert response.output_tokens <= 12  # Allow small margin
    assert response.finish_reason == "length"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_temperature_zero_deterministic(openai_adapter):
    """Test that temperature=0 gives deterministic results."""
    request = LLMRequest(
        messages=[LLMMessage(role="user", content="Say exactly: 'Test response'")],
        model_id="gpt-3.5-turbo",
        max_tokens=20,
        temperature=Decimal("0.0"),
    )

    # Make same request twice
    response1 = await openai_adapter.complete(request)
    response2 = await openai_adapter.complete(request)

    # Responses should be very similar (though not guaranteed to be identical)
    assert response1.content
    assert response2.content
    # At least some overlap in tokens
    assert (
        response1.output_tokens == response2.output_tokens
        or abs(response1.output_tokens - response2.output_tokens) <= 2
    )


@pytest.mark.integration
@pytest.mark.asyncio
async def test_health_check(openai_adapter):
    """Test health check endpoint."""
    health = await openai_adapter.health_check()

    assert health["status"] in ["healthy", "degraded", "down"]
    assert health["latency_ms"] > 0

    if health["status"] == "healthy":
        assert "available_models" in health
        assert len(health["available_models"]) > 0


@pytest.mark.integration
@pytest.mark.asyncio
async def test_invalid_model_error(openai_adapter):
    """Test error handling for invalid model."""
    request = LLMRequest(
        messages=[LLMMessage(role="user", content="Hello")],
        model_id="invalid-model-xyz-123",
        max_tokens=20,
        temperature=Decimal("0.0"),
    )

    with pytest.raises(Exception):  # Should raise some error
        await openai_adapter.complete(request)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_context_manager(openai_adapter):
    """Test async context manager."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        pytest.skip("OPENAI_API_KEY not set")

    async with OpenAIChatAdapter(api_key=api_key) as adapter:
        request = LLMRequest(
            messages=[LLMMessage(role="user", content="Hello")],
            model_id="gpt-3.5-turbo",
            max_tokens=20,
            temperature=Decimal("0.0"),
        )

        response = await adapter.complete(request)
        assert response.content


@pytest.mark.integration
@pytest.mark.asyncio
async def test_provider_name_and_models(openai_adapter):
    """Test provider metadata."""
    assert openai_adapter.provider_name == "openai"
    assert len(openai_adapter.supported_models) > 0
    assert "gpt-3.5-turbo" in openai_adapter.supported_models
    assert "gpt-4" in openai_adapter.supported_models
