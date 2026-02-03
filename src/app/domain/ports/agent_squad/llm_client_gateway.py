"""
LLM Client Gateway port.
"""

from typing import Protocol


class LLMClientGateway(Protocol):
    """
    LLM Client Gateway port.

    Implementing adapters:
    - LLMClientVertexAI (Google Vertex AI) - Primary
    - LLMClientDeepInfra (DeepInfra API) - Fallback
    Note: LLMClientOpenAI removed - using only Vertex AI and DeepInfra
    """

    async def classify_intent(
        self,
        prompt: str,
        model: str,
    ) -> dict:
        """
        Classify intent using LLM.

        Args:
            prompt: Classification prompt
            model: Model to use (e.g., "gpt-4o-mini")

        Returns:
            dict with intent, confidence, reasoning
        """
        ...

    async def recommend_agents(
        self,
        prompt: str,
        model: str,
    ) -> dict:
        """
        Recommend agents for complex task.

        Args:
            prompt: Recommendation prompt
            model: Model to use

        Returns:
            dict with agents list and reasoning
        """
        ...

    async def plan_workflow(
        self,
        prompt: str,
        max_agents: int,
    ) -> dict:
        """
        Plan multi-agent workflow.

        Args:
            prompt: Planning prompt
            max_agents: Maximum agents

        Returns:
            dict with tasks list
        """
        ...

    async def chat(
        self,
        messages: list[dict],
        model: str,
        temperature: float = 0.7,
        max_tokens: int = 1000,
    ) -> dict:
        """
        Chat completion.

        Args:
            messages: Conversation messages
            model: Model to use
            temperature: Sampling temperature
            max_tokens: Maximum response tokens

        Returns:
            dict with content, tokens_used, etc.
        """
        ...

    async def generate(
        self,
        model: str,
        messages: list[dict],
        temperature: float = 0.7,
        max_tokens: int = 1000,
    ) -> str:
        """
        Generate text completion (simple string response).

        Args:
            model: Model to use (e.g., "gpt-4o-mini")
            messages: Conversation messages
            temperature: Sampling temperature
            max_tokens: Maximum response tokens

        Returns:
            Generated text response
        """
        ...
