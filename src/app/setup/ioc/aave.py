"""
Aave Providers for Dependency Injection.

Provides configured Aave V3 services:
- AaveAdapter implementing AaveGateway port
"""

from dishka import Provider, Scope, provide

from app.domain.ports.aave_gateway import AaveGateway
from app.infrastructure.adapters.external.aave_adapter import AaveAdapter
from app.infrastructure.cache.external_api_cache import ExternalAPICache
from app.setup.config.settings import AppSettings


class AaveProvider(Provider):
    """Provider for Aave V3 infrastructure services."""

    scope = Scope.APP

    @provide
    def provide_aave_gateway(
        self,
        cache: ExternalAPICache,
        settings: AppSettings,
    ) -> AaveGateway:
        """
        Provide AaveGateway implementation.

        Uses appropriate caching for market and position data.
        """
        api_key = getattr(settings.integrations, "thegraph_api_key", None)
        return AaveAdapter(
            cache=cache,
            api_key=api_key,
            market_cache_ttl=300,  # 5 minutes
            position_cache_ttl=120,  # 2 minutes
            stats_cache_ttl=600,  # 10 minutes
        )
