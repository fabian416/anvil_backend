"""
Intent detection router for real-time intent analysis and suggestions.
"""

import time
from uuid import UUID

from dishka.integrations.fastapi import FromDishka, inject
from fastapi import APIRouter, status, Security
from fastapi.exceptions import HTTPException

from app.presentation.http.auth.fastapi_openapi_markers import bearer_scheme
from app.application.common.services.current_user import CurrentUserService
from app.application.chat.services.advanced_intent_detector import AdvancedIntentDetector
from app.presentation.http.schemas.chat import (
    DetectIntentRequest,
    DetectIntentResponse,
    IntentPredictionResponse,
    AgentSuggestionResponse,
    AlternativeIntent,
    AutocompleteRequest,
    AutocompleteResponse,
    AutocompleteSuggestionResponse,
    SimilarConversationsRequest,
    SimilarConversationsResponse,
    ConversationMatchResponse,
)


def create_intent_detection_router() -> APIRouter:
    router = APIRouter(
        prefix="/user/chat/intent",
        tags=["chat-intent"],
    )

    @router.post(
        "/detect",
        status_code=status.HTTP_200_OK,
        response_model=DetectIntentResponse,
        dependencies=[Security(bearer_scheme)],
    )
    @inject
    async def detect_intent(
        request: DetectIntentRequest,
        current_user: FromDishka[CurrentUserService],
        intent_detector: FromDishka[AdvancedIntentDetector],
    ) -> DetectIntentResponse:
        """
        Detect intent from user message with optional agent suggestions.

        Returns intent prediction with confidence score and suggested agents.
        """
        start_time = time.perf_counter()

        user = await current_user.get_current_user()

        # Detect intent
        intent = await intent_detector.detect_intent_while_typing(
            partial_message=request.message,
            conversation_context=None,  # TODO: Load from conversation_id if provided
        )

        # Build intent response
        intent_response = IntentPredictionResponse(
            intent_type=intent.intent_type.value,
            confidence=intent.confidence,
            confidence_level=intent.confidence_level.value,
            suggested_agent=intent.suggested_agent,
            extracted_entities=intent.extracted_entities or {},
            reasoning=intent.reasoning,
            alternative_intents=[
                AlternativeIntent(intent_type=alt_intent.value, confidence=alt_conf)
                for alt_intent, alt_conf in (intent.alternative_intents or [])
            ],
            is_high_confidence=intent.is_high_confidence,
            is_ambiguous=intent.is_ambiguous,
        )

        # Get agent suggestions if requested
        suggested_agents = []
        if request.include_suggestions:
            agent_suggestions = await intent_detector.suggest_agents(intent)
            suggested_agents = [
                AgentSuggestionResponse(
                    agent_name=suggestion.agent_name,
                    confidence=suggestion.confidence,
                    reasoning=suggestion.reasoning,
                    agent_description=suggestion.agent_description,
                    estimated_response_time_seconds=suggestion.estimated_response_time_seconds,
                    is_high_confidence=suggestion.is_high_confidence,
                )
                for suggestion in agent_suggestions
            ]

        end_time = time.perf_counter()
        processing_time_ms = int((end_time - start_time) * 1000)

        return DetectIntentResponse(
            intent=intent_response,
            suggested_agents=suggested_agents,
            processing_time_ms=processing_time_ms,
        )

    @router.post(
        "/autocomplete",
        status_code=status.HTTP_200_OK,
        response_model=AutocompleteResponse,
        dependencies=[Security(bearer_scheme)],
    )
    @inject
    async def autocomplete(
        request: AutocompleteRequest,
        current_user: FromDishka[CurrentUserService],
        intent_detector: FromDishka[AdvancedIntentDetector],
    ) -> AutocompleteResponse:
        """
        Get autocomplete suggestions for partial user input.

        Provides real-time suggestions for protocols, tokens, and actions.
        """
        start_time = time.perf_counter()

        user = await current_user.get_current_user()

        # Get autocomplete suggestions
        suggestions = await intent_detector.suggest_completions(
            partial_message=request.partial_message,
            user_id=user.id_.value,
            limit=request.limit,
        )

        # Build response
        suggestion_responses = [
            AutocompleteSuggestionResponse(
                completion_text=suggestion.completion_text,
                display_text=suggestion.display_text,
                confidence=suggestion.confidence,
                suggestion_type=suggestion.suggestion_type,
                icon=suggestion.icon,
                metadata=suggestion.metadata or {},
            )
            for suggestion in suggestions
        ]

        end_time = time.perf_counter()
        processing_time_ms = int((end_time - start_time) * 1000)

        return AutocompleteResponse(
            suggestions=suggestion_responses,
            processing_time_ms=processing_time_ms,
        )

    @router.post(
        "/similar-conversations",
        status_code=status.HTTP_200_OK,
        response_model=SimilarConversationsResponse,
        dependencies=[Security(bearer_scheme)],
    )
    @inject
    async def find_similar_conversations(
        request: SimilarConversationsRequest,
        current_user: FromDishka[CurrentUserService],
        intent_detector: FromDishka[AdvancedIntentDetector],
    ) -> SimilarConversationsResponse:
        """
        Find similar past conversations based on message content.

        Uses semantic similarity to find relevant conversation history.
        """
        start_time = time.perf_counter()

        user = await current_user.get_current_user()

        # Find similar conversations
        matches = await intent_detector.find_similar_conversations(
            current_message=request.message,
            user_id=user.id_.value,
            limit=request.limit,
            similarity_threshold=request.similarity_threshold,
        )

        # Build response
        match_responses = [
            ConversationMatchResponse(
                conversation_id=match.conversation_id,
                title=match.title,
                similarity_score=match.similarity_score,
                snippet=match.snippet,
                created_at=match.created_at,
                message_count=match.message_count,
                was_helpful=match.was_helpful,
            )
            for match in matches
        ]

        end_time = time.perf_counter()
        processing_time_ms = int((end_time - start_time) * 1000)

        return SimilarConversationsResponse(
            matches=match_responses,
            processing_time_ms=processing_time_ms,
        )

    return router
