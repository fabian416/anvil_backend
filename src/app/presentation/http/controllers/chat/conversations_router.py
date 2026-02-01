"""
Conversations Router.

CRUD endpoints for conversation management.
Supports both guest and authenticated users.
"""

from datetime import datetime, timedelta, UTC
from typing import Any
from uuid import UUID

from dishka.integrations.fastapi import FromDishka, inject
from fastapi import APIRouter, HTTPException, Request, status
from pydantic import BaseModel, Field, field_validator

from app.application.chat.services.conversation_service import ConversationService
from app.application.chat.services.user_service import UserService
from app.application.chat.services.rate_limit_service import RateLimitService
from app.application.chat.services.conversation_memory import ConversationMemory
from app.application.chat.services.intent_detector_v2 import IntentDetectorV2, RESTRICTED_INTENTS
from app.application.chat.services.user_context_service import UserContextService
from app.application.chat.handlers.swap_handler_v2 import SwapHandlerV2
from app.application.chat.commands.send_message_with_supervisor import SendMessageWithSupervisor
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
    
    model_config = {"extra": "ignore"}  # Ignore unknown fields from workflows

    action_type: str = Field(..., description="Type of action: swap, deposit, withdraw, transfer, approve, bridge")
    provider: str | None = Field(default=None, description="Execution provider: privy_0x for Privy + 0x swaps")
    chain: str = Field(default="base", description="Blockchain to execute on")
    from_token: str | None = Field(default=None, description="Source token symbol or address")
    to_token: str | None = Field(default=None, description="Destination token symbol (for swap)")
    amount: str | None = Field(default=None, description="Amount to execute (human readable)")
    
    @field_validator("amount", "quote_amount", "exchange_rate", "network_fee_usd", 
                     "min_amount_out", "price_impact", "gas_estimate",
                     "from_token_price_usd", "to_token_price_usd", 
                     "from_token_24h_change", "value_usd", mode="before")
    @classmethod
    def coerce_to_str(cls, v):
        """Coerce numeric values to string (workflows may return int/float)."""
        if v is not None:
            return str(v)
        return v
    
    protocol: str | None = Field(default=None, description="Protocol name (for deposit/withdraw)")
    vault_address: str | None = Field(default=None, description="Vault address (for Morpho deposits)")
    asset_address: str | None = Field(default=None, description="Underlying asset address (for Morpho deposits)")
    asset_symbol: str | None = Field(default=None, description="Underlying asset symbol (for Morpho deposits)")

    # Aave V3 specific fields
    pool_address: str | None = Field(default=None, description="Aave V3 Pool address")
    referral_code: int | None = Field(default=None, description="Aave referral code (default 0)")
    supply_apy: float | None = Field(default=None, description="Aave supply APY")
    available_liquidity_usd: float | None = Field(default=None, description="Available liquidity in USD")

    recipient: str | None = Field(default=None, description="Recipient address (for transfer)")
    slippage: float = Field(default=1.0, description="Slippage tolerance in percent")
    to_chain: str | None = Field(default=None, description="Destination chain (for cross-chain swap/bridge)")

    # Quote preview fields (for display before execution)
    quote_id: str | None = Field(default=None, description="Quote identifier")
    quote_amount: str | None = Field(default=None, description="Estimated output amount")
    min_amount_out: str | None = Field(default=None, description="Minimum output amount with slippage")
    exchange_rate: str | None = Field(default=None, description="Exchange rate for the swap")
    network_fee_usd: str | None = Field(default=None, description="Estimated network fee in USD")
    expires_at: str | None = Field(default=None, description="Quote expiration timestamp")
    
    # Price impact and gas fields
    price_impact: str | None = Field(default=None, description="Price impact percentage")
    gas_estimate: str | None = Field(default=None, description="Estimated gas units")
    
    # Token address fields
    from_token_address: str | None = Field(default=None, description="Source token contract address")
    to_token_address: str | None = Field(default=None, description="Destination token contract address")
    
    # Market data fields
    from_token_price_usd: str | None = Field(default=None, description="Source token price in USD")
    to_token_price_usd: str | None = Field(default=None, description="Destination token price in USD")
    from_token_24h_change: str | None = Field(default=None, description="Source token 24h price change %")
    value_usd: str | None = Field(default=None, description="Total transaction value in USD")


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
        status_code=status.HTTP_200_OK,
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
        swap_handler_v2: FromDishka[SwapHandlerV2],  # Hyperliquid spot swap handler
        supervisor_command: FromDishka[SendMessageWithSupervisor] = None,  # Supervisor for authenticated users
        user_context_service: FromDishka[UserContextService] = None,  # Context-aware agents
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
        
        import logging
        logger = logging.getLogger(__name__)
        
        # ============================================================
        # ✨ AUTHENTICATED SUPERVISOR PATH (LLM-based Multi-Agent) ✨
        # ============================================================
        # For authenticated users, use the AuthenticatedSupervisorCoordinator
        # for intelligent LLM-based routing to multiple agents.
        # This provides the same quality as guest chat but with real data access.
        # ============================================================
        if not user.is_guest and supervisor_command is not None:
            try:
                logger.info(
                    f"🔄 Using Authenticated Supervisor for user {user.identifier}",
                    extra={
                        "conversation_id": str(conversation_id),
                        "message_preview": request_body.content[:100],
                        "wallet_address": wallet_address[:10] + "..." if wallet_address else None,
                    }
                )
                
                # Build conversation history from context
                # Note: context.messages is returned NEWEST-FIRST from the repository
                # We need the most recent messages for workflow continuation detection
                conversation_history = []
                if context.messages:
                    # Take first 10 (newest) messages and reverse to get chronological order
                    # This matches MAX_CONTEXT_MESSAGES in conversation_memory.py
                    recent_messages = context.messages[:10]
                    for msg in reversed(recent_messages):  # Oldest-first for history
                        # ChatMessage objects have role and content attributes
                        role = msg.role.value if hasattr(msg.role, 'value') else str(msg.role)
                        msg_dict = {
                            "role": role,
                            "content": msg.content if hasattr(msg, 'content') else str(msg),
                        }
                        # Include metadata for workflow continuation detection
                        if hasattr(msg, 'metadata') and msg.metadata:
                            msg_dict["metadata"] = msg.metadata
                        conversation_history.append(msg_dict)
                
                # Build user context for supervisor
                user_context = {
                    "user_id": user.identifier,
                    "wallet_address": wallet_address,
                    "is_authenticated": True,
                }
                
                # Load context-aware data for personalized responses
                if user_context_service and not user.is_guest:
                    try:
                        context_aware = await user_context_service.get_context(user.id)
                        if context_aware:
                            user_context["context_aware"] = context_aware
                            logger.debug(
                                f"Loaded context-aware data: portfolio={context_aware.portfolio_state}, "
                                f"activity={context_aware.activity_level}, type={context_aware.user_type}"
                            )
                            
                            # If context_aware shows zero balance but user has wallet,
                            # try to fetch real-time portfolio data as fallback
                            # This handles cases where Celery task hasn't synced balance yet
                            if (
                                wallet_address
                                and float(context_aware.total_balance_usd or 0) == 0
                                and hasattr(handler_service, '_portfolio_service')
                                and handler_service._portfolio_service
                            ):
                                try:
                                    from app.domain.enums.chain_type import ChainType
                                    from decimal import Decimal
                                    
                                    logger.info(f"Context-aware shows $0, fetching real-time balance for {wallet_address[:10]}...")
                                    portfolio = await handler_service._portfolio_service.get_portfolio_by_address(
                                        address=wallet_address,
                                        chain=ChainType.BASE,
                                    )
                                    
                                    if portfolio and portfolio.total_usd > 0:
                                        # Update context_aware with real-time balance
                                        context_aware.total_balance_usd = Decimal(str(portfolio.total_usd))
                                        context_aware.token_count = len(portfolio.tokens) if portfolio.tokens else 0
                                        context_aware.primary_chain = portfolio.chain
                                        logger.info(f"Updated context with real-time balance: ${portfolio.total_usd:.2f}")
                                except Exception as portfolio_err:
                                    logger.debug(f"Real-time portfolio fetch failed (non-critical): {portfolio_err}")
                    except Exception as ctx_err:
                        logger.warning(f"Failed to load context-aware data: {ctx_err}")
                
                # Check for fast-path greeting
                if supervisor_command.is_simple_greeting(request_body.content):
                    supervisor_result = await supervisor_command.execute_fast_path_greeting(
                        conversation_id=conversation_id,
                        message=request_body.content,
                        language=request_body.language,
                    )
                else:
                    # Full supervisor workflow
                    supervisor_result = await supervisor_command.execute(
                        conversation_id=conversation_id,
                        message=request_body.content,
                        language=request_body.language,
                        conversation_history=conversation_history,
                        user_context=user_context,
                    )
                
                # Create user message (timedelta already imported at module level)
                user_timestamp = datetime.now(UTC)
                from app.domain.chat.entities.chat_message import ChatMessage
                
                user_message = ChatMessage.create_user_message(
                    conversation_id=conversation_id,
                    content=request_body.content,
                    language=request_body.language,
                    created_at=user_timestamp,
                )
                await message_repository.save(user_message)
                
                # Create assistant message
                assistant_timestamp = user_timestamp + timedelta(milliseconds=1)
                
                # Build message metadata including workflow state for multi-step continuation
                message_metadata = {
                    "agents_used": supervisor_result.agents_used,
                    "workflow_type": supervisor_result.workflow_type,
                    "task_count": supervisor_result.task_count,
                    "total_time_ms": supervisor_result.total_time_ms,
                }
                
                # Include workflow state from supervisor result (for multi-step workflows)
                if supervisor_result.metadata:
                    if supervisor_result.metadata.get("workflow_state"):
                        message_metadata["workflow_state"] = supervisor_result.metadata["workflow_state"]
                    if supervisor_result.metadata.get("workflow_name"):
                        message_metadata["workflow_name"] = supervisor_result.metadata["workflow_name"]
                
                assistant_message = ChatMessage.create_assistant_message(
                    conversation_id=conversation_id,
                    content=supervisor_result.content,
                    intent="SUPERVISOR_WORKFLOW",
                    handler="authenticated_supervisor",
                    is_restricted_action=False,
                    language=request_body.language,
                    metadata=message_metadata,
                    created_at=assistant_timestamp,
                )
                await message_repository.save(assistant_message)
                
                # Build response
                routing = {
                    "intent": "SUPERVISOR_WORKFLOW",
                    "confidence": 1.0,
                    "handler": "authenticated_supervisor",
                    "language": request_body.language,
                    "user_type": user.user_type.value,
                    "agents_used": supervisor_result.agents_used,
                }
                
                rate_limit_status = {
                    "user_type": user.user_type.value,
                    "remaining_hourly": rate_result.remaining_hourly,
                    "remaining_daily": rate_result.remaining_daily,
                }
                
                enrichment = {
                    "agent_squad": True,
                    "workflow_type": supervisor_result.workflow_type,
                    "task_count": supervisor_result.task_count,
                    "agents_used": supervisor_result.agents_used,
                    "agent_timings": supervisor_result.agent_timings,
                    "sources": supervisor_result.sources,
                    "total_time_ms": supervisor_result.total_time_ms,
                }
                
                # Extract execute_data from supervisor result (workflow agents like swap_workflow)
                execute_action_data = None
                if supervisor_result.execute_data:
                    try:
                        execute_action_data = ExecuteActionData(**supervisor_result.execute_data)
                    except Exception as ed_err:
                        logger.warning(f"Failed to parse execute_data: {ed_err}")
                
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
                        "sources": supervisor_result.sources,  # Match guest endpoint structure
                    },
                    routing=routing,
                    enrichment=enrichment,
                    registration_required=None,  # Authenticated users don't need registration
                    rate_limit_status=rate_limit_status,
                    execute=execute_action_data,  # Execute data from workflow agents (swap, lending, etc.)
                )
                
            except Exception as e:
                import traceback
                logger.warning(
                    f"Authenticated Supervisor failed, falling back to legacy flow: {e}",
                    extra={
                        "conversation_id": str(conversation_id),
                        "error": str(e),
                        "traceback": traceback.format_exc(),
                    },
                )
                # Print full traceback to console for debugging
                print(f"[SUPERVISOR ERROR] {e}")
                traceback.print_exc()
                # Fall through to legacy flow below
        
        # ============================================================
        # LEGACY FLOW (Keyword-based Intent Detection)
        # Used for: Guests, or when Supervisor fails/unavailable
        # ============================================================
        
        # Detect intent with context
        intent_detector = IntentDetectorV2()
        intent_result = intent_detector.detect(
            message=request_body.content,
            language=request_body.language,
            context=context,
        )
        
        # Debug logging for intent detection
        logger.debug(
            f"Intent detected: {intent_result.intent.value} "
            f"(confidence: {intent_result.confidence}, "
            f"handler: {intent_result.handler}, "
            f"is_restricted: {intent_result.is_restricted}) "
            f"for message: '{request_body.content[:100]}'"
        )

        # ✨ MULTI-STEP FLOW CANCELLATION DETECTION ✨
        # Detect if user is asking an unrelated question during a multi-step flow
        # If detected, automatically cancel the flow and process the new question
        from app.application.chat.services.flow_cancellation_detector import FlowCancellationDetector

        # Check if there's a pending multi-step flow
        if context.pending_intent:
            # Map intent enum to string for comparison
            current_intent_str = intent_result.intent.value.lower()

            # Detect topic change using hybrid keyword + intent detection
            detector = FlowCancellationDetector()
            should_cancel, reason = detector.detect_topic_change(
                content=request_body.content,
                pending_action=context.pending_intent,
                current_intent=current_intent_str,
                language=request_body.language,
            )

            if should_cancel:
                # Save the cancelled flow name before clearing
                cancelled_flow = context.pending_intent

                logger.info(
                    f"🔄 Multi-step flow cancelled - topic change detected",
                    extra={
                        "user_id": user.id,
                        "conversation_id": str(conversation_id),
                        "from_flow": cancelled_flow,
                        "to_intent": current_intent_str,
                        "reason": reason,
                        "user_message": request_body.content[:100],  # Changed from "message" to avoid LogRecord conflict
                    }
                )

                # Clear all flow-related state from context
                context.pending_intent = None
                context.pending_swap_info = None
                context.pending_moonpay_swap_info = None
                context.pending_lending_info = None
                context.pending_portfolio_info = None
                context.pending_activity_info = None
                context.pending_money_market_info = None
                context.pending_buy_info = None

                # ⚠️ CRITICAL: Re-detect intent WITHOUT flow context
                # The first detection was influenced by pending_intent, so we need to
                # re-classify the message as a fresh query to get the correct intent
                intent_result = intent_detector.detect(
                    message=request_body.content,
                    language=request_body.language,
                    context=context,  # Now has cleared flow state
                )

                logger.debug(
                    f"✓ Cleared multi-step flow state - re-detected intent: {intent_result.intent.value}"
                )

                # If the cancellation was triggered by an explicit keyword (cancel, stop, etc.),
                # check for compound intent (e.g., "cancel, tell me what is bitcoin")
                if "keyword_match:" in reason and any(kw in reason for kw in ["cancel", "stop", "abort", "forget", "never mind", "cancelar", "parar"]):
                    # Extract the matched keyword from reason
                    keyword = reason.split(":")[1]

                    # Check if there's additional content after cancellation keyword
                    remaining_content = FlowCancellationDetector.extract_post_cancellation_content(
                        request_body.content,
                        keyword,
                        request_body.language,
                    )

                    if remaining_content:
                        # Compound intent detected: user wants to cancel AND ask something
                        logger.info(
                            "🔄 Compound intent detected - processing new query after cancellation",
                            extra={
                                "user_id": user.id,
                                "conversation_id": str(conversation_id),
                                "original_content": request_body.content[:100],
                                "extracted_content": remaining_content[:100],
                                "cancelled_flow": cancelled_flow,
                                "keyword": keyword,
                            }
                        )

                        # Update request content to the extracted query
                        request_body.content = remaining_content

                        # CRITICAL: Re-detect intent on the EXTRACTED content
                        # The previous intent was detected on "cancel, tell me X"
                        # We need to detect intent on just "tell me X" for correct routing
                        intent_result = intent_detector.detect(
                            message=remaining_content,
                            language=request_body.language,
                            context=context,  # Flow state already cleared
                        )

                        logger.info(
                            "🔄 Re-detected intent for compound query",
                            extra={
                                "extracted_content": remaining_content[:100],
                                "new_intent": intent_result.intent.value,
                                "confidence": intent_result.confidence,
                                "handler": intent_result.handler,
                            }
                        )

                        # Continue to normal flow processing below with corrected intent
                        # The flow state is already cleared, so this will process as a fresh query
                    else:
                        # Simple cancellation: show confirmation
                        from app.domain.chat.entities.chat_message import ChatMessage, MessageRole

                        # Create user message
                        user_timestamp = datetime.now(UTC)
                        user_message = ChatMessage.create_user_message(
                            conversation_id=conversation_id,
                            content=request_body.content,
                            language=request_body.language,
                            created_at=user_timestamp,
                        )
                        await message_repository.save(user_message)

                        # Create friendly cancellation response
                        cancellation_messages = {
                            "en": "✓ Cancelled. How else can I help you?",
                            "es": "✓ Cancelado. ¿En qué más puedo ayudarte?",
                            "pt": "✓ Cancelado. Como posso ajudá-lo?",
                            "zh": "✓ 已取消。我还能帮您什么？",
                            "fr": "✓ Annulé. Comment puis-je vous aider?",
                        }
                        cancellation_content = cancellation_messages.get(request_body.language, cancellation_messages["en"])

                        # Create assistant message
                        assistant_timestamp = user_timestamp + timedelta(milliseconds=1)
                        assistant_message = ChatMessage.create_assistant_message(
                            conversation_id=conversation_id,
                            content=cancellation_content,
                            intent=None,
                            handler="flow_cancellation",
                            is_restricted_action=False,
                            language=request_body.language,
                            metadata={"flow_cancelled": True, "cancelled_flow": cancelled_flow},
                            created_at=assistant_timestamp,
                        )
                        await message_repository.save(assistant_message)

                        # Build rate limit status for response
                        rate_limit_status = {
                            "user_type": user.user_type.value,
                            "remaining_hourly": rate_result.remaining_hourly,
                            "remaining_daily": rate_result.remaining_daily,
                        }

                        # Return early with cancellation confirmation
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
                            routing={
                                "intent": "FLOW_CANCELLATION",
                                "confidence": 1.0,
                                "handler": "flow_cancellation",
                                "language": request_body.language,
                                "user_type": user.user_type.value,
                            },
                            enrichment=None,
                            registration_required=None,
                            rate_limit_status=rate_limit_status,
                            execute=None,
                        )

        # Initialize response variables
        agent_content = ""
        enrichment = None
        registration_required = None
        pending_action = None
        execute_data = None  # Execute action data for /execute endpoint
        used_agent_gateway = False  # Flag for when AgentGateway (LLM) was used
        handler_result = {}  # Default empty handler result for metadata extraction
        workflow_metadata = None  # Workflow metadata from BuyWorkflowAgent for state persistence
        
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
                    "SEND": ChatIntent.SEND,
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
        
        elif intent_result.intent.value.startswith("MOONPAY_SWAP"):
            # MOONPAY_SWAP: Uses Privy + 0x Protocol for major tokens (ETH, BTC, SOL, etc.)
            # This MUST be checked BEFORE generic SWAP to avoid routing to wrong handler
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

        elif intent_result.intent.value.startswith("SWAP"):
            # SWAP: Uses Hyperliquid spot quotes (meme tokens only)
            # Note: Major tokens (ETH, BTC, etc.) are handled by MOONPAY_SWAP above
            try:
                # Use injected swap_handler_v2 with Hyperliquid integration
                swap_handler = swap_handler_v2
                
                # Check for continuation metadata
                continuation_step = None
                continuation_value = None
                if intent_result.metadata:
                    continuation_step = intent_result.metadata.get("step")
                    continuation_value = intent_result.metadata.get("value")
                
                # Get previous swap info from context for multi-turn flow
                previous_swap_info = context.pending_swap_info
                
                # Get user context-aware data for balance checking
                # Note: user_context is only defined for authenticated users with supervisor_command
                swap_user_context = None
                try:
                    if user_context and user_context.get("context_aware"):
                        swap_user_context = user_context.get("context_aware")
                except NameError:
                    # user_context not defined (guest user without supervisor)
                    pass
                
                # Try to load context if not already available
                if swap_user_context is None and user_context_service and not user.is_guest:
                    try:
                        swap_user_context = await user_context_service.get_context(user.id)
                    except Exception:
                        pass  # Silently ignore - balance recommendation is not critical
                
                handler_result = await swap_handler.handle(
                    message=request_body.content,
                    context=context,
                    language=request_body.language,
                    continuation_step=continuation_step,
                    continuation_value=continuation_value,
                    previous_swap_info=previous_swap_info,
                    user_context=swap_user_context,
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

            # Extract execute data if available (like Swap handler does at lines 933-937)
            execute_data = None
            execute_data_dict = handler_result.get("execute_data")
            if execute_data_dict and not pending_action:
                # Lend is complete and ready for execution
                execute_data = ExecuteActionData(**execute_data_dict)

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

            # [BUY_DEBUG] Log entry to BUY handler
            logger.info(f"[BUY_DEBUG] Entering BUY handler section")
            logger.info(f"[BUY_DEBUG] Intent: {intent_result.intent.value}")
            logger.info(f"[BUY_DEBUG] User is_guest: {user.is_guest}")
            logger.info(f"[BUY_DEBUG] User identifier: {user.identifier}")

            # For guests, use the informative handler (legacy flow)
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
                # Authenticated users: This is the LEGACY FALLBACK path
                # The primary path for authenticated users is the Supervisor (lines 688-853)
                # If we reach here, it means the supervisor failed or is unavailable
                # Use the informational handler - DO NOT use workflow agents directly
                # to avoid conflicting state management with the supervisor
                logger.warning(
                    f"[BUY_DEBUG] Authenticated user in legacy BUY path - supervisor may have failed. "
                    f"Using informational handler as fallback."
                )
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
            
            # For authenticated users with informational intents (GENERAL_CONVERSATION, PROTOCOL_SEARCH, etc.),
            # use LLMGateway directly for real LLM response instead of demo data
            llm_intents = [
                ChatIntent.GENERAL_CONVERSATION,
                ChatIntent.PROTOCOL_SEARCH,  # "what is btc?", "tell me about ethereum"
                ChatIntent.RISK_ASSESSMENT,  # Risk analysis queries
                ChatIntent.SIMILAR_PROTOCOLS,  # Protocol comparison queries
            ]
            if not user.is_guest and mapped_intent in llm_intents:
                try:
                    # Build context from conversation memory
                    context_str = conversation_memory.build_context_string(context)
                    
                    # Build messages for LLM
                    system_prompt = """You are Anvil, a specialized DeFi assistant focused EXCLUSIVELY on decentralized finance, crypto trading, and blockchain technology.

✅ ALWAYS IN SCOPE (Answer these confidently):
- Cryptocurrency basics: "What is Bitcoin?", "What is Ethereum?", "What is BTC?", "What is ETH?"
- Token information: Any questions about crypto tokens, coins, or digital assets
- DeFi protocols: Aave, Compound, Uniswap, Curve, Lido, Morpho, etc.
- Blockchain technology: How blockchains work, consensus mechanisms, smart contracts
- Trading & Markets: Price analysis, trading strategies, market trends
- Portfolio management: Asset allocation, diversification, risk management
- NFTs, DAOs, and Web3 concepts

⚠️ OUT OF SCOPE (Decline politely):
- General knowledge: weather, cooking, jokes, sports, history (non-crypto)
- Personal advice: relationships, health, legal, financial planning (non-crypto)
- If clearly NOT crypto/blockchain related, respond: "I'm Anvil, a specialized DeFi assistant. I can only help with crypto and DeFi topics. Try asking about your portfolio, token swaps, lending rates, or market analysis."

⚠️ CONTEXT ISOLATION:
- If conversation history contains previous OUT_OF_SCOPE rejections (non-crypto topics), IGNORE them completely
- Do NOT reference or connect current query to previous rejected topics
- Treat each DeFi query independently - do not mix crypto questions with previous off-topic context

Response Guidelines:
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
        user_timestamp = datetime.now(UTC)
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
        # For authenticated users using BuyWorkflowAgent, store workflow_state
        # For guests using BuyHandler, store buy_info
        if intent_result.intent.value.startswith("BUY"):
            # Check if we have workflow_metadata from BuyWorkflowAgent (authenticated users)
            if 'workflow_metadata' in locals() and workflow_metadata:
                # Store workflow state from BuyWorkflowAgent
                if workflow_metadata.get("workflow_state"):
                    metadata["workflow_state"] = workflow_metadata["workflow_state"]
                    logger.info(f"[BUY_DEBUG] Saving workflow_state to message metadata")
                if workflow_metadata.get("workflow_name"):
                    metadata["workflow_name"] = workflow_metadata["workflow_name"]
                if workflow_metadata.get("current_step"):
                    metadata["current_step"] = workflow_metadata["current_step"]
            # Fallback for BuyHandler (guests or error fallback)
            elif hasattr(handler_result, "metadata") and handler_result.metadata:
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
        
        # Normalize enrichment to always include agent_timings and sources
        # This ensures consistent response structure for frontend
        if enrichment is None:
            enrichment = {}
        
        # Ensure agent_timings is always present
        if "agent_timings" not in enrichment:
            enrichment["agent_timings"] = [{
                "agent_type": handler_name or "handler",
                "task_description": f"Handle {intent_result.intent.value} intent",
                "execution_time_ms": 0,  # Not tracked in legacy flow
                "status": "completed",
            }]
        
        # Ensure sources is always present
        if "sources" not in enrichment:
            enrichment["sources"] = []
        
        # Build agent_message with sources included (match supervisor format)
        agent_message_response = {
            "id": str(assistant_message.id),
            "role": assistant_message.role.value,
            "content": assistant_message.content,
            "created_at": assistant_message.created_at.isoformat(),
            "sources": enrichment.get("sources", []),
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
            agent_message=agent_message_response,
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
                "saved_at": datetime.now(UTC).isoformat(),
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

    # ------------------------------------------
    # Leverage Loop Execute Endpoint
    # ------------------------------------------

    class ExecuteRequest(BaseModel):
        """Request to execute a transaction step."""

        transaction_hash: str = Field(..., description="Transaction hash of completed step")
        metadata: dict[str, Any] | None = Field(None, description="Additional metadata (e.g., loop_id for leverage loops)")

    class ExecuteResponse(BaseModel):
        """Response from executing a transaction step."""

        message: str = Field(..., description="Status message")
        execute_data: dict[str, Any] | None = Field(None, description="Next step execute data (if any)")
        metadata: dict[str, Any] = Field(default_factory=dict, description="Additional metadata")

    @router.post(
        "/{conversation_id}/execute",
        response_model=ExecuteResponse,
        status_code=status.HTTP_200_OK,
        summary="Execute Transaction Step",
        description="""
        Execute an approved transaction and continue multi-step workflows.

        **Use Cases:**
        - Leverage loop continuation (multi-step supply → borrow → swap cycles)
        - Multi-signature transaction workflows
        - Batch transaction execution

        **Metadata:**
        - loop_id: UUID of leverage loop execution (for leverage loops)
        - batch_id: UUID of batch execution (for batch transactions)
        """,
    )
    @inject
    async def execute_transaction(
        conversation_id: UUID,
        request: ExecuteRequest,
        http_request: Request,
        user_service: FromDishka[UserService],
        current_user: FromDishka[CurrentUserService],
    ) -> ExecuteResponse:
        """Execute approved transaction and continue multi-step workflows."""
        import logging
        from app.application.chat.handlers.lending_handler import LendingHandler
        from app.domain.ports.morpho_gateway import MorphoGateway
        from app.domain.ports.balance_checker import IBalanceChecker
        from app.domain.ports.lending_repository import ILendingRepository
        from app.application.lending.interactors.leverage_loop_interactor import LeverageLoopInteractor

        logger = logging.getLogger(__name__)

        # Resolve user
        user = await _resolve_chat_user(
            http_request=http_request,
            user_service=user_service,
            current_user=current_user,
        )

        # Check if this is a leverage loop continuation
        if request.metadata and request.metadata.get("loop_id"):
            loop_id = UUID(request.metadata["loop_id"])
            tx_hash = request.transaction_hash

            # Get user's wallet address (from auth context or user context service)
            # For now, we'll use a placeholder - this should come from user_context_service
            wallet_address = request.metadata.get("wallet_address", "0x0")

            # Get dependencies from Dishka container
            # NOTE: This is a simplified version - in production, these should be injected via Dishka
            # For now, we'll return a placeholder response

            logger.info(
                f"Leverage loop continuation request: loop_id={loop_id}, "
                f"tx_hash={tx_hash}, user_id={user.id}"
            )

            # TODO: Inject LendingHandler and call continue_leverage_loop
            # For now, return a success response
            return ExecuteResponse(
                message="Leverage loop step completed. Ready for next step.",
                execute_data=None,  # Would contain next step's execute_data
                metadata={
                    "loop_id": str(loop_id),
                    "transaction_hash": tx_hash,
                    "status": "in_progress",
                }
            )

        # Handle other execution types here
        logger.warning(f"Unknown execution type for conversation {conversation_id}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unknown execution type. Please provide loop_id or batch_id in metadata.",
        )

    return router

