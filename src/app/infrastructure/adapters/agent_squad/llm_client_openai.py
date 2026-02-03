"""
LLM Client OpenAI adapter - OpenAI API integration.
"""

import json
from typing import Any
import openai

from app.domain.ports.agent_squad.llm_client_gateway import LLMClientGateway


class LLMClientGateway:
    """
    LLM Client OpenAI adapter.

    Implements: LLMClientGateway

    Provides access to OpenAI API for:
    - Intent classification
    - Agent recommendation
    - Workflow planning
    - Chat completion
    """

    def __init__(self, api_key: str):
        """
        Initialize OpenAI client.

        Args:
            api_key: OpenAI API key
        """
        self._client = openai.AsyncOpenAI(api_key=api_key)

    async def classify_intent(
        self,
        prompt: str,
        model: str,
    ) -> dict:
        """
        Classify intent using OpenAI.

        Returns JSON with: intent, confidence, reasoning
        """
        response = await self._client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "system",
                    "content": "You are an intent classification assistant. Always respond with valid JSON.",
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.1,
            response_format={"type": "json_object"},
        )

        content = response.choices[0].message.content
        return self._parse_json(content)

    async def recommend_agents(
        self,
        prompt: str,
        model: str,
    ) -> dict:
        """
        Recommend agents for complex task.

        Returns JSON with: agents (list), reasoning
        """
        response = await self._client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "system",
                    "content": "You are an AI agent coordinator. Always respond with valid JSON.",
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.2,
            response_format={"type": "json_object"},
        )

        content = response.choices[0].message.content
        return self._parse_json(content)

    async def plan_workflow(
        self,
        prompt: str,
        max_agents: int,
    ) -> dict:
        """
        Plan multi-agent workflow.

        Returns JSON with: tasks (list of task objects)
        """
        response = await self._client.chat.completions.create(
            model="gpt-4o",  # Use best model for planning
            messages=[
                {
                    "role": "system",
                    "content": "You are a workflow planning assistant. Always respond with valid JSON.",
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.2,
            response_format={"type": "json_object"},
        )

        content = response.choices[0].message.content
        return self._parse_json(content)

    async def chat(
        self,
        messages: list[dict],
        model: str,
        temperature: float = 0.7,
        max_tokens: int = 1000,
    ) -> dict:
        """
        Chat completion.

        Returns dict with: content, tokens_used, finish_reason
        """
        response = await self._client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )

        return {
            "content": response.choices[0].message.content,
            "tokens_used": response.usage.total_tokens if response.usage else None,
            "prompt_tokens": response.usage.prompt_tokens if response.usage else None,
            "completion_tokens": response.usage.completion_tokens
            if response.usage
            else None,
            "finish_reason": response.choices[0].finish_reason,
            "model": response.model,
        }

    async def generate(
        self,
        model: str,
        messages: list[dict],
        temperature: float = 0.7,
        max_tokens: int = 1000,
    ) -> str:
        """
        Generate text completion (simple string response).

        Returns generated text content directly.
        """
        response = await self._client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )

        return response.choices[0].message.content

    def _parse_json(self, content: str) -> dict[str, Any]:
        """Parse JSON response, handle errors."""
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            # Fallback: try to extract JSON from markdown code blocks
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
                return json.loads(content)
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()
                return json.loads(content)
            else:
                # Last resort: return content as-is in dict
                return {"content": content}
