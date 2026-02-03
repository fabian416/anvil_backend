"""
Redis-based rate limiter with sliding window counter algorithm.

Implements tiered rate limiting for chat endpoints:
- Guest: 800 messages/hour (IP-based tracking)
- Free: 1000 messages/hour (user ID tracking)
- Premium: 10000 messages/hour (user ID tracking)
- Enterprise: 10000 messages/hour (user ID tracking)

Uses Redis INCR + TTL for atomic operations and automatic expiration.
"""

import logging
from datetime import datetime, timezone, timedelta
from typing import NamedTuple, Optional
from enum import Enum

from redis.asyncio import Redis

logger = logging.getLogger(__name__)


class UserTier(str, Enum):
    """User subscription tiers."""

    GUEST = "guest"
    FREE = "free"
    PREMIUM = "premium"
    ENTERPRISE = "enterprise"


class RateLimitResult(NamedTuple):
    """Result of rate limit check."""

    allowed: bool
    limit: int
    current: int
    remaining: int
    reset_at: datetime


# Rate limit configurations (messages per hour)
RATE_LIMITS = {
    UserTier.GUEST: 800,
    UserTier.FREE: 1000,
    UserTier.PREMIUM: 10000,
    UserTier.ENTERPRISE: 10000,
}


class RateLimiter:
    """Redis-based rate limiter with sliding window counter."""

    def __init__(self, redis_client: Redis):
        """
        Initialize rate limiter.

        Args:
            redis_client: Redis async client for rate limit storage
        """
        self._redis = redis_client
        self._ttl_seconds = 3600  # 1 hour

    async def check_rate_limit(
        self,
        identifier: str,
        user_tier: UserTier,
        is_authenticated: bool = False,
    ) -> RateLimitResult:
        """
        Check if request is within rate limit.

        Args:
            identifier: IP address (guest) or user ID (authenticated)
            user_tier: User subscription tier
            is_authenticated: Whether user is authenticated

        Returns:
            RateLimitResult with allow/deny decision and metadata

        Note:
            Uses sliding window counter with hourly reset.
            Key format: rate_limit:{type}:{id}:hour:{timestamp}
        """
        # Get rate limit for user tier
        limit = RATE_LIMITS.get(user_tier, 800)  # Default to guest limit

        # Build Redis key
        current_hour = self._get_current_hour_timestamp()
        key_prefix = "user" if is_authenticated else "guest"
        redis_key = f"rate_limit:{key_prefix}:{identifier}:hour:{current_hour}"

        try:
            # Atomic increment and get
            current_count = await self._redis.incr(redis_key)

            # Set TTL on first increment (only if key is new)
            if current_count == 1:
                await self._redis.expire(redis_key, self._ttl_seconds)

            # Calculate reset time (next hour)
            reset_at = self._get_next_hour_timestamp()

            # Check if within limit
            allowed = current_count <= limit
            remaining = max(0, limit - current_count)

            logger.debug(
                "Rate limit check",
                extra={
                    "identifier": identifier,
                    "tier": user_tier.value,
                    "is_authenticated": is_authenticated,
                    "current": current_count,
                    "limit": limit,
                    "allowed": allowed,
                    "remaining": remaining,
                },
            )

            if not allowed:
                logger.warning(
                    "Rate limit exceeded",
                    extra={
                        "identifier": identifier,
                        "tier": user_tier.value,
                        "current": current_count,
                        "limit": limit,
                    },
                )

            return RateLimitResult(
                allowed=allowed,
                limit=limit,
                current=current_count,
                remaining=remaining,
                reset_at=reset_at,
            )

        except Exception as e:
            logger.error(
                f"Rate limit check failed: {e} - allowing request (fail-open)",
                exc_info=True,
                extra={"identifier": identifier, "tier": user_tier.value},
            )

            # Fail-open: Allow request if Redis fails
            return RateLimitResult(
                allowed=True,
                limit=limit,
                current=0,
                remaining=limit,
                reset_at=self._get_next_hour_timestamp(),
            )

    async def get_current_usage(
        self,
        identifier: str,
        is_authenticated: bool = False,
    ) -> int:
        """
        Get current usage count for identifier.

        Args:
            identifier: IP address (guest) or user ID (authenticated)
            is_authenticated: Whether user is authenticated

        Returns:
            Current count for current hour window

        Note:
            Returns 0 if key doesn't exist or on error.
        """
        current_hour = self._get_current_hour_timestamp()
        key_prefix = "user" if is_authenticated else "guest"
        redis_key = f"rate_limit:{key_prefix}:{identifier}:hour:{current_hour}"

        try:
            count = await self._redis.get(redis_key)
            return int(count) if count else 0
        except Exception as e:
            logger.error(
                f"Failed to get current usage: {e}",
                exc_info=True,
                extra={"identifier": identifier},
            )
            return 0

    async def reset_rate_limit(
        self,
        identifier: str,
        is_authenticated: bool = False,
    ) -> bool:
        """
        Reset rate limit for identifier (admin override).

        Args:
            identifier: IP address (guest) or user ID (authenticated)
            is_authenticated: Whether user is authenticated

        Returns:
            True if reset successful, False otherwise

        Note:
            Only use for admin overrides or testing.
        """
        current_hour = self._get_current_hour_timestamp()
        key_prefix = "user" if is_authenticated else "guest"
        redis_key = f"rate_limit:{key_prefix}:{identifier}:hour:{current_hour}"

        try:
            await self._redis.delete(redis_key)
            logger.info(
                f"Rate limit reset for {identifier}",
                extra={"identifier": identifier, "is_authenticated": is_authenticated},
            )
            return True
        except Exception as e:
            logger.error(
                f"Failed to reset rate limit: {e}",
                exc_info=True,
                extra={"identifier": identifier},
            )
            return False

    def _get_current_hour_timestamp(self) -> int:
        """Get current hour timestamp (start of hour)."""
        now = datetime.now(timezone.utc)
        hour_start = now.replace(minute=0, second=0, microsecond=0)
        return int(hour_start.timestamp())

    def _get_next_hour_timestamp(self) -> datetime:
        """Get next hour timestamp (for reset_at)."""
        now = datetime.now(timezone.utc)
        next_hour = (now + timedelta(hours=1)).replace(
            minute=0, second=0, microsecond=0
        )
        return next_hour
