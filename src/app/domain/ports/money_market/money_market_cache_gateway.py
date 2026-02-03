"""
Money Market Cache Gateway Port.

Defines the domain interface for money market rate caching operations.
Implements 60s TTL caching to reduce RPC calls and improve performance.
"""

from typing import Protocol

from app.domain.entities.money_market.protocol_data import (
    MoneyMarketProtocolData,
)


class MoneyMarketCacheGateway(Protocol):
    """
    Port interface for money market rate caching operations.

    This protocol defines the contract for caching protocol rate data
    with 60-second TTL to optimize performance and reduce RPC calls.
    """

    async def get_cached_rate(
        self,
        protocol: str,
        asset: str,
        chain: str,
    ) -> MoneyMarketProtocolData | None:
        """
        Get cached rate if valid (within 60s TTL).

        Args:
            protocol: Protocol identifier ('aave_v3', 'compound_v3')
            asset: Asset symbol (e.g., 'USDC', 'WETH')
            chain: Blockchain network (e.g., 'ethereum', 'arbitrum')

        Returns:
            MoneyMarketProtocolData if cache hit and valid, None if miss or expired

        Raises:
            ValueError: If protocol/asset/chain are invalid
        """
        ...

    async def cache_rate(
        self,
        protocol_data: MoneyMarketProtocolData,
    ) -> None:
        """
        Store rate with 60s TTL.

        Args:
            protocol_data: Protocol rate data to cache

        Raises:
            ValueError: If protocol_data validation fails
            DatabaseError: If insert fails
        """
        ...

    async def invalidate_cache(
        self,
        protocol: str,
        asset: str,
        chain: str,
    ) -> None:
        """
        Manually invalidate cached rate.

        Sets valid_until to NOW to force cache miss on next request.

        Args:
            protocol: Protocol identifier
            asset: Asset symbol
            chain: Blockchain network

        Raises:
            ValueError: If protocol/asset/chain are invalid
        """
        ...

    async def get_latest_rates(
        self,
        asset: str,
        chain: str,
    ) -> list[MoneyMarketProtocolData]:
        """
        Get latest valid rates from all protocols for an asset/chain.

        Args:
            asset: Asset symbol
            chain: Blockchain network

        Returns:
            List of MoneyMarketProtocolData from all protocols with valid cache

        Raises:
            ValueError: If asset/chain are invalid
        """
        ...

    async def is_cache_valid(
        self,
        protocol: str,
        asset: str,
        chain: str,
    ) -> bool:
        """
        Check if cache exists and is valid (not expired).

        Args:
            protocol: Protocol identifier
            asset: Asset symbol
            chain: Blockchain network

        Returns:
            True if cache exists and valid_until > NOW, False otherwise
        """
        ...

    async def get_cache_stats(
        self,
    ) -> dict[str, int]:
        """
        Get cache statistics for monitoring.

        Returns:
            Dict with cache metrics:
            - total_entries: Total cached entries
            - valid_entries: Entries with valid_until > NOW
            - expired_entries: Entries with valid_until <= NOW
            - protocols_cached: Number of unique protocols
            - assets_cached: Number of unique assets
            - chains_cached: Number of unique chains
        """
        ...
