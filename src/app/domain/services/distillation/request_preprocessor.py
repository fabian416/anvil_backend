"""
Request preprocessor for distillation.

Prepares requests for validation by detecting language and formatting context.
"""
import logging
from typing import List, Optional

from app.domain.entities.distillation import DistillationRequest
from app.domain.chat.entities.message import Message

logger = logging.getLogger(__name__)


class RequestPreprocessor:
    """
    Preprocesses user requests for distillation.
    
    Handles language detection and conversation history formatting.
    """
    
    def __init__(self):
        """Initialize request preprocessor."""
        # Lazy import langdetect
        try:
            import langdetect
            self.langdetect = langdetect
            # Set seed for consistent results
            langdetect.DetectorFactory.seed = 0
        except ImportError:
            logger.warning("langdetect not installed, defaulting to 'en'")
            self.langdetect = None
    
    def preprocess(
        self,
        user_message: str,
        conversation_history: List[Message],
        user_id: str,
        conversation_id: str,
    ) -> DistillationRequest:
        """
        Preprocess a user request.
        
        Args:
            user_message: The user's message
            conversation_history: List of previous messages
            user_id: User identifier
            conversation_id: Conversation identifier
        
        Returns:
            DistillationRequest ready for validation
        """
        # Detect language
        detected_language = self.detect_language(user_message)
        
        # Create distillation request
        request = DistillationRequest(
            user_message=user_message,
            conversation_history=conversation_history,
            user_id=user_id,
            conversation_id=conversation_id,
            detected_language=detected_language,
        )
        
        logger.debug(
            f"Preprocessed request: language={detected_language}, "
            f"history_length={len(conversation_history)}"
        )
        
        return request
    
    def detect_language(self, text: str) -> str:
        """
        Detect language of text.
        
        Args:
            text: Text to analyze
        
        Returns:
            ISO 639-1 language code (e.g., 'en', 'es', 'fr')
        """
        if not self.langdetect:
            return "en"
        
        if not text or len(text.strip()) < 3:
            return "en"
        
        try:
            lang = self.langdetect.detect(text)
            logger.debug(f"Detected language: {lang}")
            return lang
        except Exception as e:
            logger.warning(f"Language detection failed: {e}, defaulting to 'en'")
            return "en"
    
    def detect_language_with_confidence(
        self,
        text: str,
    ) -> tuple[str, float]:
        """
        Detect language with confidence score.
        
        Args:
            text: Text to analyze
        
        Returns:
            Tuple of (language_code, confidence)
        """
        if not self.langdetect:
            return ("en", 1.0)
        
        if not text or len(text.strip()) < 3:
            return ("en", 1.0)
        
        try:
            probabilities = self.langdetect.detect_langs(text)
            if probabilities:
                best = probabilities[0]
                return (best.lang, best.prob)
            return ("en", 1.0)
        except Exception as e:
            logger.warning(f"Language detection failed: {e}")
            return ("en", 0.5)
