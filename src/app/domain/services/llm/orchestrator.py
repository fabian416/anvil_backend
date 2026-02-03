"""
LLM Orchestrator Core.

Main orchestration engine for multi-LLM routing, retry, and telemetry.
"""

import logging
from typing import Optional, List, AsyncIterator, Dict, Any
from datetime import datetime, UTC
from uuid import UUID, uuid4
from dataclasses import dataclass
import asyncio

from app.domain.ports.llm_provider_port import (
    LLMProviderPort,
    RetryableError,
    NonRetryableError,
)
from app.domain.value_objects.llm import LLMRequest, LLMResponse
from app.domain.services.llm.retry_engine import (
    RetryEngine,
    AllProvidersExhaustedException,
)
from app.domain.services.llm.circuit_breaker import CircuitBreakerManager

logger = logging.getLogger(__name__)


@dataclass
class OrchestratorConfig:
    """Configuration for the LLM Orchestrator."""

    # Retry settings
    max_retries_per_provider: int = 2
    max_total_retries: int = 6
    initial_delay_ms: int = 100
    max_delay_ms: int = 5000
    backoff_multiplier: float = 2.0
    jitter: bool = True

    # Timeout settings
    timeout_per_attempt_ms: int = 30000
    total_timeout_ms: int = 120000
    streaming_idle_timeout_ms: int = 10000

    # Feature flags
    enable_caching: bool = True
    enable_streaming: bool = True
    enable_cost_tracking: bool = True
    enable_ranking: bool = True


@dataclass
class RankedModel:
    """Model with ranking information."""

    model_id: UUID
    provider_name: str
    model_name: str
    display_name: str
    ranking_score: float
    provider_adapter: LLMProviderPort


