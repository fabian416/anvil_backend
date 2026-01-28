"""
Money Market Alert Gateway Port.

Defines the domain interface for rate change alert management
and notification logging.
"""

from datetime import datetime
from typing import Protocol
from uuid import UUID

from app.domain.entities.money_market.alert import MoneyMarketAlert


class MoneyMarketAlertGateway(Protocol):
    """
    Port interface for money market rate alerts.

    This protocol defines the contract for managing rate change alerts
    and logging notification history.
    """

    async def create_alert(
        self,
        alert: MoneyMarketAlert,
    ) -> UUID:
        """
        Create a new rate change alert.

        Args:
            alert: Alert entity to create

        Returns:
            UUID of created alert

        Raises:
            ValueError: If alert validation fails
            DatabaseError: If insert fails
        """
        ...

    async def get_alert_by_id(
        self,
        alert_id: UUID,
    ) -> MoneyMarketAlert | None:
        """
        Get specific alert by ID.

        Args:
            alert_id: Alert identifier

        Returns:
            MoneyMarketAlert if found, None otherwise

        Raises:
            ValueError: If alert_id is invalid
        """
        ...

    async def get_user_alerts(
        self,
        user_id: UUID,
        is_read: bool | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[MoneyMarketAlert]:
        """
        Get user's alerts with optional read status filter.

        Args:
            user_id: User identifier
            is_read: Optional filter (None = all, True = read, False = unread)
            limit: Maximum number of alerts (default: 50)
            offset: Number of alerts to skip (default: 0)

        Returns:
            List of MoneyMarketAlert ordered by created_at DESC

        Raises:
            ValueError: If user_id is invalid or limit/offset are negative
        """
        ...

    async def get_unread_alert_count(
        self,
        user_id: UUID,
    ) -> int:
        """
        Get count of unread alerts for user.

        Args:
            user_id: User identifier

        Returns:
            Count of alerts with is_read=False

        Raises:
            ValueError: If user_id is invalid
        """
        ...

    async def mark_alert_read(
        self,
        alert_id: UUID,
    ) -> bool:
        """
        Mark alert as read.

        Args:
            alert_id: Alert identifier

        Returns:
            True if updated, False if not found

        Raises:
            ValueError: If alert_id is invalid
            DatabaseError: If update fails
        """
        ...

    async def mark_all_alerts_read(
        self,
        user_id: UUID,
    ) -> int:
        """
        Mark all user alerts as read.

        Args:
            user_id: User identifier

        Returns:
            Number of alerts updated

        Raises:
            ValueError: If user_id is invalid
            DatabaseError: If update fails
        """
        ...

    async def delete_alert(
        self,
        alert_id: UUID,
    ) -> bool:
        """
        Delete an alert.

        Args:
            alert_id: Alert identifier

        Returns:
            True if deleted, False if not found

        Raises:
            ValueError: If alert_id is invalid
            DatabaseError: If delete fails
        """
        ...

    async def get_alerts_by_asset(
        self,
        user_id: UUID,
        asset: str,
        chain: str,
        limit: int = 10,
    ) -> list[MoneyMarketAlert]:
        """
        Get user's alerts for specific asset/chain.

        Args:
            user_id: User identifier
            asset: Asset symbol
            chain: Blockchain network
            limit: Maximum number of alerts (default: 10)

        Returns:
            List of MoneyMarketAlert ordered by created_at DESC

        Raises:
            ValueError: If parameters are invalid
        """
        ...

    async def get_recent_alerts(
        self,
        user_id: UUID,
        hours: int = 24,
    ) -> list[MoneyMarketAlert]:
        """
        Get user's recent alerts within time window.

        Args:
            user_id: User identifier
            hours: Time window in hours (default: 24)

        Returns:
            List of MoneyMarketAlert created within last N hours

        Raises:
            ValueError: If user_id is invalid or hours < 1
        """
        ...

    async def get_alerts_by_protocol(
        self,
        user_id: UUID,
        protocol: str,
        limit: int = 10,
    ) -> list[MoneyMarketAlert]:
        """
        Get user's alerts for specific protocol.

        Args:
            user_id: User identifier
            protocol: Protocol identifier ('aave_v3', 'compound_v3')
            limit: Maximum number of alerts (default: 10)

        Returns:
            List of MoneyMarketAlert ordered by created_at DESC

        Raises:
            ValueError: If parameters are invalid
        """
        ...

    async def update_notification_status(
        self,
        alert_id: UUID,
        notification_sent: bool,
        sent_at: datetime | None = None,
    ) -> bool:
        """
        Update alert notification status.

        Args:
            alert_id: Alert identifier
            notification_sent: Whether notification was sent
            sent_at: Timestamp when notification was sent (required if sent=True)

        Returns:
            True if updated, False if not found

        Raises:
            ValueError: If alert_id is invalid or sent=True without sent_at
            DatabaseError: If update fails
        """
        ...

    async def get_alert_statistics(
        self,
        user_id: UUID,
        days: int = 30,
    ) -> dict:
        """
        Get alert statistics for user over time period.

        Args:
            user_id: User identifier
            days: Number of days to analyze (default: 30)

        Returns:
            Dict with statistics:
            - total_alerts: Total alert count
            - unread_alerts: Unread alert count
            - alerts_by_type: Count by alert_type
            - alerts_by_severity: Count by severity
            - alerts_by_protocol: Count by protocol
            - avg_apy_change: Average APY change percentage
            - notification_success_rate: % of alerts successfully notified

        Raises:
            ValueError: If user_id is invalid or days < 1
        """
        ...
