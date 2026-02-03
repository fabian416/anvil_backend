"""
OpenSea HTTP Router.

Provides REST API endpoints for NFT marketplace operations.
"""

from decimal import Decimal

from dishka import FromDishka
from dishka.integrations.fastapi import inject
from fastapi import APIRouter, Query, status
from fastapi_error_map import ErrorAwareRouter, rule

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
from app.domain.exceptions.nft import (
    CollectionNotFoundError,
    InvalidAddressError,
    NFTError,
    NFTNotFoundError,
    OpenSeaAPIError,
    RateLimitError,
)
from app.domain.ports.nft_marketplace_gateway import NFTMarketplaceGateway
from app.presentation.http.controllers.nft.opensea_schemas import (
    CollectionStatsResponse,
    CollectionStatsResponseModel,
    CollectionValueResponse,
    FloorPriceResponse,
    ListingsResponse,
    NFTAssetResponse,
    NFTCollectionResponse,
    NFTListingResponse,
    NFTPortfolioResponse,
)
from app.presentation.http.errors.callbacks import log_error, log_info
from app.presentation.http.errors.translators import (
    NotFoundErrorTranslator,
    ServiceUnavailableTranslator,
    StandardizedErrorTranslator,
)


def create_opensea_router() -> APIRouter:
    """Create and configure the OpenSea router."""
    router = ErrorAwareRouter(prefix="/opensea", tags=["NFT", "Marketplace"])

    # Common error map
    nft_error_map = {
        CollectionNotFoundError: rule(
            status=status.HTTP_404_NOT_FOUND,
            translator=NotFoundErrorTranslator(resource_type="collection"),
            on_error=log_info,
        ),
        NFTNotFoundError: rule(
            status=status.HTTP_404_NOT_FOUND,
            translator=NotFoundErrorTranslator(resource_type="NFT"),
            on_error=log_info,
        ),
        InvalidAddressError: rule(
            status=status.HTTP_400_BAD_REQUEST,
            translator=StandardizedErrorTranslator(),
            on_error=log_info,
        ),
        RateLimitError: rule(
            status=status.HTTP_429_TOO_MANY_REQUESTS,
            translator=StandardizedErrorTranslator(),
            on_error=log_info,
        ),
        OpenSeaAPIError: rule(
            status=status.HTTP_502_BAD_GATEWAY,
            translator=ServiceUnavailableTranslator(),
            on_error=log_error,
        ),
        NFTError: rule(
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            translator=StandardizedErrorTranslator(),
            on_error=log_error,
        ),
    }

    @router.get(
        "/portfolio/{address}",
        summary="Get NFT Portfolio",
        description="Get NFT portfolio with valuation breakdown by collection",
        response_model=NFTPortfolioResponse,
        error_map=nft_error_map,
        default_on_error=log_info,
        status_code=status.HTTP_200_OK,
    )
    @inject
    async def get_portfolio(
        address: str,
        query: FromDishka[GetNFTPortfolio],
        chain: str = Query(default="ethereum", description="Blockchain"),
        include_valuation: bool = Query(
            default=True, description="Include floor price valuation"
        ),
    ) -> NFTPortfolioResponse:
        """Get NFT portfolio."""
        request = GetNFTPortfolioRequest(
            address=address,
            chain=chain,
            include_valuation=include_valuation,
        )
        response = await query.execute(request)

        return NFTPortfolioResponse(
            address=response.address,
            chain=response.chain,
            nfts=[NFTAssetResponse.from_domain(n) for n in response.nfts],
            total_count=response.total_count,
            collection_count=response.collection_count,
            total_value_eth=str(response.total_value_eth),
            total_value_usd=str(response.total_value_usd),
            by_collection=[
                CollectionValueResponse(
                    slug=c.slug,
                    count=c.count,
                    floor_price_eth=str(c.floor_price_eth),
                    total_value_eth=str(c.total_value_eth),
                )
                for c in response.by_collection
            ],
        )

    @router.get(
        "/collections/{slug}",
        summary="Get Collection",
        description="Get NFT collection information",
        response_model=NFTCollectionResponse,
        error_map=nft_error_map,
        default_on_error=log_info,
        status_code=status.HTTP_200_OK,
    )
    @inject
    async def get_collection(
        slug: str,
        query: FromDishka[GetCollection],
    ) -> NFTCollectionResponse:
        """Get collection information."""
        request = GetCollectionRequest(collection_slug=slug)
        collection = await query.execute(request)
        return NFTCollectionResponse.from_domain(collection)

    @router.get(
        "/collections/{slug}/stats",
        summary="Get Collection Stats",
        description="Get collection market statistics with sentiment analysis",
        response_model=CollectionStatsResponse,
        error_map=nft_error_map,
        default_on_error=log_info,
        status_code=status.HTTP_200_OK,
    )
    @inject
    async def get_collection_stats(
        slug: str,
        query: FromDishka[GetCollectionStats],
    ) -> CollectionStatsResponse:
        """Get collection statistics."""
        request = GetCollectionStatsRequest(collection_slug=slug)
        response = await query.execute(request)

        return CollectionStatsResponse(
            stats=CollectionStatsResponseModel.from_domain(response.stats),
            market_sentiment=response.market_sentiment,
            floor_change_alert=response.floor_change_alert,
        )

    @router.get(
        "/assets/{contract_address}/{token_id}",
        summary="Get NFT Details",
        description="Get single NFT details with traits",
        response_model=NFTAssetResponse,
        error_map=nft_error_map,
        default_on_error=log_info,
        status_code=status.HTTP_200_OK,
    )
    @inject
    async def get_nft_details(
        contract_address: str,
        token_id: str,
        query: FromDishka[GetNFTDetails],
        chain: str = Query(default="ethereum", description="Blockchain"),
    ) -> NFTAssetResponse:
        """Get NFT details."""
        request = GetNFTDetailsRequest(
            contract_address=contract_address,
            token_id=token_id,
            chain=chain,
        )
        nft = await query.execute(request)
        return NFTAssetResponse.from_domain(nft)

    @router.get(
        "/collections/{slug}/listings",
        summary="Get Listings",
        description="Get active listings for a collection",
        response_model=ListingsResponse,
        error_map=nft_error_map,
        default_on_error=log_info,
        status_code=status.HTTP_200_OK,
    )
    @inject
    async def get_listings(
        slug: str,
        query: FromDishka[GetListings],
        limit: int = Query(default=50, ge=1, le=100, description="Max results"),
    ) -> ListingsResponse:
        """Get active listings."""
        request = GetListingsRequest(collection_slug=slug, limit=limit)
        response = await query.execute(request)

        return ListingsResponse(
            listings=[NFTListingResponse.from_domain(l) for l in response.listings],
            count=response.count,
            collection_slug=response.collection_slug,
        )

    @router.get(
        "/collections/{slug}/floor",
        summary="Get Floor Price",
        description="Get current floor price for a collection",
        response_model=FloorPriceResponse,
        error_map=nft_error_map,
        default_on_error=log_info,
        status_code=status.HTTP_200_OK,
    )
    @inject
    async def get_floor_price(
        slug: str,
        gateway: FromDishka[NFTMarketplaceGateway],
    ) -> FloorPriceResponse:
        """Get floor price."""
        floor_price = await gateway.get_floor_price(slug)

        floor_usd = None
        if floor_price:
            floor_usd = str(floor_price * Decimal("2500"))  # Placeholder ETH price

        return FloorPriceResponse(
            collection_slug=slug,
            floor_price_eth=str(floor_price) if floor_price else None,
            floor_price_usd=floor_usd,
        )

    return router
