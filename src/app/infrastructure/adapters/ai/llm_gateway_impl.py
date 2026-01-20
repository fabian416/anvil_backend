from typing import Optional
from app.domain.ports.ai.llm_gateway import LLMGateway
from app.domain.enums.ai.llm_provider import LLMProvider
from app.infrastructure.factories.ai.llm_provider_factory import LLMProviderFactory
from app.infrastructure.adapters.ai.llm.retry_handler import RetryHandler

class LLMGatewayImpl(LLMGateway):
    """
    Production implementation of LLMGateway.

    Supports multiple LLM providers with automatic fallback:
    - Vertex AI (Primary)
    - DeepInfra (Fallback)
    """

    def __init__(self, factory: LLMProviderFactory):
        self._factory = factory

    async def generate(
        self,
        model: str,
        messages: list[dict],
        temperature: float = 0.7,
        max_tokens: int = 1000,
        tools: Optional[list[dict]] = None,
    ) -> str:
        """Generate text completion (delegates to generate_with_metadata)."""
        text, _ = await self.generate_with_metadata(
            model, messages, temperature, max_tokens, tools
        )
        return text

    async def generate_with_metadata(
        self,
        model: str,
        messages: list[dict],
        temperature: float = 0.7,
        max_tokens: int = 1000,
        tools: Optional[list[dict]] = None,
    ) -> tuple[str, dict]:
        """
        Generate text with usage metadata.

        Provider Priority: Vertex AI (Primary) -> DeepInfra (Fallback)
        """

        # Try Vertex AI first, fallback to DeepInfra if not available/configured
        primary_strategy = None
        fallback_strategy = None
        provider_used = None

        # Try to get Vertex AI strategy (primary)
        try:
            primary_strategy = self._factory.get_strategy(LLMProvider.VERTEX)
            provider_used = "vertex_ai"
        except (NotImplementedError, KeyError, ValueError, Exception) as e:
            # Vertex AI not available, will use DeepInfra fallback
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Vertex AI not available: {e}, falling back to DeepInfra")
        
        # Get DeepInfra strategy (fallback)
        try:
            fallback_strategy = self._factory.get_strategy(LLMProvider.DEEPINFRA)
        except Exception as fallback_error:
            if primary_strategy is None:
                raise RuntimeError(
                    f"Failed to initialize LLM providers. "
                    f"Vertex AI: {str(e) if 'e' in locals() else 'not configured'}, "
                    f"DeepInfra: {str(fallback_error)}"
                ) from fallback_error

        # Use primary if available, otherwise fallback
        strategy_to_use = primary_strategy if primary_strategy else fallback_strategy
        if strategy_to_use is None:
            raise RuntimeError("No LLM provider strategy available")
        
        # Track which provider will be used (for metadata)
        if not provider_used:
            provider_used = "deepinfra" if fallback_strategy else "unknown"
        
        # Create retry chain with fallback
        if primary_strategy and fallback_strategy:
            # Chain: primary -> fallback
            fallback_chain = RetryHandler(fallback_strategy)
            chain = RetryHandler(primary_strategy, fallback_chain)
        else:
            # Single strategy (no fallback)
            chain = RetryHandler(strategy_to_use)

        response_data = await chain.handle(
            model,
            messages,
            temperature=temperature,
            max_tokens=max_tokens
        )

        # Extract text and metadata from response
        # RetryHandler returns Tuple[str, Dict[str, Any]] from LLMStrategy.generate()
        if isinstance(response_data, tuple) and len(response_data) >= 2:
            text, provider_metadata = response_data[0], response_data[1]
            # Normalize text (ensure it's a string, not nested)
            if not isinstance(text, str):
                text = str(text)
            metadata = {
                "tokens_used": provider_metadata.get("input_tokens", 0) + provider_metadata.get("output_tokens", 0),
                "model": provider_metadata.get("model", model),
                "latency_ms": provider_metadata.get("latency_ms", 0),
                "finish_reason": "stop",
                "provider": provider_metadata.get("provider", provider_used or "unknown"),
                "cost_usd": provider_metadata.get("cost_usd", 0),
            }
            return text, metadata
        elif isinstance(response_data, dict):
            text = response_data.get("content", "")
            metadata = {
                "tokens_used": response_data.get("tokens_used", 0),
                "model": model,
                "latency_ms": response_data.get("latency_ms", 0),
                "finish_reason": response_data.get("finish_reason", "stop"),
            }
            return text, metadata
        else:
            # Fallback for unexpected return format
            return str(response_data), {"tokens_used": 0, "model": model, "latency_ms": 0, "finish_reason": "stop"}
