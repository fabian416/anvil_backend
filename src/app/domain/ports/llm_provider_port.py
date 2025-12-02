"""
LLM Provider Port.

Defines the interface for LLM providers (Vertex AI, DeepInfra, Bedrock).
"""

from typing import Protocol, AsyncIterator, Dict, Any
from uuid import UUID

from app.domain.value_objects.llm import LLMRequest, LLMResponse


class LLMProviderPort(Protocol):
    """
    Abstract interface for LLM providers.

    All LLM provider adapters must implement this interface.
    """

    @property
    def provider_name(self) -> str:
        """Get provider name (vertex_ai, deepinfra, bedrock)."""
        ...

    @property
    def provider_id(self) -> UUID:
        """Get provider UUID from database."""
        ...

    async def complete(self, request: LLMRequest) -> LLMResponse:
        """
        Execute non-streaming LLM completion.

        Args:
            request: LLM request

        Returns:
            LLM response

        Raises:
            RetryableError: For errors that should trigger retry
            NonRetryableError: For errors that should not retry
        """
        ...

    async def complete_stream(self, request: LLMRequest) -> AsyncIterator[str]:
        """
        Execute streaming LLM completion.

        Args:
            request: LLM request (with stream=True)

        Yields:
            Content chunks as they arrive

        Raises:
            RetryableError: For errors that should trigger retry
            NonRetryableError: For errors that should not retry
        """
        ...

    async def health_check(self) -> Dict[str, Any]:
        """
        Check provider health.

        Returns:
            Health status dictionary with:
            - status: healthy, degraded, down
            - latency_ms: Response time
            - message: Optional status message
        """
        ...


# Custom exceptions for provider errors
class RetryableError(Exception):
    """
    Base class for errors that should trigger retry.

    Examples:
    - Rate limit errors (429)
    - Timeout errors
    - Service unavailable (503)
    - Model overloaded errors
    - Transient network errors
    """

    pass


class NonRetryableError(Exception):
    """
    Base class for errors that should not trigger retry.

    Examples:
    - Authentication errors (401)
    - Invalid request errors (400)
    - Content policy violations
    - Resource not found (404)
    """

    pass


class RateLimitError(RetryableError):
    """Rate limit exceeded."""

    def __init__(self, message: str, retry_after: int = None):
        super().__init__(message)
        self.retry_after = retry_after


class TimeoutError(RetryableError):
    """Request timeout."""

    pass


class ServiceUnavailableError(RetryableError):
    """Provider service unavailable."""

    pass


class ModelOverloadedError(RetryableError):
    """Model is overloaded."""

    pass


class AuthenticationError(NonRetryableError):
    """Authentication failed."""

    pass


class InvalidRequestError(NonRetryableError):
    """Invalid request parameters."""

    pass


class ContentPolicyError(NonRetryableError):
    """Content violated provider policy."""

    pass
