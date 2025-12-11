"""
Cached DeFiLlama API Client.

Wraps the base DefiLlamaClient with Redis caching for:
- Protocol list (5min TTL)
- Protocol TVL (5min TTL)
- Yield data (5min TTL)
- Chain TVL (5min TTL)
- Stablecoin data (2min TTL)
- Fees/revenue (1h TTL)
"""

from dataclasses import asdict
from typing import Optional

from app.infrastructure.adapters.external.defillama_client import (
    ChainTVL,
    DefiLlamaClient,
    Protocol,
    ProtocolTVL,
    YieldData,
)
from app.infrastructure.cache.external_api_cache import ExternalAPICache


class CachedDefiLlamaClient(DefiLlamaClient):
    """
    DeFiLlama client with Redis caching.
    
    DeFiLlama is a free API with no strict rate limits,
    but caching improves response times significantly.
    
    Example:
        >>> cache = ExternalAPICache(redis_client)
        >>> client = CachedDefiLlamaClient(cache=cache)
        >>> 
        >>> # First call hits API
        >>> protocols = await client.get_all_protocols()
        >>> 
        >>> # Subsequent calls hit cache
        >>> protocols = await client.get_all_protocols()  # From cache!
    """
    
    API_NAME = "defillama"
    
    def __init__(self, cache: Optional[ExternalAPICache] = None):
        """
        Initialize cached DeFiLlama client.
        
        Args:
            cache: External API cache instance
        """
        super().__init__()
        self._cache = cache
    
    async def get_all_protocols(self) -> list[Protocol]:
        """Get all DeFi protocols with caching (5min TTL)."""
        if self._cache:
            cached = await self._cache.get(
                self.API_NAME,
                "protocols",
            )
            if cached:
                return [Protocol(**p) for p in cached]
        
        # Fetch from API
        result = await super().get_all_protocols()
        
        # Cache result
        if self._cache:
            await self._cache.set(
                self.API_NAME,
                "protocols",
                [asdict(p) for p in result],
            )
        
        return result
    
    async def get_protocol_tvl(self, protocol: str) -> ProtocolTVL:
        """Get protocol TVL with caching (5min TTL)."""
        if self._cache:
            cached = await self._cache.get(
                self.API_NAME,
                "protocol_tvl",
                protocol=protocol,
            )
            if cached:
                return ProtocolTVL(**cached)
        
        # Fetch from API
        result = await super().get_protocol_tvl(protocol)
        
        # Cache result
        if self._cache:
            await self._cache.set(
                self.API_NAME,
                "protocol_tvl",
                asdict(result),
                protocol=protocol,
            )
        
        return result
    
    async def get_protocol_yields(
        self,
        protocol: str | None = None,
        chain: str | None = None,
    ) -> list[YieldData]:
        """Get yield farming opportunities with caching (5min TTL)."""
        if self._cache:
            cached = await self._cache.get(
                self.API_NAME,
                "yields",
                protocol=protocol or "all",
                chain=chain or "all",
            )
            if cached:
                return [YieldData(**y) for y in cached]
        
        # Fetch from API
        result = await super().get_protocol_yields(protocol, chain)
        
        # Cache result
        if self._cache:
            await self._cache.set(
                self.API_NAME,
                "yields",
                [asdict(y) for y in result],
                protocol=protocol or "all",
                chain=chain or "all",
            )
        
        return result
    
    async def get_chain_tvl(self, chain: str | None = None) -> list[ChainTVL]:
        """Get chain TVL with caching (5min TTL)."""
        if self._cache:
            cached = await self._cache.get(
                self.API_NAME,
                "chain_tvl",
                chain=chain or "all",
            )
            if cached:
                return [ChainTVL(**c) for c in cached]
        
        # Fetch from API
        result = await super().get_chain_tvl(chain)
        
        # Cache result
        if self._cache:
            await self._cache.set(
                self.API_NAME,
                "chain_tvl",
                [asdict(c) for c in result],
                chain=chain or "all",
            )
        
        return result
    
    async def get_stablecoin_dominance(self) -> dict[str, float]:
        """Get stablecoin market share with caching (2min TTL)."""
        if self._cache:
            cached = await self._cache.get(
                self.API_NAME,
                "stablecoins",
            )
            if cached:
                return cached
        
        # Fetch from API
        result = await super().get_stablecoin_dominance()
        
        # Cache result
        if self._cache:
            await self._cache.set(
                self.API_NAME,
                "stablecoins",
                result,
            )
        
        return result
    
    async def get_fees_revenue(self, protocol: str) -> dict[str, float]:
        """Get protocol fees/revenue with caching (1h TTL)."""
        if self._cache:
            cached = await self._cache.get(
                self.API_NAME,
                "fees",
                protocol=protocol,
            )
            if cached:
                return cached
        
        # Fetch from API
        result = await super().get_fees_revenue(protocol)
        
        # Cache result
        if self._cache:
            await self._cache.set(
                self.API_NAME,
                "fees",
                result,
                protocol=protocol,
            )
        
        return result
