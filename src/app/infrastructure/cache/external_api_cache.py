"""
External API Cache.

Simple in-memory cache for external API responses.
"""

import logging
import time
from typing import Any

logger = logging.getLogger(__name__)


class ExternalAPICache:
    """
    Simple in-memory cache for external API responses.

    Provides TTL-based caching for expensive API calls to reduce
    rate limiting and improve response times.
    """

    def __init__(self, default_ttl: int = 300) -> None:
        """
        Initialize cache.

        Args:
            default_ttl: Default time-to-live in seconds (5 min).
        """
        self._cache: dict[str, tuple[Any, float]] = {}
        self._default_ttl = default_ttl

    def get(self, key: str) -> Any | None:
        """
        Get value from cache if not expired.

        Args:
            key: Cache key.

        Returns:
            Cached value or None if expired/missing.
        """
        if key not in self._cache:
            return None

        value, expiry = self._cache[key]
        if time.time() > expiry:
            del self._cache[key]
            return None

        return value

    def set(self, key: str, value: Any, ttl: int | None = None) -> None:
        """
        Store value in cache with TTL.

        Args:
            key: Cache key.
            value: Value to cache.
            ttl: Time-to-live in seconds (optional).
        """
        expiry = time.time() + (ttl or self._default_ttl)
        self._cache[key] = (value, expiry)

    def delete(self, key: str) -> bool:
        """
        Remove key from cache.

        Args:
            key: Cache key.

        Returns:
            True if key was deleted, False if not found.
        """
        if key in self._cache:
            del self._cache[key]
            return True
        return False

    def clear(self) -> None:
        """Clear all cached values."""
        self._cache.clear()

    def cleanup_expired(self) -> int:
        """
        Remove all expired entries.

        Returns:
            Number of entries removed.
        """
        now = time.time()
        expired = [k for k, (_, exp) in self._cache.items() if now > exp]
        for key in expired:
            del self._cache[key]
        return len(expired)
