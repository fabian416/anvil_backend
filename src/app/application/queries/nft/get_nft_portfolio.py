"""
GetNFTPortfolio Query.

Application query for retrieving NFT portfolio with valuation.
"""

from dataclasses import dataclass, field
from decimal import Decimal

from app.domain.entities.nft.nft_asset import NFTAsset
from app.domain.ports.nft_marketplace_gateway import NFTMarketplaceGateway


@dataclass
class CollectionValue:
    """Value breakdown by collection."""

    slug: str
    count: int
    floor_price_eth: Decimal
    total_value_eth: Decimal


@dataclass
class GetNFTPortfolioRequest:
    """Request parameters for GetNFTPortfolio query."""

    address: str
    chain: str = "ethereum"
    include_valuation: bool = True


@dataclass
class NFTPortfolioResponse:
    """Response for NFT portfolio query."""

    address: str
    chain: str
    nfts: list[NFTAsset]
    total_count: int
    collection_count: int
    total_value_eth: Decimal = Decimal("0")
    total_value_usd: Decimal = Decimal("0")
    by_collection: list[CollectionValue] = field(default_factory=list)


class GetNFTPortfolio:
    """
    Query to get NFT portfolio with valuation.

    Groups NFTs by collection and calculates total value
    using floor prices.
    """

    # ETH price for USD conversion (placeholder)
    ETH_PRICE_USD = Decimal("2500")

    def __init__(self, gateway: NFTMarketplaceGateway):
        """Initialize query."""
        self._gateway = gateway

    async def execute(self, request: GetNFTPortfolioRequest) -> NFTPortfolioResponse:
        """Execute query to get portfolio."""
        nfts = await self._gateway.get_nfts_by_owner(
            address=request.address,
            chain=request.chain,
        )

        # Group by collection
        by_collection: dict[str, list[NFTAsset]] = {}
        for nft in nfts:
            if nft.collection_slug not in by_collection:
                by_collection[nft.collection_slug] = []
            by_collection[nft.collection_slug].append(nft)

        # Calculate valuation
        total_value_eth = Decimal("0")
        collection_values: list[CollectionValue] = []

        if request.include_valuation:
            for slug, collection_nfts in by_collection.items():
                floor_price = await self._gateway.get_floor_price(slug)
                if floor_price:
                    collection_value = floor_price * len(collection_nfts)
                    total_value_eth += collection_value
                    collection_values.append(
                        CollectionValue(
                            slug=slug,
                            count=len(collection_nfts),
                            floor_price_eth=floor_price,
                            total_value_eth=collection_value,
                        )
                    )

        # Sort collections by value (highest first)
        collection_values.sort(key=lambda c: c.total_value_eth, reverse=True)

        return NFTPortfolioResponse(
            address=request.address,
            chain=request.chain,
            nfts=nfts,
            total_count=len(nfts),
            collection_count=len(by_collection),
            total_value_eth=total_value_eth,
            total_value_usd=total_value_eth * self.ETH_PRICE_USD,
            by_collection=collection_values,
        )
