"""
Redis caching layer for DeFi data.
"""

import json
import logging
from typing import Any, Optional, Dict
from datetime import timedelta

import redis.asyncio as aioredis

logger = logging.getLogger(__name__)


class RedisCache:
    """
    Redis-based caching layer for DeFi data.

    Provides intelligent caching with TTL management for:
    - Token prices
    - Protocol data
    - Swap quotes
    - User preferences
    """

    # Cache TTL configurations (in seconds)
    TTL_CONFIG = {
        "price": 30,  # Token prices: 30s
        "quote": 60,  # Swap quotes: 1min
        "protocol": 300,  # Protocol data: 5min
        "wallet": 60,  # Wallet balances: 1min
        "market": 120,  # Market overview: 2min
        "yield": 600,  # Yield data: 10min
        "context": 3600,  # User context: 1hr
        "default": 300,  # Default: 5min
    }

    def __init__(self, redis_url: str = "redis://localhost:6379"):
        """
        Initialize Redis cache.

        Args:
            redis_url: Redis connection URL
        """
        self.redis_url = redis_url
        self._client: Optional[aioredis.Redis] = None

    async def connect(self) -> None:
        """Establish Redis connection."""
        self._client = await aioredis.from_url(
            self.redis_url,
            encoding="utf-8",
            decode_responses=True,
        )
        logger.info("Redis cache connected")

    async def disconnect(self) -> None:
        """Close Redis connection."""
        if self._client:
            await self._client.close()
            logger.info("Redis cache disconnected")

    async def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache.

        Args:
            key: Cache key

        Returns:
            Cached value or None if not found
        """
        if not self._client:
            await self.connect()

        try:
            value = await self._client.get(key)
            if value:
                logger.debug(f"Cache HIT: {key}")
                return json.loads(value)

            logger.debug(f"Cache MISS: {key}")
            return None

        except Exception as e:
            logger.error(f"Cache get error for {key}: {e}")
            return None

    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None,
        category: str = "default",
    ) -> None:
        """
        Set value in cache.

        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds (overrides category)
            category: Cache category for TTL lookup
        """
        if not self._client:
            await self.connect()

        try:
            # Determine TTL
            if ttl is None:
                ttl = self.TTL_CONFIG.get(category, self.TTL_CONFIG["default"])

            # Store as JSON
            serialized = json.dumps(value)
            await self._client.setex(key, ttl, serialized)

            logger.debug(f"Cache SET: {key} (TTL: {ttl}s)")

        except Exception as e:
            logger.error(f"Cache set error for {key}: {e}")

    async def delete(self, key: str) -> None:
        """
        Delete value from cache.

        Args:
            key: Cache key
        """
        if not self._client:
            await self.connect()

        try:
            await self._client.delete(key)
            logger.debug(f"Cache DELETE: {key}")

        except Exception as e:
            logger.error(f"Cache delete error for {key}: {e}")

    async def delete_pattern(self, pattern: str) -> None:
        """
        Delete all keys matching pattern.

        Args:
            pattern: Key pattern (e.g., "price:*")
        """
        if not self._client:
            await self.connect()

        try:
            keys = await self._client.keys(pattern)
            if keys:
                await self._client.delete(*keys)
                logger.info(f"Cache DELETE pattern: {pattern} ({len(keys)} keys)")

        except Exception as e:
            logger.error(f"Cache delete pattern error for {pattern}: {e}")

    async def exists(self, key: str) -> bool:
        """
        Check if key exists in cache.

        Args:
            key: Cache key

        Returns:
            True if exists
        """
        if not self._client:
            await self.connect()

        try:
            return await self._client.exists(key) > 0

        except Exception as e:
            logger.error(f"Cache exists error for {key}: {e}")
            return False

    def make_key(self, *parts: str) -> str:
        """
        Create cache key from parts.

        Args:
            parts: Key components

        Returns:
            Formatted cache key

        Example:
            make_key("price", "BTC", "USD") -> "price:BTC:USD"
        """
        return ":".join(str(p) for p in parts)


# Global cache instance
_cache: Optional[RedisCache] = None


def get_cache() -> RedisCache:
    """Get global cache instance."""
    global _cache
    if _cache is None:
        _cache = RedisCache()
    return _cache
