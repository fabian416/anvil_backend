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

    async def classify_intent(
        self,
        prompt: str,
        model: str,
    ) -> dict:
        """Classify intent with fallback support."""
        try:
            return await self._primary.classify_intent(prompt, model)
        except Exception as e:
            if self._enable_fallback:
                logger.warning(
                    f"Primary provider failed for classify_intent: {e}. "
                    f"Falling back to secondary provider."
                )
                return await self._fallback.classify_intent(prompt, model)
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
            if self._enable_fallback:
                logger.warning(
                    f"Primary provider failed for recommend_agents: {e}. "
                    f"Falling back to secondary provider."
                )
                return await self._fallback.recommend_agents(prompt, model)
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
            if self._enable_fallback:
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
            if self._enable_fallback:
                logger.warning(
                    f"Primary provider failed for chat: {e}. "
                    f"Falling back to secondary provider."
                )
                return await self._fallback.chat(messages, model, temperature, max_tokens)
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
            return await self._primary.generate(model, messages, temperature, max_tokens)
        except Exception as e:
            if self._enable_fallback:
                logger.warning(
                    f"Primary provider failed for generate: {e}. "
                    f"Falling back to secondary provider."
                )
                return await self._fallback.generate(model, messages, temperature, max_tokens)
            raise
