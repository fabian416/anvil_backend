"""
Request distillator orchestrator.

Main application service that coordinates all distillation operations.
"""
import logging
from typing import List, Optional
from uuid import UUID

from app.domain.entities.distillation import DistillationRequest, DistillationResult
from app.domain.entities.message import Message
from app.domain.ports.distillator import (
    Distillator,
    DistillationError,
)
from app.domain.services.distillation.request_preprocessor import RequestPreprocessor
from app.domain.services.distillation.telemetry_collector import DistillationTelemetryCollector
from app.infrastructure.distillation.response_validator import ResponseValidator
from app.setup.config.distillation import DistillationSettings

logger = logging.getLogger(__name__)


class RequestDistillator:
    """
    Main orchestrator for request distillation.
    
    Coordinates:
    1. Request preprocessing
    2. Provider selection and validation
    3. Fallback logic
    4. Telemetry collection
    """
    
    def __init__(
        self,
        settings: DistillationSettings,
        primary_provider: Distillator,
        fallback_provider: Optional[Distillator],
        telemetry_collector: Optional[DistillationTelemetryCollector],
    ):
        """
        Initialize request distillator.
        
        Args:
            settings: Distillation settings
            primary_provider: Primary distillation provider
            fallback_provider: Optional fallback provider
            telemetry_collector: Optional telemetry collector
        """
        self.settings = settings
        self.primary_provider = primary_provider
        self.fallback_provider = fallback_provider
        self.telemetry_collector = telemetry_collector
        
        self.preprocessor = RequestPreprocessor()
        self.validator = ResponseValidator()
        
        logger.info(
            f"Request distillator initialized: "
            f"enabled={settings.enabled}, "
            f"primary={primary_provider.get_provider_name()}, "
            f"fallback={'yes' if fallback_provider else 'no'}"
        )
    
    async def validate(
        self,
        user_message: str,
        conversation_history: List[Message],
        user_id: UUID,
        conversation_id: UUID,
    ) -> DistillationResult:
        """
        Validate a user request.
        
        Args:
            user_message: The user's message
            conversation_history: Previous messages
            user_id: User identifier
            conversation_id: Conversation identifier
        
        Returns:
            DistillationResult with validation decision
        """
        # Check if distillation is enabled
        if not self.settings.enabled:
            logger.debug("Distillation disabled, allowing request")
            return self._create_bypass_result()
        
        # Preprocess request
        request = self.preprocessor.preprocess(
            user_message=user_message,
            conversation_history=conversation_history,
            user_id=str(user_id),
            conversation_id=str(conversation_id),
        )
        
        # Try primary provider
        result = await self._validate_with_provider(
            request=request,
            provider=self.primary_provider,
            is_fallback=False,
        )
        
        # Try fallback if primary failed and fail-open is disabled
        if result.error and not self.settings.fail_open and self.fallback_provider:
            logger.warning(
                f"Primary provider failed, trying fallback: {result.error}"
            )
            
            fallback_result = await self._validate_with_provider(
                request=request,
                provider=self.fallback_provider,
                is_fallback=True,
            )
            
            if not fallback_result.error:
                result = fallback_result
        
        # Fail-open: allow request if both providers failed
        if result.error and self.settings.fail_open:
            logger.warning(
                f"Distillation failed but fail-open enabled, allowing request: {result.error}"
            )
            result = self._create_fallback_result(result.detected_language)
        
        # Record telemetry
        if self.telemetry_collector:
            try:
                await self.telemetry_collector.record(request, result)
            except Exception as e:
                logger.error(f"Failed to record telemetry: {e}")
        
        logger.info(
            f"Distillation complete: success={result.success}, "
            f"reason={result.reason}, "
            f"provider={result.provider}"
        )
        
        return result
    
    async def _validate_with_provider(
        self,
        request: DistillationRequest,
        provider: Distillator,
        is_fallback: bool,
    ) -> DistillationResult:
        """
        Validate request with specific provider.
        
        Args:
            request: Distillation request
            provider: Provider to use
            is_fallback: Whether this is fallback provider
        
        Returns:
            DistillationResult
        """
        try:
            result = await provider.validate(request)
            result.fallback_used = is_fallback
            return result
        
        except DistillationError as e:
            logger.error(
                f"Provider {provider.get_provider_name()} failed: {e.message}"
            )
            
            # Return error result
            return DistillationResult(
                success=False,
                message=self.validator.create_fallback_response(
                    error=e.message,
                    detected_language=request.detected_language or "en",
                )["message"],
                reason="system_error",
                confidence=0.0,
                provider=provider.get_provider_name(),
                model=provider.get_model_name(),
                detected_language=request.detected_language or "en",
                latency_ms=0.0,
                tokens_used=0,
                cost_usd=0.0,
                fallback_used=is_fallback,
                error=str(e),
            )
        
        except Exception as e:
            logger.error(
                f"Unexpected error with provider {provider.get_provider_name()}: {e}"
            )
            
            # Return error result
            return DistillationResult(
                success=False,
                message=self.validator.create_fallback_response(
                    error=str(e),
                    detected_language=request.detected_language or "en",
                )["message"],
                reason="system_error",
                confidence=0.0,
                provider=provider.get_provider_name(),
                model=provider.get_model_name(),
                detected_language=request.detected_language or "en",
                latency_ms=0.0,
                tokens_used=0,
                cost_usd=0.0,
                fallback_used=is_fallback,
                error=str(e),
            )
    
    def _create_bypass_result(self) -> DistillationResult:
        """
        Create result for bypassed validation (distillation disabled).
        
        Returns:
            DistillationResult allowing request
        """
        return DistillationResult(
            success=True,
            message="Distillation bypassed (disabled)",
            reason="validation_passed",
            confidence=1.0,
            provider="bypass",
            model="none",
            detected_language="en",
            latency_ms=0.0,
            tokens_used=0,
            cost_usd=0.0,
            fallback_used=False,
        )
    
    def _create_fallback_result(self, detected_language: str) -> DistillationResult:
        """
        Create fallback result (fail-open scenario).
        
        Args:
            detected_language: User's language
        
        Returns:
            DistillationResult allowing request
        """
        return DistillationResult(
            success=True,
            message="Request allowed (distillation failed, fail-open enabled)",
            reason="validation_passed",
            confidence=0.5,
            provider="fallback",
            model="none",
            detected_language=detected_language,
            latency_ms=0.0,
            tokens_used=0,
            cost_usd=0.0,
            fallback_used=True,
            error="Distillation failed but fail-open enabled",
        )
    
    async def check_health(self) -> dict:
        """
        Check health of distillation system.
        
        Returns:
            Health status dictionary
        """
        health = {
            "enabled": self.settings.enabled,
            "primary_provider": None,
            "fallback_provider": None,
        }
        
        if self.settings.enabled:
            # Check primary
            try:
                primary_health = await self.primary_provider.check_health()
                health["primary_provider"] = {
                    "name": self.primary_provider.get_provider_name(),
                    **primary_health,
                }
            except Exception as e:
                health["primary_provider"] = {
                    "name": self.primary_provider.get_provider_name(),
                    "healthy": False,
                    "error": str(e),
                }
            
            # Check fallback
            if self.fallback_provider:
                try:
                    fallback_health = await self.fallback_provider.check_health()
                    health["fallback_provider"] = {
                        "name": self.fallback_provider.get_provider_name(),
                        **fallback_health,
                    }
                except Exception as e:
                    health["fallback_provider"] = {
                        "name": self.fallback_provider.get_provider_name(),
                        "healthy": False,
                        "error": str(e),
                    }
        
        return health
