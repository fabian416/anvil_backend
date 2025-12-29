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
from sqlalchemy.ext.asyncio import AsyncSession

# Domain Ports - Repositories
from app.domain.chat.ports.analytics_repository import AnalyticsRepository
from app.domain.ports.agent_orchestration_repository import AgentOrchestrationRepository
from app.domain.ports.audit_log_repository import AuditLogRepository
from app.domain.chat.ports.export_repository import ExportRepository
from app.domain.ports.export_generator import ExportGenerator
from app.domain.chat.ports.template_repository import TemplateRepository
from app.domain.chat.ports.template_execution_repository import TemplateExecutionRepository
from app.domain.preferences.ports.user_preferences_repository import UserPreferencesRepository

# Domain Ports - External Services
from app.domain.ports.chat_llm_provider import ChatLLMProvider
from app.domain.ports.embeddings.embedding_service import EmbeddingService
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
from app.infrastructure.adapters.chat.analytics_repository_adapter import AnalyticsRepositoryAdapter
from app.infrastructure.adapters.chat.agent_orchestration_repository_adapter import AgentOrchestrationRepositoryAdapter
from app.infrastructure.adapters.chat.audit_log_repository_adapter import AuditLogRepositoryAdapter
from app.infrastructure.adapters.chat.export_repository_adapter import ExportRepositoryAdapter
from app.infrastructure.adapters.chat.export_generator_adapter import ExportGeneratorAdapter
from app.infrastructure.adapters.chat.template_repository_adapter import TemplateRepositoryAdapter
from app.infrastructure.adapters.chat.template_execution_repository_adapter import TemplateExecutionRepositoryAdapter
from app.infrastructure.adapters.chat.preferences_repository_adapter import UserPreferencesRepositoryAdapter

# Infrastructure Adapters - External Services
from app.infrastructure.adapters.ai.openai_chat_adapter import OpenAIChatAdapter
from app.infrastructure.adapters.ai.anthropic_chat_adapter import AnthropicChatAdapter
from app.infrastructure.adapters.ai.openai_embedding_adapter import OpenAIEmbeddingAdapter
from app.infrastructure.adapters.ai.cached_embedding_adapter import CachedEmbeddingAdapter

# Application Services
from app.application.chat.services.intent_detector import IntentDetectorService
from app.application.chat.commands.send_message_unified import UnifiedChatOrchestrator
from app.application.chat.commands.send_message import SendMessage
from app.application.chat.graph_search_handler import ChatGraphSearchHandler
from app.application.chat.risk_insights_handler import ChatRiskInsightsHandler
from app.application.agent_squad.commands.send_agent_squad_message import SendAgentSquadMessage
from app.application.agent_squad.commands.execute_supervisor_workflow import ExecuteSupervisorWorkflow

# Optional: Cohere embedding adapter (requires cohere package)
try:
    from app.infrastructure.adapters.ai.cohere_embedding_adapter import CohereEmbeddingAdapter
    COHERE_AVAILABLE = True
except ImportError:
    COHERE_AVAILABLE = False

# Optional: DeepL translation adapter (requires deepl package)
try:
    from app.infrastructure.adapters.external.deepl_translation_adapter import DeepLTranslationAdapter
    DEEPL_AVAILABLE = True
except ImportError:
    DEEPL_AVAILABLE = False

# Infrastructure Adapters - Redis
from app.infrastructure.adapters.chat.redis_cache_adapter import RedisCacheAdapter
from app.infrastructure.adapters.chat.redis_intent_cache_adapter import RedisIntentCacheAdapter
from app.infrastructure.adapters.chat.redis_session_store_adapter import RedisSessionStoreAdapter
from app.infrastructure.adapters.chat.redis_offline_queue_adapter import RedisOfflineQueueAdapter
from app.infrastructure.adapters.chat.redis_translation_cache_adapter import RedisTranslationCacheAdapter
from app.infrastructure.adapters.chat.notification_adapter import NotificationAdapter as NotificationAdapterImpl

# WebSocket Handlers
from app.presentation.http.websocket.connection_manager import ConnectionManager

