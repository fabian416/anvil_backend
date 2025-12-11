"""
Hyperliquid Providers for Dependency Injection.

Provides configured Hyperliquid services:
- HyperliquidClient for API communication
- HyperliquidAdapter implementing PerpetualGateway port
- Application queries and commands
"""

from dishka import Provider, Scope, provide

from app.application.commands.perpetual.calculate_risk import CalculateRisk
from app.application.queries.perpetual.get_funding_rates import GetFundingRates
from app.application.queries.perpetual.get_liquidations import GetLiquidations
from app.application.queries.perpetual.get_markets import GetMarkets
from app.application.queries.perpetual.get_order_book import GetOrderBook
from app.application.queries.perpetual.get_positions import GetPositions
from app.domain.ports.perpetual_gateway import PerpetualGateway
from app.infrastructure.adapters.external.hyperliquid_adapter import HyperliquidAdapter
from app.infrastructure.adapters.external.hyperliquid_client import HyperliquidClient
from app.infrastructure.cache.external_api_cache import ExternalAPICache


class HyperliquidProvider(Provider):
    """Provider for Hyperliquid infrastructure and application services."""

    scope = Scope.APP

    @provide
    def provide_hyperliquid_client(self) -> HyperliquidClient:
        """
        Provide HyperliquidClient instance.

        No API key needed for public data endpoints.
        """
        return HyperliquidClient(testnet=False)

    @provide
    def provide_perpetual_gateway(
        self,
        client: HyperliquidClient,
        cache: ExternalAPICache,
    ) -> PerpetualGateway:
        """
        Provide PerpetualGateway implementation.

        Uses minimal caching for real-time data.
        """
        return HyperliquidAdapter(
            client=client,
            cache=cache,
            market_cache_ttl=5,  # 5 seconds
            funding_cache_ttl=30,  # 30 seconds
            position_cache_ttl=10,  # 10 seconds
            liquidation_cache_ttl=60,  # 1 minute
        )

    # Application Layer Queries

    @provide(scope=Scope.REQUEST)
    def provide_get_markets(self, gateway: PerpetualGateway) -> GetMarkets:
        """Provide GetMarkets query."""
        return GetMarkets(gateway=gateway)

    @provide(scope=Scope.REQUEST)
    def provide_get_order_book(self, gateway: PerpetualGateway) -> GetOrderBook:
        """Provide GetOrderBook query."""
        return GetOrderBook(gateway=gateway)

    @provide(scope=Scope.REQUEST)
    def provide_get_funding_rates(self, gateway: PerpetualGateway) -> GetFundingRates:
        """Provide GetFundingRates query."""
        return GetFundingRates(gateway=gateway)

    @provide(scope=Scope.REQUEST)
    def provide_get_liquidations(self, gateway: PerpetualGateway) -> GetLiquidations:
        """Provide GetLiquidations query."""
        return GetLiquidations(gateway=gateway)

    @provide(scope=Scope.REQUEST)
    def provide_get_positions(self, gateway: PerpetualGateway) -> GetPositions:
        """Provide GetPositions query."""
        return GetPositions(gateway=gateway)

    # Application Layer Commands

    @provide(scope=Scope.REQUEST)
    def provide_calculate_risk(self, gateway: PerpetualGateway) -> CalculateRisk:
        """Provide CalculateRisk command."""
        return CalculateRisk(gateway=gateway)
