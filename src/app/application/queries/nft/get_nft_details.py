"""
GetNFTDetails Query.

Application query for retrieving single NFT details.
"""

from dataclasses import dataclass

from app.domain.entities.nft.nft_asset import NFTAsset
from app.domain.exceptions.nft import NFTNotFoundError
from app.domain.ports.nft_marketplace_gateway import NFTMarketplaceGateway


@dataclass
class GetNFTDetailsRequest:
    """Request parameters for GetNFTDetails query."""

    contract_address: str
    token_id: str
    chain: str = "ethereum"


class GetNFTDetails:
    """
    Query to get single NFT details.
    """

    def __init__(self, gateway: NFTMarketplaceGateway):
        """Initialize query."""
        self._gateway = gateway

    async def execute(self, request: GetNFTDetailsRequest) -> NFTAsset:
        """Execute query to get NFT details."""
        nft = await self._gateway.get_nft(
            contract_address=request.contract_address,
            token_id=request.token_id,
            chain=request.chain,
        )

        if not nft:
            raise NFTNotFoundError(request.contract_address, request.token_id)

        return nft
