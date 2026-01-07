"""
Embedding Service Dependency Injection.

Configures and provides embedding services (OpenAI, Cohere, cached).
"""

from typing import Optional

import redis.asyncio as aioredis
from dishka import Provider, Scope, provide

from app.domain.ports.ai.embedding_service import EmbeddingService
# OpenAI removed - using only Cohere and DeepInfra for embeddings
# from app.infrastructure.adapters.ai.openai_embedding_adapter import (
#     OpenAIEmbeddingAdapter,
# )
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

    # OpenAI removed - using only Cohere and DeepInfra for embeddings
    # @provide
    # def provide_openai_embedding_service(...) -> Optional[OpenAIEmbeddingAdapter]:
    #     """OpenAI embedding service - REMOVED"""
    #     return None

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
        cohere_service: Optional[CohereEmbeddingAdapter],
        redis_client: aioredis.Redis,
        settings: AppSettings,
    ) -> EmbeddingService:
        """
        Provide default embedding service with caching.

        Priority:
        1. Cohere (if configured)
        2. DeepInfra (fallback)
        3. Raises error if neither is configured

        Note: OpenAI removed - using only Cohere and DeepInfra.

        Returns:
            Cached embedding service wrapping the selected provider

        Raises:
            ValueError: If no embedding service is configured
        """
        import os
        import logging
        from app.infrastructure.embeddings import DeepInfraEmbeddingService
        from app.setup.config.loader import load_full_config, get_current_env
        
        logger = logging.getLogger(__name__)
        
        # Select base service
        base_service = None
        if cohere_service is not None:
            base_service = cohere_service
        else:
            # Fallback to DeepInfra - try .secrets.toml first, then env var
            deepinfra_key = ""
            try:
                raw_config = load_full_config(env=get_current_env())
                deepinfra_key = raw_config.get("deepinfra", {}).get("API_KEY", "")
            except Exception as e:
                logger.debug(f"Could not load config from .secrets.toml: {e}")
            
            # Fallback to environment variable
            if not deepinfra_key:
                deepinfra_key = os.getenv("DEEPINFRA_API_KEY", "")
            
            if deepinfra_key:
                logger.info("DeepInfra embedding service configured from .secrets.toml or env var")
                base_service = DeepInfraEmbeddingService(api_key=deepinfra_key)
            else:
                raise ValueError(
                    "No embedding service configured. "
                    "Configure Cohere (COHERE_API_KEY) or DeepInfra ([deepinfra] API_KEY in .secrets.toml) in settings."
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
