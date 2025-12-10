"""
OpenSea API Client - Stub implementation.

This is a stub that provides the necessary classes for the OpenSeaAdapter.
Actual implementation should use OpenSea API.
"""

from dataclasses import dataclass, field
from decimal import Decimal
from typing import List, Optional, Dict, Any
from enum import Enum
import httpx


class Chain(str, Enum):
    """Supported blockchain networks."""
    ETHEREUM = "ethereum"
    POLYGON = "polygon"
    ARBITRUM = "arbitrum"
    OPTIMISM = "optimism"
    BASE = "base"


@dataclass
class NFTTrait:
    """NFT trait/attribute."""
    trait_type: str
    value: str
    display_type: Optional[str] = None
    trait_count: Optional[int] = None


@dataclass
class NFTAsset:
    """NFT asset from API."""
    identifier: str
    collection: str
    contract: str
    token_standard: str
    name: Optional[str] = None
    description: Optional[str] = None
    image_url: Optional[str] = None
    metadata_url: Optional[str] = None
    created_date: Optional[str] = None
    updated_date: Optional[str] = None
    is_disabled: bool = False
    is_nsfw: bool = False
    traits: List[NFTTrait] = field(default_factory=list)
    owners: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class NFTCollection:
    """NFT collection from API."""
    collection: str
    name: str
    description: Optional[str] = None
    image_url: Optional[str] = None
    banner_image_url: Optional[str] = None
    owner: Optional[str] = None
    safelist_status: str = "not_requested"
    category: Optional[str] = None
    is_disabled: bool = False
    is_nsfw: bool = False
    trait_offers_enabled: bool = False
    collection_offers_enabled: bool = True
    opensea_url: Optional[str] = None
    project_url: Optional[str] = None
    wiki_url: Optional[str] = None
    discord_url: Optional[str] = None
    telegram_url: Optional[str] = None
    twitter_username: Optional[str] = None
    instagram_username: Optional[str] = None
    contracts: List[Dict[str, str]] = field(default_factory=list)


@dataclass
class CollectionStats:
    """Collection statistics from API."""
    total_supply: int
    num_owners: int
    floor_price: Optional[Decimal] = None
    floor_price_symbol: str = "ETH"
    total_volume: Decimal = Decimal("0")
    one_day_volume: Decimal = Decimal("0")
    seven_day_volume: Decimal = Decimal("0")
    thirty_day_volume: Decimal = Decimal("0")
    one_day_change: Decimal = Decimal("0")
    seven_day_change: Decimal = Decimal("0")
    thirty_day_change: Decimal = Decimal("0")
    one_day_sales: int = 0
    seven_day_sales: int = 0
    thirty_day_sales: int = 0
    total_sales: int = 0
    one_day_average_price: Decimal = Decimal("0")
    seven_day_average_price: Decimal = Decimal("0")
    thirty_day_average_price: Decimal = Decimal("0")
    market_cap: Decimal = Decimal("0")


@dataclass
class NFTListing:
    """NFT listing from API."""
    order_hash: str
    chain: str
    protocol_address: str
    maker_address: str
    taker_address: Optional[str] = None
    current_price: Decimal = Decimal("0")
    price_symbol: str = "ETH"
    start_date: Optional[str] = None
    expiration_date: Optional[str] = None
    order_type: str = "basic"
    protocol_data: Dict[str, Any] = field(default_factory=dict)


class OpenSeaClient:
    """
    OpenSea API client.
    
    Provides access to NFT collections, assets, listings, and statistics.
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: str = "https://api.opensea.io/api/v2",
        timeout: float = 30.0,
    ):
        self.api_key = api_key
        self.base_url = base_url
        headers = {}
        if api_key:
            headers["X-API-KEY"] = api_key
        self.client = httpx.AsyncClient(timeout=timeout, headers=headers)
    
    async def get_nfts_by_owner(
        self,
        owner_address: str,
        chain: Chain = Chain.ETHEREUM,
        limit: int = 50,
    ) -> List[NFTAsset]:
        """Get NFTs owned by an address."""
        return []
    
    async def get_collection(self, collection_slug: str) -> NFTCollection:
        """Get collection by slug."""
        return NFTCollection(
            collection=collection_slug,
            name=collection_slug.replace("-", " ").title(),
        )
    
    async def get_collection_stats(self, collection_slug: str) -> CollectionStats:
        """Get collection statistics."""
        return CollectionStats(
            total_supply=10000,
            num_owners=5000,
            floor_price=Decimal("0.1"),
        )
    
    async def get_nft(
        self,
        collection_slug: str,
        token_id: str,
    ) -> NFTAsset:
        """Get specific NFT."""
        return NFTAsset(
            identifier=token_id,
            collection=collection_slug,
            contract="0x0000000000000000000000000000000000000000",
            token_standard="ERC721",
            name=f"{collection_slug} #{token_id}",
        )
    
    async def get_listings(
        self,
        collection_slug: str,
        limit: int = 50,
    ) -> List[NFTListing]:
        """Get active listings for a collection."""
        return []
    
    async def get_floor_price(
        self,
        collection_slug: str,
    ) -> Optional[Decimal]:
        """Get floor price for a collection."""
        return Decimal("0.1")
    
    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()
