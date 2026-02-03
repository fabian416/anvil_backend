"""
Analytics repository port.

Defines the interface for conversation analytics persistence and aggregation.
"""

from typing import Protocol, List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime

from app.domain.entities.chat.conversation_analytics import ConversationAnalytics


class AnalyticsRepository(Protocol):
    """
    Port for conversation analytics repository.

    Provides methods for persisting and querying conversation analytics data.
    """

    async def save(self, analytics: ConversationAnalytics) -> ConversationAnalytics:
        """
        Save or update analytics record.

        Args:
            analytics: Analytics entity to save

        Returns:
            Saved analytics entity
        """
        ...

    async def get_by_id(self, analytics_id: UUID) -> Optional[ConversationAnalytics]:
        """
        Get analytics by ID.

        Args:
            analytics_id: Analytics identifier

        Returns:
            ConversationAnalytics or None if not found
        """
        ...

    async def get_by_conversation(
        self, conversation_id: UUID
    ) -> Optional[ConversationAnalytics]:
        """
        Get analytics for a conversation.

        Args:
            conversation_id: Conversation identifier

        Returns:
            ConversationAnalytics or None if not found
        """
        ...

    async def get_by_user(
        self,
        user_id: UUID,
        limit: int = 50,
        offset: int = 0,
    ) -> List[ConversationAnalytics]:
        """
        Get analytics for user's conversations.

        Args:
            user_id: User identifier
            limit: Maximum number of records to return
            offset: Number of records to skip

        Returns:
            List of analytics records (most recent first)
        """
        ...

    async def get_by_user_date_range(
        self,
        user_id: UUID,
        start_date: datetime,
        end_date: datetime,
    ) -> List[ConversationAnalytics]:
        """
        Get analytics for user within date range.

        Args:
            user_id: User identifier
            start_date: Start of date range (inclusive)
            end_date: End of date range (inclusive)

        Returns:
            List of analytics records in date range
        """
        ...

    async def get_aggregate_by_user(
        self,
        user_id: UUID,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """
        Get aggregated analytics for a user.

        Args:
            user_id: User identifier
            start_date: Optional start date for filtering
            end_date: Optional end date for filtering

        Returns:
            Dictionary with aggregated metrics
        """
        ...

    async def get_aggregate_by_date_range(
        self,
        start_date: datetime,
        end_date: datetime,
        user_id: Optional[UUID] = None,
    ) -> Dict[str, Any]:
        """
        Get aggregated analytics for a date range.

        Args:
            start_date: Start of date range (inclusive)
            end_date: End of date range (inclusive)
            user_id: Optional user filter

        Returns:
            Dictionary with aggregated metrics for the time period
        """
        ...

    async def get_top_conversations_by_cost(
        self,
        limit: int = 10,
        user_id: Optional[UUID] = None,
        start_date: Optional[datetime] = None,
    ) -> List[ConversationAnalytics]:
        """
        Get conversations with highest costs.

        Args:
            limit: Maximum number of conversations to return
            user_id: Optional user filter
            start_date: Optional start date filter

        Returns:
            List of analytics records ordered by cost (highest first)
        """
        ...

    async def get_top_conversations_by_messages(
        self,
        limit: int = 10,
        user_id: Optional[UUID] = None,
        start_date: Optional[datetime] = None,
    ) -> List[ConversationAnalytics]:
        """
        Get conversations with most messages.

        Args:
            limit: Maximum number of conversations to return
            user_id: Optional user filter
            start_date: Optional start date filter

        Returns:
            List of analytics records ordered by message count (highest first)
        """
        ...

    async def get_conversations_by_quality_score(
        self,
        min_score: float,
        max_score: float,
        user_id: Optional[UUID] = None,
        limit: int = 50,
    ) -> List[ConversationAnalytics]:
        """
        Get conversations within quality score range.

        Args:
            min_score: Minimum quality score (0.0 to 1.0)
            max_score: Maximum quality score (0.0 to 1.0)
            user_id: Optional user filter
            limit: Maximum number of conversations to return

        Returns:
            List of analytics records within quality range
        """
        ...

    async def get_agent_usage_stats(
        self,
        user_id: Optional[UUID] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> Dict[str, Dict[str, Any]]:
        """
        Get aggregated agent usage statistics.

        Args:
            user_id: Optional user filter
            start_date: Optional start date filter
            end_date: Optional end date filter

        Returns:
            Dictionary mapping agent names to usage stats
        """
        ...

    async def get_cost_breakdown_by_agent(
        self,
        user_id: Optional[UUID] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> Dict[str, float]:
        """
        Get cost breakdown by agent.

        Args:
            user_id: Optional user filter
            start_date: Optional start date filter
            end_date: Optional end date filter

        Returns:
            Dictionary mapping agent names to total costs in USD
        """
        ...

    async def get_daily_analytics(
        self,
        user_id: UUID,
        start_date: datetime,
        end_date: datetime,
    ) -> List[Dict[str, Any]]:
        """
        Get daily aggregated analytics for user.

        Args:
            user_id: User identifier
            start_date: Start of date range (inclusive)
            end_date: End of date range (inclusive)

        Returns:
            List of daily analytics dictionaries
        """
        ...

    async def delete(self, analytics_id: UUID) -> bool:
        """
        Delete analytics record.

        Args:
            analytics_id: Analytics identifier

        Returns:
            True if deleted, False if not found
        """
        ...

    async def delete_by_conversation(self, conversation_id: UUID) -> bool:
        """
        Delete analytics for a conversation.

        Args:
            conversation_id: Conversation identifier

        Returns:
            True if deleted, False if not found
        """
        ...

    async def delete_old_analytics(self, days_to_keep: int = 90) -> int:
        """
        Delete analytics older than specified days.

        Args:
            days_to_keep: Number of days of analytics to retain

        Returns:
            Number of analytics records deleted
        """
        ...
