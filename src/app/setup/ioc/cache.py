"""
Cache Layer Providers.

Provides DI configuration for caching infrastructure.
"""

from dishka import Provider, Scope, provide
from redis.asyncio import Redis

from app.infrastructure.cache.external_api_cache import CacheConfig, ExternalAPICache
from app.infrastructure.cache.graph_cache import GraphQueryCache


class CacheProvider(Provider):
    """Provider for cache infrastructure."""
    
    scope = Scope.APP
    
    @provide
    def provide_cache_config(self) -> CacheConfig:
        """Provide cache configuration."""
        return CacheConfig(
            enabled=True,
            prefix="api_cache",
            # TTL values from config.toml could be injected here
            price_ttl=30,
            market_data_ttl=60,
            tvl_ttl=300,
            yield_ttl=300,
            protocol_details_ttl=900,
            historical_ttl=3600,
            trending_ttl=300,
            global_stats_ttl=120,
            gas_ttl=15,
            security_alerts_ttl=60,
            governance_ttl=600,
            nft_ttl=300,
            chain_data_ttl=300,
        )
    
    @provide
    def provide_external_api_cache(
        self,
        redis_client: Redis,
        config: CacheConfig,
    ) -> ExternalAPICache:
        """Provide external API cache."""
        return ExternalAPICache(
            redis_client=redis_client,
            config=config,
        )
    
    @provide
    def provide_graph_cache(
        self,
        redis_client: Redis,
    ) -> GraphQueryCache:
        """Provide graph query cache."""
        return GraphQueryCache(
            redis_client=redis_client,
            default_ttl=300,  # 5 minutes
        )
