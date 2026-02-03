"""
Unified Chat Dependency Injection Provider.

Provides DI setup for unified chat components that serve both guest and
authenticated users:
- Chat repositories (chat_users, chat_conversations, chat_messages)
- GuestCache (shared across all users)
"""

import logging
from dishka import Provider, Scope, provide
from app.application.chat.services.user_context_service import UserContextService
from app.application.chat.services.response_template_service import ResponseTemplateService
from app.domain.ports.chat_repository import (
    ChatUserRepository,
    ChatConversationRepository,
    ChatMessageRepository,
)
from app.domain.chat.ports.user_context_repository import UserContextRepository
from app.domain.chat.ports.wallet_balance import WalletBalancePort
from app.domain.chat.ports.analytics_repository import AnalyticsRepository
from app.infrastructure.adapters.chat_repository_sqla import (
    ChatUserRepositorySqla,
    ChatConversationRepositorySqla,
    ChatMessageRepositorySqla,
)
from app.infrastructure.adapters.user_context_repository_sqla import (
    UserContextRepositorySqla,
)
from app.infrastructure.adapters.wallet_balance_db import WalletBalanceDbAdapter
from app.infrastructure.adapters.analytics_repository_sqla import (
    AnalyticsRepositorySqla,
)
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

    @provide(scope=Scope.REQUEST)
    def provide_analytics_repository(
        self,
        session: MainAsyncSession,
    ) -> AnalyticsRepository:
        """
        Provide AnalyticsRepository implementation.
        
        Used for persisting and querying user context analytics snapshots.
        Supports daily/weekly/monthly snapshots, trends, and cohort analysis.
        """
        return AnalyticsRepositorySqla(session)

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

    @provide(scope=Scope.REQUEST)
    def provide_optional_user_context_service(
        self,
        user_context_service: UserContextService,
    ) -> UserContextService | None:
        """
        Provide Optional[UserContextService] for backwards compatibility.
        
        Some commands (like PrivyLogin) declare UserContextService as optional
        to maintain backwards compatibility. This provider bridges the gap
        between the required service and the optional type hint.
        """
        return user_context_service

    @provide(scope=Scope.REQUEST)
    def provide_optional_chat_user_repository(
        self,
        chat_user_repo: ChatUserRepository,
    ) -> ChatUserRepository | None:
        """
        Provide Optional[ChatUserRepository] for backwards compatibility.
        
        Some commands (like PrivyLogin) declare ChatUserRepository as optional
        to maintain backwards compatibility.
        """
        return chat_user_repo

    @provide(scope=Scope.APP)
    def provide_response_template_service(self) -> ResponseTemplateService:
        """
        Provide ResponseTemplateService for context-aware agents.
        
        This service loads and serves pre-defined response templates
        based on user classification (portfolio state, activity level, 
        user type). Templates are loaded once at app startup and cached
        in memory.
        
        Benefits:
        - Reduces LLM calls for common scenarios
        - Ensures consistent, localized messaging
        - Supports multi-language (en, es, pt, zh)
        - Provides workflow blocking logic
        """
        return ResponseTemplateService()

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


def chat_provider() -> ChatProvider:
    """Factory function for Chat provider."""
    return ChatProvider()
