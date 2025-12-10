"""
Aave Gateway Adapter.

Implements the AaveGateway port using the AaveClient
with caching for market and position data.
"""

import logging
import re
from datetime import datetime
from decimal import Decimal

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
from app.infrastructure.adapters.external.aave_client import AaveClient
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
        client: AaveClient,
        cache: ExternalAPICache,
        market_cache_ttl: int = DEFAULT_MARKET_CACHE_TTL,
        position_cache_ttl: int = DEFAULT_POSITION_CACHE_TTL,
        stats_cache_ttl: int = DEFAULT_STATS_CACHE_TTL,
    ):
        """Initialize AaveAdapter."""
        self._client = client
        self._cache = cache
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
                # Create client with correct chain
                client = AaveClient(
                    api_key=self._client._api_key,
                    chain=chain,
                )

                try:
                    raw_markets = await client.get_market_data()
                    markets = [self._transform_market(m, chain) for m in raw_markets]

                    await self._cache.set(
                        "aave",
                        "markets",
                        [m.to_dict() for m in markets],
                        ttl=self._market_cache_ttl,
                        **cache_key_params,
                    )
                    logger.debug(f"Fetched {len(markets)} Aave markets on {chain}")

                finally:
                    await client.close()

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
            # Create client with correct chain
            client = AaveClient(
                api_key=self._client._api_key,
                chain=chain,
            )

            try:
                raw_position = await client.get_user_position(address)
                position = self._transform_position(raw_position, chain)

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

            finally:
                await client.close()

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
            client = AaveClient(
                api_key=self._client._api_key,
                chain=chain,
            )

            try:
                stats = await client.get_protocol_stats()

                await self._cache.set(
                    "aave",
                    "stats",
                    stats,
                    ttl=self._stats_cache_ttl,
                    **cache_key_params,
                )

                return stats

            finally:
                await client.close()

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
    # Transformation Methods
    # =========================================================================

    def _transform_market(self, raw, chain: str) -> AaveMarket:
        """Transform client market data to domain entity."""
        return AaveMarket(
            asset_address=raw.asset,
            symbol=raw.symbol,
            name=raw.name,
            chain=chain,
            decimals=raw.decimals,
            supply_apy=Decimal(str(raw.supply_apy)) / 100,  # Convert to decimal
            total_supplied=Decimal(str(raw.total_supplied)),
            total_supplied_usd=Decimal(str(raw.total_supplied_usd)),
            supply_cap=Decimal("0"),  # Not available in basic API
            borrow_apy_variable=Decimal(str(raw.borrow_apy_variable)) / 100,
            borrow_apy_stable=Decimal(str(raw.borrow_apy_stable)) / 100,
            total_borrowed=Decimal(str(raw.total_borrowed)),
            total_borrowed_usd=Decimal(str(raw.total_borrowed_usd)),
            borrow_cap=Decimal("0"),
            utilization_rate=Decimal(str(raw.utilization_rate)),
            liquidity_available=Decimal(str(raw.liquidity_available)),
            ltv=Decimal(str(raw.ltv)),
            liquidation_threshold=Decimal(str(raw.liquidation_threshold)),
            liquidation_bonus=Decimal(str(raw.liquidation_bonus)),
            is_active=True,
            is_frozen=False,
            is_paused=False,
            can_use_as_collateral=raw.ltv > 0,
            can_borrow=True,
            e_mode_category=0,
            e_mode_label=None,
            price_usd=Decimal(str(raw.total_supplied_usd)) / Decimal(str(raw.total_supplied)) if raw.total_supplied > 0 else Decimal("0"),
            updated_at=datetime.utcnow(),
        )

    def _transform_position(self, raw, chain: str) -> AavePosition:
        """Transform client position data to domain entity."""
        # Transform supplies
        supplies = [
            AaveSupplyPosition(
                asset_address=s.get("asset", ""),
                symbol=s.get("symbol", ""),
                balance=Decimal(str(s.get("balance", "0"))),
                balance_usd=Decimal(str(s.get("value_usd", "0"))),
                apy=Decimal("0"),  # Would need market data
                is_collateral=s.get("as_collateral", True),
            )
            for s in raw.supplies
        ]

        # Transform borrows
        borrows = [
            AaveBorrowPosition(
                asset_address=b.get("asset", ""),
                symbol=b.get("symbol", ""),
                balance=Decimal(str(b.get("balance", "0"))),
                balance_usd=Decimal(str(b.get("value_usd", "0"))),
                apy=Decimal("0"),  # Would need market data
                borrow_type="variable" if b.get("variable_debt", 0) > 0 else "stable",
            )
            for b in raw.borrows
        ]

        # Parse health factor
        hf = raw.health_factor
        if hf == float("inf"):
            health_factor = Decimal("inf")
        else:
            health_factor = Decimal(str(hf))

        total_collateral = Decimal(str(raw.total_collateral_usd))
        total_debt = Decimal(str(raw.total_debt_usd))

        return AavePosition(
            user_address=raw.user_address.lower(),
            chain=chain,
            total_collateral_usd=total_collateral,
            total_debt_usd=total_debt,
            available_borrow_usd=Decimal(str(raw.available_borrow_usd)),
            net_worth_usd=total_collateral - total_debt,
            health_factor=health_factor,
            current_ltv=Decimal(str(raw.ltv)),
            max_ltv=Decimal("0.7"),  # Average max LTV
            e_mode_category=0,
            e_mode_label=None,
            supplies=supplies,
            borrows=borrows,
            updated_at=datetime.utcnow(),
        )
