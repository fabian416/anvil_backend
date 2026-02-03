"""NFT application queries."""

from app.application.queries.nft.get_collection import (
    GetCollection,
    GetCollectionRequest,
)
from app.application.queries.nft.get_collection_stats import (
    GetCollectionStats,
    GetCollectionStatsRequest,
)
from app.application.queries.nft.get_listings import GetListings, GetListingsRequest
from app.application.queries.nft.get_nft_details import (
    GetNFTDetails,
    GetNFTDetailsRequest,
)
from app.application.queries.nft.get_nft_portfolio import (
    GetNFTPortfolio,
    GetNFTPortfolioRequest,
)

__all__ = [
    "GetNFTPortfolio",
    "GetNFTPortfolioRequest",
    "GetCollection",
    "GetCollectionRequest",
    "GetCollectionStats",
    "GetCollectionStatsRequest",
    "GetNFTDetails",
    "GetNFTDetailsRequest",
    "GetListings",
    "GetListingsRequest",
]
