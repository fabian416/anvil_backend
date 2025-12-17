"""
Chat Phase 2 Dependency Injection Configuration.

Provides DI setup for all Phase 2 components:
- 15 Repository adapters (PostgreSQL + Redis)
- External service providers (LLM, Embedding, Translation, Vector DB)
- WebSocket handlers (Chat, Analytics, Template Execution)
- Session management and caching
"""

import os
from typing import Optional

from dishka import Provider, Scope, provide
from redis.asyncio import Redis, ConnectionPool
from sqlalchemy.ext.asyncio import AsyncSession

# Domain Ports - Repositories
from app.domain.ports.analytics_repository import AnalyticsRepository
from app.domain.ports.agent_orchestration_repository import AgentOrchestrationRepository
from app.domain.ports.audit_log_repository import AuditLogRepository
from app.domain.ports.export_repository import ExportRepository
from app.domain.ports.export_generator import ExportGenerator
from app.domain.ports.template_repository import TemplateRepository
from app.domain.ports.template_execution_repository import TemplateExecutionRepository
from app.domain.ports.user_preferences_repository import UserPreferencesRepository

# Domain Ports - External Services
from app.domain.ports.chat_llm_provider import ChatLLMProvider
from app.domain.ports.embeddings.embedding_service import EmbeddingService
from app.domain.ports.translation_adapter import TranslationAdapter
from app.domain.ports.vector.vector_repository import VectorRepository

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
from app.infrastructure.adapters.ai.cohere_embedding_adapter import CohereEmbeddingAdapter
from app.infrastructure.adapters.ai.cached_embedding_adapter import CachedEmbeddingAdapter
from app.infrastructure.adapters.external.deepl_translation_adapter import DeepLTranslationAdapter

# Infrastructure Adapters - Redis
from app.infrastructure.adapters.chat.redis_cache_adapter import RedisCacheAdapter
from app.infrastructure.adapters.chat.redis_intent_cache_adapter import RedisIntentCacheAdapter
from app.infrastructure.adapters.chat.redis_session_store_adapter import RedisSessionStoreAdapter
from app.infrastructure.adapters.chat.redis_offline_queue_adapter import RedisOfflineQueueAdapter
from app.infrastructure.adapters.chat.redis_translation_cache_adapter import RedisTranslationCacheAdapter
from app.infrastructure.adapters.chat.notification_adapter import NotificationAdapter as NotificationAdapterImpl

# WebSocket Handlers
from app.presentation.http.websocket.chat_websocket import ChatWebSocketHandler
from app.presentation.http.websocket.analytics_handler import AnalyticsWebSocketHandler
from app.presentation.http.websocket.template_handler import TemplateExecutionWebSocketHandler
from app.presentation.http.websocket.connection_manager import ConnectionManager

# Application Services
from app.application.chat.services.advanced_intent_detector import AdvancedIntentDetector
from app.application.chat.services.user_analytics_service import UserChatAnalyticsService
from app.application.chat.services.admin_analytics_service import AdminChatAnalyticsService
from app.domain.ports.conversation_repository import ConversationRepository


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
            batch_size=100,
        )

    @provide(scope=Scope.APP)
    def provide_cohere_embedding_service(self) -> Optional[EmbeddingService]:
        """
        Provide Cohere embedding service.

        Optional fallback embedding service configured with:
        - embed-english-v3.0 or embed-multilingual-v3.0
        - Batch processing support

        Returns None if API key not configured.
        """
        api_key = os.getenv("COHERE_API_KEY")
        if not api_key:
            return None

        model = os.getenv("COHERE_EMBEDDING_MODEL", "embed-english-v3.0")

        return CohereEmbeddingAdapter(
            api_key=api_key,
            model=model,
            timeout=30.0,
            max_retries=3,
            batch_size=96,
        )

    @provide(scope=Scope.APP)
    def provide_cached_embedding_service(
        self,
        openai_embedding_service: EmbeddingService,
        redis_cache_client: Redis,
    ) -> EmbeddingService:
        """
        Provide cached embedding service.

        Wraps primary embedding service with Redis cache layer
        to reduce API costs and improve latency.
        """
        return CachedEmbeddingAdapter(
            embedding_service=openai_embedding_service,
            redis_client=redis_cache_client,
            key_prefix="embed",
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

        Returns None if API key not configured.
        """
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
    # Vector Database (APP-scoped)
    # ========================================

    @provide(scope=Scope.APP)
    def provide_vector_repository(
        self,
        session: AsyncSession,
    ) -> VectorRepository:
        """
        Provide vector repository for similarity search.

        Currently uses PostgreSQL with pgvector extension.
        Can be swapped to Pinecone, Weaviate, or other vector DBs.

        Configuration via environment:
        - VECTOR_DB_TYPE: "pgvector" (default), "pinecone", "weaviate"
        - PINECONE_API_KEY: API key for Pinecone
        - PINECONE_ENVIRONMENT: Pinecone environment
        - WEAVIATE_URL: Weaviate instance URL
        """
        vector_db_type = os.getenv("VECTOR_DB_TYPE", "pgvector")

        if vector_db_type == "pinecone":
            # Lazy import to avoid dependencies if not used
            from app.infrastructure.adapters.vector.pinecone_adapter import PineconeVectorAdapter

            api_key = os.getenv("PINECONE_API_KEY")
            environment = os.getenv("PINECONE_ENVIRONMENT", "us-west1-gcp")

            if not api_key:
                raise ValueError("PINECONE_API_KEY required when VECTOR_DB_TYPE=pinecone")

            return PineconeVectorAdapter(
                api_key=api_key,
                environment=environment,
                index_name="anvil-embeddings",
            )

        elif vector_db_type == "weaviate":
            # Lazy import to avoid dependencies if not used
            from app.infrastructure.adapters.vector.weaviate_adapter import WeaviateVectorAdapter

            url = os.getenv("WEAVIATE_URL", "http://localhost:8080")
            api_key = os.getenv("WEAVIATE_API_KEY")  # Optional for local

            return WeaviateVectorAdapter(
                url=url,
                api_key=api_key,
                class_name="AnvilEmbedding",
            )

        else:  # Default: pgvector
            from app.infrastructure.adapters.vector.pgvector_adapter import PgVectorAdapter

            return PgVectorAdapter(session=session)

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
    ) -> ChatWebSocketHandler:
        """Provide chat WebSocket handler."""
        return ChatWebSocketHandler(
            connection_manager=connection_manager,
            session_store=session_store,
        )

    @provide(scope=Scope.APP)
    def provide_analytics_websocket_handler(
        self,
        connection_manager: ConnectionManager,
        analytics_repository: AnalyticsRepository,
    ) -> AnalyticsWebSocketHandler:
        """Provide analytics WebSocket handler."""
        return AnalyticsWebSocketHandler(
            connection_manager=connection_manager,
            analytics_repository=analytics_repository,
        )

    @provide(scope=Scope.APP)
    def provide_template_execution_websocket_handler(
        self,
        connection_manager: ConnectionManager,
        template_execution_repository: TemplateExecutionRepository,
    ) -> TemplateExecutionWebSocketHandler:
        """Provide template execution WebSocket handler."""
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


def chat_phase2_provider() -> ChatPhase2Provider:
    """Factory function for Chat Phase 2 provider."""
    return ChatPhase2Provider()
