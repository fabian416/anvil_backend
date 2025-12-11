"""
Morpho Providers for Dependency Injection.

Provides configured Morpho services:
- MorphoClient for GraphQL communication
- MorphoAdapter implementing MorphoGateway port
- Application queries
"""

from dishka import Provider, Scope, provide

from app.application.queries.morpho.compare_yields import CompareYields
from app.application.queries.morpho.get_markets import GetMarkets
from app.application.queries.morpho.get_user_positions import GetUserPositions
from app.application.queries.morpho.get_vault_apy import GetVaultAPY
from app.application.queries.morpho.get_vault_details import GetVaultDetails
from app.application.queries.morpho.get_vaults import GetVaults
from app.domain.ports.morpho_gateway import MorphoGateway
from app.infrastructure.adapters.external.morpho_adapter import MorphoAdapter
from app.infrastructure.adapters.external.morpho_client import MorphoClient
from app.infrastructure.cache.external_api_cache import ExternalAPICache


class MorphoProvider(Provider):
    """Provider for Morpho infrastructure and application services."""

    scope = Scope.APP

    @provide
    def provide_morpho_client(self) -> MorphoClient:
        """
        Provide MorphoClient instance.

        Uses default subgraph URL for Morpho Blue mainnet.
        """
        return MorphoClient()

    @provide
    def provide_morpho_gateway(
        self,
        client: MorphoClient,
        cache: ExternalAPICache,
    ) -> MorphoGateway:
        """
        Provide MorphoGateway implementation.

        Uses appropriate caching for vault data.
        """
        return MorphoAdapter(
            client=client,
            cache=cache,
            vault_cache_ttl=600,  # 10 minutes
            apy_cache_ttl=300,  # 5 minutes
            position_cache_ttl=600,  # 10 minutes
            market_cache_ttl=300,  # 5 minutes
        )

    # Application Layer Queries

    @provide(scope=Scope.REQUEST)
    def provide_get_vaults(self, gateway: MorphoGateway) -> GetVaults:
        """Provide GetVaults query."""
        return GetVaults(gateway=gateway)

    @provide(scope=Scope.REQUEST)
    def provide_get_vault_details(self, gateway: MorphoGateway) -> GetVaultDetails:
        """Provide GetVaultDetails query."""
        return GetVaultDetails(gateway=gateway)

    @provide(scope=Scope.REQUEST)
    def provide_get_vault_apy(self, gateway: MorphoGateway) -> GetVaultAPY:
        """Provide GetVaultAPY query."""
        return GetVaultAPY(gateway=gateway)

    @provide(scope=Scope.REQUEST)
    def provide_get_markets(self, gateway: MorphoGateway) -> GetMarkets:
        """Provide GetMarkets query."""
        return GetMarkets(gateway=gateway)

    @provide(scope=Scope.REQUEST)
    def provide_get_user_positions(self, gateway: MorphoGateway) -> GetUserPositions:
        """Provide GetUserPositions query."""
        return GetUserPositions(gateway=gateway)

    @provide(scope=Scope.REQUEST)
    def provide_compare_yields(self, gateway: MorphoGateway) -> CompareYields:
        """Provide CompareYields query."""
        return CompareYields(gateway=gateway)
