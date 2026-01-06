"""
LLM Provider Failover with Circuit Breaker.

Implements automatic failover between LLM providers with:
- Circuit breaker pattern for failing providers
- Cost optimization (cheaper fallback models)
- Retry logic with exponential backoff
- Health monitoring and recovery
"""

import time
import asyncio
from typing import AsyncIterator, Optional, List, Dict, Any
from decimal import Decimal
from dataclasses import dataclass, field
from enum import Enum
import logging

from app.domain.ports.chat_llm_provider import (
    ChatLLMProvider,
    ChatProviderError,
    RateLimitError,
    TimeoutError,
    AuthenticationError,
    InvalidRequestError,
    ProviderUnavailableError,
)
from app.domain.value_objects.llm import LLMRequest, LLMResponse

logger = logging.getLogger(__name__)


class CircuitState(Enum):
    """Circuit breaker states."""

    CLOSED = "closed"  # Normal operation
    OPEN = "open"  # Provider is failing, don't use
    HALF_OPEN = "half_open"  # Testing if provider recovered


@dataclass
class CircuitBreaker:
    """
    Circuit breaker for individual provider.

    Tracks failures and prevents cascading failures by temporarily
    disabling failing providers.
    """

    provider_name: str
    failure_threshold: int = 5  # Failures before opening circuit
    success_threshold: int = 2  # Successes to close circuit (from half-open)
    timeout_seconds: int = 60  # Time before half-open state
    state: CircuitState = CircuitState.CLOSED
    failure_count: int = 0
    success_count: int = 0
    last_failure_time: Optional[float] = None
    last_state_change: float = field(default_factory=time.time)

    def record_success(self):
        """Record successful request."""
        if self.state == CircuitState.HALF_OPEN:
            self.success_count += 1
            if self.success_count >= self.success_threshold:
                self._close_circuit()
        elif self.state == CircuitState.CLOSED:
            # Reset failure count on success
            self.failure_count = 0

    def record_failure(self):
        """Record failed request."""
        self.last_failure_time = time.time()

        if self.state == CircuitState.HALF_OPEN:
            # Failed during testing, reopen circuit
            self._open_circuit()
        elif self.state == CircuitState.CLOSED:
            self.failure_count += 1
            if self.failure_count >= self.failure_threshold:
                self._open_circuit()

    def can_attempt(self) -> bool:
        """Check if provider can be attempted."""
        if self.state == CircuitState.CLOSED:
            return True

        if self.state == CircuitState.OPEN:
            # Check if timeout elapsed
            if self.last_failure_time:
                elapsed = time.time() - self.last_failure_time
                if elapsed >= self.timeout_seconds:
                    self._half_open_circuit()
                    return True
            return False

        if self.state == CircuitState.HALF_OPEN:
            return True

        return False

    def _open_circuit(self):
        """Open circuit (disable provider)."""
        self.state = CircuitState.OPEN
        self.last_state_change = time.time()
        self.success_count = 0
        logger.warning(
            f"Circuit breaker OPENED for {self.provider_name} "
            f"after {self.failure_count} failures"
        )

    def _close_circuit(self):
        """Close circuit (enable provider)."""
        self.state = CircuitState.CLOSED
        self.last_state_change = time.time()
        self.failure_count = 0
        self.success_count = 0
        logger.info(f"Circuit breaker CLOSED for {self.provider_name}")

    def _half_open_circuit(self):
        """Half-open circuit (test provider)."""
        self.state = CircuitState.HALF_OPEN
        self.last_state_change = time.time()
        self.success_count = 0
        logger.info(
            f"Circuit breaker HALF-OPEN for {self.provider_name} (testing recovery)"
        )


@dataclass
class ProviderConfig:
    """Configuration for a provider in the failover chain."""

    provider: ChatLLMProvider
    priority: int = 0  # Lower = higher priority
    cost_tier: str = "standard"  # "cheap", "standard", "premium"
    is_fallback: bool = False


