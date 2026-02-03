"""
Caching decorators for functions.
"""

import functools
import logging
from typing import Callable, Any, Optional

from app.infrastructure.caching.redis_cache import get_cache

logger = logging.getLogger(__name__)


def cached(
    category: str = "default",
    ttl: Optional[int] = None,
    key_prefix: Optional[str] = None,
):
    """
    Cache function results in Redis.

    Args:
        category: Cache category for TTL
        ttl: Override TTL in seconds
        key_prefix: Prefix for cache key

    Example:
        @cached(category="price", ttl=60)
        async def get_token_price(token: str):
            return await fetch_price(token)
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            cache = get_cache()

            # Build cache key from function name and arguments
            key_parts = [key_prefix or func.__name__]

            # Add positional args
            for arg in args:
                if isinstance(arg, (str, int, float)):
                    key_parts.append(str(arg))

            # Add keyword args
            for k, v in sorted(kwargs.items()):
                if isinstance(v, (str, int, float)):
                    key_parts.append(f"{k}:{v}")

            cache_key = cache.make_key(*key_parts)

            # Try to get from cache
            cached_value = await cache.get(cache_key)
            if cached_value is not None:
                logger.debug(f"Cache hit for {func.__name__}")
                return cached_value

            # Call function
            result = await func(*args, **kwargs)

            # Cache result
            await cache.set(cache_key, result, ttl=ttl, category=category)

            return result

        return wrapper

    return decorator


def invalidate_cache(pattern: str):
    """
    Invalidate cache entries matching pattern.

    Args:
        pattern: Cache key pattern

    Example:
        @invalidate_cache("price:BTC:*")
        async def update_btc_price():
            ...
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            result = await func(*args, **kwargs)

            # Invalidate cache
            cache = get_cache()
            await cache.delete_pattern(pattern)
            logger.info(f"Invalidated cache pattern: {pattern}")

            return result

        return wrapper

    return decorator
