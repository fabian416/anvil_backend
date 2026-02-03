"""
Chat Phase 2 Dependency Injection Configuration.

Provides DI setup for all Phase 2 components:
- 15 Repository adapters (PostgreSQL + Redis)
- External service providers (LLM, Embedding, Translation, Vector DB)
- WebSocket handlers (Chat, Analytics, Template Execution)
- Session management and caching
"""

import os
from typing import Optional, Any

from dishka import Provider, Scope, provide, decorate
from redis.asyncio import Redis, ConnectionPool

# Infrastructure Types
from app.infrastructure.adapters.types import MainAsyncSession

# Domain Ports - Repositories
from app.domain.chat.ports.analytics_repository import AnalyticsRepository
from app.domain.ports.agent_orchestration_repository import AgentOrchestrationRepository
from app.domain.ports.audit_log_repository import AuditLogRepository
from app.domain.chat.ports.export_repository import ExportRepository
from app.domain.ports.export_generator import ExportGenerator
from app.domain.chat.ports.template_repository import TemplateRepository
from app.domain.chat.ports.template_execution_repository import (
    TemplateExecutionRepository,
)
from app.domain.preferences.ports.user_preferences_repository import (
    UserPreferencesRepository,
)

# Domain Ports - External Services
from app.domain.ports.chat_llm_provider import ChatLLMProvider
from app.domain.ports.translation_adapter import TranslationAdapter
from app.domain.ports.vector.vector_repository import VectorRepository
from app.domain.ports.ai.llm_gateway import LLMGateway

# Domain Ports - Infrastructure
from app.domain.ports.cache_adapter import CacheAdapter
from app.domain.ports.intent_cache_adapter import IntentCacheAdapter
from app.domain.ports.notification_adapter import NotificationAdapter
from app.domain.ports.offline_queue_adapter import OfflineQueueAdapter
from app.domain.ports.session_store import SessionStore

# Infrastructure Adapters - Repositories
from app.infrastructure.adapters.chat.analytics_repository_adapter import (
    AnalyticsRepositoryAdapter,
)
from app.infrastructure.adapters.chat.agent_orchestration_repository_adapter import (
    AgentOrchestrationRepositoryAdapter,
)
from app.infrastructure.adapters.chat.audit_log_repository_adapter import (
    AuditLogRepositoryAdapter,
)
from app.infrastructure.adapters.chat.export_repository_adapter import (
    ExportRepositoryAdapter,
)
from app.infrastructure.adapters.chat.export_generator_adapter import (
    ExportGeneratorAdapter,
)
from app.infrastructure.adapters.chat.template_repository_adapter import (
    TemplateRepositoryAdapter,
)
from app.infrastructure.adapters.chat.template_execution_repository_adapter import (
    TemplateExecutionRepositoryAdapter,
)
from app.infrastructure.adapters.chat.preferences_repository_adapter import (
    UserPreferencesRepositoryAdapter,
)

# Infrastructure Adapters - External Services
# OpenAI removed - using only Vertex AI and DeepInfra
# from app.infrastructure.adapters.ai.openai_chat_adapter import OpenAIChatAdapter
from app.infrastructure.adapters.ai.anthropic_chat_adapter import AnthropicChatAdapter

# Application Services
from app.application.chat.services.intent_detector import IntentDetectorService
from app.application.chat.commands.send_message_unified import UnifiedChatOrchestrator
from app.application.chat.commands.send_message import SendMessage
from app.application.chat.commands.execute_action import ExecuteActionCommand
from app.application.chat.graph_search_handler import ChatGraphSearchHandler
from app.application.chat.risk_insights_handler import ChatRiskInsightsHandler
from app.application.agent_squad.commands.send_agent_squad_message import (
    SendAgentSquadMessage,
)
from app.application.agent_squad.commands.execute_supervisor_workflow import (
    ExecuteSupervisorWorkflow,
)
from app.application.common.services.current_user import CurrentUserService

# Demo mode service (same handlers as /guest/chat)
from app.application.guest.handlers.guest_handler_service import GuestHandlerService
from app.setup.config.agent_squad import AgentSquadSettings

# Chat V2 Services (Unified Chat System)
from app.application.chat.services.user_service import UserService
from app.application.chat.services.rate_limit_service import RateLimitService
from app.application.chat.services.conversation_service import ConversationService
from app.application.chat.services.conversation_memory import ConversationMemory
from app.application.common.services.current_user import CurrentUserService

# Chat V2 Repositories (Unified Chat System)
from app.infrastructure.adapters.chat_unified_repository_sqla import (
    ChatUserRepositorySqla,
    ChatConversationRepositorySqla,
    ChatMessageRepositorySqla,
    RateLimitRepositorySqla,
)

