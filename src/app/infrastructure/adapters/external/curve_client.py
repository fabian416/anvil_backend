"""
Curve Finance API Client - Stub implementation.

This is a stub that provides the necessary classes for the CurveAdapter.
Actual implementation should use Curve Finance APIs.
"""

from dataclasses import dataclass
from decimal import Decimal
from typing import List, Optional
import httpx


@dataclass
class CurvePool:
    """Curve pool data from API."""
    address: str
    name: str
    symbol: str
    coins: List[str]
    coin_addresses: List[str]
    tvl_usd: Decimal
    volume_24h: Decimal
    apy: Optional[Decimal] = None


@dataclass
class PoolAPY:
    """Pool APY data from API."""
    base_apy: Decimal
    reward_apy: Decimal
    total_apy: Decimal


@dataclass
class SwapQuote:
    """Swap quote from API."""
    from_amount: Decimal
    to_amount: Decimal
    exchange_rate: Decimal
    price_impact: Decimal
    route: List[str]


@dataclass
class GaugeData:
    """Gauge data from API."""
    address: str
    pool_address: str
    name: str
    crv_apy: Decimal
    relative_weight: Decimal


class CurveClient:
    """
    Curve Finance API client.
    
    Provides access to Curve pools, APYs, swaps, and gauges.
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: str = "https://api.curve.fi",
        timeout: float = 30.0,
    ):
        self.api_key = api_key
        self.base_url = base_url
        self.client = httpx.AsyncClient(timeout=timeout)
    
    async def get_pools(self, chain: str = "ethereum") -> List[CurvePool]:
        """Get all Curve pools."""
        # Stub - return empty list
        return []
    
    async def get_pool_apy(self, pool_address: str) -> PoolAPY:
        """Get APY for a specific pool."""
        return PoolAPY(
            base_apy=Decimal("0"),
            reward_apy=Decimal("0"),
            total_apy=Decimal("0"),
        )
    
    async def get_swap_quote(
        self,
        from_token: str,
        to_token: str,
        amount: Decimal,
    ) -> SwapQuote:
        """Get swap quote."""
        return SwapQuote(
            from_amount=amount,
            to_amount=amount,
            exchange_rate=Decimal("1"),
            price_impact=Decimal("0"),
            route=[from_token, to_token],
        )
    
    async def get_gauges(self, chain: str = "ethereum") -> List[GaugeData]:
        """Get all gauges."""
        return []
    
    async def get_tvl(self, chain: str = "ethereum") -> Decimal:
        """Get total TVL."""
        return Decimal("0")
    
    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()
