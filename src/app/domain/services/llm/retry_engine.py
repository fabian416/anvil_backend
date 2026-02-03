"""
Retry Engine with Carousel Logic.

Implements intelligent retry strategies with model rotation.
"""

import logging
import asyncio
from typing import List, Callable, Any, Optional
from datetime import datetime
import random

from app.domain.value_objects.llm import RetryConfig
from app.domain.ports.llm_provider_port import RetryableError, NonRetryableError

logger = logging.getLogger(__name__)


class RetryEngine:
    """
    Retry engine with carousel logic.

    Implements:
    - Exponential backoff with jitter
    - Model carousel (rotate through models on retry)
    - Error classification
    - Attempt tracking
    """

    def __init__(self, config: RetryConfig = None):
        """
        Initialize retry engine.

        Args:
            config: Retry configuration
        """
        self.config = config or RetryConfig()

    def calculate_backoff(self, attempt: int) -> float:
        """
        Calculate backoff delay for attempt.

        Args:
            attempt: Attempt number (0-indexed)

        Returns:
            Delay in seconds
        """
        delay_ms = self.config.calculate_delay(attempt)
        return delay_ms / 1000.0

    def should_retry(self, error: Exception) -> bool:
        """
        Determine if error should trigger retry.

        Args:
            error: Exception raised

        Returns:
            True if should retry
        """
        # NonRetryableError should never retry
        if isinstance(error, NonRetryableError):
            logger.info(f"Non-retryable error, will not retry: {type(error).__name__}")
            return False

        # RetryableError should retry
        if isinstance(error, RetryableError):
            logger.info(f"Retryable error, will retry: {type(error).__name__}")
            return True

        # Default: retry for safety (could be transient)
        logger.warning(f"Unknown error type, will retry: {type(error).__name__}")
        return True

    def classify_error(self, error: Exception) -> str:
        """
        Classify error type for tracking.

        Args:
            error: Exception

        Returns:
            Error type string
        """
        error_str = str(error).lower()

        if "rate limit" in error_str or "429" in error_str:
            return "rate_limit"
        elif "timeout" in error_str:
            return "timeout"
        elif "503" in error_str or "unavailable" in error_str:
            return "service_unavailable"
        elif "overloaded" in error_str:
            return "model_overloaded"
        elif "authentication" in error_str or "401" in error_str or "403" in error_str:
            return "authentication_error"
        elif "invalid" in error_str or "400" in error_str:
            return "invalid_request"
        elif "content" in error_str and "policy" in error_str:
            return "content_policy"
        else:
            return "internal_error"

    async def execute_with_retry(
        self,
        func: Callable,
        models: List[Any],
        on_attempt: Optional[Callable] = None,
    ) -> Any:
        """
        Execute function with carousel retry logic.

        Args:
            func: Async function to execute (receives model as arg)
            models: List of models to try (ordered by ranking)
            on_attempt: Optional callback for each attempt

        Returns:
            Function result

        Raises:
            Exception: If all retries exhausted
        """
        attempt = 0
        last_error = None

        for model in models:
            # Try each model up to max_retries_per_provider
            for provider_attempt in range(self.config.max_retries_per_provider):
                attempt += 1

                if attempt > self.config.max_total_retries:
                    logger.warning(
                        f"Max total retries ({self.config.max_total_retries}) exceeded"
                    )
                    break

                try:
                    logger.debug(
                        f"Attempt {attempt}: Trying {model.get('model_id', 'unknown')}"
                    )

                    # Callback before attempt
                    if on_attempt:
                        await on_attempt(
                            attempt=attempt, model=model, is_retry=attempt > 1
                        )

                    # Execute function
                    result = await func(model)

                    logger.info(
                        f"Success on attempt {attempt} with {model.get('model_id', 'unknown')}"
                    )

                    return result

                except NonRetryableError as e:
                    # Don't retry non-retryable errors
                    logger.error(f"Non-retryable error on attempt {attempt}: {e}")
                    last_error = e
                    break  # Skip to next model

                except RetryableError as e:
                    last_error = e
                    error_type = self.classify_error(e)

                    logger.warning(
                        f"Retryable error ({error_type}) on attempt {attempt}: {e}"
                    )

                    # Apply backoff before next retry
                    if (
                        provider_attempt < self.config.max_retries_per_provider - 1
                        and attempt < self.config.max_total_retries
                    ):
                        backoff = self.calculate_backoff(attempt)
                        logger.debug(f"Applying backoff: {backoff:.2f}s")
                        await asyncio.sleep(backoff)

                except Exception as e:
                    # Unknown error, treat as retryable
                    last_error = e
                    logger.error(f"Unknown error on attempt {attempt}: {e}")

                    # Apply backoff
                    if (
                        provider_attempt < self.config.max_retries_per_provider - 1
                        and attempt < self.config.max_total_retries
                    ):
                        backoff = self.calculate_backoff(attempt)
                        await asyncio.sleep(backoff)

        # All retries exhausted
        error_message = (
            f"All {attempt} attempts failed across {len(models)} models. "
            f"Last error: {last_error}"
        )

        logger.error(error_message)
        raise AllProvidersExhaustedException(error_message)


class AllProvidersExhaustedException(Exception):
    """Raised when all retry attempts are exhausted."""

    pass
