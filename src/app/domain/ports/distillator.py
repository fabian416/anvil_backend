"""
Distillator port (interface).

Defines the contract for distillation providers.
"""
from typing import Protocol, Dict, Any

from app.domain.entities.distillation import DistillationRequest, DistillationResult


class Distillator(Protocol):
    """
    Port for distillation providers.
    
    Defines the interface that all distillation providers must implement.
    Providers validate user requests before main LLM processing.
    """
    
    async def validate(
        self,
        request: DistillationRequest,
    ) -> DistillationResult:
        """
        Validate a user request.
        
        Args:
            request: The distillation request to validate
        
        Returns:
            DistillationResult containing validation decision and metadata
        
        Raises:
            DistillationError: If validation fails due to provider error
        """
        ...
    
    def get_provider_name(self) -> str:
        """
        Get the name of this distillation provider.
        
        Returns:
            Provider name (e.g., "vertex_ai", "deepinfra")
        """
        ...
    
    def get_model_name(self) -> str:
        """
        Get the model being used by this provider.
        
        Returns:
            Model name (e.g., "gemini-1.5-flash")
        """
        ...
    
    async def check_health(self) -> Dict[str, Any]:
        """
        Check health/availability of the distillation provider.
        
        Returns:
            Health status dictionary with keys:
                - healthy: bool
                - latency_ms: float
                - error: Optional[str]
        """
        ...
    
    async def close(self) -> None:
        """
        Close any open connections/resources.
        
        Should be called when the provider is no longer needed.
        """
        ...


class DistillationError(Exception):
    """
    Base exception for distillation errors.
    
    Raised when distillation validation fails due to provider
    errors (not validation failures).
    """
    
    def __init__(
        self,
        message: str,
        provider: str,
        error_code: str = "unknown",
        retryable: bool = True,
    ):
        """
        Initialize distillation error.
        
        Args:
            message: Error message
            provider: Provider that raised the error
            error_code: Error code for categorization
            retryable: Whether the operation can be retried
        """
        self.message = message
        self.provider = provider
        self.error_code = error_code
        self.retryable = retryable
        super().__init__(message)


class DistillationTimeoutError(DistillationError):
    """Raised when distillation request times out."""
    
    def __init__(self, provider: str, timeout_seconds: float):
        super().__init__(
            message=f"Distillation request timed out after {timeout_seconds}s",
            provider=provider,
            error_code="timeout",
            retryable=True,
        )
        self.timeout_seconds = timeout_seconds


class DistillationRateLimitError(DistillationError):
    """Raised when provider rate limit is exceeded."""
    
    def __init__(self, provider: str, retry_after_seconds: float = None):
        message = f"Rate limit exceeded for provider {provider}"
        if retry_after_seconds:
            message += f", retry after {retry_after_seconds}s"
        
        super().__init__(
            message=message,
            provider=provider,
            error_code="rate_limit",
            retryable=True,
        )
        self.retry_after_seconds = retry_after_seconds


class DistillationAuthenticationError(DistillationError):
    """Raised when authentication fails."""
    
    def __init__(self, provider: str):
        super().__init__(
            message=f"Authentication failed for provider {provider}",
            provider=provider,
            error_code="authentication",
            retryable=False,
        )


class DistillationInvalidResponseError(DistillationError):
    """Raised when provider returns invalid/unparseable response."""
    
    def __init__(self, provider: str, details: str):
        super().__init__(
            message=f"Invalid response from provider {provider}: {details}",
            provider=provider,
            error_code="invalid_response",
            retryable=True,
        )
        self.details = details
