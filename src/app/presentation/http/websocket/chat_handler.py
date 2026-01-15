"""
Chat WebSocket handler.

Implements real-time chat features with multi-agent orchestration following
hexagonal architecture principles. Handles WebSocket lifecycle, message routing,
and agent response streaming.

Endpoint: /ws/chat/{conversation_id}

Features:
    - Real-time message streaming
    - Agent typing indicators
    - Multi-agent voting progress updates
    - Debate phase notifications
    - Connection management (connect, disconnect, heartbeat)
    - Authentication and authorization
"""

import asyncio
import logging
from datetime import datetime, UTC
from typing import Any, Dict, Optional
from uuid import UUID

from dishka.integrations.fastapi import FromDishka, inject
from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect, status

from app.application.chat.services.advanced_intent_detector import (
    AdvancedIntentDetector,
)
from app.application.chat.services.agent_orchestration_service import (
    AgentOrchestrationService,
)
from app.application.common.ports.identity_provider import IdentityProvider
from app.application.common.ports.user_command_gateway import UserCommandGateway
from app.domain.entities.user import User
from app.domain.exceptions.chat import (
    AgentProcessingError,
    AgentTimeoutError,
    AgentUnavailableError,
    ChatRateLimitError,
    ConversationAccessDeniedError,
    ConversationClosedError,
    ConversationNotFoundError,
    DebateTimeoutError,
    MessageEmptyError,
    MessageTooLongError,
    NoConsensusError,
    VotingFailedError,
)
from app.domain.ports.session_store import SessionStore
from app.presentation.http.websocket.auth_helper import (
    WebSocketAuthHelper,
    close_websocket_with_error,
)
from app.presentation.http.websocket.connection_manager import connection_manager
from app.presentation.http.websocket.schemas import (
    ChatMessageRequest,
    DebatePhase,
    DebatePhaseMessage,
    ErrorMessage,
    IntentSuggestionMessage,
    MessageCompleteMessage,
    PingMessage,
    PongMessage,
    ProgressMessage,
    StreamTokenMessage,
    SystemMessage,
    TypingIndicatorAction,
    TypingIndicatorMessage,
    VotingUpdateMessage,
    WebSocketMessageType,
)

router = APIRouter()
logger = logging.getLogger(__name__)


# =============================================================================
# WEBSOCKET ENDPOINT
# =============================================================================


