"""
LLM Client with Fallback - Provides automatic fallback between providers.
"""

import logging
from typing import Optional

from app.domain.ports.agent_squad.llm_client_gateway import LLMClientGateway

logger = logging.getLogger(__name__)


class LLMClientWithFallback:
    """
    LLM Client wrapper with automatic fallback support.

    Tries primary provider first, falls back to secondary on failure.
    """

    def __init__(
        self,
        primary_client: LLMClientGateway,
        fallback_client: Optional[LLMClientGateway] = None,
        enable_fallback: bool = True,
    ):
        """
        Initialize LLM client with fallback.

        Args:
            primary_client: Primary LLM client
            fallback_client: Fallback LLM client (optional)
            enable_fallback: Whether to enable automatic fallback
        """
        self._primary = primary_client
        self._fallback = fallback_client
        self._enable_fallback = enable_fallback and fallback_client is not None

        primary_name = type(primary_client).__name__
        fallback_name = type(fallback_client).__name__ if fallback_client else "None"
        logger.info(
            f"LLM Client initialized: primary={primary_name}, "
            f"fallback={fallback_name}, fallback_enabled={self._enable_fallback}"
        )

    def _map_model_for_fallback(self, model: str) -> str:
        """
        Map Vertex AI model names to DeepInfra model names.

        Args:
            model: Original model name (may be Vertex AI model)

        Returns:
            DeepInfra-compatible model name
        """
        # Vertex AI Gemini models → DeepInfra Llama models
        # This matches the mapping in LLMClientDeepInfra
        model_mapping = {
            "gemini-2.0-flash": "meta-llama/Meta-Llama-3.1-70B-Instruct",  # Most common
            "gemini-2.0-flash-exp": "meta-llama/Meta-Llama-3.1-70B-Instruct",
            "gemini-1.5-flash": "meta-llama/Meta-Llama-3.1-70B-Instruct",
            "gemini-1.5-pro": "meta-llama/Meta-Llama-3.1-405B-Instruct",
            "gemini-2.0-pro": "meta-llama/Meta-Llama-3.1-405B-Instruct",
        }

        # If it's a Vertex AI model, map to DeepInfra equivalent
        if model in model_mapping:
            mapped_model = model_mapping[model]
            logger.info(
                f"🔄 Mapping Vertex AI model '{model}' → DeepInfra model '{mapped_model}' for fallback"
            )
            return mapped_model

        # If it's already a DeepInfra model (starts with meta-llama/) or unknown, return as-is
        if model.startswith("meta-llama/"):
            return model

        # Unknown model - use default DeepInfra model
        default_fallback = "meta-llama/Meta-Llama-3.1-70B-Instruct"
        logger.warning(
            f"⚠️ Unknown model '{model}' for fallback, using default DeepInfra model: {default_fallback}"
        )
        return default_fallback

    async def classify_intent(
        self,
        prompt: str,
        model: str,
    ) -> dict:
        """Classify intent with fallback support."""
        try:
            return await self._primary.classify_intent(prompt, model)
        except Exception as e:
            error_str = str(e)
            is_rate_limit = (
                "429" in error_str
                or "rate limit" in error_str.lower()
                or "resource exhausted" in error_str.lower()
                or "RESOURCE_EXHAUSTED" in error_str
            )

            if self._enable_fallback:
                if is_rate_limit:
                    logger.warning(
                        f"⚠️ Primary provider (Vertex AI) rate limited (429). "
                        f"Falling back to DeepInfra for intent classification."
                    )
                else:
                    logger.warning(
                        f"Primary provider failed for classify_intent: {e}. "
                        f"Falling back to secondary provider."
                    )
                fallback_model = self._map_model_for_fallback(model)
                return await self._fallback.classify_intent(prompt, fallback_model)
            raise

    async def recommend_agents(
        self,
        prompt: str,
        model: str,
    ) -> dict:
        """Recommend agents with fallback support."""
        try:
            return await self._primary.recommend_agents(prompt, model)
        except Exception as e:
            error_str = str(e)
            is_rate_limit = (
                "429" in error_str
                or "rate limit" in error_str.lower()
                or "resource exhausted" in error_str.lower()
                or "RESOURCE_EXHAUSTED" in error_str
            )

            if self._enable_fallback:
                if is_rate_limit:
                    logger.warning(
                        f"⚠️ Primary provider (Vertex AI) rate limited (429). "
                        f"Falling back to DeepInfra for agent recommendation."
                    )
                else:
                    logger.warning(
                        f"Primary provider failed for recommend_agents: {e}. "
                        f"Falling back to secondary provider."
                    )
                fallback_model = self._map_model_for_fallback(model)
                return await self._fallback.recommend_agents(prompt, fallback_model)
            raise

    async def plan_workflow(
        self,
        prompt: str,
        max_agents: int,
    ) -> dict:
        """Plan workflow with fallback support."""
        try:
            return await self._primary.plan_workflow(prompt, max_agents)
        except Exception as e:
            error_str = str(e)
            is_rate_limit = (
                "429" in error_str
                or "rate limit" in error_str.lower()
                or "resource exhausted" in error_str.lower()
                or "RESOURCE_EXHAUSTED" in error_str
            )

            if self._enable_fallback:
                if is_rate_limit:
                    logger.warning(
                        f"⚠️ Primary provider (Vertex AI) rate limited (429). "
                        f"Falling back to DeepInfra for workflow planning."
                    )
                else:
                    logger.warning(
                        f"Primary provider failed for plan_workflow: {e}. "
                        f"Falling back to secondary provider."
                    )
                return await self._fallback.plan_workflow(prompt, max_agents)
            raise

    async def chat(
        self,
        messages: list[dict],
        model: str,
        temperature: float = 0.7,
        max_tokens: int = 1000,
    ) -> dict:
        """Chat completion with fallback support."""
        try:
            return await self._primary.chat(messages, model, temperature, max_tokens)
        except Exception as e:
            error_str = str(e)
            # Check if it's a rate limit error (429)
            is_rate_limit = (
                "429" in error_str
                or "rate limit" in error_str.lower()
                or "resource exhausted" in error_str.lower()
                or "RESOURCE_EXHAUSTED" in error_str
            )

            if self._enable_fallback:
                if is_rate_limit:
                    logger.warning(
                        f"⚠️ Primary provider (Vertex AI) rate limited (429). "
                        f"Falling back to DeepInfra for chat completion."
                    )
                else:
                    logger.warning(
                        f"Primary provider failed for chat: {e}. "
                        f"Falling back to secondary provider."
                    )
                # Map Vertex AI model to DeepInfra model if needed
                fallback_model = self._map_model_for_fallback(model)
                return await self._fallback.chat(
                    messages, fallback_model, temperature, max_tokens
                )
            raise

    async def generate(
        self,
        model: str,
        messages: list[dict],
        temperature: float = 0.7,
        max_tokens: int = 1000,
    ) -> str:
        """Generate text completion with fallback support."""
        try:
            return await self._primary.generate(
                model, messages, temperature, max_tokens
            )
        except Exception as e:
            error_str = str(e)
            # Check if it's a rate limit error (429)
            is_rate_limit = (
                "429" in error_str
                or "rate limit" in error_str.lower()
                or "resource exhausted" in error_str.lower()
                or "RESOURCE_EXHAUSTED" in error_str
            )

            if self._enable_fallback:
                if is_rate_limit:
                    logger.warning(
                        f"⚠️ Primary provider (Vertex AI) rate limited (429). "
                        f"Falling back to DeepInfra for text generation."
                    )
                else:
                    logger.warning(
                        f"Primary provider failed for generate: {e}. "
                        f"Falling back to secondary provider."
                    )
                # Map Vertex AI model to DeepInfra model if needed
                fallback_model = self._map_model_for_fallback(model)
                return await self._fallback.generate(
                    fallback_model, messages, temperature, max_tokens
                )
            raise
