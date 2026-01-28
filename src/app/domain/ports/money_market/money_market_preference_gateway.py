"""
Money Market Preference Gateway Port.

Defines the domain interface for user preference management
(rate alerts, notification settings, protocol preferences).
"""

from typing import Protocol
from uuid import UUID

from app.domain.entities.money_market.user_preference import (
    MoneyMarketUserPreference,
)


class MoneyMarketPreferenceGateway(Protocol):
    """
    Port interface for money market user preferences.

    This protocol defines the contract for managing user-specific
    rate alert settings and notification preferences.
    """

    async def get_preferences(
        self,
        user_id: UUID,
    ) -> MoneyMarketUserPreference | None:
        """
        Get user's money market preferences.

        Args:
            user_id: User identifier

        Returns:
            MoneyMarketUserPreference if found, None otherwise

        Raises:
            ValueError: If user_id is invalid
        """
        ...

    async def upsert_preferences(
        self,
        user_preference: MoneyMarketUserPreference,
    ) -> None:
        """
        Create or update user preferences (INSERT ON CONFLICT UPDATE).

        Uses UPSERT pattern to handle unique constraint on user_id.
        Creates if not exists, updates if exists.

        Args:
            user_preference: User preference entity

        Raises:
            ValueError: If user_preference validation fails
            DatabaseError: If upsert fails
        """
        ...

    async def delete_preferences(
        self,
        user_id: UUID,
    ) -> bool:
        """
        Delete user's preferences.

        Args:
            user_id: User identifier

        Returns:
            True if deleted, False if not found

        Raises:
            ValueError: If user_id is invalid
            DatabaseError: If delete fails
        """
        ...

    async def get_users_with_rate_alerts_enabled(
        self,
        asset: str | None = None,
        chain: str | None = None,
    ) -> list[MoneyMarketUserPreference]:
        """
        Get all users with rate alerts enabled.

        Optionally filter by asset/chain to get users watching specific markets.

        Args:
            asset: Optional asset filter (checks watched_assets)
            chain: Optional chain filter (checks watched_chains)

        Returns:
            List of MoneyMarketUserPreference with enable_rate_alerts=True

        Raises:
            ValueError: If asset/chain format is invalid
        """
        ...

    async def get_preferences_by_protocol(
        self,
        protocol: str,
    ) -> list[MoneyMarketUserPreference]:
        """
        Get users who prefer a specific protocol.

        Args:
            protocol: Protocol identifier ('aave_v3', 'compound_v3')

        Returns:
            List of MoneyMarketUserPreference with matching preferred_protocol

        Raises:
            ValueError: If protocol is invalid
        """
        ...

    async def count_users_watching_asset(
        self,
        asset: str,
    ) -> int:
        """
        Count users watching a specific asset.

        Args:
            asset: Asset symbol (e.g., 'USDC')

        Returns:
            Count of users with asset in watched_assets

        Raises:
            ValueError: If asset is invalid
        """
        ...

    async def count_users_watching_chain(
        self,
        chain: str,
    ) -> int:
        """
        Count users watching a specific chain.

        Args:
            chain: Blockchain network (e.g., 'ethereum')

        Returns:
            Count of users with chain in watched_chains

        Raises:
            ValueError: If chain is invalid
        """
        ...

    async def get_notification_enabled_users(
        self,
    ) -> list[MoneyMarketUserPreference]:
        """
        Get all users with notifications enabled.

        Returns:
            List of MoneyMarketUserPreference with notification_enabled=True
        """
        ...