class LLMOrchestrator:
    """
    Main orchestration engine for multi-LLM routing.

    Responsibilities:
    - Model selection based on adaptive ranking
    - Retry with carousel fallback
    - Circuit breaker management
    - Telemetry collection
    - Cost tracking
    """

    def __init__(
        self,
        providers: Dict[str, LLMProviderPort],
        circuit_breaker_manager: CircuitBreakerManager,
        config: OrchestratorConfig = None,
    ):
        """
        Initialize orchestrator.

        Args:
            providers: Dictionary of provider_name -> provider adapter
            circuit_breaker_manager: Circuit breaker manager
            config: Orchestrator configuration
        """
        self.providers = providers
        self.circuit_breakers = circuit_breaker_manager
        self.config = config or OrchestratorConfig()

        # Initialize retry engine
        from app.domain.value_objects.llm import RetryConfig

        self.retry_engine = RetryEngine(
            config=RetryConfig(
                max_retries_per_provider=self.config.max_retries_per_provider,
                max_total_retries=self.config.max_total_retries,
                initial_delay_ms=self.config.initial_delay_ms,
                max_delay_ms=self.config.max_delay_ms,
                backoff_multiplier=self.config.backoff_multiplier,
                jitter=self.config.jitter,
            )
        )

    async def execute(
        self,
        request: LLMRequest,
        agent_type: str,
        ranked_models: List[RankedModel],
        user_id: Optional[UUID] = None,
        session_id: Optional[str] = None,
        on_attempt: Optional[callable] = None,
    ) -> LLMResponse:
        """
        Execute an LLM request with full orchestration.

        Flow:
        1. Filter out models with open circuit breakers
        2. Execute with retry/fallback logic (carousel)
        3. Record telemetry (via callback)
        4. Update rankings (via callback)

        Args:
            request: The LLM request to execute
            agent_type: Type of agent making the request
            ranked_models: Pre-ranked models (from ranking engine)
            user_id: Optional user ID for tracking
            session_id: Optional session ID for context
            on_attempt: Optional callback for each attempt

        Returns:
            LLMResponse from the successful model

        Raises:
            AllProvidersExhaustedException: All retries failed
            NoAvailableModelsError: No models available
        """
        request_id = self._generate_request_id()
        start_time = datetime.now(UTC)

        # Filter out models with open circuit breakers
        available_models = [
            m for m in ranked_models if not self.circuit_breakers.is_open(m.model_id)
        ]

        if not available_models:
            raise NoAvailableModelsError(
                f"No available models for agent {agent_type} (all circuit breakers open)"
            )

        logger.info(
            f"Request {request_id}: {len(available_models)} available models for {agent_type}"
        )

        # Define execution function for retry engine
        async def execute_model(model: RankedModel) -> LLMResponse:
            """Execute request on specific model."""
            # Set model ID in request
            request.model_id = model.model_name

            # Get provider adapter
            provider = model.provider_adapter

            # Execute with timeout
            try:
                response = await asyncio.wait_for(
                    provider.complete(request),
                    timeout=self.config.timeout_per_attempt_ms / 1000,
                )

                # Record success in circuit breaker
                self.circuit_breakers.record_success(model.model_id)

                return response

            except asyncio.TimeoutError:
                # Record failure in circuit breaker
                self.circuit_breakers.record_failure(model.model_id)
                raise RetryableError(
                    f"Request timed out after {self.config.timeout_per_attempt_ms}ms"
                )

            except RetryableError as e:
                # Record failure
                self.circuit_breakers.record_failure(model.model_id)
                raise

            except NonRetryableError as e:
                # Don't update circuit breaker for non-retryable errors
                raise

            except Exception as e:
                # Unknown error, record as failure and retry
                self.circuit_breakers.record_failure(model.model_id)
                raise RetryableError(f"Unknown error: {e}")

        # Convert models to dict format for retry engine
        model_dicts = [
            {
                "model_id": m.model_name,
                "provider": m.provider_name,
                "ranking_score": m.ranking_score,
                "adapter": m.provider_adapter,
                "_ranked_model": m,  # Keep reference
            }
            for m in available_models
        ]

        # Execute with retry logic
        try:
            response = await self.retry_engine.execute_with_retry(
                func=lambda model_dict: execute_model(model_dict["_ranked_model"]),
                models=model_dicts,
                on_attempt=on_attempt,
            )

            total_latency_ms = int(
                (datetime.now(UTC) - start_time).total_seconds() * 1000
            )

            logger.info(
                f"Request {request_id} completed successfully in {total_latency_ms}ms"
            )

            return response

        except AllProvidersExhaustedException as e:
            logger.error(f"Request {request_id} failed: {e}")
            raise

    async def execute_stream(
        self,
        request: LLMRequest,
        agent_type: str,
        ranked_models: List[RankedModel],
        user_id: Optional[UUID] = None,
        session_id: Optional[str] = None,
    ) -> AsyncIterator[str]:
        """
        Execute a streaming LLM request.

        Args:
            request: LLM request (with stream=True)
            agent_type: Agent type
            ranked_models: Pre-ranked models
            user_id: Optional user ID
            session_id: Optional session ID

        Yields:
            Content chunks
        """
        request.stream = True
        request_id = self._generate_request_id()

        # Filter available models
        available_models = [
            m for m in ranked_models if not self.circuit_breakers.is_open(m.model_id)
        ]

        if not available_models:
            raise NoAvailableModelsError(f"No available models for agent {agent_type}")

        # For streaming, try each model sequentially until one works
        last_error = None

        for model in available_models:
            try:
                logger.info(
                    f"Streaming request {request_id}: Trying {model.model_name}"
                )

                # Set model ID
                request.model_id = model.model_name

                # Get provider
                provider = model.provider_adapter

                # Start streaming
                first_chunk = True
                async for chunk in provider.complete_stream(request):
                    if first_chunk:
                        logger.info(
                            f"Streaming request {request_id}: First chunk received from {model.model_name}"
                        )
                        first_chunk = False

                    yield chunk

                # Stream completed successfully
                self.circuit_breakers.record_success(model.model_id)
                logger.info(
                    f"Streaming request {request_id} completed with {model.model_name}"
                )
                return

            except RetryableError as e:
                last_error = e
                self.circuit_breakers.record_failure(model.model_id)
                logger.warning(
                    f"Streaming failed with {model.model_name}, trying next: {e}"
                )
                continue

            except NonRetryableError as e:
                logger.error(f"Non-retryable streaming error: {e}")
                raise

            except Exception as e:
                last_error = e
                self.circuit_breakers.record_failure(model.model_id)
                logger.error(f"Streaming error with {model.model_name}: {e}")
                continue

        # All models failed
        raise AllProvidersExhaustedException(
            f"All streaming attempts failed. Last error: {last_error}"
        )

    def _generate_request_id(self) -> str:
        """Generate unique request ID."""
        return f"req_{uuid4().hex[:16]}"

    def _extract_capabilities(self, request: LLMRequest) -> List[str]:
        """
        Extract required capabilities from request.

        Args:
            request: LLM request

        Returns:
            List of required capabilities
        """
        capabilities = ["chat"]

        if request.tools:
            capabilities.append("function_calling")

        return capabilities


class NoAvailableModelsError(Exception):
    """Raised when no models are available for a request."""

    pass
