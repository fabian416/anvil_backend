"""Universal chat router for guest and authenticated users.

This module provides a single unified endpoint that serves both guest and
authenticated users through context detection and polymorphic handling.
"""
import logging
from typing import Optional, Annotated
from dishka.integrations.fastapi import FromDishka, inject
from fastapi import APIRouter, Depends, Header, Request
from pydantic import BaseModel, Field

from app.domain.chat.value_objects import (
    GuestContext,
    AuthenticatedContext,
    UserContext,
)
from app.application.chat.handlers.unified_chat_handler import UnifiedChatHandler
from app.domain.entities.user import User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["Universal Chat"])


# ============================================================================
# Request/Response Models
# ============================================================================


class ChatRequest(BaseModel):
    """Universal chat request for guest and authenticated users."""

    content: str = Field(
        ...,
        min_length=1,
        max_length=2000,
        description="User message content",
        examples=["What's the sentiment for BTC?", "Show me ETH trading signals"],
    )
    language: str = Field(
        default="en",
        pattern="^(en|es|pt|zh)$",
        description="Language code for response",
        examples=["en", "es", "pt", "zh"],
    )

    class Config:
        json_schema_extra = {
            "examples": [
                {
                    "content": "What's the sentiment for BTC?",
                    "language": "en",
                },
                {
                    "content": "Muéstrame las señales de trading para ETH",
                    "language": "es",
                },
            ]
        }


class ChatResponse(BaseModel):
    """Universal chat response."""

    message_id: str = Field(..., description="Unique message identifier")
    content: str = Field(..., description="Hunter AI response content")
    intent: str = Field(..., description="Detected intent")
    enrichment: Optional[dict] = Field(
        None, description="Hunter AI enrichment data"
    )
    requires_registration: bool = Field(
        False, description="Whether feature requires authentication"
    )
    user_type: str = Field(
        ..., description="User type (guest or authenticated)"
    )
    features_available: dict = Field(
        ..., description="Available features for user"
    )

    class Config:
        json_schema_extra = {
            "examples": [
                {
                    "message_id": "123e4567-e89b-12d3-a456-426614174000",
                    "content": "BTC sentiment is bullish...",
                    "intent": "hunter_sentiment",
                    "enrichment": {
                        "token": "BTC",
                        "price": 45000.0,
                        "sentiment_score": 0.75,
                    },
                    "requires_registration": False,
                    "user_type": "guest",
                    "features_available": {
                        "basic": {
                            "sentiment": True,
                            "trading_signals": True,
                            "price_prediction": True,
                        },
                        "premium": {
                            "patterns": False,
                            "portfolio": False,
                            "risk_signals": False,
                        },
                    },
                }
            ]
        }


# ============================================================================
# Dependencies
# ============================================================================


async def get_optional_user(
    request: Request,
    authorization: Optional[str] = Header(None),
) -> Optional[User]:
    """Get authenticated user if JWT token provided.

    Returns None if no token (guest user), allowing the same endpoint to serve
    both guest and authenticated users seamlessly.

    Args:
        request: FastAPI request object
        authorization: Optional Authorization header with Bearer token

    Returns:
        User object if authenticated, None if guest

    Note:
        Does NOT raise exceptions for invalid tokens - returns None instead,
        treating invalid tokens as guest users. This provides graceful
        degradation instead of authentication failures.
    """
    if not authorization:
        logger.debug("No authorization header - treating as guest user")
        return None

    if not authorization.startswith("Bearer "):
        logger.debug("Invalid authorization header format - treating as guest")
        return None

    try:
        token = authorization.replace("Bearer ", "")

        # TODO: Implement JWT verification
        # For now, this is a placeholder that will be implemented in Day 2-3
        # when we integrate with the existing authentication system
        #
        # Expected implementation:
        # from app.infrastructure.auth.jwt_handler import verify_jwt_token
        # user = await verify_jwt_token(token)
        # return user

        logger.warning(
            "JWT verification not yet implemented - treating as guest user"
        )
        return None

    except Exception as e:
        logger.warning(
            f"Error verifying JWT token: {e} - treating as guest user"
        )
        return None


async def get_client_ip(request: Request) -> str:
    """Extract client IP address from request.

    Handles X-Forwarded-For header for proxy/load balancer scenarios.

    Args:
        request: FastAPI request object

    Returns:
        Client IP address as string
    """
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        # Take first IP if multiple (client IP is first in chain)
        return forwarded.split(",")[0].strip()

    return request.client.host if request.client else "unknown"




# ============================================================================
# Endpoints
# ============================================================================


