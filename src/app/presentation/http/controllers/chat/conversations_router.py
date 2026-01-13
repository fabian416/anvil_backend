"""
Conversations Router.

CRUD endpoints for conversation management.
Supports both guest and authenticated users.
"""

from datetime import datetime
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
from app.application.chat.handlers.moonpay_swap_flow_handler import MoonPaySwapFlowHandler
from app.application.chat.handlers.moonpay_swap_handler import MoonPaySwapHandler
from app.application.chat.handlers.restricted_handler import RestrictedActionHandler
from app.application.guest.handlers.guest_handler_service import GuestHandlerService
from app.domain.ports.ai.llm_gateway import LLMGateway
from app.infrastructure.adapters.chat_unified_repository_sqla import ChatMessageRepositorySqla
from app.application.common.services.current_user import CurrentUserService
from app.application.common.exceptions.authorization import AuthorizationError
from app.infrastructure.auth.exceptions import AuthenticationError


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


class UpdateConversationRequest(BaseModel):
    """Request to update a conversation."""
    
    title: str | None = Field(None, max_length=255, description="New title for the conversation")


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
    metadata: dict[str, Any] | None = None  # Swap quote data, enrichment, etc.


class ConversationWithMessagesResponse(BaseModel):
    """Response for conversation with messages."""
    
    conversation: ConversationResponse
    messages: list[MessageResponse]


