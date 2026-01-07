"""
LLM Client Gateway Adapter.

Adapts the unified LLMGateway interface to provide LLMClientGateway compatibility
for the Agent Squad bounded context.

This adapter enables:
- Single LLM implementation in production
- No changes to existing agents
- Gradual migration path to unified interface
"""

import json
import re
from typing import Optional

from app.domain.ports.agent_squad.llm_client_gateway import LLMClientGateway
from app.domain.ports.ai.llm_gateway import LLMGateway


class LLMClientGatewayAdapter(LLMClientGateway):
    """
    Adapter that implements LLMClientGateway using LLMGateway.

    Translates specialized agent squad calls into unified LLM gateway calls.
    """

    def __init__(self, llm_gateway: LLMGateway):
        """
        Initialize with unified LLM gateway.

        Args:
            llm_gateway: The unified LLM gateway to delegate to
        """
        self._llm = llm_gateway

    async def classify_intent(
        self,
        prompt: str,
        model: str,
    ) -> dict:
        """
        Classify intent using LLM via unified gateway.

        Translates to generate() call with intent classification prompt.
        """
        messages = [
            {
                "role": "system",
                "content": """You are an intent classifier. Analyze the prompt and classify the intent.
Return JSON: {"intent": "...", "confidence": 0.0-1.0, "reasoning": "..."}""",
            },
            {"role": "user", "content": prompt},
        ]

        response = await self._llm.generate(
            model=model,
            messages=messages,
            temperature=0.1,  # Low for consistent classification
            max_tokens=300,
        )

        return self._parse_json_response(response, {
            "intent": "unknown",
            "confidence": 0.5,
            "reasoning": response,
        })

    async def recommend_agents(
        self,
        prompt: str,
        model: str,
    ) -> dict:
        """
        Recommend agents for complex task via unified gateway.
        """
        messages = [
            {
                "role": "system",
                "content": """You are an agent recommender. Analyze the task and recommend the best agents.
Return JSON: {"agents": ["agent1", "agent2"], "reasoning": "..."}""",
            },
            {"role": "user", "content": prompt},
        ]

        response = await self._llm.generate(
            model=model,
            messages=messages,
            temperature=0.3,
            max_tokens=500,
        )

        return self._parse_json_response(response, {
            "agents": [],
            "reasoning": response,
        })

    async def plan_workflow(
        self,
        prompt: str,
        max_agents: int,
    ) -> dict:
        """
        Plan multi-agent workflow via unified gateway.
        """
        messages = [
            {
                "role": "system",
                "content": f"""You are a workflow planner. Create a plan with up to {max_agents} agents.
Return JSON: {{"tasks": [{{"agent": "...", "task": "...", "order": 1}}]}}""",
            },
            {"role": "user", "content": prompt},
        ]

        response = await self._llm.generate(
            model="meta-llama/Meta-Llama-3.1-70B-Instruct",  # Use DeepInfra Llama model for planning
            messages=messages,
            temperature=0.3,
            max_tokens=800,
        )

        return self._parse_json_response(response, {
            "tasks": [],
        })

    async def chat(
        self,
        messages: list[dict],
        model: str,
        temperature: float = 0.7,
        max_tokens: int = 1000,
    ) -> dict:
        """
        Chat completion via unified gateway.

        Translates generate() response to chat format expected by agents.
        """
        response = await self._llm.generate(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )

        # Return in expected chat format
        return {
            "content": response,
            "role": "assistant",
            "tokens_used": len(response.split()) * 2,  # Rough estimate
            "model": model,
        }

    async def generate(
        self,
        model: str,
        messages: list[dict],
        temperature: float = 0.7,
        max_tokens: int = 1000,
    ) -> str:
        """
        Generate text completion (direct passthrough).
        """
        return await self._llm.generate(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )

    def _parse_json_response(self, response: str, default: dict) -> dict:
        """
        Parse JSON from LLM response with fallback.
        """
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            # Try to extract JSON from response
            json_match = re.search(r"\{.*\}", response, re.DOTALL)
            if json_match:
                try:
                    return json.loads(json_match.group(0))
                except json.JSONDecodeError:
                    pass
            return default
