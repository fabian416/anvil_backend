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
        Detect intent with LLM + fallback.

        Strategy:
        1. Try LLM classification
        2. If confidence >= threshold, return LLM result
        3. If LLM fails or low confidence, fallback to keywords
        """
        # Try LLM first
        try:
            llm_result = await self._llm.detect_intent(request)

            if llm_result.confidence >= self._min_confidence:
                return llm_result

            # Low confidence, use fallback
            self._logger.warning(
                f"LLM confidence {llm_result.confidence} < {self._min_confidence}, "
                f"using keyword fallback"
            )

        except IntentDetectionError as e:
            # LLM failed, use fallback
            self._logger.warning(
                f"LLM intent detection failed: {e}, using keyword fallback"
            )
        except Exception as e:
            # Unexpected error, use fallback
            self._logger.error(
                f"Unexpected error in LLM intent detection: {e}, using keyword fallback"
            )

        # Fallback to keywords
        return await self._keyword.detect_intent(request)

    def supports_streaming(self) -> bool:
        return False
