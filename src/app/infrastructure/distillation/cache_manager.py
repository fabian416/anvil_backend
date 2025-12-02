"""Cache manager for distillation system."""
import asyncio
from datetime import datetime, timedelta
from typing import List, Optional

from app.domain.ports.distillation_repository import CacheRepository
from app.domain.value_objects.distillation import (
    CachedResponse,
    CacheLevel,
    Intent,
)


class CacheManager:
    """
    Hierarchical caching with fallback.
    
    Three levels:
    1. L1: Exact match (Redis, <5ms)
    2. L2: Semantic match (pgvector, <20ms)
    3. L3: Miss - will need LLM
    """
    
    def __init__(
        self,
        cache_repository: CacheRepository,
        embedding_service: Optional[object] = None,  # TODO: Define embedding service port
    ):
        self.cache_repo = cache_repository
        self.embedding_service = embedding_service
    
    async def get(
        self,
        cache_key: str,
        query: str,
        semantic_threshold: float = 0.95,
    ) -> tuple[Optional[str], CacheLevel]:
        """
        Get cached response with level indicator.
        
        Args:
            cache_key: Exact cache key
            query: Original query for semantic search
            semantic_threshold: Minimum similarity for semantic match
            
        Returns:
            Tuple of (cached_content, cache_level)
        """
        # L1: Try exact match first (fastest)
        exact_hit = await self.cache_repo.get_exact(cache_key)
        if exact_hit and exact_hit.expires_at > datetime.utcnow():
            # Update hit statistics
            await self._increment_hit_count(exact_hit)
            return exact_hit.response_content, CacheLevel.EXACT
        
        # L2: Try semantic match (slower but still fast)
        if self.embedding_service:
            try:
                # Generate embedding for query
                embedding = await self._get_embedding(query)
                
                # Search semantic cache
                semantic_hit = await self.cache_repo.get_semantic(
                    query_embedding=embedding,
                    threshold=semantic_threshold,
                )
                
                if semantic_hit and semantic_hit.expires_at > datetime.utcnow():
                    # Update hit statistics
                    await self._increment_hit_count(semantic_hit)
                    return semantic_hit.response_content, CacheLevel.SEMANTIC
            except Exception:
                # Semantic search failed, continue to miss
                pass
        
        # L3: Cache miss
        return None, CacheLevel.NONE
    
    async def set(
        self,
        cache_key: str,
        query: str,
        intent: Intent,
        response_content: str,
        ttl_seconds: int,
        entities: Optional[dict] = None,
        source_model: Optional[str] = None,
        source_request_id: Optional[str] = None,
    ) -> None:
        """
        Store response in both exact and semantic caches.
        
        Args:
            cache_key: Exact cache key
            query: Original query
            intent: Classified intent
            response_content: Response to cache
            ttl_seconds: Time to live in seconds
            entities: Extracted entities
            source_model: Model that generated response
            source_request_id: Original request ID
        """
        normalized_query = query.lower().strip()
        
        # Store in exact cache
        await self.cache_repo.set_exact(
            cache_key=cache_key,
            normalized_query=normalized_query,
            intent=intent,
            response_content=response_content,
            ttl_seconds=ttl_seconds,
            entities=entities or {},
            source_model=source_model,
            source_request_id=source_request_id,
        )
        
        # Store in semantic cache if embedding service available
        if self.embedding_service:
            try:
                embedding = await self._get_embedding(query)
                
                await self.cache_repo.set_semantic(
                    query_embedding=embedding,
                    original_query=query,
                    intent=intent,
                    response_content=response_content,
                    ttl_seconds=ttl_seconds,
                    entities=entities or {},
                    source_model=source_model,
                    source_request_id=source_request_id,
                )
            except Exception:
                # Semantic cache failed, but exact cache succeeded
                pass
    
    async def invalidate(
        self,
        cache_type: str = "all",
        filters: Optional[dict] = None,
    ) -> int:
        """
        Invalidate cache entries.
        
        Args:
            cache_type: "exact", "semantic", or "all"
            filters: Optional filters (intent, older_than_hours, etc.)
            
        Returns:
            Number of entries invalidated
        """
        return await self.cache_repo.invalidate(cache_type, filters)
    
    async def get_stats(self) -> dict:
        """Get cache statistics."""
        return await self.cache_repo.get_stats()
    
    async def warm_cache(
        self,
        queries: List[str],
        responses: List[str],
        intents: List[Intent],
        ttl_seconds: int = 3600,
    ) -> int:
        """
        Pre-warm cache with common queries.
        
        Args:
            queries: List of queries to cache
            responses: List of corresponding responses
            intents: List of intents
            ttl_seconds: TTL for cached entries
            
        Returns:
            Number of entries cached
        """
        tasks = []
        
        for query, response, intent in zip(queries, responses, intents):
            # Generate cache key
            normalized = query.lower().strip()
            import hashlib
            cache_key = f"distill:v1:{hashlib.sha256(normalized.encode()).hexdigest()[:16]}"
            
            # Create set task
            task = self.set(
                cache_key=cache_key,
                query=query,
                intent=intent,
                response_content=response,
                ttl_seconds=ttl_seconds,
            )
            tasks.append(task)
        
        # Execute all sets in parallel
        await asyncio.gather(*tasks, return_exceptions=True)
        
        return len(tasks)
    
    async def _get_embedding(self, text: str) -> List[float]:
        """
        Get embedding for text.
        
        TODO: Implement with actual embedding service
        (OpenAI text-embedding-3-small or similar)
        """
        if self.embedding_service:
            return await self.embedding_service.embed(text)
        
        # Placeholder: return zeros
        return [0.0] * 1536
    
    async def _increment_hit_count(self, cached: CachedResponse) -> None:
        """Increment hit count for cached entry."""
        # This will be handled by the repository layer
        # The repository should update hit_count and last_hit_at
        pass
