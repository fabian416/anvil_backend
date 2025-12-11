"""
OpenSea Pydantic Schemas.

Request and response models for NFT API endpoints.
"""

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field

from app.domain.entities.nft.nft_asset import NFTAsset
from app.domain.entities.nft.nft_collection import NFTCollection
from app.domain.value_objects.nft.collection_stats import CollectionStats
from app.domain.value_objects.nft.nft_listing import NFTListing
from app.domain.value_objects.nft.nft_trait import NFTTrait


# =============================================================================
# Response Models
# =============================================================================


class NFTTraitResponse(BaseModel):
    """NFT trait response model."""

    trait_type: str
    value: str
    rarity_pct: str | None = None

    @classmethod
    def from_domain(cls, trait: NFTTrait) -> "NFTTraitResponse":
        """Create from domain value object."""
        return cls(
            trait_type=trait.trait_type,
            value=trait.value,
            rarity_pct=str(trait.rarity_pct) if trait.rarity_pct else None,
        )


class NFTAssetResponse(BaseModel):
    """NFT asset response model."""

    identifier: str
    collection_slug: str
    contract_address: str
    name: str | None = None
    display_name: str
    description: str | None = None
    image_url: str | None = None
    animation_url: str | None = None
    traits: list[NFTTraitResponse] = Field(default_factory=list)
    rarity_rank: int | None = None
    last_sale_price: str | None = None
    last_sale_currency: str | None = None

    @classmethod
    def from_domain(cls, nft: NFTAsset) -> "NFTAssetResponse":
        """Create from domain entity."""
        return cls(
            identifier=nft.identifier,
            collection_slug=nft.collection_slug,
            contract_address=nft.contract_address,
            name=nft.name,
            display_name=nft.display_name,
            description=nft.description,
            image_url=nft.image_url,
            animation_url=nft.animation_url,
            traits=[NFTTraitResponse.from_domain(t) for t in nft.traits],
            rarity_rank=nft.rarity_rank,
            last_sale_price=str(nft.last_sale_price) if nft.last_sale_price else None,
            last_sale_currency=nft.last_sale_currency,
        )


class CollectionValueResponse(BaseModel):
    """Collection value breakdown response model."""

    slug: str
    count: int
    floor_price_eth: str
    total_value_eth: str


class NFTPortfolioResponse(BaseModel):
    """NFT portfolio response model."""

    address: str
    chain: str
    nfts: list[NFTAssetResponse]
    total_count: int
    collection_count: int
    total_value_eth: str
    total_value_usd: str
    by_collection: list[CollectionValueResponse] = Field(default_factory=list)


class NFTCollectionResponse(BaseModel):
    """NFT collection response model."""

    slug: str
    name: str
    description: str | None = None
    image_url: str | None = None
    banner_image_url: str | None = None
    total_supply: int
    created_date: datetime | None = None
    primary_contract: str | None = None
    chain: str | None = None

    @classmethod
    def from_domain(cls, collection: NFTCollection) -> "NFTCollectionResponse":
        """Create from domain entity."""
        return cls(
            slug=collection.slug,
            name=collection.name,
            description=collection.description,
            image_url=collection.image_url,
            banner_image_url=collection.banner_image_url,
            total_supply=collection.total_supply,
            created_date=collection.created_date,
            primary_contract=collection.primary_contract,
            chain=collection.chain,
        )


class CollectionStatsResponseModel(BaseModel):
    """Collection stats response model."""

    slug: str
    floor_price: str
    floor_price_usd: str
    total_volume: str
    total_sales: int
    num_owners: int
    average_price: str
    market_cap: str
    one_day_volume: str
    one_day_change: str
    seven_day_volume: str
    seven_day_change: str
    is_trending: bool

    @classmethod
    def from_domain(cls, stats: CollectionStats) -> "CollectionStatsResponseModel":
        """Create from domain value object."""
        return cls(
            slug=stats.slug,
            floor_price=str(stats.floor_price),
            floor_price_usd=str(stats.floor_price_usd),
            total_volume=str(stats.total_volume),
            total_sales=stats.total_sales,
            num_owners=stats.num_owners,
            average_price=str(stats.average_price),
            market_cap=str(stats.market_cap),
            one_day_volume=str(stats.one_day_volume),
            one_day_change=str(stats.one_day_change),
            seven_day_volume=str(stats.seven_day_volume),
            seven_day_change=str(stats.seven_day_change),
            is_trending=stats.is_trending,
        )


class CollectionStatsResponse(BaseModel):
    """Collection stats with analysis response model."""

    stats: CollectionStatsResponseModel
    market_sentiment: str = Field(description="BULLISH, BEARISH, or NEUTRAL")
    floor_change_alert: str | None = Field(
        default=None, description="SIGNIFICANT_DROP or SIGNIFICANT_RISE"
    )


class NFTListingResponse(BaseModel):
    """NFT listing response model."""

    order_hash: str
    token_id: str
    collection_slug: str
    price: str
    price_usd: str
    currency: str
    seller: str
    created_date: datetime
    expiration_date: datetime | None = None

    @classmethod
    def from_domain(cls, listing: NFTListing) -> "NFTListingResponse":
        """Create from domain value object."""
        return cls(
            order_hash=listing.order_hash,
            token_id=listing.token_id,
            collection_slug=listing.collection_slug,
            price=str(listing.price),
            price_usd=str(listing.price_usd),
            currency=listing.currency,
            seller=listing.seller,
            created_date=listing.created_date,
            expiration_date=listing.expiration_date,
        )


class ListingsResponse(BaseModel):
    """Listings list response model."""

    listings: list[NFTListingResponse]
    count: int
    collection_slug: str


class FloorPriceResponse(BaseModel):
    """Floor price response model."""

    collection_slug: str
    floor_price_eth: str | None
    floor_price_usd: str | None