# Optional: WebSocket handlers (may not be fully implemented)
try:
    from app.presentation.http.websocket.chat_websocket import ChatWebSocketHandler
    CHAT_WEBSOCKET_AVAILABLE = True
except (ImportError, AttributeError):
    CHAT_WEBSOCKET_AVAILABLE = False

try:
    from app.presentation.http.websocket.analytics_handler import AnalyticsWebSocketHandler
    ANALYTICS_WEBSOCKET_AVAILABLE = True
except (ImportError, AttributeError):
    ANALYTICS_WEBSOCKET_AVAILABLE = False

try:
    from app.presentation.http.websocket.template_handler import TemplateExecutionWebSocketHandler
    TEMPLATE_WEBSOCKET_AVAILABLE = True
except (ImportError, AttributeError):
    TEMPLATE_WEBSOCKET_AVAILABLE = False

# Application Services
from app.application.chat.services.advanced_intent_detector import AdvancedIntentDetector
from app.application.chat.services.user_analytics_service import UserChatAnalyticsService
from app.application.chat.services.admin_analytics_service import AdminChatAnalyticsService
from app.domain.chat.ports.conversation_repository import ConversationRepository


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
        redis_url = os.getenv("REDIS_CACHE_URL", os.getenv("REDIS_URL", "redis://localhost:6379/2"))

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
        session: AsyncSession,
    ) -> AnalyticsRepository:
        """Provide conversation analytics repository."""
        return AnalyticsRepositoryAdapter(session=session)

    @provide
    def provide_agent_orchestration_repository(
        self,
        session: AsyncSession,
    ) -> AgentOrchestrationRepository:
        """Provide agent orchestration repository."""
        return AgentOrchestrationRepositoryAdapter(session=session)

    @provide
    def provide_audit_log_repository(
        self,
        session: AsyncSession,
    ) -> AuditLogRepository:
        """Provide audit log repository."""
        return AuditLogRepositoryAdapter(session=session)

    @provide
    def provide_export_repository(
        self,
        session: AsyncSession,
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
        session: AsyncSession,
    ) -> TemplateRepository:
        """Provide conversation template repository."""
        return TemplateRepositoryAdapter(session=session)

    @provide
    def provide_template_execution_repository(
        self,
        session: AsyncSession,
    ) -> TemplateExecutionRepository:
        """Provide template execution repository."""
        return TemplateExecutionRepositoryAdapter(session=session)

    @provide
    def provide_user_preferences_repository(
        self,
        session: AsyncSession,
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

    @provide(scope=Scope.APP)
    def provide_openai_chat_provider(self) -> ChatLLMProvider:
        """
        Provide OpenAI chat LLM provider.

        Configured with:
        - GPT-4 Turbo or GPT-3.5 Turbo
        - Streaming support
        - Retry policies with exponential backoff
        """
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable not set")

        model = os.getenv("OPENAI_CHAT_MODEL", "gpt-4-turbo-preview")

        return OpenAIChatAdapter(
            api_key=api_key,
            model=model,
            temperature=0.7,
            max_tokens=2048,
            timeout=60.0,
            max_retries=3,
            retry_delay=1.0,
        )

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
    # Embedding Services (APP-scoped)
    # ========================================

    @provide(scope=Scope.APP)
    def provide_openai_embedding_service(self) -> EmbeddingService:
        """
        Provide OpenAI embedding service.

        Configured with:
        - text-embedding-3-large (3072 dimensions)
        - Batch processing support
        - Rate limiting
        """
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable not set")

        model = os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-large")

        return OpenAIEmbeddingAdapter(
            api_key=api_key,
            model=model,
            timeout=30.0,
            max_retries=3,
        )

    @provide(scope=Scope.APP)
    def provide_cohere_embedding_service(self) -> Optional[EmbeddingService]:
        """
        Provide Cohere embedding service.

        Optional fallback embedding service configured with:
        - embed-english-v3.0 or embed-multilingual-v3.0
        - Batch processing support

        Returns None if API key not configured or cohere package not installed.
        """
        if not COHERE_AVAILABLE:
            return None

        api_key = os.getenv("COHERE_API_KEY")
        if not api_key:
            return None

        model = os.getenv("COHERE_EMBEDDING_MODEL", "embed-english-v3.0")

        return CohereEmbeddingAdapter(
            api_key=api_key,
            model=model,
            timeout=30.0,
            max_retries=3,
        )

    @decorate
    def provide_cached_embedding_service(
        self,
        openai_embedding_service: EmbeddingService,
        redis_cache_client: Redis,
    ) -> EmbeddingService:
        """
        Provide cached embedding service.

        Wraps primary embedding service with Redis cache layer
        to reduce API costs and improve latency.

        Uses @decorate to wrap the base EmbeddingService provider.
        """
        return CachedEmbeddingAdapter(
            embedding_service=openai_embedding_service,
            redis_client=redis_cache_client,
            prefix="embed",
            ttl=2592000,  # 30 days
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
        session: AsyncSession,
    ) -> VectorRepository:
        """
        Provide vector repository for similarity search.

        Uses PostgreSQL with array operations for vector storage.
        """
        from app.infrastructure.persistence_sqla.repositories.vector_repository_sqla import VectorRepositorySqla

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
    ) -> Optional[Any]:
        """Provide template execution WebSocket handler (REQUEST-scoped to access repository)."""
        if not TEMPLATE_WEBSOCKET_AVAILABLE:
            return None
        return TemplateExecutionWebSocketHandler(
            connection_manager=connection_manager,
            template_execution_repository=template_execution_repository,
        )

    # ========================================
    # Analytics Services (REQUEST-scoped)
    # ========================================

    @provide
    def provide_user_chat_analytics_service(
        self,
        conversation_repository: ConversationRepository,
        analytics_repository: AnalyticsRepository,
    ) -> UserChatAnalyticsService:
        """
        Provide user-level chat analytics service.

        Generates personalized analytics for individual users.
        """
        return UserChatAnalyticsService(
            conversation_repository=conversation_repository,
            analytics_repository=analytics_repository,
        )

    @provide
    def provide_admin_chat_analytics_service(
        self,
        conversation_repository: ConversationRepository,
        analytics_repository: AnalyticsRepository,
    ) -> AdminChatAnalyticsService:
        """
        Provide admin-level chat analytics service.

        Aggregates analytics across all users for admin dashboards.
        """
        return AdminChatAnalyticsService(
            conversation_repository=conversation_repository,
            analytics_repository=analytics_repository,
        )

    # ========================================
    # Intent Detection (REQUEST-scoped)
    # ========================================

    @provide
    def provide_advanced_intent_detector(
        self,
        conversation_repository: ConversationRepository,
    ) -> AdvancedIntentDetector:
        """
        Provide advanced intent detection service.

        Analyzes user input to detect intent and provide real-time suggestions.
        """
        return AdvancedIntentDetector(
            conversation_repository=conversation_repository,
        )

    # ========================================
    # Unified Chat Routing (Phase 8)
    # ========================================

    @provide
    def provide_intent_detector_service(
        self,
        llm_gateway: LLMGateway,
    ) -> IntentDetectorService:
        """
        Provide intent detector for unified routing.

        Uses LLM-powered classification with keyword fallback.
        LLM gateway is automatically injected by Dishka:
        - In tests: MockLLMGateway from TestMockProvider
        - In production: LLMGatewayImpl or InstrumentedLLMGateway
        """
        return IntentDetectorService(llm_gateway=llm_gateway)

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
    ) -> UnifiedChatOrchestrator:
        """
        Provide unified chat orchestrator.

        Routes messages to appropriate handlers based on detected intent.
        """
        return UnifiedChatOrchestrator(
            conversation_repo=conversation_repository,
            intent_detector=intent_detector_service,
            graphrag_search=graphrag_search_handler,
            graphrag_risk=graphrag_risk_handler,
            agent_squad=agent_squad_message_command,
            supervisor=supervisor_workflow_command,
            regular_chat=regular_chat_command,
        )


def chat_phase2_provider() -> ChatPhase2Provider:
    """Factory function for Chat Phase 2 provider."""
    return ChatPhase2Provider()
