"""
DeFi Rates Service - Unified APY/Rate Aggregator.

Aggregates real-time lending rates from multiple DeFi protocols:
- Aave V3 (via DeFiLlama)
- Compound V3 (via DeFiLlama)
- Morpho (via DeFiLlama + Morpho API)

Uses DeFiLlama as primary data source for consistent, real-time data.
"""

import logging
from dataclasses import dataclass
from typing import Any

from app.infrastructure.adapters.external.defillama_client import DefiLlamaClient, YieldData
from app.infrastructure.cache.external_api_cache import ExternalAPICache

logger = logging.getLogger(__name__)


@dataclass
class ProtocolRate:
    """Rate data for a specific protocol."""
    
    protocol: str  # aave, compound, morpho
    protocol_name: str  # Display name
    asset: str  # USDC, ETH, etc.
    chain: str  # ethereum, base, etc.
    supply_apy: float  # Supply/Deposit APY
    borrow_apy: float | None  # Borrow APY (if applicable)
    tvl_usd: float  # Total Value Locked
    pool_id: str | None = None  # DeFiLlama pool ID
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "protocol": self.protocol,
            "name": self.protocol_name,
            "supply_apy": self.supply_apy,
            "borrow_apy": self.borrow_apy or 0,
            "tvl": self.tvl_usd,
            "utilization": 0,  # Not always available from DeFiLlama
        }