@router.websocket("/ws/chat/{conversation_id}")
@inject
async def chat_websocket_handler(
    websocket: WebSocket,
    conversation_id: UUID,
    token: str = Query(..., description="JWT authentication token"),
    identity_provider: FromDishka[IdentityProvider] = None,  # type: ignore[assignment]
    user_gateway: FromDishka[UserCommandGateway] = None,  # type: ignore[assignment]
    session_store: FromDishka[SessionStore] = None,  # type: ignore[assignment]
    orchestration_service: FromDishka[AgentOrchestrationService] = None,  # type: ignore[assignment]
    intent_detector: FromDishka[AdvancedIntentDetector] = None,  # type: ignore[assignment]
):
    """
    WebSocket endpoint for real-time chat with multi-agent orchestration.

    Connection:
        ws://localhost:8000/api/v1/ws/chat/<conversation_id>?token=<jwt>

    Message Flow:
        1. Client connects with JWT token
        2. Server authenticates and registers connection
        3. Client sends ChatMessageRequest
        4. Server detects intent and sends suggestions
        5. Server streams agent response with progress updates
        6. Client receives typing indicators, voting updates, debate phases
        7. Server sends MessageCompleteMessage when done

    Args:
        websocket: WebSocket connection instance
        conversation_id: Conversation UUID for this chat session
        token: JWT authentication token
        identity_provider: Identity provider for authentication (injected)
        user_gateway: User gateway for user retrieval (injected)
        session_store: Session store for connection tracking (injected)
        orchestration_service: Agent orchestration service (injected)
        intent_detector: Advanced intent detection service (injected)
    """
    # Initialize authentication helper
    auth_helper = WebSocketAuthHelper(identity_provider, user_gateway)

    # Authenticate user before accepting connection
    user = await auth_helper.authenticate_websocket(websocket, token)

    if not user:
        await close_websocket_with_error(
            websocket,
            code=status.WS_1008_POLICY_VIOLATION,
            reason="Authentication failed: Invalid or expired token",
        )
        return

    # Check conversation access (basic authorization)
    has_access = await auth_helper.check_conversation_access(user, conversation_id)
    if not has_access:
        await close_websocket_with_error(
            websocket,
            code=status.WS_1008_POLICY_VIOLATION,
            reason="Access denied: You don't have access to this conversation",
        )
        return

    # Generate session ID for this connection
    session_id = f"ws_{user.id}_{conversation_id}_{datetime.now(UTC).timestamp()}"

    # Register connection with manager
    await connection_manager.connect(
        websocket,
        user_id=str(user.id),
        session_id=session_id,
        metadata={
            "conversation_id": str(conversation_id),
            "email": user.email,
            "connected_at": datetime.now(UTC).isoformat(),
        },
    )

    # Send welcome system message
    welcome_msg = SystemMessage(
        message=f"Connected to conversation {conversation_id}",
        data={
            "user_id": str(user.id),
            "session_id": session_id,
            "conversation_id": str(conversation_id),
        },
    )
    await websocket.send_json(welcome_msg.model_dump(mode="json"))

    logger.info(
        f"[WS Chat] User {user.id} connected to conversation {conversation_id} "
        f"(session={session_id})"
    )

    try:
        # Main message loop
        await _handle_message_loop(
            websocket=websocket,
            user=user,
            conversation_id=conversation_id,
            session_id=session_id,
            orchestration_service=orchestration_service,
            intent_detector=intent_detector,
        )

    except WebSocketDisconnect:
        logger.info(
            f"[WS Chat] Client disconnected: user={user.id}, "
            f"conversation={conversation_id}, session={session_id}"
        )

    except Exception as e:
        logger.error(
            f"[WS Chat] Unexpected error in WebSocket handler: {e}",
            exc_info=True,
        )
        # Try to send error message before closing
        try:
            error_msg = ErrorMessage(
                error="Internal server error",
                code="internal_error",
                details={"message": str(e)},
            )
            await websocket.send_json(error_msg.model_dump(mode="json"))
        except Exception:
            pass

    finally:
        # Disconnect from manager
        await connection_manager.disconnect(websocket, str(user.id), session_id)
        logger.info(
            f"[WS Chat] Connection cleaned up: user={user.id}, "
            f"conversation={conversation_id}"
        )


# =============================================================================
# MESSAGE HANDLING
# =============================================================================


async def _handle_message_loop(
    websocket: WebSocket,
    user: User,
    conversation_id: UUID,
    session_id: str,
    orchestration_service: Optional[AgentOrchestrationService],
    intent_detector: Optional[AdvancedIntentDetector],
) -> None:
    """
    Handle incoming WebSocket messages in a loop.

    Processes different message types (message, ping) and delegates to
    appropriate handlers.

    Args:
        websocket: WebSocket connection
        user: Authenticated user
        conversation_id: Current conversation ID
        session_id: WebSocket session ID
        orchestration_service: Agent orchestration service
        intent_detector: Advanced intent detection service
    """
    while True:
        # Receive message from client
        try:
            data = await websocket.receive_json()
        except Exception as e:
            logger.warning(f"[WS Chat] Error receiving message: {e}")
            break

        message_type = data.get("type")

        # Handle ping/pong heartbeat
        if message_type == WebSocketMessageType.PING:
            await _handle_ping(websocket)
            continue

        # Handle chat message
        if message_type == WebSocketMessageType.MESSAGE:
            await _handle_chat_message(
                websocket=websocket,
                user=user,
                conversation_id=conversation_id,
                session_id=session_id,
                data=data,
                orchestration_service=orchestration_service,
                intent_detector=intent_detector,
            )
            continue

        # Unknown message type
        logger.warning(f"[WS Chat] Unknown message type: {message_type}")
        error_msg = ErrorMessage(
            error=f"Unknown message type: {message_type}",
            code="unknown_message_type",
        )
        await websocket.send_json(error_msg.model_dump(mode="json"))


