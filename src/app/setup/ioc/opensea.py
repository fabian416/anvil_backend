"""
OpenSea Providers for Dependency Injection.

Provides configured OpenSea services:
- OpenSeaClient for API communication
- OpenSeaAdapter implementing NFTMarketplaceGateway port
- Application queries
"""

from dishka import Provider, Scope, provide

from app.application.queries.nft.get_collection import GetCollection
from app.application.queries.nft.get_collection_stats import GetCollectionStats
from app.application.queries.nft.get_listings import GetListings
from app.application.queries.nft.get_nft_details import GetNFTDetails
from app.application.queries.nft.get_nft_portfolio import GetNFTPortfolio
from app.domain.ports.nft_marketplace_gateway import NFTMarketplaceGateway
from app.infrastructure.adapters.external.opensea_adapter import OpenSeaAdapter
from app.infrastructure.adapters.external.opensea_client import OpenSeaClient
from app.infrastructure.cache.external_api_cache import ExternalAPICache


class OpenSeaProvider(Provider):
    """Provider for OpenSea infrastructure and application services."""

    scope = Scope.APP

    @provide
    def provide_opensea_client(self) -> OpenSeaClient:
        """
        Provide OpenSeaClient instance.

        Note: API key can be configured via settings.
        """
        return OpenSeaClient()

    @provide
    def provide_nft_marketplace_gateway(
        self,
        client: OpenSeaClient,
        cache: ExternalAPICache,
    ) -> NFTMarketplaceGateway:
        """
        Provide NFTMarketplaceGateway implementation.

        Uses caching:
        - Collections: 15 minutes
        - Stats: 5 minutes
        - Portfolio: 10 minutes
        - Listings: 1 minute
        """
        return OpenSeaAdapter(
            client=client,
            cache=cache,
            collection_cache_ttl=900,  # 15 minutes
            stats_cache_ttl=300,  # 5 minutes
            portfolio_cache_ttl=600,  # 10 minutes
            nft_cache_ttl=900,  # 15 minutes
            listings_cache_ttl=60,  # 1 minute
        )

    # Application Layer Queries

    @provide(scope=Scope.REQUEST)
    def provide_get_nft_portfolio(self, gateway: NFTMarketplaceGateway) -> GetNFTPortfolio:
        """Provide GetNFTPortfolio query."""
        return GetNFTPortfolio(gateway=gateway)

    @provide(scope=Scope.REQUEST)
    def provide_get_collection(self, gateway: NFTMarketplaceGateway) -> GetCollection:
        """Provide GetCollection query."""
        return GetCollection(gateway=gateway)

    @provide(scope=Scope.REQUEST)
    def provide_get_collection_stats(self, gateway: NFTMarketplaceGateway) -> GetCollectionStats:
        """Provide GetCollectionStats query."""
        return GetCollectionStats(gateway=gateway)

    @provide(scope=Scope.REQUEST)
    def provide_get_nft_details(self, gateway: NFTMarketplaceGateway) -> GetNFTDetails:
        """Provide GetNFTDetails query."""
        return GetNFTDetails(gateway=gateway)

    @provide(scope=Scope.REQUEST)
    def provide_get_listings(self, gateway: NFTMarketplaceGateway) -> GetListings:
        """Provide GetListings query."""
        return GetListings(gateway=gateway)
