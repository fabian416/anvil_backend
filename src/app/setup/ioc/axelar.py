"""
Axelar Providers for Dependency Injection.

Provides configured Axelar services:
- AxelarClient for API communication
- AxelarAdapter implementing AxelarGateway port
- Application queries
"""

from decimal import Decimal

from dishka import Provider, Scope, provide

from app.application.queries.axelar.estimate_transfer import EstimateTransfer
from app.application.queries.axelar.get_chains import GetChains
from app.application.queries.axelar.get_routes import GetRoutes
from app.application.queries.axelar.get_tokens import GetTokens
from app.application.queries.axelar.track_transfer import TrackTransfer
from app.domain.ports.axelar_gateway import AxelarGateway
from app.infrastructure.adapters.external.axelar_adapter import AxelarAdapter
from app.infrastructure.adapters.external.axelar_client import AxelarClient
from app.infrastructure.cache.external_api_cache import ExternalAPICache


class AxelarProvider(Provider):
    """Provider for Axelar infrastructure and application services."""

    scope = Scope.APP

    @provide
    def provide_axelar_client(self) -> AxelarClient:
        """
        Provide AxelarClient instance.

        Uses mainnet by default.
        """
        return AxelarClient()

    @provide
    def provide_axelar_gateway(
        self,
        client: AxelarClient,
        cache: ExternalAPICache,
    ) -> AxelarGateway:
        """
        Provide AxelarGateway implementation.

        Uses caching for static data:
        - Routes: 5 minutes
        - Chains: 1 hour
        - Active transfers: 15 seconds
        """
        return AxelarAdapter(
            client=client,
            cache=cache,
            route_cache_ttl=300,  # 5 minutes
            chain_cache_ttl=3600,  # 1 hour
            transfer_cache_ttl=15,  # 15 seconds
            completed_cache_ttl=86400,  # 24 hours
            express_fee_multiplier=Decimal("2.0"),
            express_time_divisor=3,
        )

    # Application Layer Queries

    @provide(scope=Scope.REQUEST)
    def provide_get_routes(self, gateway: AxelarGateway) -> GetRoutes:
        """Provide GetRoutes query."""
        return GetRoutes(gateway=gateway)

    @provide(scope=Scope.REQUEST)
    def provide_estimate_transfer(self, gateway: AxelarGateway) -> EstimateTransfer:
        """Provide EstimateTransfer query."""
        return EstimateTransfer(gateway=gateway)

    @provide(scope=Scope.REQUEST)
    def provide_track_transfer(self, gateway: AxelarGateway) -> TrackTransfer:
        """Provide TrackTransfer query."""
        return TrackTransfer(gateway=gateway)

    @provide(scope=Scope.REQUEST)
    def provide_get_chains(self, gateway: AxelarGateway) -> GetChains:
        """Provide GetChains query."""
        return GetChains(gateway=gateway)

    @provide(scope=Scope.REQUEST)
    def provide_get_tokens(self, gateway: AxelarGateway) -> GetTokens:
        """Provide GetTokens query."""
        return GetTokens(gateway=gateway)
