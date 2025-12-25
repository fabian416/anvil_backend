"""
LLM Client DeepInfra adapter - OpenAI-compatible API integration.
"""

import json
from typing import Any
import logging
import openai

from app.domain.ports.agent_squad.llm_client_gateway import LLMClientGateway

logger = logging.getLogger(__name__)


class LLMClientDeepInfra:
    """
    LLM Client DeepInfra adapter.

    Implements: LLMClientGateway

    Provides access to DeepInfra API (OpenAI-compatible) for:
    - Intent classification
    - Agent recommendation
    - Workflow planning
    - Chat completion
    """

    def __init__(
        self,
        api_key: str,
        base_url: str = "https://api.deepinfra.com/v1/openai",
        model_mapping: dict[str, str] | None = None,
    ):
        """
        Initialize DeepInfra client.

        Args:
            api_key: DeepInfra API key
            base_url: DeepInfra base URL (OpenAI-compatible endpoint)
            model_mapping: Map OpenAI model names to DeepInfra models
                          Example: {"gpt-4o": "meta-llama/Meta-Llama-3.1-70B-Instruct"}
        """
        self._client = openai.AsyncOpenAI(
            api_key=api_key,
            base_url=base_url,
        )
        logger.info(f"DeepInfra LLM client initialized with base_url={base_url}")

        # Default model mapping (OpenAI model names -> DeepInfra models)
        self._model_mapping = model_mapping or {
            "gpt-4o": "meta-llama/Meta-Llama-3.1-70B-Instruct",
            "gpt-4o-mini": "meta-llama/Llama-3.2-3B-Instruct",
            "gpt-4": "meta-llama/Meta-Llama-3.1-405B-Instruct",
            "gpt-3.5-turbo": "meta-llama/Llama-3.2-3B-Instruct",
        }

    def _map_model(self, openai_model: str) -> str:
        """Map OpenAI model name to DeepInfra model."""
        return self._model_mapping.get(openai_model, "meta-llama/Llama-3.2-3B-Instruct")

    async def classify_intent(
        self,
        prompt: str,
        model: str,
    ) -> dict:
        """
        Classify intent using DeepInfra.

        Returns JSON with: intent, confidence, reasoning
        """
        deepinfra_model = self._map_model(model)

        response = await self._client.chat.completions.create(
            model=deepinfra_model,
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
        deepinfra_model = self._map_model(model)

        response = await self._client.chat.completions.create(
            model=deepinfra_model,
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
        # Use best model for planning
        deepinfra_model = "meta-llama/Meta-Llama-3.1-405B-Instruct"

        response = await self._client.chat.completions.create(
            model=deepinfra_model,
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
        deepinfra_model = self._map_model(model)

        response = await self._client.chat.completions.create(
            model=deepinfra_model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )

        return {
            "content": response.choices[0].message.content,
            "tokens_used": response.usage.total_tokens if response.usage else None,
            "prompt_tokens": response.usage.prompt_tokens if response.usage else None,
            "completion_tokens": (
                response.usage.completion_tokens if response.usage else None
            ),
            "finish_reason": response.choices[0].finish_reason,
            "model": response.model,
        }

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
