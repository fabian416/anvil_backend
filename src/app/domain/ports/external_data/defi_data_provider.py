"""
DeFi Data Provider Port

Interface for external DeFi data sources.
"""

from typing import Protocol, List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal


@dataclass
class ProtocolData:
    """Protocol information from external sources"""

    name: str
    slug: str
    description: Optional[str]
    category: str
    chains: List[str]
    tvl: Decimal
    change_24h: Optional[float]
    website: Optional[str]
    twitter: Optional[str]
    github: Optional[str]
    logo: Optional[str]
    audit_links: Optional[List[str]]
    token_symbol: Optional[str]
    raw_data: Dict[str, Any]  # Original API response
    last_updated: datetime


@dataclass
class TokenData:
    """Token information from external sources"""

    symbol: str
    name: str
    address: Optional[str]
    chain: Optional[str]
    decimals: Optional[int]
    price_usd: Optional[Decimal]
    market_cap: Optional[Decimal]
    volume_24h: Optional[Decimal]
    change_24h: Optional[float]
    logo: Optional[str]
    coingecko_id: Optional[str]
    raw_data: Dict[str, Any]
    last_updated: datetime


@dataclass
class ChainData:
    """Blockchain information from external sources"""

    name: str
    chain_id: Optional[int]
    native_token: str
    tvl: Decimal
    protocols_count: int
    raw_data: Dict[str, Any]
    last_updated: datetime


@dataclass
class AuditData:
    """Audit information from external sources"""

    protocol_name: str
    auditor: str
    date: Optional[datetime]
    report_url: Optional[str]
    findings: Optional[int]
    critical_findings: Optional[int]
    raw_data: Dict[str, Any]
    last_updated: datetime


@dataclass
class TVLData:
    """TVL time series data"""

    protocol: str
    chain: Optional[str]
    tvl: Decimal
    timestamp: datetime


class DefiDataProvider(Protocol):
    """
    Port for external DeFi data providers.

    Implementations:
    - DeFiLlama
    - The Graph
    - 1inch
    - CoinGecko
    """

    async def get_all_protocols(
        self,
        limit: Optional[int] = None,
    ) -> List[ProtocolData]:
        """
        Get all DeFi protocols.

        Args:
            limit: Maximum number of protocols to return

        Returns:
            List of protocol data
        """
        ...

    async def get_protocol(
        self,
        slug: str,
    ) -> Optional[ProtocolData]:
        """
        Get specific protocol by slug.

        Args:
            slug: Protocol slug (e.g., 'aave', 'uniswap')

        Returns:
            Protocol data if found
        """
        ...

    async def get_protocol_tvl(
        self,
        slug: str,
    ) -> List[TVLData]:
        """
        Get TVL history for a protocol.

        Args:
            slug: Protocol slug

        Returns:
            List of TVL data points
        """
        ...

    async def get_chains(self) -> List[ChainData]:
        """
        Get all supported chains.

        Returns:
            List of chain data
        """
        ...

    async def get_chain_protocols(
        self,
        chain: str,
    ) -> List[ProtocolData]:
        """
        Get all protocols on a specific chain.

        Args:
            chain: Chain name (e.g., 'Ethereum', 'Polygon')

        Returns:
            List of protocols
        """
        ...

    async def get_token_price(
        self,
        address: str,
        chain: str,
    ) -> Optional[TokenData]:
        """
        Get token price and info.

        Args:
            address: Token contract address
            chain: Chain name

        Returns:
            Token data if found
        """
        ...

    async def search_protocols(
        self,
        query: str,
        limit: int = 10,
    ) -> List[ProtocolData]:
        """
        Search protocols by name.

        Args:
            query: Search query
            limit: Maximum results

        Returns:
            List of matching protocols
        """
        ...

    async def get_audits(
        self,
        protocol_slug: str,
    ) -> List[AuditData]:
        """
        Get audit information for a protocol.

        Args:
            protocol_slug: Protocol slug

        Returns:
            List of audits
        """
        ...
