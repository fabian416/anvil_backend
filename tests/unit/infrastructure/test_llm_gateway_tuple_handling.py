"""
Unit tests: LLMGatewayImpl correctly handles tuple returns from RetryHandler/LLMStrategy.

The bug was that DeepInfraStrategy returns (text, metadata) tuple, but 
LLMGatewayImpl was checking `isinstance(response_data, dict)` which is False for tuples,
causing the whole tuple to be stringified as "('text', {...})".
"""

import pytest
from unittest.mock import AsyncMock, MagicMock


@pytest.fixture
def mock_factory():
    """Create a mock LLMProviderFactory."""
    factory = MagicMock()
    return factory


@pytest.fixture
def gateway(mock_factory):
    """Create LLMGatewayImpl with mocked factory."""
    from app.infrastructure.adapters.ai.llm_gateway_impl import LLMGatewayImpl
    return LLMGatewayImpl(factory=mock_factory)


# ---------------------------------------------------------------------------
# Tuple handling (the main bug fix)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_generate_with_metadata_handles_tuple_correctly(gateway, mock_factory):
    """
    When RetryHandler returns a tuple (text, metadata), extract text properly.
    
    This was the bug: tuple was being stringified as "('text', {...})" 
    instead of extracting the first element.
    """
    # Simulate DeepInfra response format
    mock_strategy = AsyncMock()
    mock_strategy.generate.return_value = (
        "Hello, this is the LLM response!",
        {
            "provider": "deepinfra",
            "model": "meta-llama/Meta-Llama-3.1-70B-Instruct",
            "input_tokens": 50,
            "output_tokens": 100,
            "latency_ms": 1500,
            "cost_usd": 0.0001,
        }
    )
    
    mock_factory.get_strategy.return_value = mock_strategy
    
    text, metadata = await gateway.generate_with_metadata(
        model="meta-llama/Meta-Llama-3.1-70B-Instruct",
        messages=[{"role": "user", "content": "Hello"}],
    )
    
    # The text should be the first element of the tuple, NOT the tuple stringified
    assert text == "Hello, this is the LLM response!"
    assert "(" not in text  # Should not contain tuple representation
    assert "provider" not in text  # Should not contain metadata in text
    
    # Metadata should be properly extracted
    assert metadata["provider"] == "deepinfra"
    assert metadata["tokens_used"] == 150  # 50 + 100
    assert metadata["latency_ms"] == 1500


@pytest.mark.asyncio
async def test_generate_with_metadata_handles_spanish_response(gateway, mock_factory):
    """
    Test with Spanish response (as seen in the user's bug report).
    """
    spanish_response = "¡Hola! Bienvenido al mundo de DeFi (Finanzas Descentralizadas). Estoy aquí para ayudarte."
    
    mock_strategy = AsyncMock()
    mock_strategy.generate.return_value = (
        spanish_response,
        {
            "provider": "deepinfra",
            "model": "meta-llama/Meta-Llama-3.1-70B-Instruct",
            "input_tokens": 69,
            "output_tokens": 292,
            "latency_ms": 11237,
            "cost_usd": 0.00027139,
        }
    )
    
    mock_factory.get_strategy.return_value = mock_strategy
    
    text, metadata = await gateway.generate_with_metadata(
        model="meta-llama/Meta-Llama-3.1-70B-Instruct",
        messages=[{"role": "user", "content": "Hola"}],
    )
    
    # Critical: text should be the clean Spanish response
    assert text == spanish_response
    assert text.startswith("¡Hola!")
    assert "provider" not in text
    assert "deepinfra" not in text


@pytest.mark.asyncio
async def test_generate_still_handles_dict_format(gateway, mock_factory):
    """
    Ensure backward compatibility with dict return format.
    """
    mock_strategy = AsyncMock()
    mock_strategy.generate.return_value = {
        "content": "Response from dict format",
        "tokens_used": 100,
        "latency_ms": 500,
        "finish_reason": "stop",
    }
    
    mock_factory.get_strategy.return_value = mock_strategy
    
    text, metadata = await gateway.generate_with_metadata(
        model="some-model",
        messages=[{"role": "user", "content": "Hello"}],
    )
    
    assert text == "Response from dict format"
    assert metadata["tokens_used"] == 100


@pytest.mark.asyncio
async def test_generate_returns_only_text(gateway, mock_factory):
    """
    Test that generate() (without metadata) returns clean text.
    """
    mock_strategy = AsyncMock()
    mock_strategy.generate.return_value = (
        "Just the text please",
        {"provider": "test", "input_tokens": 10, "output_tokens": 20, "latency_ms": 100}
    )
    
    mock_factory.get_strategy.return_value = mock_strategy
    
    text = await gateway.generate(
        model="test-model",
        messages=[{"role": "user", "content": "Test"}],
    )
    
    assert text == "Just the text please"
    assert isinstance(text, str)

