"""Universal chat router for guest and authenticated users.

This module provides a single unified endpoint that serves both guest and
authenticated users through context detection and polymorphic handling.
"""
import logging
from datetime import datetime, timezone
from typing import Optional, Annotated
from dishka.integrations.fastapi import FromDishka, inject
from fastapi import APIRouter, Depends, Header, Request, HTTPException, status
from pydantic import BaseModel, Field

from app.domain.chat.value_objects import (
    GuestContext,
    AuthenticatedContext,
    UserContext,
)
from app.application.chat.handlers.unified_chat_handler import UnifiedChatHandler
from app.domain.entities.user import User
from app.infrastructure.rate_limiting.rate_limiter import (
    RateLimiter,
    UserTier,
)

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Universal Chat"])


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
        from sqlalchemy import text
        from app.infrastructure.persistence_sqla.db_uow import get_async_session
        from app.presentation.http.auth.access_token_processor_jwt import (
            JwtAccessTokenProcessor,
        )
        from app.setup.config import get_config

        token = authorization.replace("Bearer ", "")

        # Get JWT secret from config
        config = get_config()
        jwt_secret = config.auth.jwt_secret

        # Decode and validate JWT token
        jwt_processor = JwtAccessTokenProcessor(secret=jwt_secret, algorithm="HS256")
        auth_session_id = jwt_processor.decode_auth_session_id(token)

        if not auth_session_id:
            logger.debug("Invalid JWT token - treating as guest user")
            return None

        # Get database session from Dishka container (stored in request state)
        async_session = request.state.dishka_container.get(get_async_session)

        # Query database to validate session and get user
        query = text("""
            SELECT u.id, u.email, u.first_name, u.last_name, u.role,
                   u.is_active, u.is_verified
            FROM auth_sessions s
            JOIN users u ON u.id = s.user_id
            WHERE s.id = :session_id
              AND s.expiration > NOW()
              AND u.is_active = TRUE
        """)

        async with async_session() as session:
            result = await session.execute(query, {"session_id": auth_session_id})
            row = result.fetchone()

            if not row:
                logger.debug(
                    "Session not found or expired - treating as guest user",
                    extra={"session_id": auth_session_id}
                )
                return None

            # Create User entity from database row
            from app.domain.value_objects.user_id import UserId
            from app.domain.value_objects.email import Email

            user = User(
                id=UserId(row[0]),  # user.id
                email=Email(row[1]),  # user.email
                first_name=row[2],
                last_name=row[3],
                role=row[4],
                is_active=row[5],
                is_verified=row[6],
            )

            logger.info(
                "User authenticated successfully",
                extra={
                    "user_id": row[0],
                    "email": row[1],
                    "session_id": auth_session_id,
                }
            )

            return user

    except Exception as e:
        logger.warning(
            f"Error verifying JWT token: {e} - treating as guest user",
            exc_info=True
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
                        "detail": "Rate limit exceeded. Guest users: 800 messages/hour. Please register for higher limits."
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
    rate_limiter: FromDishka[RateLimiter],
) -> ChatResponse:
    """Universal chat endpoint for guest and authenticated users.

    This single endpoint serves both user types through context abstraction:
    - Guest users (no JWT): Basic features, IP-based tracking, 800 msg/hour limit
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
            → Basic features, IP tracking, 800/hour limit

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

    # Check rate limit
    is_authenticated = user is not None
    identifier = str(user.id.value) if user else ip_address
    user_tier = UserTier.FREE if user else UserTier.GUEST  # TODO: Get actual tier from user

    rate_limit_result = await rate_limiter.check_rate_limit(
        identifier=identifier,
        user_tier=user_tier,
        is_authenticated=is_authenticated,
    )

    # Add rate limit headers to response
    # Note: FastAPI doesn't easily allow setting headers on HTTPException,
    # so we'll add them to the normal response later

    if not rate_limit_result.allowed:
        # Rate limit exceeded - return 429 with detailed message
        user_type_str = "authenticated users" if is_authenticated else "guest users"
        tier_limit = rate_limit_result.limit
        reset_time = rate_limit_result.reset_at.strftime("%Y-%m-%d %H:%M:%S UTC")

        error_message = (
            f"Rate limit exceeded. {user_type_str.capitalize()}: "
            f"{tier_limit} messages/hour. "
            f"Current usage: {rate_limit_result.current}/{tier_limit}. "
            f"Limit resets at {reset_time}."
        )

        if not is_authenticated:
            error_message += " Please register for higher limits (1,000+ messages/hour)."

        logger.warning(
            "Rate limit exceeded",
            extra={
                "identifier": identifier,
                "is_authenticated": is_authenticated,
                "tier": user_tier.value,
                "current": rate_limit_result.current,
                "limit": tier_limit,
                "reset_at": reset_time,
            },
        )

        # Calculate retry-after in seconds
        now = datetime.now(timezone.utc)
        retry_after_seconds = max(0, int((rate_limit_result.reset_at - now).total_seconds()))

        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=error_message,
            headers={
                "X-RateLimit-Limit": str(rate_limit_result.limit),
                "X-RateLimit-Remaining": str(rate_limit_result.remaining),
                "X-RateLimit-Reset": str(int(rate_limit_result.reset_at.timestamp())),
                "Retry-After": str(retry_after_seconds),
            },
        )

    logger.info(
        "Rate limit check passed",
        extra={
            "identifier": identifier,
            "tier": user_tier.value,
            "current": rate_limit_result.current,
            "limit": rate_limit_result.limit,
            "remaining": rate_limit_result.remaining,
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


# REMOVED: This endpoint was overriding the proper guest chat endpoint
# The proper guest chat endpoint is in guest/router.py which uses SendGuestMessageCommand
# with proper supervisor routing and registration_required logic.
#
# @router.post(
#     "/guest/chat",
#     response_model=ChatResponse,
#     summary="Guest chat endpoint (backward compatibility)",
#     description=(
#         "Legacy guest chat endpoint for backward compatibility. "
#         "New integrations should use /api/v1/chat instead. "
#         "This endpoint forces guest context regardless of JWT presence."
#     ),
#     deprecated=True,
# )
# @inject
# async def guest_chat_legacy(
#     request_data: ChatRequest,
#     request: Request,
#     ip_address: Annotated[str, Depends(get_client_ip)],
#     handler: FromDishka[UnifiedChatHandler],
# ) -> ChatResponse:
#     """Legacy guest chat endpoint for backward compatibility.
#
#     This endpoint maintains backward compatibility with existing guest chat
#     integrations. It always creates a guest context regardless of JWT presence.
#
#     New integrations should use the universal /api/v1/chat endpoint instead.
#
#     Args:
#         request_data: Chat request with content and language
#         request: FastAPI request object
#         ip_address: Client IP address
#         handler: Unified chat handler
#
#     Returns:
#         ChatResponse with guest user context
#
#     Note:
#         This endpoint is deprecated and will be removed in a future version.
#         Please migrate to /api/v1/chat.
#     """
#     logger.warning(
#         "Legacy guest chat endpoint called - recommend migration to /api/v1/chat",
#         extra={"ip_address": ip_address},
#     )
#
#     # Always create guest context (ignore JWT if present)
#     context = GuestContext(ip_address=ip_address)
#
#     # Handle message
#     response_data = await handler.handle_message(
#         content=request_data.content,
#         language=request_data.language,
#         context=context,
#     )
#
#     return ChatResponse(**response_data)
