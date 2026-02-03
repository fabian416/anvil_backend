"""
Instrumented LLM Gateway with Full Telemetry.

Wraps the LLM gateway with comprehensive telemetry:
- Token usage tracking
- Cost estimation
- Latency metrics
- Provider health monitoring
- Error tracking
- Distributed tracing

Usage:
    from app.infrastructure.adapters.ai.instrumented_llm_gateway import (
        InstrumentedLLMGateway,
    )

    # Wrap existing gateway
    instrumented = InstrumentedLLMGateway(
        gateway=existing_gateway,
        telemetry=llm_telemetry,
        tracing=tracing_service,
    )

    # Use normally - all calls are instrumented
    response = await instrumented.generate(
        model="gemini-1.5-pro",
        messages=[{"role": "user", "content": "Hello"}],
    )
"""

from typing import Optional

from app.domain.ports.ai.llm_gateway import LLMGateway
from app.infrastructure.telemetry.llm_telemetry import (
    LLMTelemetry,
    LLMCallStatus,
    get_llm_telemetry,
)
from app.infrastructure.telemetry.tracing import (
    TracingService,
    SpanKind,
    SpanStatus,
    get_tracing_service,
)


class InstrumentedLLMGateway:
    """
    LLM Gateway wrapper with full telemetry instrumentation.

    This class wraps any LLMGateway implementation and adds:
    - Request/response logging
    - Token counting and cost estimation
    - Latency tracking with percentiles
    - Provider health monitoring
    - Distributed tracing
    - Budget alerting
    """

    # Provider detection based on model names
    PROVIDER_PATTERNS = {
        "vertex_ai": ["gemini", "palm", "codechat", "textembedding"],
        "openai": ["gpt-3.5", "gpt-4", "text-embedding", "whisper", "dall-e"],
        "anthropic": ["claude"],
        "deepinfra": ["llama", "mixtral", "mistral", "falcon", "deepinfra"],
        "bedrock": ["anthropic.", "amazon.", "ai21.", "cohere.", "meta."],
    }

    def __init__(
        self,
        gateway: LLMGateway,
        telemetry: Optional[LLMTelemetry] = None,
        tracing: Optional[TracingService] = None,
        default_provider: str = "unknown",
    ):
        """
        Initialize instrumented gateway.

        Args:
            gateway: The underlying LLM gateway to wrap
            telemetry: LLM telemetry service (uses global if None)
            tracing: Tracing service (uses global if None)
            default_provider: Default provider name if detection fails
        """
        self._gateway = gateway
        self._telemetry = telemetry or get_llm_telemetry()
        self._tracing = tracing or get_tracing_service()
        self._default_provider = default_provider

    def _detect_provider(self, model_name: str) -> str:
        """Detect provider from model name."""
        model_lower = model_name.lower()

        for provider, patterns in self.PROVIDER_PATTERNS.items():
            for pattern in patterns:
                if pattern in model_lower:
                    return provider

        return self._default_provider

    def _classify_error(self, error: Exception) -> LLMCallStatus:
        """Classify error type."""
        error_str = str(error).lower()
        error_type = type(error).__name__.lower()

        if "timeout" in error_str or "timeout" in error_type:
            return LLMCallStatus.TIMEOUT

        if "rate" in error_str and "limit" in error_str:
            return LLMCallStatus.RATE_LIMITED

        if "429" in error_str:
            return LLMCallStatus.RATE_LIMITED

        if "auth" in error_str or "401" in error_str or "403" in error_str:
            return LLMCallStatus.AUTH_FAILURE

        if "validation" in error_str or "invalid" in error_str:
            return LLMCallStatus.VALIDATION_ERROR

        if "circuit" in error_str:
            return LLMCallStatus.CIRCUIT_BREAKER

        return LLMCallStatus.ERROR

    async def generate(
        self,
        model: str,
        messages: list[dict],
        temperature: float = 0.7,
        max_tokens: int = 1000,
        tools: Optional[list[dict]] = None,
    ) -> str:
        """
        Generate response with telemetry.

        Returns only the text response.
        """
        provider = self._detect_provider(model)

        ctx = self._telemetry.start_call(
            provider=provider,
            model=model,
            operation="generate",
            temperature=temperature,
            max_tokens=max_tokens,
            has_tools=tools is not None,
        )

        with self._tracing.start_span(
            name=f"llm.{provider}.generate",
            kind=SpanKind.CLIENT,
            attributes={
                "llm.provider": provider,
                "llm.model": model,
                "llm.operation": "generate",
                "llm.temperature": temperature,
                "llm.message_count": len(messages),
            },
        ) as span:
            try:
                response = await self._gateway.generate(
                    model=model,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    tools=tools,
                )

                # Estimate tokens from response (approximation)
                input_tokens = sum(len(m.get("content", "")) // 4 for m in messages)
                output_tokens = len(response) // 4

                ctx.complete(
                    status=LLMCallStatus.SUCCESS,
                    input_tokens=input_tokens,
                    output_tokens=output_tokens,
                )

                span.set_status(SpanStatus.OK)
                span.set_attribute("llm.input_tokens_est", input_tokens)
                span.set_attribute("llm.output_tokens_est", output_tokens)

                return response

            except Exception as e:
                error_status = self._classify_error(e)
                ctx.complete(
                    status=error_status,
                    error_message=str(e),
                    error_type=type(e).__name__,
                )
                span.set_status(SpanStatus.ERROR, str(e))
                raise

            finally:
                await self._telemetry.record(ctx)

    async def generate_with_metadata(
        self,
        model: str,
        messages: list[dict],
        temperature: float = 0.7,
        max_tokens: int = 1000,
        tools: Optional[list[dict]] = None,
    ) -> tuple[str, dict]:
        """
        Generate response with metadata and telemetry.

        Returns response text and metadata including tokens and cost.
        """
        provider = self._detect_provider(model)

        ctx = self._telemetry.start_call(
            provider=provider,
            model=model,
            operation="generate_with_metadata",
            temperature=temperature,
            max_tokens=max_tokens,
            has_tools=tools is not None,
        )

        with self._tracing.start_span(
            name=f"llm.{provider}.generate_with_metadata",
            kind=SpanKind.CLIENT,
            attributes={
                "llm.provider": provider,
                "llm.model": model,
                "llm.operation": "generate_with_metadata",
                "llm.temperature": temperature,
                "llm.message_count": len(messages),
            },
        ) as span:
            try:
                response_text, metadata = await self._gateway.generate_with_metadata(
                    model=model,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    tools=tools,
                )

                input_tokens = metadata.get(
                    "input_tokens", metadata.get("tokens_used", 0)
                )
                output_tokens = metadata.get("output_tokens", 0)
                cost_usd = metadata.get("cost_usd", 0.0)

                ctx.complete(
                    status=LLMCallStatus.SUCCESS,
                    input_tokens=input_tokens,
                    output_tokens=output_tokens,
                    cost_usd=cost_usd,
                )

                span.set_status(SpanStatus.OK)
                span.set_attribute("llm.input_tokens", input_tokens)
                span.set_attribute("llm.output_tokens", output_tokens)
                span.set_attribute("llm.cost_usd", cost_usd)
                span.set_attribute("llm.latency_ms", ctx.duration_ms)

                return response_text, metadata

            except Exception as e:
                error_status = self._classify_error(e)
                ctx.complete(
                    status=error_status,
                    error_message=str(e),
                    error_type=type(e).__name__,
                )
                span.set_status(SpanStatus.ERROR, str(e))
                raise

            finally:
                await self._telemetry.record(ctx)


# ============================================================================
# FACTORY FUNCTION
# ============================================================================


def create_instrumented_gateway(
    gateway: LLMGateway,
    telemetry: Optional[LLMTelemetry] = None,
    tracing: Optional[TracingService] = None,
) -> InstrumentedLLMGateway:
    """
    Factory function to create an instrumented LLM gateway.

    Args:
        gateway: The underlying LLM gateway to wrap
        telemetry: Optional LLM telemetry service
        tracing: Optional tracing service

    Returns:
        Instrumented gateway with full telemetry
    """
    return InstrumentedLLMGateway(
        gateway=gateway,
        telemetry=telemetry,
        tracing=tracing,
    )
