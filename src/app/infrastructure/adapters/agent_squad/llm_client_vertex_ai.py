"""
LLM Client Vertex AI adapter - Google Gemini API integration.
"""

import json
from typing import Any
import logging

from app.domain.ports.agent_squad.llm_client_gateway import LLMClientGateway

logger = logging.getLogger(__name__)


class LLMClientVertexAI:
    """
    LLM Client Vertex AI adapter.

    Implements: LLMClientGateway

    Provides access to Google Gemini API for:
    - Intent classification
    - Agent recommendation
    - Workflow planning
    - Chat completion
    """

    def __init__(self, api_key: str, model_mapping: dict[str, str] | None = None):
        """
        Initialize Vertex AI client.

        Args:
            api_key: Google Cloud API key
            model_mapping: Map OpenAI model names to Gemini models
                          Example: {"gpt-4o": "gemini-2.0-flash-exp", "gpt-4o-mini": "gemini-2.0-flash-exp"}
        """
        try:
            import google.genai as genai
            self._client = genai.Client(api_key=api_key)
            self._genai = genai
            logger.info("Vertex AI LLM client initialized with Google Genai SDK")
        except ImportError as e:
            raise RuntimeError(
                "google-genai not installed. Run: pip install google-genai"
            ) from e

        # Default model mapping (OpenAI model names -> Gemini models)
        self._model_mapping = model_mapping or {
            "gpt-4o": "gemini-2.0-flash-exp",
            "gpt-4o-mini": "gemini-2.0-flash-exp",
            "gpt-4": "gemini-1.5-pro",
            "gpt-3.5-turbo": "gemini-2.0-flash-exp",
        }

    def _map_model(self, openai_model: str) -> str:
        """Map OpenAI model name to Gemini model."""
        return self._model_mapping.get(openai_model, "gemini-2.0-flash-exp")

    async def classify_intent(
        self,
        prompt: str,
        model: str,
    ) -> dict:
        """
        Classify intent using Gemini.

        Returns JSON with: intent, confidence, reasoning
        """
        gemini_model = self._map_model(model)

        full_prompt = (
            "You are an intent classification assistant. Always respond with valid JSON.\n\n"
            f"{prompt}"
        )

        response = self._client.models.generate_content(
            model=gemini_model,
            contents=full_prompt,
            config={
                "temperature": 0.1,
                "response_mime_type": "application/json",
            },
        )

        content = response.text
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
        gemini_model = self._map_model(model)

        full_prompt = (
            "You are an AI agent coordinator. Always respond with valid JSON.\n\n"
            f"{prompt}"
        )

        response = self._client.models.generate_content(
            model=gemini_model,
            contents=full_prompt,
            config={
                "temperature": 0.2,
                "response_mime_type": "application/json",
            },
        )

        content = response.text
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
        gemini_model = "gemini-1.5-pro"

        full_prompt = (
            "You are a workflow planning assistant. Always respond with valid JSON.\n\n"
            f"{prompt}"
        )

        response = self._client.models.generate_content(
            model=gemini_model,
            contents=full_prompt,
            config={
                "temperature": 0.2,
                "response_mime_type": "application/json",
            },
        )

        content = response.text
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
        gemini_model = self._map_model(model)

        # Convert OpenAI-style messages to Gemini format
        prompt = self._convert_messages_to_prompt(messages)

        response = self._client.models.generate_content(
            model=gemini_model,
            contents=prompt,
            config={
                "temperature": temperature,
                "max_output_tokens": max_tokens,
            },
        )

        # Extract token usage
        tokens_used = 0
        prompt_tokens = 0
        completion_tokens = 0

        if hasattr(response, 'usage_metadata'):
            prompt_tokens = response.usage_metadata.prompt_token_count
            completion_tokens = response.usage_metadata.candidates_token_count
            tokens_used = prompt_tokens + completion_tokens

        return {
            "content": response.text,
            "tokens_used": tokens_used,
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "finish_reason": "stop",  # Gemini doesn't provide finish reason
            "model": gemini_model,
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
        gemini_model = self._map_model(model)

        # Convert OpenAI-style messages to Gemini format
        prompt = self._convert_messages_to_prompt(messages)

        response = self._client.models.generate_content(
            model=gemini_model,
            contents=prompt,
            config={
                "temperature": temperature,
                "max_output_tokens": max_tokens,
            },
        )

        return response.text

    def _convert_messages_to_prompt(self, messages: list[dict]) -> str:
        """Convert OpenAI-style messages to a single prompt for Gemini."""
        prompt_parts = []

        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")

            if role == "system":
                prompt_parts.append(f"Instructions: {content}")
            elif role == "user":
                prompt_parts.append(f"User: {content}")
            elif role == "assistant":
                prompt_parts.append(f"Assistant: {content}")

        return "\n\n".join(prompt_parts)

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
