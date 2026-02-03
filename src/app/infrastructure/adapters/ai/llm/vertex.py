"""
Vertex AI Strategy Implementation.

Implements LLMStrategy for Google Vertex AI (Gemini models).
"""

import ssl
import time
import aiohttp
import json
from typing import List, Dict, Any, Tuple, Optional
from app.infrastructure.adapters.ai.llm.strategy import LLMStrategy


class VertexStrategy(LLMStrategy):
    """
    Adapter for Vertex AI API (Gemini models).

    Supports both API key and OAuth token authentication.
    """

    def __init__(
        self,
        project_id: str,
        location: str = "us-central1",
        api_key: Optional[str] = None,
        credentials_path: Optional[str] = None,
    ):
        """
        Initialize Vertex AI strategy.

        Args:
            project_id: GCP project ID
            location: GCP region (default: us-central1)
            api_key: Optional API key for authentication
            credentials_path: Optional path to service account JSON
        """
        self.project_id = project_id
        self.location = location
        self.api_key = api_key
        self.credentials_path = credentials_path
        # Use Generative AI API for API key auth, Platform API for OAuth
        if api_key:
            # Generative AI API (simpler, works with API keys)
            self.base_url = "https://generativelanguage.googleapis.com/v1"
        else:
            # Vertex AI Platform API (requires OAuth)
            self.base_url = f"https://{location}-aiplatform.googleapis.com/v1"
        self._access_token: Optional[str] = None
        self._token_expiry: Optional[float] = None

    async def _get_access_token(self) -> Optional[str]:
        """
        Get OAuth access token if using service account.

        Returns:
            Access token or None if using API key
        """
        if self.api_key:
            # Using API key, no token needed
            return None

        # Check if token is still valid (cache for 50 minutes)
        if self._access_token and self._token_expiry:
            if time.time() < self._token_expiry:
                return self._access_token

        # Get new token using Google Auth
        try:
            from google.auth import default
            from google.auth.transport.requests import Request
            import os

            # Set credentials path if provided
            if self.credentials_path:
                os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = self.credentials_path

            credentials, _ = default(
                scopes=["https://www.googleapis.com/auth/cloud-platform"]
            )
            credentials.refresh(Request())

            self._access_token = credentials.token
            # Token expires in ~1 hour, cache for 50 minutes
            self._token_expiry = time.time() + (50 * 60)

            return self._access_token
        except Exception as e:
            raise Exception(f"Failed to get Vertex AI access token: {e}")

    def _convert_messages(self, messages: List[Dict[str, str]]) -> List[Dict[str, Any]]:
        """
        Convert OpenAI-format messages to Vertex AI format.

        Args:
            messages: List of messages with 'role' and 'content'

        Returns:
            Vertex AI formatted contents
        """
        contents = []
        system_parts = []

        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")

            if role == "system":
                system_parts.append(content)
            elif role == "user":
                # Combine system messages with user message
                user_content = "\n\n".join(system_parts) + (
                    "\n\n" + content if system_parts else content
                )
                contents.append({"role": "user", "parts": [{"text": user_content}]})
                system_parts = []  # Clear after first user message
            elif role == "assistant":
                contents.append({"role": "model", "parts": [{"text": content}]})

        return contents

    async def generate(
        self, model_name: str, messages: List[Dict[str, str]], **kwargs
    ) -> Tuple[str, Dict[str, Any]]:
        """
        Generate text using Vertex AI.

        Args:
            model_name: Model name (e.g., "gemini-2.0-flash-exp")
            messages: Conversation messages
            **kwargs: Additional parameters (temperature, max_tokens, etc.)

        Returns:
            Tuple of (response_text, metadata_dict)
        """
        start_time = time.time()

        # Convert model name to Vertex AI format
        # Only Gemini models work with Vertex AI
        # If model is a DeepInfra model (meta-llama, etc.), raise error to trigger fallback
        if (
            model_name.startswith("meta-llama")
            or "/" in model_name
            and "llama" in model_name.lower()
        ):
            raise ValueError(
                f"Model {model_name} is not a Vertex AI model. Use Gemini models (gemini-*) for Vertex AI."
            )

        # Vertex AI API expects model names like "gemini-2.0-flash" or "gemini-1.5-pro"
        # Use the model name as-is (should already be a Gemini model)
        vertex_model = model_name

        # Build endpoint URL
        if self.api_key:
            # Use Generative AI API (simpler endpoint for API key auth)
            # Format: https://generativelanguage.googleapis.com/v1/models/{model}:generateContent?key={api_key}
            # Model names in Generative AI API: "gemini-2.0-flash-exp", "gemini-1.5-pro", etc.
            endpoint = f"{self.base_url}/models/{vertex_model}:generateContent?key={self.api_key}"
            headers = {"Content-Type": "application/json"}
        else:
            # Use Vertex AI Platform API (requires OAuth)
            # Model names in Platform API: "gemini-2.0-flash-exp", "gemini-1.5-pro", etc.
            endpoint = (
                f"{self.base_url}/projects/{self.project_id}/"
                f"locations/{self.location}/publishers/google/"
                f"models/{vertex_model}:generateContent"
            )
            token = await self._get_access_token()
            if not token:
                raise Exception(
                    "No authentication method available (neither API key nor OAuth token)"
                )
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            }

        # Convert messages to Vertex AI format
        contents = self._convert_messages(messages)

        # Build generation config
        generation_config = {
            "maxOutputTokens": kwargs.get("max_tokens", 1024),
            "temperature": kwargs.get("temperature", 0.7),
        }

        # Build payload - format differs slightly between APIs
        if self.api_key:
            # Generative AI API format
            payload = {
                "contents": contents,
                "generationConfig": generation_config,
            }
        else:
            # Vertex AI Platform API format
            payload = {
                "contents": contents,
                "generationConfig": generation_config,
            }

        # Configure timeout and SSL
        timeout = aiohttp.ClientTimeout(total=60)  # 60 second timeout
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
        connector = aiohttp.TCPConnector(ssl=ssl_context)

        try:
            async with aiohttp.ClientSession(
                timeout=timeout, connector=connector
            ) as session:
                async with session.post(
                    endpoint, headers=headers, json=payload
                ) as response:
                    if response.status != 200:
                        text = await response.text()
                        import logging

                        logger = logging.getLogger(__name__)
                        logger.error(
                            f"Vertex AI API Error {response.status}: {text[:500]}"
                        )
                        logger.error(f"Endpoint: {endpoint[:200]}")
                        logger.error(f"Model: {vertex_model}")
                        raise Exception(
                            f"Vertex AI Error {response.status}: {text[:200]}"
                        )

                    data = await response.json()
        except aiohttp.ClientError as e:
            raise Exception(f"Vertex AI network error: {e}")

        end_time = time.time()
        latency_ms = int((end_time - start_time) * 1000)

        # Parse response
        candidates = data.get("candidates", [])
        if not candidates:
            raise Exception("No candidates in Vertex AI response")

        candidate = candidates[0]
        content_parts = candidate.get("content", {}).get("parts", [])

        # Extract text content
        response_text = ""
        for part in content_parts:
            if "text" in part:
                response_text += part["text"]

        # Extract token usage (format differs between APIs)
        if self.api_key:
            # Generative AI API format
            usage = data.get("usageMetadata", {})
            input_tokens = usage.get("promptTokenCount", 0)
            output_tokens = usage.get("candidatesTokenCount", 0)
        else:
            # Vertex AI Platform API format (same structure)
            usage = data.get("usageMetadata", {})
            input_tokens = usage.get("promptTokenCount", 0)
            output_tokens = usage.get("candidatesTokenCount", 0)

        # Approximate cost calculation for Gemini models
        # gemini-2.0-flash-exp: ~$0.075/1M input, $0.30/1M output
        # gemini-1.5-pro: ~$1.25/1M input, $5.00/1M output
        if "flash" in model_name.lower() or "2.0" in model_name:
            cost = (input_tokens * 0.075 + output_tokens * 0.30) / 1_000_000
        else:
            cost = (input_tokens * 1.25 + output_tokens * 5.00) / 1_000_000

        metadata = {
            "provider": "vertex_ai",
            "model": model_name,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "latency_ms": latency_ms,
            "cost_usd": cost,
        }

        return response_text, metadata
