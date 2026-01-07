"""
Conversations Router.

CRUD endpoints for conversation management.
Supports both guest and authenticated users.
"""

from typing import Any
from uuid import UUID

from dishka.integrations.fastapi import FromDishka, inject
from fastapi import APIRouter, HTTPException, Request, status
from pydantic import BaseModel, Field

from app.application.chat.services.conversation_service import ConversationService
from app.application.chat.services.user_service import UserService
from app.application.chat.services.rate_limit_service import RateLimitService
from app.application.chat.services.conversation_memory import ConversationMemory
from app.application.chat.services.intent_detector_v2 import IntentDetectorV2, RESTRICTED_INTENTS
from app.application.chat.handlers.swap_handler_v2 import SwapHandlerV2
from app.application.chat.handlers.restricted_handler import RestrictedActionHandler
from app.application.guest.handlers.guest_handler_service import GuestHandlerService
from app.infrastructure.adapters.chat_unified_repository_sqla import ChatMessageRepositorySqla


# ========================================
# Request/Response Schemas
# ========================================


class CreateConversationRequest(BaseModel):
    """Request to create a new conversation."""
    
    title: str | None = Field(None, max_length=255)
    language: str = Field(default="en", pattern="^(en|es|pt|zh)$")


class SendMessageRequest(BaseModel):
    """Request to send a message."""
    
    content: str = Field(..., min_length=1, max_length=2000)
    language: str = Field(default="en", pattern="^(en|es|pt|zh)$")


class ConversationResponse(BaseModel):
    """Response for a conversation."""
    
    id: str
    title: str | None = None
    status: str
    created_at: str
    updated_at: str
    last_message_at: str | None = None
    message_count: int
    language: str


class MessageResponse(BaseModel):
    """Response for a message."""
    
    id: str
    role: str
    content: str
    intent: str | None = None
    is_restricted_action: bool = False
    created_at: str


class ConversationWithMessagesResponse(BaseModel):
    """Response for conversation with messages."""
    
    conversation: ConversationResponse
    messages: list[MessageResponse]


class ChatResponse(BaseModel):
    """Response from sending a message."""
    
    conversation_id: str
    message_id: str
    user_message: dict[str, Any]
    agent_message: dict[str, Any]
    routing: dict[str, Any]
    enrichment: dict[str, Any] | None = None
    registration_required: dict[str, Any] | None = None
    rate_limit_status: dict[str, Any] | None = None


class RateLimitErrorResponse(BaseModel):
    """Response for rate limit error."""
    
    error: str = "rate_limit_exceeded"
    reason: str
    limit: int
    current: int
    reset_in: int
    message: dict[str, str]


# ========================================
# Router Factory
# ========================================


