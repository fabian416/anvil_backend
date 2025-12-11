"""
Curve Finance Gateway Port.

Defines the domain interface for Curve Finance operations.
This port follows the hexagonal architecture pattern, allowing the domain layer
to remain decoupled from infrastructure concerns.
"""

from typing import Protocol

from app.domain.entities.curve.gauge import Gauge
from app.domain.entities.curve.pool import Pool
from app.domain.value_objects.curve.pool_apy import PoolAPY
from app.domain.value_objects.curve.swap_quote import SwapQuote
from app.domain.value_objects.curve.tvl_data import TVLData


class CurveGateway(Protocol):
    """
    Port interface for Curve Finance operations.

    This protocol defines the contract for accessing Curve data.
    Implementations (adapters) handle the actual API communication,
    caching, and data transformation.
    """

    async def get_pools(
        self,
        chain: str = "ethereum",
    ) -> list[Pool]:
        """
        Get all pools on the specified chain.

        Args:
            chain: Blockchain name (ethereum, arbitrum, optimism, etc.)

        Returns:
            List of Pool entities with current data

        Raises:
            CurveAPIError: If the Curve API is unavailable
        """
        ...

    async def get_pool_by_address(
        self,
        pool_address: str,
        chain: str = "ethereum",
    ) -> Pool:
        """
        Get a specific pool by its contract address.

        Args:
            pool_address: Pool contract address
            chain: Blockchain name

        Returns:
            Pool entity with current data

        Raises:
            PoolNotFoundError: If the pool address doesn't exist
            CurveAPIError: If the Curve API is unavailable
        """
        ...

    async def get_pool_apy(
        self,
        pool_address: str,
        chain: str = "ethereum",
    ) -> PoolAPY:
        """
        Get detailed APY breakdown for a pool.

        Args:
            pool_address: Pool contract address
            chain: Blockchain name

        Returns:
            PoolAPY value object with APY breakdown

        Raises:
            PoolNotFoundError: If the pool address doesn't exist
            CurveAPIError: If the Curve API is unavailable
        """
        ...

    async def get_swap_quote(
        self,
        from_token: str,
        to_token: str,
        amount: str,
        chain: str = "ethereum",
    ) -> SwapQuote:
        """
        Get a swap quote for token exchange.

        Args:
            from_token: Source token address
            to_token: Destination token address
            amount: Amount to swap in smallest unit (wei)
            chain: Blockchain name

        Returns:
            SwapQuote value object with quote details

        Raises:
            InvalidTokenError: If tokens are not supported
            CurveAPIError: If the Curve API is unavailable
        """
        ...

    async def get_gauges(
        self,
        chain: str = "ethereum",
    ) -> list[Gauge]:
        """
        Get all gauge data for rewards.

        Args:
            chain: Blockchain name

        Returns:
            List of Gauge entities with reward data

        Raises:
            CurveAPIError: If the Curve API is unavailable
        """
        ...

    async def get_tvl(
        self,
        chain: str = "ethereum",
    ) -> TVLData:
        """
        Get total value locked data.

        Args:
            chain: Blockchain name

        Returns:
            TVLData value object with TVL breakdown

        Raises:
            CurveAPIError: If the Curve API is unavailable
        """
        ...