# Intent Detection Port & Adapters (Hexagonal Architecture)
from app.domain.ports.chat.intent_detection_port import IntentDetectionPort
from app.infrastructure.adapters.chat.keyword_intent_detection_adapter import (
    KeywordIntentDetectionAdapter,
)
from app.infrastructure.adapters.chat.llm_intent_detection_adapter import (
    LLMIntentDetectionAdapter,
)
from app.infrastructure.adapters.chat.hybrid_intent_detection_adapter import (
    HybridIntentDetectionAdapter,
)

# Optional: DeepL translation adapter (requires deepl package)
try:
    from app.infrastructure.adapters.external.deepl_translation_adapter import (
        DeepLTranslationAdapter,
    )

    DEEPL_AVAILABLE = True
except ImportError:
    DEEPL_AVAILABLE = False

# Infrastructure Adapters - Redis
from app.infrastructure.adapters.chat.redis_cache_adapter import RedisCacheAdapter
from app.infrastructure.adapters.chat.redis_intent_cache_adapter import (
    RedisIntentCacheAdapter,
)
from app.infrastructure.adapters.chat.redis_session_store_adapter import (
    RedisSessionStoreAdapter,
)
from app.infrastructure.adapters.chat.redis_offline_queue_adapter import (
    RedisOfflineQueueAdapter,
)
from app.infrastructure.adapters.chat.redis_translation_cache_adapter import (
    RedisTranslationCacheAdapter,
)
from app.infrastructure.adapters.chat.notification_adapter import (
    NotificationAdapter as NotificationAdapterImpl,
)

# WebSocket Handlers
from app.presentation.http.websocket.connection_manager import ConnectionManager

# Optional: WebSocket handlers (may not be fully implemented)
try:
    from app.presentation.http.websocket.chat_websocket import ChatWebSocketHandler

    CHAT_WEBSOCKET_AVAILABLE = True
except (ImportError, AttributeError):
    CHAT_WEBSOCKET_AVAILABLE = False

try:
    from app.presentation.http.websocket.analytics_handler import (
        AnalyticsWebSocketHandler,
    )

    ANALYTICS_WEBSOCKET_AVAILABLE = True
except (ImportError, AttributeError):
    ANALYTICS_WEBSOCKET_AVAILABLE = False

# Import JwtAccessTokenProcessor for type hints (always available)
from app.presentation.http.auth.access_token_processor_jwt import (
    JwtAccessTokenProcessor,
)

try:
    from app.presentation.http.websocket.template_handler import (
        TemplateExecutionWebSocketHandler,
    )

    TEMPLATE_WEBSOCKET_AVAILABLE = True
except (ImportError, AttributeError):
    TEMPLATE_WEBSOCKET_AVAILABLE = False
    TemplateExecutionWebSocketHandler = None  # type: ignore

# Application Services
from app.application.chat.services.advanced_intent_detector import (
    AdvancedIntentDetector,
)
from app.application.chat.services.user_analytics_service import (
    UserChatAnalyticsService,
)
from app.application.chat.services.admin_analytics_service import (
    AdminChatAnalyticsService,
)
from app.domain.chat.ports.conversation_repository import ConversationRepository

# DeFi Shortcut Handlers
from app.application.chat.handlers.lending_handler import LendingHandler
from app.application.lending.interactors.leverage_loop_interactor import (
    LeverageLoopInteractor,
)
from app.domain.ports.lending_repository import ILendingRepository
from app.application.chat.handlers.portfolio_handler import PortfolioHandler
from app.application.chat.handlers.swap_handler import SwapHandler
from app.application.chat.handlers.swap_handler_v2 import SwapHandlerV2
from app.application.chat.handlers.activity_handler import ActivityHandler
from app.infrastructure.adapters.external.hyperliquid_client import HyperliquidClient
from app.application.chat.handlers.receive_handler import ReceiveHandler
from app.application.chat.handlers.buy_handler import BuyHandler
from app.application.chat.handlers.money_market_handler import MoneyMarketHandler
from app.application.chat.handlers.moonpay_swap_handler import MoonPaySwapHandler
from app.domain.ports.morpho_gateway import MorphoGateway
from app.domain.ports.aave_gateway import AaveGateway
from app.domain.ports.compound_gateway import CompoundGateway
from app.domain.ports.money_market.money_market_cache_gateway import (
    MoneyMarketCacheGateway,
)
from app.domain.ports.money_market.money_market_comparison_gateway import (
    MoneyMarketComparisonGateway,
)
from app.domain.ports.balance_checker import IBalanceChecker
from app.infrastructure.adapters.external.compound_client import CompoundClient
from app.infrastructure.adapters.external.compound_adapter import CompoundAdapter
from app.infrastructure.adapters.balance.portfolio_balance_checker import (
    PortfolioBalanceChecker,
)
from app.infrastructure.adapters.external.oneinch_client import OneInchClient
from app.infrastructure.adapters.external.lifi_client import LiFiClient
from app.infrastructure.adapters.external.moonpay_swap_client import MoonPaySwapClient
from app.application.portfolio.portfolio_service import PortfolioService
from app.domain.transactions.ports.transaction.transaction_repository import (
    TransactionRepository,
)
from app.domain.ports.wallet.wallet_repository import WalletRepository
from app.domain.ports.wallet.embedded_wallet_provider import EmbeddedWalletProviderPort
from app.setup.config.privy import PrivySettings


