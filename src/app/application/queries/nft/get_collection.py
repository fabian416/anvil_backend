"""
GetCollection Query.

Application query for retrieving collection information.
"""

from dataclasses import dataclass

from app.domain.entities.nft.nft_collection import NFTCollection
from app.domain.exceptions.nft import CollectionNotFoundError
from app.domain.ports.nft_marketplace_gateway import NFTMarketplaceGateway


@dataclass
class GetCollectionRequest:
    """Request parameters for GetCollection query."""

    collection_slug: str


class GetCollection:
    """
    Query to get collection information.
    """

    def __init__(self, gateway: NFTMarketplaceGateway):
        """Initialize query."""
        self._gateway = gateway

    async def execute(self, request: GetCollectionRequest) -> NFTCollection:
        """Execute query to get collection."""
        collection = await self._gateway.get_collection(request.collection_slug)

        if not collection:
            raise CollectionNotFoundError(request.collection_slug)

        return collection
