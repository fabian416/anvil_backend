"""
LayerZero Providers for Dependency Injection.

Provides configured LayerZero services:
- LayerZeroClient for API communication
- LayerZeroAdapter implementing LayerZeroGateway port
- Application queries
"""

from dishka import Provider, Scope, provide

from app.application.queries.layerzero.estimate_fees import EstimateFees
from app.application.queries.layerzero.get_chains import GetChains
from app.application.queries.layerzero.get_message_history import GetMessageHistory
from app.application.queries.layerzero.get_oft_transfers import GetOFTTransfers
from app.application.queries.layerzero.track_message import TrackMessage
from app.domain.ports.layerzero_gateway import LayerZeroGateway
from app.infrastructure.adapters.external.layerzero_adapter import LayerZeroAdapter
from app.infrastructure.adapters.external.layerzero_client import LayerZeroClient
from app.infrastructure.cache.external_api_cache import ExternalAPICache


class LayerZeroProvider(Provider):
    """Provider for LayerZero infrastructure and application services."""

    scope = Scope.APP

    @provide
    def provide_layerzero_client(self) -> LayerZeroClient:
        """
        Provide LayerZeroClient instance.

        Uses default API endpoint.
        """
        return LayerZeroClient()

    @provide
    def provide_layerzero_gateway(
        self,
        client: LayerZeroClient,
        cache: ExternalAPICache,
    ) -> LayerZeroGateway:
        """
        Provide LayerZeroGateway implementation.

        Uses smart caching:
        - DELIVERED messages: 24h
        - INFLIGHT messages: 10s
        - Chains: 1h
        """
        return LayerZeroAdapter(
            client=client,
            cache=cache,
            chain_cache_ttl=3600,  # 1 hour
            message_cache_ttl=10,  # 10 seconds
            delivered_cache_ttl=86400,  # 24 hours
            fee_cache_ttl=30,  # 30 seconds
            history_cache_ttl=60,  # 1 minute
        )

    # Application Layer Queries

    @provide(scope=Scope.REQUEST)
    def provide_track_message(self, gateway: LayerZeroGateway) -> TrackMessage:
        """Provide TrackMessage query."""
        return TrackMessage(gateway=gateway)

    @provide(scope=Scope.REQUEST)
    def provide_get_message_history(
        self, gateway: LayerZeroGateway
    ) -> GetMessageHistory:
        """Provide GetMessageHistory query."""
        return GetMessageHistory(gateway=gateway)

    @provide(scope=Scope.REQUEST)
    def provide_get_chains(self, gateway: LayerZeroGateway) -> GetChains:
        """Provide GetChains query."""
        return GetChains(gateway=gateway)

    @provide(scope=Scope.REQUEST)
    def provide_estimate_fees(self, gateway: LayerZeroGateway) -> EstimateFees:
        """Provide EstimateFees query."""
        return EstimateFees(gateway=gateway)

    @provide(scope=Scope.REQUEST)
    def provide_get_oft_transfers(self, gateway: LayerZeroGateway) -> GetOFTTransfers:
        """Provide GetOFTTransfers query."""
        return GetOFTTransfers(gateway=gateway)