class ChatPhase2Provider(Provider):
    """
    Provider for Chat Phase 2 components.

    Configures:
    - Repository adapters for PostgreSQL and Redis
    - External service providers (LLM, Embedding, Translation)
    - WebSocket handlers and session management
    - Caching and offline queue infrastructure
    """

    scope = Scope.REQUEST

    # ========================================
    # Redis Clients (APP-scoped)
    # ========================================

    @provide(scope=Scope.APP)
    async def provide_redis_chat_client(self) -> Redis:
        """
        Provide Redis client for chat operations.

        Uses connection pooling for optimal performance.
        Separate from other Redis clients to avoid resource contention.
        """
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/1")

        pool = ConnectionPool.from_url(
            redis_url,
            max_connections=50,  # Higher pool for chat operations
            decode_responses=True,  # Auto decode for text operations
            socket_timeout=5,
            socket_connect_timeout=5,
        )

        return Redis(connection_pool=pool)

    @provide(scope=Scope.APP)
    async def provide_redis_cache_client(self) -> Redis:
        """
        Provide Redis client for caching operations.

        Dedicated client with binary support for vector caching.
        """
        redis_url = os.getenv(
            "REDIS_CACHE_URL", os.getenv("REDIS_URL", "redis://localhost:6379/2")
        )

        pool = ConnectionPool.from_url(
            redis_url,
            max_connections=30,
            decode_responses=False,  # Keep binary for flexibility
            socket_timeout=3,
            socket_connect_timeout=3,
        )

        return Redis(connection_pool=pool)

    # ========================================
    # Repository Adapters (REQUEST-scoped)
    # ========================================

    @provide
    def provide_analytics_repository(
        self,
        session: MainAsyncSession,
    ) -> AnalyticsRepository:
        """Provide conversation analytics repository."""
        return AnalyticsRepositoryAdapter(session=session)

    @provide
    def provide_agent_orchestration_repository(
        self,
        session: MainAsyncSession,
    ) -> AgentOrchestrationRepository:
        """Provide agent orchestration repository."""
        return AgentOrchestrationRepositoryAdapter(session=session)

    @provide
    def provide_audit_log_repository(
        self,
        session: MainAsyncSession,
    ) -> AuditLogRepository:
        """Provide audit log repository."""
        return AuditLogRepositoryAdapter(session=session)

    @provide
    def provide_export_repository(
        self,
        session: MainAsyncSession,
    ) -> ExportRepository:
        """Provide conversation export repository."""
        return ExportRepositoryAdapter(session=session)

    @provide
    def provide_export_generator(self) -> ExportGenerator:
        """Provide export file generator."""
        export_dir = os.getenv("EXPORT_DIR", "/tmp/anvil_exports")
        return ExportGeneratorAdapter(export_directory=export_dir)

    @provide
    def provide_template_repository(
        self,
        session: MainAsyncSession,
    ) -> TemplateRepository:
        """Provide conversation template repository."""
        return TemplateRepositoryAdapter(session=session)

    @provide
    def provide_template_execution_repository(
        self,
        session: MainAsyncSession,
    ) -> TemplateExecutionRepository:
        """Provide template execution repository."""
        return TemplateExecutionRepositoryAdapter(session=session)

    @provide
    def provide_user_preferences_repository(
        self,
        session: MainAsyncSession,
    ) -> UserPreferencesRepository:
        """Provide user chat preferences repository."""
        return UserPreferencesRepositoryAdapter(session=session)

    # ========================================
    # Redis Infrastructure (REQUEST-scoped)
    # ========================================

    @provide
    def provide_cache_adapter(
        self,
        redis_cache_client: Redis,
    ) -> CacheAdapter:
        """Provide general-purpose cache adapter."""
        return RedisCacheAdapter(
            redis_client=redis_cache_client,
            key_prefix="chat",
            default_ttl=3600,  # 1 hour default
        )

    @provide
    def provide_intent_cache_adapter(
        self,
        redis_cache_client: Redis,
    ) -> IntentCacheAdapter:
        """Provide intent classification cache."""
        return RedisIntentCacheAdapter(
            redis_client=redis_cache_client,
            key_prefix="intent",
            ttl=86400,  # 24 hours
        )

    @provide
    def provide_session_store(
        self,
        redis_chat_client: Redis,
    ) -> SessionStore:
        """Provide WebSocket session store."""
        return RedisSessionStoreAdapter(
            redis_client=redis_chat_client,
            key_prefix="ws_session",
            pool_size=50,
        )

    @provide
    def provide_offline_queue_adapter(
        self,
        redis_chat_client: Redis,
    ) -> OfflineQueueAdapter:
        """Provide offline message queue."""
        return RedisOfflineQueueAdapter(
            redis_client=redis_chat_client,
            queue_prefix="offline_msg",
            max_queue_size=100,
        )

    @provide
    def provide_translation_cache_adapter(
        self,
        redis_cache_client: Redis,
    ) -> CacheAdapter:
        """Provide translation cache adapter."""
        return RedisTranslationCacheAdapter(
            redis_client=redis_cache_client,
            key_prefix="translation",
            ttl=604800,  # 7 days
        )

    @provide
    def provide_notification_adapter(
        self,
        redis_chat_client: Redis,
    ) -> NotificationAdapter:
        """Provide WebSocket notification adapter."""
        return NotificationAdapterImpl(
            redis_client=redis_chat_client,
            channel_prefix="chat_notify",
        )

    # ========================================
    # External LLM Providers (APP-scoped)
    # ========================================

    # OpenAI removed - using only Vertex AI and DeepInfra
    # @provide(scope=Scope.APP)
    # def provide_openai_chat_provider(self) -> ChatLLMProvider:
    #     """OpenAI chat provider - REMOVED"""
    #     pass

    @provide(scope=Scope.APP)
    def provide_anthropic_chat_provider(self) -> Optional[ChatLLMProvider]:
        """
        Provide Anthropic Claude chat LLM provider.

        Optional fallback provider configured with:
        - Claude 3 Opus or Sonnet
        - Streaming support
        - Retry policies

        Returns None if API key not configured.
        """
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            return None

        model = os.getenv("ANTHROPIC_CHAT_MODEL", "claude-3-opus-20240229")

        return AnthropicChatAdapter(
            api_key=api_key,
            model=model,
            temperature=0.7,
            max_tokens=2048,
            timeout=60.0,
            max_retries=3,
            retry_delay=1.0,
        )

    # ========================================
    # Translation Services (APP-scoped)
    # ========================================

    @provide(scope=Scope.APP)
    def provide_deepl_translation_adapter(self) -> Optional[TranslationAdapter]:
        """
        Provide DeepL translation service.

        Configured with:
        - High-quality neural translation
        - Support for 30+ languages
        - Formality and context awareness

        Returns None if API key not configured or deepl package not installed.
        """
        if not DEEPL_AVAILABLE:
            return None

        api_key = os.getenv("DEEPL_API_KEY")
        if not api_key:
            return None

        is_free = os.getenv("DEEPL_FREE_TIER", "false").lower() == "true"

        return DeepLTranslationAdapter(
            api_key=api_key,
            use_free_api=is_free,
            timeout=15.0,
            max_retries=3,
        )

    # ========================================
    # Vector Database (REQUEST-scoped)
    # ========================================

    @provide(scope=Scope.REQUEST)
    def provide_vector_repository(
        self,
        session: MainAsyncSession,
    ) -> VectorRepository:
        """
        Provide vector repository for similarity search.

        Uses PostgreSQL with array operations for vector storage.
        """
        from app.infrastructure.persistence_sqla.repositories.vector_repository_sqla import (
            VectorRepositorySqla,
        )

        return VectorRepositorySqla(session=session)

    # ========================================
    # WebSocket Handlers (APP-scoped)
    # ========================================

    @provide(scope=Scope.APP)
    def provide_connection_manager(self) -> ConnectionManager:
        """
        Provide WebSocket connection manager.

        Manages active WebSocket connections with:
        - Connection pooling
        - Message broadcasting
        - Room-based grouping
        - Automatic cleanup
        """
        return ConnectionManager()

    @provide(scope=Scope.APP)
    def provide_chat_websocket_handler(
        self,
        connection_manager: ConnectionManager,
        session_store: SessionStore,
    ) -> Optional[Any]:
        """Provide chat WebSocket handler (optional)."""
        if not CHAT_WEBSOCKET_AVAILABLE:
            return None
        return ChatWebSocketHandler(
            connection_manager=connection_manager,
            session_store=session_store,
        )

    @provide(scope=Scope.REQUEST)
    def provide_analytics_websocket_handler(
        self,
        connection_manager: ConnectionManager,
        analytics_repository: AnalyticsRepository,
    ) -> Optional[Any]:
        """Provide analytics WebSocket handler (REQUEST-scoped to access repository)."""
        if not ANALYTICS_WEBSOCKET_AVAILABLE:
            return None
        return AnalyticsWebSocketHandler(
            connection_manager=connection_manager,
            analytics_repository=analytics_repository,
        )

    @provide(scope=Scope.REQUEST)
    def provide_template_execution_websocket_handler(
        self,
        connection_manager: ConnectionManager,
        template_execution_repository: TemplateExecutionRepository,
        jwt_processor: JwtAccessTokenProcessor,
    ) -> Optional[Any]:
        """Provide template execution WebSocket handler (REQUEST-scoped to access repository)."""
        if not TEMPLATE_WEBSOCKET_AVAILABLE:
            return None
        return TemplateExecutionWebSocketHandler(
            execution_repository=template_execution_repository,
            jwt_processor=jwt_processor,
            connection_manager=connection_manager,
        )

    # ========================================
    # Analytics Services (REQUEST-scoped)
    # ========================================

    @provide
    def provide_user_chat_analytics_service(
        self,
        analytics_repository: AnalyticsRepository,
    ) -> UserChatAnalyticsService:
        """
        Provide user-level chat analytics service.

        Generates personalized analytics for individual users.
        """
        return UserChatAnalyticsService(
            analytics_repository=analytics_repository,
        )

    @provide
    def provide_admin_chat_analytics_service(
        self,
        analytics_repository: AnalyticsRepository,
    ) -> AdminChatAnalyticsService:
        """
        Provide admin-level chat analytics service.

        Aggregates analytics across all users for admin dashboards.
        """
        return AdminChatAnalyticsService(
            analytics_repository=analytics_repository,
        )

    # ========================================
    # Intent Detection (REQUEST-scoped)
    # ========================================

    @provide
    def provide_advanced_intent_detector(
        self,
        message_repository: ChatMessageRepositorySqla,
    ) -> AdvancedIntentDetector:
        """
        Provide advanced intent detection service.

        Analyzes user input to detect intent and provide real-time suggestions.
        Uses unified chat message repository for similar conversation search.
        """
        return AdvancedIntentDetector(
            message_repository=message_repository,
        )

    # ========================================
    # Unified Chat Routing (Phase 8)
    # ========================================

    # ========================================
    # Intent Detection Port & Adapters (Hexagonal Architecture)
    # ========================================

    @provide
    def provide_keyword_intent_adapter(self) -> KeywordIntentDetectionAdapter:
        """
        Provide keyword-based intent detection adapter.

        Fast, deterministic, no LLM costs. Used as fallback.
        """
        return KeywordIntentDetectionAdapter()

    @provide
    def provide_llm_intent_adapter(
        self,
        llm_gateway: LLMGateway,
    ) -> LLMIntentDetectionAdapter:
        """
        Provide LLM-based intent detection adapter.

        High accuracy, uses LLM gateway for classification.
        """
        return LLMIntentDetectionAdapter(llm_gateway=llm_gateway)

    @provide
    def provide_intent_detection_port(
        self,
        llm_adapter: LLMIntentDetectionAdapter,
        keyword_adapter: KeywordIntentDetectionAdapter,
    ) -> IntentDetectionPort:
        """
        Provide hybrid intent detection (production).

        Uses LLM for accuracy with keyword fallback for reliability.
        """
        return HybridIntentDetectionAdapter(
            llm_adapter=llm_adapter,
            keyword_adapter=keyword_adapter,
            min_llm_confidence=0.7,
        )

    @provide
    def provide_intent_detector_service(
        self,
        intent_port: IntentDetectionPort,
    ) -> IntentDetectorService:
        """
        Provide intent detector for unified routing.

        Now uses IntentDetectionPort for classification:
        - In production: HybridIntentDetectionAdapter (LLM + keyword fallback)
        - In tests: KeywordIntentDetectionAdapter (fast, deterministic)

        The service delegates to the port, maintaining clean architecture.
        """
        return IntentDetectorService(intent_port=intent_port)

    # ========================================
    # DeFi Shortcut Handlers (Morpho, Swap, etc.)
    # ========================================

    @provide
    def provide_balance_checker(
        self,
        portfolio_service: PortfolioService,
    ) -> IBalanceChecker:
        """
        Provide balance checker for validating wallet balances.

        Uses PortfolioService for real-time RPC balance checks.
        Critical for preventing transactions with insufficient balance.
        """
        return PortfolioBalanceChecker(portfolio_service=portfolio_service)

    @provide(scope=Scope.REQUEST)
    def provide_lending_handler(
        self,
        morpho_gateway: MorphoGateway,
        balance_checker: IBalanceChecker,
        leverage_loop_interactor: LeverageLoopInteractor,
        lending_repository: ILendingRepository,
    ) -> LendingHandler:
        """
        Provide lending handler for Morpho vault operations.

        Uses real data from Morpho GraphQL API:
        - Ethereum mainnet vaults
        - Base L2 vaults (USDC, ETH, etc.)
        - APY comparison
        - Whitelisted vault recommendations

        Includes:
        - Balance validation via BalanceChecker to prevent insufficient balance transactions
        - Leverage loop operations via LeverageLoopInteractor (provided by LendingProvider)
        - Position persistence via ILendingRepository (provided by LendingProvider)

        Per CEO spec: Morpho only for lending (top 3 vaults by APY).
        Leverage loops and position tracking are optional features enabled when
        LendingProvider is registered in provider_registry.
        """
        return LendingHandler(
            morpho_gateway=morpho_gateway,
            balance_checker=balance_checker,
            leverage_loop_interactor=leverage_loop_interactor,
            lending_repository=lending_repository,
        )

    @provide
    def provide_portfolio_handler(
        self,
        portfolio_service: PortfolioService,
    ) -> PortfolioHandler:
        """
        Provide portfolio handler for balance and portfolio queries.

        Uses real on-chain data via RPC:
        - Native token balances
        - ERC-20 token balances
        - USD pricing from DeFiLlama
        """
        return PortfolioHandler(portfolio_service=portfolio_service)

    @provide
    def provide_swap_handler(self) -> SwapHandler:
        """
        Provide swap handler for token exchange quotes.

        Per CEO spec: Hyperliquid + LiFi + 1inch for swaps.

        Currently returns handler with no clients configured.
        To enable real quotes, configure API keys in settings and
        inject OneInchClient, LiFiClient, HyperliquidClient.
        """
        # TODO: Inject clients when API keys are configured
        # - oneinch_client: OneInchClient for single-chain swaps
        # - lifi_client: LiFiClient for cross-chain bridges
        # - hyperliquid_client: HyperliquidClient for perpetuals
        return SwapHandler(
            oneinch_client=None,
            lifi_client=None,
            hyperliquid_client=None,
        )

    @provide
    def provide_hyperliquid_client(self) -> HyperliquidClient | None:
        """
        Provide HyperliquidClient for spot swap quotes.

        Returns:
            HyperliquidClient configured for mainnet, or None if disabled.
        """
        import logging

        logger = logging.getLogger(__name__)

        try:
            client = HyperliquidClient(testnet=False)
            logger.info("✅ HyperliquidClient enabled for SwapHandlerV2")
            return client
        except Exception as e:
            logger.warning(f"⚠️ Failed to create HyperliquidClient: {e}")
            return None

    @provide
    def provide_swap_handler_v2(
        self,
        hyperliquid_client: HyperliquidClient | None,
    ) -> SwapHandlerV2:
        """
        Provide SwapHandlerV2 with Hyperliquid spot (ONLY provider).

        Features:
        - Real-time Hyperliquid spot quotes
        - Zero gas fees
        - High-speed execution (20,000+ TPS)
        - 0.02% trading fee

        Supported tokens (16):
        ETH, USDC, USDT, DAI, WBTC, WETH, BTC, SOL,
        MATIC, ARB, OP, LINK, UNI, AAVE, CRV, MKR
        """
        import logging

        logger = logging.getLogger(__name__)

        if hyperliquid_client:
            logger.info(
                "🔵 SwapHandlerV2 initialized with Hyperliquid spot (ONLY provider)"
            )
        else:
            logger.error(
                "❌ SwapHandlerV2: Hyperliquid client not available - swaps will fail"
            )

        return SwapHandlerV2(hyperliquid_client=hyperliquid_client)

    @provide
    def provide_activity_handler(
        self,
        transaction_repository: TransactionRepository,
    ) -> ActivityHandler:
        """
        Provide activity handler for transaction history.

        Uses database records for transaction history.
        """
        return ActivityHandler(transaction_repository=transaction_repository)

    @provide
    def provide_receive_handler(
        self,
        wallet_repository: WalletRepository,
        current_user_service: CurrentUserService,
        wallet_provider: EmbeddedWalletProviderPort,
        privy_settings: PrivySettings,
    ) -> ReceiveHandler:
        """
        Provide receive handler for wallet address display.

        Uses wallet repository to fetch user's primary address.
        """
        return ReceiveHandler(
            wallet_repository=wallet_repository,
            current_user_service=current_user_service,
            wallet_provider=wallet_provider,
            privy_settings=privy_settings,
        )

    @provide(scope=Scope.REQUEST)
    def provide_buy_handler(
        self,
        wallet_repository: WalletRepository,
        current_user_service: CurrentUserService,
        wallet_provider: EmbeddedWalletProviderPort,
        privy_settings: PrivySettings,
    ) -> BuyHandler:
        """
        Provide buy handler for crypto on-ramp.

        Uses wallet repository to fetch user's primary address.
        Actual on-ramp is handled by Privy SDK on frontend.
        """
        return BuyHandler(
            wallet_repository=wallet_repository,
            current_user_service=current_user_service,
            wallet_provider=wallet_provider,
            privy_settings=privy_settings,
        )

    @provide(scope=Scope.APP)
    def provide_moonpay_swap_client(self) -> MoonPaySwapClient:
        """
        Provide MoonPay Swap API client.

        Configured with:
        - MoonPay publishable API key
        - Sandbox or production environment
        - 12 supported swap pairs (BTC, ETH, SOL, USDC)

        Used for crypto-to-crypto swap quotes only.
        Actual swap execution is handled by Privy SDK on frontend.
        """
        import os

        api_key = os.getenv("MOONPAY_API_KEY", "pk_test_zJtsRVDetOru63X98XExqNoRHaFDco")
        environment = os.getenv("MOONPAY_ENVIRONMENT", "sandbox")

        return MoonPaySwapClient(
            api_key=api_key,
            environment=environment,
        )

    @provide(scope=Scope.REQUEST)
    def provide_moonpay_swap_handler(
        self,
        swap_client: MoonPaySwapClient,
    ) -> MoonPaySwapHandler:
        """
        Provide MoonPay swap handler for chat integration.

        Supports:
        - 12 swap pairs (BTC, ETH, SOL, USDC bidirectional)
        - Real-time swap quotes with pricing
        - Multi-language support (en, es, pt, zh, fr)
        - Frontend execution via Privy modal

        Uses MoonPaySwapClient for API calls.
        """
        return MoonPaySwapHandler(swap_client=swap_client)

    @provide
    def provide_compound_client(self) -> CompoundClient:
        """Provide Compound V3 API client."""
        return CompoundClient(timeout=30)

    @provide
    def provide_compound_gateway(
        self,
        compound_client: CompoundClient,
    ) -> CompoundGateway:
        """Provide Compound V3 gateway adapter."""
        return CompoundAdapter(client=compound_client)

    @provide(scope=Scope.REQUEST)
    def provide_money_market_handler(
        self,
        aave_gateway: AaveGateway,
        compound_gateway: CompoundGateway,
        cache_gateway: MoneyMarketCacheGateway,
        comparison_gateway: MoneyMarketComparisonGateway,
    ) -> MoneyMarketHandler:
        """
        Provide money market handler for rate comparison.

        Per CEO spec: Aave + Compound only for money market.
        (Morpho is handled by LendingHandler for vault deposits)

        Uses real data from:
        - Aave: AaveGateway for market rates
        - Compound: CompoundGateway for market rates
        - Cache: MoneyMarketCacheGateway for 60s TTL rate caching (provided by MoneyMarketProvider)
        - Comparison: MoneyMarketComparisonGateway for analytics logging (provided by MoneyMarketProvider)

        Cache and comparison gateways are provided by MoneyMarketProvider (registered in provider_registry).
        Both are required dependencies - MoneyMarketProvider must be registered for this to work.
        """
        return MoneyMarketHandler(
            aave_gateway=aave_gateway,
            compound_gateway=compound_gateway,
            cache_gateway=cache_gateway,
            comparison_gateway=comparison_gateway,
        )

    @provide
    def provide_unified_chat_orchestrator(
        self,
        conversation_repository: ConversationRepository,
        intent_detector_service: IntentDetectorService,
        graphrag_search_handler: ChatGraphSearchHandler,
        graphrag_risk_handler: ChatRiskInsightsHandler,
        agent_squad_message_command: SendAgentSquadMessage,
        supervisor_workflow_command: ExecuteSupervisorWorkflow,
        regular_chat_command: SendMessage,
        lending_handler: LendingHandler,
        portfolio_handler: PortfolioHandler,
        swap_handler: SwapHandler,
        activity_handler: ActivityHandler,
        receive_handler: ReceiveHandler,
        buy_handler: BuyHandler,
        money_market_handler: MoneyMarketHandler,
        moonpay_swap_handler: MoonPaySwapHandler,
        morpho_gateway: MorphoGateway,
        wallet_repository: WalletRepository,
        agent_squad_settings: AgentSquadSettings,
    ) -> UnifiedChatOrchestrator:
        """
        Provide unified chat orchestrator.

        Routes messages to appropriate handlers based on detected intent:
        - GraphRAG (search, risk, similar)
        - Hunter AI (sentiment, predictions, patterns)
        - ULTRA (arbitrage, flash loans, MEV)
        - DeFi Shortcuts (lending, swap, balance, portfolio)
        - Agent Squad (specialist tasks, complex workflows)

        DEMO MODE (use_demo_mode=True in config):
        - Uses GuestHandlerService instead of real LLM calls
        - Provides same responses as /guest/chat endpoint
        - Useful for demos and testing without API costs
        """
        # Create GuestHandlerService for demo mode
        guest_handler = GuestHandlerService(
            lending_handler=lending_handler,
            swap_handler=swap_handler,
            money_market_handler=money_market_handler,
            moonpay_swap_handler=moonpay_swap_handler,
            morpho_gateway=morpho_gateway,
        )

        return UnifiedChatOrchestrator(
            conversation_repo=conversation_repository,
            intent_detector=intent_detector_service,
            graphrag_search=graphrag_search_handler,
            graphrag_risk=graphrag_risk_handler,
            agent_squad=agent_squad_message_command,
            supervisor=supervisor_workflow_command,
            regular_chat=regular_chat_command,
            lending_handler=lending_handler,
            portfolio_handler=portfolio_handler,
            swap_handler=swap_handler,
            activity_handler=activity_handler,
            receive_handler=receive_handler,
            buy_handler=buy_handler,
            money_market_handler=money_market_handler,
            moonpay_swap_handler=moonpay_swap_handler,
            wallet_repository=wallet_repository,
            # Demo mode dependencies
            agent_squad_settings=agent_squad_settings,
            guest_handler_service=guest_handler,
        )

    @provide(scope=Scope.REQUEST)
    def provide_execute_action_command(
        self,
        conversation_repository: ConversationRepository,
        wallet_repository: WalletRepository,
        moonpay_swap_client: MoonPaySwapClient,
    ) -> ExecuteActionCommand:
        """
        Provide execute action command for transaction execution.

        Supports:
        - Token swaps: 1inch (same-chain) + LiFi (cross-chain) + MoonPay (crypto-to-crypto)
        - Deposits (Morpho, Aave)
        - Withdrawals (Morpho, Aave)
        - Transfers
        - Approvals
        - Cross-chain bridges

        Requirements:
        - ONEINCH_API_KEY: Required for same-chain swaps
        - LiFi: No API key required (always available for cross-chain)
        - MOONPAY_API_KEY: Required for MoonPay swaps (crypto-to-crypto)

        NO SIMULATION: If clients cannot be created, swaps will fail with clear error.
        """
        import os
        import logging

        logger = logging.getLogger(__name__)

        # Create LiFi client (no API key required) - for cross-chain
        lifi_client = LiFiClient()
        logger.info("LiFiClient created for ExecuteActionCommand (cross-chain swaps)")

        # Create 1inch client - REQUIRED for same-chain swaps
        oneinch_api_key = os.getenv("ONEINCH_API_KEY", "").strip()
        if not oneinch_api_key:
            logger.warning(
                "ONEINCH_API_KEY not configured. Same-chain swaps will fail. "
                "Get your API key from https://portal.1inch.dev/"
            )
            oneinch_client = None
        else:
            oneinch_client = OneInchClient(
                api_key=oneinch_api_key,
                chain="base",  # Default chain, request will specify actual chain
            )
            logger.info(
                "OneInchClient created for ExecuteActionCommand (same-chain swaps)"
            )

        logger.info(
            "MoonPaySwapClient injected into ExecuteActionCommand (crypto-to-crypto swaps)"
        )

        return ExecuteActionCommand(
            conversation_repo=conversation_repository,
            wallet_repository=wallet_repository,
            oneinch_client=oneinch_client,
            lifi_client=lifi_client,
            moonpay_swap_client=moonpay_swap_client,
            morpho_gateway=None,
            aave_gateway=None,
        )

    # ========================================
    # Chat V2 Repositories (Unified Chat System)
    # ========================================

    @provide(scope=Scope.REQUEST)
    def provide_chat_user_repository(
        self,
        session: MainAsyncSession,
    ) -> ChatUserRepositorySqla:
        """Provide chat user repository for unified chat system."""
        return ChatUserRepositorySqla(session)

    @provide(scope=Scope.REQUEST)
    def provide_chat_conversation_repository(
        self,
        session: MainAsyncSession,
    ) -> ChatConversationRepositorySqla:
        """Provide chat conversation repository for unified chat system."""
        return ChatConversationRepositorySqla(session)

    @provide(scope=Scope.REQUEST)
    def provide_chat_message_repository(
        self,
        session: MainAsyncSession,
    ) -> ChatMessageRepositorySqla:
        """Provide chat message repository for unified chat system."""
        return ChatMessageRepositorySqla(session)

    @provide(scope=Scope.REQUEST)
    def provide_rate_limit_repository(
        self,
        session: MainAsyncSession,
    ) -> RateLimitRepositorySqla:
        """Provide rate limit repository for unified chat system."""
        return RateLimitRepositorySqla(session)

    # ========================================
    # Chat V2 Services (Unified Chat System)
    # ========================================

    @provide(scope=Scope.REQUEST)
    def provide_chat_user_service(
        self,
        user_repository: ChatUserRepositorySqla,
    ) -> UserService:
        """Provide user service for unified chat system."""
        return UserService(
            user_repository=user_repository,
            privy_client=None,  # Optional Privy integration
        )

    @provide(scope=Scope.REQUEST)
    def provide_rate_limit_service(
        self,
        rate_limit_repository: RateLimitRepositorySqla,
    ) -> RateLimitService:
        """Provide rate limit service for unified chat system."""
        return RateLimitService(rate_limit_repository=rate_limit_repository)

    @provide(scope=Scope.REQUEST)
    def provide_conversation_memory(
        self,
        message_repository: ChatMessageRepositorySqla,
    ) -> ConversationMemory:
        """Provide conversation memory for unified chat system."""
        return ConversationMemory(message_repository=message_repository)

    @provide(scope=Scope.REQUEST)
    def provide_conversation_service(
        self,
        conversation_repository: ChatConversationRepositorySqla,
        message_repository: ChatMessageRepositorySqla,
    ) -> ConversationService:
        """Provide conversation service for unified chat system."""
        return ConversationService(
            conversation_repository=conversation_repository,
            message_repository=message_repository,
        )


def chat_phase2_provider() -> ChatPhase2Provider:
    """Factory function for Chat Phase 2 provider."""
    return ChatPhase2Provider()