async def _handle_ping(websocket: WebSocket) -> None:
    """
    Handle ping message with pong response.

    Args:
        websocket: WebSocket connection
    """
    pong_msg = PongMessage()
    await websocket.send_json(pong_msg.model_dump(mode="json"))


async def _handle_chat_message(
    websocket: WebSocket,
    user: User,
    conversation_id: UUID,
    session_id: str,
    data: Dict[str, Any],
    orchestration_service: Optional[AgentOrchestrationService],
    intent_detector: Optional[AdvancedIntentDetector],
) -> None:
    """
    Handle incoming chat message from client.

    Validates message, detects intent, routes to agent orchestration,
    and streams response with progress updates.

    Args:
        websocket: WebSocket connection
        user: Authenticated user
        conversation_id: Current conversation ID
        session_id: WebSocket session ID
        data: Raw message data from client
        orchestration_service: Agent orchestration service
        intent_detector: Advanced intent detection service
    """
    try:
        # Validate message schema
        message_request = ChatMessageRequest(**data)

        # Validate content
        if not message_request.content.strip():
            raise MessageEmptyError()

        logger.info(
            f"[WS Chat] User {user.id}: {message_request.content[:100]}... "
            f"(conversation={conversation_id})"
        )

        # Detect intent and send suggestions
        if intent_detector:
            try:
                # Detect intent from message
                intent = await intent_detector.detect_intent_while_typing(
                    partial_message=message_request.content,
                    conversation_context=None,  # TODO: Load conversation context
                )

                # Send intent suggestion to client
                intent_msg = IntentSuggestionMessage(
                    intent_type=intent.intent_type.value,
                    confidence=intent.confidence,
                    confidence_level=intent.confidence_level.value,
                    suggested_agent=intent.suggested_agent,
                    agent_reasoning=intent.reasoning,
                    extracted_entities=intent.extracted_entities or {},
                    autocomplete_suggestions=[],  # Could be populated from autocomplete service
                    is_high_confidence=intent.is_high_confidence,
                )
                await websocket.send_json(intent_msg.model_dump(mode="json"))

                logger.info(
                    f"[WS Chat] Sent intent suggestion: {intent.intent_type.value} "
                    f"(confidence={intent.confidence:.2f})"
                )

            except Exception as e:
                # Log but don't fail the message processing
                logger.warning(
                    f"[WS Chat] Intent detection failed: {e}",
                    exc_info=True,
                )

        # Send typing indicator
        typing_msg = TypingIndicatorMessage(
            action=TypingIndicatorAction.STARTED,
            agent_name="AI Assistant",
        )
        await websocket.send_json(typing_msg.model_dump(mode="json"))

        # Send initial progress
        progress_msg = ProgressMessage(
            status="thinking",
            message="Processing your request...",
        )
        await websocket.send_json(progress_msg.model_dump(mode="json"))

        # Route to agent orchestration service if available
        if orchestration_service:
            await _process_with_orchestration(
                websocket=websocket,
                user=user,
                conversation_id=conversation_id,
                message_content=message_request.content,
                orchestration_service=orchestration_service,
            )
        else:
            # Fallback: Simple echo response
            await _process_fallback_response(
                websocket=websocket,
                message_content=message_request.content,
            )

    except MessageEmptyError as e:
        logger.warning(f"[WS Chat] Empty message from user {user.id}")
        error_msg = ErrorMessage(
            error="Message content cannot be empty",
            code="CHAT_004",
            details={"field": "content"},
        )
        await websocket.send_json(error_msg.model_dump(mode="json"))

    except MessageTooLongError as e:
        logger.warning(f"[WS Chat] Message too long from user {user.id}")
        error_msg = ErrorMessage(
            error="Message exceeds maximum length",
            code="CHAT_005",
            details=e.details if hasattr(e, "details") else {},
        )
        await websocket.send_json(error_msg.model_dump(mode="json"))

    except ChatRateLimitError as e:
        logger.warning(f"[WS Chat] Rate limit exceeded for user {user.id}")
        error_msg = ErrorMessage(
            error="Rate limit exceeded",
            code="CHAT_007",
            details=e.details if hasattr(e, "details") else {},
        )
        await websocket.send_json(error_msg.model_dump(mode="json"))

    except ConversationNotFoundError as e:
        logger.warning(f"[WS Chat] Conversation not found: {conversation_id}")
        error_msg = ErrorMessage(
            error="Conversation not found",
            code="CHAT_001",
            details={"conversation_id": str(conversation_id)},
        )
        await websocket.send_json(error_msg.model_dump(mode="json"))

    except ConversationClosedError as e:
        logger.warning(f"[WS Chat] Conversation closed: {conversation_id}")
        error_msg = ErrorMessage(
            error="Conversation is closed",
            code="CHAT_003",
            details={"conversation_id": str(conversation_id)},
        )
        await websocket.send_json(error_msg.model_dump(mode="json"))

    except ConversationAccessDeniedError as e:
        logger.warning(f"[WS Chat] Access denied for user {user.id}")
        error_msg = ErrorMessage(
            error="Access denied to conversation",
            code="CHAT_002",
            details={"conversation_id": str(conversation_id)},
        )
        await websocket.send_json(error_msg.model_dump(mode="json"))

    except Exception as e:
        logger.error(
            f"[WS Chat] Error processing message from user {user.id}: {e}",
            exc_info=True,
        )
        error_msg = ErrorMessage(
            error="Failed to process message",
            code="processing_error",
            details={"message": str(e)},
        )
        await websocket.send_json(error_msg.model_dump(mode="json"))

    finally:
        # Stop typing indicator
        try:
            typing_stop_msg = TypingIndicatorMessage(
                action=TypingIndicatorAction.STOPPED,
                agent_name="AI Assistant",
            )
            await websocket.send_json(typing_stop_msg.model_dump(mode="json"))
        except Exception:
            pass


