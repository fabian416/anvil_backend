"""
Rate Limit Service.

Handles rate limiting based on user type.
"""

import logging
from datetime import datetime, timedelta
from typing import Protocol
from uuid import UUID

from app.application.chat.services.rate_limit_config import (
    RATE_LIMITS,
    get_rate_limit_config,
    has_unlimited_access,
)
from app.domain.chat.entities.chat_user import ChatUser
from app.domain.chat.entities.rate_limit import RateLimitResult, WindowType

logger = logging.getLogger(__name__)


class RateLimitRepositoryProtocol(Protocol):
    """Protocol for rate limit repository."""
    
    async def get_hourly_count(self, user_id: UUID) -> int:
        """Get message count for current hour."""
        ...
    
    async def get_daily_count(self, user_id: UUID) -> int:
        """Get message count for current day."""
        ...
    
    async def increment(self, user_id: UUID) -> None:
        """Increment message counts."""
        ...


class RateLimitService:
    """
    Service for rate limiting based on user type.
    
    Different limits for guest, authenticated, and premium users.
    """
    
    def __init__(self, rate_limit_repository: RateLimitRepositoryProtocol):
        self._repo = rate_limit_repository
    
    async def check_and_increment(self, user: ChatUser) -> RateLimitResult:
        """
        Check rate limits and increment usage if allowed.
        
        Args:
            user: Chat user to check
            
        Returns:
            RateLimitResult with allowed status and remaining counts
        """
        user_type = user.user_type.value
        limits = get_rate_limit_config(user_type)
        
        # Premium users have no limits
        if has_unlimited_access(user_type):
            return RateLimitResult.allow()
        
        # Get current counts
        hourly_count = await self._repo.get_hourly_count(user.id)
        daily_count = await self._repo.get_daily_count(user.id)
        
        hourly_limit = limits["messages_per_hour"]
        daily_limit = limits["messages_per_day"]
        
        # Check hourly limit
        if hourly_limit and hourly_count >= hourly_limit:
            return RateLimitResult.deny(
                reason="hourly_limit",
                limit=hourly_limit,
                current=hourly_count,
                reset_in=self._seconds_until_hour_reset(),
            )
        
        # Check daily limit
        if daily_limit and daily_count >= daily_limit:
            return RateLimitResult.deny(
                reason="daily_limit",
                limit=daily_limit,
                current=daily_count,
                reset_in=self._seconds_until_day_reset(),
            )
        
        # Increment counter
        await self._repo.increment(user.id)
        
        # Calculate remaining
        remaining_hourly = (hourly_limit - hourly_count - 1) if hourly_limit else None
        remaining_daily = (daily_limit - daily_count - 1) if daily_limit else None
        
        return RateLimitResult.allow(
            remaining_hourly=remaining_hourly,
            remaining_daily=remaining_daily,
        )
    
    async def get_status(self, user: ChatUser) -> dict:
        """
        Get current rate limit status for user.
        
        Args:
            user: Chat user to check
            
        Returns:
            Dict with current limits and usage
        """
        user_type = user.user_type.value
        limits = get_rate_limit_config(user_type)
        
        if has_unlimited_access(user_type):
            return {
                "user_type": user_type,
                "unlimited": True,
                "hourly_limit": None,
                "daily_limit": None,
                "hourly_used": 0,
                "daily_used": 0,
                "hourly_remaining": None,
                "daily_remaining": None,
            }
        
        hourly_count = await self._repo.get_hourly_count(user.id)
        daily_count = await self._repo.get_daily_count(user.id)
        
        hourly_limit = limits["messages_per_hour"]
        daily_limit = limits["messages_per_day"]
        
        return {
            "user_type": user_type,
            "unlimited": False,
            "hourly_limit": hourly_limit,
            "daily_limit": daily_limit,
            "hourly_used": hourly_count,
            "daily_used": daily_count,
            "hourly_remaining": max(0, hourly_limit - hourly_count) if hourly_limit else None,
            "daily_remaining": max(0, daily_limit - daily_count) if daily_limit else None,
            "hourly_reset_in": self._seconds_until_hour_reset(),
            "daily_reset_in": self._seconds_until_day_reset(),
        }
    
    def _seconds_until_hour_reset(self) -> int:
        """Calculate seconds until the next hour."""
        now = datetime.utcnow()
        next_hour = now.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)
        return int((next_hour - now).total_seconds())
    
    def _seconds_until_day_reset(self) -> int:
        """Calculate seconds until midnight UTC."""
        now = datetime.utcnow()
        tomorrow = now.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
        return int((tomorrow - now).total_seconds())

