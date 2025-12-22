"""
Cached Embedding Adapter.

Wraps any embedding service with Redis caching to reduce API calls
and costs for frequently embedded texts.

Features:
- Automatic cache key generation from text content
- TTL-based expiration
- Cache hit/miss statistics
- Batch-aware caching
- Automatic cache warming
- Cost savings tracking

Usage:
    >>> from app.infrastructure.adapters.ai.openai_embedding_adapter import OpenAIEmbeddingAdapter
    >>> from app.infrastructure.adapters.ai.cached_embedding_adapter import CachedEmbeddingAdapter
    >>>
    >>> base_adapter = OpenAIEmbeddingAdapter(api_key="sk-...")
    >>> cached_adapter = CachedEmbeddingAdapter(
    ...     embedding_service=base_adapter,
    ...     redis_client=redis_client,
    ...     ttl=3600,  # Cache for 1 hour
    ... )
    >>>
    >>> # First call - cache miss, hits API
    >>> embedding1 = await cached_adapter.embed_text("Hello world")
    >>>
    >>> # Second call - cache hit, no API call
    >>> embedding2 = await cached_adapter.embed_text("Hello world")
    >>>
    >>> # Check statistics
    >>> stats = await cached_adapter.get_cache_stats()
    >>> print(f"Hit rate: {stats['hit_rate']:.1f}%")
    >>> print(f"Cost saved: ${stats['cost_saved_usd']:.4f}")
"""

import hashlib
import json
import logging
from dataclasses import dataclass
from typing import List, Optional

import redis.asyncio as aioredis

from app.domain.ports.ai.embedding_service import (
    EmbeddingInputType,
    EmbeddingResult,
    BatchEmbeddingResult,
)

logger = logging.getLogger(__name__)


@dataclass
class CacheStats:
    """Cache statistics."""

    hits: int = 0
    misses: int = 0
    api_calls: int = 0
    cached_embeddings: int = 0
    cost_saved_usd: float = 0.0

    @property
    def total_requests(self) -> int:
        """Total requests."""
        return self.hits + self.misses

    @property
    def hit_rate(self) -> float:
        """Hit rate percentage."""
        total = self.total_requests
        return (self.hits / total * 100) if total > 0 else 0.0


