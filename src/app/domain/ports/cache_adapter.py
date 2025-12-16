"""
Cache adapter port.

Domain-defined interface for caching systems (Redis, Memcached, etc.).
"""

from abc import ABC, abstractmethod
from typing import Optional, List
from datetime import timedelta

from app.domain.value_objects.chat.performance import CacheEntry, CacheStatistics


class CacheAdapter(ABC):
    """
    Port for cache systems.

    Abstracts integration with caching backends (Redis, Memcached,
    DynamoDB, etc.) for language-agnostic business logic.
    """

    @abstractmethod
    async def get(self, key: str) -> Optional[CacheEntry]:
        """
        Get cached entry by key.

        Args:
            key: Cache key

        Returns:
            CacheEntry or None if not found or expired
        """
        pass

    @abstractmethod
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
            True if successful, False otherwise
        """
        pass

    @abstractmethod
    async def delete(self, key: str) -> bool:
        """
        Delete cached entry.

        Args:
            key: Cache key

        Returns:
            True if deleted, False if not found
        """
        pass

    @abstractmethod
    async def exists(self, key: str) -> bool:
        """
        Check if key exists in cache.

        Args:
            key: Cache key

        Returns:
            True if exists and not expired, False otherwise
        """
        pass

    @abstractmethod
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
        pass

    @abstractmethod
    async def increment_hit_count(self, key: str) -> int:
        """
        Increment cache hit counter.

        Args:
            key: Cache key

        Returns:
            New hit count
        """
        pass

    @abstractmethod
    async def get_statistics(self) -> CacheStatistics:
        """
        Get cache performance statistics.

        Returns:
            CacheStatistics with current metrics
        """
        pass

    @abstractmethod
    async def clear_agent_cache(self, agent_name: str) -> int:
        """
        Clear all cache entries for a specific agent.

        Args:
            agent_name: Agent name

        Returns:
            Number of entries cleared
        """
        pass

    @abstractmethod
    async def clear_expired(self) -> int:
        """
        Clear all expired cache entries.

        Returns:
            Number of entries cleared
        """
        pass

    @abstractmethod
    async def clear_all(self) -> bool:
        """
        Clear all cache entries (use with caution).

        Returns:
            True if successful
        """
        pass

    @abstractmethod
    async def get_memory_usage_mb(self) -> float:
        """
        Get current cache memory usage in MB.

        Returns:
            Memory usage in megabytes
        """
        pass
