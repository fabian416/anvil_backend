from typing import Protocol, Optional


class LLMGateway(Protocol):
    """
    Unified LLM gateway for all AI interactions.

    Consolidates previous LLMGateway and LLMClientGateway interfaces.
    This defines the contract for multi-model LLM operations.

    Implementations:
    - LLMGatewayImpl: Production adapter with Vertex AI, DeepInfra, OpenAI
    - MockLLMGateway: Test mock for deterministic responses
    """

    async def generate(
        self,
        model: str,
        messages: list[dict],
        temperature: float = 0.7,
        max_tokens: int = 1000,
        tools: Optional[list[dict]] = None,
    ) -> str:
        """
        Generate text completion.

        Args:
            model: Model identifier (e.g., "gpt-4o-mini", "claude-sonnet-4")
            messages: Conversation messages [{"role": "user", "content": "..."}]
            temperature: Sampling temperature (0.0-1.0)
            max_tokens: Maximum response tokens
            tools: Optional tool definitions for function calling

        Returns:
            Generated text response

        Example:
            >>> response = await gateway.generate(
            ...     model="gpt-4o-mini",
            ...     messages=[
            ...         {"role": "system", "content": "You are a helpful assistant"},
            ...         {"role": "user", "content": "Hello"},
            ...     ],
            ...     temperature=0.7,
            ... )
        """
        ...

    async def generate_with_metadata(
        self,
        model: str,
        messages: list[dict],
        temperature: float = 0.7,
        max_tokens: int = 1000,
        tools: Optional[list[dict]] = None,
    ) -> tuple[str, dict]:
        """
        Generate with usage metadata.

        Args:
            model: Model identifier (e.g., "gpt-4o-mini", "claude-sonnet-4")
            messages: Conversation messages [{"role": "user", "content": "..."}]
            temperature: Sampling temperature (0.0-1.0)
            max_tokens: Maximum response tokens
            tools: Optional tool definitions for function calling

        Returns:
            Tuple of (response_text, metadata)
            metadata = {
                "tokens_used": int,
                "model": str,
                "latency_ms": int,
                "finish_reason": str,
            }

        Example:
            >>> response, metadata = await gateway.generate_with_metadata(
            ...     model="gpt-4o-mini",
            ...     messages=[{"role": "user", "content": "Hello"}],
            ... )
            >>> print(f"Used {metadata['tokens_used']} tokens")
        """
        ...
