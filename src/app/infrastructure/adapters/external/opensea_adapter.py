"""
OpenSea Gateway Adapter.

Implements the NFTMarketplaceGateway port using the OpenSeaClient
with caching for collection and portfolio data.
"""

import logging
import re
from decimal import Decimal

from app.domain.entities.nft.nft_asset import NFTAsset
from app.domain.entities.nft.nft_collection import NFTCollection
from app.domain.exceptions.nft import InvalidAddressError, OpenSeaAPIError
from app.domain.ports.nft_marketplace_gateway import NFTMarketplaceGateway
from app.domain.value_objects.nft.collection_stats import CollectionStats
from app.domain.value_objects.nft.nft_listing import NFTListing
from app.domain.value_objects.nft.nft_trait import NFTTrait
from app.infrastructure.adapters.external.opensea_client import (
    Chain,
    CollectionStats as ClientStats,
    NFTAsset as ClientNFT,
    NFTCollection as ClientCollection,
    NFTListing as ClientListing,
    OpenSeaClient,
)
from app.infrastructure.cache.external_api_cache import ExternalAPICache

logger = logging.getLogger(__name__)

# Address pattern
ADDRESS_PATTERN = re.compile(r"^0x[a-fA-F0-9]{40}$")


class OpenSeaAdapter(NFTMarketplaceGateway):
    """
    OpenSea implementation of NFTMarketplaceGateway.

    Uses caching:
    - Collections: 15 minutes
    - Stats: 5 minutes
    - Portfolio: 10 minutes
    - Listings: 1 minute
    """

    DEFAULT_COLLECTION_CACHE_TTL = 900  # 15 minutes
    DEFAULT_STATS_CACHE_TTL = 300  # 5 minutes
    DEFAULT_PORTFOLIO_CACHE_TTL = 600  # 10 minutes
    DEFAULT_NFT_CACHE_TTL = 900  # 15 minutes
    DEFAULT_LISTINGS_CACHE_TTL = 60  # 1 minute

    # ETH price for USD conversion (placeholder)
    ETH_PRICE_USD = Decimal("2500")

    def __init__(
        self,
        client: OpenSeaClient,
        cache: ExternalAPICache,
        collection_cache_ttl: int = DEFAULT_COLLECTION_CACHE_TTL,
        stats_cache_ttl: int = DEFAULT_STATS_CACHE_TTL,
        portfolio_cache_ttl: int = DEFAULT_PORTFOLIO_CACHE_TTL,
        nft_cache_ttl: int = DEFAULT_NFT_CACHE_TTL,
        listings_cache_ttl: int = DEFAULT_LISTINGS_CACHE_TTL,
    ):
        """Initialize OpenSeaAdapter."""
        self._client = client
        self._cache = cache
        self._collection_cache_ttl = collection_cache_ttl
        self._stats_cache_ttl = stats_cache_ttl
        self._portfolio_cache_ttl = portfolio_cache_ttl
        self._nft_cache_ttl = nft_cache_ttl
        self._listings_cache_ttl = listings_cache_ttl

    async def get_nfts_by_owner(
        self,
        address: str,
        chain: str = "ethereum",
        limit: int = 50,
    ) -> list[NFTAsset]:
        """Get NFTs owned by an address with caching."""
        if not ADDRESS_PATTERN.match(address):
            raise InvalidAddressError(address)

        cache_key_params = {
            "chain": chain.lower(),
            "address": address.lower(),
            "limit": limit,
        }

        cached = await self._cache.get("opensea", "portfolio", **cache_key_params)
        if cached:
            return [NFTAsset.from_dict(n) for n in cached]

        try:
            chain_enum = (
                Chain(chain.lower()) if chain.lower() != "ethereum" else Chain.ETHEREUM
            )
            raw_nfts = await self._client.get_nfts_by_account(
                address=address,
                chain=chain_enum,
                limit=limit,
            )
            nfts = [self._transform_nft(n) for n in raw_nfts]

            await self._cache.set(
                "opensea",
                "portfolio",
                [n.to_dict() for n in nfts],
                ttl=self._portfolio_cache_ttl,
                **cache_key_params,
            )

            return nfts

        except Exception as e:
            logger.error(f"Error getting NFTs for {address}: {e}")
            raise OpenSeaAPIError(str(e)) from e

    async def get_collection(
        self,
        collection_slug: str,
    ) -> NFTCollection | None:
        """Get collection information with caching."""
        cache_key_params = {"slug": collection_slug.lower()}

        cached = await self._cache.get("opensea", "collection", **cache_key_params)
        if cached:
            return NFTCollection.from_dict(cached)

        try:
            raw = await self._client.get_collection(collection_slug)
            if not raw:
                return None

            collection = self._transform_collection(raw)

            await self._cache.set(
                "opensea",
                "collection",
                collection.to_dict(),
                ttl=self._collection_cache_ttl,
                **cache_key_params,
            )

            return collection

        except Exception as e:
            logger.error(f"Error getting collection {collection_slug}: {e}")
            raise OpenSeaAPIError(str(e)) from e

    async def get_collection_stats(
        self,
        collection_slug: str,
    ) -> CollectionStats | None:
        """Get collection statistics with caching."""
        cache_key_params = {"slug": collection_slug.lower()}

        cached = await self._cache.get("opensea", "stats", **cache_key_params)
        if cached:
            return CollectionStats.from_dict(cached)

        try:
            raw = await self._client.get_collection_stats(collection_slug)
            if not raw:
                return None

            stats = self._transform_stats(raw)

            await self._cache.set(
                "opensea",
                "stats",
                stats.to_dict(),
                ttl=self._stats_cache_ttl,
                **cache_key_params,
            )

            return stats

        except Exception as e:
            logger.error(f"Error getting stats for {collection_slug}: {e}")
            raise OpenSeaAPIError(str(e)) from e

    async def get_nft(
        self,
        contract_address: str,
        token_id: str,
        chain: str = "ethereum",
    ) -> NFTAsset | None:
        """Get single NFT details with caching."""
        cache_key_params = {
            "chain": chain.lower(),
            "contract": contract_address.lower(),
            "token_id": token_id,
        }

        cached = await self._cache.get("opensea", "nft", **cache_key_params)
        if cached:
            return NFTAsset.from_dict(cached)

        try:
            chain_enum = (
                Chain(chain.lower()) if chain.lower() != "ethereum" else Chain.ETHEREUM
            )
            raw = await self._client.get_nft(
                contract_address=contract_address,
                token_id=token_id,
                chain=chain_enum,
            )
            if not raw:
                return None

            nft = self._transform_nft(raw)

            await self._cache.set(
                "opensea",
                "nft",
                nft.to_dict(),
                ttl=self._nft_cache_ttl,
                **cache_key_params,
            )

            return nft

        except Exception as e:
            logger.error(f"Error getting NFT {contract_address}/{token_id}: {e}")
            raise OpenSeaAPIError(str(e)) from e

    async def get_listings(
        self,
        collection_slug: str,
        limit: int = 50,
    ) -> list[NFTListing]:
        """Get active listings with short caching."""
        cache_key_params = {"slug": collection_slug.lower(), "limit": limit}

        cached = await self._cache.get("opensea", "listings", **cache_key_params)
        if cached:
            return [NFTListing.from_dict(l) for l in cached]

        try:
            raw_listings = await self._client.get_listings(collection_slug, limit)
            listings = [
                self._transform_listing(l, collection_slug) for l in raw_listings
            ]

            await self._cache.set(
                "opensea",
                "listings",
                [l.to_dict() for l in listings],
                ttl=self._listings_cache_ttl,
                **cache_key_params,
            )

            return listings

        except Exception as e:
            logger.error(f"Error getting listings for {collection_slug}: {e}")
            raise OpenSeaAPIError(str(e)) from e

    async def get_floor_price(
        self,
        collection_slug: str,
    ) -> Decimal | None:
        """Get floor price from collection stats."""
        stats = await self.get_collection_stats(collection_slug)
        return stats.floor_price if stats else None

    # =========================================================================
    # Transformation Methods
    # =========================================================================

    def _transform_nft(self, raw: ClientNFT) -> NFTAsset:
        """Transform client NFT to domain entity."""
        traits = [
            NFTTrait(
                trait_type=t.get("trait_type", ""),
                value=str(t.get("value", "")),
                rarity_pct=None,  # Not provided by client
            )
            for t in raw.traits
        ]

        last_sale = None
        if raw.last_sale_price:
            last_sale = Decimal(str(raw.last_sale_price))

        return NFTAsset(
            identifier=raw.identifier,
            collection_slug=raw.collection,
            contract_address=raw.contract,
            name=raw.name,
            description=raw.description,
            image_url=raw.image_url,
            animation_url=raw.animation_url,
            traits=traits,
            rarity_rank=raw.rarity_rank,
            last_sale_price=last_sale,
            last_sale_currency=raw.last_sale_currency,
        )

    def _transform_collection(self, raw: ClientCollection) -> NFTCollection:
        """Transform client collection to domain entity."""
        return NFTCollection(
            slug=raw.slug,
            name=raw.name,
            description=raw.description,
            image_url=raw.image_url,
            banner_image_url=raw.banner_image_url,
            total_supply=raw.total_supply,
            created_date=raw.created_date,
            contracts=raw.contracts,
        )

    def _transform_stats(self, raw: ClientStats) -> CollectionStats:
        """Transform client stats to domain value object."""
        return CollectionStats(
            slug=raw.slug,
            floor_price=Decimal(str(raw.floor_price)),
            floor_price_usd=Decimal(str(raw.floor_price_usd)),
            total_volume=Decimal(str(raw.total_volume)),
            total_sales=raw.total_sales,
            num_owners=raw.num_owners,
            average_price=Decimal(str(raw.average_price)),
            market_cap=Decimal(str(raw.market_cap)),
            one_day_volume=Decimal(str(raw.one_day_volume)),
            one_day_change=Decimal(str(raw.one_day_change)),
            seven_day_volume=Decimal(str(raw.seven_day_volume)),
            seven_day_change=Decimal(str(raw.seven_day_change)),
        )

    def _transform_listing(
        self, raw: ClientListing, collection_slug: str
    ) -> NFTListing:
        """Transform client listing to domain value object."""
        price = Decimal(str(raw.price))
        return NFTListing(
            order_hash=raw.order_hash,
            token_id=raw.asset_identifier,
            collection_slug=collection_slug,
            price=price,
            price_usd=price * self.ETH_PRICE_USD,
            currency=raw.currency,
            seller=raw.maker,
            created_date=raw.created_date,
            expiration_date=raw.expiration_date,
        )
