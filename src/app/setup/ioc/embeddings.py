"""
Embedding Service Dependency Injection.

Configures and provides embedding services (OpenAI, Cohere, cached).
"""

from typing import Optional

import redis.asyncio as aioredis
from dishka import Provider, Scope, provide

from app.domain.ports.ai.embedding_service import EmbeddingService
from app.infrastructure.adapters.ai.openai_embedding_adapter import (
    OpenAIEmbeddingAdapter,
)
from app.infrastructure.adapters.ai.cohere_embedding_adapter import (
    CohereEmbeddingAdapter,
)
from app.infrastructure.adapters.ai.cached_embedding_adapter import (
    CachedEmbeddingAdapter,
)
from app.setup.config.settings import AppSettings


class EmbeddingProvider(Provider):
    """Provider for embedding services."""

    scope = Scope.APP

    @provide
    def provide_openai_embedding_service(
        self,
        settings: AppSettings,
    ) -> Optional[OpenAIEmbeddingAdapter]:
        """
        Provide OpenAI embedding service.

        Requires settings.openai.api_key to be configured.

        Returns:
            OpenAIEmbeddingAdapter or None if not configured
        """
        # Check if OpenAI settings exist
        if not hasattr(settings, "openai") or not settings.openai:
            return None

        if not settings.openai.api_key:
            return None

        # Get model configuration
        model = getattr(settings.openai, "embedding_model", "text-embedding-3-large")
        dimensions = getattr(settings.openai, "embedding_dimensions", None)

        return OpenAIEmbeddingAdapter(
            api_key=settings.openai.api_key,
            model=model,
            dimensions=dimensions,
            organization=getattr(settings.openai, "organization", None),
        )

    @provide
    def provide_cohere_embedding_service(
        self,
        settings: AppSettings,
    ) -> Optional[CohereEmbeddingAdapter]:
        """
        Provide Cohere embedding service.

        Requires settings.cohere.api_key to be configured.

        Returns:
            CohereEmbeddingAdapter or None if not configured
        """
        # Check if Cohere settings exist
        if not hasattr(settings, "cohere") or not settings.cohere:
            return None

        if not settings.cohere.api_key:
            return None

        # Get model configuration
        model = getattr(settings.cohere, "embedding_model", "embed-english-v3.0")

        return CohereEmbeddingAdapter(
            api_key=settings.cohere.api_key,
            model=model,
        )

    @provide
    def provide_default_embedding_service(
        self,
        openai_service: Optional[OpenAIEmbeddingAdapter],
        cohere_service: Optional[CohereEmbeddingAdapter],
        redis_client: aioredis.Redis,
        settings: AppSettings,
    ) -> EmbeddingService:
        """
        Provide default embedding service with caching.

        Priority:
        1. OpenAI (if configured)
        2. Cohere (if configured)
        3. Raises error if neither is configured

        Returns:
            Cached embedding service wrapping the selected provider

        Raises:
            ValueError: If no embedding service is configured
        """
        # Select base service
        base_service = None
        if openai_service is not None:
            base_service = openai_service
        elif cohere_service is not None:
            base_service = cohere_service
        else:
            raise ValueError(
                "No embedding service configured. "
                "Configure OpenAI or Cohere in settings."
            )

        # Get cache settings
        cache_enabled = getattr(
            getattr(settings, "embedding_cache", None),
            "enabled",
            True,
        )
        cache_ttl = getattr(
            getattr(settings, "embedding_cache", None),
            "ttl",
            3600,
        )

        # Wrap with caching if enabled
        if cache_enabled:
            return CachedEmbeddingAdapter(
                embedding_service=base_service,
                redis_client=redis_client,
                ttl=cache_ttl,
                prefix="emb_cache",
            )

        # Return base service without caching
        return base_service  # type: ignore