class ExecuteActionData(BaseModel):
    """Execute action data for executable intents (swap, deposit, withdraw, etc.)."""
    
    action_type: str = Field(..., description="Type of action: swap, deposit, withdraw, transfer, approve, bridge")
    chain: str = Field(default="base", description="Blockchain to execute on")
    from_token: str | None = Field(default=None, description="Source token symbol or address")
    to_token: str | None = Field(default=None, description="Destination token symbol (for swap)")
    amount: str | None = Field(default=None, description="Amount to execute (human readable)")
    protocol: str | None = Field(default=None, description="Protocol name (for deposit/withdraw)")
    vault_address: str | None = Field(default=None, description="Vault address (for Morpho deposits)")
    recipient: str | None = Field(default=None, description="Recipient address (for transfer)")
    slippage: float = Field(default=1.0, description="Slippage tolerance in percent")
    to_chain: str | None = Field(default=None, description="Destination chain (for cross-chain swap/bridge)")


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
    execute: ExecuteActionData | None = Field(
        default=None,
        description="Execute action data for executable intents (swap, deposit, withdraw, etc.)"
    )


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

    async def _resolve_chat_user(
        *,
        http_request: Request,
        user_service: UserService,
        current_user: CurrentUserService,
        language: str = "en",
    ):
        """
        Resolve the ChatUser for this request.
        
        Priority:
        1) Backend JWT (Authorization Bearer anvil_access_token) -> authenticated ChatUser
        2) Privy access token -> authenticated ChatUser (if Privy client configured)
        3) IP-based guest ChatUser
        """
        ip_address = http_request.client.host if http_request.client else "unknown"
        bearer_token = http_request.headers.get("Authorization", "").replace("Bearer ", "")

        authenticated_user_id: str | None = None
        authenticated_email: str | None = None
        try:
            app_user = await current_user.get_current_user()
            authenticated_user_id = str(app_user.id_.value)
            authenticated_email = app_user.email.value
        except (AuthenticationError, AuthorizationError):
            authenticated_user_id = None
            authenticated_email = None

        return await user_service.get_or_create_user(
            ip_address=ip_address,
            authenticated_user_id=authenticated_user_id,
            authenticated_email=authenticated_email,
            privy_token=bearer_token if bearer_token else None,
            language=language,
        )

    async def _strip_signup_prompt_for_authenticated(content: str) -> str:
        """
        Remove signup CTA blocks from responses when the caller is authenticated.
        
        /api/v1/conversations supports both guest and authenticated flows. Some demo
        handlers include "/signup" CTA text which is correct for guests, but confusing
        for authenticated users (already registered/logged in).
        """
        if not content:
            return content
        
        # Remove lines containing signup CTAs
        lines = content.splitlines()
        filtered_lines = []
        for line in lines:
            # Skip lines with signup CTAs
            if "/signup" in line.lower() or "👉" in line or "sign up" in line.lower():
                # Check if this is a standalone CTA line (not part of main content)
                if any(marker in line.lower() for marker in ["sign up", "signup", "👉", "→", "->"]):
                    continue  # Skip this line
            filtered_lines.append(line)
        
        result = "\n".join(filtered_lines).strip()
        
        # Also remove any trailing signup URLs or CTAs
        result = result.split("👉")[0].strip() if "👉" in result else result
        result = result.split("/signup")[0].strip() if "/signup" in result else result
        
        # Remove empty lines at the end
        while result.endswith("\n\n"):
            result = result.rstrip("\n")
        
        return result if result else content
    
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
        current_user: FromDishka[CurrentUserService],
        conversation_service: FromDishka[ConversationService],
    ) -> ConversationResponse:
        """Create a new conversation."""
        user = await _resolve_chat_user(
            http_request=http_request,
            user_service=user_service,
            current_user=current_user,
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
        current_user: FromDishka[CurrentUserService],
        conversation_service: FromDishka[ConversationService],
        status_filter: str = "active",
        limit: int = 20,
        offset: int = 0,
    ) -> list[ConversationResponse]:
        """List user conversations."""
        user = await _resolve_chat_user(
            http_request=http_request,
            user_service=user_service,
            current_user=current_user,
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
        description="""
        Get a conversation with its messages.

        **Query Parameters:**
        - `limit`: Optional. Maximum number of messages to return (default: 50, max: 100)

        **Example:**
        - `GET /api/v1/conversations/{id}` - Returns conversation with last 50 messages
        - `GET /api/v1/conversations/{id}?limit=10` - Returns conversation with last 10 messages
        """,
    )
    @inject
    async def get_conversation(
        conversation_id: UUID,
        http_request: Request,
        user_service: FromDishka[UserService],
        current_user: FromDishka[CurrentUserService],
        conversation_service: FromDishka[ConversationService],
        limit: int = 50,
    ) -> ConversationWithMessagesResponse:
        """Get conversation with messages.

        Args:
            conversation_id: The conversation UUID
            limit: Maximum number of messages to return (default: 50, max: 100)
        """
        # Validate and cap the limit
        if limit < 1:
            limit = 1
        elif limit > 100:
            limit = 100

        user = await _resolve_chat_user(
            http_request=http_request,
            user_service=user_service,
            current_user=current_user,
        )

        # Get conversation with messages
        result = await conversation_service.get_with_messages(
            conversation_id=conversation_id,
            user_id=user.id,
            message_limit=limit,
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
    
    @router.patch(
        "/{conversation_id}",
        response_model=ConversationResponse,
        status_code=status.HTTP_200_OK,
        summary="Update Conversation",
        description="""
        Update a conversation's title.
        
        This endpoint allows updating the conversation title.
        Other fields are not currently modifiable.
        """,
    )
    @inject
    async def update_conversation(
        conversation_id: UUID,
        request: UpdateConversationRequest,
        http_request: Request,
        user_service: FromDishka[UserService],
        current_user: FromDishka[CurrentUserService],
        conversation_service: FromDishka[ConversationService],
    ) -> ConversationResponse:
        """
        Update a conversation.
        
        Currently supports updating the title only.
        """
        import logging
        logger = logging.getLogger(__name__)
        
        user = await _resolve_chat_user(
            http_request=http_request,
            user_service=user_service,
            current_user=current_user,
        )
        
        logger.debug(
            f"Update conversation request: conversation_id={conversation_id}, "
            f"user_id={user.id}, user_type={user.user_type.value}, "
            f"identifier={user.identifier}, title={request.title}"
        )
        
        if request.title is not None:
            conversation = await conversation_service.update_title(
                conversation_id=conversation_id,
                user_id=user.id,
                title=request.title,
            )
        else:
            # If no fields provided, just fetch the conversation
            conversation = await conversation_service.get(
                conversation_id=conversation_id,
                user_id=user.id,
            )
        
        if not conversation:
            logger.warning(
                f"Conversation not found: conversation_id={conversation_id}, "
                f"user_id={user.id}, user_type={user.user_type.value}"
            )
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
        current_user: FromDishka[CurrentUserService],
        conversation_service: FromDishka[ConversationService],
    ) -> ConversationResponse:
        """
        Archive a conversation.
        
        This endpoint archives the conversation instead of permanently deleting it.
        Archived conversations are excluded from the default conversation list
        (which filters by status='active').
        """
        user = await _resolve_chat_user(
            http_request=http_request,
            user_service=user_service,
            current_user=current_user,
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
        current_user: FromDishka[CurrentUserService],
        conversation_service: FromDishka[ConversationService],
    ) -> ConversationResponse:
        """Archive a conversation."""
        user = await _resolve_chat_user(
            http_request=http_request,
            user_service=user_service,
            current_user=current_user,
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
        - Guest: 800 messages/hour
        - Authenticated: 1000 messages/hour
        - Premium: 10,000 messages/hour
        """,
    )
    @inject
    async def send_message(
        conversation_id: UUID,
        request_body: SendMessageRequest,
        http_request: Request,
        user_service: FromDishka[UserService],
        current_user: FromDishka[CurrentUserService],
        conversation_service: FromDishka[ConversationService],
        rate_limit_service: FromDishka[RateLimitService],
        conversation_memory: FromDishka[ConversationMemory],
        handler_service: FromDishka[GuestHandlerService],
        message_repository: FromDishka[ChatMessageRepositorySqla],
        llm_gateway: FromDishka[LLMGateway],
        moonpay_swap_handler: FromDishka[MoonPaySwapHandler],
    ) -> ChatResponse:
        """Send a message to a conversation."""
        from app.domain.chat.entities.chat_message import ChatMessage, MessageRole
        
        user = await _resolve_chat_user(
            http_request=http_request,
            user_service=user_service,
            current_user=current_user,
            language=request_body.language,
        )

        # Get wallet address for authenticated users
        wallet_address = None
        if user.is_authenticated:
            try:
                app_user = await current_user.get_current_user()
                if app_user.primary_wallet_address:
                    wallet_address = str(app_user.primary_wallet_address.value)
            except (AuthenticationError, AuthorizationError):
                # No wallet address available
                pass

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
        
        # Debug logging for intent detection
        import logging
        logger = logging.getLogger(__name__)
        logger.debug(
            f"Intent detected: {intent_result.intent.value} "
            f"(confidence: {intent_result.confidence}, "
            f"handler: {intent_result.handler}, "
            f"is_restricted: {intent_result.is_restricted}) "
            f"for message: '{request_body.content[:100]}'"
        )
        
        # Initialize response variables
        agent_content = ""
        enrichment = None
        registration_required = None
        pending_action = None
        execute_data = None  # Execute action data for /execute endpoint
        used_agent_gateway = False  # Flag for when AgentGateway (LLM) was used
        handler_result = {}  # Default empty handler result for metadata extraction
        
        # Handle based on intent
        if intent_result.is_restricted:
            # Restricted actions should only show signup CTA to guests.
            if user.is_guest:
                restricted_handler = RestrictedActionHandler()
                handler_result = await restricted_handler.handle(
                    intent=intent_result.intent.value,
                    language=request_body.language,
                )
                agent_content = handler_result.content
                registration_required = handler_result.metadata
            else:
                # Authenticated user: Use actual handlers with improved formatting
                # These intents are handled through SendMessageUnified for real data
                # Use guest handler service which already has the handlers configured
                from app.application.chat.services.intent_detector import ChatIntent
                
                # Map restricted intent to ChatIntent
                intent_map = {
                    "PORTFOLIO": ChatIntent.PORTFOLIO,
                    "BALANCE": ChatIntent.BALANCE,
                    "ACTIVITY": ChatIntent.ACTIVITY,
                    "RECEIVE": ChatIntent.RECEIVE,
                }
                mapped_intent = intent_map.get(intent_result.intent.value, ChatIntent.GENERAL_CONVERSATION)
                
                context_str = conversation_memory.build_context_string(context)
                handler_result = await handler_service.handle_intent(
                    intent=mapped_intent,
                    content=request_body.content,
                    language=request_body.language,
                    context=context_str,
                    is_authenticated=True,
                    wallet_address=wallet_address,
                    user_id=int(user.id) if user.id else None,
                )
                agent_content = handler_result.get("content", "")
                enrichment = handler_result.get("enrichment")
                pending_action = handler_result.get("pending_action")
                registration_required = None
        
        elif intent_result.intent.value.startswith("SWAP"):
            # Swap flow (including continuation)
            try:
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
                
                # Extract execute data if swap is complete (no pending_action means ready to execute)
                execute_data = None
                if handler_result.execute_data and not pending_action:
                    # Swap is complete and ready for execution
                    execute_data = ExecuteActionData(**handler_result.execute_data)
                
                if user.is_guest and handler_result.requires_registration:
                    registration_required = {
                        "required": True,
                        "reason": "action_required",
                        "signup_url": "/signup",
                    }
            except Exception as e:
                # Log the error for debugging
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"SwapHandlerV2 error for message '{request_body.content}': {e}", exc_info=True)
                
                # Fallback to guest handler service for swap
                from app.application.chat.services.intent_detector import ChatIntent
                context_str = conversation_memory.build_context_string(context)
                handler_result = await handler_service.handle_intent(
                    intent=ChatIntent.SWAP,
                    content=request_body.content,
                    language=request_body.language,
                    context=context_str,
                    is_authenticated=not user.is_guest,
                )
                agent_content = handler_result.get("content", "")
                enrichment = handler_result.get("enrichment")
                if user.is_guest and handler_result.get("requires_registration"):
                    registration_required = {
                        "required": True,
                        "reason": "action_required",
                        "signup_url": "/signup",
                    }

        elif intent_result.intent.value.startswith("MOONPAY_SWAP"):
            # MoonPay Swap flow (including continuation)
            try:
                moonpay_swap_flow_handler = MoonPaySwapFlowHandler(
                    moonpay_swap_handler=moonpay_swap_handler
                )

                # Check for continuation metadata
                continuation_step = None
                continuation_value = None
                if intent_result.metadata:
                    continuation_step = intent_result.metadata.get("step")
                    continuation_value = intent_result.metadata.get("value")

                # Get previous swap info from context for multi-turn flow
                previous_swap_info = context.pending_moonpay_swap_info

                handler_result = await moonpay_swap_flow_handler.handle(
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

                # Extract execute data if swap is complete (no pending_action means ready to execute)
                execute_data = None
                if handler_result.execute_data and not pending_action:
                    # Swap is complete and ready for execution - show banner
                    execute_data = ExecuteActionData(**handler_result.execute_data)

                if user.is_guest and handler_result.requires_registration:
                    registration_required = {
                        "required": True,
                        "reason": "action_required",
                        "signup_url": "/signup",
                    }
            except Exception as e:
                # Log the error for debugging
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"MoonPaySwapFlowHandler error for message '{request_body.content}': {e}", exc_info=True)

                # Fallback to guest handler service for swap
                from app.application.chat.services.intent_detector import ChatIntent
                context_str = conversation_memory.build_context_string(context)
                handler_result = await handler_service.handle_intent(
                    intent=ChatIntent.SWAP,
                    content=request_body.content,
                    language=request_body.language,
                    context=context_str,
                    is_authenticated=not user.is_guest,
                )
                agent_content = handler_result.get("content", "")
                enrichment = handler_result.get("enrichment")
                if user.is_guest and handler_result.get("requires_registration"):
                    registration_required = {
                        "required": True,
                        "reason": "action_required",
                        "signup_url": "/signup",
                    }

        elif intent_result.intent.value == "LENDING":
            # Handle LENDING intent with continuation support
            from app.application.chat.services.intent_detector import ChatIntent

            # Check for continuation metadata
            continuation_step = None
            intent_metadata = None
            if intent_result.metadata:
                continuation_step = intent_result.metadata.get("step")
                intent_metadata = intent_result.metadata

            # Get previous lending info from context
            previous_lending_info = context.pending_lending_info

            context_str = conversation_memory.build_context_string(context)
            handler_result = await handler_service.handle_intent(
                intent=ChatIntent.LENDING,
                content=request_body.content,
                language=request_body.language,
                context=context_str,
                is_authenticated=not user.is_guest,
                continuation_step=continuation_step,
                previous_lending_info=previous_lending_info,
                wallet_address=wallet_address,
            )
            agent_content = handler_result.get("content", "")
            enrichment = handler_result.get("enrichment")
            pending_action = handler_result.get("pending_action")
            if user.is_guest and handler_result.get("requires_registration"):
                registration_required = {
                    "required": True,
                    "reason": "action_required",
                    "signup_url": "/signup",
                }
        
        elif intent_result.intent.value == "MONEY_MARKET":
            # Handle MONEY_MARKET intent (not restricted, uses guest handler service)
            from app.application.chat.services.intent_detector import ChatIntent
            
            # Check for continuation metadata
            continuation_step = None
            if intent_result.metadata:
                continuation_step = intent_result.metadata.get("step")
            
            # Get previous money market info from context
            previous_money_market_info = context.pending_money_market_info
            
            context_str = conversation_memory.build_context_string(context)
            handler_result = await handler_service.handle_intent(
                intent=ChatIntent.MONEY_MARKET,
                content=request_body.content,
                language=request_body.language,
                context=context_str,
                is_authenticated=not user.is_guest,
            )
            agent_content = handler_result.get("content", "")
            enrichment = handler_result.get("enrichment")
            pending_action = handler_result.get("pending_action")
            if user.is_guest and handler_result.get("requires_registration"):
                registration_required = {
                    "required": True,
                    "reason": "action_required",
                    "signup_url": "/signup",
                }
        
        elif intent_result.intent.value.startswith("BUY"):
            # Handle BUY and BUY_CONTINUE intents (on-ramp crypto purchase with multi-turn flow)
            from app.application.chat.handlers.buy_handler import BuyHandler, BuyInfo
            
            # [BUY_DEBUG] Log entry to BUY handler
            logger.info(f"[BUY_DEBUG] Entering BUY handler section")
            logger.info(f"[BUY_DEBUG] Intent: {intent_result.intent.value}")
            logger.info(f"[BUY_DEBUG] User is_guest: {user.is_guest}")
            logger.info(f"[BUY_DEBUG] User identifier: {user.identifier}")
            
            # For guests, use the old informative flow
            if user.is_guest:
                from app.application.chat.services.intent_detector import ChatIntent
                context_str = conversation_memory.build_context_string(context)
                handler_result = await handler_service.handle_intent(
                    intent=ChatIntent.BUY,
                    content=request_body.content,
                    language=request_body.language,
                    context=context_str,
                    is_authenticated=False,
                    user_id=None,
                )
                agent_content = handler_result.get("content", "")
                enrichment = handler_result.get("enrichment")
                pending_action = handler_result.get("pending_action")
                if handler_result.get("requires_registration"):
                    registration_required = {
                        "required": True,
                        "reason": "action_required",
                        "signup_url": "/signup",
                    }
            else:
                # Authenticated users get the multi-turn conversational flow
                logger.info(f"[BUY_DEBUG] User is authenticated, using multi-turn flow")
                try:
                    # Get dependencies for BuyHandler
                    from app.domain.ports.wallet.wallet_repository import WalletRepository
                    from dishka import AsyncContainer
                    
                    container: AsyncContainer = http_request.state.dishka_container
                    wallet_repo = await container.get(WalletRepository)
                    
                    buy_handler = BuyHandler(
                        wallet_repository=wallet_repo,
                        current_user_service=current_user,
                    )
                    
                    # Check for continuation metadata
                    continuation_step = None
                    continuation_value = None
                    if intent_result.metadata:
                        continuation_step = intent_result.metadata.get("step")
                        continuation_value = intent_result.metadata.get("value")
                    
                    logger.info(f"[BUY_DEBUG] continuation_step: {continuation_step}")
                    logger.info(f"[BUY_DEBUG] continuation_value: {continuation_value}")
                    
                    # Get previous buy info from context for multi-turn flow
                    previous_buy_info = None
                    if context.pending_buy_info:
                        previous_buy_info = BuyInfo.from_dict(context.pending_buy_info)
                        logger.info(f"[BUY_DEBUG] previous_buy_info: {previous_buy_info}")
                    else:
                        logger.info(f"[BUY_DEBUG] No previous_buy_info in context")
                    
                    # Handle based on whether it's a continuation or new buy request
                    if continuation_step and continuation_value:
                        # Continuation of multi-turn flow
                        logger.info(f"[BUY_DEBUG] Calling handle_buy_continuation()")
                        handler_result = await buy_handler.handle_buy_continuation(
                            user_id=int(user.identifier),
                            message=continuation_value,
                            step=continuation_step,
                            previous_buy_info=previous_buy_info,
                            language=request_body.language,
                        )
                    else:
                        # New buy request - start the flow
                        logger.info(f"[BUY_DEBUG] Calling start_buy_flow()")
                        handler_result = await buy_handler.start_buy_flow(
                            user_id=int(user.identifier),
                            message=request_body.content,
                            language=request_body.language,
                        )
                    
                    logger.info(f"[BUY_DEBUG] handler_result.content: {handler_result.content[:100] if handler_result.content else 'None'}...")
                    logger.info(f"[BUY_DEBUG] handler_result.pending_action: {handler_result.pending_action}")
                    agent_content = handler_result.content
                    enrichment = {
                        "wallet_address": handler_result.wallet_address,
                        "supported_assets": handler_result.supported_assets,
                        "supported_networks": handler_result.supported_networks,
                        "requires_privy_modal": handler_result.requires_privy_modal,
                        "action_type": "fund_wallet" if handler_result.requires_privy_modal else None,
                    }
                    pending_action = handler_result.pending_action
                    
                    # Extract execute data if buy is complete (no pending_action means ready to execute)
                    if handler_result.execute_data and not pending_action:
                        execute_data = ExecuteActionData(**handler_result.execute_data)
                    
                except Exception as e:
                    # Log the error and fallback to old handler
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.error(f"BuyHandler error for message '{request_body.content}': {e}", exc_info=True)
                    
                    # Fallback to old handler service
                    from app.application.chat.services.intent_detector import ChatIntent
                    context_str = conversation_memory.build_context_string(context)
                    handler_result = await handler_service.handle_intent(
                        intent=ChatIntent.BUY,
                        content=request_body.content,
                        language=request_body.language,
                        context=context_str,
                        is_authenticated=True,
                        user_id=int(user.identifier),
                    )
                    agent_content = handler_result.get("content", "")
                    enrichment = handler_result.get("enrichment")
                    pending_action = handler_result.get("pending_action")
        
        else:
            # Use existing handler service for other intents
            from app.application.chat.services.intent_detector import ChatIntent
            import logging
            logger = logging.getLogger(__name__)
            
            # Map intent
            try:
                mapped_intent = ChatIntent[intent_result.intent.value]
            except KeyError:
                mapped_intent = ChatIntent.GENERAL_CONVERSATION
            
            # For authenticated users with GENERAL_CONVERSATION intent,
            # use LLMGateway directly for real LLM response
            if not user.is_guest and mapped_intent == ChatIntent.GENERAL_CONVERSATION:
                try:
                    # Build context from conversation memory
                    context_str = conversation_memory.build_context_string(context)
                    
                    # Build messages for LLM
                    system_prompt = """You are Anvil, a specialized DeFi assistant focused EXCLUSIVELY on decentralized finance, crypto trading, and blockchain technology.

⚠️ CRITICAL SCOPE RESTRICTION:
- ONLY answer questions about: DeFi protocols, crypto, trading, blockchain, portfolio management, tokens, NFTs, DAOs
- If the query is NOT crypto/DeFi related, respond with: "I'm Anvil, a specialized DeFi assistant. I can only help with crypto and DeFi topics. Try asking about your portfolio, token swaps, lending rates, or market analysis."
- Do NOT engage with: general knowledge, baking, cooking, weather, jokes, personal advice, or any non-crypto topics
- Be strict about scope - when in doubt, decline politely

⚠️ CONTEXT ISOLATION:
- If conversation history contains previous OUT_OF_SCOPE rejections (non-crypto topics), IGNORE them completely
- Do NOT reference or connect current query to previous rejected topics
- Treat each DeFi query independently - do not mix crypto questions with previous off-topic context

For valid DeFi/crypto questions:
- Be concise, accurate, and friendly
- If you don't know something, say so
- Respond in the same language the user uses
- Use conversation history for context ONLY for DeFi-related exchanges"""
                    
                    # Build user message with context if available
                    user_prompt = request_body.content
                    if context_str:
                        user_prompt = f"Previous conversation:\n{context_str}\n\nUser: {request_body.content}"
                    
                    messages = [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ]
                    
                    # Using 3B model because 70B is frequently overloaded ("Model busy")
                    raw_response = await llm_gateway.generate(
                        model="meta-llama/Llama-3.2-3B-Instruct",
                        messages=messages,
                        temperature=0.7,
                        max_tokens=500,
                    )
                    
                    # Normalize response - extract text if tuple/dict returned
                    if isinstance(raw_response, tuple):
                        agent_content = str(raw_response[0]) if raw_response else ""
                    elif isinstance(raw_response, dict):
                        agent_content = raw_response.get("content", raw_response.get("text", str(raw_response)))
                    else:
                        agent_content = str(raw_response) if raw_response else ""
                    
                    enrichment = None
                    pending_action = None
                    
                except Exception as e:
                    import logging
                    logging.getLogger(__name__).error(f"LLM call failed: {e}")
                    # Fallback to handler
                    context_str = conversation_memory.build_context_string(context)
                    handler_result = await handler_service.handle_intent(
                        intent=mapped_intent,
                        content=request_body.content,
                        language=request_body.language,
                        context=context_str,
                        is_authenticated=True,
                    )
                    agent_content = handler_result.get("content", "")
                    enrichment = handler_result.get("enrichment")
                    pending_action = handler_result.get("pending_action")
            else:
                # Use GuestHandlerService for:
                # - Guest users (all intents)
                # - Authenticated users with non-GENERAL_CONVERSATION intents (swap, buy, etc.)
                context_str = conversation_memory.build_context_string(context)
                handler_result = await handler_service.handle_intent(
                    intent=mapped_intent,
                    content=request_body.content,
                    language=request_body.language,
                    context=context_str,
                    is_authenticated=not user.is_guest,
                )
                agent_content = handler_result.get("content", "")
                enrichment = handler_result.get("enrichment")
                pending_action = handler_result.get("pending_action")
                if user.is_guest and handler_result.get("requires_registration"):
                    registration_required = {
                        "required": True,
                        "reason": "action_required",
                        "signup_url": "/signup",
                    }

        # For authenticated users, strip demo "signup" CTA text that some handlers embed.
        if not user.is_guest:
            agent_content = await _strip_signup_prompt_for_authenticated(agent_content)
            registration_required = None
        
        # Create user message with explicit timestamp
        from datetime import timedelta
        user_timestamp = datetime.utcnow()
        user_message = ChatMessage.create_user_message(
            conversation_id=conversation_id,
            content=request_body.content,
            language=request_body.language,
            created_at=user_timestamp,
        )
        
        # Create assistant message with timestamp 1ms after user message
        # This ensures correct chronological ordering in the database
        assistant_timestamp = user_timestamp + timedelta(milliseconds=1)
        
        # Prepare metadata for assistant message
        metadata = {}
        if pending_action:
            metadata["pending_action"] = pending_action
        # Store swap info for multi-turn swap flow persistence
        if intent_result.intent.value.startswith("SWAP") and hasattr(handler_result, "metadata"):
            swap_info = handler_result.metadata
            if swap_info:
                metadata["swap_info"] = swap_info
        # Store MoonPay swap info for multi-turn flow persistence
        if intent_result.intent.value.startswith("MOONPAY_SWAP") and hasattr(handler_result, "metadata"):
            moonpay_swap_info = handler_result.metadata
            if moonpay_swap_info:
                metadata["moonpay_swap_info"] = moonpay_swap_info
                # Also store in swap_info for compatibility
                metadata["swap_info"] = moonpay_swap_info
        # Store lending info for multi-turn lending flow persistence
        if intent_result.intent.value == "LENDING":
            if handler_result.get("lending_info"):
                metadata["lending_info"] = handler_result["lending_info"]
            elif pending_action and pending_action.startswith("lending_"):
                # Create lending_info from handler result if not provided
                metadata["lending_info"] = {
                    "chain": handler_result.get("enrichment", {}).get("chain", "base"),
                    "asset": handler_result.get("enrichment", {}).get("asset", "USDC"),
                }
        
        # Store portfolio info for multi-turn portfolio flow persistence
        if intent_result.intent.value == "PORTFOLIO" and pending_action and pending_action.startswith("portfolio_"):
            metadata["portfolio_info"] = {
                "chain": handler_result.get("enrichment", {}).get("chain", "base"),
            }
        
        # Store activity info for multi-turn activity flow persistence
        if intent_result.intent.value == "ACTIVITY" and pending_action and pending_action.startswith("activity_"):
            metadata["activity_info"] = {
                "chain": handler_result.get("enrichment", {}).get("chain"),
            }
        
        # Store money market info for multi-turn money market flow persistence
        if intent_result.intent.value == "MONEY_MARKET" and pending_action and pending_action.startswith("money_market_"):
            metadata["money_market_info"] = {
                "chain": handler_result.get("enrichment", {}).get("chain", "ethereum"),
                "asset": handler_result.get("enrichment", {}).get("asset", "USDC"),
            }
        
        # Store buy info for multi-turn buy flow persistence
        if intent_result.intent.value.startswith("BUY") and hasattr(handler_result, "metadata"):
            buy_info = handler_result.metadata
            if buy_info:
                metadata["buy_info"] = buy_info
        
        # Determine handler name for routing info
        handler_name = "agent_gateway_llm" if used_agent_gateway else intent_result.handler
        
        assistant_message = ChatMessage.create_assistant_message(
            conversation_id=conversation_id,
            content=agent_content,
            intent=intent_result.intent.value,
            intent_confidence=intent_result.confidence,
            handler=handler_name,
            is_restricted_action=bool(registration_required),
            language=request_body.language,
            metadata=metadata,
            created_at=assistant_timestamp,
        )
        
        # CRITICAL: Save messages to database for multi-turn flow persistence
        await message_repository.save(user_message)
        await message_repository.save(assistant_message)
        
        # Update conversation message count
        conversation.increment_messages()
        conversation.increment_messages()  # Both user and assistant
        
        # Auto-generate title if needed
        if not conversation.title:
            conversation.auto_generate_title(request_body.content)
        
        # Note: Conversation updates (message_count, title) are handled by the repository
        # when messages are saved. The conversation entity is updated in memory for response.
        
        # Build routing info
        routing = {
            "intent": intent_result.intent.value,
            "confidence": intent_result.confidence,
            "handler": handler_name,
            "language": request_body.language,
            "user_type": user.user_type.value,
        }

        # Only include demo mode flag for guest users
        if user.is_guest:
            routing["is_demo_mode"] = True
        
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
            execute=execute_data,
        )
    
    # ========================================
    # Swap Quote Persistence Endpoint
    # ========================================
    
    class SaveSwapQuoteRequest(BaseModel):
        """Request to save swap quote data to a message."""
        
        swap_quote: dict[str, Any] = Field(
            ...,
            description="MoonPay swap quote data including fromToken, toToken, amount, rate, etc."
        )
        status: str = Field(
            default="pending",
            description="Swap status: pending, executed, cancelled, expired"
        )
    
    # ========================================
    # System Message Endpoint (Skip LLM)
    # ========================================
    
    class CreateSystemMessageRequest(BaseModel):
        """Request to create a system/assistant message without triggering LLM."""
        
        content: str = Field(..., min_length=1, max_length=5000, description="Message content")
        metadata: dict[str, Any] | None = Field(
            default=None,
            description="Optional metadata (type, transaction_id, etc.)"
        )
        language: str = Field(default="en", pattern="^(en|es|pt|zh)$")
    
    class SystemMessageResponse(BaseModel):
        """Response for a created system message."""
        
        id: str
        role: str
        content: str
        created_at: str
        metadata: dict[str, Any] | None = None
    
    @router.post(
        "/{conversation_id}/system-message",
        response_model=SystemMessageResponse,
        status_code=status.HTTP_201_CREATED,
        summary="Create System Message",
        description="""
        Create an assistant message without triggering LLM response.
        
        **Use Cases:**
        - Transaction confirmations (MoonPay, swap execution)
        - System notifications
        - Status updates
        
        **Key Features:**
        - Message is saved with role="assistant"
        - NO LLM is invoked
        - Message appears on the left side (assistant) in chat UI
        - Persists in conversation history
        
        **Metadata Types:**
        - moonpay_confirmation: MoonPay purchase confirmation
        - swap_confirmation: Swap execution confirmation
        - system_notification: General system notification
        """,
    )
    @inject
    async def create_system_message(
        conversation_id: UUID,
        request_body: CreateSystemMessageRequest,
        http_request: Request,
        user_service: FromDishka[UserService],
        current_user: FromDishka[CurrentUserService],
        conversation_service: FromDishka[ConversationService],
        message_repository: FromDishka[ChatMessageRepositorySqla],
    ) -> SystemMessageResponse:
        """
        Create an assistant message without triggering LLM.
        
        This endpoint is used for transaction confirmations and system notifications
        that should appear as assistant messages but don't need LLM processing.
        """
        from app.domain.chat.entities.chat_message import ChatMessage, MessageRole
        import logging
        logger = logging.getLogger(__name__)
        
        # Resolve user
        user = await _resolve_chat_user(
            http_request=http_request,
            user_service=user_service,
            current_user=current_user,
            language=request_body.language,
        )
        
        # Verify conversation belongs to user
        conversation = await conversation_service.get(
            conversation_id=conversation_id,
            user_id=user.id,
        )
        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found",
            )
        
        # Build metadata
        metadata = request_body.metadata or {}
        metadata["system_message"] = True  # Mark as system-generated
        metadata["skip_llm"] = True  # Indicate LLM was not used
        
        # Create assistant message directly (no LLM invocation)
        assistant_message = ChatMessage.create_assistant_message(
            conversation_id=conversation_id,
            content=request_body.content,
            intent="SYSTEM_MESSAGE",
            intent_confidence=1.0,
            handler="system_message_handler",
            is_restricted_action=False,
            language=request_body.language,
            metadata=metadata,
        )
        
        # Save to database
        await message_repository.save(assistant_message)
        
        # Update conversation message count
        conversation.increment_messages()
        
        logger.info(
            f"Created system message {assistant_message.id} in conversation {conversation_id} "
            f"for user {user.id} (type: {metadata.get('type', 'unknown')})"
        )
        
        return SystemMessageResponse(
            id=str(assistant_message.id),
            role=assistant_message.role.value,
            content=assistant_message.content,
            created_at=assistant_message.created_at.isoformat(),
            metadata=assistant_message.metadata,
        )
    
    class SaveSwapQuoteResponse(BaseModel):
        """Response after saving swap quote."""
        
        message_id: str
        metadata: dict[str, Any]
    
    @router.patch(
        "/{conversation_id}/messages/{message_id}/swap-quote",
        response_model=SaveSwapQuoteResponse,
        status_code=status.HTTP_200_OK,
        summary="Save Swap Quote",
        description="""
        Save MoonPay swap quote data to a message for persistence.
        
        This endpoint allows the frontend to save swap quote data after
        receiving it from MoonPay, ensuring the swap appears in chat history.
        
        **Swap Status Values:**
        - pending: Quote received, awaiting user action
        - executed: Swap was executed successfully
        - cancelled: User cancelled the swap
        - expired: Quote expired before execution
        """,
    )
    @inject
    async def save_swap_quote(
        conversation_id: UUID,
        message_id: UUID,
        request_body: SaveSwapQuoteRequest,
        http_request: Request,
        user_service: FromDishka[UserService],
        current_user: FromDishka[CurrentUserService],
        conversation_service: FromDishka[ConversationService],
        message_repository: FromDishka[ChatMessageRepositorySqla],
    ) -> SaveSwapQuoteResponse:
        """Save swap quote data to a message."""
        import logging
        logger = logging.getLogger(__name__)
        
        # Resolve user
        user = await _resolve_chat_user(
            http_request=http_request,
            user_service=user_service,
            current_user=current_user,
        )
        
        # Verify conversation belongs to user
        conversation = await conversation_service.get(
            conversation_id=conversation_id,
            user_id=user.id,
        )
        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found",
            )
        
        # Build swap metadata
        swap_metadata = {
            "swap_info": {
                "quote": request_body.swap_quote,
                "status": request_body.status,
                "saved_at": datetime.utcnow().isoformat(),
            }
        }
        
        # Update message metadata
        updated_message = await message_repository.update_metadata(
            message_id=message_id,
            metadata=swap_metadata,
            merge=True,
        )
        
        if not updated_message:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Message not found",
            )
        
        logger.info(
            f"Saved swap quote for message {message_id} in conversation {conversation_id}"
        )
        
        return SaveSwapQuoteResponse(
            message_id=str(message_id),
            metadata=updated_message.metadata,
        )
    
    return router

