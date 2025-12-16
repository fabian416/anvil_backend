"""
Redis cache adapter implementation.

Implements CacheAdapter port using Redis for high-performance caching
with semantic similarity search support.
"""

import json
from datetime import timedelta
from typing import List, Optional
import asyncio

from redis.asyncio import Redis
from redis.commands.search.query import Query
from redis.commands.search.field import TextField, NumericField, VectorField
from redis.commands.search.indexDefinition import IndexDefinition, IndexType

from app.domain.ports.cache_adapter import CacheAdapter
from app.domain.value_objects.chat.performance import CacheEntry, CacheStatistics


class RedisCacheAdapter(CacheAdapter):
    """
    Redis implementation of cache adapter.

    Features:
    - High-performance key-value storage
    - Vector similarity search for semantic caching
    - Automatic TTL management
    - Hit/miss statistics tracking
    - Memory usage monitoring
    """

    def __init__(
        self,
        redis_client: Redis,
        key_prefix: str = "chat:cache:",
        stats_key: str = "chat:cache:stats",
    ) -> None:
        """
        Initialize Redis cache adapter.

        Args:
            redis_client: Redis async client
            key_prefix: Prefix for cache keys
            stats_key: Key for statistics storage
        """
        self._redis = redis_client
        self._key_prefix = key_prefix
        self._stats_key = stats_key
        self._index_name = "chat_cache_idx"

    async def initialize(self) -> None:
        """
        Initialize Redis indices for vector search.

        Creates RediSearch index for semantic similarity.
        """
        try:
            # Create vector search index for semantic caching
            schema = (
                TextField("$.query", as_name="query"),
                TextField("$.agent_name", as_name="agent_name"),
                NumericField("$.hit_count", as_name="hit_count"),
                VectorField(
                    "$.embedding",
                    "FLAT",
                    {
                        "TYPE": "FLOAT32",
                        "DIM": 1536,  # OpenAI embedding dimension
                        "DISTANCE_METRIC": "COSINE",
                    },
                    as_name="embedding",
                ),
            )

            definition = IndexDefinition(
                prefix=[self._key_prefix],
                index_type=IndexType.JSON,
            )

            await self._redis.ft(self._index_name).create_index(
                schema,
                definition=definition,
            )

        except Exception:
            # Index may already exist
            pass

    async def get(self, key: str) -> Optional[CacheEntry]:
        """
        Get cached entry by key.

        Args:
            key: Cache key

        Returns:
            CacheEntry or None if not found or expired
        """
        full_key = self._key_prefix + key

        # Get from Redis
        data = await self._redis.get(full_key)
        if not data:
            await self._increment_stat("misses")
            return None

        # Deserialize
        entry_dict = json.loads(data)
        entry = self._dict_to_entry(entry_dict)

        # Check if expired
        if entry.is_expired():
            await self.delete(key)
            await self._increment_stat("misses")
            return None

        await self._increment_stat("hits")
        return entry

    async def set(
        self,
        key: str,
        entry: CacheEntry,
        ttl: Optional[timedelta] = None,
    ) -> bool:
        """
        Set cache entry with optional TTL.

        Args:
            key: Cache key
            entry: Cache entry to store
            ttl: Time-to-live (uses entry.ttl_seconds if None)

        Returns:
            True if successful
        """
        try:
            full_key = self._key_prefix + key

            # Serialize entry
            entry_dict = self._entry_to_dict(entry)
            data = json.dumps(entry_dict)

            # Determine TTL
            ttl_seconds = ttl.total_seconds() if ttl else entry.ttl_seconds

            # Set in Redis with TTL
            await self._redis.setex(
                full_key,
                int(ttl_seconds),
                data,
            )

            await self._increment_stat("total_entries")
            return True

        except Exception:
            return False

    async def delete(self, key: str) -> bool:
        """
        Delete cached entry.

        Args:
            key: Cache key

        Returns:
            True if deleted, False if not found
        """
        full_key = self._key_prefix + key
        deleted = await self._redis.delete(full_key)
        return deleted > 0

    async def exists(self, key: str) -> bool:
        """
        Check if key exists in cache.

        Args:
            key: Cache key

        Returns:
            True if exists and not expired
        """
        full_key = self._key_prefix + key
        exists = await self._redis.exists(full_key)
        return exists > 0

    async def find_similar(
        self,
        query_embedding: List[float],
        agent_name: str,
        threshold: float = 0.85,
        limit: int = 5,
    ) -> List[CacheEntry]:
        """
        Find semantically similar cached queries using vector search.

        Args:
            query_embedding: Query embedding vector
            agent_name: Agent name to filter by
            threshold: Similarity threshold (0.0 to 1.0)
            limit: Maximum number of results

        Returns:
            List of similar cache entries
        """
        try:
            # Convert embedding to bytes
            embedding_bytes = self._embedding_to_bytes(query_embedding)

            # Build RediSearch query
            query = (
                Query(f"@agent_name:{agent_name}")
                .return_fields("query", "response", "hit_count", "embedding")
                .sort_by("__embedding_score")
                .paging(0, limit)
                .dialect(2)
            )

            # Execute vector search
            results = await self._redis.ft(self._index_name).search(
                query,
                query_params={"embedding": embedding_bytes},
            )

            # Filter by similarity threshold and convert to entries
            entries = []
            for doc in results.docs:
                similarity = 1 - float(doc.__embedding_score)  # Convert distance to similarity
                if similarity >= threshold:
                    entry_dict = json.loads(doc.json)
                    entry = self._dict_to_entry(entry_dict)
                    entries.append(entry)

            return entries

        except Exception:
            return []

    async def increment_hit_count(self, key: str) -> int:
        """
        Increment cache hit counter.

        Args:
            key: Cache key

        Returns:
            New hit count
        """
        full_key = self._key_prefix + key

        # Get current entry
        entry = await self.get(key)
        if not entry:
            return 0

        # Increment hit count
        new_hit_count = entry.hit_count + 1

        # Update entry (preserve original)
        updated_entry = CacheEntry(
            cache_key=entry.cache_key,
            query=entry.query,
            response=entry.response,
            agent_name=entry.agent_name,
            conversation_context_hash=entry.conversation_context_hash,
            embedding=entry.embedding,
            hit_count=new_hit_count,
            ttl_seconds=entry.ttl_seconds,
            similarity_threshold=entry.similarity_threshold,
            created_at=entry.created_at,
            last_accessed_at=entry.last_accessed_at,
        )

        # Save updated entry
        await self.set(key, updated_entry)
        return new_hit_count

    async def get_statistics(self) -> CacheStatistics:
        """
        Get cache performance statistics.

        Returns:
            CacheStatistics with current metrics
        """
        # Get statistics from Redis hash
        stats = await self._redis.hgetall(self._stats_key)

        total_requests = int(stats.get(b"hits", 0)) + int(stats.get(b"misses", 0))
        hits = int(stats.get(b"hits", 0))
        misses = int(stats.get(b"misses", 0))

        hit_rate = hits / total_requests if total_requests > 0 else 0.0

        # Calculate response time savings (estimated)
        avg_cached_time_ms = 150  # Cached responses are ~150ms
        avg_uncached_time_ms = 2340  # Uncached are ~2.3s
        time_saved_ms = hits * (avg_uncached_time_ms - avg_cached_time_ms)

        # Estimate cost savings ($0.015 per uncached query)
        cost_saved_usd = hits * 0.015

        # Get memory usage
        memory_mb = await self.get_memory_usage_mb()

        # Get eviction count from Redis INFO
        info = await self._redis.info("stats")
        evictions = info.get("evicted_keys", 0)

        return CacheStatistics(
            total_requests=total_requests,
            cache_hits=hits,
            cache_misses=misses,
            hit_rate=hit_rate,
            avg_response_time_cached_ms=avg_cached_time_ms,
            avg_response_time_uncached_ms=avg_uncached_time_ms,
            time_saved_ms=time_saved_ms,
            cost_saved_usd=cost_saved_usd,
            memory_usage_mb=memory_mb,
            evictions=evictions,
        )

    async def clear_agent_cache(self, agent_name: str) -> int:
        """
        Clear all cache entries for a specific agent.

        Args:
            agent_name: Agent name

        Returns:
            Number of entries cleared
        """
        # Scan for keys matching agent pattern
        pattern = f"{self._key_prefix}*"
        cursor = 0
        deleted = 0

        while True:
            cursor, keys = await self._redis.scan(cursor, match=pattern, count=100)

            for key in keys:
                # Get entry and check agent name
                data = await self._redis.get(key)
                if data:
                    entry_dict = json.loads(data)
                    if entry_dict.get("agent_name") == agent_name:
                        await self._redis.delete(key)
                        deleted += 1

            if cursor == 0:
                break

        return deleted

    async def clear_expired(self) -> int:
        """
        Clear all expired cache entries.

        Redis handles this automatically with TTL, so this is a no-op.

        Returns:
            0 (Redis handles expiration automatically)
        """
        return 0

    async def clear_all(self) -> bool:
        """
        Clear all cache entries (use with caution).

        Returns:
            True if successful
        """
        try:
            # Delete all keys matching prefix
            pattern = f"{self._key_prefix}*"
            cursor = 0

            while True:
                cursor, keys = await self._redis.scan(cursor, match=pattern, count=100)
                if keys:
                    await self._redis.delete(*keys)
                if cursor == 0:
                    break

            # Reset statistics
            await self._redis.delete(self._stats_key)

            return True

        except Exception:
            return False

    async def get_memory_usage_mb(self) -> float:
        """
        Get current cache memory usage in MB.

        Returns:
            Memory usage in megabytes
        """
        # Get Redis memory info
        info = await self._redis.info("memory")
        used_memory_bytes = info.get("used_memory", 0)
        return used_memory_bytes / (1024 * 1024)

    # =========================================================================
    # HELPER METHODS
    # =========================================================================

    async def _increment_stat(self, stat_name: str) -> None:
        """Increment a statistics counter."""
        await self._redis.hincrby(self._stats_key, stat_name, 1)

    def _entry_to_dict(self, entry: CacheEntry) -> dict:
        """Convert CacheEntry to dictionary for serialization."""
        return {
            "cache_key": entry.cache_key,
            "query": entry.query,
            "response": entry.response,
            "agent_name": entry.agent_name,
            "conversation_context_hash": entry.conversation_context_hash,
            "embedding": entry.embedding,
            "hit_count": entry.hit_count,
            "ttl_seconds": entry.ttl_seconds,
            "similarity_threshold": entry.similarity_threshold,
            "created_at": entry.created_at.isoformat() if entry.created_at else None,
            "last_accessed_at": entry.last_accessed_at.isoformat()
            if entry.last_accessed_at
            else None,
        }

    def _dict_to_entry(self, entry_dict: dict) -> CacheEntry:
        """Convert dictionary to CacheEntry."""
        from datetime import datetime

        return CacheEntry(
            cache_key=entry_dict["cache_key"],
            query=entry_dict["query"],
            response=entry_dict["response"],
            agent_name=entry_dict["agent_name"],
            conversation_context_hash=entry_dict.get("conversation_context_hash"),
            embedding=entry_dict.get("embedding"),
            hit_count=entry_dict.get("hit_count", 0),
            ttl_seconds=entry_dict.get("ttl_seconds", 3600),
            similarity_threshold=entry_dict.get("similarity_threshold", 0.85),
            created_at=datetime.fromisoformat(entry_dict["created_at"])
            if entry_dict.get("created_at")
            else None,
            last_accessed_at=datetime.fromisoformat(entry_dict["last_accessed_at"])
            if entry_dict.get("last_accessed_at")
            else None,
        )

    def _embedding_to_bytes(self, embedding: List[float]) -> bytes:
        """Convert embedding vector to bytes for Redis."""
        import struct

        return struct.pack(f"{len(embedding)}f", *embedding)
