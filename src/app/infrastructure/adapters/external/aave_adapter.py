"""
Aave Gateway Adapter.

Implements the AaveGateway port with caching
for market and position data.
"""

import logging
import re
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any

from app.domain.entities.lending.aave_market import AaveMarket
from app.domain.entities.lending.aave_position import (
    AaveBorrowPosition,
    AavePosition,
    AaveSupplyPosition,
)
from app.domain.exceptions.aave import (
    AaveAPIError,
    InvalidAddressError,
    MarketNotFoundError,
    PositionNotFoundError,
    UnsupportedChainError,
)
from app.domain.ports.aave_gateway import AaveGateway
from app.domain.value_objects.lending.health_factor import HealthFactor
from app.infrastructure.cache.external_api_cache import ExternalAPICache

logger = logging.getLogger(__name__)

# Ethereum address pattern
ETH_ADDRESS_PATTERN = re.compile(r"^0x[a-fA-F0-9]{40}$")

# Supported chains
SUPPORTED_CHAINS = {"ethereum", "polygon", "arbitrum", "optimism", "avalanche", "base"}


class AaveAdapter(AaveGateway):
    """
    Aave V3 implementation of AaveGateway.

    Uses caching for market and position data:
    - Markets: 5 min cache
    - Positions: 2 min cache (more dynamic)
    - Stats: 10 min cache
    """

    DEFAULT_MARKET_CACHE_TTL = 300  # 5 minutes
    DEFAULT_POSITION_CACHE_TTL = 120  # 2 minutes
    DEFAULT_STATS_CACHE_TTL = 600  # 10 minutes

    def __init__(
        self,
        cache: ExternalAPICache,
        api_key: str | None = None,
        market_cache_ttl: int = DEFAULT_MARKET_CACHE_TTL,
        position_cache_ttl: int = DEFAULT_POSITION_CACHE_TTL,
        stats_cache_ttl: int = DEFAULT_STATS_CACHE_TTL,
    ):
        """Initialize AaveAdapter."""
        self._cache = cache
        self._api_key = api_key
        self._market_cache_ttl = market_cache_ttl
        self._position_cache_ttl = position_cache_ttl
        self._stats_cache_ttl = stats_cache_ttl

    def _validate_chain(self, chain: str) -> None:
        """Validate chain is supported."""
        if chain.lower() not in SUPPORTED_CHAINS:
            raise UnsupportedChainError(chain)

    def _validate_address(self, address: str) -> None:
        """Validate Ethereum address format."""
        if not ETH_ADDRESS_PATTERN.match(address):
            raise InvalidAddressError(address)

    async def get_markets(
        self,
        asset: str | None = None,
        chain: str = "ethereum",
    ) -> list[AaveMarket]:
        """Get Aave V3 markets with caching."""
        self._validate_chain(chain)

        cache_key_params = {"chain": chain}

        cached = await self._cache.get("aave", "markets", **cache_key_params)
        if cached:
            logger.debug("Cache hit for Aave markets")
            markets = [AaveMarket.from_dict(m) for m in cached]
        else:
            try:
                # Use fallback data for development
                markets = self._get_fallback_markets(chain)

                await self._cache.set(
                    "aave",
                    "markets",
                    [m.to_dict() for m in markets],
                    ttl=self._market_cache_ttl,
                    **cache_key_params,
                )
                logger.debug(f"Fetched {len(markets)} Aave markets on {chain}")

            except UnsupportedChainError:
                raise
            except Exception as e:
                logger.error(f"Error fetching Aave markets: {e}")
                raise AaveAPIError(str(e)) from e

        # Filter by asset if specified
        if asset:
            asset_upper = asset.upper()
            markets = [
                m for m in markets
                if m.symbol.upper() == asset_upper
                or m.asset_address.lower() == asset.lower()
            ]

        return markets

    async def get_market_details(
        self,
        asset: str,
        chain: str = "ethereum",
    ) -> AaveMarket:
        """Get detailed market information for an asset."""
        self._validate_chain(chain)

        markets = await self.get_markets(asset=asset, chain=chain)
        
        if not markets:
            raise MarketNotFoundError(asset, chain)

        return markets[0]

    async def get_user_position(
        self,
        address: str,
        chain: str = "ethereum",
    ) -> AavePosition:
        """Get user's complete Aave position."""
        self._validate_chain(chain)
        self._validate_address(address)

        cache_key_params = {"chain": chain, "address": address.lower()}

        cached = await self._cache.get("aave", "position", **cache_key_params)
        if cached:
            logger.debug(f"Cache hit for Aave position {address}")
            return AavePosition.from_dict(cached)

        try:
            # Use fallback position for development
            position = self._get_fallback_position(address, chain)

            # Check if user has any position
            if (
                position.total_collateral_usd == 0
                and position.total_debt_usd == 0
                and not position.supplies
                and not position.borrows
            ):
                raise PositionNotFoundError(address, chain)

            await self._cache.set(
                "aave",
                "position",
                position.to_dict(),
                ttl=self._position_cache_ttl,
                **cache_key_params,
            )

            return position

        except (PositionNotFoundError, InvalidAddressError, UnsupportedChainError):
            raise
        except Exception as e:
            logger.error(f"Error fetching position for {address}: {e}")
            raise AaveAPIError(str(e)) from e

    async def get_health_factor(
        self,
        address: str,
        chain: str = "ethereum",
    ) -> HealthFactor:
        """Get user's health factor with risk analysis."""
        self._validate_chain(chain)
        self._validate_address(address)

        try:
            position = await self.get_user_position(address, chain)
            
            return HealthFactor.calculate(
                collateral_usd=position.total_collateral_usd,
                debt_usd=position.total_debt_usd,
                liquidation_threshold=Decimal("0.825"),  # Average threshold
            )

        except PositionNotFoundError:
            # No position means infinite health factor
            return HealthFactor.calculate(
                collateral_usd=Decimal("0"),
                debt_usd=Decimal("0"),
            )

    async def calculate_health_factor(
        self,
        collateral_usd: Decimal,
        debt_usd: Decimal,
        liquidation_threshold: Decimal = Decimal("0.825"),
    ) -> HealthFactor:
        """Calculate health factor from collateral and debt."""
        return HealthFactor.calculate(
            collateral_usd=collateral_usd,
            debt_usd=debt_usd,
            liquidation_threshold=liquidation_threshold,
        )

    async def get_available_to_borrow(
        self,
        address: str,
        asset: str,
        chain: str = "ethereum",
    ) -> Decimal:
        """Get maximum amount user can borrow of an asset."""
        self._validate_chain(chain)
        self._validate_address(address)

        position = await self.get_user_position(address, chain)
        market = await self.get_market_details(asset, chain)

        if not market.is_borrowable:
            return Decimal("0")

        # Calculate based on available borrow power
        if market.price_usd == 0:
            return Decimal("0")

        max_borrow_usd = position.available_borrow_usd
        max_borrow_asset = max_borrow_usd / market.price_usd

        # Also consider borrow cap
        cap_remaining = market.borrow_cap_remaining
        if cap_remaining < max_borrow_asset:
            max_borrow_asset = cap_remaining

        # Consider available liquidity
        if market.liquidity_available < max_borrow_asset:
            max_borrow_asset = market.liquidity_available

        return max(Decimal("0"), max_borrow_asset)

    async def get_liquidation_threshold(
        self,
        asset: str,
        chain: str = "ethereum",
    ) -> Decimal:
        """Get liquidation threshold for an asset."""
        market = await self.get_market_details(asset, chain)
        return market.liquidation_threshold

    async def get_protocol_stats(
        self,
        chain: str = "ethereum",
    ) -> dict:
        """Get protocol-wide statistics."""
        self._validate_chain(chain)

        cache_key_params = {"chain": chain}

        cached = await self._cache.get("aave", "stats", **cache_key_params)
        if cached:
            return cached

        try:
            # Use fallback stats for development
            stats = self._get_fallback_stats(chain)

            await self._cache.set(
                "aave",
                "stats",
                stats,
                ttl=self._stats_cache_ttl,
                **cache_key_params,
            )

            return stats

        except Exception as e:
            logger.error(f"Error fetching protocol stats: {e}")
            raise AaveAPIError(str(e)) from e

    async def get_supply_apy(
        self,
        asset: str,
        chain: str = "ethereum",
    ) -> Decimal:
        """Get current supply APY for an asset."""
        market = await self.get_market_details(asset, chain)
        return market.supply_apy

    async def get_borrow_apy(
        self,
        asset: str,
        chain: str = "ethereum",
        rate_type: str = "variable",
    ) -> Decimal:
        """Get current borrow APY for an asset."""
        market = await self.get_market_details(asset, chain)
        
        if rate_type == "stable":
            return market.borrow_apy_stable
        return market.borrow_apy_variable

    # =========================================================================
    # Fallback Data Methods (for development/testing)
    # =========================================================================

    def _get_fallback_markets(self, chain: str) -> list[AaveMarket]:
        """Get fallback market data for development."""
        return [
            AaveMarket(
                asset_address="0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
                symbol="USDC",
                name="USD Coin",
                chain=chain,
                decimals=6,
                supply_apy=Decimal("0.045"),
                total_supplied=Decimal("2500000000"),
                total_supplied_usd=Decimal("2500000000"),
                borrow_apy_variable=Decimal("0.052"),
                borrow_apy_stable=Decimal("0.065"),
                total_borrowed=Decimal("1800000000"),
                total_borrowed_usd=Decimal("1800000000"),
                utilization_rate=Decimal("72"),
                liquidity_available=Decimal("700000000"),
                ltv=Decimal("0.80"),
                liquidation_threshold=Decimal("0.85"),
                liquidation_bonus=Decimal("0.05"),
                price_usd=Decimal("1.0"),
                updated_at=datetime.now(timezone.utc),
            ),
            AaveMarket(
                asset_address="0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2",
                symbol="WETH",
                name="Wrapped Ether",
                chain=chain,
                decimals=18,
                supply_apy=Decimal("0.025"),
                total_supplied=Decimal("500000"),
                total_supplied_usd=Decimal("1000000000"),
                borrow_apy_variable=Decimal("0.035"),
                borrow_apy_stable=Decimal("0.045"),
                total_borrowed=Decimal("350000"),
                total_borrowed_usd=Decimal("700000000"),
                utilization_rate=Decimal("70"),
                liquidity_available=Decimal("150000"),
                ltv=Decimal("0.82"),
                liquidation_threshold=Decimal("0.86"),
                liquidation_bonus=Decimal("0.05"),
                price_usd=Decimal("2000"),
                updated_at=datetime.now(timezone.utc),
            ),
            AaveMarket(
                asset_address="0x2260FAC5E5542a773Aa44fBCfeDf7C193bc2C599",
                symbol="WBTC",
                name="Wrapped Bitcoin",
                chain=chain,
                decimals=8,
                supply_apy=Decimal("0.015"),
                total_supplied=Decimal("15000"),
                total_supplied_usd=Decimal("600000000"),
                borrow_apy_variable=Decimal("0.022"),
                borrow_apy_stable=Decimal("0.030"),
                total_borrowed=Decimal("9000"),
                total_borrowed_usd=Decimal("360000000"),
                utilization_rate=Decimal("60"),
                liquidity_available=Decimal("6000"),
                ltv=Decimal("0.72"),
                liquidation_threshold=Decimal("0.78"),
                liquidation_bonus=Decimal("0.06"),
                price_usd=Decimal("40000"),
                updated_at=datetime.now(timezone.utc),
            ),
        ]

    def _get_fallback_position(self, address: str, chain: str) -> AavePosition:
        """Get fallback position data for development."""
        return AavePosition(
            user_address=address.lower(),
            chain=chain,
            total_collateral_usd=Decimal("10000"),
            total_debt_usd=Decimal("4000"),
            available_borrow_usd=Decimal("4500"),
            net_worth_usd=Decimal("6000"),
            health_factor=Decimal("2.0625"),
            current_ltv=Decimal("0.40"),
            max_ltv=Decimal("0.80"),
            supplies=[
                AaveSupplyPosition(
                    asset_address="0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
                    symbol="USDC",
                    balance=Decimal("10000"),
                    balance_usd=Decimal("10000"),
                    apy=Decimal("0.045"),
                    is_collateral=True,
                )
            ],
            borrows=[
                AaveBorrowPosition(
                    asset_address="0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2",
                    symbol="WETH",
                    balance=Decimal("2.0"),
                    balance_usd=Decimal("4000"),
                    apy=Decimal("0.035"),
                    borrow_type="variable",
                )
            ],
            updated_at=datetime.now(timezone.utc),
        )

    def _get_fallback_stats(self, chain: str) -> dict:
        """Get fallback protocol stats for development."""
        return {
            "chain": chain,
            "total_tvl_usd": "15000000000",
            "total_supplied_usd": "18000000000",
            "total_borrowed_usd": "12000000000",
            "num_markets": 35,
        }
