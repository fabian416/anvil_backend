"""Unified chat handler for guest and authenticated users.

This module provides a single handler that serves both guest and authenticated
users through context abstraction, maximizing code reuse while supporting
different features and configurations.
"""
import logging
from typing import Any, Optional
from uuid import UUID, uuid4

from app.domain.chat.value_objects import (
    UserContext,
    GuestContext,
    AuthenticatedContext,
    FeatureFlags,
)
from app.application.chat.commands.get_or_create_chat_user import (
    GetOrCreateChatUserCommand,
)
from app.application.chat.commands.get_or_create_chat_conversation import (
    GetOrCreateChatConversationCommand,
)
from app.application.chat.commands.create_chat_message import (
    CreateChatMessageCommand,
)
from app.infrastructure.caching.guest_cache import GuestCache

logger = logging.getLogger(__name__)


class UnifiedChatHandler:
    """
    Universal chat handler for guest and authenticated users.

    Architecture:
    - Single handler serves both user types through context abstraction
    - Context determines behavior (storage, features, rate limits)
    - Feature flags control premium access
    - Same Hunter AI core for all users
    - Shared cache maximizes hit rate

    Example:
        # Guest user
        context = GuestContext(ip_address="1.2.3.4")
        response = await handler.handle_message(content, language, context)

        # Authenticated user
        context = AuthenticatedContext(user_id=uuid, email="user@example.com")
        response = await handler.handle_message(content, language, context)
    """

    def __init__(
        self,
        # Command handlers for guest storage (optional - for backward compatibility)
        get_or_create_guest_user: Any = None,
        get_or_create_guest_conversation: Any = None,
        create_guest_message: Any = None,

        # Command handlers for authenticated storage
        get_or_create_chat_user: Optional[GetOrCreateChatUserCommand] = None,
        get_or_create_chat_conversation: Optional[GetOrCreateChatConversationCommand] = None,
        create_chat_message: Optional[CreateChatMessageCommand] = None,

        # Shared infrastructure
        cache: Any = None,  # GuestCache
        hunter_service: Any = None,  # GuestHandlerService for Hunter AI processing
    ):
        """Initialize unified chat handler.

        Args:
            get_or_create_guest_user: Guest user command handler (optional)
            get_or_create_guest_conversation: Guest conversation command (optional)
            create_guest_message: Guest message command (optional)
            get_or_create_chat_user: Authenticated user command handler
            get_or_create_chat_conversation: Authenticated conversation command
            create_chat_message: Authenticated message command
            cache: Redis cache for Hunter AI responses
            hunter_service: Hunter AI processing service
        """
        # Guest storage handlers (optional)
        self._get_or_create_guest_user = get_or_create_guest_user
        self._get_or_create_guest_conversation = get_or_create_guest_conversation
        self._create_guest_message = create_guest_message

        # Authenticated storage handlers
        self._get_or_create_chat_user = get_or_create_chat_user
        self._get_or_create_chat_conversation = get_or_create_chat_conversation
        self._create_chat_message = create_chat_message

        # Shared infrastructure
        self._cache = cache
        self._hunter_service = hunter_service

    async def handle_message(
        self,
        content: str,
        language: str,
        context: UserContext,
    ) -> dict[str, Any]:
        """
        Handle chat message for any user type.

        Flow:
        1. Validate context and get feature flags
        2. Get or create user/conversation (context-specific storage)
        3. Classify intent from message content
        4. Check if intent is allowed for user's feature flags
        5. Check cache (shared across all users)
        6. Process with Hunter AI if not cached
        7. Save message (context-specific storage)
        8. Return response

        Args:
            content: User message content
            language: Language code (en, es, pt, zh)
            context: User context (Guest or Authenticated)

        Returns:
            Dictionary with response data:
            - content: Response message
            - intent: Detected intent
            - enrichment: Hunter AI enrichment data
            - requires_registration: Whether feature requires auth
            - user_type: "guest" or "authenticated"
            - features_available: Available feature flags

        Raises:
            ValueError: If context type is not supported
        """
        logger.info(
            f"Unified chat message",
            extra={
                "user_id": context.get_user_id(),
                "is_authenticated": context.is_authenticated(),
                "language": language,
                "content_length": len(content),
            },
        )

        # 1. Get feature flags for this context
        features = FeatureFlags.from_context(context)

        # 2. Get or create conversation (storage depends on context)
        conversation_id = await self._get_or_create_conversation(
            context, language
        )

        # 3. Classify intent from content
        intent = await self._classify_intent(content)

        logger.debug(
            f"Intent classified: {intent}",
            extra={"user_id": context.get_user_id(), "intent": intent},
        )

        # 4. Check if intent is allowed for user's features
        if not features.is_intent_allowed(intent):
            logger.info(
                f"Intent not allowed for user",
                extra={
                    "user_id": context.get_user_id(),
                    "intent": intent,
                    "is_authenticated": context.is_authenticated(),
                },
            )

            # Return upgrade prompt
            return {
                "message_id": str(uuid4()),
                "content": self._get_upgrade_message(intent),
                "intent": intent,
                "enrichment": None,
                "requires_registration": True,
                "user_type": "guest" if isinstance(context, GuestContext) else "authenticated",
                "features_available": features.to_dict(),
            }

        # 5. Extract token from content
        token = self._extract_token(content) or "BTC"

        # 6. Check cache (shared across all users)
        cached = await self._cache.get_hunter_response(
            intent, token, language
        )

        if cached:
            logger.debug(
                f"Cache HIT",
                extra={
                    "user_id": context.get_user_id(),
                    "intent": intent,
                    "token": token,
                },
            )

            # Save message from cache
            message_id = await self._save_message(
                context=context,
                conversation_id=conversation_id,
                role="user",
                content=content,
                intent=intent,
                enrichment=cached.get("enrichment"),
            )

            return {
                "message_id": message_id,
                "content": cached.get("content"),
                "intent": intent,
                "enrichment": cached.get("enrichment"),
                "requires_registration": False,
                "user_type": "guest" if isinstance(context, GuestContext) else "authenticated",
                "features_available": features.to_dict(),
            }

        # 7. Process with Hunter AI (cache miss)
        logger.debug(
            f"Cache MISS - processing with Hunter AI",
            extra={
                "user_id": context.get_user_id(),
                "intent": intent,
                "token": token,
            },
        )

        response = await self._hunter_service.process_intent(
            intent=intent,
            token=token,
            language=language,
            content=content,
            is_authenticated=context.is_authenticated(),
        )

        # 8. Cache response (shared)
        await self._cache.set_hunter_response(
            intent, token, language, response
        )

        # 9. Save message
        message_id = await self._save_message(
            context=context,
            conversation_id=conversation_id,
            role="user",
            content=content,
            intent=intent,
            enrichment=response.get("enrichment"),
        )

        return {
            "message_id": message_id,
            "content": response.get("content"),
            "intent": intent,
            "enrichment": response.get("enrichment"),
            "requires_registration": False,
            "user_type": "guest" if isinstance(context, GuestContext) else "authenticated",
            "features_available": features.to_dict(),
        }

    async def _get_or_create_conversation(
        self, context: UserContext, language: str
    ) -> UUID:
        """Get or create conversation based on context.

        Args:
            context: User context
            language: Language code

        Returns:
            Conversation UUID

        Raises:
            ValueError: If context type not supported
        """
        if isinstance(context, GuestContext):
            # Guest user - use guest storage
            user = await self._get_or_create_guest_user.execute(
                context.ip_address
            )

            conversation = await self._get_or_create_guest_conversation.execute(
                user.id, language
            )

            return conversation.id

        elif isinstance(context, AuthenticatedContext):
            # Authenticated user - use chat storage
            if not self._get_or_create_chat_user or not self._get_or_create_chat_conversation:
                raise NotImplementedError(
                    "Authenticated chat handlers not configured. "
                    "Ensure get_or_create_chat_user and get_or_create_chat_conversation "
                    "are provided during initialization."
                )

            # Get or create chat user (bridge to legacy users table)
            chat_user = await self._get_or_create_chat_user.execute(
                user_id=context.user_id,  # Legacy INTEGER user_id
                email=context.email,
                subscription_tier=context.subscription_tier,
            )

            # Get or create conversation
            conversation = await self._get_or_create_chat_conversation.execute(
                chat_user.id_, language
            )

            return conversation.id_

        else:
            raise ValueError(f"Unknown context type: {type(context)}")

    async def _save_message(
        self,
        context: UserContext,
        conversation_id: UUID,
        role: str,
        content: str,
        intent: Optional[str] = None,
        enrichment: Optional[dict] = None,
    ) -> str:
        """Save message to appropriate storage.

        Args:
            context: User context
            conversation_id: Conversation UUID
            role: Message role (user, assistant)
            content: Message content
            intent: Detected intent
            enrichment: Hunter AI enrichment data

        Returns:
            Message ID (string)

        Raises:
            ValueError: If context type not supported
        """
        if isinstance(context, GuestContext):
            # Guest user - use guest storage
            message = await self._create_guest_message.execute(
                conversation_id=conversation_id,
                role=role,
                content=content,
                intent=intent,
                enrichment=enrichment,
            )

            return str(message.id)

        elif isinstance(context, AuthenticatedContext):
            # Authenticated user - use chat storage
            if not self._create_chat_message:
                raise NotImplementedError(
                    "Authenticated chat message handler not configured. "
                    "Ensure create_chat_message is provided during initialization."
                )

            message = await self._create_chat_message.execute(
                conversation_id=conversation_id,
                role=role,
                content=content,
                intent=intent,
                enrichment=enrichment,
            )

            return str(message.id_)

        else:
            raise ValueError(f"Unknown context type: {type(context)}")

    def _classify_intent(self, content: str) -> str:
        """Classify intent from message content.

        This is a simplified version. The actual implementation should use
        the existing intent classification logic from GuestHandlerService.

        Args:
            content: User message content

        Returns:
            Intent name (hunter_sentiment, hunter_trading_signals, etc.)
        """
        content_lower = content.lower()

        # Pattern matching for intent classification
        # TODO: Use more sophisticated classification from GuestHandlerService

        if any(word in content_lower for word in ["sentiment", "feel", "bullish", "bearish"]):
            return "hunter_sentiment"

        if any(word in content_lower for word in ["signal", "buy", "sell", "trade"]):
            return "hunter_trading_signals"

        if any(word in content_lower for word in ["price", "predict", "forecast", "where"]):
            return "hunter_price_prediction"

        if any(word in content_lower for word in ["pattern", "chart", "technical"]):
            return "hunter_patterns"

        if any(word in content_lower for word in ["portfolio", "optimize", "allocation"]):
            return "hunter_portfolio"

        if any(word in content_lower for word in ["risk", "danger", "warning"]):
            return "hunter_risk_signals"

        # Default to sentiment
        return "hunter_sentiment"

    def _extract_token(self, content: str) -> Optional[str]:
        """Extract cryptocurrency token from content.

        Args:
            content: User message content

        Returns:
            Token symbol (BTC, ETH, etc.) or None
        """
        content_upper = content.upper()

        # Common token symbols
        tokens = ["BTC", "ETH", "SOL", "USDT", "BNB", "USDC", "ADA", "DOT", "MATIC", "LINK"]

        for token in tokens:
            if token in content_upper:
                return token

        return None

    def _get_upgrade_message(self, intent: str) -> str:
        """Get upgrade message for locked features.

        Args:
            intent: Intent that requires upgrade

        Returns:
            User-friendly upgrade message
        """
        feature_names = {
            "hunter_patterns": "Pattern Detection",
            "hunter_portfolio": "Portfolio Optimization",
            "hunter_risk_signals": "Risk Analysis",
        }

        feature_name = feature_names.get(intent, "This feature")

        return (
            f"🔒 **{feature_name}** is a premium feature.\n\n"
            f"Sign up for free to unlock:\n"
            f"✨ Pattern Detection\n"
            f"✨ Portfolio Optimization\n"
            f"✨ Risk Analysis\n"
            f"✨ Unlimited messages\n"
            f"✨ Permanent conversation history\n\n"
            f"[Sign Up Free](https://anvil.fi/signup)"
        )
