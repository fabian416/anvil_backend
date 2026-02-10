"""
Morpho Gateway Adapter.

Implements the MorphoGateway port using the MorphoClient
with caching for vault and position data.

Supports multiple chains:
- Ethereum (chain_id: 1)
- Base (chain_id: 8453)
"""

import logging
import re
from decimal import Decimal

from app.domain.entities.lending.morpho_market import MorphoMarket
from app.domain.entities.lending.morpho_position import MorphoPosition
from app.domain.entities.lending.morpho_vault import MorphoVault
from app.domain.exceptions.morpho import (
    InvalidVaultAddressError,
    MorphoAPIError,
    VaultNotFoundError,
)
from app.domain.ports.morpho_gateway import MorphoGateway
from app.domain.value_objects.lending.market_allocation import MarketAllocation
from app.domain.value_objects.lending.risk_tier import RiskTier
from app.domain.value_objects.lending.vault_apy import VaultAPY
from app.infrastructure.adapters.external.morpho_client import (
    CHAIN_IDS,
    MorphoClient,
    MorphoMarketData,
    MorphoPositionData,
    MorphoVaultData,
)
from app.infrastructure.cache.external_api_cache import ExternalAPICache

logger = logging.getLogger(__name__)

# Ethereum address pattern
ETH_ADDRESS_PATTERN = re.compile(r"^0x[a-fA-F0-9]{40}$")

# Chain-specific asset addresses (Morpho API sometimes returns wrong addresses)
# This mapping ensures we use the correct on-chain addresses for each network
ASSET_ADDRESSES = {
    "base": {
        "USDC": "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913",
        "USDT": "0xfde4C96c8593536E31F229EA8f37b2ADa2699bb2",
        "DAI": "0x50c5725949A6F0c72E6C4a641F24049A917DB0Cb",
        "WETH": "0x4200000000000000000000000000000000000006",
        "ETH": "0x4200000000000000000000000000000000000006",  # WETH on Base
        "WBTC": "0x0555E30da8f98308EdB960aa94C0Db47230d2B9c",
    },
    "ethereum": {
        "USDC": "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
        "USDT": "0xdAC17F958D2ee523a2206206994597C13D831ec7",
        "DAI": "0x6B175474E89094C44Da98b954EedeAC495271d0F",
        "WETH": "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2",
        "ETH": "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2",
        "WBTC": "0x2260FAC5E5542a773Aa44fBCfeDf7C193bc2C599",
    },
}


def _get_chain_id(chain: str) -> int:
    """Convert chain name to chain ID."""
    return CHAIN_IDS.get(chain.lower(), 1)


