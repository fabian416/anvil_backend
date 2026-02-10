"""
Aave Gateway Adapter.

Implements the AaveGateway port with caching
for market and position data.
Uses AaveClient for real on-chain position when RPC is available.
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
from app.infrastructure.adapters.external.aave_client import AaveClient
from app.infrastructure.adapters.external.aave_contract_helper import (
    generate_withdraw_transaction,
)
from app.infrastructure.cache.external_api_cache import ExternalAPICache

logger = logging.getLogger(__name__)

# Aave V3 pool addresses by chain (for withdraw tx building)
AAVE_POOL_ADDRESSES = {
    "ethereum": "0x87870Bca3F3fD6335C3F4ce8392D69350B4fA4E2",
    "base": "0xA238Dd80C259a72e81d7e4664a9801593F98d1C5",
    "polygon": "0x794a61358D6845594F94dc1DB02A252b5b4814aD",
    "arbitrum": "0x794a61358D6845594F94dc1DB02A252b5b4814aD",
    "optimism": "0x794a61358D6845594F94dc1DB02A252b5b4814aD",
    "avalanche": "0x794a61358D6845594F94dc1DB02A252b5b4814aD",
}

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
                m
                for m in markets
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
        """Get user's complete Aave position from on-chain data when available."""
        self._validate_chain(chain)
        self._validate_address(address)

        cache_key_params = {"chain": chain, "address": address.lower()}

        cached = await self._cache.get("aave", "position", **cache_key_params)
        if cached:
            logger.debug(f"Cache hit for Aave position {address}")
            return AavePosition.from_dict(cached)

        try:
            # Prefer real on-chain data via AaveClient
            position = await self._get_position_via_client(address, chain)
            if position is None:
                raise PositionNotFoundError(address, chain)

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

    # Synthetic "USD" supply is used when position has only aggregate data; map to
    # real market for withdraw (USDC is the main stablecoin on supported chains).
    _WITHDRAW_SYMBOL_MAP = {"USD": "USDC"}

    async def build_withdraw_supply_transaction(
        self,
        user_address: str,
        asset_symbol: str,
        amount: str,
        chain: str = "base",
    ) -> dict:
        """Build Aave V3 withdraw supply transaction for frontend signing."""
        try:
            pool_address = AAVE_POOL_ADDRESSES.get(chain.lower())
            if not pool_address:
                return {
                    "success": False,
                    "error": f"Aave V3 pool not configured for chain {chain}",
                    "chain": chain,
                }
            # Map synthetic aggregate symbol to real market for withdraw
            lookup_symbol = self._WITHDRAW_SYMBOL_MAP.get(
                asset_symbol.strip().upper(), asset_symbol
            )
            market = await self.get_market_details(asset=lookup_symbol, chain=chain)
            tx = generate_withdraw_transaction(
                pool_address=pool_address,
                asset_address=market.asset_address,
                amount=amount,
                asset_decimals=market.decimals,
                user_address=user_address,
            )
            return {
                "success": True,
                "to": tx["to"],
                "data": tx["data"],
                "value": tx.get("value", "0"),
                "asset_address": market.asset_address,
                "asset": lookup_symbol,
                "amount": amount,
                "chain": chain,
            }
        except Exception as e:
            logger.error(f"Aave build_withdraw_supply error: {e}")
            return {"success": False, "error": str(e), "chain": chain}

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

    async def _get_position_via_client(
        self, address: str, chain: str
    ) -> AavePosition | None:
        """
        Fetch position from AaveClient (on-chain). Returns None if no position.
        When client returns aggregates but no per-asset supplies, builds one
        synthetic supply so 'my lendings' shows the correct total.
        """
        client = AaveClient(chain=chain, api_key=self._api_key)
        try:
            raw = await client.get_user_position(address)
        except Exception as e:
            logger.debug("AaveClient get_user_position failed: %s", e)
            return None
        finally:
            await client.close()

        if not raw:
            return None

        total_collateral_usd = Decimal(str(raw.get("total_collateral_usd", "0")))
        total_debt_usd = Decimal(str(raw.get("total_debt_usd", "0")))
        available_borrow_usd = Decimal(str(raw.get("available_borrow_usd", "0")))
        net_worth_usd = Decimal(str(raw.get("net_worth_usd", "0")))
        hf_str = raw.get("health_factor", "inf")
        health_factor = (
            Decimal("inf")
            if str(hf_str).lower() in ("inf", "∞", "infinity")
            else Decimal(str(hf_str))
        )
        current_ltv = Decimal(str(raw.get("current_ltv", "0")))
        max_ltv = Decimal(str(raw.get("max_ltv", "0")))

        supplies: list[AaveSupplyPosition] = []
        for s in raw.get("supplies") or []:
            supplies.append(
                AaveSupplyPosition(
                    asset_address=s.get("asset_address", ""),
                    symbol=s.get("symbol", "?"),
                    balance=Decimal(str(s.get("balance", "0"))),
                    balance_usd=Decimal(str(s.get("balance_usd", "0"))),
                    apy=Decimal(str(s.get("apy", "0"))),
                    is_collateral=s.get("is_collateral", True),
                )
            )

        # Client often returns supplies=[]; use aggregate so UI shows correct total
        if not supplies and total_collateral_usd > 0:
            supplies = [
                AaveSupplyPosition(
                    asset_address="",
                    symbol="USD",
                    balance=total_collateral_usd,
                    balance_usd=total_collateral_usd,
                    apy=Decimal("0"),
                    is_collateral=True,
                )
            ]

        borrows: list[AaveBorrowPosition] = []
        for b in raw.get("borrows") or []:
            borrows.append(
                AaveBorrowPosition(
                    asset_address=b.get("asset_address", ""),
                    symbol=b.get("symbol", "?"),
                    balance=Decimal(str(b.get("balance", "0"))),
                    balance_usd=Decimal(str(b.get("balance_usd", "0"))),
                    apy=Decimal(str(b.get("apy", "0"))),
                    borrow_type=b.get("borrow_type", "variable"),
                )
            )

        return AavePosition(
            user_address=raw.get("user_address", address.lower()),
            chain=raw.get("chain", chain),
            total_collateral_usd=total_collateral_usd,
            total_debt_usd=total_debt_usd,
            available_borrow_usd=available_borrow_usd,
            net_worth_usd=net_worth_usd,
            health_factor=health_factor,
            current_ltv=current_ltv,
            max_ltv=max_ltv,
            supplies=supplies,
            borrows=borrows,
            updated_at=datetime.now(timezone.utc),
        )

    # =========================================================================
    # Fallback Data Methods (for development/testing)
    # =========================================================================

    def _get_fallback_markets(self, chain: str) -> list[AaveMarket]:
        """Get fallback market data for development with correct chain-specific addresses."""
        # Asset addresses by chain
        ASSET_ADDRESSES = {
            "ethereum": {
                "USDC": "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
                "WETH": "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2",
                "WBTC": "0x2260FAC5E5542a773Aa44fBCfeDf7C193bc2C599",
            },
            "base": {
                "USDC": "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913",
                "WETH": "0x4200000000000000000000000000000000000006",  # Base WETH
                "WBTC": "0x0555E30da8f98308EdB960aa94C0Db47230d2B9c",  # Base WBTC (wrapped)
            },
            "polygon": {
                "USDC": "0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174",
                "WETH": "0x7ceB23fD6bC0adD59E62ac25578270cFf1b9f619",
                "WBTC": "0x1BFD67037B42Cf73acF2047067bd4F2C47D9BfD6",
            },
            "arbitrum": {
                "USDC": "0xaf88d065e77c8cC2239327C5EDb3A432268e5831",
                "WETH": "0x82aF49447D8a07e3bd95BD0d56f35241523fBab1",
                "WBTC": "0x2f2a2543B76A4166549F7aaB2e75Bef0aefC5B0f",
            },
            "optimism": {
                "USDC": "0x7F5c764cBc14f9669B88837ca1490cCa17c31607",
                "WETH": "0x4200000000000000000000000000000000000006",
                "WBTC": "0x68f180fcCe6836688e9084f035309E29Bf0A2095",
            },
            "avalanche": {
                "USDC": "0xB97EF9Ef8734C71904D8002F8b6Bc66Dd9c48a6E",
                "WETH": "0x49D5c2BdFfac6CE2BFdB6640F4F80f226bc10bAB",  # WETH.e
                "WBTC": "0x50b7545627a5162F82A992c33b87aDc75187B218",  # WBTC.e
            },
        }

        # Get addresses for the current chain, fallback to Ethereum
        addresses = ASSET_ADDRESSES.get(chain, ASSET_ADDRESSES["ethereum"])

        return [
            AaveMarket(
                asset_address=addresses["USDC"],
                symbol="USDC",
                name="USD Coin",
                chain=chain,
                decimals=6,
                supply_apy=Decimal("0.045"),
                total_supplied=Decimal("2500000000"),
                total_supplied_usd=Decimal("2500000000"),
                supply_cap=Decimal("3000000000"),
                borrow_apy_variable=Decimal("0.052"),
                borrow_apy_stable=Decimal("0.065"),
                total_borrowed=Decimal("1800000000"),
                total_borrowed_usd=Decimal("1800000000"),
                borrow_cap=Decimal("2500000000"),
                utilization_rate=Decimal("72"),
                liquidity_available=Decimal("700000000"),
                ltv=Decimal("0.80"),
                liquidation_threshold=Decimal("0.85"),
                liquidation_bonus=Decimal("0.05"),
                price_usd=Decimal("1.0"),
                is_active=True,
                is_frozen=False,
                is_paused=False,
                can_use_as_collateral=True,
                can_borrow=True,
                updated_at=datetime.now(timezone.utc),
            ),
            AaveMarket(
                asset_address=addresses["WETH"],
                symbol="WETH",
                name="Wrapped Ether",
                chain=chain,
                decimals=18,
                supply_apy=Decimal("0.025"),
                total_supplied=Decimal("500000"),
                total_supplied_usd=Decimal("1000000000"),
                supply_cap=Decimal("600000"),
                borrow_apy_variable=Decimal("0.035"),
                borrow_apy_stable=Decimal("0.045"),
                total_borrowed=Decimal("350000"),
                total_borrowed_usd=Decimal("700000000"),
                borrow_cap=Decimal("500000"),
                utilization_rate=Decimal("70"),
                liquidity_available=Decimal("150000"),
                ltv=Decimal("0.82"),
                liquidation_threshold=Decimal("0.86"),
                liquidation_bonus=Decimal("0.05"),
                price_usd=Decimal("2000"),
                is_active=True,
                is_frozen=False,
                is_paused=False,
                can_use_as_collateral=True,
                can_borrow=True,
                updated_at=datetime.now(timezone.utc),
            ),
            AaveMarket(
                asset_address=addresses["WBTC"],
                symbol="WBTC",
                name="Wrapped Bitcoin",
                chain=chain,
                decimals=8,
                supply_apy=Decimal("0.015"),
                total_supplied=Decimal("15000"),
                total_supplied_usd=Decimal("600000000"),
                supply_cap=Decimal("20000"),
                borrow_apy_variable=Decimal("0.022"),
                borrow_apy_stable=Decimal("0.030"),
                total_borrowed=Decimal("9000"),
                total_borrowed_usd=Decimal("360000000"),
                borrow_cap=Decimal("15000"),
                utilization_rate=Decimal("60"),
                liquidity_available=Decimal("6000"),
                ltv=Decimal("0.72"),
                liquidation_threshold=Decimal("0.78"),
                liquidation_bonus=Decimal("0.06"),
                price_usd=Decimal("40000"),
                is_active=True,
                is_frozen=False,
                is_paused=False,
                can_use_as_collateral=True,
                can_borrow=True,
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
