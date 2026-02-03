"""
LLM-specific domain exceptions with standardized error codes.

This module provides all exceptions related to:
- LLM providers and models
- Token budgets and rate limits
- Generation and processing
"""

from typing import Any
from uuid import UUID

from app.domain.exceptions.base import ApplicationError
from app.domain.exceptions.error_codes import ErrorCode


class LLMProviderUnavailableError(ApplicationError):
    """Raised when an LLM provider is unavailable."""

    def __init__(
        self,
        provider: str | None = None,
        reason: str | None = None,
        retry_after_seconds: int | None = None,
    ) -> None:
        details = {}
        if provider:
            details["provider"] = provider
        if reason:
            details["reason"] = reason
        if retry_after_seconds is not None:
            details["retry_after_seconds"] = retry_after_seconds
        super().__init__(ErrorCode.LLM_PROVIDER_UNAVAILABLE, details=details)


class LLMRateLimitError(ApplicationError):
    """Raised when LLM rate limit is exceeded."""

    def __init__(
        self,
        provider: str | None = None,
        retry_after_seconds: int | None = None,
        requests_limit: int | None = None,
        tokens_limit: int | None = None,
    ) -> None:
        details = {}
        if provider:
            details["provider"] = provider
        if retry_after_seconds is not None:
            details["retry_after_seconds"] = retry_after_seconds
        if requests_limit is not None:
            details["requests_limit"] = requests_limit
        if tokens_limit is not None:
            details["tokens_limit"] = tokens_limit
        super().__init__(ErrorCode.LLM_RATE_LIMIT, details=details)


class LLMBudgetExceededError(ApplicationError):
    """Raised when LLM budget limit is reached."""

    def __init__(
        self,
        budget_type: str | None = None,
        limit: float | int | None = None,
        current_usage: float | int | None = None,
        reset_at: str | None = None,
    ) -> None:
        details = {}
        if budget_type:
            details["budget_type"] = budget_type
        if limit is not None:
            details["limit"] = limit
        if current_usage is not None:
            details["current_usage"] = current_usage
        if reset_at:
            details["reset_at"] = reset_at
        super().__init__(ErrorCode.LLM_BUDGET_EXCEEDED, details=details)


class LLMGenerationFailedError(ApplicationError):
    """Raised when LLM response generation fails."""

    def __init__(
        self,
        provider: str | None = None,
        model: str | None = None,
        reason: str | None = None,
        request_id: str | None = None,
    ) -> None:
        details = {}
        if provider:
            details["provider"] = provider
        if model:
            details["model"] = model
        if reason:
            details["reason"] = reason
        if request_id:
            details["request_id"] = request_id
        super().__init__(ErrorCode.LLM_GENERATION_FAILED, details=details)


class InvalidPromptError(ApplicationError):
    """Raised when a prompt is invalid."""

    def __init__(
        self,
        reason: str | None = None,
        max_length: int | None = None,
        current_length: int | None = None,
    ) -> None:
        details = {}
        if reason:
            details["reason"] = reason
        if max_length is not None:
            details["max_length"] = max_length
        if current_length is not None:
            details["current_length"] = current_length
        super().__init__(ErrorCode.LLM_INVALID_PROMPT, details=details, field="prompt")


class AllProvidersFailedError(ApplicationError):
    """Raised when all LLM providers fail."""

    def __init__(
        self,
        attempted_providers: list[str] | None = None,
        errors: dict[str, str] | None = None,
    ) -> None:
        details = {}
        if attempted_providers:
            details["attempted_providers"] = attempted_providers
        if errors:
            details["errors"] = errors
        super().__init__(ErrorCode.LLM_ALL_PROVIDERS_FAILED, details=details)


# Additional LLM-specific exceptions