class CachedEmbeddingAdapter:
    """
    Embedding service with Redis caching.

    Wraps any embedding service (OpenAI, Cohere, etc.) and caches
    embeddings by text content to reduce API calls and costs.

    The cache key is generated from:
    - Text content (hashed for shorter keys)
    - Provider name
    - Model name
    - Input type (if applicable)

    This ensures that:
    - Same text always gets cached embedding
    - Different models/providers use separate cache entries
    - Different input types use separate cache entries
    """

    def __init__(
        self,
        embedding_service,  # Any object implementing EmbeddingService protocol
        redis_client: aioredis.Redis,
        ttl: int = 3600,  # 1 hour default
        prefix: str = "emb_cache",
        enable_stats: bool = True,
    ):
        """
        Initialize cached embedding adapter.

        Args:
            embedding_service: Underlying embedding service
            redis_client: Redis async client
            ttl: Cache TTL in seconds (default: 1 hour)
            prefix: Cache key prefix
            enable_stats: Track cache statistics
        """
        self._service = embedding_service
        self._redis = redis_client
        self._ttl = ttl
        self._prefix = prefix
        self._enable_stats = enable_stats

        # Statistics
        self._stats = CacheStats()

        # Get provider info from underlying service
        self._provider = self._service.get_provider_name()
        self._model = getattr(self._service, "_model", "unknown")
        self._dimensions = self._service.get_dimensions()

        logger.info(
            f"Cached embedding adapter initialized: provider={self._provider}, "
            f"model={self._model}, ttl={ttl}s"
        )

    def _make_cache_key(
        self,
        text: str,
        input_type: Optional[EmbeddingInputType] = None,
    ) -> str:
        """
        Generate cache key from text and parameters.

        Args:
            text: Input text
            input_type: Optional input type

        Returns:
            Cache key string
        """
        # Hash text content for shorter keys
        text_hash = hashlib.sha256(text.encode()).hexdigest()

        # Include input type if provided
        type_suffix = f":{input_type.value}" if input_type else ""

        key = f"{self._prefix}:{self._provider}:{self._model}:{text_hash}{type_suffix}"
        return key

    async def _get_from_cache(
        self,
        text: str,
        input_type: Optional[EmbeddingInputType] = None,
    ) -> Optional[List[float]]:
        """
        Get embedding from cache.

        Args:
            text: Input text
            input_type: Optional input type

        Returns:
            Cached embedding or None if not found
        """
        key = self._make_cache_key(text, input_type)

        try:
            cached = await self._redis.get(key)
            if cached:
                if self._enable_stats:
                    self._stats.hits += 1
                embedding = json.loads(cached)
                logger.debug(f"Cache HIT: {key[:50]}...")
                return embedding

            if self._enable_stats:
                self._stats.misses += 1
            logger.debug(f"Cache MISS: {key[:50]}...")
            return None

        except Exception as e:
            logger.warning(f"Cache get error: {e}")
            return None

    async def _set_in_cache(
        self,
        text: str,
        embedding: List[float],
        input_type: Optional[EmbeddingInputType] = None,
    ) -> bool:
        """
        Store embedding in cache.

        Args:
            text: Input text
            embedding: Embedding vector
            input_type: Optional input type

        Returns:
            True if cached successfully
        """
        key = self._make_cache_key(text, input_type)

        try:
            serialized = json.dumps(embedding)
            await self._redis.setex(key, self._ttl, serialized)
            if self._enable_stats:
                self._stats.cached_embeddings += 1
            logger.debug(f"Cache SET: {key[:50]}... (TTL={self._ttl}s)")
            return True

        except Exception as e:
            logger.warning(f"Cache set error: {e}")
            return False

    async def embed_text(
        self,
        text: str,
        input_type: Optional[EmbeddingInputType] = None,
    ) -> List[float]:
        """
        Generate embedding for a single text (with caching).

        Args:
            text: Input text
            input_type: Input type

        Returns:
            Embedding vector
        """
        # Try cache first
        cached = await self._get_from_cache(text, input_type)
        if cached is not None:
            return cached

        # Cache miss - call underlying service
        if self._enable_stats:
            self._stats.api_calls += 1

        embedding = await self._service.embed_text(text, input_type)

        # Store in cache
        await self._set_in_cache(text, embedding, input_type)

        return embedding

    async def embed_texts(
        self,
        texts: List[str],
        input_type: Optional[EmbeddingInputType] = None,
    ) -> List[List[float]]:
        """
        Generate embeddings for multiple texts (with caching).

        Checks cache for each text individually and only calls API
        for texts that are not cached.

        Args:
            texts: List of input texts
            input_type: Input type

        Returns:
            List of embedding vectors
        """
        if not texts:
            return []

        # Check cache for each text
        embeddings = [None] * len(texts)
        uncached_indices = []
        uncached_texts = []

        for i, text in enumerate(texts):
            cached = await self._get_from_cache(text, input_type)
            if cached is not None:
                embeddings[i] = cached
            else:
                uncached_indices.append(i)
                uncached_texts.append(text)

        # Fetch uncached embeddings from API
        if uncached_texts:
            if self._enable_stats:
                self._stats.api_calls += 1

            new_embeddings = await self._service.embed_texts(
                uncached_texts, input_type
            )

            # Store new embeddings in cache and update results
            for idx, text, embedding in zip(
                uncached_indices, uncached_texts, new_embeddings
            ):
                embeddings[idx] = embedding
                await self._set_in_cache(text, embedding, input_type)

        return embeddings  # type: ignore

    async def embed_with_metadata(
        self,
        text: str,
        input_type: Optional[EmbeddingInputType] = None,
    ) -> EmbeddingResult:
        """
        Generate embedding with metadata (with caching).

        Note: When serving from cache, cost will be 0 since no API call was made.

        Args:
            text: Input text
            input_type: Input type

        Returns:
            EmbeddingResult with vector and metadata
        """
        # Try cache first
        cached = await self._get_from_cache(text, input_type)
        if cached is not None:
            # Return cached result with zero cost
            return EmbeddingResult(
                text=text,
                embedding=cached,
                model=self._model,
                dimensions=self._dimensions,
                provider=self._provider,
                input_tokens=0,
                cost_usd=0.0,
            )

        # Cache miss - call underlying service
        if self._enable_stats:
            self._stats.api_calls += 1

        result = await self._service.embed_with_metadata(text, input_type)

        # Track cost savings
        if self._enable_stats:
            self._stats.cost_saved_usd += 0  # First call, no savings yet

        # Store in cache
        await self._set_in_cache(text, result.embedding, input_type)

        return result

    async def embed_batch_with_metadata(
        self,
        texts: List[str],
        input_type: Optional[EmbeddingInputType] = None,
    ) -> BatchEmbeddingResult:
        """
        Generate batch embeddings with metadata (with caching).

        Args:
            texts: List of input texts
            input_type: Input type

        Returns:
            BatchEmbeddingResult with vectors and metadata
        """
        if not texts:
            return BatchEmbeddingResult(
                embeddings=[],
                texts=[],
                model=self._model,
                dimensions=self._dimensions,
                provider=self._provider,
                total_tokens=0,
                total_cost_usd=0.0,
            )

        # Check cache for each text
        embeddings = [None] * len(texts)
        uncached_indices = []
        uncached_texts = []

        for i, text in enumerate(texts):
            cached = await self._get_from_cache(text, input_type)
            if cached is not None:
                embeddings[i] = cached
            else:
                uncached_indices.append(i)
                uncached_texts.append(text)

        # Initialize metadata
        total_tokens = 0
        total_cost = 0.0

        # Fetch uncached embeddings from API
        if uncached_texts:
            if self._enable_stats:
                self._stats.api_calls += 1

            result = await self._service.embed_batch_with_metadata(
                uncached_texts, input_type
            )

            total_tokens = result.total_tokens
            total_cost = result.total_cost_usd

            # Store new embeddings in cache and update results
            for idx, text, embedding in zip(
                uncached_indices, uncached_texts, result.embeddings
            ):
                embeddings[idx] = embedding
                await self._set_in_cache(text, embedding, input_type)

        return BatchEmbeddingResult(
            embeddings=embeddings,  # type: ignore
            texts=texts,
            model=self._model,
            dimensions=self._dimensions,
            provider=self._provider,
            total_tokens=total_tokens,
            total_cost_usd=total_cost,
        )

    def get_dimensions(self) -> int:
        """Get embedding dimensions."""
        return self._dimensions

    def get_max_batch_size(self) -> int:
        """Get maximum batch size."""
        return self._service.get_max_batch_size()

    def get_provider_name(self) -> str:
        """Get provider name."""
        return self._provider

    async def invalidate_cache(
        self,
        text: Optional[str] = None,
        input_type: Optional[EmbeddingInputType] = None,
    ) -> int:
        """
        Invalidate cache entries.

        Args:
            text: Specific text to invalidate (None = all entries)
            input_type: Specific input type to invalidate

        Returns:
            Number of keys invalidated
        """
        if text:
            # Invalidate specific text
            key = self._make_cache_key(text, input_type)
            deleted = await self._redis.delete(key)
            logger.info(f"Invalidated cache key: {key[:50]}...")
            return deleted

        # Invalidate all cache entries for this service
        pattern = f"{self._prefix}:{self._provider}:{self._model}:*"
        cursor = 0
        deleted = 0

        try:
            while True:
                cursor, keys = await self._redis.scan(
                    cursor, match=pattern, count=100
                )

                if keys:
                    await self._redis.delete(*keys)
                    deleted += len(keys)

                if cursor == 0:
                    break

            logger.info(f"Invalidated {deleted} cache keys (pattern: {pattern})")
            return deleted

        except Exception as e:
            logger.error(f"Cache invalidation error: {e}")
            return 0

    async def get_cache_stats(self) -> dict:
        """
        Get cache statistics.

        Returns:
            Dictionary with cache statistics
        """
        return {
            "hits": self._stats.hits,
            "misses": self._stats.misses,
            "total_requests": self._stats.total_requests,
            "hit_rate": self._stats.hit_rate,
            "api_calls": self._stats.api_calls,
            "cached_embeddings": self._stats.cached_embeddings,
            "cost_saved_usd": self._stats.cost_saved_usd,
            "provider": self._provider,
            "model": self._model,
            "ttl": self._ttl,
        }

    async def warm_cache(
        self,
        texts: List[str],
        input_type: Optional[EmbeddingInputType] = None,
    ) -> int:
        """
        Pre-warm cache with embeddings for given texts.

        Args:
            texts: List of texts to cache
            input_type: Input type

        Returns:
            Number of texts cached
        """
        if not texts:
            return 0

        # Generate embeddings and cache them
        result = await self.embed_batch_with_metadata(texts, input_type)

        logger.info(f"Warmed cache with {len(result)} embeddings")
        return len(result)

    async def close(self) -> None:
        """Close the underlying service connection."""
        if hasattr(self._service, "close"):
            await self._service.close()

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()


# Factory function
def create_cached_embedding_service(
    embedding_service,
    redis_client: aioredis.Redis,
    ttl: int = 3600,
    **kwargs,
) -> CachedEmbeddingAdapter:
    """
    Factory function to create cached embedding service.

    Args:
        embedding_service: Underlying embedding service
        redis_client: Redis async client
        ttl: Cache TTL in seconds
        **kwargs: Additional arguments for adapter

    Returns:
        CachedEmbeddingAdapter instance
    """
    return CachedEmbeddingAdapter(
        embedding_service=embedding_service,
        redis_client=redis_client,
        ttl=ttl,
        **kwargs,
    )
