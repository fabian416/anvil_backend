"""
DeFiLlama API Client.

Provides access to DeFi protocol data:
- Protocol TVL
- Yield data (APY/APR)
- Historical data
- Chain TVL
- Stablecoin data

API Docs: https://defillama.com/docs/api
Rate Limit: No strict limits (public API, be respectful)
"""

from dataclasses import dataclass
from typing import Any

import httpx


@dataclass
class Protocol:
    """Protocol information."""
    id: str
    name: str
    symbol: str
    chain: str
    tvl: float
    change_1d: float | None = None
    change_7d: float | None = None
    category: str | None = None
    chains: list[str] | None = None


@dataclass
class ProtocolTVL:
    """Protocol TVL data."""
    protocol: str
    tvl: float
    chain_tvls: dict[str, float]  # TVL per chain
    tokens_in_usd: dict[str, float] | None = None


@dataclass
class YieldData:
    """Yield farming opportunity data."""
    pool: str
    chain: str
    project: str
    symbol: str
    tvl_usd: float
    apy: float
    apy_base: float | None = None  # Base APY (no rewards)
    apy_reward: float | None = None  # Reward APY
    il_risk: str | None = None  # Impermanent loss risk


@dataclass
class ChainTVL:
    """Chain TVL data."""
    chain: str
    tvl: float
    token_symbol: str | None = None