class MorphoAdapter(MorphoGateway):
    """
    Morpho implementation of MorphoGateway.

    Uses caching for vault and position data:
    - Vaults: 10 min cache
    - APY: 5 min cache
    - Positions: 10 min cache
    """

    DEFAULT_VAULT_CACHE_TTL = 600  # 10 minutes
    DEFAULT_APY_CACHE_TTL = 300  # 5 minutes
    DEFAULT_POSITION_CACHE_TTL = 600  # 10 minutes
    DEFAULT_MARKET_CACHE_TTL = 300  # 5 minutes

    # Risk thresholds
    LLTV_HIGH_THRESHOLD = Decimal("0.85")
    UTILIZATION_HIGH_THRESHOLD = Decimal("0.90")

    def __init__(
        self,
        client: MorphoClient,
        cache: ExternalAPICache,
        vault_cache_ttl: int = DEFAULT_VAULT_CACHE_TTL,
        apy_cache_ttl: int = DEFAULT_APY_CACHE_TTL,
        position_cache_ttl: int = DEFAULT_POSITION_CACHE_TTL,
        market_cache_ttl: int = DEFAULT_MARKET_CACHE_TTL,
    ):
        """Initialize MorphoAdapter."""
        self._client = client
        self._cache = cache
        self._vault_cache_ttl = vault_cache_ttl
        self._apy_cache_ttl = apy_cache_ttl
        self._position_cache_ttl = position_cache_ttl
        self._market_cache_ttl = market_cache_ttl

    async def get_vaults(
        self,
        asset: str | None = None,
        chain: str = "ethereum",
    ) -> list[MorphoVault]:
        """
        Get MetaMorpho vaults with caching.

        Args:
            asset: Filter by underlying asset symbol (e.g., "USDC")
            chain: Blockchain ("ethereum" or "base")

        Returns:
            List of MorphoVault entities
        """
        chain_id = _get_chain_id(chain)
        cache_key_params = {"chain": chain}

        cached = await self._cache.get("morpho", "vaults", **cache_key_params)
        if cached:
            logger.debug(f"Cache hit for Morpho vaults on {chain}")
            vaults = [MorphoVault.from_dict(v) for v in cached]
        else:
            try:
                # Pass chain_id to the client
                raw_vaults = await self._client.get_vaults(chain_id=chain_id)
                vaults = [self._transform_vault(v) for v in raw_vaults]

                await self._cache.set(
                    "morpho",
                    "vaults",
                    [v.to_dict() for v in vaults],
                    ttl=self._vault_cache_ttl,
                    **cache_key_params,
                )
                logger.debug(f"Fetched {len(vaults)} Morpho vaults on {chain}")

            except Exception as e:
                logger.error(f"Error fetching Morpho vaults on {chain}: {e}")
                raise MorphoAPIError(str(e)) from e

        # Filter by asset if specified
        if asset:
            vaults = [v for v in vaults if v.asset.upper() == asset.upper()]

        return vaults

    async def get_vault_details(
        self,
        vault_address: str,
        chain: str = "ethereum",
    ) -> MorphoVault:
        """Get detailed vault information."""
        if not ETH_ADDRESS_PATTERN.match(vault_address):
            raise InvalidVaultAddressError(vault_address)

        chain_id = _get_chain_id(chain)
        cache_key_params = {"chain": chain, "address": vault_address.lower()}

        cached = await self._cache.get("morpho", "vault_details", **cache_key_params)
        if cached:
            return MorphoVault.from_dict(cached)

        try:
            raw_vault = await self._client.get_vault(vault_address, chain_id=chain_id)
            if not raw_vault:
                raise VaultNotFoundError(vault_address, chain)

            vault = self._transform_vault(raw_vault)

            await self._cache.set(
                "morpho",
                "vault_details",
                vault.to_dict(),
                ttl=self._vault_cache_ttl,
                **cache_key_params,
            )

            return vault

        except VaultNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Error fetching vault {vault_address} on {chain}: {e}")
            raise MorphoAPIError(str(e)) from e

    async def get_vault_apy(
        self,
        vault_address: str,
        chain: str = "ethereum",
    ) -> VaultAPY:
        """Get vault APY with historical data."""
        if not ETH_ADDRESS_PATTERN.match(vault_address):
            raise InvalidVaultAddressError(vault_address)

        chain_id = _get_chain_id(chain)
        cache_key_params = {"chain": chain, "address": vault_address.lower()}

        cached = await self._cache.get("morpho", "apy", **cache_key_params)
        if cached:
            return VaultAPY.from_dict(cached)

        try:
            raw_apy = await self._client.get_vault_apy(vault_address, chain_id=chain_id)
            apy = self._transform_apy(vault_address, raw_apy)

            await self._cache.set(
                "morpho",
                "apy",
                apy.to_dict(),
                ttl=self._apy_cache_ttl,
                **cache_key_params,
            )

            return apy

        except Exception as e:
            logger.error(f"Error fetching APY for {vault_address} on {chain}: {e}")
            raise MorphoAPIError(str(e)) from e

    async def get_markets(
        self,
        chain: str = "ethereum",
    ) -> list[MorphoMarket]:
        """Get Morpho Blue markets."""
        chain_id = _get_chain_id(chain)
        cache_key_params = {"chain": chain}

        cached = await self._cache.get("morpho", "markets", **cache_key_params)
        if cached:
            return [MorphoMarket.from_dict(m) for m in cached]

        try:
            raw_markets = await self._client.get_markets(chain_id=chain_id)
            markets = [self._transform_market(m) for m in raw_markets]

            await self._cache.set(
                "morpho",
                "markets",
                [m.to_dict() for m in markets],
                ttl=self._market_cache_ttl,
                **cache_key_params,
            )

            return markets

        except Exception as e:
            logger.error(f"Error fetching Morpho markets on {chain}: {e}")
            raise MorphoAPIError(str(e)) from e

    async def get_user_positions(
        self,
        address: str,
        chain: str = "ethereum",
    ) -> list[MorphoPosition]:
        """Get user vault positions."""
        if not ETH_ADDRESS_PATTERN.match(address):
            raise InvalidVaultAddressError(address, "Invalid wallet address format")

        chain_id = _get_chain_id(chain)
        cache_key_params = {"chain": chain, "address": address.lower()}

        cached = await self._cache.get("morpho", "positions", **cache_key_params)
        if cached:
            return [MorphoPosition.from_dict(p) for p in cached]

        try:
            raw_positions = await self._client.get_user_positions(
                address, chain_id=chain_id
            )
            positions = [self._transform_position(p, address) for p in raw_positions]

            await self._cache.set(
                "morpho",
                "positions",
                [p.to_dict() for p in positions],
                ttl=self._position_cache_ttl,
                **cache_key_params,
            )

            return positions

        except Exception as e:
            logger.error(f"Error fetching positions for {address} on {chain}: {e}")
            raise MorphoAPIError(str(e)) from e

    async def get_user_deposits(
        self,
        address: str,
        chain: str = "ethereum",
    ) -> list[MorphoPosition]:
        """Alias for get_user_positions."""
        return await self.get_user_positions(address, chain)

    async def build_withdraw_transaction(
        self,
        user_address: str,
        vault_address: str,
        amount: str,
        chain: str = "base",
    ) -> dict:
        """Build MetaMorpho vault withdraw transaction for frontend signing."""
        try:
            positions = await self.get_user_positions(
                address=user_address,
                chain=chain,
            )
            position = None
            for p in positions:
                if p.vault_address.lower() == vault_address.lower():
                    position = p
                    break
            if not position:
                return {
                    "success": False,
                    "error": f"No position found in vault {vault_address}",
                    "chain": chain,
                }
            if position.shares <= 0:
                return {
                    "success": False,
                    "error": "No supply to withdraw",
                    "chain": chain,
                }
            if amount.lower() == "max":
                withdraw_shares = int(position.shares)
                withdraw_amount = position.assets
            else:
                withdraw_amount = Decimal(amount)
                if withdraw_amount > position.assets:
                    return {
                        "success": False,
                        "error": (
                            f"Insufficient balance. You have {position.assets:.6f} "
                            f"{position.asset_symbol}"
                        ),
                        "chain": chain,
                    }
                if position.assets > 0:
                    share_ratio = float(withdraw_amount / position.assets)
                    withdraw_shares = int(float(position.shares) * share_ratio)
                else:
                    withdraw_shares = 0
            tx_data = self._build_metamorpho_withdraw_calldata(
                vault_address=vault_address,
                shares=withdraw_shares,
                user_address=user_address,
            )
            return {
                "success": True,
                "to": tx_data["to"],
                "data": tx_data["data"],
                "value": tx_data["value"],
                "amount": str(withdraw_amount),
                "asset": position.asset_symbol,
                "vault_name": position.vault_name,
                "chain": chain,
            }
        except Exception as e:
            logger.error(f"Morpho build_withdraw_transaction error: {e}")
            return {"success": False, "error": str(e), "chain": chain}

    def _build_metamorpho_withdraw_calldata(
        self,
        vault_address: str,
        shares: int,
        user_address: str,
    ) -> dict:
        """Build ERC4626 redeem(uint256,address,address) calldata for MetaMorpho."""
        function_selector = "0xba087652"
        shares_hex = hex(shares)[2:].zfill(64)
        receiver_hex = user_address.lower()[2:].zfill(64)
        owner_hex = user_address.lower()[2:].zfill(64)
        calldata = f"{function_selector}{shares_hex}{receiver_hex}{owner_hex}"
        return {
            "to": vault_address,
            "data": calldata,
            "value": "0x0",
        }

    # =========================================================================
    # Risk Calculation
    # =========================================================================

    def _calculate_risk_tier(
        self,
        max_lltv: Decimal,
        avg_utilization: Decimal,
    ) -> RiskTier:
        """Calculate risk tier based on vault allocations."""
        if max_lltv >= Decimal("0.90") and avg_utilization >= Decimal("0.85"):
            return RiskTier.VERY_HIGH
        elif (
            max_lltv >= self.LLTV_HIGH_THRESHOLD
            or avg_utilization >= self.UTILIZATION_HIGH_THRESHOLD
        ):
            return RiskTier.HIGH
        elif max_lltv >= Decimal("0.75") or avg_utilization >= Decimal("0.60"):
            return RiskTier.MEDIUM
        return RiskTier.LOW

    # =========================================================================
    # Transformation Methods
    # =========================================================================

    def _transform_vault(self, raw: MorphoVaultData) -> MorphoVault:
        """Transform client vault data to domain entity."""
        # Parse total assets with decimal handling
        try:
            total_assets_raw = Decimal(str(raw.total_assets))
            # Handle already-scaled values from new API (no 1e18 scaling needed)
            if total_assets_raw > Decimal("1e12"):
                total_assets = total_assets_raw / Decimal(10**raw.asset_decimals)
            else:
                total_assets = total_assets_raw
        except (ValueError, TypeError):
            total_assets = Decimal("0")

        try:
            total_shares_raw = Decimal(str(raw.total_supply))
            if total_shares_raw > Decimal("1e12"):
                total_shares = total_shares_raw / Decimal(10**raw.asset_decimals)
            else:
                total_shares = total_shares_raw
        except (ValueError, TypeError):
            total_shares = Decimal("0")

        # Fee is typically in basis points (1e4) or decimal (0.05)
        try:
            fee = Decimal(str(raw.performance_fee))
            if fee > 1:
                fee = fee / Decimal("10000")  # Convert from basis points
        except (ValueError, TypeError):
            fee = Decimal("0")

        # Transform allocations
        allocations = [self._transform_allocation(a) for a in raw.allocations]

        # Calculate risk tier
        max_lltv = Decimal("0")
        for alloc in allocations:
            if alloc.lltv > max_lltv:
                max_lltv = alloc.lltv

        risk_tier = self._calculate_risk_tier(max_lltv, Decimal("0.5"))

        # Parse APY from new API (already a decimal like 0.0452 = 4.52%)
        try:
            apy = Decimal(str(raw.net_apy))
            # If APY looks like percentage (e.g., 4.52), convert to decimal
            if apy > Decimal("1"):
                apy = apy / Decimal("100")
        except (ValueError, TypeError):
            apy = Decimal("0")

        # Map chain_id to chain name
        chain_name = "base" if raw.chain_id == 8453 else "ethereum"

        # CRITICAL FIX: Use chain-specific asset address
        # Morpho API sometimes returns Ethereum addresses for Base vaults
        asset_symbol_upper = raw.asset_symbol.upper()
        correct_asset_address = ASSET_ADDRESSES.get(chain_name, {}).get(
            asset_symbol_upper,
            raw.asset_address,  # Fallback to API value if not in mapping
        )

        # Log if we corrected the address
        if correct_asset_address != raw.asset_address:
            logger.warning(
                f"[MORPHO_ADAPTER] Corrected asset address for {raw.name} ({raw.asset_symbol}) "
                f"on {chain_name}: {raw.asset_address} → {correct_asset_address}"
            )

        return MorphoVault(
            address=raw.id,
            name=raw.name,
            symbol=raw.symbol,
            asset=raw.asset_symbol,
            asset_address=correct_asset_address,  # Use corrected address
            asset_decimals=raw.asset_decimals,
            total_assets=total_assets,
            total_shares=total_shares,
            apy=apy,
            fee_percentage=fee,
            curator_address=raw.curator,
            guardian_address=raw.guardian,
            risk_tier=risk_tier,
            market_allocations=allocations,
            chain=chain_name,
            whitelisted=raw.whitelisted,
        )

    def _transform_allocation(self, raw: dict) -> MarketAllocation:
        """Transform allocation data to domain value object."""
        market = raw.get("market", {})

        return MarketAllocation(
            market_id=market.get("id", ""),
            collateral_asset=market.get("collateralAsset", {}).get("symbol", ""),
            loan_asset="",  # Not always available
            allocation_percentage=Decimal(str(raw.get("assets", "0")))
            / Decimal("1e18"),
            lltv=Decimal(str(market.get("lltv", "0"))) / Decimal("1e18"),
            supply_apy=Decimal("0"),
        )

    def _transform_market(self, raw: MorphoMarketData) -> MorphoMarket:
        """Transform client market data to domain entity."""
        # Parse amounts
        total_supply = Decimal(raw.total_supply_assets)
        total_borrow = Decimal(raw.total_borrow_assets)

        # Parse APY (typically in percentage already)
        supply_apy = Decimal(raw.supply_rate)
        borrow_apy = Decimal(raw.borrow_rate)

        # Parse LLTV (typically 1e18 scaled)
        lltv = Decimal(raw.lltv)
        if lltv > 1:
            lltv = lltv / Decimal("1e18")

        return MorphoMarket(
            market_id=raw.id,
            collateral_asset=raw.collateral_symbol,
            collateral_address=raw.collateral_address,
            loan_asset=raw.loan_symbol,
            loan_address=raw.loan_address,
            lltv=lltv,
            oracle=raw.oracle,
            irm_address=raw.irm,
            total_supply=total_supply,
            total_borrow=total_borrow,
            supply_apy=supply_apy,
            borrow_apy=borrow_apy,
        )

    def _transform_position(
        self,
        raw: MorphoPositionData,
        user_address: str,
    ) -> MorphoPosition:
        """Transform client position data to domain entity.

        API returns assets in smallest units (e.g. 7000285 for 7.000285 USDC).
        Convert to human-readable using decimals; use assetsUsd from API when present.
        """
        shares = Decimal(raw.shares)
        decimals = raw.decimals or 18
        assets_raw = Decimal(raw.assets)
        assets_human = assets_raw / (Decimal(10) ** decimals)
        apy = Decimal(str(raw.net_apy)) if raw.net_apy else Decimal("0")
        assets_usd = getattr(raw, "assets_usd", None)
        if assets_usd is not None:
            try:
                assets_usd = float(assets_usd)
            except (TypeError, ValueError):
                assets_usd = None

        return MorphoPosition(
            user_address=user_address.lower(),
            vault_address=raw.vault_id,
            vault_name=raw.vault_name,
            asset_symbol=raw.asset_symbol,
            shares=shares,
            assets=assets_human,
            deposited_assets=assets_human,
            apy=apy,
            assets_usd=assets_usd,
        )

    def _transform_apy(self, vault_address: str, raw: dict) -> VaultAPY:
        """Transform APY data to domain value object."""
        return VaultAPY(
            vault_address=vault_address.lower(),
            base_apy=Decimal(str(raw.get("base_apy", "0"))),
            supply_apy=Decimal(str(raw.get("supply_apy", "0"))),
            reward_apy=Decimal(str(raw.get("reward_apy", "0"))),
            fee_percentage=Decimal(str(raw.get("fee", "0"))),
            apy_7d_avg=Decimal("0"),  # Would need historical data
            apy_30d_avg=Decimal("0"),
        )
