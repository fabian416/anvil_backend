"""
Multi-Intent Integration Service.

This service integrates the multi-intent detection and orchestration system
into the chat system, providing seamless support for both
single and multi-intent messages.

Architecture:
    Chat Handler → MultiIntentIntegrationService → Multi-Intent Pipeline
                ↓
             Single-Intent Pipeline (backward compatible)

Features:
    - Automatic detection of multi-intent vs single-intent messages
    - Backward compatible fallback to single-intent processing
    - Integration with existing cache, storage, and Hunter AI services
    - Feature flag support for gradual rollout
    - Comprehensive logging and monitoring

Example:
    >>> service = MultiIntentIntegrationService(
    ...     detector=intent_detector_v2,
    ...     orchestrator=intent_orchestrator,
    ...     formatter=response_formatter,
    ...     hunter_service=hunter_service,
    ...     cache=guest_cache,
    ... )
    >>> result = await service.process_message(
    ...     content="show btc eth ada prices",
    ...     language="en",
    ...     context=user_context,
    ... )
"""

import logging
from typing import Any, Dict, Optional
from uuid import UUID

from app.application.chat.services.intent_detector_v2 import IntentDetectorV2
from app.application.chat.services.intent_orchestrator import IntentOrchestrator
from app.application.chat.services.multi_intent_response_formatter import (
    MultiIntentResponseFormatter,
)
from app.domain.chat.value_objects import UserContext

logger = logging.getLogger(__name__)


