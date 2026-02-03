"""
LLM Client Vertex AI adapter - Google Gemini API integration.

Uses native Gemini model names directly (no OpenAI mapping).
"""

import json
from typing import Any
import logging

from app.domain.ports.agent_squad.llm_client_gateway import LLMClientGateway

logger = logging.getLogger(__name__)

# Default model (DeepInfra-compatible)
DEFAULT_MODEL = "meta-llama/Meta-Llama-3.1-70B-Instruct"


class LLMClientVertexAI:
    """
    LLM Client Vertex AI adapter.

    Implements: LLMClientGateway

    Provides access to Google Gemini API for:
    - Intent classification
    - Agent recommendation
    - Workflow planning
    - Chat completion

    Available models:
    - meta-llama/Meta-Llama-3.1-70B-Instruct  (default, balanced)
    - meta-llama/Meta-Llama-3.1-405B-Instruct (premium, complex reasoning)
    - meta-llama/Llama-3.2-3B-Instruct        (fast, cost-effective)
    """

    def __init__(self, api_key: str, default_model: str = DEFAULT_MODEL):
        """
        Initialize Vertex AI client.

        Args:
            api_key: Google Cloud API key
            default_model: Default model to use (default: meta-llama/Meta-Llama-3.1-70B-Instruct)
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

        self._default_model = default_model

    def _resolve_model(self, model: str) -> str:
        """
        Resolve model name, using default if empty or invalid.

        For intent classification, we prefer gemini-2.0-flash (fast, cost-effective).
        If model is not a Gemini model, use default (for fallback scenarios).
        """
        # For intent classification, prefer fast Gemini model
        if not model:
            return "gemini-2.0-flash"  # Fast model for classification

        # If it's already a Gemini model, use it
        if model.startswith("gemini"):
            return model

        # If it's a DeepInfra model name (for fallback), return default
        # The fallback handler will map it correctly
        if model.startswith("meta-llama/"):
            return self._default_model

        # Unknown model - use fast Gemini model for classification
        return "gemini-2.0-flash"

    async def classify_intent(
        self,
        prompt: str,
        model: str = "gemini-2.0-flash",  # Default to fast model for classification
    ) -> dict:
        """
        Classify intent using Gemini.

        Uses gemini-2.0-flash by default for fast, cost-effective classification.
        Automatically falls back to DeepInfra if Vertex AI is unavailable.

        Returns JSON with: intent, confidence, reasoning
        """
        # Use fast Gemini model for classification (optimized for speed and cost)
        gemini_model = self._resolve_model(model)

        # If model is not a Gemini model (e.g., DeepInfra model for fallback),
        # this will be handled by the fallback mechanism
        if not gemini_model.startswith("gemini"):
            # This shouldn't happen, but if it does, use default
            gemini_model = "gemini-2.0-flash"

        full_prompt = (
            "You are an intent classification assistant. Always respond with valid JSON.\n\n"
            f"{prompt}"
        )

        try:
            response = self._client.models.generate_content(
                model=gemini_model,
                contents=full_prompt,
                config={
                    "temperature": 0.1,  # Low temperature for consistent classification
                    "response_mime_type": "application/json",
                },
            )

            content = response.text
            return self._parse_json(content)
        except Exception as e:
            # Log error and re-raise (fallback will be handled by LLMClientWithFallback)
            logger.error(f"Vertex AI classification error: {e}")
            raise

    async def recommend_agents(
        self,
        prompt: str,
        model: str,
    ) -> dict:
        """
        Recommend agents for complex task.

        Returns JSON with: agents (list), reasoning
        """
        gemini_model = self._resolve_model(model)

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
        gemini_model = self._resolve_model(model)

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

        if hasattr(response, "usage_metadata"):
            prompt_tokens = response.usage_metadata.prompt_token_count or 0
            completion_tokens = response.usage_metadata.candidates_token_count or 0
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
        gemini_model = self._resolve_model(model)

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