@router.post(
    "/chat",
    response_model=ChatResponse,
    summary="Universal chat endpoint",
    description=(
        "Universal chat endpoint that serves both guest and authenticated users. "
        "Automatically detects user type from JWT token presence and routes to "
        "appropriate storage and feature set. Guest users are identified by IP "
        "address and have basic features. Authenticated users have premium features "
        "based on subscription tier."
    ),
    responses={
        200: {
            "description": "Successful chat response",
            "content": {
                "application/json": {
                    "example": {
                        "message_id": "123e4567-e89b-12d3-a456-426614174000",
                        "content": "BTC sentiment is currently bullish...",
                        "intent": "hunter_sentiment",
                        "enrichment": {
                            "token": "BTC",
                            "price": 45000.0,
                            "sentiment_score": 0.75,
                        },
                        "requires_registration": False,
                        "user_type": "authenticated",
                        "features_available": {
                            "basic": {
                                "sentiment": True,
                                "trading_signals": True,
                                "price_prediction": True,
                            },
                            "premium": {
                                "patterns": True,
                                "portfolio": True,
                                "risk_signals": True,
                            },
                        },
                    }
                }
            },
        },
        429: {
            "description": "Rate limit exceeded",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Rate limit exceeded. Guest users: 20 messages/hour. Please register for higher limits."
                    }
                }
            },
        },
        503: {
            "description": "Hunter AI service unavailable",
            "content": {
                "application/json": {
                    "example": {"detail": "Hunter AI service temporarily unavailable"}
                }
            },
        },
    },
)
@inject
async def universal_chat(
    request_data: ChatRequest,
    request: Request,
    user: Annotated[Optional[User], Depends(get_optional_user)],
    ip_address: Annotated[str, Depends(get_client_ip)],
    handler: FromDishka[UnifiedChatHandler],
) -> ChatResponse:
    """Universal chat endpoint for guest and authenticated users.

    This single endpoint serves both user types through context abstraction:
    - Guest users (no JWT): Basic features, IP-based tracking, 20 msg/hour limit
    - Authenticated users (JWT): Premium features, persistent storage, 1000+ msg/hour

    Args:
        request_data: Chat request with content and language
        request: FastAPI request object (for logging)
        user: Optional authenticated user from JWT token
        ip_address: Client IP address for guest identification
        handler: Unified chat handler with injected dependencies

    Returns:
        ChatResponse with Hunter AI response and user context

    Flow:
        1. Detect user type from JWT presence
        2. Create appropriate context (Guest or Authenticated)
        3. Route to unified handler
        4. Return response with user-specific features and data

    Examples:
        Guest request (no JWT):
            POST /api/v1/chat
            {"content": "What's BTC sentiment?", "language": "en"}
            → Basic features, IP tracking, 20/hour limit

        Authenticated request (with JWT):
            POST /api/v1/chat
            Authorization: Bearer eyJhbGc...
            {"content": "What's BTC sentiment?", "language": "en"}
            → Premium features, persistent storage, 1000+/hour limit
    """
    logger.info(
        "Universal chat request",
        extra={
            "is_authenticated": user is not None,
            "user_id": str(user.id) if user else None,
            "ip_address": ip_address,
            "language": request_data.language,
            "content_length": len(request_data.content),
        },
    )

    # Create context based on authentication status
    context: UserContext
    if user:
        # Authenticated user - create authenticated context
        # Handle UserId value object (extract integer value)
        user_id_int = user.id.value if hasattr(user.id, 'value') else int(user.id)

        context = AuthenticatedContext(
            user_id=user_id_int,
            email=user.email,
            subscription_tier=getattr(user, "subscription_tier", "free"),
        )

        logger.debug(
            f"Created authenticated context",
            extra={
                "user_id": user_id_int,
                "email": user.email,
                "subscription_tier": context.subscription_tier,
            },
        )
    else:
        # Guest user - create guest context
        context = GuestContext(ip_address=ip_address)

        logger.debug(
            f"Created guest context",
            extra={"ip_address": ip_address},
        )

    # Handle message with unified handler
    response_data = await handler.handle_message(
        content=request_data.content,
        language=request_data.language,
        context=context,
    )

    logger.info(
        "Chat response generated",
        extra={
            "message_id": response_data["message_id"],
            "intent": response_data["intent"],
            "user_type": response_data["user_type"],
            "requires_registration": response_data["requires_registration"],
        },
    )

    return ChatResponse(**response_data)


# ============================================================================
# Backward Compatibility Aliases
# ============================================================================


@router.post(
    "/guest/chat",
    response_model=ChatResponse,
    summary="Guest chat endpoint (backward compatibility)",
    description=(
        "Legacy guest chat endpoint for backward compatibility. "
        "New integrations should use /api/v1/chat instead. "
        "This endpoint forces guest context regardless of JWT presence."
    ),
    deprecated=True,
)
@inject
async def guest_chat_legacy(
    request_data: ChatRequest,
    request: Request,
    ip_address: Annotated[str, Depends(get_client_ip)],
    handler: FromDishka[UnifiedChatHandler],
) -> ChatResponse:
    """Legacy guest chat endpoint for backward compatibility.

    This endpoint maintains backward compatibility with existing guest chat
    integrations. It always creates a guest context regardless of JWT presence.

    New integrations should use the universal /api/v1/chat endpoint instead.

    Args:
        request_data: Chat request with content and language
        request: FastAPI request object
        ip_address: Client IP address
        handler: Unified chat handler

    Returns:
        ChatResponse with guest user context

    Note:
        This endpoint is deprecated and will be removed in a future version.
        Please migrate to /api/v1/chat.
    """
    logger.warning(
        "Legacy guest chat endpoint called - recommend migration to /api/v1/chat",
        extra={"ip_address": ip_address},
    )

    # Always create guest context (ignore JWT if present)
    context = GuestContext(ip_address=ip_address)

    # Handle message
    response_data = await handler.handle_message(
        content=request_data.content,
        language=request_data.language,
        context=context,
    )

    return ChatResponse(**response_data)
