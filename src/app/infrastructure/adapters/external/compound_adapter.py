"""
Compound V3 Gateway Adapter.

Implements the CompoundGateway port using the CompoundClient.
Provides real-time Compound V3 (Comet) data from on-chain.
"""

import logging
from typing import Optional

from app.domain.ports.compound_gateway import (
    CompoundGateway,
    CompoundMarketData,
    CompoundUserPosition,
)
from app.infrastructure.adapters.external.compound_client import (
    CompoundClient,
    CompoundMarket,
)

logger = logging.getLogger(__name__)


class CompoundAdapter(CompoundGateway):
    """
    Adapter implementing CompoundGateway using CompoundClient.

    Features:
    - Real-time rates from Comet contracts
    - Multi-chain support
    - Automatic fallback on errors
    """

    def __init__(self, client: CompoundClient):
        """
        Initialize Compound adapter.

        Args:
            client: CompoundClient instance
        """
        self._client = client

    async def get_market_details(
        self,
        asset: str,
        chain: str = "ethereum",
    ) -> Optional[CompoundMarketData]:
        """Get market details for a specific asset."""
        market = await self._client.get_market(asset=asset, chain=chain)

        if not market:
            return None

        return self._transform_market(market)

    async def get_markets(
        self,
        chain: str = "ethereum",
    ) -> list[CompoundMarketData]:
        """Get all markets on a specific chain."""
        markets = await self._client.get_markets(chain=chain)
        return [self._transform_market(m) for m in markets]

    async def get_supply_apy(
        self,
        asset: str,
        chain: str = "ethereum",
    ) -> float:
        """Get current supply APY for an asset."""
        market = await self._client.get_market(asset=asset, chain=chain)

        if not market:
            # Return fallback rate
            return self._get_fallback_supply_apy(asset)

        return market.supply_apy

    async def get_borrow_apy(
        self,
        asset: str,
        chain: str = "ethereum",
    ) -> float:
        """Get current borrow APY for an asset."""
        market = await self._client.get_market(asset=asset, chain=chain)

        if not market:
            # Return fallback rate
            return self._get_fallback_borrow_apy(asset)

        return market.borrow_apy

    async def get_user_position(
        self,
        user_address: str,
        asset: str = "USDC",
        chain: str = "ethereum",
    ) -> Optional[CompoundUserPosition]:
        """Get user's position in a Compound V3 market."""
        position = await self._client.get_user_position(
            user_address=user_address,
            asset=asset,
            chain=chain,
        )

        if not position:
            return None

        return CompoundUserPosition(
            chain=position.chain,
            base_asset=position.base_asset,
            user_address=position.user_address,
            supplied=position.supplied,
            borrowed=position.borrowed,
            health_factor=position.health_factor,
        )

    def _transform_market(self, market: CompoundMarket) -> CompoundMarketData:
        """Transform client market to gateway data."""
        return CompoundMarketData(
            chain=market.chain,
            base_asset=market.base_asset,
            comet_address=market.comet_address,
            supply_apy=market.supply_apy,
            borrow_apy=market.borrow_apy,
            utilization=market.utilization,
            total_supply_usd=market.total_supply,  # Already in base asset units
            total_borrow_usd=market.total_borrow,
        )

    def _get_fallback_supply_apy(self, asset: str) -> float:
        """Get fallback supply APY when API fails."""
        fallback_rates = {
            "USDC": 4.2,
            "WETH": 1.8,
            "ETH": 1.8,
        }
        return fallback_rates.get(asset.upper(), 3.0)

    def _get_fallback_borrow_apy(self, asset: str) -> float:
        """Get fallback borrow APY when API fails."""
        fallback_rates = {
            "USDC": 5.5,
            "WETH": 3.2,
            "ETH": 3.2,
        }
        return fallback_rates.get(asset.upper(), 4.0)
