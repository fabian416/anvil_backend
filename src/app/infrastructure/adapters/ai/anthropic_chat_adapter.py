"""
Anthropic Chat Adapter.

Implements ChatLLMProvider for Anthropic's Claude API.
Supports Claude 3 family (Opus, Sonnet, Haiku) with streaming and token tracking.
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


class AnthropicChatAdapter:
    """
    Anthropic Claude chat completion adapter.

    Implements unified interface for Anthropic's Messages API with:
    - Streaming and non-streaming completions
    - Automatic retry with exponential backoff
    - Token usage tracking
    - Cost estimation
    - Error handling and classification
    """

    # Model pricing per 1M tokens (as of 2025)
    PRICING = {
        "claude-opus-4-5": {"input": Decimal("15.00"), "output": Decimal("75.00")},
        "claude-3-opus-20240229": {
            "input": Decimal("15.00"),
            "output": Decimal("75.00"),
        },
        "claude-sonnet-4-5": {"input": Decimal("3.00"), "output": Decimal("15.00")},
        "claude-3-5-sonnet-20241022": {
            "input": Decimal("3.00"),
            "output": Decimal("15.00"),
        },
        "claude-3-sonnet-20240229": {
            "input": Decimal("3.00"),
            "output": Decimal("15.00"),
        },
        "claude-3-haiku-20240307": {
            "input": Decimal("0.25"),
            "output": Decimal("1.25"),
        },
        "claude-2.1": {"input": Decimal("8.00"), "output": Decimal("24.00")},
        "claude-2.0": {"input": Decimal("8.00"), "output": Decimal("24.00")},
    }

    def __init__(
        self,
        api_key: str,
        base_url: str = "https://api.anthropic.com/v1",
        timeout: int = 60,
        max_retries: int = 3,
        anthropic_version: str = "2023-06-01",
    ):
        """
        Initialize Anthropic adapter.

        Args:
            api_key: Anthropic API key
            base_url: API base URL
            timeout: Request timeout in seconds
            max_retries: Maximum retry attempts
            anthropic_version: API version header
        """
        self._api_key = api_key
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout
        self._max_retries = max_retries
        self._anthropic_version = anthropic_version

        # Create HTTP client with connection pooling
        self._client = httpx.AsyncClient(
            timeout=httpx.Timeout(timeout=timeout, connect=10.0),
            limits=httpx.Limits(max_keepalive_connections=10, max_connections=50),
        )

    @property
    def provider_name(self) -> str:
        """Get provider name."""
        return "anthropic"

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
            endpoint="/messages",
            payload=payload,
            model=request.model_id or "claude-3-haiku-20240307",
        )

        # Extract response data
        content_blocks = response_data.get("content", [])

        # Combine text from all content blocks
        content = ""
        tool_calls_list = []

        for block in content_blocks:
            if block.get("type") == "text":
                content += block.get("text", "")
            elif block.get("type") == "tool_use":
                # Anthropic tool use format
                tool_calls_list.append(
                    ToolCall(
                        id=block.get("id", ""),
                        type="function",
                        function={
                            "name": block.get("name", ""),
                            "arguments": block.get("input", {}),
                        },
                    )
                )

        finish_reason = response_data.get("stop_reason", "end_turn")

        # Map Anthropic stop reasons to standard reasons
        finish_reason_map = {
            "end_turn": "stop",
            "max_tokens": "length",
            "stop_sequence": "stop",
            "tool_use": "tool_calls",
        }
        finish_reason = finish_reason_map.get(finish_reason, finish_reason)

        # Extract token usage
        usage = response_data.get("usage", {})
        input_tokens = usage.get("input_tokens", 0)
        output_tokens = usage.get("output_tokens", 0)

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
            tool_calls=tool_calls_list if tool_calls_list else None,
            cost_usd=cost,
            metadata={
                "id": response_data.get("id"),
                "type": response_data.get("type"),
                "role": response_data.get("role"),
            },
        )

    async def complete_stream(self, request: LLMRequest) -> AsyncIterator[str]:
        """Execute streaming chat completion."""
        payload = self._build_payload(request, stream=True)
        model = request.model_id or "claude-3-haiku-20240307"

        headers = self._build_headers()

        try:
            async with self._client.stream(
                "POST",
                f"{self._base_url}/messages",
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

                        try:
                            import json

                            event = json.loads(data)
                            event_type = event.get("type")

                            # Handle different event types
                            if event_type == "content_block_delta":
                                delta = event.get("delta", {})
                                if delta.get("type") == "text_delta":
                                    text = delta.get("text", "")
                                    if text:
                                        yield text

                            elif event_type == "message_stop":
                                break

                        except (json.JSONDecodeError, KeyError) as e:
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
        # Normalize model name
        base_model = self._normalize_model_name(model)

        pricing = self.PRICING.get(
            base_model, {"input": Decimal("3.00"), "output": Decimal("15.00")}
        )

        input_cost = (Decimal(input_tokens) * pricing["input"]) / Decimal("1000000")
        output_cost = (Decimal(output_tokens) * pricing["output"]) / Decimal("1000000")

        return input_cost + output_cost

    async def health_check(self) -> Dict[str, Any]:
        """Check provider health status."""
        start_time = time.time()

        try:
            # Simple health check: make a minimal request
            headers = self._build_headers()

            # Anthropic doesn't have a dedicated health endpoint,
            # so we make a minimal completion request
            minimal_payload = {
                "model": "claude-3-haiku-20240307",
                "messages": [{"role": "user", "content": "Hi"}],
                "max_tokens": 10,
            }

            response = await self._client.post(
                f"{self._base_url}/messages",
                json=minimal_payload,
                headers=headers,
                timeout=5.0,
            )

            latency_ms = int((time.time() - start_time) * 1000)

            if response.status_code == 200:
                return {
                    "status": "healthy",
                    "latency_ms": latency_ms,
                    "available_models": self.supported_models,
                    "message": "Anthropic API is operational",
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
        """Build Anthropic API request payload."""
        # Anthropic requires system messages to be separate
        system_messages = []
        conversation_messages = []

        for msg in request.messages:
            if msg.role == "system":
                system_messages.append(msg.content)
            else:
                # Map assistant/user/tool roles
                role = msg.role
                if role not in ["user", "assistant"]:
                    # Tool responses become user messages
                    role = "user"

                message_content = msg.content

                # Handle tool calls in assistant messages
                if msg.tool_calls:
                    # Convert to Anthropic's tool_use format
                    content_blocks = []
                    if message_content:
                        content_blocks.append({"type": "text", "text": message_content})

                    for tc in msg.tool_calls:
                        content_blocks.append({
                            "type": "tool_use",
                            "id": tc.get("id", ""),
                            "name": tc.get("function", {}).get("name", ""),
                            "input": tc.get("function", {}).get("arguments", {}),
                        })

                    message_content = content_blocks

                conversation_messages.append({
                    "role": role,
                    "content": message_content,
                })

        payload = {
            "model": request.model_id or "claude-3-haiku-20240307",
            "messages": conversation_messages,
            "max_tokens": request.max_tokens,
            "temperature": float(request.temperature),
            "stream": stream,
        }

        # Add system prompt if present
        if system_messages:
            payload["system"] = "\n\n".join(system_messages)

        # Add optional parameters
        if request.top_p is not None:
            payload["top_p"] = float(request.top_p)

        if request.stop:
            payload["stop_sequences"] = request.stop

        if request.tools:
            # Convert OpenAI-style tools to Anthropic format
            payload["tools"] = [
                {
                    "name": tool.get("function", {}).get("name", ""),
                    "description": tool.get("function", {}).get("description", ""),
                    "input_schema": tool.get("function", {}).get("parameters", {}),
                }
                for tool in request.tools
            ]

        # Metadata for tracking
        if request.user:
            payload["metadata"] = {"user_id": request.user}

        return payload

    def _build_headers(self) -> Dict[str, str]:
        """Build request headers."""
        return {
            "x-api-key": self._api_key,
            "anthropic-version": self._anthropic_version,
            "Content-Type": "application/json",
        }

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
            # Extract retry-after from headers or error message
            retry_after = None
            if "retry" in error_message.lower():
                try:
                    # Try to parse retry time from message
                    import re

                    match = re.search(r"(\d+)\s*second", error_message)
                    if match:
                        retry_after = int(match.group(1))
                except (ValueError, AttributeError):
                    pass

            raise RateLimitError(
                f"Rate limit exceeded: {error_message}",
                provider=self.provider_name,
                retry_after=retry_after,
                model=model,
            )

        if status_code == 529:
            # Anthropic-specific: overloaded
            raise ProviderUnavailableError(
                f"Service overloaded: {error_message}",
                provider=self.provider_name,
                model=model,
            )

        if status_code == 503:
            raise ProviderUnavailableError(
                f"Service unavailable: {error_message}",
                provider=self.provider_name,
                model=model,
            )

        # Content filter / policy violation
        if "content" in error_type.lower() or "policy" in error_message.lower():
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
        # Map model variants to base pricing
        if "opus-4-5" in model or "opus-4.5" in model:
            return "claude-opus-4-5"
        if "sonnet-4-5" in model or "sonnet-4.5" in model:
            return "claude-sonnet-4-5"
        if "claude-3-opus" in model:
            return "claude-3-opus-20240229"
        if "claude-3-5-sonnet" in model or "claude-3.5-sonnet" in model:
            return "claude-3-5-sonnet-20241022"
        if "claude-3-sonnet" in model:
            return "claude-3-sonnet-20240229"
        if "claude-3-haiku" in model:
            return "claude-3-haiku-20240307"
        if "claude-2.1" in model:
            return "claude-2.1"
        if "claude-2" in model:
            return "claude-2.0"

        return model

    async def close(self):
        """Close HTTP client."""
        await self._client.aclose()

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()
