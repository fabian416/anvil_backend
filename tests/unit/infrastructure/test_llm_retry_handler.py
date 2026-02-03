"""
Unit tests for LLM retry handler.

Tests chain of responsibility pattern for retries.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock


@pytest.mark.unit
class TestRetryHandlerStructure:
    """Tests for RetryHandler structure and initialization."""

    def test_retry_handler_exists(self):
        """Test RetryHandler class exists."""
        from app.infrastructure.adapters.ai.llm.retry_handler import RetryHandler

        assert RetryHandler is not None

    def test_retry_handler_instantiation(self):
        """Test retry handler can be instantiated."""
        from app.infrastructure.adapters.ai.llm.retry_handler import RetryHandler

        mock_strategy = AsyncMock()
        handler = RetryHandler(mock_strategy)

        assert handler is not None
        assert handler._strategy is mock_strategy
        assert handler._next_handler is None

    def test_retry_handler_with_next_handler(self):
        """Test retry handler with next handler in chain."""
        from app.infrastructure.adapters.ai.llm.retry_handler import RetryHandler

        mock_strategy1 = AsyncMock()
        mock_strategy2 = AsyncMock()

        handler2 = RetryHandler(mock_strategy2)
        handler1 = RetryHandler(mock_strategy1, next_handler=handler2)

        assert handler1._next_handler is handler2
        assert handler2._next_handler is None


@pytest.mark.unit
@pytest.mark.asyncio
class TestRetryHandlerSuccess:
    """Tests for successful retry handler execution."""

    async def test_handle_successful_on_first_try(self):
        """Test handle succeeds on first strategy."""
        from app.infrastructure.adapters.ai.llm.retry_handler import RetryHandler

        # Arrange
        mock_strategy = AsyncMock()
        mock_strategy.generate.return_value = ("Generated response", {"tokens": 100})

        handler = RetryHandler(mock_strategy)

        # Act
        result, metadata = await handler.handle(
            "gpt-4", [{"role": "user", "content": "Hello"}]
        )

        # Assert
        assert result == "Generated response"
        assert metadata == {"tokens": 100}
        mock_strategy.generate.assert_called_once()

    async def test_handle_with_kwargs(self):
        """Test handle passes kwargs to strategy."""
        from app.infrastructure.adapters.ai.llm.retry_handler import RetryHandler

        # Arrange
        mock_strategy = AsyncMock()
        mock_strategy.generate.return_value = ("Response", {})

        handler = RetryHandler(mock_strategy)

        # Act
        await handler.handle(
            "claude-3",
            [{"role": "user", "content": "Test"}],
            temperature=0.7,
            max_tokens=500,
        )

        # Assert
        mock_strategy.generate.assert_called_once_with(
            "claude-3",
            [{"role": "user", "content": "Test"}],
            temperature=0.7,
            max_tokens=500,
        )


@pytest.mark.unit
@pytest.mark.asyncio
class TestRetryHandlerFailureAndRetry:
    """Tests for retry handler failure and retry logic."""

    async def test_handle_retries_on_failure(self):
        """Test handle retries with next handler on failure."""
        from app.infrastructure.adapters.ai.llm.retry_handler import RetryHandler

        # Arrange
        mock_strategy1 = AsyncMock()
        mock_strategy1.generate.side_effect = Exception("Strategy 1 failed")

        mock_strategy2 = AsyncMock()
        mock_strategy2.generate.return_value = (
            "Fallback response",
            {"provider": "fallback"},
        )

        handler2 = RetryHandler(mock_strategy2)
        handler1 = RetryHandler(mock_strategy1, next_handler=handler2)

        # Act
        result, metadata = await handler1.handle(
            "model", [{"role": "user", "content": "Test"}]
        )

        # Assert
        assert result == "Fallback response"
        assert metadata["provider"] == "fallback"
        mock_strategy1.generate.assert_called_once()
        mock_strategy2.generate.assert_called_once()

    async def test_handle_raises_if_all_handlers_fail(self):
        """Test handle raises exception if all handlers fail."""
        from app.infrastructure.adapters.ai.llm.retry_handler import RetryHandler

        # Arrange
        mock_strategy1 = AsyncMock()
        mock_strategy1.generate.side_effect = Exception("Strategy 1 failed")

        mock_strategy2 = AsyncMock()
        mock_strategy2.generate.side_effect = Exception("Strategy 2 failed")

        handler2 = RetryHandler(mock_strategy2)
        handler1 = RetryHandler(mock_strategy1, next_handler=handler2)

        # Act & Assert
        with pytest.raises(Exception, match="Strategy 2 failed"):
            await handler1.handle("model", [{"role": "user", "content": "Test"}])

    async def test_handle_three_level_chain(self):
        """Test handle with three-level retry chain."""
        from app.infrastructure.adapters.ai.llm.retry_handler import RetryHandler

        # Arrange
        mock_strategy1 = AsyncMock()
        mock_strategy1.generate.side_effect = Exception("Strategy 1 failed")

        mock_strategy2 = AsyncMock()
        mock_strategy2.generate.side_effect = Exception("Strategy 2 failed")

        mock_strategy3 = AsyncMock()
        mock_strategy3.generate.return_value = ("Final fallback", {"attempt": 3})

        handler3 = RetryHandler(mock_strategy3)
        handler2 = RetryHandler(mock_strategy2, next_handler=handler3)
        handler1 = RetryHandler(mock_strategy1, next_handler=handler2)

        # Act
        result, metadata = await handler1.handle("model", [])

        # Assert
        assert result == "Final fallback"
        assert metadata["attempt"] == 3
        mock_strategy1.generate.assert_called_once()
        mock_strategy2.generate.assert_called_once()
        mock_strategy3.generate.assert_called_once()


@pytest.mark.unit
@pytest.mark.asyncio
class TestRetryHandlerEdgeCases:
    """Tests for retry handler edge cases."""

    async def test_handle_with_empty_messages(self):
        """Test handle with empty messages list."""
        from app.infrastructure.adapters.ai.llm.retry_handler import RetryHandler

        # Arrange
        mock_strategy = AsyncMock()
        mock_strategy.generate.return_value = ("Empty response", {})

        handler = RetryHandler(mock_strategy)

        # Act
        result, metadata = await handler.handle("model", [])

        # Assert
        assert result == "Empty response"

    async def test_handle_with_none_model_name(self):
        """Test handle with None model name."""
        from app.infrastructure.adapters.ai.llm.retry_handler import RetryHandler

        # Arrange
        mock_strategy = AsyncMock()
        mock_strategy.generate.return_value = ("Response", {})

        handler = RetryHandler(mock_strategy)

        # Act
        result, metadata = await handler.handle(
            None, [{"role": "user", "content": "Test"}]
        )

        # Assert
        assert result == "Response"
        mock_strategy.generate.assert_called_once_with(
            None, [{"role": "user", "content": "Test"}]
        )

    async def test_handle_preserves_exception_type(self):
        """Test handle preserves original exception type."""
        from app.infrastructure.adapters.ai.llm.retry_handler import RetryHandler

        # Arrange
        class CustomError(Exception):
            pass

        mock_strategy = AsyncMock()
        mock_strategy.generate.side_effect = CustomError("Custom error")

        handler = RetryHandler(mock_strategy)

        # Act & Assert
        with pytest.raises(CustomError, match="Custom error"):
            await handler.handle("model", [])

    async def test_handle_with_complex_metadata(self):
        """Test handle with complex metadata structure."""
        from app.infrastructure.adapters.ai.llm.retry_handler import RetryHandler

        # Arrange
        complex_metadata = {
            "tokens": 150,
            "cost": 0.003,
            "latency_ms": 1250,
            "provider": "openai",
            "model_version": "gpt-4-0613",
            "nested": {"cache_hit": False, "retry_count": 0},
        }

        mock_strategy = AsyncMock()
        mock_strategy.generate.return_value = ("Response", complex_metadata)

        handler = RetryHandler(mock_strategy)

        # Act
        result, metadata = await handler.handle("gpt-4", [])

        # Assert
        assert metadata == complex_metadata
        assert metadata["nested"]["cache_hit"] is False


@pytest.mark.unit
@pytest.mark.asyncio
class TestRetryHandlerChainBehavior:
    """Tests for chain of responsibility behavior."""

    async def test_chain_stops_at_first_success(self):
        """Test chain stops processing at first successful handler."""
        from app.infrastructure.adapters.ai.llm.retry_handler import RetryHandler

        # Arrange
        mock_strategy1 = AsyncMock()
        mock_strategy1.generate.return_value = ("Success from handler 1", {})

        mock_strategy2 = AsyncMock()
        mock_strategy2.generate.return_value = ("Should not be called", {})

        handler2 = RetryHandler(mock_strategy2)
        handler1 = RetryHandler(mock_strategy1, next_handler=handler2)

        # Act
        result, metadata = await handler1.handle("model", [])

        # Assert
        assert result == "Success from handler 1"
        mock_strategy1.generate.assert_called_once()
        mock_strategy2.generate.assert_not_called()

    async def test_chain_passes_same_parameters(self):
        """Test chain passes same parameters to all handlers."""
        from app.infrastructure.adapters.ai.llm.retry_handler import RetryHandler

        # Arrange
        mock_strategy1 = AsyncMock()
        mock_strategy1.generate.side_effect = Exception("Failed")

        mock_strategy2 = AsyncMock()
        mock_strategy2.generate.return_value = ("Success", {})

        handler2 = RetryHandler(mock_strategy2)
        handler1 = RetryHandler(mock_strategy1, next_handler=handler2)

        messages = [{"role": "user", "content": "Test"}]
        kwargs = {"temperature": 0.8, "max_tokens": 200}

        # Act
        await handler1.handle("gpt-4", messages, **kwargs)

        # Assert
        mock_strategy1.generate.assert_called_once_with("gpt-4", messages, **kwargs)
        mock_strategy2.generate.assert_called_once_with("gpt-4", messages, **kwargs)

    async def test_single_handler_chain(self):
        """Test chain with only one handler."""
        from app.infrastructure.adapters.ai.llm.retry_handler import RetryHandler

        # Arrange
        mock_strategy = AsyncMock()
        mock_strategy.generate.return_value = ("Single handler response", {})

        handler = RetryHandler(mock_strategy)

        # Act
        result, metadata = await handler.handle("model", [])

        # Assert
        assert result == "Single handler response"
        assert handler._next_handler is None
