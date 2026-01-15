"""
DeFiLlama API Client

Adapter for DeFiLlama API - the largest DeFi TVL aggregator.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime, UTC
from decimal import Decimal
import httpx

from app.domain.ports.external_data import (
    DefiDataProvider,
    ProtocolData,
    TokenData,
    ChainData,
    TVLData,
    AuditData,
)


class DeFiLlamaClient(DefiDataProvider):
    """
    DeFiLlama API client implementation.
    
    API Docs: https://defillama.com/docs/api
    """
    
    BASE_URL = "https://api.llama.fi"
    
    def __init__(
        self,
        timeout: int = 30,
        max_retries: int = 3,
    ):
        """
        Initialize DeFiLlama client.
        
        Args:
            timeout: Request timeout in seconds
            max_retries: Maximum number of retries
        """
        self.timeout = timeout
        self.max_retries = max_retries
        self._client: Optional[httpx.AsyncClient] = None
    
    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client"""
        if self._client is None:
            self._client = httpx.AsyncClient(
                timeout=self.timeout,
                follow_redirects=True,
            )
        return self._client
    
    async def close(self):
        """Close HTTP client"""
        if self._client:
            await self._client.aclose()
            self._client = None
    
    async def _make_request(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Make HTTP request with retries.
        
        Args:
            endpoint: API endpoint
            params: Query parameters
            
        Returns:
            JSON response
            
        Raises:
            httpx.HTTPError: On request failure
        """
        client = await self._get_client()
        url = f"{self.BASE_URL}{endpoint}"
        
        for attempt in range(self.max_retries):
            try:
                response = await client.get(url, params=params)
                response.raise_for_status()
                return response.json()
            except httpx.HTTPError as e:
                if attempt == self.max_retries - 1:
                    raise
                # Exponential backoff
                await httpx.AsyncClient().aclose()  # Small delay
        
        return {}
    
    async def get_all_protocols(
        self,
        limit: Optional[int] = None,
    ) -> List[ProtocolData]:
        """Get all DeFi protocols from DeFiLlama"""
        
        data = await self._make_request("/protocols")
        protocols = []
        
        for item in data[:limit] if limit else data:
            protocols.append(self._parse_protocol(item))
        
        return protocols
    
    async def get_protocol(
        self,
        slug: str,
    ) -> Optional[ProtocolData]:
        """Get specific protocol by slug"""
        
        try:
            data = await self._make_request(f"/protocol/{slug}")
            return self._parse_protocol_detail(data)
        except httpx.HTTPError:
            return None
    
    async def get_protocol_tvl(
        self,
        slug: str,
    ) -> List[TVLData]:
        """Get TVL history for a protocol"""
        
        try:
            data = await self._make_request(f"/protocol/{slug}")
            tvl_data = []
            
            if "tvl" in data and isinstance(data["tvl"], list):
                for point in data["tvl"]:
                    tvl_data.append(TVLData(
                        protocol=slug,
                        chain=None,
                        tvl=Decimal(str(point.get("totalLiquidityUSD", 0))),
                        timestamp=datetime.fromtimestamp(point.get("date", 0)),
                    ))
            
            return tvl_data
        except httpx.HTTPError:
            return []
    
    async def get_chains(self) -> List[ChainData]:
        """Get all supported chains"""
        
        data = await self._make_request("/chains")
        chains = []
        
        for item in data:
            chains.append(ChainData(
                name=item.get("name", "Unknown"),
                chain_id=item.get("chainId"),
                native_token=item.get("tokenSymbol", ""),
                tvl=Decimal(str(item.get("tvl", 0))),
                protocols_count=item.get("protocols", 0),
                raw_data=item,
                last_updated=datetime.now(UTC),
            ))
        
        return chains
    
    async def get_chain_protocols(
        self,
        chain: str,
    ) -> List[ProtocolData]:
        """Get all protocols on a specific chain"""
        
        all_protocols = await self.get_all_protocols()
        
        # Filter by chain
        return [
            p for p in all_protocols
            if chain.lower() in [c.lower() for c in p.chains]
        ]
    
    async def get_token_price(
        self,
        address: str,
        chain: str,
    ) -> Optional[TokenData]:
        """Get token price (DeFiLlama has limited token data)"""
        
        # DeFiLlama's coins API
        try:
            # Format: chain:address
            coin_id = f"{chain}:{address}"
            data = await self._make_request(f"/coins/prices/current/{coin_id}")
            
            if "coins" in data and coin_id in data["coins"]:
                coin = data["coins"][coin_id]
                return TokenData(
                    symbol=coin.get("symbol", ""),
                    name=coin.get("name", ""),
                    address=address,
                    chain=chain,
                    decimals=coin.get("decimals"),
                    price_usd=Decimal(str(coin.get("price", 0))),
                    market_cap=None,
                    volume_24h=None,
                    change_24h=None,
                    logo=None,
                    coingecko_id=None,
                    raw_data=coin,
                    last_updated=datetime.now(UTC),
                )
        except httpx.HTTPError:
            pass
        
        return None
    
    async def search_protocols(
        self,
        query: str,
        limit: int = 10,
    ) -> List[ProtocolData]:
        """Search protocols by name"""
        
        all_protocols = await self.get_all_protocols()
        
        # Simple text search
        query_lower = query.lower()
        matches = [
            p for p in all_protocols
            if query_lower in p.name.lower() or query_lower in p.slug.lower()
        ]
        
        return matches[:limit]
    
    async def get_audits(
        self,
        protocol_slug: str,
    ) -> List[AuditData]:
        """Get audit information (limited in DeFiLlama)"""
        
        # DeFiLlama doesn't have a dedicated audits endpoint
        # But some protocols include audit links in their data
        protocol = await self.get_protocol(protocol_slug)
        
        if not protocol or not protocol.audit_links:
            return []
        
        audits = []
        for link in protocol.audit_links:
            audits.append(AuditData(
                protocol_name=protocol.name,
                auditor="Unknown",  # Would need to parse from link
                date=None,
                report_url=link,
                findings=None,
                critical_findings=None,
                raw_data={"url": link},
                last_updated=datetime.now(UTC),
            ))
        
        return audits
    
    def _parse_protocol(self, data: Dict[str, Any]) -> ProtocolData:
        """Parse protocol data from list endpoint"""
        
        return ProtocolData(
            name=data.get("name", "Unknown"),
            slug=data.get("slug", ""),
            description=data.get("description"),
            category=data.get("category", "Other"),
            chains=data.get("chains", []),
            tvl=Decimal(str(data.get("tvl", 0))),
            change_24h=data.get("change_1d"),
            website=data.get("url"),
            twitter=data.get("twitter"),
            github=data.get("github"),
            logo=data.get("logo"),
            audit_links=data.get("audits", "").split(", ") if data.get("audits") else None,
            token_symbol=data.get("symbol"),
            raw_data=data,
            last_updated=datetime.now(UTC),
        )
    
    def _parse_protocol_detail(self, data: Dict[str, Any]) -> ProtocolData:
        """Parse protocol data from detail endpoint"""
        
        return ProtocolData(
            name=data.get("name", "Unknown"),
            slug=data.get("slug", ""),
            description=data.get("description"),
            category=data.get("category", "Other"),
            chains=list(data.get("chainTvls", {}).keys()) if "chainTvls" in data else [],
            tvl=Decimal(str(data.get("tvl", 0))),
            change_24h=data.get("change_1d"),
            website=data.get("url"),
            twitter=data.get("twitter"),
            github=data.get("github", [])[0] if data.get("github") else None,
            logo=data.get("logo"),
            audit_links=data.get("audits", []) if isinstance(data.get("audits"), list) else None,
            token_symbol=data.get("symbol"),
            raw_data=data,
            last_updated=datetime.now(UTC),
        )
