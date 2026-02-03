"""
DeepInfra distillation provider.

Implements distillation using DeepInfra's API.
"""

import json
import time
from typing import Dict, Any
import logging

import httpx
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)

from app.domain.entities.distillation import DistillationRequest, DistillationResult
from app.domain.ports.distillator import (
    Distillator,
    DistillationError,
    DistillationTimeoutError,
    DistillationRateLimitError,
    DistillationAuthenticationError,
    DistillationInvalidResponseError,
)
from app.setup.config.distillation import DistillationSettings
from app.infrastructure.distillation.prompt_templates import build_distillation_prompt

logger = logging.getLogger(__name__)


class DeepInfraDistillator:
    """
    DeepInfra implementation of the Distillator port.

    Uses DeepInfra's API with Llama models for request validation.
    """

    def __init__(
        self,
        settings: DistillationSettings,
    ):
        """
        Initialize DeepInfra distillator.

        Args:
            settings: Distillation settings including DeepInfra config
        """
        self.settings = settings
        self.deepinfra_settings = settings.deepinfra
        self.provider_name = "deepinfra"
        self.model_name = self.deepinfra_settings.model

        # Initialize HTTP client
        self.client = httpx.AsyncClient(
            base_url=self.deepinfra_settings.base_url,
            headers={
                "Authorization": f"Bearer {self.deepinfra_settings.api_key}",
                "Content-Type": "application/json",
            },
            timeout=self.settings.timeout_seconds,
        )

        # Setup retry decorator
        retry_config = settings.retry
        if retry_config.enabled:
            self._retry_decorator = retry(
                stop=stop_after_attempt(retry_config.max_retries),
                wait=wait_exponential(
                    multiplier=1,
                    min=retry_config.initial_backoff_seconds,
                    max=retry_config.max_backoff_seconds,
                ),
                retry=retry_if_exception_type((
                    DistillationTimeoutError,
                    DistillationRateLimitError,
                    httpx.HTTPError,
                )),
                reraise=True,
            )
        else:
            self._retry_decorator = lambda f: f

        logger.info(f"DeepInfra initialized: model={self.model_name}")

    async def validate(
        self,
        request: DistillationRequest,
    ) -> DistillationResult:
        """
        Validate a user request using DeepInfra.

        Args:
            request: The distillation request

        Returns:
            DistillationResult with validation decision

        Raises:
            DistillationError: If validation fails due to provider error
        """
        start_time = time.time()

        try:
            # Build prompt
            prompt = build_distillation_prompt(
                user_message=request.user_message,
                conversation_history=request.conversation_history,
                detected_language=request.detected_language or "en",
            )

            # Call DeepInfra with retry
            response_text, tokens_used = await self._call_deepinfra_with_retry(prompt)

            # Parse response
            response_data = self._parse_response(response_text)

            # Calculate metrics
            latency_ms = (time.time() - start_time) * 1000
            cost_usd = self._calculate_cost(tokens_used)

            # Create result
            result = DistillationResult(
                success=response_data.get("success", False),
                message=response_data.get("message", ""),
                reason=response_data.get("reason", "system_error"),
                confidence=response_data.get("confidence", 0.0),
                provider=self.provider_name,
                model=self.model_name,
                detected_language=request.detected_language or "en",
                latency_ms=latency_ms,
                tokens_used=tokens_used,
                cost_usd=cost_usd,
            )

            logger.info(
                f"DeepInfra validation complete: success={result.success}, "
                f"reason={result.reason}, latency={latency_ms:.0f}ms"
            )

            return result

        except DistillationError:
            raise

        except Exception as e:
            logger.error(f"Unexpected error in DeepInfra distillation: {e}")
            raise DistillationError(
                message=f"Unexpected error: {str(e)}",
                provider=self.provider_name,
                error_code="unexpected",
                retryable=False,
            ) from e

    async def _call_deepinfra_with_retry(self, prompt: str) -> tuple[str, int]:
        """
        Call DeepInfra API with retry support.

        Args:
            prompt: The prompt to send

        Returns:
            Tuple of (response_text, tokens_used)

        Raises:
            DistillationError: On API errors
        """

        @self._retry_decorator
        async def _call():
            try:
                response = await self.client.post(
                    "/chat/completions",
                    json={
                        "model": self.model_name,
                        "messages": [
                            {
                                "role": "user",
                                "content": prompt,
                            }
                        ],
                        "temperature": self.settings.temperature,
                        "max_tokens": self.settings.max_tokens,
                    },
                )

                # Check for HTTP errors
                if response.status_code == 401:
                    raise DistillationAuthenticationError(provider=self.provider_name)
                elif response.status_code == 429:
                    retry_after = response.headers.get("Retry-After")
                    raise DistillationRateLimitError(
                        provider=self.provider_name,
                        retry_after_seconds=float(retry_after) if retry_after else None,
                    )
                elif response.status_code >= 500:
                    raise DistillationError(
                        message=f"Server error: {response.status_code}",
                        provider=self.provider_name,
                        error_code="server_error",
                        retryable=True,
                    )

                response.raise_for_status()

                # Parse response
                data = response.json()

                if "choices" not in data or len(data["choices"]) == 0:
                    raise DistillationInvalidResponseError(
                        provider=self.provider_name,
                        details="No choices in response",
                    )

                response_text = data["choices"][0]["message"]["content"]

                # Extract token usage
                tokens_used = 0
                if "usage" in data:
                    tokens_used = data["usage"].get("total_tokens", 0)
                else:
                    # Estimate
                    tokens_used = len(prompt) // 4 + len(response_text) // 4

                return response_text, tokens_used

            except httpx.TimeoutException as e:
                raise DistillationTimeoutError(
                    provider=self.provider_name,
                    timeout_seconds=self.settings.timeout_seconds,
                ) from e

            except httpx.HTTPError as e:
                raise DistillationError(
                    message=f"HTTP error: {str(e)}",
                    provider=self.provider_name,
                    error_code="http_error",
                    retryable=True,
                ) from e

        return await _call()

    def _parse_response(self, response_text: str) -> Dict[str, Any]:
        """
        Parse JSON response from LLM.

        Args:
            response_text: Raw response text

        Returns:
            Parsed response dictionary

        Raises:
            DistillationInvalidResponseError: If parsing fails
        """
        try:
            # Remove markdown code blocks if present
            text = response_text.strip()
            if text.startswith("```json"):
                text = text[7:]
            if text.startswith("```"):
                text = text[3:]
            if text.endswith("```"):
                text = text[:-3]
            text = text.strip()

            # Parse JSON
            data = json.loads(text)

            # Validate required fields
            required_fields = ["success", "message", "reason", "confidence"]
            for field in required_fields:
                if field not in data:
                    raise ValueError(f"Missing required field: {field}")

            return data

        except (json.JSONDecodeError, ValueError) as e:
            logger.error(f"Failed to parse DeepInfra response: {response_text[:200]}")
            raise DistillationInvalidResponseError(
                provider=self.provider_name,
                details=f"JSON parse error: {str(e)}",
            ) from e

    def _calculate_cost(self, tokens_used: int) -> float:
        """
        Calculate cost of API call.

        Args:
            tokens_used: Number of tokens used

        Returns:
            Cost in USD
        """
        # DeepInfra Llama 3.2 3B pricing: ~$0.06 per 1M tokens
        cost_per_1m_tokens = 0.06
        return (tokens_used / 1_000_000) * cost_per_1m_tokens

    def get_provider_name(self) -> str:
        """Get provider name."""
        return self.provider_name

    def get_model_name(self) -> str:
        """Get model name."""
        return self.model_name

    async def check_health(self) -> Dict[str, Any]:
        """
        Check health of DeepInfra.

        Returns:
            Health status dictionary
        """
        start_time = time.time()

        try:
            test_prompt = 'Respond with \'OK\' in JSON: {"status": "OK"}'

            _, _ = await self._call_deepinfra_with_retry(test_prompt)

            latency_ms = (time.time() - start_time) * 1000

            return {
                "healthy": True,
                "latency_ms": latency_ms,
                "error": None,
            }

        except Exception as e:
            latency_ms = (time.time() - start_time) * 1000

            return {
                "healthy": False,
                "latency_ms": latency_ms,
                "error": str(e),
            }

    async def close(self) -> None:
        """Close HTTP client."""
        await self.client.aclose()
        logger.info("DeepInfra distillator closed")
