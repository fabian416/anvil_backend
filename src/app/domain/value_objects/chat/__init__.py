"""
Chat-related value objects.
"""

from .intent_prediction import (
    IntentPrediction,
    IntentType,
    IntentConfidence,
    IntentResult,
)
from .agent_suggestion import AgentSuggestion, AutocompleteSuggestion, ConversationMatch
from .multi_intent_result import (
    MultiIntentResult,
    OrchestrationStrategy,
    IntentDependency,
)

__all__ = [
    "IntentPrediction",
    "IntentType",
    "IntentConfidence",
    "IntentResult",
    "AgentSuggestion",
    "AutocompleteSuggestion",
    "ConversationMatch",
    "MultiIntentResult",
    "OrchestrationStrategy",
    "IntentDependency",
]
