"""
Vertex AI distillation provider.

Implements distillation using Google Cloud Vertex AI.
"""
import json
import time
from typing import Dict, Any, Optional
import logging

from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)

from app.domain.entities.distillation import DistillationRequest, DistillationResult
from app.domain.ports.distillator import (
    Distillator,
    DistillationError,
    DistillationTimeoutError,
    DistillationRateLimitError,
    DistillationAuthenticationError,
    DistillationInvalidResponseError,
)
from app.setup.config.distillation import DistillationSettings
from app.infrastructure.distillation.prompt_templates import build_distillation_prompt

logger = logging.getLogger(__name__)


class VertexAIDistillator:
    """
    Vertex AI implementation of the Distillator port.
    
    Uses Google Cloud Vertex AI's Gemini models for request validation.
    """
    
    def __init__(
        self,
        settings: DistillationSettings,
    ):
        """
        Initialize Vertex AI distillator.
        
        Args:
            settings: Distillation settings including Vertex AI config
        """
        self.settings = settings
        self.vertex_settings = settings.vertex_ai
        self.provider_name = "vertex_ai"
        self.model_name = self.vertex_settings.model
        
        # Lazy import - prefer new google.genai SDK with API key
        try:
            if self.vertex_settings.api_key:
                # Use new google.genai SDK (recommended)
                import google.genai as genai

                self.use_genai_sdk = True
                self.genai_client = genai.Client(api_key=self.vertex_settings.api_key)

                logger.info(
                    f"Vertex AI initialized with Google Genai SDK (API Key): "
                    f"project={self.vertex_settings.project_id}, model={self.model_name}"
                )
            else:
                # Fallback to old Vertex AI SDK (requires service account)
                from google.cloud import aiplatform
                from google.oauth2 import service_account
                import google.auth.exceptions

                self.use_genai_sdk = False
                self.aiplatform = aiplatform
                self.service_account = service_account
                self.google_auth_exceptions = google.auth.exceptions

                # Initialize Vertex AI
                if self.vertex_settings.credentials_path:
                    credentials = self.service_account.Credentials.from_service_account_file(
                        self.vertex_settings.credentials_path
                    )
                    self.aiplatform.init(
                        project=self.vertex_settings.project_id,
                        location=self.vertex_settings.location,
                        credentials=credentials,
                    )
                    logger.info(
                        f"Vertex AI initialized with Service Account: project={self.vertex_settings.project_id}, "
                        f"location={self.vertex_settings.location}, model={self.model_name}"
                    )
                else:
                    self.aiplatform.init(
                        project=self.vertex_settings.project_id,
                        location=self.vertex_settings.location,
                    )
                    logger.info(
                        f"Vertex AI initialized with default credentials: project={self.vertex_settings.project_id}, "
                        f"location={self.vertex_settings.location}, model={self.model_name}"
                    )

        except ImportError as e:
            raise DistillationError(
                message="google-genai or google-cloud-aiplatform not installed. Run: pip install google-genai",
                provider=self.provider_name,
                error_code="missing_dependency",
                retryable=False,
            ) from e
        except Exception as e:
            logger.error(f"Failed to initialize Vertex AI: {e}")
            raise DistillationAuthenticationError(provider=self.provider_name) from e
        
        # Setup retry decorator
        retry_config = settings.retry
        if retry_config.enabled:
            self._retry_decorator = retry(
                stop=stop_after_attempt(retry_config.max_retries),
                wait=wait_exponential(
                    multiplier=1,
                    min=retry_config.initial_backoff_seconds,
                    max=retry_config.max_backoff_seconds,
                ),
                retry=retry_if_exception_type((
                    DistillationTimeoutError,
                    DistillationRateLimitError,
                )),
                reraise=True,
            )
        else:
            # No retry decorator
            self._retry_decorator = lambda f: f
    
    async def validate(
        self,
        request: DistillationRequest,
    ) -> DistillationResult:
        """
        Validate a user request using Vertex AI.
        
        Args:
            request: The distillation request
        
        Returns:
            DistillationResult with validation decision
        
        Raises:
            DistillationError: If validation fails due to provider error
        """
        start_time = time.time()
        
        try:
            # Build prompt
            prompt = build_distillation_prompt(
                user_message=request.user_message,
                conversation_history=request.conversation_history,
                detected_language=request.detected_language or "en",
            )
            
            # Call Vertex AI with retry
            response_text, tokens_used = await self._call_vertex_ai_with_retry(prompt)
            
            # Parse response
            response_data = self._parse_response(response_text)
            
            # Calculate metrics
            latency_ms = (time.time() - start_time) * 1000
            cost_usd = self._calculate_cost(tokens_used)
            
            # Create result
            result = DistillationResult(
                success=response_data.get("success", False),
                message=response_data.get("message", ""),
                reason=response_data.get("reason", "system_error"),
                confidence=response_data.get("confidence", 0.0),
                provider=self.provider_name,
                model=self.model_name,
                detected_language=request.detected_language or "en",
                latency_ms=latency_ms,
                tokens_used=tokens_used,
                cost_usd=cost_usd,
            )
            
            logger.info(
                f"Vertex AI validation complete: success={result.success}, "
                f"reason={result.reason}, latency={latency_ms:.0f}ms"
            )
            
            return result
        
        except DistillationError:
            # Re-raise distillation errors
            raise
        
        except Exception as e:
            logger.error(f"Unexpected error in Vertex AI distillation: {e}")
            raise DistillationError(
                message=f"Unexpected error: {str(e)}",
                provider=self.provider_name,
                error_code="unexpected",
                retryable=False,
            ) from e
    
    async def _call_vertex_ai_with_retry(self, prompt: str) -> tuple[str, int]:
        """
        Call Vertex AI API with retry support.

        Args:
            prompt: The prompt to send

        Returns:
            Tuple of (response_text, tokens_used)

        Raises:
            DistillationError: On API errors
        """
        @self._retry_decorator
        async def _call():
            try:
                if self.use_genai_sdk:
                    # Use new google.genai SDK (simpler, API key based)
                    response = self.genai_client.models.generate_content(
                        model=self.model_name,
                        contents=prompt,
                        config={
                            "temperature": self.settings.temperature,
                            "max_output_tokens": self.settings.max_tokens,
                        },
                    )

                    response_text = response.text

                    # Get token usage if available
                    tokens_used = 0
                    if hasattr(response, 'usage_metadata'):
                        tokens_used = (
                            response.usage_metadata.prompt_token_count +
                            response.usage_metadata.candidates_token_count
                        )
                    else:
                        # Estimate tokens
                        tokens_used = len(prompt) // 4 + len(response_text) // 4

                    return response_text, tokens_used
                else:
                    # Use old Vertex AI SDK (service account based)
                    from google.cloud.aiplatform_v1beta1.types import content as gapic_content_types
                    from vertexai.generative_models import GenerativeModel, Part

                    # Initialize model
                    model = GenerativeModel(self.model_name)

                    # Generate content
                    response = model.generate_content(
                        [Part.from_text(prompt)],
                        generation_config={
                            "temperature": self.settings.temperature,
                            "max_output_tokens": self.settings.max_tokens,
                        },
                    )

                    # Extract response
                    if not response.candidates:
                        raise DistillationInvalidResponseError(
                            provider=self.provider_name,
                            details="No candidates in response",
                        )

                    response_text = response.text

                    # Estimate tokens (Vertex AI doesn't always return usage)
                    tokens_used = len(prompt) // 4 + len(response_text) // 4
                    if hasattr(response, 'usage_metadata'):
                        tokens_used = (
                            response.usage_metadata.prompt_token_count +
                            response.usage_metadata.candidates_token_count
                        )

                    return response_text, tokens_used

            except TimeoutError as e:
                raise DistillationTimeoutError(
                    provider=self.provider_name,
                    timeout_seconds=self.settings.timeout_seconds,
                ) from e

            except Exception as e:
                error_str = str(e).lower()

                # Check for rate limit
                if "quota" in error_str or "rate limit" in error_str:
                    raise DistillationRateLimitError(provider=self.provider_name) from e

                # Check for authentication
                if "auth" in error_str or "permission" in error_str or "credentials" in error_str:
                    raise DistillationAuthenticationError(provider=self.provider_name) from e

                # Generic error
                raise DistillationError(
                    message=f"Vertex AI API error: {str(e)}",
                    provider=self.provider_name,
                    error_code="api_error",
                    retryable=True,
                ) from e

        return await _call()
    
    def _parse_response(self, response_text: str) -> Dict[str, Any]:
        """
        Parse JSON response from LLM.
        
        Args:
            response_text: Raw response text
        
        Returns:
            Parsed response dictionary
        
        Raises:
            DistillationInvalidResponseError: If parsing fails
        """
        try:
            # Remove markdown code blocks if present
            text = response_text.strip()
            if text.startswith("```json"):
                text = text[7:]
            if text.startswith("```"):
                text = text[3:]
            if text.endswith("```"):
                text = text[:-3]
            text = text.strip()
            
            # Parse JSON
            data = json.loads(text)
            
            # Validate required fields
            required_fields = ["success", "message", "reason", "confidence"]
            for field in required_fields:
                if field not in data:
                    raise ValueError(f"Missing required field: {field}")
            
            return data
        
        except (json.JSONDecodeError, ValueError) as e:
            logger.error(f"Failed to parse Vertex AI response: {response_text[:200]}")
            raise DistillationInvalidResponseError(
                provider=self.provider_name,
                details=f"JSON parse error: {str(e)}",
            ) from e
    
    def _calculate_cost(self, tokens_used: int) -> float:
        """
        Calculate cost of API call.
        
        Args:
            tokens_used: Number of tokens used
        
        Returns:
            Cost in USD
        """
        # Gemini 1.5 Flash pricing: $0.10 per 1M tokens (approximate)
        cost_per_1m_tokens = 0.10
        return (tokens_used / 1_000_000) * cost_per_1m_tokens
    
    def get_provider_name(self) -> str:
        """Get provider name."""
        return self.provider_name
    
    def get_model_name(self) -> str:
        """Get model name."""
        return self.model_name
    
    async def check_health(self) -> Dict[str, Any]:
        """
        Check health of Vertex AI.
        
        Returns:
            Health status dictionary
        """
        start_time = time.time()
        
        try:
            # Simple test prompt
            test_prompt = "Respond with 'OK' in JSON: {\"status\": \"OK\"}"
            
            _, _ = await self._call_vertex_ai_with_retry(test_prompt)
            
            latency_ms = (time.time() - start_time) * 1000
            
            return {
                "healthy": True,
                "latency_ms": latency_ms,
                "error": None,
            }
        
        except Exception as e:
            latency_ms = (time.time() - start_time) * 1000
            
            return {
                "healthy": False,
                "latency_ms": latency_ms,
                "error": str(e),
            }
    
    async def close(self) -> None:
        """Close resources (no-op for Vertex AI)."""
        logger.info("Vertex AI distillator closed")
