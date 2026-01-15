"""
AWS Bedrock Provider Adapter.

Implements LLMProviderPort for AWS Bedrock (Claude models).
"""

import logging
import json
from typing import AsyncIterator, Dict, Any, List, Optional
from uuid import UUID
from datetime import datetime, UTC

import httpx
import boto3
from botocore.exceptions import ClientError

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


class BedrockAdapter:
    """
    AWS Bedrock provider adapter.

    Implements AWS Bedrock integration for Claude models.
    """

    def __init__(
        self,
        region: str = "us-east-1",
        aws_access_key_id: Optional[str] = None,
        aws_secret_access_key: Optional[str] = None,
        provider_id: Optional[UUID] = None,
    ):
        """
        Initialize Bedrock adapter.

        Args:
            region: AWS region
            aws_access_key_id: AWS access key (optional, uses default credentials)
            aws_secret_access_key: AWS secret key
            provider_id: Database provider ID
        """
        self.region = region
        self._provider_id = provider_id

        # Initialize Bedrock client
        kwargs = {"region_name": region}
        if aws_access_key_id and aws_secret_access_key:
            kwargs["aws_access_key_id"] = aws_access_key_id
            kwargs["aws_secret_access_key"] = aws_secret_access_key

        self._bedrock_runtime = boto3.client("bedrock-runtime", **kwargs)

    @property
    def provider_name(self) -> str:
        """Get provider name."""
        return "bedrock"

    @property
    def provider_id(self) -> UUID:
        """Get provider UUID."""
        return self._provider_id

    async def complete(self, request: LLMRequest) -> LLMResponse:
        """
        Execute non-streaming completion.

        Args:
            request: LLM request

        Returns:
            LLM response
        """
        model_id = request.model_id or "anthropic.claude-3-5-sonnet-20241022-v2:0"

        # Build Claude request format
        system_message = ""
        messages = []

        for msg in request.messages:
            if msg.role == "system":
                system_message = msg.content
            else:
                messages.append({"role": msg.role, "content": msg.content})

        body = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": request.max_tokens,
            "temperature": float(request.temperature),
            "messages": messages,
        }

        if system_message:
            body["system"] = system_message

        if request.top_p:
            body["top_p"] = float(request.top_p)

        if request.stop:
            body["stop_sequences"] = request.stop

        if request.tools:
            body["tools"] = self._convert_tools(request.tools)

        # Execute request
        start_time = datetime.now(UTC)

        try:
            response = self._bedrock_runtime.invoke_model(
                modelId=model_id, body=json.dumps(body)
            )

            response_body = json.loads(response["body"].read())

            latency_ms = int((datetime.now(UTC) - start_time).total_seconds() * 1000)

            return self._parse_response(response_body, model_id, latency_ms)

        except ClientError as e:
            self._handle_bedrock_error(e)
        except Exception as e:
            logger.error(f"Bedrock request failed: {e}")
            raise RetryableError(f"Bedrock error: {e}")

    async def complete_stream(self, request: LLMRequest) -> AsyncIterator[str]:
        """
        Execute streaming completion.

        Args:
            request: LLM request

        Yields:
            Content chunks
        """
        model_id = request.model_id or "anthropic.claude-3-5-sonnet-20241022-v2:0"

        # Build request
        system_message = ""
        messages = []

        for msg in request.messages:
            if msg.role == "system":
                system_message = msg.content
            else:
                messages.append({"role": msg.role, "content": msg.content})

        body = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": request.max_tokens,
            "temperature": float(request.temperature),
            "messages": messages,
        }

        if system_message:
            body["system"] = system_message

        if request.tools:
            body["tools"] = self._convert_tools(request.tools)

        try:
            response = self._bedrock_runtime.invoke_model_with_response_stream(
                modelId=model_id, body=json.dumps(body)
            )

            stream = response.get("body")

            for event in stream:
                chunk = event.get("chunk")
                if chunk:
                    chunk_data = json.loads(chunk.get("bytes").decode())

                    if chunk_data.get("type") == "content_block_delta":
                        delta = chunk_data.get("delta", {})
                        text = delta.get("text")
                        if text:
                            yield text

        except ClientError as e:
            self._handle_bedrock_error(e)
        except Exception as e:
            logger.error(f"Bedrock streaming failed: {e}")
            raise RetryableError(f"Bedrock streaming error: {e}")

    async def health_check(self) -> Dict[str, Any]:
        """
        Check Bedrock health.

        Returns:
            Health status
        """
        try:
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
                "message": "Bedrock is operational",
            }

        except Exception as e:
            logger.error(f"Bedrock health check failed: {e}")
            return {
                "status": "down",
                "latency_ms": None,
                "message": f"Health check failed: {str(e)}",
            }

    def _convert_tools(self, tools: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Convert OpenAI tools to Claude format.

        Args:
            tools: OpenAI format tools

        Returns:
            Claude format tools
        """
        claude_tools = []

        for tool in tools:
            if tool.get("type") == "function":
                func = tool.get("function", {})
                claude_tools.append(
                    {
                        "name": func.get("name"),
                        "description": func.get("description"),
                        "input_schema": func.get("parameters"),
                    }
                )

        return claude_tools

    def _parse_response(
        self, data: Dict[str, Any], model_id: str, latency_ms: int
    ) -> LLMResponse:
        """
        Parse Claude response.

        Args:
            data: Response data
            model_id: Model ID
            latency_ms: Latency

        Returns:
            LLM response
        """
        # Extract content
        content_blocks = data.get("content", [])
        content = ""
        tool_calls = []

        for block in content_blocks:
            if block.get("type") == "text":
                content += block.get("text", "")
            elif block.get("type") == "tool_use":
                tool_calls.append(
                    ToolCall(
                        id=block.get("id", ""),
                        type="function",
                        function={
                            "name": block.get("name"),
                            "arguments": block.get("input", {}),
                        },
                    )
                )

        # Extract usage
        usage = data.get("usage", {})
        input_tokens = usage.get("input_tokens", 0)
        output_tokens = usage.get("output_tokens", 0)

        # Extract finish reason
        stop_reason = data.get("stop_reason", "end_turn")
        finish_reason_map = {
            "end_turn": "stop",
            "max_tokens": "length",
            "stop_sequence": "stop",
            "tool_use": "tool_calls",
        }
        finish_reason = finish_reason_map.get(stop_reason, stop_reason)

        return LLMResponse(
            content=content,
            model_id=model_id,
            provider="bedrock",
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            latency_ms=latency_ms,
            finish_reason=finish_reason,
            tool_calls=tool_calls if tool_calls else None,
        )

    def _handle_bedrock_error(self, error: ClientError):
        """
        Handle Bedrock errors.

        Args:
            error: Bedrock client error

        Raises:
            Appropriate custom exception
        """
        error_code = error.response.get("Error", {}).get("Code", "Unknown")
        error_message = error.response.get("Error", {}).get("Message", str(error))

        if error_code == "ThrottlingException":
            raise RateLimitError(f"Bedrock rate limit: {error_message}")
        elif error_code == "ServiceUnavailableException":
            raise ServiceUnavailableError(f"Bedrock unavailable: {error_message}")
        elif error_code == "ModelNotReadyException":
            raise ServiceUnavailableError(f"Bedrock model not ready: {error_message}")
        elif error_code == "AccessDeniedException":
            raise AuthenticationError(f"Bedrock access denied: {error_message}")
        elif error_code == "ValidationException":
            raise InvalidRequestError(f"Bedrock validation error: {error_message}")
        else:
            raise RetryableError(f"Bedrock error {error_code}: {error_message}")