class DefiLlamaClient:
    """
    DeFiLlama API client for DeFi protocol data.
    
    Features:
    - Protocol TVL tracking
    - Yield farming data
    - Historical analytics
    - Multi-chain support
    """
    
    BASE_URL = "https://api.llama.fi"
    YIELDS_URL = "https://yields.llama.fi"
    
    def __init__(self):
        """Initialize DeFiLlama client (no API key required)."""
        self._client = httpx.AsyncClient(
            base_url=self.BASE_URL,
            timeout=30.0,
        )
        self._yields_client = httpx.AsyncClient(
            base_url=self.YIELDS_URL,
            timeout=30.0,
        )
    
    async def close(self):
        """Close HTTP clients."""
        await self._client.aclose()
        await self._yields_client.aclose()
    
    async def get_all_protocols(self) -> list[Protocol]:
        """
        Get all DeFi protocols with TVL data.
        
        Returns:
            List of protocols with current TVL
            
        Example:
            >>> protocols = await client.get_all_protocols()
            >>> top_5 = sorted(protocols, key=lambda p: p.tvl, reverse=True)[:5]
            >>> for p in top_5:
            ...     print(f"{p.name}: ${p.tvl / 1e9:.2f}B TVL")
        """
        response = await self._client.get("/protocols")
        response.raise_for_status()
        data = response.json()
        
        protocols = []
        for item in data:
            # Handle TVL - can be None, int, float, or missing
            tvl_value = item.get("tvl")
            if tvl_value is None:
                tvl_value = 0.0
            elif isinstance(tvl_value, (int, float)):
                tvl_value = float(tvl_value)
            else:
                # Try to convert string or other types
                try:
                    tvl_value = float(tvl_value)
                except (ValueError, TypeError):
                    tvl_value = 0.0
            
            protocols.append(
                Protocol(
                    id=item.get("slug", ""),
                    name=item.get("name", ""),
                    symbol=item.get("symbol", ""),
                    chain=item.get("chain", "Multi-Chain"),
                    tvl=tvl_value,
                    change_1d=item.get("change_1d"),
                    change_7d=item.get("change_7d"),
                    category=item.get("category"),
                    chains=item.get("chains", []),
                )
            )
        
        return protocols
    
    async def get_protocol_tvl(self, protocol: str) -> ProtocolTVL:
        """
        Get detailed TVL data for a specific protocol.
        
        Args:
            protocol: Protocol slug (e.g., "aave", "uniswap")
            
        Returns:
            ProtocolTVL with current and historical data
            
        Example:
            >>> tvl = await client.get_protocol_tvl("aave")
            >>> print(f"Aave TVL: ${tvl.tvl / 1e9:.2f}B")
            >>> print(f"Ethereum: ${tvl.chain_tvls.get('Ethereum', 0) / 1e9:.2f}B")
        """
        response = await self._client.get(f"/protocol/{protocol}")
        response.raise_for_status()
        data = response.json()
        
        # Calculate chain TVLs - handle various response formats
        chain_tvls = {}
        chain_tvls_data = data.get("chainTvls", {})
        if not isinstance(chain_tvls_data, dict):
            # If chainTvls is not a dict, skip it
            chain_tvls_data = {}
        
        for chain, value in chain_tvls_data.items():
            try:
                if isinstance(value, dict):
                    # Some chains return dict with tvl key
                    tvl_value = value.get("tvl", 0)
                    chain_tvls[chain] = float(tvl_value) if tvl_value is not None else 0.0
                elif isinstance(value, (int, float)):
                    chain_tvls[chain] = float(value)
                elif isinstance(value, list):
                    # Some chains return list of TVL values - use the latest
                    if len(value) > 0:
                        latest = value[-1]
                        if isinstance(latest, (int, float)):
                            chain_tvls[chain] = float(latest)
                        elif isinstance(latest, dict):
                            tvl_val = latest.get("tvl", 0)
                            chain_tvls[chain] = float(tvl_val) if tvl_val is not None else 0.0
                        else:
                            chain_tvls[chain] = 0.0
                    else:
                        chain_tvls[chain] = 0.0
                else:
                    # Unknown format - skip this chain
                    continue
            except (ValueError, TypeError) as e:
                # Skip chains with invalid data
                continue
        
        # Extract total TVL - handle different response formats
        total_tvl = 0.0
        tvl_data = data.get("tvl", None)
        if tvl_data:
            if isinstance(tvl_data, (int, float)):
                total_tvl = float(tvl_data)
            elif isinstance(tvl_data, list) and len(tvl_data) > 0:
                # TVL is a list of historical data points
                latest_tvl = tvl_data[-1]
                if isinstance(latest_tvl, dict):
                    total_tvl = float(latest_tvl.get("totalLiquidityUSD", latest_tvl.get("tvl", 0)) or 0)
                elif isinstance(latest_tvl, (int, float)):
                    total_tvl = float(latest_tvl)
            elif isinstance(tvl_data, dict):
                total_tvl = float(tvl_data.get("totalLiquidityUSD", tvl_data.get("tvl", 0)) or 0)
        
        return ProtocolTVL(
            protocol=data.get("name", protocol),
            tvl=total_tvl,
            chain_tvls=chain_tvls,
            tokens_in_usd=data.get("tokensInUsd"),
        )
    
    async def get_protocol_yields(
        self,
        protocol: str | None = None,
        chain: str | None = None,
    ) -> list[YieldData]:
        """
        Get yield farming opportunities.
        
        Args:
            protocol: Filter by protocol (optional)
            chain: Filter by chain (optional)
            
        Returns:
            List of yield pools with APY data
            
        Example:
            >>> yields = await client.get_protocol_yields(protocol="aave")
            >>> best_yield = max(yields, key=lambda y: y.apy)
            >>> print(f"Best Aave yield: {best_yield.apy:.2f}% APY on {best_yield.chain}")
        """
        response = await self._yields_client.get("/pools")
        response.raise_for_status()
        data = response.json()
        
        yields = []
        for pool in data.get("data", []):
            # Apply filters
            if protocol and pool.get("project", "").lower() != protocol.lower():
                continue
            if chain and pool.get("chain", "").lower() != chain.lower():
                continue
            
            yields.append(
                YieldData(
                    pool=pool.get("pool", ""),
                    chain=pool.get("chain", ""),
                    project=pool.get("project", ""),
                    symbol=pool.get("symbol", ""),
                    tvl_usd=float(pool.get("tvlUsd", 0)),
                    apy=float(pool.get("apy", 0)),
                    apy_base=pool.get("apyBase"),
                    apy_reward=pool.get("apyReward"),
                    il_risk=pool.get("ilRisk"),
                )
            )
        
        return yields
    
    async def get_chain_tvl(self, chain: str | None = None) -> list[ChainTVL]:
        """
        Get TVL by blockchain.
        
        Args:
            chain: Specific chain name (optional, None = all chains)
            
        Returns:
            List of chains with TVL
            
        Example:
            >>> chains = await client.get_chain_tvl()
            >>> eth_tvl = next(c for c in chains if c.chain == "Ethereum")
            >>> print(f"Ethereum TVL: ${eth_tvl.tvl / 1e9:.2f}B")
        """
        response = await self._client.get("/v2/chains")
        response.raise_for_status()
        data = response.json()
        
        chain_tvls = []
        for chain_data in data:
            chain_name = chain_data.get("name", "")
            
            # Filter by chain if specified
            if chain and chain.lower() != chain_name.lower():
                continue
            
            chain_tvls.append(
                ChainTVL(
                    chain=chain_name,
                    tvl=float(chain_data.get("tvl", 0)),
                    token_symbol=chain_data.get("tokenSymbol"),
                )
            )
        
        return chain_tvls
    
    async def get_stablecoin_dominance(self) -> dict[str, float]:
        """
        Get stablecoin market share.
        
        Returns:
            Dict mapping stablecoin name to circulating supply (USD)
            
        Example:
            >>> dominance = await client.get_stablecoin_dominance()
            >>> total = sum(dominance.values())
            >>> for coin, supply in sorted(dominance.items(), key=lambda x: x[1], reverse=True)[:5]:
            ...     pct = (supply / total) * 100
            ...     print(f"{coin}: ${supply / 1e9:.2f}B ({pct:.1f}%)")
        """
        response = await self._client.get("/stablecoins?includePrices=true")
        response.raise_for_status()
        data = response.json()
        
        dominance = {}
        for stablecoin in data.get("peggedAssets", []):
            name = stablecoin.get("name", "")
            circulating = float(stablecoin.get("circulating", {}).get("peggedUSD", 0))
            if circulating > 0:
                dominance[name] = circulating
        
        return dominance
    
    async def get_fees_revenue(self, protocol: str) -> dict[str, float]:
        """
        Get protocol fees and revenue data.
        
        Args:
            protocol: Protocol slug
            
        Returns:
            Dict with fees and revenue metrics
            
        Example:
            >>> data = await client.get_fees_revenue("uniswap")
            >>> print(f"24h fees: ${data.get('total24h', 0) / 1e6:.2f}M")
        """
        response = await self._client.get(f"/summary/fees/{protocol}")
        response.raise_for_status()
        data = response.json()
        
        return {
            "total24h": float(data.get("total24h", 0)),
            "total7d": float(data.get("total7d", 0)),
            "total30d": float(data.get("total30d", 0)),
            "totalAllTime": float(data.get("totalAllTime", 0)),
        }