def create_conversations_router() -> APIRouter:
    """Create the conversations router."""
    
    router = APIRouter(
        prefix="/conversations",
        tags=["Conversations"],
    )
    
    # ------------------------------------------
    # CRUD Endpoints
    # ------------------------------------------
    
    @router.post(
        "",
        response_model=ConversationResponse,
        status_code=status.HTTP_201_CREATED,
        summary="Create Conversation",
        description="Create a new conversation. Uses Privy token if provided, otherwise creates guest conversation.",
    )
    @inject
    async def create_conversation(
        request_body: CreateConversationRequest,
        http_request: Request,
        user_service: FromDishka[UserService],
        conversation_service: FromDishka[ConversationService],
    ) -> ConversationResponse:
        """Create a new conversation."""
        # Get user (authenticated or guest)
        ip_address = http_request.client.host if http_request.client else "unknown"
        privy_token = http_request.headers.get("Authorization", "").replace("Bearer ", "")
        
        user = await user_service.get_or_create_user(
            ip_address=ip_address,
            privy_token=privy_token if privy_token else None,
            language=request_body.language,
        )
        
        # Create conversation
        conversation = await conversation_service.create(
            user_id=user.id,
            title=request_body.title,
            language=request_body.language,
        )
        
        return ConversationResponse(
            id=str(conversation.id),
            title=conversation.title,
            status=conversation.status.value,
            created_at=conversation.created_at.isoformat(),
            updated_at=conversation.updated_at.isoformat(),
            last_message_at=conversation.last_message_at.isoformat() if conversation.last_message_at else None,
            message_count=conversation.message_count,
            language=conversation.language,
        )
    
    @router.get(
        "",
        response_model=list[ConversationResponse],
        status_code=status.HTTP_200_OK,
        summary="List Conversations",
        description="List conversations for the current user.",
    )
    @inject
    async def list_conversations(
        http_request: Request,
        user_service: FromDishka[UserService],
        conversation_service: FromDishka[ConversationService],
        status_filter: str = "active",
        limit: int = 20,
        offset: int = 0,
    ) -> list[ConversationResponse]:
        """List user conversations."""
        # Get user
        ip_address = http_request.client.host if http_request.client else "unknown"
        privy_token = http_request.headers.get("Authorization", "").replace("Bearer ", "")
        
        user = await user_service.get_or_create_user(
            ip_address=ip_address,
            privy_token=privy_token if privy_token else None,
        )
        
        # List conversations
        conversations = await conversation_service.list(
            user_id=user.id,
            status=status_filter,
            limit=limit,
            offset=offset,
        )
        
        return [
            ConversationResponse(
                id=conv["id"],
                title=conv["title"],
                status=conv["status"],
                created_at=conv["created_at"],
                updated_at=conv["updated_at"],
                last_message_at=conv.get("last_message_at"),
                message_count=conv["message_count"],
                language=conv["language"],
            )
            for conv in conversations
        ]
    
    @router.get(
        "/{conversation_id}",
        response_model=ConversationWithMessagesResponse,
        status_code=status.HTTP_200_OK,
        summary="Get Conversation",
        description="Get a conversation with its messages.",
    )
    @inject
    async def get_conversation(
        conversation_id: UUID,
        http_request: Request,
        user_service: FromDishka[UserService],
        conversation_service: FromDishka[ConversationService],
    ) -> ConversationWithMessagesResponse:
        """Get conversation with messages."""
        # Get user
        ip_address = http_request.client.host if http_request.client else "unknown"
        privy_token = http_request.headers.get("Authorization", "").replace("Bearer ", "")
        
        user = await user_service.get_or_create_user(
            ip_address=ip_address,
            privy_token=privy_token if privy_token else None,
        )
        
        # Get conversation with messages
        result = await conversation_service.get_with_messages(
            conversation_id=conversation_id,
            user_id=user.id,
        )
        
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found",
            )
        
        return ConversationWithMessagesResponse(
            conversation=ConversationResponse(**result["conversation"]),
            messages=[MessageResponse(**msg) for msg in result["messages"]],
        )
    
    @router.delete(
        "/{conversation_id}",
        response_model=ConversationResponse,
        status_code=status.HTTP_200_OK,
        summary="Archive Conversation",
        description="""
        Archive a conversation (soft delete).
        
        This endpoint archives the conversation, marking it as archived.
        Archived conversations are not shown in the default conversation list.
        The conversation can be restored later if needed.
        """,
    )
    @inject
    async def delete_conversation(
        conversation_id: UUID,
        http_request: Request,
        user_service: FromDishka[UserService],
        conversation_service: FromDishka[ConversationService],
    ) -> ConversationResponse:
        """
        Archive a conversation.
        
        This endpoint archives the conversation instead of permanently deleting it.
        Archived conversations are excluded from the default conversation list
        (which filters by status='active').
        """
        # Get user
        ip_address = http_request.client.host if http_request.client else "unknown"
        privy_token = http_request.headers.get("Authorization", "").replace("Bearer ", "")
        
        user = await user_service.get_or_create_user(
            ip_address=ip_address,
            privy_token=privy_token if privy_token else None,
        )
        
        # Archive conversation (instead of deleting)
        conversation = await conversation_service.archive(
            conversation_id=conversation_id,
            user_id=user.id,
        )
        
        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found",
            )
        
        return ConversationResponse(
            id=str(conversation.id),
            title=conversation.title,
            status=conversation.status.value,
            created_at=conversation.created_at.isoformat(),
            updated_at=conversation.updated_at.isoformat(),
            last_message_at=conversation.last_message_at.isoformat() if conversation.last_message_at else None,
            message_count=conversation.message_count,
            language=conversation.language,
        )
    
    @router.post(
        "/{conversation_id}/archive",
        response_model=ConversationResponse,
        status_code=status.HTTP_200_OK,
        summary="Archive Conversation",
        description="Archive a conversation.",
    )
    @inject
    async def archive_conversation(
        conversation_id: UUID,
        http_request: Request,
        user_service: FromDishka[UserService],
        conversation_service: FromDishka[ConversationService],
    ) -> ConversationResponse:
        """Archive a conversation."""
        # Get user
        ip_address = http_request.client.host if http_request.client else "unknown"
        privy_token = http_request.headers.get("Authorization", "").replace("Bearer ", "")
        
        user = await user_service.get_or_create_user(
            ip_address=ip_address,
            privy_token=privy_token if privy_token else None,
        )
        
        # Archive conversation
        conversation = await conversation_service.archive(
            conversation_id=conversation_id,
            user_id=user.id,
        )
        
        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found",
            )
        
        return ConversationResponse(
            id=str(conversation.id),
            title=conversation.title,
            status=conversation.status.value,
            created_at=conversation.created_at.isoformat(),
            updated_at=conversation.updated_at.isoformat(),
            last_message_at=conversation.last_message_at.isoformat() if conversation.last_message_at else None,
            message_count=conversation.message_count,
            language=conversation.language,
        )
    
    # ------------------------------------------
    # Message Endpoint
    # ------------------------------------------
    
    @router.post(
        "/{conversation_id}/messages",
        response_model=ChatResponse,
        status_code=status.HTTP_201_CREATED,
        summary="Send Message",
        description="""
        Send a message to a conversation.
        
        **Features:**
        - Conversational memory (context from last 10 messages)
        - Multi-turn flows (e.g., swap with multiple steps)
        - Intent detection with multi-language support
        - Rate limiting based on user type
        
        **User Types:**
        - Guest: 20 messages/hour, 50/day
        - Authenticated: 200 messages/hour, 1000/day
        - Premium: Unlimited
        """,
    )
    @inject
    async def send_message(
        conversation_id: UUID,
        request_body: SendMessageRequest,
        http_request: Request,
        user_service: FromDishka[UserService],
        conversation_service: FromDishka[ConversationService],
        rate_limit_service: FromDishka[RateLimitService],
        conversation_memory: FromDishka[ConversationMemory],
        handler_service: FromDishka[GuestHandlerService],
        message_repository: FromDishka[ChatMessageRepositorySqla],
    ) -> ChatResponse:
        """Send a message to a conversation."""
        from app.domain.chat.entities.chat_message import ChatMessage
        
        # Get user
        ip_address = http_request.client.host if http_request.client else "unknown"
        privy_token = http_request.headers.get("Authorization", "").replace("Bearer ", "")
        
        user = await user_service.get_or_create_user(
            ip_address=ip_address,
            privy_token=privy_token if privy_token else None,
            language=request_body.language,
        )
        
        # Check if user is blocked
        if user.is_blocked:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User is blocked",
            )
        
        # Check rate limit
        rate_result = await rate_limit_service.check_and_increment(user)
        if not rate_result.allowed:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail={
                    "error": "rate_limit_exceeded",
                    "reason": rate_result.reason,
                    "limit": rate_result.limit,
                    "current": rate_result.current,
                    "reset_in": rate_result.reset_in,
                    "message": {
                        "en": f"Rate limit exceeded. Try again in {rate_result.reset_in // 60} minutes.",
                        "es": f"Límite de tasa excedido. Intenta de nuevo en {rate_result.reset_in // 60} minutos.",
                        "pt": f"Limite de taxa excedido. Tente novamente em {rate_result.reset_in // 60} minutos.",
                    },
                },
            )
        
        # Get conversation (verify ownership)
        conversation = await conversation_service.get(
            conversation_id=conversation_id,
            user_id=user.id,
        )
        
        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found",
            )
        
        # Get conversation context for memory
        context = await conversation_memory.get_context(conversation_id)
        
        # Detect intent with context
        intent_detector = IntentDetectorV2()
        intent_result = intent_detector.detect(
            message=request_body.content,
            language=request_body.language,
            context=context,
        )
        
        # Initialize response variables
        agent_content = ""
        enrichment = None
        registration_required = None
        pending_action = None
        
        # Handle based on intent
        if intent_result.is_restricted:
            # Restricted action - return registration message
            restricted_handler = RestrictedActionHandler()
            handler_result = await restricted_handler.handle(
                intent=intent_result.intent.value,
                language=request_body.language,
            )
            agent_content = handler_result.content
            registration_required = handler_result.metadata
        
        elif intent_result.intent.value.startswith("SWAP"):
            # Swap flow (including continuation)
            swap_handler = SwapHandlerV2()
            
            # Check for continuation metadata
            continuation_step = None
            continuation_value = None
            if intent_result.metadata:
                continuation_step = intent_result.metadata.get("step")
                continuation_value = intent_result.metadata.get("value")
            
            # Get previous swap info from context for multi-turn flow
            previous_swap_info = context.pending_swap_info
            
            handler_result = await swap_handler.handle(
                message=request_body.content,
                context=context,
                language=request_body.language,
                continuation_step=continuation_step,
                continuation_value=continuation_value,
                previous_swap_info=previous_swap_info,
            )
            agent_content = handler_result.content
            enrichment = handler_result.enrichment
            pending_action = handler_result.pending_action
            if handler_result.requires_registration:
                registration_required = {
                    "required": True,
                    "reason": "action_required",
                    "signup_url": "/signup",
                }
        
        else:
            # Use existing handler service for other intents
            from app.application.chat.services.intent_detector import ChatIntent
            
            # Map intent
            try:
                mapped_intent = ChatIntent[intent_result.intent.value]
            except KeyError:
                mapped_intent = ChatIntent.GENERAL_CONVERSATION
            
            context_str = conversation_memory.build_context_string(context)
            handler_result = await handler_service.handle_intent(
                intent=mapped_intent,
                content=request_body.content,
                language=request_body.language,
                context=context_str,
            )
            agent_content = handler_result.get("content", "")
            enrichment = handler_result.get("enrichment")
            if handler_result.get("requires_registration"):
                registration_required = {
                    "required": True,
                    "reason": "action_required",
                    "signup_url": "/signup",
                }
        
        # Create and save user message
        user_message = ChatMessage.create_user_message(
            conversation_id=conversation_id,
            content=request_body.content,
            language=request_body.language,
        )
        
        # Create and save assistant message
        metadata = {}
        if pending_action:
            metadata["pending_action"] = pending_action
        # Store swap info for multi-turn swap flow persistence
        if intent_result.intent.value.startswith("SWAP") and hasattr(handler_result, "metadata"):
            swap_info = handler_result.metadata
            if swap_info:
                metadata["swap_info"] = swap_info
        
        assistant_message = ChatMessage.create_assistant_message(
            conversation_id=conversation_id,
            content=agent_content,
            intent=intent_result.intent.value,
            intent_confidence=intent_result.confidence,
            handler=intent_result.handler,
            is_restricted_action=intent_result.is_restricted,
            language=request_body.language,
            metadata=metadata,
        )
        
        # CRITICAL: Save messages to database for multi-turn flow persistence
        await message_repository.save(user_message)
        await message_repository.save(assistant_message)
        
        # Update conversation
        conversation.increment_messages()
        conversation.increment_messages()  # Both user and assistant
        if not conversation.title:
            conversation.auto_generate_title(request_body.content)
        
        # Build routing info
        routing = {
            "intent": intent_result.intent.value,
            "confidence": intent_result.confidence,
            "handler": intent_result.handler,
            "language": request_body.language,
            "is_demo_mode": user.is_guest,
            "user_type": user.user_type.value,
        }
        
        # Build rate limit status
        rate_limit_status = {
            "user_type": user.user_type.value,
            "remaining_hourly": rate_result.remaining_hourly,
            "remaining_daily": rate_result.remaining_daily,
        }
        
        return ChatResponse(
            conversation_id=str(conversation_id),
            message_id=str(assistant_message.id),
            user_message={
                "id": str(user_message.id),
                "role": user_message.role.value,
                "content": user_message.content,
                "created_at": user_message.created_at.isoformat(),
            },
            agent_message={
                "id": str(assistant_message.id),
                "role": assistant_message.role.value,
                "content": assistant_message.content,
                "created_at": assistant_message.created_at.isoformat(),
            },
            routing=routing,
            enrichment=enrichment,
            registration_required=registration_required,
            rate_limit_status=rate_limit_status,
        )
    
    return router

