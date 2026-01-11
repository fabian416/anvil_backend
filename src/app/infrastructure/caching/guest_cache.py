"""
Guest chat caching layer for Hunter AI responses and user context.

Extends RedisCache with guest-specific TTL configurations and helper methods
for caching Hunter AI responses, user context, and rate limiting data.
"""

import logging
from typing import Any, Optional, Dict, List
from datetime import datetime

from .redis_cache import RedisCache

logger = logging.getLogger(__name__)


class GuestCache:
    """
    Guest-specific caching layer for Hunter AI and user context.

    Provides intelligent caching with optimized TTLs for:
    - Hunter AI responses (sentiment, signals, predictions, etc.)
    - User conversation context
    - Rate limiting counters
    - Popular token data
    """

    # Extended TTL configurations for guest system (in seconds)
    GUEST_TTL_CONFIG = {
        # Hunter AI response caching
        "hunter:sentiment": 300,           # Sentiment analysis: 5min
        "hunter:trading_signals": 300,     # Trading signals: 5min
        "hunter:patterns": 600,            # Pattern detection: 10min
        "hunter:portfolio": 600,           # Portfolio optimization: 10min
        "hunter:price_prediction": 300,    # Price predictions: 5min
        "hunter:risk_signals": 300,        # Risk signals: 5min

        # User context and session data
        "guest:context": 3600,             # User conversation context: 1hr
        "guest:preferences": 3600,         # Language/token preferences: 1hr
        "guest:session": 1800,             # Session state: 30min

        # Rate limiting
        "ratelimit:counter": 3600,         # Rate limit counters: 1hr
        "ratelimit:blocked": 86400,        # Blocked user cache: 24hr

        # Token data (pre-warmed)
        "token:price": 60,                 # Current prices: 1min
        "token:metadata": 3600,            # Token metadata: 1hr
        "token:trending": 300,             # Trending tokens: 5min
    }

    # Popular tokens to pre-warm on startup
    POPULAR_TOKENS = ["BTC", "ETH", "SOL", "USDT", "BNB", "USDC", "XRP", "ADA", "DOGE", "MATIC"]

    # Supported languages for cache warming
    SUPPORTED_LANGUAGES = ["en", "es", "pt", "zh"]

    def __init__(self, redis_cache: Optional[RedisCache] = None):
        """
        Initialize guest cache.

        Args:
            redis_cache: Optional RedisCache instance (creates new if None)
        """
        self.cache = redis_cache or RedisCache()

    # ========== Hunter AI Response Caching ==========

    async def get_hunter_response(
        self,
        intent: str,
        token: str,
        language: str = "en"
    ) -> Optional[Dict[str, Any]]:
        """
        Get cached Hunter AI response.

        Args:
            intent: Hunter AI intent (sentiment, trading_signals, etc.)
            token: Token symbol (BTC, ETH, etc.)
            language: Language code

        Returns:
            Cached response or None
        """
        key = self.cache.make_key("hunter", intent, token, language)
        return await self.cache.get(key)

    async def set_hunter_response(
        self,
        intent: str,
        token: str,
        language: str,
        response: Dict[str, Any],
    ) -> None:
        """
        Cache Hunter AI response.

        Args:
            intent: Hunter AI intent
            token: Token symbol
            language: Language code
            response: Full response to cache
        """
        key = self.cache.make_key("hunter", intent, token, language)
        ttl_key = f"hunter:{intent}"
        ttl = self.GUEST_TTL_CONFIG.get(ttl_key, 300)  # Default 5min

        await self.cache.set(key, response, ttl=ttl)
        logger.debug(f"Cached Hunter AI response: {intent}/{token}/{language} (TTL: {ttl}s)")

    async def invalidate_hunter_response(
        self,
        intent: Optional[str] = None,
        token: Optional[str] = None,
    ) -> None:
        """
        Invalidate Hunter AI cache entries.

        Args:
            intent: Specific intent to invalidate (all if None)
            token: Specific token to invalidate (all if None)
        """
        if intent and token:
            # Invalidate all languages for specific intent/token
            pattern = self.cache.make_key("hunter", intent, token, "*")
        elif intent:
            # Invalidate all tokens for specific intent
            pattern = self.cache.make_key("hunter", intent, "*")
        elif token:
            # Invalidate all intents for specific token
            pattern = self.cache.make_key("hunter", "*", token, "*")
        else:
            # Invalidate all Hunter AI cache
            pattern = self.cache.make_key("hunter", "*")

        await self.cache.delete_pattern(pattern)

    # ========== User Context Caching ==========

    async def get_user_context(self, ip_address: str) -> Optional[Dict[str, Any]]:
        """
        Get cached user context.

        Args:
            ip_address: User's IP address

        Returns:
            Cached context or None
        """
        key = self.cache.make_key("guest", "context", ip_address)
        return await self.cache.get(key)

    async def set_user_context(
        self,
        ip_address: str,
        context: Dict[str, Any],
    ) -> None:
        """
        Cache user context.

        Args:
            ip_address: User's IP address
            context: Context data (recent tokens, language, etc.)
        """
        key = self.cache.make_key("guest", "context", ip_address)
        ttl = self.GUEST_TTL_CONFIG["guest:context"]

        # Add timestamp
        context["cached_at"] = datetime.utcnow().isoformat()

        await self.cache.set(key, context, ttl=ttl)

    async def update_user_context(
        self,
        ip_address: str,
        updates: Dict[str, Any],
    ) -> None:
        """
        Update specific fields in user context.

        Args:
            ip_address: User's IP address
            updates: Fields to update
        """
        # Get existing context
        context = await self.get_user_context(ip_address) or {}

        # Merge updates
        context.update(updates)

        # Save back
        await self.set_user_context(ip_address, context)

    # ========== Rate Limiting ==========

    async def get_rate_limit_count(self, ip_address: str) -> int:
        """
        Get current rate limit count for IP.

        Args:
            ip_address: User's IP address

        Returns:
            Current message count
        """
        key = self.cache.make_key("ratelimit", "counter", ip_address)
        count = await self.cache.get(key)
        return count if count is not None else 0

    async def increment_rate_limit(self, ip_address: str) -> int:
        """
        Increment rate limit counter.

        Args:
            ip_address: User's IP address

        Returns:
            New count
        """
        if not self.cache._client:
            await self.cache.connect()

        key = self.cache.make_key("ratelimit", "counter", ip_address)
        ttl = self.GUEST_TTL_CONFIG["ratelimit:counter"]

        # Atomic increment with TTL
        count = await self.cache._client.incr(key)
        if count == 1:
            # First increment, set TTL
            await self.cache._client.expire(key, ttl)

        return count

    async def reset_rate_limit(self, ip_address: str) -> None:
        """
        Reset rate limit counter for IP.

        Args:
            ip_address: User's IP address
        """
        key = self.cache.make_key("ratelimit", "counter", ip_address)
        await self.cache.delete(key)

    async def is_user_blocked(self, ip_address: str) -> bool:
        """
        Check if user is blocked in cache.

        Args:
            ip_address: User's IP address

        Returns:
            True if blocked
        """
        key = self.cache.make_key("ratelimit", "blocked", ip_address)
        return await self.cache.exists(key)

    async def block_user(self, ip_address: str, duration: int = 86400) -> None:
        """
        Block user in cache.

        Args:
            ip_address: User's IP address
            duration: Block duration in seconds (default 24hr)
        """
        key = self.cache.make_key("ratelimit", "blocked", ip_address)
        await self.cache.set(key, {"blocked_at": datetime.utcnow().isoformat()}, ttl=duration)

    # ========== Token Data Caching ==========

    async def get_token_price(self, token: str) -> Optional[float]:
        """
        Get cached token price.

        Args:
            token: Token symbol

        Returns:
            Price or None
        """
        key = self.cache.make_key("token", "price", token)
        data = await self.cache.get(key)
        return data.get("price") if data else None

    async def set_token_price(self, token: str, price: float) -> None:
        """
        Cache token price.

        Args:
            token: Token symbol
            price: Current price
        """
        key = self.cache.make_key("token", "price", token)
        ttl = self.GUEST_TTL_CONFIG["token:price"]

        data = {
            "price": price,
            "fetched_at": datetime.utcnow().isoformat(),
        }

        await self.cache.set(key, data, ttl=ttl)

    # ========== Cache Warming ==========

    async def warm_cache(self) -> Dict[str, int]:
        """
        Pre-warm cache with popular tokens and common queries.

        This should be called on application startup to populate
        cache with frequently accessed data.

        Returns:
            Statistics of warmed entries
        """
        logger.info("Starting cache warming for guest system...")

        stats = {
            "tokens_warmed": 0,
            "hunter_responses_warmed": 0,
            "errors": 0,
        }

        # Note: Actual data fetching would be done by calling
        # the appropriate services. This is a placeholder structure.
        # In practice, you'd inject the services needed to fetch
        # real data here.

        logger.info(f"Cache warming complete: {stats}")
        return stats

    # ========== Cache Statistics ==========

    async def get_cache_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.

        Returns:
            Cache statistics including hit rates, memory usage
        """
        if not self.cache._client:
            await self.cache.connect()

        try:
            # Get Redis INFO
            info = await self.cache._client.info("stats")

            stats = {
                "total_keys": await self.cache._client.dbsize(),
                "hits": info.get("keyspace_hits", 0),
                "misses": info.get("keyspace_misses", 0),
                "hit_rate": 0.0,
            }

            # Calculate hit rate
            total_requests = stats["hits"] + stats["misses"]
            if total_requests > 0:
                stats["hit_rate"] = (stats["hits"] / total_requests) * 100

            return stats

        except Exception as e:
            logger.error(f"Error getting cache stats: {e}")
            return {}

    async def clear_guest_cache(self) -> None:
        """Clear all guest-related cache entries."""
        patterns = [
            "hunter:*",
            "guest:*",
            "ratelimit:*",
            "token:*",
        ]

        for pattern in patterns:
            await self.cache.delete_pattern(pattern)

        logger.info("Guest cache cleared")


# Global guest cache instance
_guest_cache: Optional[GuestCache] = None


def get_guest_cache() -> GuestCache:
    """Get global guest cache instance."""
    global _guest_cache
    if _guest_cache is None:
        _guest_cache = GuestCache()
    return _guest_cache
