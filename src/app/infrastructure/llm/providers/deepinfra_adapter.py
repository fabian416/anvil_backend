"""
DeepInfra Provider Adapter.

Implements LLMProviderPort for DeepInfra.
"""

import logging
from typing import AsyncIterator, Dict, Any, List, Optional
from uuid import UUID
from datetime import datetime, UTC

import httpx

from app.domain.ports.llm_provider_port import (
    LLMProviderPort,
    RetryableError,
    NonRetryableError,
    RateLimitError,
    TimeoutError as LLMTimeoutError,
    ServiceUnavailableError,
    AuthenticationError,
    InvalidRequestError,
)
from app.domain.value_objects.llm import LLMRequest, LLMResponse, LLMMessage, ToolCall

logger = logging.getLogger(__name__)


class DeepInfraAdapter:
    """
    DeepInfra provider adapter.

    Implements DeepInfra integration using OpenAI-compatible API.
    """

    def __init__(
        self,
        api_key: str,
        base_url: str = "https://api.deepinfra.com/v1/openai",
        provider_id: Optional[UUID] = None,
    ):
        """
        Initialize DeepInfra adapter.

        Args:
            api_key: DeepInfra API key
            base_url: API base URL
            provider_id: Database provider ID
        """
        self.api_key = api_key
        self.base_url = base_url
        self._provider_id = provider_id
        self._client: Optional[httpx.AsyncClient] = None

    @property
    def provider_name(self) -> str:
        """Get provider name."""
        return "deepinfra"

    @property
    def provider_id(self) -> UUID:
        """Get provider UUID."""
        return self._provider_id

    async def _ensure_client(self):
        """Ensure HTTP client is initialized."""
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                timeout=60.0,
            )

    async def complete(self, request: LLMRequest) -> LLMResponse:
        """
        Execute non-streaming completion.

        Args:
            request: LLM request

        Returns:
            LLM response
        """
        await self._ensure_client()

        # Build OpenAI-compatible request
        model_id = request.model_id or "meta-llama/Meta-Llama-3.1-405B-Instruct"

        # Convert messages to OpenAI format
        messages = self._convert_messages(request.messages)

        payload = {
            "model": model_id,
            "messages": messages,
            "max_tokens": request.max_tokens,
            "temperature": float(request.temperature),
            "stream": False,
        }

        if request.top_p:
            payload["top_p"] = float(request.top_p)

        if request.stop:
            payload["stop"] = request.stop

        if request.tools:
            payload["tools"] = request.tools
            if request.tool_choice:
                payload["tool_choice"] = request.tool_choice

        # Execute request
        start_time = datetime.now(UTC)

        try:
            response = await self._client.post("/chat/completions", json=payload)
            response.raise_for_status()
            data = response.json()

            latency_ms = int((datetime.now(UTC) - start_time).total_seconds() * 1000)

            # Parse OpenAI-format response
            return self._parse_response(data, model_id, latency_ms)

        except httpx.HTTPStatusError as e:
            self._handle_http_error(e)
        except httpx.TimeoutException as e:
            raise LLMTimeoutError(f"DeepInfra request timed out: {e}")
        except Exception as e:
            logger.error(f"DeepInfra request failed: {e}")
            raise RetryableError(f"DeepInfra error: {e}")

    async def complete_stream(self, request: LLMRequest) -> AsyncIterator[str]:
        """
        Execute streaming completion.

        Args:
            request: LLM request

        Yields:
            Content chunks
        """
        await self._ensure_client()

        model_id = request.model_id or "meta-llama/Meta-Llama-3.1-405B-Instruct"

        messages = self._convert_messages(request.messages)

        payload = {
            "model": model_id,
            "messages": messages,
            "max_tokens": request.max_tokens,
            "temperature": float(request.temperature),
            "stream": True,
        }

        if request.tools:
            payload["tools"] = request.tools

        try:
            async with self._client.stream(
                "POST", "/chat/completions", json=payload
            ) as response:
                response.raise_for_status()

                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        chunk_data = line[6:]  # Remove "data: " prefix

                        if chunk_data == "[DONE]":
                            break

                        try:
                            import json

                            chunk = json.loads(chunk_data)
                            delta = chunk.get("choices", [{}])[0].get("delta", {})
                            content = delta.get("content")

                            if content:
                                yield content

                        except json.JSONDecodeError:
                            continue

        except httpx.HTTPStatusError as e:
            self._handle_http_error(e)
        except httpx.TimeoutException as e:
            raise LLMTimeoutError(f"DeepInfra streaming timed out: {e}")
        except Exception as e:
            logger.error(f"DeepInfra streaming failed: {e}")
            raise RetryableError(f"DeepInfra streaming error: {e}")

    async def health_check(self) -> Dict[str, Any]:
        """
        Check DeepInfra health.

        Returns:
            Health status
        """
        try:
            await self._ensure_client()

            # Test with minimal request
            test_request = LLMRequest(
                messages=[LLMMessage(role="user", content="Hi")], max_tokens=10
            )

            start_time = datetime.now(UTC)
            await self.complete(test_request)
            latency_ms = int((datetime.now(UTC) - start_time).total_seconds() * 1000)

            return {
                "status": "healthy",
                "latency_ms": latency_ms,
                "message": "DeepInfra is operational",
            }

        except Exception as e:
            logger.error(f"DeepInfra health check failed: {e}")
            return {
                "status": "down",
                "latency_ms": None,
                "message": f"Health check failed: {str(e)}",
            }

    def _convert_messages(self, messages: List[LLMMessage]) -> List[Dict[str, str]]:
        """
        Convert messages to OpenAI format.

        Args:
            messages: List of LLM messages

        Returns:
            OpenAI formatted messages
        """
        return [{"role": msg.role, "content": msg.content} for msg in messages]

    def _parse_response(
        self, data: Dict[str, Any], model_id: str, latency_ms: int
    ) -> LLMResponse:
        """
        Parse OpenAI-format response.

        Args:
            data: Response data
            model_id: Model ID
            latency_ms: Latency

        Returns:
            LLM response
        """
        choices = data.get("choices", [])
        if not choices:
            raise InvalidRequestError("No choices in DeepInfra response")

        choice = choices[0]
        message = choice.get("message", {})

        content = message.get("content", "")
        finish_reason = choice.get("finish_reason", "stop")

        # Extract tool calls if present
        tool_calls = None
        if "tool_calls" in message:
            tool_calls = [
                ToolCall(
                    id=tc.get("id", f"call_{i}"),
                    type=tc.get("type", "function"),
                    function=tc.get("function", {}),
                )
                for i, tc in enumerate(message["tool_calls"])
            ]

        # Extract usage
        usage = data.get("usage", {})
        input_tokens = usage.get("prompt_tokens", 0)
        output_tokens = usage.get("completion_tokens", 0)

        return LLMResponse(
            content=content,
            model_id=model_id,
            provider="deepinfra",
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            latency_ms=latency_ms,
            finish_reason=finish_reason,
            tool_calls=tool_calls,
        )

    def _handle_http_error(self, error: httpx.HTTPStatusError):
        """
        Handle HTTP errors from DeepInfra.

        Args:
            error: HTTP error

        Raises:
            Appropriate custom exception
        """
        status_code = error.response.status_code
        error_data = {}

        try:
            error_data = error.response.json()
        except Exception:
            pass

        error_message = error_data.get("error", {}).get("message", str(error))

        if status_code == 429:
            raise RateLimitError(f"DeepInfra rate limit: {error_message}")
        elif status_code == 503:
            raise ServiceUnavailableError(f"DeepInfra unavailable: {error_message}")
        elif status_code == 401 or status_code == 403:
            raise AuthenticationError(f"DeepInfra auth failed: {error_message}")
        elif status_code == 400:
            raise InvalidRequestError(f"DeepInfra invalid request: {error_message}")
        else:
            raise RetryableError(f"DeepInfra HTTP {status_code}: {error_message}")

    async def close(self):
        """Close HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None
