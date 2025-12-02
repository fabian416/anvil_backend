"""
Vertex AI Provider Adapter.

Implements LLMProviderPort for Google Vertex AI.
"""

import logging
from typing import AsyncIterator, Dict, Any, List, Optional
from uuid import UUID
from datetime import datetime
import asyncio

import httpx
from google.auth import default
from google.auth.transport.requests import Request

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


class VertexAIAdapter:
    """
    Vertex AI provider adapter.

    Implements Google Vertex AI integration for Gemini models.
    """

    def __init__(
        self,
        project_id: str,
        location: str = "us-central1",
        provider_id: Optional[UUID] = None,
    ):
        """
        Initialize Vertex AI adapter.

        Args:
            project_id: GCP project ID
            location: GCP region (default: us-central1)
            provider_id: Database provider ID
        """
        self.project_id = project_id
        self.location = location
        self._provider_id = provider_id
        self._base_url = f"https://{location}-aiplatform.googleapis.com/v1"
        self._client: Optional[httpx.AsyncClient] = None
        self._credentials = None
        self._token = None
        self._token_expiry = None

    @property
    def provider_name(self) -> str:
        """Get provider name."""
        return "vertex_ai"

    @property
    def provider_id(self) -> UUID:
        """Get provider UUID."""
        return self._provider_id

    async def _ensure_client(self):
        """Ensure HTTP client is initialized."""
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=60.0)

    async def _get_access_token(self) -> str:
        """
        Get access token for Google Cloud API.

        Uses Application Default Credentials.
        """
        # Check if token is still valid
        if self._token and self._token_expiry:
            if datetime.now() < self._token_expiry:
                return self._token

        # Get new token
        if self._credentials is None:
            # This will use GOOGLE_APPLICATION_CREDENTIALS env var
            self._credentials, project = default(
                scopes=["https://www.googleapis.com/auth/cloud-platform"]
            )

        # Refresh token
        self._credentials.refresh(Request())
        self._token = self._credentials.token
        self._token_expiry = self._credentials.expiry

        return self._token

    async def complete(self, request: LLMRequest) -> LLMResponse:
        """
        Execute non-streaming completion.

        Args:
            request: LLM request

        Returns:
            LLM response
        """
        await self._ensure_client()

        # Build Vertex AI request
        model_id = request.model_id or "gemini-1.5-pro"
        endpoint = (
            f"{self._base_url}/projects/{self.project_id}/"
            f"locations/{self.location}/publishers/google/"
            f"models/{model_id}:generateContent"
        )

        # Convert messages to Vertex AI format
        contents = self._convert_messages(request.messages)

        # Build generation config
        generation_config = {
            "maxOutputTokens": request.max_tokens,
            "temperature": float(request.temperature),
        }

        if request.top_p:
            generation_config["topP"] = float(request.top_p)

        if request.stop:
            generation_config["stopSequences"] = request.stop

        payload = {
            "contents": contents,
            "generationConfig": generation_config,
        }

        # Add tools if present
        if request.tools:
            payload["tools"] = self._convert_tools(request.tools)

        # Execute request
        start_time = datetime.utcnow()

        try:
            token = await self._get_access_token()

            response = await self._client.post(
                endpoint,
                json=payload,
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json",
                },
            )

            response.raise_for_status()
            data = response.json()

            latency_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)

            # Parse response
            return self._parse_response(data, model_id, latency_ms, request.input_tokens)

        except httpx.HTTPStatusError as e:
            self._handle_http_error(e)
        except httpx.TimeoutException as e:
            raise LLMTimeoutError(f"Vertex AI request timed out: {e}")
        except Exception as e:
            logger.error(f"Vertex AI request failed: {e}")
            raise RetryableError(f"Vertex AI error: {e}")

    async def complete_stream(self, request: LLMRequest) -> AsyncIterator[str]:
        """
        Execute streaming completion.

        Args:
            request: LLM request

        Yields:
            Content chunks
        """
        await self._ensure_client()

        model_id = request.model_id or "gemini-1.5-pro"
        endpoint = (
            f"{self._base_url}/projects/{self.project_id}/"
            f"locations/{self.location}/publishers/google/"
            f"models/{model_id}:streamGenerateContent"
        )

        contents = self._convert_messages(request.messages)

        generation_config = {
            "maxOutputTokens": request.max_tokens,
            "temperature": float(request.temperature),
        }

        payload = {
            "contents": contents,
            "generationConfig": generation_config,
        }

        try:
            token = await self._get_access_token()

            async with self._client.stream(
                "POST",
                endpoint,
                json=payload,
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json",
                },
            ) as response:
                response.raise_for_status()

                async for line in response.aiter_lines():
                    if line.strip():
                        # Parse streaming response
                        chunk = self._parse_streaming_chunk(line)
                        if chunk:
                            yield chunk

        except httpx.HTTPStatusError as e:
            self._handle_http_error(e)
        except httpx.TimeoutException as e:
            raise LLMTimeoutError(f"Vertex AI streaming timed out: {e}")
        except Exception as e:
            logger.error(f"Vertex AI streaming failed: {e}")
            raise RetryableError(f"Vertex AI streaming error: {e}")

    async def health_check(self) -> Dict[str, Any]:
        """
        Check Vertex AI health.

        Returns:
            Health status
        """
        try:
            # Try to get access token
            token = await self._get_access_token()

            # Test request with minimal prompt
            test_request = LLMRequest(
                messages=[LLMMessage(role="user", content="Hi")], max_tokens=10
            )

            start_time = datetime.utcnow()
            await self.complete(test_request)
            latency_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)

            return {
                "status": "healthy",
                "latency_ms": latency_ms,
                "message": "Vertex AI is operational",
            }

        except Exception as e:
            logger.error(f"Vertex AI health check failed: {e}")
            return {
                "status": "down",
                "latency_ms": None,
                "message": f"Health check failed: {str(e)}",
            }

    def _convert_messages(self, messages: List[LLMMessage]) -> List[Dict[str, Any]]:
        """
        Convert messages to Vertex AI format.

        Args:
            messages: List of LLM messages

        Returns:
            Vertex AI formatted messages
        """
        # Gemini uses "user" and "model" roles
        # System messages are typically prepended to first user message
        system_content = ""
        converted = []

        for msg in messages:
            if msg.role == "system":
                system_content += msg.content + "\n\n"
            elif msg.role == "user":
                content = system_content + msg.content if system_content else msg.content
                converted.append({"role": "user", "parts": [{"text": content}]})
                system_content = ""  # Reset after first user message
            elif msg.role == "assistant":
                converted.append({"role": "model", "parts": [{"text": msg.content}]})

        return converted

    def _convert_tools(self, tools: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Convert tools to Vertex AI format.

        Args:
            tools: OpenAI-format tools

        Returns:
            Vertex AI format tools
        """
        # Convert OpenAI function calling format to Vertex AI
        vertex_tools = []

        for tool in tools:
            if tool.get("type") == "function":
                func = tool.get("function", {})
                vertex_tools.append(
                    {
                        "functionDeclarations": [
                            {
                                "name": func.get("name"),
                                "description": func.get("description"),
                                "parameters": func.get("parameters"),
                            }
                        ]
                    }
                )

        return vertex_tools

    def _parse_response(
        self, data: Dict[str, Any], model_id: str, latency_ms: int, input_tokens: int
    ) -> LLMResponse:
        """
        Parse Vertex AI response.

        Args:
            data: Response data
            model_id: Model ID used
            latency_ms: Request latency
            input_tokens: Input token count

        Returns:
            LLM response
        """
        # Extract content from candidates
        candidates = data.get("candidates", [])
        if not candidates:
            raise InvalidRequestError("No candidates in Vertex AI response")

        candidate = candidates[0]
        content_parts = candidate.get("content", {}).get("parts", [])

        # Extract text content
        content = ""
        for part in content_parts:
            if "text" in part:
                content += part["text"]

        # Extract tool calls if present
        tool_calls = None
        if "functionCall" in content_parts[0]:
            tool_calls = self._parse_tool_calls(content_parts)

        # Extract token usage
        usage = data.get("usageMetadata", {})
        output_tokens = usage.get("candidatesTokenCount", 0)

        # Determine finish reason
        finish_reason = candidate.get("finishReason", "STOP").lower()

        return LLMResponse(
            content=content,
            model_id=model_id,
            provider="vertex_ai",
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            latency_ms=latency_ms,
            finish_reason=finish_reason,
            tool_calls=tool_calls,
        )

    def _parse_tool_calls(self, parts: List[Dict[str, Any]]) -> List[ToolCall]:
        """Parse tool calls from response parts."""
        tool_calls = []

        for i, part in enumerate(parts):
            if "functionCall" in part:
                fc = part["functionCall"]
                tool_calls.append(
                    ToolCall(
                        id=f"call_{i}",
                        type="function",
                        function={
                            "name": fc.get("name"),
                            "arguments": fc.get("args", {}),
                        },
                    )
                )

        return tool_calls if tool_calls else None

    def _parse_streaming_chunk(self, line: str) -> Optional[str]:
        """
        Parse streaming response chunk.

        Args:
            line: Response line

        Returns:
            Extracted text or None
        """
        try:
            import json

            data = json.loads(line)
            candidates = data.get("candidates", [])

            if candidates:
                parts = candidates[0].get("content", {}).get("parts", [])
                for part in parts:
                    if "text" in part:
                        return part["text"]

        except Exception as e:
            logger.debug(f"Failed to parse streaming chunk: {e}")

        return None

    def _handle_http_error(self, error: httpx.HTTPStatusError):
        """
        Handle HTTP errors from Vertex AI.

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
            raise RateLimitError(f"Vertex AI rate limit: {error_message}")
        elif status_code == 503:
            raise ServiceUnavailableError(f"Vertex AI unavailable: {error_message}")
        elif status_code == 401 or status_code == 403:
            raise AuthenticationError(f"Vertex AI auth failed: {error_message}")
        elif status_code == 400:
            raise InvalidRequestError(f"Vertex AI invalid request: {error_message}")
        else:
            # Generic retryable error for other status codes
            raise RetryableError(f"Vertex AI HTTP {status_code}: {error_message}")

    async def close(self):
        """Close HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None
