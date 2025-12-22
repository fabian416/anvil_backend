"""
OpenAI Chat Adapter.

Implements ChatLLMProvider for OpenAI's chat completion API.
Supports GPT-4, GPT-3.5-turbo with streaming and token tracking.
"""

import time
import asyncio
from typing import AsyncIterator, Dict, Any, Optional
from decimal import Decimal
import logging

import httpx

from app.domain.ports.chat_llm_provider import (
    ChatLLMProvider,
    RateLimitError,
    TimeoutError,
    AuthenticationError,
    InvalidRequestError,
    ModelNotFoundError,
    ContentFilterError,
    ProviderUnavailableError,
)
from app.domain.value_objects.llm import LLMRequest, LLMResponse, ToolCall

logger = logging.getLogger(__name__)


class OpenAIChatAdapter:
    """
    OpenAI chat completion adapter.

    Implements unified interface for OpenAI's chat API with:
    - Streaming and non-streaming completions
    - Automatic retry with exponential backoff
    - Token usage tracking
    - Cost estimation
    - Error handling and classification
    """

    # Model pricing per 1M tokens (as of 2025)
    PRICING = {
        "gpt-4-turbo": {"input": Decimal("10.00"), "output": Decimal("30.00")},
        "gpt-4-turbo-preview": {"input": Decimal("10.00"), "output": Decimal("30.00")},
        "gpt-4": {"input": Decimal("30.00"), "output": Decimal("60.00")},
        "gpt-4-32k": {"input": Decimal("60.00"), "output": Decimal("120.00")},
        "gpt-3.5-turbo": {"input": Decimal("0.50"), "output": Decimal("1.50")},
        "gpt-3.5-turbo-16k": {"input": Decimal("3.00"), "output": Decimal("4.00")},
        "gpt-4o": {"input": Decimal("5.00"), "output": Decimal("15.00")},
        "gpt-4o-mini": {"input": Decimal("0.15"), "output": Decimal("0.60")},
    }

    def __init__(
        self,
        api_key: str,
        base_url: str = "https://api.openai.com/v1",
        timeout: int = 60,
        max_retries: int = 3,
        organization: Optional[str] = None,
    ):
        """
        Initialize OpenAI adapter.

        Args:
            api_key: OpenAI API key
            base_url: API base URL
            timeout: Request timeout in seconds
            max_retries: Maximum retry attempts
            organization: Optional OpenAI organization ID
        """
        self._api_key = api_key
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout
        self._max_retries = max_retries
        self._organization = organization

        # Create HTTP client with connection pooling
        self._client = httpx.AsyncClient(
            timeout=httpx.Timeout(timeout=timeout, connect=10.0),
            limits=httpx.Limits(max_keepalive_connections=10, max_connections=50),
        )

    @property
    def provider_name(self) -> str:
        """Get provider name."""
        return "openai"

    @property
    def supported_models(self) -> list[str]:
        """Get list of supported model IDs."""
        return list(self.PRICING.keys())

    async def complete(self, request: LLMRequest) -> LLMResponse:
        """Execute non-streaming chat completion."""
        start_time = time.time()

        # Build request payload
        payload = self._build_payload(request, stream=False)

        # Make API request with retries
        response_data = await self._make_request(
            endpoint="/chat/completions",
            payload=payload,
            model=request.model_id or "gpt-3.5-turbo",
        )

        # Extract response data
        choice = response_data["choices"][0]
        message = choice["message"]
        content = message.get("content", "")
        finish_reason = choice.get("finish_reason", "stop")

        # Extract token usage
        usage = response_data.get("usage", {})
        input_tokens = usage.get("prompt_tokens", 0)
        output_tokens = usage.get("completion_tokens", 0)

        # Extract tool calls if present
        tool_calls = None
        if "tool_calls" in message and message["tool_calls"]:
            tool_calls = [
                ToolCall(
                    id=tc["id"],
                    type=tc["type"],
                    function=tc["function"],
                )
                for tc in message["tool_calls"]
            ]

        # Calculate metrics
        latency_ms = int((time.time() - start_time) * 1000)
        model = response_data.get("model", request.model_id or "unknown")
        cost = await self.estimate_cost(input_tokens, output_tokens, model)

        return LLMResponse(
            content=content,
            model_id=model,
            provider=self.provider_name,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            latency_ms=latency_ms,
            finish_reason=finish_reason,
            tool_calls=tool_calls,
            cost_usd=cost,
            metadata={
                "system_fingerprint": response_data.get("system_fingerprint"),
                "created": response_data.get("created"),
            },
        )

    async def complete_stream(self, request: LLMRequest) -> AsyncIterator[str]:
        """Execute streaming chat completion."""
        payload = self._build_payload(request, stream=True)
        model = request.model_id or "gpt-3.5-turbo"

        headers = self._build_headers()

        try:
            async with self._client.stream(
                "POST",
                f"{self._base_url}/chat/completions",
                json=payload,
                headers=headers,
            ) as response:
                # Check for errors
                if response.status_code != 200:
                    error_text = await response.aread()
                    self._handle_error(response.status_code, error_text.decode(), model)

                # Process SSE stream
                async for line in response.aiter_lines():
                    if not line or line.strip() == "":
                        continue

                    if line.startswith("data: "):
                        data = line[6:]  # Remove 'data: ' prefix

                        if data.strip() == "[DONE]":
                            break

                        try:
                            import json

                            chunk = json.loads(data)
                            delta = chunk["choices"][0].get("delta", {})

                            if "content" in delta and delta["content"]:
                                yield delta["content"]

                        except (json.JSONDecodeError, KeyError, IndexError) as e:
                            logger.warning(f"Failed to parse streaming chunk: {e}")
                            continue

        except httpx.TimeoutException as e:
            raise TimeoutError(
                f"Request timed out after {self._timeout}s",
                provider=self.provider_name,
                model=model,
            ) from e
        except httpx.NetworkError as e:
            raise ProviderUnavailableError(
                f"Network error: {str(e)}",
                provider=self.provider_name,
                model=model,
            ) from e

    async def estimate_cost(
        self, input_tokens: int, output_tokens: int, model: str
    ) -> Decimal:
        """Estimate cost for given token usage."""
        # Normalize model name (handle versioned models)
        base_model = self._normalize_model_name(model)

        pricing = self.PRICING.get(
            base_model, {"input": Decimal("1.00"), "output": Decimal("2.00")}
        )

        input_cost = (Decimal(input_tokens) * pricing["input"]) / Decimal("1000000")
        output_cost = (Decimal(output_tokens) * pricing["output"]) / Decimal("1000000")

        return input_cost + output_cost

    async def health_check(self) -> Dict[str, Any]:
        """Check provider health status."""
        start_time = time.time()

        try:
            # Simple health check: list models
            headers = self._build_headers()
            response = await self._client.get(
                f"{self._base_url}/models", headers=headers, timeout=5.0
            )

            latency_ms = int((time.time() - start_time) * 1000)

            if response.status_code == 200:
                data = response.json()
                available_models = [m["id"] for m in data.get("data", [])]

                return {
                    "status": "healthy",
                    "latency_ms": latency_ms,
                    "available_models": available_models,
                    "message": "OpenAI API is operational",
                }
            else:
                return {
                    "status": "degraded",
                    "latency_ms": latency_ms,
                    "message": f"HTTP {response.status_code}",
                }

        except Exception as e:
            latency_ms = int((time.time() - start_time) * 1000)
            return {
                "status": "down",
                "latency_ms": latency_ms,
                "message": f"Health check failed: {str(e)}",
            }

    # ========================================================================
    # PRIVATE METHODS
    # ========================================================================

    def _build_payload(self, request: LLMRequest, stream: bool) -> Dict[str, Any]:
        """Build OpenAI API request payload."""
        payload = {
            "model": request.model_id or "gpt-3.5-turbo",
            "messages": [
                {
                    "role": msg.role,
                    "content": msg.content,
                    **({"name": msg.name} if msg.name else {}),
                    **({"tool_calls": msg.tool_calls} if msg.tool_calls else {}),
                    **({"tool_call_id": msg.tool_call_id} if msg.tool_call_id else {}),
                }
                for msg in request.messages
            ],
            "temperature": float(request.temperature),
            "max_tokens": request.max_tokens,
            "stream": stream,
        }

        # Add optional parameters
        if request.top_p is not None:
            payload["top_p"] = float(request.top_p)

        if request.stop:
            payload["stop"] = request.stop

        if request.tools:
            payload["tools"] = request.tools

        if request.tool_choice:
            payload["tool_choice"] = request.tool_choice

        if request.response_format:
            payload["response_format"] = request.response_format

        if request.user:
            payload["user"] = request.user

        return payload

    def _build_headers(self) -> Dict[str, str]:
        """Build request headers."""
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }

        if self._organization:
            headers["OpenAI-Organization"] = self._organization

        return headers

    async def _make_request(
        self, endpoint: str, payload: Dict[str, Any], model: str
    ) -> Dict[str, Any]:
        """Make HTTP request with retry logic."""
        headers = self._build_headers()
        url = f"{self._base_url}{endpoint}"

        last_exception = None

        for attempt in range(self._max_retries):
            try:
                response = await self._client.post(url, json=payload, headers=headers)

                if response.status_code == 200:
                    return response.json()

                # Handle error responses
                error_text = response.text
                self._handle_error(response.status_code, error_text, model)

            except (RateLimitError, AuthenticationError, InvalidRequestError):
                # Don't retry on these errors
                raise

            except Exception as e:
                last_exception = e
                if attempt < self._max_retries - 1:
                    # Exponential backoff
                    delay = 2**attempt
                    logger.warning(
                        f"Request failed (attempt {attempt + 1}/{self._max_retries}), "
                        f"retrying in {delay}s: {e}"
                    )
                    await asyncio.sleep(delay)
                    continue

        # All retries exhausted
        raise ProviderUnavailableError(
            f"Request failed after {self._max_retries} attempts: {last_exception}",
            provider=self.provider_name,
            model=model,
        )

    def _handle_error(self, status_code: int, error_text: str, model: str):
        """Handle API error responses."""
        try:
            import json

            error_data = json.loads(error_text)
            error_message = error_data.get("error", {}).get("message", error_text)
            error_type = error_data.get("error", {}).get("type", "unknown")
        except json.JSONDecodeError:
            error_message = error_text
            error_type = "unknown"

        if status_code == 401:
            raise AuthenticationError(
                f"Authentication failed: {error_message}",
                provider=self.provider_name,
                model=model,
            )

        if status_code == 400:
            raise InvalidRequestError(
                f"Invalid request: {error_message}",
                provider=self.provider_name,
                model=model,
            )

        if status_code == 404:
            raise ModelNotFoundError(
                f"Model not found: {error_message}",
                provider=self.provider_name,
                model=model,
            )

        if status_code == 429:
            # Extract retry-after header if present
            retry_after = None
            if "retry-after" in error_text.lower():
                try:
                    retry_after = int(error_message.split("retry after ")[1].split()[0])
                except (IndexError, ValueError):
                    pass

            raise RateLimitError(
                f"Rate limit exceeded: {error_message}",
                provider=self.provider_name,
                retry_after=retry_after,
                model=model,
            )

        if status_code == 503:
            raise ProviderUnavailableError(
                f"Service unavailable: {error_message}",
                provider=self.provider_name,
                model=model,
            )

        # Content filter / policy violation
        if "content_filter" in error_type or "policy" in error_message.lower():
            raise ContentFilterError(
                f"Content policy violation: {error_message}",
                provider=self.provider_name,
                model=model,
            )

        # Generic error
        raise ProviderUnavailableError(
            f"API error {status_code}: {error_message}",
            provider=self.provider_name,
            model=model,
        )

    def _normalize_model_name(self, model: str) -> str:
        """Normalize model name for pricing lookup."""
        # Remove version suffixes like -0613, -0125, etc.
        import re

        normalized = re.sub(r"-\d{4}(-\d{2})?$", "", model)

        # Map specific models to base pricing
        if normalized.startswith("gpt-4-turbo"):
            return "gpt-4-turbo"
        if normalized.startswith("gpt-4-32k"):
            return "gpt-4-32k"
        if normalized.startswith("gpt-4o-mini"):
            return "gpt-4o-mini"
        if normalized.startswith("gpt-4o"):
            return "gpt-4o"
        if normalized.startswith("gpt-4"):
            return "gpt-4"
        if normalized.startswith("gpt-3.5-turbo-16k"):
            return "gpt-3.5-turbo-16k"
        if normalized.startswith("gpt-3.5-turbo"):
            return "gpt-3.5-turbo"

        return normalized

    async def close(self):
        """Close HTTP client."""
        await self._client.aclose()

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()
