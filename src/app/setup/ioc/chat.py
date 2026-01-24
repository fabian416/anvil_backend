"""
Unified Chat Dependency Injection Provider.

Provides DI setup for unified chat components that serve both guest and
authenticated users:
- Chat repositories (chat_users, chat_conversations, chat_messages)
- Chat command handlers
- UnifiedChatHandler
- GuestCache (shared across all users)
"""

import logging
from dishka import Provider, Scope, provide

from app.application.chat.commands.get_or_create_chat_user import (
    GetOrCreateChatUserCommand,
)
from app.application.chat.commands.get_or_create_chat_conversation import (
    GetOrCreateChatConversationCommand,
)
from app.application.chat.commands.create_chat_message import (
    CreateChatMessageCommand,
)
from app.application.chat.handlers.unified_chat_handler import UnifiedChatHandler
from app.application.chat.services.user_context_service import UserContextService
from app.domain.ports.chat_repository import (
    ChatUserRepository,
    ChatConversationRepository,
    ChatMessageRepository,
)
from app.domain.chat.ports.user_context_repository import UserContextRepository
from app.domain.chat.ports.wallet_balance import WalletBalancePort
from app.infrastructure.adapters.chat_repository_sqla import (
    ChatUserRepositorySqla,
    ChatConversationRepositorySqla,
    ChatMessageRepositorySqla,
)
from app.infrastructure.adapters.user_context_repository_sqla import (
    UserContextRepositorySqla,
)
from app.infrastructure.adapters.wallet_balance_db import WalletBalanceDbAdapter
from app.infrastructure.adapters.types import MainAsyncSession
from app.infrastructure.caching.guest_cache import GuestCache
from app.infrastructure.caching.redis_cache import RedisCache
from app.infrastructure.rate_limiting.rate_limiter import RateLimiter

logger = logging.getLogger(__name__)


