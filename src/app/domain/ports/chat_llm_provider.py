"""
Chat LLM Provider Port.

Defines the interface for chat-focused LLM providers (OpenAI, Anthropic).
This is distinct from the general LLM provider port which supports broader use cases.
"""

from typing import Protocol, AsyncIterator, Dict, Any, Optional
from decimal import Decimal

from app.domain.value_objects.llm import LLMRequest, LLMResponse


class ChatLLMProvider(Protocol):
    """
    Abstract interface for chat-focused LLM providers.

    Supports both OpenAI and Anthropic APIs with unified interface.
    Providers must implement both streaming and non-streaming completions.
    """

    @property
    def provider_name(self) -> str:
        """Get provider name (openai, anthropic)."""
        ...

    @property
    def supported_models(self) -> list[str]:
        """Get list of supported model IDs."""
        ...

    async def complete(self, request: LLMRequest) -> LLMResponse:
        """
        Execute non-streaming chat completion.

        Args:
            request: LLM request with messages and parameters

        Returns:
            LLM response with content and metadata

        Raises:
            ChatProviderError: For provider-specific errors
            RateLimitError: For rate limit errors (429)
            TimeoutError: For timeout errors
            AuthenticationError: For auth errors (401)
            InvalidRequestError: For invalid requests (400)
        """
        ...

    async def complete_stream(self, request: LLMRequest) -> AsyncIterator[str]:
        """
        Execute streaming chat completion.

        Args:
            request: LLM request (with stream=True)

        Yields:
            Content chunks as they arrive from the provider

        Raises:
            ChatProviderError: For provider-specific errors
            RateLimitError: For rate limit errors (429)
            TimeoutError: For timeout errors
            AuthenticationError: For auth errors (401)
            InvalidRequestError: For invalid requests (400)
        """
        ...

    async def estimate_cost(
        self, input_tokens: int, output_tokens: int, model: str
    ) -> Decimal:
        """
        Estimate cost for given token usage.

        Args:
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
            model: Model identifier

        Returns:
            Estimated cost in USD
        """
        ...

    async def health_check(self) -> Dict[str, Any]:
        """
        Check provider health status.

        Returns:
            Health status dictionary with:
            - status: 'healthy', 'degraded', or 'down'
            - latency_ms: Response time for health check
            - message: Optional status message
            - available_models: List of currently available models
        """
        ...


# ============================================================================
# EXCEPTIONS
# ============================================================================


class ChatProviderError(Exception):
    """Base exception for chat provider errors."""

    def __init__(self, message: str, provider: str, model: Optional[str] = None):
        super().__init__(message)
        self.provider = provider
        self.model = model


class RateLimitError(ChatProviderError):
    """Rate limit exceeded."""

    def __init__(
        self,
        message: str,
        provider: str,
        retry_after: Optional[int] = None,
        model: Optional[str] = None,
    ):
        super().__init__(message, provider, model)
        self.retry_after = retry_after


class TimeoutError(ChatProviderError):
    """Request timeout."""

    pass


class AuthenticationError(ChatProviderError):
    """Authentication failed."""

    pass


class InvalidRequestError(ChatProviderError):
    """Invalid request parameters."""

    pass


class ModelNotFoundError(ChatProviderError):
    """Requested model not found."""

    pass


class ContentFilterError(ChatProviderError):
    """Content violated provider policy."""

    pass


class ProviderUnavailableError(ChatProviderError):
    """Provider service unavailable."""

    pass
