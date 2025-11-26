"""
Ports (interfaces) for user metrics functionality.
"""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, TypedDict

from app.domain.entities.user_event import UserEvent


class UserMetricsSummary(TypedDict):
    """Summary of user metrics."""
    user_id: int
    total_events: int
    first_event_at: datetime | None
    last_event_at: datetime | None
    events_by_category: dict[str, int]
    events_by_type: dict[str, int]
    devices_used: list[str]
    platforms_used: list[str]


class UserEventFilter(TypedDict, total=False):
    """Filters for querying user events."""
    user_id: int | None
    event_type: str | None
    event_category: str | None
    device_type: str | None
    platform: str | None
    from_date: datetime | None
    to_date: datetime | None


class UserMetricsRepository(ABC):
    """
    Repository interface for user metrics/events.
    """

    @abstractmethod
    async def record_event(self, event: UserEvent) -> int:
        """
        Record a new user event.
        
        Args:
            event: The user event to record
            
        Returns:
            The ID of the created event
        """
        pass

    @abstractmethod
    async def get_events(
        self,
        filters: UserEventFilter,
        limit: int = 100,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        """
        Get user events with optional filters.
        
        Args:
            filters: Filtering criteria
            limit: Maximum number of events to return
            offset: Number of events to skip
            
        Returns:
            List of events as dictionaries
        """
        pass

    @abstractmethod
    async def get_user_metrics_summary(self, user_id: int) -> UserMetricsSummary | None:
        """
        Get a summary of metrics for a specific user.
        
        Args:
            user_id: The user ID
            
        Returns:
            Summary of user metrics or None if no events found
        """
        pass

    @abstractmethod
    async def get_event_count(
        self,
        user_id: int | None = None,
        event_type: str | None = None,
        from_date: datetime | None = None,
        to_date: datetime | None = None,
    ) -> int:
        """
        Get the count of events matching criteria.
        
        Args:
            user_id: Filter by user ID
            event_type: Filter by event type
            from_date: Filter events after this date
            to_date: Filter events before this date
            
        Returns:
            Count of matching events
        """
        pass

    @abstractmethod
    async def get_active_users_count(
        self,
        from_date: datetime,
        to_date: datetime | None = None,
    ) -> int:
        """
        Get the count of unique active users in a date range.
        
        Args:
            from_date: Start of date range
            to_date: End of date range (defaults to now)
            
        Returns:
            Count of unique active users
        """
        pass

