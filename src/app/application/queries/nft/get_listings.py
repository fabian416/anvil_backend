"""
GetListings Query.

Application query for retrieving active listings.
"""

from dataclasses import dataclass

from app.domain.ports.nft_marketplace_gateway import NFTMarketplaceGateway
from app.domain.value_objects.nft.nft_listing import NFTListing


@dataclass
class GetListingsRequest:
    """Request parameters for GetListings query."""

    collection_slug: str
    limit: int = 50


@dataclass
class ListingsResponse:
    """Response for listings query."""

    listings: list[NFTListing]
    count: int
    collection_slug: str


class GetListings:
    """
    Query to get active listings for a collection.

    Returns listings sorted by price (lowest first).
    """

    def __init__(self, gateway: NFTMarketplaceGateway):
        """Initialize query."""
        self._gateway = gateway

    async def execute(self, request: GetListingsRequest) -> ListingsResponse:
        """Execute query to get listings."""
        listings = await self._gateway.get_listings(
            collection_slug=request.collection_slug,
            limit=request.limit,
        )

        # Sort by price (ascending)
        listings.sort(key=lambda l: l.price)

        return ListingsResponse(
            listings=listings,
            count=len(listings),
            collection_slug=request.collection_slug,
        )
