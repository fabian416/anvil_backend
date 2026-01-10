"""
Hybrid intent detection with LLM + keyword fallback.

Best of both worlds: high accuracy with reliability.
Uses LLM for primary classification, falls back to keywords if LLM fails or confidence is low.

This adapter is ideal for:
- Production use (reliability + accuracy)
- Graceful degradation when LLM is unavailable
- Cost optimization (skip LLM for clear intents)
"""

import logging

from app.domain.ports.chat.intent_detection_port import (
    IntentDetectionPort,
    IntentDetectionRequest,
    IntentDetectionResult,
)
from app.infrastructure.adapters.chat.llm_intent_detection_adapter import (
    LLMIntentDetectionAdapter,
    IntentDetectionError,
)
from app.infrastructure.adapters.chat.keyword_intent_detection_adapter import (
    KeywordIntentDetectionAdapter,
)


class HybridIntentDetectionAdapter(IntentDetectionPort):
    """
    Intent detection with LLM primary and keyword fallback.

    Tries LLM first for accuracy, falls back to keywords for reliability.
    """

    def __init__(
        self,
        llm_adapter: LLMIntentDetectionAdapter,
        keyword_adapter: KeywordIntentDetectionAdapter,
        min_llm_confidence: float = 0.7,
    ):
        """
        Initialize hybrid adapter.

        Args:
            llm_adapter: Primary LLM-based detector
            keyword_adapter: Fallback keyword detector
            min_llm_confidence: Minimum confidence to accept LLM result
        """
        self._llm = llm_adapter
        self._keyword = keyword_adapter
        self._min_confidence = min_llm_confidence
        self._logger = logging.getLogger(__name__)

    async def detect_intent(
        self,
        request: IntentDetectionRequest,
    ) -> IntentDetectionResult:
        """
        Detect intent with keyword priority + LLM fallback.

        Strategy:
        1. Try keyword classification first (fast, deterministic)
        2. If keyword confidence >= 0.9, return keyword result (exact match)
        3. Otherwise, try LLM for semantic understanding
        4. If LLM confidence >= threshold, return LLM result
        5. If LLM also has low confidence, return keyword result as final fallback
        """
        # Try keyword adapter first for exact matches
        keyword_result = await self._keyword.detect_intent(request)

        # If keyword has high confidence (exact match), use it
        if keyword_result.confidence >= 0.9:
            return keyword_result

        # Try LLM for semantic understanding
        try:
            llm_result = await self._llm.detect_intent(request)

            if llm_result.confidence >= self._min_confidence:
                return llm_result

            # Low confidence from both, prefer keyword
            self._logger.warning(
                f"LLM confidence {llm_result.confidence} < {self._min_confidence}, "
                f"using keyword result (confidence: {keyword_result.confidence})"
            )
            return keyword_result

        except IntentDetectionError as e:
            # LLM failed, use keyword
            self._logger.warning(
                f"LLM intent detection failed: {e}, using keyword result"
            )
            return keyword_result
        except Exception as e:
            # Unexpected error, use keyword
            self._logger.error(
                f"Unexpected error in LLM intent detection: {e}, using keyword result"
            )
            return keyword_result

    def supports_streaming(self) -> bool:
        return False