class ModelNotFoundError(ApplicationError):
    """Raised when an LLM model is not found."""

    def __init__(
        self,
        model: str | None = None,
        provider: str | None = None,
        available_models: list[str] | None = None,
    ) -> None:
        details = {}
        if model:
            details["model"] = model
        if provider:
            details["provider"] = provider
        if available_models:
            details["available_models"] = available_models
        super().__init__(
            ErrorCode.LLM_PROVIDER_UNAVAILABLE,
            details=details,
            override_message="Model not found or unavailable",
        )


class ContextLengthExceededError(ApplicationError):
    """Raised when context length exceeds model's limit."""

    def __init__(
        self,
        model: str | None = None,
        current_tokens: int | None = None,
        max_tokens: int | None = None,
    ) -> None:
        details = {}
        if model:
            details["model"] = model
        if current_tokens is not None:
            details["current_tokens"] = current_tokens
        if max_tokens is not None:
            details["max_tokens"] = max_tokens
        super().__init__(
            ErrorCode.LLM_INVALID_PROMPT,
            details=details,
            override_message="Context length exceeds model's maximum",
        )


class ContentFilterError(ApplicationError):
    """Raised when content is filtered by safety systems."""

    def __init__(
        self,
        filter_type: str | None = None,
        reason: str | None = None,
    ) -> None:
        details = {}
        if filter_type:
            details["filter_type"] = filter_type
        if reason:
            details["reason"] = reason
        super().__init__(
            ErrorCode.LLM_GENERATION_FAILED,
            details=details,
            override_message="Content was filtered by safety systems",
        )


class LLMTimeoutError(ApplicationError):
    """Raised when LLM request times out."""

    def __init__(
        self,
        provider: str | None = None,
        model: str | None = None,
        timeout_seconds: int | None = None,
    ) -> None:
        details = {}
        if provider:
            details["provider"] = provider
        if model:
            details["model"] = model
        if timeout_seconds is not None:
            details["timeout_seconds"] = timeout_seconds
        super().__init__(
            ErrorCode.LLM_PROVIDER_UNAVAILABLE,
            details=details,
            override_message="LLM request timed out",
        )


class StreamingError(ApplicationError):
    """Raised when streaming response fails."""

    def __init__(
        self,
        provider: str | None = None,
        reason: str | None = None,
        tokens_received: int | None = None,
    ) -> None:
        details = {}
        if provider:
            details["provider"] = provider
        if reason:
            details["reason"] = reason
        if tokens_received is not None:
            details["tokens_received"] = tokens_received
        super().__init__(
            ErrorCode.LLM_GENERATION_FAILED,
            details=details,
            override_message="Streaming response interrupted",
        )


class InvalidModelParametersError(ApplicationError):
    """Raised when model parameters are invalid."""

    def __init__(
        self,
        parameter: str | None = None,
        value: Any | None = None,
        valid_range: str | None = None,
    ) -> None:
        details = {}
        if parameter:
            details["parameter"] = parameter
        if value is not None:
            details["value"] = value
        if valid_range:
            details["valid_range"] = valid_range
        super().__init__(
            ErrorCode.LLM_INVALID_PROMPT,
            details=details,
            field=parameter,
            override_message="Invalid model parameter",
        )


class EmbeddingError(ApplicationError):
    """Raised when embedding generation fails."""

    def __init__(
        self,
        provider: str | None = None,
        reason: str | None = None,
    ) -> None:
        details = {}
        if provider:
            details["provider"] = provider
        if reason:
            details["reason"] = reason
        super().__init__(
            ErrorCode.LLM_GENERATION_FAILED,
            details=details,
            override_message="Embedding generation failed",
        )


class CircuitBreakerOpenError(ApplicationError):
    """Raised when circuit breaker is open for a provider."""

    def __init__(
        self,
        provider: str | None = None,
        open_since: str | None = None,
        reset_at: str | None = None,
    ) -> None:
        details = {}
        if provider:
            details["provider"] = provider
        if open_since:
            details["open_since"] = open_since
        if reset_at:
            details["reset_at"] = reset_at
        super().__init__(
            ErrorCode.LLM_PROVIDER_UNAVAILABLE,
            details=details,
            override_message="Provider circuit breaker is open",
        )
