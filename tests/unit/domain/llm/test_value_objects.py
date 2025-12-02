"""
Unit tests for LLM value objects.
"""

import pytest
from decimal import Decimal

from app.domain.value_objects.llm import (
    LLMRequest,
    LLMResponse,
    LLMMessage,
    ToolCall,
    RetryConfig,
)


class TestLLMMessage:
    """Test LLMMessage value object."""

    def test_create_message(self):
        """Test creating an LLM message."""
        msg = LLMMessage(role="user", content="Hello")

        assert msg.role == "user"
        assert msg.content == "Hello"
        assert msg.name is None


class TestLLMRequest:
    """Test LLMRequest value object."""

    def test_create_valid_request(self):
        """Test creating a valid LLM request."""
        request = LLMRequest(
            messages=[LLMMessage(role="user", content="Hello")],
            max_tokens=1000,
            temperature=Decimal("0.7"),
        )

        assert len(request.messages) == 1
        assert request.max_tokens == 1000
        assert request.temperature == Decimal("0.7")

    def test_request_requires_messages(self):
        """Test request validation requires messages."""
        with pytest.raises(ValueError, match="at least one message"):
            LLMRequest(messages=[], max_tokens=1000)

    def test_max_tokens_must_be_positive(self):
        """Test max_tokens validation."""
        with pytest.raises(ValueError, match="must be positive"):
            LLMRequest(
                messages=[LLMMessage(role="user", content="Hi")], max_tokens=0
            )

    def test_temperature_range_validation(self):
        """Test temperature must be 0-2."""
        with pytest.raises(ValueError, match="temperature"):
            LLMRequest(
                messages=[LLMMessage(role="user", content="Hi")],
                max_tokens=100,
                temperature=Decimal("3.0"),
            )

    def test_input_tokens_estimation(self):
        """Test input token estimation."""
        request = LLMRequest(
            messages=[
                LLMMessage(role="user", content="a" * 400)  # 400 chars ≈ 100 tokens
            ],
            max_tokens=1000,
        )

        assert request.input_tokens == 100

    def test_to_dict(self):
        """Test converting request to dict."""
        request = LLMRequest(
            messages=[LLMMessage(role="user", content="Hello")],
            max_tokens=1000,
        )

        data = request.to_dict()

        assert data["max_tokens"] == 1000
        assert len(data["messages"]) == 1
        assert data["messages"][0]["content"] == "Hello"


class TestLLMResponse:
    """Test LLMResponse value object."""

    def test_create_valid_response(self):
        """Test creating a valid LLM response."""
        response = LLMResponse(
            content="Hello!",
            model_id="gpt-4",
            provider="openai",
            input_tokens=100,
            output_tokens=50,
            latency_ms=1234,
            finish_reason="stop",
        )

        assert response.content == "Hello!"
        assert response.total_tokens == 150

    def test_tokens_must_be_non_negative(self):
        """Test token validation."""
        with pytest.raises(ValueError, match="non-negative"):
            LLMResponse(
                content="Hi",
                model_id="gpt-4",
                provider="openai",
                input_tokens=-1,
                output_tokens=50,
                latency_ms=100,
                finish_reason="stop",
            )

    def test_to_dict(self):
        """Test converting response to dict."""
        response = LLMResponse(
            content="Hello!",
            model_id="gpt-4",
            provider="openai",
            input_tokens=100,
            output_tokens=50,
            latency_ms=1234,
            finish_reason="stop",
        )

        data = response.to_dict()

        assert data["content"] == "Hello!"
        assert data["model_id"] == "gpt-4"
        assert data["input_tokens"] == 100


class TestRetryConfig:
    """Test RetryConfig value object."""

    def test_create_valid_config(self):
        """Test creating valid retry config."""
        config = RetryConfig(
            max_retries_per_provider=3,
            max_total_retries=9,
            initial_delay_ms=100,
            max_delay_ms=5000,
        )

        assert config.max_retries_per_provider == 3

    def test_max_delay_must_exceed_initial(self):
        """Test max_delay validation."""
        with pytest.raises(ValueError, match="max_delay_ms"):
            RetryConfig(initial_delay_ms=1000, max_delay_ms=500)

    def test_calculate_delay(self):
        """Test delay calculation."""
        config = RetryConfig(
            initial_delay_ms=100, max_delay_ms=5000, backoff_multiplier=2.0, jitter=False
        )

        # Attempt 0: 100ms
        assert config.calculate_delay(0) == 100

        # Attempt 1: 200ms
        assert config.calculate_delay(1) == 200

        # Attempt 2: 400ms
        assert config.calculate_delay(2) == 400

        # High attempt: capped at max
        assert config.calculate_delay(10) == 5000

    def test_calculate_delay_with_jitter(self):
        """Test delay calculation with jitter."""
        config = RetryConfig(
            initial_delay_ms=100, max_delay_ms=5000, backoff_multiplier=2.0, jitter=True
        )

        # With jitter, delay should be within ±25% of calculated value
        delay = config.calculate_delay(2)  # Base: 400ms

        assert 300 <= delay <= 500  # 400 ± 100
