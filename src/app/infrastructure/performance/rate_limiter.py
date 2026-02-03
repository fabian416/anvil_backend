"""
Rate limiting for API endpoints and external calls.
"""

import logging
import time
from typing import Dict, Optional
from datetime import datetime, timedelta
from collections import defaultdict

logger = logging.getLogger(__name__)


class RateLimiter:
    """
    Token bucket rate limiter.

    Implements rate limiting for:
    - API endpoints (per user)
    - External API calls (per provider)
    - Database operations (per table)
    """

    def __init__(self):
        """Initialize rate limiter."""
        # Store buckets: key -> (tokens, last_refill_time)
        self._buckets: Dict[str, tuple[float, float]] = {}

        # Configuration: key -> (max_tokens, refill_rate_per_second)
        self._config: Dict[str, tuple[int, float]] = {}

    def configure(
        self,
        key: str,
        max_tokens: int,
        refill_rate: float,
    ) -> None:
        """
        Configure rate limit for a key.

        Args:
            key: Identifier (e.g., "user:123", "api:coingecko")
            max_tokens: Maximum tokens in bucket
            refill_rate: Tokens refilled per second
        """
        self._config[key] = (max_tokens, refill_rate)
        self._buckets[key] = (max_tokens, time.time())

    async def acquire(
        self,
        key: str,
        tokens: int = 1,
        timeout: float = 5.0,
    ) -> bool:
        """
        Acquire tokens from bucket.

        Args:
            key: Identifier
            tokens: Number of tokens to consume
            timeout: Max wait time in seconds

        Returns:
            True if acquired, False if timeout
        """
        # Get or create bucket
        if key not in self._config:
            # Default: 60 requests per minute
            self.configure(key, max_tokens=60, refill_rate=1.0)

        max_tokens, refill_rate = self._config[key]

        start_time = time.time()

        while True:
            # Refill bucket
            current_tokens, last_refill = self._buckets.get(
                key, (max_tokens, time.time())
            )

            now = time.time()
            time_passed = now - last_refill
            refill_amount = time_passed * refill_rate

            current_tokens = min(max_tokens, current_tokens + refill_amount)

            # Try to consume tokens
            if current_tokens >= tokens:
                self._buckets[key] = (current_tokens - tokens, now)
                return True

            # Check timeout
            if time.time() - start_time >= timeout:
                logger.warning(f"Rate limit timeout for {key}")
                return False

            # Wait for refill
            wait_time = (tokens - current_tokens) / refill_rate
            time.sleep(min(wait_time, 0.1))

    def get_remaining(self, key: str) -> float:
        """
        Get remaining tokens for key.

        Args:
            key: Identifier

        Returns:
            Number of available tokens
        """
        if key not in self._buckets:
            return 0.0

        current_tokens, last_refill = self._buckets[key]
        max_tokens, refill_rate = self._config.get(key, (60, 1.0))

        # Calculate current tokens with refill
        now = time.time()
        time_passed = now - last_refill
        refill_amount = time_passed * refill_rate

        return min(max_tokens, current_tokens + refill_amount)


# Global rate limiter
_limiter: Optional[RateLimiter] = None


def get_rate_limiter() -> RateLimiter:
    """Get global rate limiter instance."""
    global _limiter
    if _limiter is None:
        _limiter = RateLimiter()

        # Configure common limits

        # API endpoints (per user)
        _limiter.configure(
            "api:user:default", max_tokens=100, refill_rate=1.67
        )  # 100/min

        # External APIs
        _limiter.configure("api:coingecko", max_tokens=50, refill_rate=0.83)  # 50/min
        _limiter.configure("api:defillama", max_tokens=100, refill_rate=1.67)  # 100/min
        _limiter.configure("api:1inch", max_tokens=60, refill_rate=1.0)  # 60/min
        _limiter.configure(
            "api:hyperliquid", max_tokens=100, refill_rate=1.67
        )  # 100/min

        # Database operations
        _limiter.configure("db:write", max_tokens=200, refill_rate=3.33)  # 200/min
        _limiter.configure("db:read", max_tokens=500, refill_rate=8.33)  # 500/min

    return _limiter


async def rate_limit(key: str, tokens: int = 1) -> bool:
    """
    Convenience function for rate limiting.

    Args:
        key: Rate limit key
        tokens: Tokens to consume

    Returns:
        True if acquired
    """
    limiter = get_rate_limiter()
    return await limiter.acquire(key, tokens)