class DefiRatesService:
    """
    Unified service for fetching DeFi lending rates.
    
    Uses DeFiLlama as primary source for real-time APY data.
    Falls back to protocol-specific APIs if needed.
    """
    
    # Protocol slugs in DeFiLlama
    PROTOCOL_SLUGS = {
        "aave": ["aave-v3", "aave-v2"],
        "compound": ["compound-v3", "compound"],
        "morpho": ["morpho-blue", "morpho-aave", "morpho-compound"],
    }
    
    # Chain mappings (DeFiLlama uses different chain names)
    CHAIN_MAPPINGS = {
        "ethereum": "Ethereum",
        "base": "Base",
        "polygon": "Polygon",
        "arbitrum": "Arbitrum",
        "optimism": "Optimism",
        "avalanche": "Avalanche",
    }
    
    CACHE_TTL = 300  # 5 minutes
    
    def __init__(
        self,
        defillama_client: DefiLlamaClient | None = None,
        cache: ExternalAPICache | None = None,
    ):
        """Initialize DeFi rates service."""
        self._defillama = defillama_client or DefiLlamaClient()
        self._cache = cache
    
    async def get_all_rates(
        self,
        asset: str,
        chain: str = "base",
    ) -> list[ProtocolRate]:
        """
        Get lending rates from all supported protocols.
        
        Args:
            asset: Asset symbol (USDC, ETH, DAI, etc.)
            chain: Blockchain (base, ethereum, etc.)
            
        Returns:
            List of ProtocolRate sorted by supply_apy (highest first)
        """
        rates = []
        
        # Fetch from each protocol
        aave_rate = await self.get_aave_rate(asset, chain)
        if aave_rate:
            rates.append(aave_rate)
        
        compound_rate = await self.get_compound_rate(asset, chain)
        if compound_rate:
            rates.append(compound_rate)
        
        morpho_rate = await self.get_morpho_rate(asset, chain)
        if morpho_rate:
            rates.append(morpho_rate)
        
        # Sort by supply APY (highest first)
        rates.sort(key=lambda r: r.supply_apy, reverse=True)
        
        return rates
    
    async def get_aave_rate(
        self,
        asset: str,
        chain: str = "base",
    ) -> ProtocolRate | None:
        """Get Aave V3 lending rate for asset."""
        
        try:
            cache_key = f"aave_rate:{chain}:{asset.upper()}"
            
            # Check cache
            if self._cache:
                cached = await self._cache.get("defi_rates", cache_key)
                if cached:
                    return ProtocolRate(**cached)
            
            # Fetch from DeFiLlama
            yields = await self._defillama.get_protocol_yields(protocol="aave-v3")
            
            # Filter by chain and asset
            chain_name = self.CHAIN_MAPPINGS.get(chain.lower(), chain.title())
            asset_upper = asset.upper()
            
            matching = [
                y for y in yields
                if y.chain.lower() == chain_name.lower()
                and self._matches_asset(y.symbol, asset_upper)
            ]
            
            if not matching:
                logger.debug(f"No Aave rate found for {asset} on {chain}")
                return None
            
            # Get best matching pool (highest APY)
            best = max(matching, key=lambda y: y.apy)
            
            rate = ProtocolRate(
                protocol="aave",
                protocol_name="Aave V3",
                asset=asset_upper,
                chain=chain,
                supply_apy=best.apy,
                borrow_apy=None,  # DeFiLlama doesn't provide borrow rates
                tvl_usd=best.tvl_usd,
                pool_id=best.pool,
            )
            
            # Cache result
            if self._cache:
                await self._cache.set(
                    "defi_rates",
                    cache_key,
                    rate.__dict__,
                    ttl=self.CACHE_TTL,
                )
            
            return rate
            
        except Exception as e:
            logger.error(f"Error fetching Aave rate: {e}")
            return None
    
    async def get_compound_rate(
        self,
        asset: str,
        chain: str = "base",
    ) -> ProtocolRate | None:
        """Get Compound V3 lending rate for asset."""
        
        try:
            cache_key = f"compound_rate:{chain}:{asset.upper()}"
            
            # Check cache
            if self._cache:
                cached = await self._cache.get("defi_rates", cache_key)
                if cached:
                    return ProtocolRate(**cached)
            
            # Fetch from DeFiLlama
            yields = await self._defillama.get_protocol_yields(protocol="compound-v3")
            
            # Filter by chain and asset
            chain_name = self.CHAIN_MAPPINGS.get(chain.lower(), chain.title())
            asset_upper = asset.upper()
            
            matching = [
                y for y in yields
                if y.chain.lower() == chain_name.lower()
                and self._matches_asset(y.symbol, asset_upper)
            ]
            
            if not matching:
                logger.debug(f"No Compound rate found for {asset} on {chain}")
                return None
            
            # Get best matching pool
            best = max(matching, key=lambda y: y.apy)
            
            rate = ProtocolRate(
                protocol="compound",
                protocol_name="Compound V3",
                asset=asset_upper,
                chain=chain,
                supply_apy=best.apy,
                borrow_apy=None,
                tvl_usd=best.tvl_usd,
                pool_id=best.pool,
            )
            
            # Cache result
            if self._cache:
                await self._cache.set(
                    "defi_rates",
                    cache_key,
                    rate.__dict__,
                    ttl=self.CACHE_TTL,
                )
            
            return rate
            
        except Exception as e:
            logger.error(f"Error fetching Compound rate: {e}")
            return None
    
    async def get_morpho_rate(
        self,
        asset: str,
        chain: str = "base",
    ) -> ProtocolRate | None:
        """Get Morpho vault rate for asset."""
        
        try:
            cache_key = f"morpho_rate:{chain}:{asset.upper()}"
            
            # Check cache
            if self._cache:
                cached = await self._cache.get("defi_rates", cache_key)
                if cached:
                    return ProtocolRate(**cached)
            
            # Fetch from DeFiLlama (try multiple Morpho protocols)
            all_morpho_yields = []
            for protocol in self.PROTOCOL_SLUGS["morpho"]:
                try:
                    yields = await self._defillama.get_protocol_yields(protocol=protocol)
                    all_morpho_yields.extend(yields)
                except Exception:
                    continue
            
            # Filter by chain and asset
            chain_name = self.CHAIN_MAPPINGS.get(chain.lower(), chain.title())
            asset_upper = asset.upper()
            
            matching = [
                y for y in all_morpho_yields
                if y.chain.lower() == chain_name.lower()
                and self._matches_asset(y.symbol, asset_upper)
            ]
            
            if not matching:
                logger.debug(f"No Morpho rate found for {asset} on {chain}")
                return None
            
            # Get best matching pool
            best = max(matching, key=lambda y: y.apy)
            
            rate = ProtocolRate(
                protocol="morpho",
                protocol_name=f"Morpho ({best.project})",
                asset=asset_upper,
                chain=chain,
                supply_apy=best.apy,
                borrow_apy=None,
                tvl_usd=best.tvl_usd,
                pool_id=best.pool,
            )
            
            # Cache result
            if self._cache:
                await self._cache.set(
                    "defi_rates",
                    cache_key,
                    rate.__dict__,
                    ttl=self.CACHE_TTL,
                )
            
            return rate
            
        except Exception as e:
            logger.error(f"Error fetching Morpho rate: {e}")
            return None
    
    async def get_best_yield(
        self,
        asset: str,
        chain: str = "base",
    ) -> ProtocolRate | None:
        """
        Get the best yield for an asset across all protocols.
        
        Args:
            asset: Asset symbol
            chain: Blockchain
            
        Returns:
            ProtocolRate with highest APY, or None if no rates found
        """
        rates = await self.get_all_rates(asset, chain)
        return rates[0] if rates else None
    
    def _matches_asset(self, symbol: str, target_asset: str) -> bool:
        """
        Check if pool symbol matches target asset.
        
        DeFiLlama symbols can be complex (e.g., "USDC-WETH", "aUSDC").
        """
        symbol_upper = symbol.upper()
        target = target_asset.upper()
        
        # Direct match
        if symbol_upper == target:
            return True
        
        # Common variants
        variants = {
            "USDC": ["USDC", "AUSDC", "CUSDC", "USDC.E"],
            "ETH": ["ETH", "WETH", "AETH", "STETH"],
            "DAI": ["DAI", "ADAI", "CDAI"],
            "USDT": ["USDT", "AUSDT", "CUSDT"],
            "WBTC": ["WBTC", "AWBTC", "CWBTC"],
        }
        
        target_variants = variants.get(target, [target])
        
        # Check if symbol contains any variant
        for variant in target_variants:
            if variant in symbol_upper:
                return True
        
        return False
    
    async def close(self):
        """Close underlying clients."""
        if self._defillama:
            await self._defillama.close()
