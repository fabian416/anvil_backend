"""
Curve Finance Providers for Dependency Injection.

Provides configured Curve services:
- CurveClient for API communication
- CurveAdapter implementing CurveGateway port
- Application queries and commands
"""

from dishka import Provider, Scope, provide

from app.application.commands.curve.get_swap_quote import GetSwapQuote
from app.application.queries.curve.get_gauges import GetGauges
from app.application.queries.curve.get_pool_apy import GetPoolAPY
from app.application.queries.curve.get_pools import GetPools
from app.application.queries.curve.get_tvl import GetTVL
from app.domain.ports.curve_gateway import CurveGateway
from app.infrastructure.adapters.external.curve_adapter import CurveAdapter
from app.infrastructure.adapters.external.curve_client import CurveClient
from app.infrastructure.cache.external_api_cache import ExternalAPICache


class CurveProvider(Provider):
    """Provider for Curve Finance infrastructure and application services."""

    scope = Scope.APP

    @provide
    def provide_curve_client(self) -> CurveClient:
        """
        Provide CurveClient instance.

        Uses default chain (ethereum) - the adapter handles chain switching.
        """
        return CurveClient(chain="ethereum")

    @provide
    def provide_curve_gateway(
        self,
        client: CurveClient,
        cache: ExternalAPICache,
    ) -> CurveGateway:
        """
        Provide CurveGateway implementation.

        The CurveAdapter wraps the client with caching and
        transforms data to domain models.
        """
        return CurveAdapter(
            client=client,
            cache=cache,
            pool_cache_ttl=300,  # 5 minutes
            apy_cache_ttl=60,  # 1 minute
            gauge_cache_ttl=600,  # 10 minutes
            tvl_cache_ttl=300,  # 5 minutes
        )

    # Application Layer Queries

    @provide(scope=Scope.REQUEST)
    def provide_get_pools(self, gateway: CurveGateway) -> GetPools:
        """Provide GetPools query."""
        return GetPools(gateway=gateway)

    @provide(scope=Scope.REQUEST)
    def provide_get_pool_apy(self, gateway: CurveGateway) -> GetPoolAPY:
        """Provide GetPoolAPY query."""
        return GetPoolAPY(gateway=gateway)

    @provide(scope=Scope.REQUEST)
    def provide_get_gauges(self, gateway: CurveGateway) -> GetGauges:
        """Provide GetGauges query."""
        return GetGauges(gateway=gateway)

    @provide(scope=Scope.REQUEST)
    def provide_get_tvl(self, gateway: CurveGateway) -> GetTVL:
        """Provide GetTVL query."""
        return GetTVL(gateway=gateway)

    # Application Layer Commands

    @provide(scope=Scope.REQUEST)
    def provide_get_swap_quote(self, gateway: CurveGateway) -> GetSwapQuote:
        """Provide GetSwapQuote command."""
        return GetSwapQuote(gateway=gateway)
