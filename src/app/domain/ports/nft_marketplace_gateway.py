"""
NFT Marketplace Gateway Port.

Defines the domain interface for NFT marketplace operations.
"""

from decimal import Decimal
from typing import Protocol

from app.domain.entities.nft.nft_asset import NFTAsset
from app.domain.entities.nft.nft_collection import NFTCollection
from app.domain.value_objects.nft.collection_stats import CollectionStats
from app.domain.value_objects.nft.nft_listing import NFTListing


class NFTMarketplaceGateway(Protocol):
    """
    Port interface for NFT marketplace operations.

    This protocol defines the contract for NFT data retrieval,
    collection stats, and portfolio management.
    """

    async def get_nfts_by_owner(
        self,
        address: str,
        chain: str = "ethereum",
        limit: int = 50,
    ) -> list[NFTAsset]:
        """
        Get NFTs owned by an address.

        Args:
            address: Wallet address
            chain: Blockchain name
            limit: Maximum NFTs to return

        Returns:
            List of NFTAsset entities
        """
        ...

    async def get_collection(
        self,
        collection_slug: str,
    ) -> NFTCollection | None:
        """
        Get collection information.

        Args:
            collection_slug: Collection identifier

        Returns:
            NFTCollection entity or None if not found
        """
        ...

    async def get_collection_stats(
        self,
        collection_slug: str,
    ) -> CollectionStats | None:
        """
        Get collection statistics.

        Args:
            collection_slug: Collection identifier

        Returns:
            CollectionStats value object or None
        """
        ...

    async def get_nft(
        self,
        contract_address: str,
        token_id: str,
        chain: str = "ethereum",
    ) -> NFTAsset | None:
        """
        Get single NFT details.

        Args:
            contract_address: NFT contract address
            token_id: Token identifier
            chain: Blockchain name

        Returns:
            NFTAsset entity or None if not found
        """
        ...

    async def get_listings(
        self,
        collection_slug: str,
        limit: int = 50,
    ) -> list[NFTListing]:
        """
        Get active listings for a collection.

        Args:
            collection_slug: Collection identifier
            limit: Maximum listings to return

        Returns:
            List of NFTListing value objects
        """
        ...

    async def get_floor_price(
        self,
        collection_slug: str,
    ) -> Decimal | None:
        """
        Get collection floor price.

        Args:
            collection_slug: Collection identifier

        Returns:
            Floor price in ETH or None
        """
        ...