class LLMProviderFailover:
    """
    Failover orchestrator for multiple LLM providers.

    Manages automatic failover between providers with:
    - Circuit breaker for each provider
    - Priority-based routing
    - Cost optimization (use cheaper models on fallback)
    - Automatic retry with exponential backoff
    """

    def __init__(
        self,
        providers: List[ProviderConfig],
        failure_threshold: int = 5,
        success_threshold: int = 2,
        circuit_timeout: int = 60,
        max_retries: int = 3,
        enable_cost_fallback: bool = True,
    ):
        """
        Initialize failover orchestrator.

        Args:
            providers: List of provider configurations (ordered by priority)
            failure_threshold: Failures before opening circuit
            success_threshold: Successes to close circuit
            circuit_timeout: Seconds before testing recovery
            max_retries: Maximum retry attempts across all providers
            enable_cost_fallback: Use cheaper models on fallback
        """
        # Sort providers by priority
        self._providers = sorted(providers, key=lambda p: p.priority)
        self._max_retries = max_retries
        self._enable_cost_fallback = enable_cost_fallback

        # Initialize circuit breakers
        self._circuit_breakers: Dict[str, CircuitBreaker] = {}
        for provider_config in self._providers:
            self._circuit_breakers[provider_config.provider.provider_name] = (
                CircuitBreaker(
                    provider_name=provider_config.provider.provider_name,
                    failure_threshold=failure_threshold,
                    success_threshold=success_threshold,
                    timeout_seconds=circuit_timeout,
                )
            )

        # Model mapping for cost-based fallback
        self._fallback_models = {
            # OpenAI fallbacks
            "gpt-4-turbo": "gpt-4o-mini",
            "gpt-4": "gpt-4o-mini",
            "gpt-4o": "gpt-4o-mini",
            "gpt-3.5-turbo": "gpt-3.5-turbo",  # Already cheap
            # Anthropic fallbacks
            "claude-opus-4-5": "claude-3-haiku-20240307",
            "claude-sonnet-4-5": "claude-3-haiku-20240307",
            "claude-3-opus-20240229": "claude-3-haiku-20240307",
            "claude-3-5-sonnet-20241022": "claude-3-haiku-20240307",
            "claude-3-sonnet-20240229": "claude-3-haiku-20240307",
            "claude-3-haiku-20240307": "claude-3-haiku-20240307",  # Already cheap
        }

    async def complete(self, request: LLMRequest) -> LLMResponse:
        """
        Execute completion with automatic failover.

        Tries providers in priority order, skipping those with open circuits.
        Falls back to cheaper models on secondary providers if enabled.
        """
        original_model = request.model_id
        last_error = None
        attempts = 0

        for provider_config in self._providers:
            provider = provider_config.provider
            circuit = self._circuit_breakers[provider.provider_name]

            # Skip if circuit is open
            if not circuit.can_attempt():
                logger.debug(
                    f"Skipping {provider.provider_name} - circuit breaker is OPEN"
                )
                continue

            # Adjust model for cost optimization on fallback
            if provider_config.is_fallback and self._enable_cost_fallback:
                request.model_id = self._get_fallback_model(original_model)
                logger.info(
                    f"Using fallback model {request.model_id} "
                    f"(original: {original_model})"
                )

            # Try this provider with retries
            for retry in range(self._max_retries):
                attempts += 1

                try:
                    logger.debug(
                        f"Attempting {provider.provider_name} "
                        f"(attempt {attempts}, retry {retry})"
                    )

                    response = await provider.complete(request)

                    # Success - record it
                    circuit.record_success()
                    logger.info(
                        f"Success with {provider.provider_name} "
                        f"(model: {response.model_id}, "
                        f"tokens: {response.total_tokens}, "
                        f"cost: ${response.cost_usd})"
                    )
                    return response

                except (AuthenticationError, InvalidRequestError) as e:
                    # Don't retry these errors
                    logger.error(f"Non-retryable error from {provider.provider_name}: {e}")
                    circuit.record_failure()
                    raise

                except RateLimitError as e:
                    logger.warning(
                        f"Rate limit from {provider.provider_name}: {e}"
                    )
                    circuit.record_failure()
                    last_error = e

                    # Wait for retry-after if specified
                    if e.retry_after and retry < self._max_retries - 1:
                        await asyncio.sleep(min(e.retry_after, 60))
                        continue

                    # Otherwise try next provider
                    break

                except (TimeoutError, ProviderUnavailableError) as e:
                    logger.warning(
                        f"Provider error from {provider.provider_name}: {e}"
                    )
                    circuit.record_failure()
                    last_error = e

                    # Exponential backoff
                    if retry < self._max_retries - 1:
                        delay = 2**retry
                        await asyncio.sleep(delay)
                        continue

                    # Try next provider
                    break

                except Exception as e:
                    logger.error(
                        f"Unexpected error from {provider.provider_name}: {e}",
                        exc_info=True,
                    )
                    circuit.record_failure()
                    last_error = e
                    break

        # All providers exhausted
        error_msg = (
            f"All providers exhausted after {attempts} attempts. "
            f"Last error: {last_error}"
        )
        logger.error(error_msg)
        raise ProviderUnavailableError(
            error_msg,
            provider="failover",
            model=original_model,
        )

    async def complete_stream(self, request: LLMRequest) -> AsyncIterator[str]:
        """
        Execute streaming completion with failover.

        Note: Streaming is harder to recover from mid-stream,
        so we fail over immediately on errors.
        """
        original_model = request.model_id
        last_error = None

        for provider_config in self._providers:
            provider = provider_config.provider
            circuit = self._circuit_breakers[provider.provider_name]

            # Skip if circuit is open
            if not circuit.can_attempt():
                logger.debug(
                    f"Skipping {provider.provider_name} - circuit breaker is OPEN"
                )
                continue

            # Adjust model for cost optimization on fallback
            if provider_config.is_fallback and self._enable_cost_fallback:
                request.model_id = self._get_fallback_model(original_model)
                logger.info(
                    f"Using fallback model {request.model_id} "
                    f"(original: {original_model})"
                )

            try:
                logger.debug(f"Streaming with {provider.provider_name}")

                # Start streaming
                chunk_count = 0
                async for chunk in provider.complete_stream(request):
                    chunk_count += 1
                    yield chunk

                # Successful stream
                circuit.record_success()
                logger.info(
                    f"Stream completed with {provider.provider_name} "
                    f"({chunk_count} chunks)"
                )
                return

            except (AuthenticationError, InvalidRequestError) as e:
                logger.error(f"Non-retryable error from {provider.provider_name}: {e}")
                circuit.record_failure()
                raise

            except Exception as e:
                logger.warning(
                    f"Streaming failed with {provider.provider_name}: {e}"
                )
                circuit.record_failure()
                last_error = e
                continue  # Try next provider

        # All providers exhausted
        error_msg = f"All providers exhausted for streaming. Last error: {last_error}"
        logger.error(error_msg)
        raise ProviderUnavailableError(
            error_msg,
            provider="failover",
            model=original_model,
        )

    async def get_provider_status(self) -> Dict[str, Any]:
        """Get status of all providers and circuit breakers."""
        status = {}

        for provider_config in self._providers:
            provider = provider_config.provider
            circuit = self._circuit_breakers[provider.provider_name]

            # Get health check
            try:
                health = await provider.health_check()
            except Exception as e:
                health = {"status": "error", "message": str(e)}

            status[provider.provider_name] = {
                "priority": provider_config.priority,
                "cost_tier": provider_config.cost_tier,
                "is_fallback": provider_config.is_fallback,
                "circuit_state": circuit.state.value,
                "failure_count": circuit.failure_count,
                "health": health,
            }

        return status

    def _get_fallback_model(self, original_model: str) -> str:
        """Get cheaper fallback model for cost optimization."""
        # Try to find mapping
        for key, fallback in self._fallback_models.items():
            if key in (original_model or ""):
                logger.debug(f"Mapped {original_model} -> {fallback}")
                return fallback

        # No mapping found, return original
        return original_model


