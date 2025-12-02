"""
Graph Query Cache

Redis-based caching for GraphRAG queries.
"""

import json
import hashlib
from typing import Any, Optional, List
from datetime import timedelta
import redis.asyncio as aioredis
import logging

logger = logging.getLogger(__name__)


class GraphQueryCache:
    """
    Redis cache for graph queries.
    
    Caches:
    - Hybrid search results
    - Similar protocol results
    - Protocol context
    - Analytics data
    """
    
    def __init__(
        self,
        redis_client: aioredis.Redis,
        default_ttl: int = 300,  # 5 minutes
    ):
        """
        Initialize graph query cache.
        
        Args:
            redis_client: Redis async client
            default_ttl: Default TTL in seconds
        """
        self._redis = redis_client
        self._default_ttl = default_ttl
        self._prefix = "graph:"
    
    def _make_key(self, operation: str, **params) -> str:
        """
        Generate cache key from operation and parameters.
        
        Args:
            operation: Operation name
            **params: Parameters for the operation
            
        Returns:
            Cache key
        """
        # Sort params for consistent keys
        sorted_params = sorted(params.items())
        param_str = json.dumps(sorted_params, sort_keys=True)
        
        # Hash for shorter keys
        param_hash = hashlib.md5(param_str.encode()).hexdigest()
        
        return f"{self._prefix}{operation}:{param_hash}"
    
    async def get_hybrid_search(
        self,
        query: str,
        limit: int,
        include_risks: bool,
        include_dependencies: bool,
        similarity_threshold: float,
    ) -> Optional[List[dict]]:
        """Get cached hybrid search results"""
        
        key = self._make_key(
            "hybrid_search",
            query=query,
            limit=limit,
            include_risks=include_risks,
            include_dependencies=include_dependencies,
            similarity_threshold=similarity_threshold,
        )
        
        try:
            cached = await self._redis.get(key)
            if cached:
                logger.debug(f"Cache HIT: hybrid_search({query})")
                return json.loads(cached)
            
            logger.debug(f"Cache MISS: hybrid_search({query})")
            return None
        except Exception as e:
            logger.error(f"Cache get error: {e}")
            return None
    
    async def set_hybrid_search(
        self,
        query: str,
        limit: int,
        include_risks: bool,
        include_dependencies: bool,
        similarity_threshold: float,
        results: List[dict],
        ttl: Optional[int] = None,
    ) -> None:
        """Cache hybrid search results"""
        
        key = self._make_key(
            "hybrid_search",
            query=query,
            limit=limit,
            include_risks=include_risks,
            include_dependencies=include_dependencies,
            similarity_threshold=similarity_threshold,
        )
        
        try:
            ttl = ttl or self._default_ttl
            await self._redis.setex(
                key,
                ttl,
                json.dumps(results),
            )
            logger.debug(f"Cache SET: hybrid_search({query}) TTL={ttl}s")
        except Exception as e:
            logger.error(f"Cache set error: {e}")
    
    async def get_similar_protocols(
        self,
        protocol_id: str,
        limit: int,
    ) -> Optional[List[dict]]:
        """Get cached similar protocols"""
        
        key = self._make_key(
            "similar_protocols",
            protocol_id=protocol_id,
            limit=limit,
        )
        
        try:
            cached = await self._redis.get(key)
            if cached:
                logger.debug(f"Cache HIT: similar_protocols({protocol_id})")
                return json.loads(cached)
            
            logger.debug(f"Cache MISS: similar_protocols({protocol_id})")
            return None
        except Exception as e:
            logger.error(f"Cache get error: {e}")
            return None
    
    async def set_similar_protocols(
        self,
        protocol_id: str,
        limit: int,
        results: List[dict],
        ttl: Optional[int] = None,
    ) -> None:
        """Cache similar protocols"""
        
        key = self._make_key(
            "similar_protocols",
            protocol_id=protocol_id,
            limit=limit,
        )
        
        try:
            ttl = ttl or self._default_ttl
            await self._redis.setex(
                key,
                ttl,
                json.dumps(results),
            )
            logger.debug(f"Cache SET: similar_protocols({protocol_id}) TTL={ttl}s")
        except Exception as e:
            logger.error(f"Cache set error: {e}")
    
    async def get_analytics(self, analytics_type: str) -> Optional[dict]:
        """Get cached analytics"""
        
        key = self._make_key("analytics", type=analytics_type)
        
        try:
            cached = await self._redis.get(key)
            if cached:
                logger.debug(f"Cache HIT: analytics({analytics_type})")
                return json.loads(cached)
            
            logger.debug(f"Cache MISS: analytics({analytics_type})")
            return None
        except Exception as e:
            logger.error(f"Cache get error: {e}")
            return None
    
    async def set_analytics(
        self,
        analytics_type: str,
        data: dict,
        ttl: Optional[int] = None,
    ) -> None:
        """Cache analytics data"""
        
        key = self._make_key("analytics", type=analytics_type)
        
        try:
            # Analytics can be cached longer (15 minutes)
            ttl = ttl or 900
            await self._redis.setex(
                key,
                ttl,
                json.dumps(data),
            )
            logger.debug(f"Cache SET: analytics({analytics_type}) TTL={ttl}s")
        except Exception as e:
            logger.error(f"Cache set error: {e}")
    
    async def invalidate_protocol(self, protocol_id: str) -> None:
        """
        Invalidate all caches for a protocol.
        
        Call this when protocol data changes.
        """
        
        pattern = f"{self._prefix}*{protocol_id}*"
        
        try:
            cursor = 0
            deleted = 0
            
            while True:
                cursor, keys = await self._redis.scan(
                    cursor,
                    match=pattern,
                    count=100,
                )
                
                if keys:
                    await self._redis.delete(*keys)
                    deleted += len(keys)
                
                if cursor == 0:
                    break
            
            logger.info(f"Invalidated {deleted} cache keys for protocol {protocol_id}")
        except Exception as e:
            logger.error(f"Cache invalidation error: {e}")
    
    async def clear_all(self) -> None:
        """Clear all graph caches"""
        
        pattern = f"{self._prefix}*"
        
        try:
            cursor = 0
            deleted = 0
            
            while True:
                cursor, keys = await self._redis.scan(
                    cursor,
                    match=pattern,
                    count=100,
                )
                
                if keys:
                    await self._redis.delete(*keys)
                    deleted += len(keys)
                
                if cursor == 0:
                    break
            
            logger.info(f"Cleared {deleted} graph cache keys")
        except Exception as e:
            logger.error(f"Cache clear error: {e}")
    
    async def get_stats(self) -> dict:
        """Get cache statistics"""
        
        try:
            info = await self._redis.info("stats")
            
            # Count graph cache keys
            pattern = f"{self._prefix}*"
            cursor = 0
            key_count = 0
            
            while True:
                cursor, keys = await self._redis.scan(
                    cursor,
                    match=pattern,
                    count=100,
                )
                key_count += len(keys)
                
                if cursor == 0:
                    break
            
            return {
                "graph_cache_keys": key_count,
                "total_keys": info.get("db0", {}).get("keys", 0),
                "hits": info.get("keyspace_hits", 0),
                "misses": info.get("keyspace_misses", 0),
                "hit_rate": (
                    info.get("keyspace_hits", 0) /
                    (info.get("keyspace_hits", 0) + info.get("keyspace_misses", 1))
                ) if info.get("keyspace_hits", 0) > 0 else 0.0,
            }
        except Exception as e:
            logger.error(f"Cache stats error: {e}")
            return {}
