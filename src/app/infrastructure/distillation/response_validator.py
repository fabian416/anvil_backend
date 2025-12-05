"""
Response validator for distillation.

Validates and parses distillation responses.
"""
import json
import logging
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field, ValidationError

from app.domain.value_objects.distillation_reason import DistillationReason

logger = logging.getLogger(__name__)


class DistillationResponseSchema(BaseModel):
    """
    Pydantic schema for distillation responses.
    
    Validates the structure of responses from distillation providers.
    """
    
    success: bool = Field(
        ...,
        description="Whether request should be processed",
    )
    message: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="User-facing message in detected language",
    )
    reason: str = Field(
        ...,
        description="Validation reason code",
    )
    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Confidence score (0-1)",
    )


class ResponseValidator:
    """
    Validates distillation provider responses.
    
    Ensures responses conform to expected schema and handles errors.
    """
    
    def validate(
        self,
        response_data: Dict[str, Any],
    ) -> tuple[bool, Optional[str]]:
        """
        Validate response data.
        
        Args:
            response_data: Raw response dictionary from provider
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            # Validate with Pydantic
            validated = DistillationResponseSchema(**response_data)
            
            # Additional validation
            if not self._is_valid_reason(validated.reason):
                return (
                    False,
                    f"Invalid reason code: {validated.reason}",
                )
            
            return (True, None)
        
        except ValidationError as e:
            error_msg = f"Schema validation failed: {str(e)}"
            logger.error(error_msg)
            return (False, error_msg)
        
        except Exception as e:
            error_msg = f"Unexpected validation error: {str(e)}"
            logger.error(error_msg)
            return (False, error_msg)
    
    def _is_valid_reason(self, reason: str) -> bool:
        """
        Check if reason code is valid.
        
        Args:
            reason: Reason code to validate
        
        Returns:
            True if valid
        """
        try:
            # Try to convert to enum
            DistillationReason(reason)
            return True
        except ValueError:
            logger.warning(f"Unknown reason code: {reason}")
            # Allow unknown reasons but log warning
            return True
    
    def parse_json_safe(
        self,
        response_text: str,
    ) -> tuple[Optional[Dict[str, Any]], Optional[str]]:
        """
        Safely parse JSON from response text.
        
        Handles common issues like markdown code blocks.
        
        Args:
            response_text: Raw response text
        
        Returns:
            Tuple of (parsed_data, error_message)
        """
        if not response_text:
            return (None, "Empty response")
        
        try:
            # Clean up response text
            text = response_text.strip()
            
            # Remove markdown code blocks
            if text.startswith("```json"):
                text = text[7:]
            elif text.startswith("```"):
                text = text[3:]
            
            if text.endswith("```"):
                text = text[:-3]
            
            text = text.strip()
            
            # Try to find JSON in text
            # Look for first { and last }
            start_idx = text.find("{")
            end_idx = text.rfind("}")
            
            if start_idx == -1 or end_idx == -1:
                return (None, "No JSON object found in response")
            
            json_text = text[start_idx:end_idx+1]
            
            # Parse JSON
            data = json.loads(json_text)
            
            return (data, None)
        
        except json.JSONDecodeError as e:
            error_msg = f"JSON decode error: {str(e)}"
            logger.error(f"{error_msg}\nResponse: {response_text[:200]}")
            return (None, error_msg)
        
        except Exception as e:
            error_msg = f"Unexpected parse error: {str(e)}"
            logger.error(error_msg)
            return (None, error_msg)
    
    def create_fallback_response(
        self,
        error: str,
        detected_language: str = "en",
    ) -> Dict[str, Any]:
        """
        Create fallback response when validation fails.
        
        Args:
            error: Error message
            detected_language: User's language
        
        Returns:
            Fallback response dictionary
        """
        # Multilingual error messages
        messages = {
            "en": "Unable to validate your request. Please try again.",
            "es": "No se pudo validar tu solicitud. Por favor, inténtalo de nuevo.",
            "fr": "Impossible de valider votre demande. Veuillez réessayer.",
            "de": "Ihre Anfrage konnte nicht validiert werden. Bitte versuchen Sie es erneut.",
            "pt": "Não foi possível validar sua solicitação. Por favor, tente novamente.",
            "it": "Impossibile convalidare la tua richiesta. Per favore riprova.",
            "ja": "リクエストを検証できませんでした。もう一度お試しください。",
            "zh": "无法验证您的请求。请重试。",
            "ko": "요청을 검증할 수 없습니다. 다시 시도해 주세요.",
        }
        
        message = messages.get(detected_language, messages["en"])
        
        return {
            "success": False,
            "message": message,
            "reason": "system_error",
            "confidence": 0.0,
        }