class ChatProvider(Provider):
    """Dependency injection provider for unified chat components."""

    # ========== Authenticated Chat Repositories ==========

    @provide(scope=Scope.REQUEST)
    def provide_chat_user_repository(
        self,
        session: MainAsyncSession,
    ) -> ChatUserRepository:
        """Provide ChatUserRepository implementation."""
        return ChatUserRepositorySqla(session)

    @provide(scope=Scope.REQUEST)
    def provide_chat_conversation_repository(
        self,
        session: MainAsyncSession,
    ) -> ChatConversationRepository:
        """Provide ChatConversationRepository implementation."""
        return ChatConversationRepositorySqla(session)

    @provide(scope=Scope.REQUEST)
    def provide_chat_message_repository(
        self,
        session: MainAsyncSession,
    ) -> ChatMessageRepository:
        """Provide ChatMessageRepository implementation."""
        return ChatMessageRepositorySqla(session)

    @provide(scope=Scope.REQUEST)
    def provide_user_context_repository(
        self,
        session: MainAsyncSession,
    ) -> UserContextRepository:
        """
        Provide UserContextRepository implementation.
        
        Used for context-aware agent responses - stores pre-computed
        user classification data (portfolio state, activity level, user type).
        """
        return UserContextRepositorySqla(session)

    @provide(scope=Scope.REQUEST)
    def provide_wallet_balance_adapter(
        self,
        session: MainAsyncSession,
    ) -> WalletBalancePort:
        """
        Provide WalletBalancePort implementation.
        
        Used for aggregating wallet balances from local DB tables
        (wallets, chain_addresses, portfolio_snapshots) to calculate
        accurate portfolio_state classification.
        """
        return WalletBalanceDbAdapter(session)

    # ========== User Context Service ==========

    @provide(scope=Scope.REQUEST)
    def provide_user_context_service(
        self,
        context_repo: UserContextRepository,
        message_repo: ChatMessageRepository,
        conversation_repo: ChatConversationRepository,
        wallet_balance_adapter: WalletBalancePort,
    ) -> UserContextService:
        """
        Provide UserContextService for context-aware agents.
        
        This service:
        1. Creates context for new users (privy-login)
        2. Updates context periodically (Celery task)
        3. Provides context for chat sessions
        
        The wallet_balance_adapter enables accurate portfolio_state
        classification based on real wallet balances.
        """
        return UserContextService(
            context_repository=context_repo,
            chat_message_repository=message_repo,
            chat_conversation_repository=conversation_repo,
            wallet_repository=None,  # Deprecated - use wallet_balance_adapter
            wallet_balance_adapter=wallet_balance_adapter,
        )

    # ========== Authenticated Chat Command Handlers ==========

    @provide(scope=Scope.REQUEST)
    def provide_get_or_create_chat_user(
        self,
        chat_user_repo: ChatUserRepository,
    ) -> GetOrCreateChatUserCommand:
        """
        Provide GetOrCreateChatUser command.

        Creates or retrieves chat user bridging to legacy users table.
        """
        return GetOrCreateChatUserCommand(chat_user_repository=chat_user_repo)

    @provide(scope=Scope.REQUEST)
    def provide_get_or_create_chat_conversation(
        self,
        chat_conversation_repo: ChatConversationRepository,
    ) -> GetOrCreateChatConversationCommand:
        """
        Provide GetOrCreateChatConversation command.

        Gets active conversation or creates new one.
        """
        return GetOrCreateChatConversationCommand(
            chat_conversation_repository=chat_conversation_repo
        )

    @provide(scope=Scope.REQUEST)
    def provide_create_chat_message(
        self,
        chat_message_repo: ChatMessageRepository,
        chat_conversation_repo: ChatConversationRepository,
    ) -> CreateChatMessageCommand:
        """
        Provide CreateChatMessage command.

        Creates message and increments conversation message count.
        """
        return CreateChatMessageCommand(
            chat_message_repository=chat_message_repo,
            chat_conversation_repository=chat_conversation_repo,
        )

    # ========== Shared Cache Infrastructure ==========

    @provide(scope=Scope.APP)
    def provide_redis_cache(self) -> RedisCache:
        """
        Provide RedisCache for guest cache system.

        Uses environment variables for configuration:
        - REDIS_URL (default: redis://localhost:6379/0)
        """
        return RedisCache()

    @provide(scope=Scope.APP)
    def provide_guest_cache(
        self,
        redis_cache: RedisCache,
    ) -> GuestCache:
        """
        Provide GuestCache for Hunter AI response caching.

        Shared across all users (guest and authenticated) to maximize cache hit rate.
        Currently at 96.1% hit rate with 5-10min TTL for Hunter AI responses.
        """
        return GuestCache(redis_cache=redis_cache)

    @provide(scope=Scope.APP)
    async def provide_rate_limiter(
        self,
        redis_cache: RedisCache,
    ) -> RateLimiter:
        """
        Provide RateLimiter for chat endpoints.

        Implements tiered rate limiting:
        - Guest: 800 messages/hour (IP-based)
        - Free: 1000 messages/hour (user ID)
        - Premium: 10000 messages/hour (user ID)
        - Enterprise: 10000 messages/hour (user ID)

        Uses Redis sliding window counter with fail-open strategy.
        """
        # Ensure Redis is connected
        if redis_cache._client is None:
            await redis_cache.connect()
        return RateLimiter(redis_client=redis_cache._client)

    # ========== Unified Chat Handler ==========

    @provide(scope=Scope.REQUEST)
    def provide_unified_chat_handler(
        self,
        # Authenticated chat command handlers
        get_or_create_chat_user: GetOrCreateChatUserCommand,
        get_or_create_chat_conversation: GetOrCreateChatConversationCommand,
        create_chat_message: CreateChatMessageCommand,
        # Shared infrastructure
        cache: GuestCache,
    ) -> UnifiedChatHandler:
        """
        Provide UnifiedChatHandler with all dependencies.

        This handler serves both guest and authenticated users through
        context abstraction. Guest handlers are imported dynamically
        from the guest provider to maintain modularity.

        Args:
            get_or_create_chat_user: Authenticated user command
            get_or_create_chat_conversation: Authenticated conversation command
            create_chat_message: Authenticated message command
            cache: Shared GuestCache for Hunter AI responses

        Returns:
            Configured UnifiedChatHandler instance

        Note:
            Guest handlers (get_or_create_guest_user, etc.) and hunter_service
            are currently NOT injected via Dishka. They will be added when
            we fully migrate the guest system to use the unified handler.

            For now, hunter_service must be injected directly in the endpoint
            function to avoid Request context dependency issues.
        """
        logger.info("Creating UnifiedChatHandler (hunter_service will be set by endpoint)")

        return UnifiedChatHandler(
            # Guest handlers (not yet migrated to unified handler)
            get_or_create_guest_user=None,
            get_or_create_guest_conversation=None,
            create_guest_message=None,
            # Authenticated handlers
            get_or_create_chat_user=get_or_create_chat_user,
            get_or_create_chat_conversation=get_or_create_chat_conversation,
            create_chat_message=create_chat_message,
            # Shared infrastructure
            cache=cache,
            hunter_service=None,  # Will be injected in endpoint via setter
        )


def chat_provider() -> ChatProvider:
    """Factory function for Chat provider."""
    return ChatProvider()