# ============================================================================
# FACTORY FUNCTIONS
# ============================================================================


def create_openai_anthropic_failover(
    openai_api_key: str,  # Not used - OpenAI removed
    anthropic_api_key: str,
    primary: str = "anthropic",  # Changed default from "openai"
    enable_cost_fallback: bool = True,
) -> LLMProviderFailover:
    """
    Create failover with Anthropic provider (OpenAI removed).

    Args:
        openai_api_key: Not used - OpenAI removed
        anthropic_api_key: Anthropic API key
        primary: Primary provider ("anthropic" - OpenAI removed)
        enable_cost_fallback: Use cheaper models on fallback

    Returns:
        Configured failover orchestrator
        
    Note:
        OpenAI provider has been removed. This function now only supports Anthropic.
        For Vertex AI/DeepInfra, use the agent_squad_infrastructure provider.
    """
    # OpenAI removed - using only Anthropic and Vertex AI/DeepInfra
    # from app.infrastructure.adapters.ai.openai_chat_adapter import OpenAIChatAdapter
    from app.infrastructure.adapters.ai.anthropic_chat_adapter import (
        AnthropicChatAdapter,
    )

    # Create adapters (OpenAI removed)
    # openai = OpenAIChatAdapter(api_key=openai_api_key)
    anthropic = AnthropicChatAdapter(api_key=anthropic_api_key)

    # Configure priority based on primary (OpenAI removed)
    if primary == "openai":
        raise ValueError(
            "OpenAI provider has been removed. "
            "Please use 'anthropic' or configure Vertex AI/DeepInfra as primary."
        )
    
    # Only Anthropic supported now (OpenAI removed)
    providers = [
        ProviderConfig(provider=anthropic, priority=0, cost_tier="standard"),
    ]

    return LLMProviderFailover(
        providers=providers,
        enable_cost_fallback=enable_cost_fallback,
    )
