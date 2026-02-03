"""
Money Market Comparison Gateway Port.

Defines the domain interface for logging rate comparison requests
and querying comparison analytics.
"""

from datetime import datetime
from typing import Protocol
from uuid import UUID

from app.domain.entities.money_market.rate_comparison import (
    MoneyMarketRateComparison,
)


class MoneyMarketComparisonGateway(Protocol):
    """
    Port interface for money market rate comparison logging.

    This protocol defines the contract for logging user comparisons
    and querying analytics data for optimization insights.
    """

    async def log_comparison(
        self,
        rate_comparison: MoneyMarketRateComparison,
    ) -> UUID:
        """
        Store comparison record for analytics.

        Args:
            rate_comparison: Rate comparison entity to log

        Returns:
            UUID of created comparison record

        Raises:
            ValueError: If rate_comparison validation fails
            DatabaseError: If insert fails
        """
        ...

    async def get_user_comparisons(
        self,
        user_id: UUID,
        limit: int = 10,
        offset: int = 0,
    ) -> list[MoneyMarketRateComparison]:
        """
        Get user's comparison history with pagination.

        Args:
            user_id: User identifier
            limit: Maximum number of records to return (default: 10)
            offset: Number of records to skip (default: 0)

        Returns:
            List of MoneyMarketRateComparison ordered by created_at DESC

        Raises:
            ValueError: If user_id is invalid or limit/offset are negative
        """
        ...

    async def get_comparison_by_id(
        self,
        comparison_id: UUID,
    ) -> MoneyMarketRateComparison | None:
        """
        Get specific comparison by ID.

        Args:
            comparison_id: Comparison identifier

        Returns:
            MoneyMarketRateComparison if found, None otherwise

        Raises:
            ValueError: If comparison_id is invalid
        """
        ...

    async def get_comparison_analytics(
        self,
        asset: str,
        chain: str,
        days: int = 7,
    ) -> dict:
        """
        Get analytics for asset/chain comparisons over time period.

        Args:
            asset: Asset symbol (e.g., 'USDC')
            chain: Blockchain network (e.g., 'ethereum')
            days: Number of days to analyze (default: 7)

        Returns:
            Dict with analytics:
            - total_comparisons: Total comparison count
            - unique_users: Number of unique users
            - avg_latency_ms: Average response time
            - most_compared_protocols: List of protocol comparison counts
            - best_supply_protocol: Protocol with most 'best supply' wins
            - best_borrow_protocol: Protocol with most 'best borrow' wins
            - cache_hit_rate: Average cache hit percentage

        Raises:
            ValueError: If asset/chain are invalid or days < 1
        """
        ...

    async def get_popular_comparisons(
        self,
        days: int = 7,
        limit: int = 10,
    ) -> list[dict]:
        """
        Get most popular asset/chain combinations.

        Args:
            days: Number of days to analyze (default: 7)
            limit: Maximum number of combinations (default: 10)

        Returns:
            List of dicts with:
            - asset: Asset symbol
            - chain: Blockchain network
            - comparison_count: Number of comparisons
            - avg_latency_ms: Average response time
            - unique_users: Number of unique users

        Raises:
            ValueError: If days < 1 or limit < 1
        """
        ...

    async def get_user_comparison_count(
        self,
        user_id: UUID,
        since: datetime | None = None,
    ) -> int:
        """
        Get total comparison count for a user.

        Args:
            user_id: User identifier
            since: Optional start datetime (default: all time)

        Returns:
            Total number of comparisons

        Raises:
            ValueError: If user_id is invalid
        """
        ...

    async def get_guest_comparison_count(
        self,
        guest_session_id: str,
        since: datetime | None = None,
    ) -> int:
        """
        Get total comparison count for a guest session.

        Args:
            guest_session_id: Guest session identifier
            since: Optional start datetime (default: all time)

        Returns:
            Total number of comparisons

        Raises:
            ValueError: If guest_session_id is invalid
        """
        ...