# =============================================================================
# AGENT ORCHESTRATION
# =============================================================================


async def _process_with_orchestration(
    websocket: WebSocket,
    user: User,
    conversation_id: UUID,
    message_content: str,
    orchestration_service: AgentOrchestrationService,
) -> None:
    """
    Process message with multi-agent orchestration.

    Handles agent routing, multi-agent voting, debate phases, and streams
    the final response with progress updates.

    Args:
        websocket: WebSocket connection
        user: Authenticated user
        conversation_id: Current conversation ID
        message_content: User's message content
        orchestration_service: Agent orchestration service
    """
    try:
        # Phase 1: Initial Analysis
        debate_phase_msg = DebatePhaseMessage(
            phase=DebatePhase.INITIAL_ANALYSIS,
            description="Analyzing your request and determining the best approach...",
        )
        await websocket.send_json(debate_phase_msg.model_dump(mode="json"))

        # Phase 2: Multi-Agent Voting (if enabled)
        # This is a placeholder - actual implementation would delegate to orchestration service
        voting_msg = DebatePhaseMessage(
            phase=DebatePhase.VOTING,
            description="Agents are voting on the best response approach...",
            participating_agents=["Analyst", "Strategist", "Executor"],
        )
        await websocket.send_json(voting_msg.model_dump(mode="json"))

        # Simulate voting progress updates
        for i in range(1, 4):
            await asyncio.sleep(0.5)  # Simulate voting time
            voting_update_msg = VotingUpdateMessage(
                total_agents=3,
                votes_received=i,
                vote_summary={"Option A": i, "Option B": 3 - i},
                leading_option="Option A" if i >= 2 else "Option B",
            )
            await websocket.send_json(voting_update_msg.model_dump(mode="json"))

        # Phase 3: Consensus
        consensus_msg = DebatePhaseMessage(
            phase=DebatePhase.CONSENSUS,
            description="Agents reached consensus on the approach...",
        )
        await websocket.send_json(consensus_msg.model_dump(mode="json"))

        # Phase 4: Final Response
        final_phase_msg = DebatePhaseMessage(
            phase=DebatePhase.FINAL_RESPONSE,
            description="Generating final response...",
        )
        await websocket.send_json(final_phase_msg.model_dump(mode="json"))

        # Stream the actual response
        # TODO: Integrate with actual orchestration service streaming
        response_text = (
            f"Based on multi-agent analysis, here's the response to: {message_content[:50]}...\n\n"
            "This is a placeholder response. In production, this would be the actual "
            "agent-generated response streamed token-by-token."
        )

        message_id = UUID("12345678-1234-5678-1234-567812345678")  # Placeholder

        # Stream tokens
        for token in response_text.split():
            stream_msg = StreamTokenMessage(
                content=token + " ",
                message_id=message_id,
            )
            await websocket.send_json(stream_msg.model_dump(mode="json"))
            await asyncio.sleep(0.05)  # Simulate streaming delay

        # Send completion message
        complete_msg = MessageCompleteMessage(
            message_id=message_id,
            content=response_text,
            metadata={
                "agents_used": ["Analyst", "Strategist", "Executor"],
                "voting_rounds": 1,
                "consensus_reached": True,
            },
        )
        await websocket.send_json(complete_msg.model_dump(mode="json"))

    except VotingFailedError as e:
        logger.error(f"[WS Chat] Multi-agent voting failed: {e}")
        error_msg = ErrorMessage(
            error="Multi-agent voting failed",
            code="voting_failed",
            details=e.details if hasattr(e, "details") else {},
        )
        await websocket.send_json(error_msg.model_dump(mode="json"))

    except DebateTimeoutError as e:
        logger.error(f"[WS Chat] Debate timeout: {e}")
        error_msg = ErrorMessage(
            error="Agent debate timed out",
            code="debate_timeout",
            details=e.details if hasattr(e, "details") else {},
        )
        await websocket.send_json(error_msg.model_dump(mode="json"))

    except NoConsensusError as e:
        logger.error(f"[WS Chat] No consensus reached: {e}")
        error_msg = ErrorMessage(
            error="Agents could not reach consensus",
            code="no_consensus",
            details=e.details if hasattr(e, "details") else {},
        )
        await websocket.send_json(error_msg.model_dump(mode="json"))

    except AgentUnavailableError as e:
        logger.error(f"[WS Chat] Agent unavailable: {e}")
        error_msg = ErrorMessage(
            error="Required agent is unavailable",
            code="CHAT_006",
            details=e.details if hasattr(e, "details") else {},
        )
        await websocket.send_json(error_msg.model_dump(mode="json"))

    except AgentTimeoutError as e:
        logger.error(f"[WS Chat] Agent timeout: {e}")
        error_msg = ErrorMessage(
            error="Agent response timed out",
            code="agent_timeout",
            details=e.details if hasattr(e, "details") else {},
        )
        await websocket.send_json(error_msg.model_dump(mode="json"))

    except AgentProcessingError as e:
        logger.error(f"[WS Chat] Agent processing error: {e}")
        error_msg = ErrorMessage(
            error="Agent encountered an error",
            code="CHAT_008",
            details=e.details if hasattr(e, "details") else {},
        )
        await websocket.send_json(error_msg.model_dump(mode="json"))


async def _process_fallback_response(
    websocket: WebSocket,
    message_content: str,
) -> None:
    """
    Process message with simple fallback response.

    Used when orchestration service is not available.

    Args:
        websocket: WebSocket connection
        message_content: User's message content
    """
    # Simple echo response for fallback
    response_text = (
        f"Echo: {message_content}\n\n"
        "Note: Agent orchestration service is not available. "
        "This is a fallback response."
    )

    message_id = UUID("00000000-0000-0000-0000-000000000000")

    # Stream response
    for token in response_text.split():
        stream_msg = StreamTokenMessage(
            content=token + " ",
            message_id=message_id,
        )
        await websocket.send_json(stream_msg.model_dump(mode="json"))
        await asyncio.sleep(0.05)

    # Send completion
    complete_msg = MessageCompleteMessage(
        message_id=message_id,
        content=response_text,
        metadata={"fallback": True},
    )
    await websocket.send_json(complete_msg.model_dump(mode="json"))
