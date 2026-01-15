"""
Rate Limit Entity.

Tracks message usage for rate limiting.
"""

from dataclasses import dataclass, field
from datetime import datetime, UTC
from enum import Enum
from uuid import UUID, uuid4


class WindowType(str, Enum):
    """Rate limit window type."""
    
    HOURLY = "hourly"
    DAILY = "daily"


@dataclass
class RateLimit:
    """
    Rate limit tracking entity.
    
    Tracks message counts per user within time windows.
    """
    
    id: UUID = field(default_factory=uuid4)
    user_id: UUID = field(default_factory=uuid4)
    window_type: WindowType = WindowType.HOURLY
    window_start: datetime = field(default_factory=lambda: datetime.now(UTC))
    message_count: int = 0
    
    def increment(self) -> None:
        """Increment message count."""
        self.message_count += 1
    
    def reset(self) -> None:
        """Reset message count for new window."""
        self.message_count = 0
        self.window_start = datetime.now(UTC)
    
    def is_expired(self) -> bool:
        """Check if the rate limit window has expired."""
        now = datetime.now(UTC)
        if self.window_type == WindowType.HOURLY:
            # Check if more than 1 hour has passed
            delta = now - self.window_start
            return delta.total_seconds() >= 3600
        else:  # DAILY
            # Check if it's a new day
            return now.date() != self.window_start.date()


@dataclass
class RateLimitResult:
    """Result of a rate limit check."""
    
    allowed: bool
    reason: str | None = None
    limit: int | None = None
    current: int = 0
    remaining: int | None = None
    reset_in: int | None = None  # Seconds until reset
    remaining_hourly: int | None = None
    remaining_daily: int | None = None
    
    @classmethod
    def allow(
        cls,
        remaining_hourly: int | None = None,
        remaining_daily: int | None = None,
    ) -> "RateLimitResult":
        """Create an allowed result."""
        return cls(
            allowed=True,
            remaining_hourly=remaining_hourly,
            remaining_daily=remaining_daily,
        )
    
    @classmethod
    def deny(
        cls,
        reason: str,
        limit: int,
        current: int,
        reset_in: int,
    ) -> "RateLimitResult":
        """Create a denied result."""
        return cls(
            allowed=False,
            reason=reason,
            limit=limit,
            current=current,
            reset_in=reset_in,
        )

