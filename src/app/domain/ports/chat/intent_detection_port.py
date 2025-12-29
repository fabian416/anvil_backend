"""
Intent detection port for chat domain.

Defines the interface for detecting user intent from messages.
Implementations can use LLM, keywords, ML models, or hybrid approaches.

This port follows hexagonal architecture principles:
- Domain defines the interface
- Infrastructure provides implementations
- Application layer uses the port, not the implementation
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from app.domain.chat.entities.message import Message
    from app.application.chat.services.intent_detector import ChatIntent


@dataclass
class IntentDetectionRequest:
    """
    Request for intent detection.

    Contains all information needed to classify user intent.
    """

    message: str
    conversation_history: Optional[list["Message"]] = None
    user_context: Optional[dict] = field(default_factory=dict)  # User preferences, tier, etc.


@dataclass
class IntentDetectionResult:
    """
    Result of intent detection.

    Includes classified intent, confidence, extracted entities, and reasoning.
    """

    intent: "ChatIntent"
    confidence: float  # 0.0 - 1.0
    entities: dict  # Extracted entities (protocol_name, token_symbol, etc.)
    reasoning: str  # Human-readable explanation
    handler: str  # Handler category (graphrag_search, ultra, hunter_ai, etc.)
    suggested_agent: Optional[str] = None  # For SPECIALIST_TASK


class IntentDetectionPort(ABC):
    """
    Port for detecting user intent from chat messages.

    Implementations:
    - LLMIntentDetectionAdapter: Uses LLM for high accuracy
    - KeywordIntentDetectionAdapter: Fast keyword-based fallback
    - HybridIntentDetectionAdapter: LLM with keyword fallback

    Usage:
        # In application layer
        class IntentDetectorService:
            def __init__(self, intent_detector: IntentDetectionPort):
                self._detector = intent_detector

            async def detect_intent(self, message: str) -> IntentDetectionResult:
                request = IntentDetectionRequest(message=message)
                return await self._detector.detect_intent(request)
    """

    @abstractmethod
    async def detect_intent(
        self,
        request: IntentDetectionRequest,
    ) -> IntentDetectionResult:
        """
        Detect user intent from message.

        Args:
            request: Intent detection request with message and context

        Returns:
            Intent detection result with classification and entities

        Raises:
            IntentDetectionError: If detection fails critically
        """
        ...

    @abstractmethod
    def supports_streaming(self) -> bool:
        """
        Whether this implementation supports streaming responses.

        Returns:
            True if streaming is supported, False otherwise
        """
        ...
