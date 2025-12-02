"""Agent Response Caching.

Caches agent responses to improve performance and reduce LLM API costs.

Features:
    - Redis-backed caching
    - TTL configuration
    - Query normalization
    - Cache invalidation
    - Statistics tracking
"""
import hashlib
import json
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
import logging

try:
    import redis.asyncio as aioredis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    aioredis = None


logger = logging.getLogger(__name__)


class AgentResponseCache:
    """
    Caches agent responses to improve performance.
    
    Uses Redis for distributed caching with configurable TTL.
    
    Usage:
        cache = AgentResponseCache(
            redis_url="redis://localhost:6379",
            ttl_seconds=3600,
        )
        await cache.initialize()
        
        # Check cache
        cached = await cache.get("user_query", agent_type="trading")
        if cached:
            return cached
        
        # Execute agent
        result = await agent.run(query)
        
        # Cache result
        await cache.set("user_query", result, agent_type="trading")
    """
    
    def __init__(
        self,
        redis_url: str = "redis://localhost:6379",
        ttl_seconds: int = 3600,  # 1 hour default
        key_prefix: str = "agno:cache:",
        enabled: bool = True,
    ):
        """
        Initialize cache.
        
        Args:
            redis_url: Redis connection URL
            ttl_seconds: Cache TTL in seconds
            key_prefix: Key prefix for namespacing
            enabled: Enable/disable caching
        """
        self.redis_url = redis_url
        self.ttl_seconds = ttl_seconds
        self.key_prefix = key_prefix
        self.enabled = enabled and REDIS_AVAILABLE
        
        self.redis: Optional[aioredis.Redis] = None
        self._stats = {
            "hits": 0,
            "misses": 0,
            "sets": 0,
            "errors": 0,
        }
        
        if not REDIS_AVAILABLE and enabled:
            logger.warning("Redis not available, caching disabled")
    
    async def initialize(self):
        """Initialize Redis connection."""
        if not self.enabled:
            return
        
        try:
            self.redis = await aioredis.from_url(
                self.redis_url,
                encoding="utf-8",
                decode_responses=True,
            )
            await self.redis.ping()
            logger.info(f"Agent cache initialized (TTL: {self.ttl_seconds}s)")
        except Exception as e:
            logger.error(f"Failed to initialize cache: {e}")
            self.enabled = False
    
    async def close(self):
        """Close Redis connection."""
        if self.redis:
            await self.redis.close()
    
    def _normalize_query(self, query: str) -> str:
        """
        Normalize query for consistent caching.
        
        Args:
            query: Raw query string
        
        Returns:
            Normalized query
        """
        # Lowercase, strip whitespace, remove extra spaces
        normalized = " ".join(query.lower().strip().split())
        return normalized
    
    def _generate_key(
        self,
        query: str,
        agent_type: Optional[str] = None,
        user_id: Optional[str] = None,
    ) -> str:
        """
        Generate cache key.
        
        Args:
            query: Query string
            agent_type: Agent type (optional)
            user_id: User ID for user-specific caching (optional)
        
        Returns:
            Cache key
        """
        # Normalize query
        normalized = self._normalize_query(query)
        
        # Create hash components
        components = [normalized]
        if agent_type:
            components.append(agent_type)
        if user_id:
            components.append(user_id)
        
        # Generate hash
        hash_input = "|".join(components)
        hash_value = hashlib.sha256(hash_input.encode()).hexdigest()[:16]
        
        # Build key
        key_parts = [self.key_prefix, hash_value]
        if agent_type:
            key_parts.insert(1, agent_type)
        
        return ":".join(key_parts)
    
    async def get(
        self,
        query: str,
        agent_type: Optional[str] = None,
        user_id: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Get cached response.
        
        Args:
            query: Query string
            agent_type: Agent type (optional)
            user_id: User ID (optional)
        
        Returns:
            Cached response or None
        """
        if not self.enabled or not self.redis:
            return None
        
        try:
            key = self._generate_key(query, agent_type, user_id)
            value = await self.redis.get(key)
            
            if value:
                self._stats["hits"] += 1
                logger.debug(f"Cache hit: {key}")
                return json.loads(value)
            else:
                self._stats["misses"] += 1
                logger.debug(f"Cache miss: {key}")
                return None
        
        except Exception as e:
            logger.error(f"Cache get error: {e}")
            self._stats["errors"] += 1
            return None
    
    async def set(
        self,
        query: str,
        response: Dict[str, Any],
        agent_type: Optional[str] = None,
        user_id: Optional[str] = None,
        ttl_seconds: Optional[int] = None,
    ):
        """
        Cache response.
        
        Args:
            query: Query string
            response: Response to cache
            agent_type: Agent type (optional)
            user_id: User ID (optional)
            ttl_seconds: Override default TTL (optional)
        """
        if not self.enabled or not self.redis:
            return
        
        try:
            key = self._generate_key(query, agent_type, user_id)
            value = json.dumps(response)
            ttl = ttl_seconds or self.ttl_seconds
            
            await self.redis.setex(key, ttl, value)
            self._stats["sets"] += 1
            logger.debug(f"Cache set: {key} (TTL: {ttl}s)")
        
        except Exception as e:
            logger.error(f"Cache set error: {e}")
            self._stats["errors"] += 1
    
    async def delete(
        self,
        query: str,
        agent_type: Optional[str] = None,
        user_id: Optional[str] = None,
    ):
        """
        Delete cached response.
        
        Args:
            query: Query string
            agent_type: Agent type (optional)
            user_id: User ID (optional)
        """
        if not self.enabled or not self.redis:
            return
        
        try:
            key = self._generate_key(query, agent_type, user_id)
            await self.redis.delete(key)
            logger.debug(f"Cache deleted: {key}")
        
        except Exception as e:
            logger.error(f"Cache delete error: {e}")
            self._stats["errors"] += 1
    
    async def clear(self, pattern: Optional[str] = None):
        """
        Clear cache entries matching pattern.
        
        Args:
            pattern: Key pattern (e.g., "agno:cache:trading:*")
                    None = clear all
        """
        if not self.enabled or not self.redis:
            return
        
        try:
            pattern = pattern or f"{self.key_prefix}*"
            
            # Scan and delete in batches
            cursor = 0
            deleted = 0
            
            while True:
                cursor, keys = await self.redis.scan(cursor, match=pattern, count=100)
                if keys:
                    await self.redis.delete(*keys)
                    deleted += len(keys)
                
                if cursor == 0:
                    break
            
            logger.info(f"Cache cleared: {deleted} keys deleted")
        
        except Exception as e:
            logger.error(f"Cache clear error: {e}")
            self._stats["errors"] += 1
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get cache statistics.
        
        Returns:
            Statistics dictionary
        """
        total_requests = self._stats["hits"] + self._stats["misses"]
        hit_rate = (
            self._stats["hits"] / total_requests * 100
            if total_requests > 0
            else 0
        )
        
        return {
            "enabled": self.enabled,
            "hits": self._stats["hits"],
            "misses": self._stats["misses"],
            "sets": self._stats["sets"],
            "errors": self._stats["errors"],
            "hit_rate": round(hit_rate, 2),
            "total_requests": total_requests,
        }
    
    def reset_statistics(self):
        """Reset statistics counters."""
        self._stats = {
            "hits": 0,
            "misses": 0,
            "sets": 0,
            "errors": 0,
        }


# Global cache instance
_cache: Optional[AgentResponseCache] = None


def get_cache() -> AgentResponseCache:
    """
    Get global cache instance.
    
    Returns:
        AgentResponseCache instance
    """
    global _cache
    if _cache is None:
        _cache = AgentResponseCache()
    return _cache


async def initialize_cache(
    redis_url: str = "redis://localhost:6379",
    ttl_seconds: int = 3600,
    enabled: bool = True,
):
    """
    Initialize global cache.
    
    Args:
        redis_url: Redis connection URL
        ttl_seconds: Cache TTL
        enabled: Enable caching
    """
    global _cache
    _cache = AgentResponseCache(
        redis_url=redis_url,
        ttl_seconds=ttl_seconds,
        enabled=enabled,
    )
    await _cache.initialize()