class MultiIntentIntegrationService:
    """
    Integration service for multi-intent processing.

    This service acts as a bridge between the existing unified chat handler
    and the new multi-intent detection/orchestration system. It provides:

    1. Automatic multi-intent detection
    2. Orchestrated execution of multiple intents
    3. Response formatting and aggregation
    4. Backward compatibility with single-intent flow
    5. Feature flag controls for gradual rollout

    The service maintains full backward compatibility by falling back to
    single-intent processing when:
    - Feature flag is disabled
    - Only one intent is detected
    - Multi-intent processing fails
    """

    def __init__(
        self,
        detector: IntentDetectorV2,
        orchestrator: IntentOrchestrator,
        formatter: MultiIntentResponseFormatter,
        hunter_service: Any,
        cache: Any,
        enable_multi_intent: bool = True,
    ):
        """
        Initialize multi-intent integration service.

        Args:
            detector: IntentDetectorV2 for intent detection
            orchestrator: IntentOrchestrator for execution
            formatter: MultiIntentResponseFormatter for response formatting
            hunter_service: Hunter AI service for intent processing
            cache: Cache service for response caching
            enable_multi_intent: Feature flag to enable/disable multi-intent
        """
        self.detector = detector
        self.orchestrator = orchestrator
        self.formatter = formatter
        self.hunter_service = hunter_service
        self.cache = cache
        self.enable_multi_intent = enable_multi_intent

        logger.info(
            f"MultiIntentIntegrationService initialized (multi_intent={'ENABLED' if enable_multi_intent else 'DISABLED'})"
        )

    async def process_message(
        self,
        content: str,
        language: str,
        context: UserContext,
        conversation_id: Optional[UUID] = None,
    ) -> Dict[str, Any]:
        """
        Process message with multi-intent support.

        This method:
        1. Detects if message has multiple intents
        2. Routes to multi-intent or single-intent pipeline
        3. Returns unified response format

        Args:
            content: User message content
            language: Language code (en, es, pt, zh)
            context: User context (guest or authenticated)
            conversation_id: Optional conversation ID

        Returns:
            Dictionary with response data:
            - content: Formatted response message
            - intent: Primary intent or "MULTI_INTENT"
            - intents: List of all detected intents (for multi-intent)
            - enrichment: Hunter AI enrichment data
            - multi_intent: Boolean indicating multi-intent processing
            - execution_time_ms: Total execution time

        Example:
            >>> result = await service.process_message(
            ...     "show btc eth prices",
            ...     "en",
            ...     guest_context
            ... )
            >>> print(result["content"])
            "BTC: $95,000 | ETH: $3,500"
        """
        import time

        start_time = time.time()

        logger.info(
            f"Processing message (multi_intent={self.enable_multi_intent})",
            extra={
                "user_id": context.get_user_id(),
                "language": language,
                "content_length": len(content),
            },
        )

        # Check if multi-intent is enabled
        if not self.enable_multi_intent:
            logger.debug("Multi-intent disabled, using single-intent flow")
            return await self._process_single_intent(
                content, language, context, conversation_id
            )

        try:
            # Detect intents
            multi_intent_result = self.detector.detect_multi_intent(
                message=content,
                language=language,
                context=None,  # Conversation context would go here
            )

            # Check if single intent (backward compatibility)
            if multi_intent_result.is_single_intent:
                logger.debug("Single intent detected, using single-intent flow")
                return await self._process_single_intent(
                    content, language, context, conversation_id
                )

            # Multi-intent detected
            logger.info(
                f"🎯 Multi-intent detected: {len(multi_intent_result.intents)} intents",
                extra={
                    "user_id": context.get_user_id(),
                    "intents": multi_intent_result.intent_types,
                    "strategy": multi_intent_result.orchestration_strategy.value,
                },
            )

            # Process multi-intent
            result = await self._process_multi_intent(
                multi_intent_result, language, context, conversation_id
            )

            execution_time = (time.time() - start_time) * 1000
            result["execution_time_ms"] = execution_time

            logger.info(
                f"✅ Multi-intent processing complete: {execution_time:.2f}ms",
                extra={
                    "user_id": context.get_user_id(),
                    "intent_count": len(multi_intent_result.intents),
                },
            )

            return result

        except Exception as e:
            logger.error(
                f"❌ Multi-intent processing failed: {e}",
                exc_info=True,
                extra={"user_id": context.get_user_id()},
            )

            # Fallback to single-intent on error
            logger.info("Falling back to single-intent processing")
            return await self._process_single_intent(
                content, language, context, conversation_id
            )

    async def _process_multi_intent(
        self,
        multi_intent_result,
        language: str,
        context: UserContext,
        conversation_id: Optional[UUID],
    ) -> Dict[str, Any]:
        """
        Process message with multiple intents.

        Args:
            multi_intent_result: MultiIntentResult from detector
            language: Language code
            context: User context
            conversation_id: Conversation ID

        Returns:
            Formatted multi-intent response
        """
        # Build execution context
        execution_context = {
            "user_id": context.get_user_id(),
            "is_authenticated": context.is_authenticated(),
            "language": language,
            "conversation_id": str(conversation_id) if conversation_id else None,
        }

        # Execute intents
        orchestrated_result = await self.orchestrator.execute(
            multi_intent_result, execution_context
        )

        # Format response
        formatted_response = self.formatter.format(orchestrated_result, language)

        # Build response
        return {
            "content": formatted_response.message,
            "intent": "MULTI_INTENT",
            "intents": multi_intent_result.intent_types,
            "enrichment": formatted_response.data,
            "multi_intent": True,
            "orchestration_strategy": multi_intent_result.orchestration_strategy.value,
            "success": formatted_response.success,
            "partial_success": formatted_response.partial_success,
            "total_intents": len(multi_intent_result.intents),
        }

    async def _process_single_intent(
        self,
        content: str,
        language: str,
        context: UserContext,
        conversation_id: Optional[UUID],
    ) -> Dict[str, Any]:
        """
        Process message with single intent (backward compatibility).

        This method maintains the existing single-intent flow for:
        - Messages with only one intent
        - When multi-intent is disabled
        - Fallback on multi-intent errors

        Args:
            content: User message
            language: Language code
            context: User context
            conversation_id: Conversation ID

        Returns:
            Single-intent response (existing format)
        """
        # Use existing single-intent detection
        intent_result = self.detector.detect(
            message=content,
            language=language,
            context=None,
        )

        intent = intent_result.intent.value
        token = self._extract_token(content) or "BTC"

        # Check cache
        cached = await self.cache.get_hunter_response(intent, token, language)

        if cached:
            logger.debug(
                f"Cache HIT (single-intent)",
                extra={
                    "user_id": context.get_user_id(),
                    "intent": intent,
                    "token": token,
                },
            )

            return {
                "content": cached.get("content"),
                "intent": intent,
                "enrichment": cached.get("enrichment"),
                "multi_intent": False,
            }

        # Process with Hunter AI
        logger.debug(
            f"Cache MISS - processing with Hunter AI (single-intent)",
            extra={
                "user_id": context.get_user_id(),
                "intent": intent,
                "token": token,
            },
        )

        response = await self.hunter_service.process_intent(
            intent=intent,
            token=token,
            language=language,
            content=content,
            is_authenticated=context.is_authenticated(),
        )

        # Cache response
        await self.cache.set_hunter_response(intent, token, language, response)

        return {
            "content": response.get("content"),
            "intent": intent,
            "enrichment": response.get("enrichment"),
            "multi_intent": False,
        }

    def _extract_token(self, content: str) -> Optional[str]:
        """
        Extract token symbol from message.

        This is a simplified version for backward compatibility.
        The full multi-intent system uses entity extraction.

        Args:
            content: User message

        Returns:
            Token symbol or None
        """
        import re

        content_lower = content.lower()

        # Common tokens
        tokens = {
            "btc": "BTC",
            "bitcoin": "BTC",
            "eth": "ETH",
            "ethereum": "ETH",
            "usdc": "USDC",
            "usdt": "USDT",
            "sol": "SOL",
            "solana": "SOL",
            "ada": "ADA",
            "cardano": "ADA",
        }

        for key, value in tokens.items():
            if re.search(rf"\b{key}\b", content_lower):
                return value

        return None
