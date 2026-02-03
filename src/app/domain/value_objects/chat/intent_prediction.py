"""
Intent prediction value object for chat intent detection.
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from enum import Enum


class IntentType(Enum):
    """Types of detected intents."""

    # Analytics intents
    SHOW_ANALYTICS = "show_analytics"
    SHOW_STATS = "show_stats"

    # Query intents
    RISK_ANALYSIS = "risk_analysis"
    YIELD_OPTIMIZATION = "yield_optimization"
    PORTFOLIO_REVIEW = "portfolio_review"
    MARKET_ANALYSIS = "market_analysis"

    # Action intents
    EXECUTE_TRADE = "execute_trade"
    EXECUTE_TEMPLATE = "execute_template"

    # Preference management
    UPDATE_PREFERENCES = "update_preferences"

    # Export/compliance
    EXPORT_CONVERSATION = "export_conversation"

    # Translation
    TRANSLATE_CONTENT = "translate_content"

    # Unknown/ambiguous
    UNKNOWN = "unknown"


class IntentConfidence(Enum):
    """Confidence levels for intent detection."""

    HIGH = "high"  # > 0.8
    MEDIUM = "medium"  # 0.5 - 0.8
    LOW = "low"  # < 0.5


@dataclass(frozen=True)
class IntentPrediction:
    """
    Predicted intent from user message.

    Represents the detected intent with confidence score and context.
    """

    intent_type: IntentType
    confidence: float
    confidence_level: IntentConfidence
    suggested_agent: Optional[str] = None
    extracted_entities: Optional[dict] = None
    reasoning: Optional[str] = None
    alternative_intents: Optional[List[tuple[IntentType, float]]] = None

    @classmethod
    def create(
        cls,
        intent_type: IntentType,
        confidence: float,
        suggested_agent: Optional[str] = None,
        extracted_entities: Optional[dict] = None,
        reasoning: Optional[str] = None,
        alternative_intents: Optional[List[tuple[IntentType, float]]] = None,
    ) -> "IntentPrediction":
        """
        Create intent prediction with automatic confidence level.

        Args:
            intent_type: Detected intent type
            confidence: Confidence score (0.0 - 1.0)
            suggested_agent: Recommended agent for handling intent
            extracted_entities: Extracted data from message
            reasoning: Explanation of why this intent was detected
            alternative_intents: Other possible intents with scores

        Returns:
            IntentPrediction instance
        """
        # Determine confidence level
        if confidence >= 0.8:
            confidence_level = IntentConfidence.HIGH
        elif confidence >= 0.5:
            confidence_level = IntentConfidence.MEDIUM
        else:
            confidence_level = IntentConfidence.LOW

        return cls(
            intent_type=intent_type,
            confidence=confidence,
            confidence_level=confidence_level,
            suggested_agent=suggested_agent,
            extracted_entities=extracted_entities or {},
            reasoning=reasoning,
            alternative_intents=alternative_intents or [],
        )

    @property
    def is_high_confidence(self) -> bool:
        """Check if prediction has high confidence."""
        return self.confidence_level == IntentConfidence.HIGH

    @property
    def is_ambiguous(self) -> bool:
        """Check if intent is ambiguous (multiple viable alternatives)."""
        if not self.alternative_intents:
            return False

        # Ambiguous if any alternative has confidence within 0.15 of primary
        return any(
            abs(self.confidence - alt_conf) < 0.15
            for _, alt_conf in self.alternative_intents
        )

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            "intent_type": self.intent_type.value,
            "confidence": self.confidence,
            "confidence_level": self.confidence_level.value,
            "suggested_agent": self.suggested_agent,
            "extracted_entities": self.extracted_entities,
            "reasoning": self.reasoning,
            "alternative_intents": [
                {"intent": intent.value, "confidence": conf}
                for intent, conf in (self.alternative_intents or [])
            ],
            "is_high_confidence": self.is_high_confidence,
            "is_ambiguous": self.is_ambiguous,
        }


@dataclass(frozen=True)
class IntentResult:
    """
    Single intent detection result for multi-intent orchestration.

    This is a simplified domain value object used by the multi-intent
    detection system to represent a single detected intent with its
    confidence score, extracted entities, and metadata.

    Unlike IntentPrediction which is used for single-intent detection
    with reasoning and alternatives, IntentResult is designed for
    multi-intent orchestration where multiple intents need to be
    detected, prioritized, and executed.

    Attributes:
        intent: The detected intent (from any intent enum, typically ChatIntentV2)
        confidence: Confidence score (0.0 - 1.0)
        entities: Extracted entities from the message (e.g., ["BTC", "ETH"])
        metadata: Additional context and metadata for the intent

    Example:
        >>> intent_result = IntentResult(
        ...     intent=ChatIntentV2.SWAP,
        ...     confidence=0.95,
        ...     entities=["USDC", "ETH"],
        ...     metadata={"amount": "100"}
        ... )
    """

    intent: Any  # Typically ChatIntentV2, but kept flexible for extensibility
    confidence: float
    entities: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Validate confidence score."""
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError(
                f"Confidence must be between 0.0 and 1.0, got {self.confidence}"
            )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "intent": self.intent.value
            if hasattr(self.intent, "value")
            else str(self.intent),
            "confidence": self.confidence,
            "entities": self.entities,
            "metadata": self.metadata,
        }
