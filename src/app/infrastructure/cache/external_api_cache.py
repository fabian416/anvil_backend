"""
External API Cache Layer.

Redis-based caching for external API responses to reduce API calls,
improve response times, and handle rate limits gracefully.

Features:
- Configurable TTL per API/endpoint
- Automatic cache key generation
- Cache warming support
- Statistics tracking
- Graceful degradation
"""

import hashlib
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Optional, TypeVar

import redis.asyncio as aioredis

logger = logging.getLogger(__name__)

T = TypeVar("T")


class CacheTier(Enum):
    """Cache TTL tiers for different data freshness requirements."""
    
    REALTIME = 10        # 10 seconds - prices, gas
    SHORT = 60           # 1 minute - trending, hot data
    MEDIUM = 300         # 5 minutes - market data, TVL
    LONG = 900           # 15 minutes - protocol details
    EXTENDED = 3600      # 1 hour - historical data, static info
    DAILY = 86400        # 24 hours - rarely changing data


@dataclass
class CacheConfig:
    """Configuration for external API caching."""
    
    # Default TTLs by data type (in seconds)
    price_ttl: int = 30                    # Price data - 30 seconds
    market_data_ttl: int = 60              # Market caps, volumes - 1 minute
    tvl_ttl: int = 300                     # TVL data - 5 minutes
    yield_ttl: int = 300                   # Yield/APY data - 5 minutes
    protocol_details_ttl: int = 900        # Protocol info - 15 minutes
    historical_ttl: int = 3600             # Historical data - 1 hour
    trending_ttl: int = 300                # Trending data - 5 minutes
    global_stats_ttl: int = 120            # Global market stats - 2 minutes
    gas_ttl: int = 15                      # Gas prices - 15 seconds
    security_alerts_ttl: int = 60          # Security alerts - 1 minute
    governance_ttl: int = 600              # Governance data - 10 minutes
    nft_ttl: int = 300                     # NFT data - 5 minutes
    chain_data_ttl: int = 300              # Chain/bridge data - 5 minutes
    
    # Cache behavior
    enabled: bool = True
    prefix: str = "api_cache"
    max_key_length: int = 256
    compression_threshold: int = 1024      # Compress values > 1KB
    
    # Rate limit protection
    rate_limit_backoff_ttl: int = 60       # Cache rate-limited responses for 60s
    error_cache_ttl: int = 10              # Cache errors briefly to prevent thundering herd


@dataclass
class CacheStats:
    """Cache statistics."""
    
    hits: int = 0
    misses: int = 0
    errors: int = 0
    size_bytes: int = 0
    keys_count: int = 0
    avg_ttl: float = 0.0
    
    @property
    def hit_rate(self) -> float:
        """Calculate hit rate percentage."""
        total = self.hits + self.misses
        return (self.hits / total * 100) if total > 0 else 0.0


@dataclass
class CachedResponse:
    """Cached API response with metadata."""
    
    data: Any
    cached_at: datetime
    ttl: int
    source: str
    hit_count: int = 0
    
    def is_expired(self) -> bool:
        """Check if cache entry has expired."""
        elapsed = (datetime.utcnow() - self.cached_at).total_seconds()
        return elapsed > self.ttl


class ExternalAPICache:
    """
    Redis-based cache for external API responses.
    
    Supports all external API clients:
    - CoinGecko (prices, market data)
    - DeFiLlama (TVL, yields)
    - 1inch (swap quotes)
    - The Graph (protocol data)
    - Forta (security alerts)
    - OpenSea (NFT data)
    - And more...
    
    Example:
        >>> cache = ExternalAPICache(redis_client)
        >>> 
        >>> # Check cache first
        >>> cached = await cache.get("coingecko", "price", coin_id="ethereum")
        >>> if cached:
        ...     return cached
        >>> 
        >>> # Fetch from API
        >>> data = await coingecko_client.get_price("ethereum")
        >>> 
        >>> # Store in cache
        >>> await cache.set("coingecko", "price", data, coin_id="ethereum")
    """
    
    def __init__(
        self,
        redis_client: aioredis.Redis,
        config: Optional[CacheConfig] = None,
    ):
        """
        Initialize external API cache.
        
        Args:
            redis_client: Redis async client
            config: Cache configuration (optional)
        """
        self._redis = redis_client
        self._config = config or CacheConfig()
        self._stats = CacheStats()
        
        # TTL mapping by API and operation type
        self._ttl_map = {
            # CoinGecko
            ("coingecko", "price"): self._config.price_ttl,
            ("coingecko", "prices_bulk"): self._config.price_ttl,
            ("coingecko", "market_chart"): self._config.historical_ttl,
            ("coingecko", "coin_details"): self._config.protocol_details_ttl,
            ("coingecko", "trending"): self._config.trending_ttl,
            ("coingecko", "global"): self._config.global_stats_ttl,
            ("coingecko", "search"): self._config.protocol_details_ttl,
            
            # DeFiLlama
            ("defillama", "protocols"): self._config.tvl_ttl,
            ("defillama", "protocol_tvl"): self._config.tvl_ttl,
            ("defillama", "yields"): self._config.yield_ttl,
            ("defillama", "chain_tvl"): self._config.tvl_ttl,
            ("defillama", "stablecoins"): self._config.market_data_ttl,
            ("defillama", "fees"): self._config.historical_ttl,
            
            # 1inch
            ("oneinch", "quote"): self._config.price_ttl,
            ("oneinch", "swap"): 5,  # Very short - swap data changes fast
            ("oneinch", "tokens"): self._config.protocol_details_ttl,
            ("oneinch", "liquidity"): self._config.tvl_ttl,
            
            # The Graph / Uniswap
            ("thegraph", "query"): self._config.tvl_ttl,
            ("uniswap", "pools"): self._config.tvl_ttl,
            ("uniswap", "tokens"): self._config.market_data_ttl,
            ("uniswap", "positions"): self._config.tvl_ttl,
            
            # Aave
            ("aave", "markets"): self._config.tvl_ttl,
            ("aave", "user_positions"): self._config.tvl_ttl,
            ("aave", "rates"): self._config.yield_ttl,
            
            # Curve
            ("curve", "pools"): self._config.tvl_ttl,
            ("curve", "gauges"): self._config.yield_ttl,
            
            # Hyperliquid
            ("hyperliquid", "orderbook"): 5,  # Very short - orderbook changes fast
            ("hyperliquid", "positions"): self._config.price_ttl,
            ("hyperliquid", "funding"): self._config.price_ttl,
            
            # Gas / Etherscan
            ("etherscan", "gas"): self._config.gas_ttl,
            ("blocknative", "gas"): self._config.gas_ttl,
            ("etherscan", "transactions"): self._config.historical_ttl,
            
            # Security
            ("forta", "alerts"): self._config.security_alerts_ttl,
            ("chainalysis", "screening"): self._config.security_alerts_ttl,
            ("trm_labs", "screening"): self._config.security_alerts_ttl,
            
            # NFT
            ("opensea", "collection"): self._config.nft_ttl,
            ("opensea", "listings"): self._config.nft_ttl,
            ("opensea", "floor_price"): self._config.price_ttl,
            
            # Governance
            ("snapshot", "proposals"): self._config.governance_ttl,
            ("snapshot", "votes"): self._config.governance_ttl,
            ("snapshot", "spaces"): self._config.protocol_details_ttl,
            
            # Cross-chain
            ("axelar", "routes"): self._config.chain_data_ttl,
            ("layerzero", "routes"): self._config.chain_data_ttl,

            # Gnosis Safe
            ("gnosis", "safes"): self._config.chain_data_ttl,
            ("gnosis", "transactions"): self._config.historical_ttl,

            # Translation
            ("deepl", "translate"): self._config.protocol_details_ttl,  # 15 minutes
            ("deepl", "detect"): self._config.protocol_details_ttl,
            ("google_translate", "translate"): self._config.protocol_details_ttl,
            ("google_translate", "detect"): self._config.protocol_details_ttl,
        }
    
    def _make_key(self, api: str, operation: str, **params) -> str:
        """
        Generate cache key from API, operation, and parameters.
        
        Args:
            api: API name (e.g., "coingecko", "defillama")
            operation: Operation name (e.g., "price", "tvl")
            **params: Parameters for the operation
            
        Returns:
            Cache key string
        """
        # Sort params for consistent keys
        sorted_params = sorted(
            (k, str(v)) for k, v in params.items() 
            if v is not None
        )
        param_str = json.dumps(sorted_params, sort_keys=True)
        
        # Hash for shorter keys
        param_hash = hashlib.sha256(param_str.encode()).hexdigest()[:16]
        
        key = f"{self._config.prefix}:{api}:{operation}:{param_hash}"
        
        # Truncate if too long
        if len(key) > self._config.max_key_length:
            key = key[:self._config.max_key_length]
        
        return key
    
    def _get_ttl(self, api: str, operation: str) -> int:
        """
        Get TTL for API/operation combination.
        
        Args:
            api: API name
            operation: Operation name
            
        Returns:
            TTL in seconds
        """
        return self._ttl_map.get(
            (api.lower(), operation.lower()),
            self._config.market_data_ttl,  # Default TTL
        )
    
    async def get(
        self,
        api: str,
        operation: str,
        **params,
    ) -> Optional[Any]:
        """
        Get cached API response.
        
        Args:
            api: API name (e.g., "coingecko")
            operation: Operation name (e.g., "price")
            **params: Parameters used in the API call
            
        Returns:
            Cached data or None if not found/expired
            
        Example:
            >>> data = await cache.get("coingecko", "price", coin_id="ethereum")
            >>> if data:
            ...     print(f"Cached ETH price: ${data['usd']}")
        """
        if not self._config.enabled:
            return None
        
        key = self._make_key(api, operation, **params)
        
        try:
            cached = await self._redis.get(key)
            
            if cached:
                self._stats.hits += 1
                data = json.loads(cached)
                logger.debug(f"Cache HIT: {api}/{operation} ({key})")
                return data
            
            self._stats.misses += 1
            logger.debug(f"Cache MISS: {api}/{operation} ({key})")
            return None
            
        except Exception as e:
            self._stats.errors += 1
            logger.warning(f"Cache get error for {api}/{operation}: {e}")
            return None
    
    async def set(
        self,
        api: str,
        operation: str,
        data: Any,
        ttl: Optional[int] = None,
        **params,
    ) -> bool:
        """
        Cache API response.
        
        Args:
            api: API name
            operation: Operation name
            data: Data to cache (must be JSON serializable)
            ttl: Optional custom TTL (uses default if not provided)
            **params: Parameters used in the API call
            
        Returns:
            True if cached successfully
            
        Example:
            >>> await cache.set(
            ...     "coingecko", "price",
            ...     {"usd": 3500.0, "usd_24h_change": 2.5},
            ...     coin_id="ethereum"
            ... )
        """
        if not self._config.enabled:
            return False
        
        key = self._make_key(api, operation, **params)
        ttl = ttl or self._get_ttl(api, operation)
        
        try:
            serialized = json.dumps(data)
            await self._redis.setex(key, ttl, serialized)
            logger.debug(f"Cache SET: {api}/{operation} TTL={ttl}s ({key})")
            return True
            
        except Exception as e:
            self._stats.errors += 1
            logger.warning(f"Cache set error for {api}/{operation}: {e}")
            return False
    
    async def get_or_fetch(
        self,
        api: str,
        operation: str,
        fetch_func: Callable[[], T],
        ttl: Optional[int] = None,
        **params,
    ) -> T:
        """
        Get from cache or fetch from API.
        
        This is the recommended pattern for using the cache.
        
        Args:
            api: API name
            operation: Operation name
            fetch_func: Async function to call if cache misses
            ttl: Optional custom TTL
            **params: Parameters for cache key and fetch function
            
        Returns:
            Cached or freshly fetched data
            
        Example:
            >>> async def fetch_price():
            ...     return await coingecko.get_price("ethereum")
            >>> 
            >>> price = await cache.get_or_fetch(
            ...     "coingecko", "price",
            ...     fetch_price,
            ...     coin_id="ethereum"
            ... )
        """
        # Try cache first
        cached = await self.get(api, operation, **params)
        if cached is not None:
            return cached
        
        # Fetch from API
        data = await fetch_func()
        
        # Cache the result
        await self.set(api, operation, data, ttl=ttl, **params)
        
        return data
    
    async def invalidate(
        self,
        api: Optional[str] = None,
        operation: Optional[str] = None,
    ) -> int:
        """
        Invalidate cache entries.
        
        Args:
            api: API name to invalidate (None = all APIs)
            operation: Operation to invalidate (None = all operations)
            
        Returns:
            Number of keys invalidated
            
        Example:
            >>> # Invalidate all CoinGecko cache
            >>> await cache.invalidate(api="coingecko")
            >>> 
            >>> # Invalidate all price caches
            >>> await cache.invalidate(operation="price")
        """
        if api and operation:
            pattern = f"{self._config.prefix}:{api}:{operation}:*"
        elif api:
            pattern = f"{self._config.prefix}:{api}:*"
        elif operation:
            pattern = f"{self._config.prefix}:*:{operation}:*"
        else:
            pattern = f"{self._config.prefix}:*"
        
        try:
            cursor = 0
            deleted = 0
            
            while True:
                cursor, keys = await self._redis.scan(
                    cursor,
                    match=pattern,
                    count=100,
                )
                
                if keys:
                    await self._redis.delete(*keys)
                    deleted += len(keys)
                
                if cursor == 0:
                    break
            
            logger.info(f"Invalidated {deleted} cache keys (pattern: {pattern})")
            return deleted
            
        except Exception as e:
            logger.error(f"Cache invalidation error: {e}")
            return 0
    
    async def warm(
        self,
        warmup_data: list[tuple[str, str, Any, dict]],
    ) -> int:
        """
        Pre-warm cache with data.
        
        Args:
            warmup_data: List of (api, operation, data, params) tuples
            
        Returns:
            Number of entries cached
            
        Example:
            >>> warmup = [
            ...     ("coingecko", "price", {"usd": 3500}, {"coin_id": "ethereum"}),
            ...     ("coingecko", "price", {"usd": 95000}, {"coin_id": "bitcoin"}),
            ... ]
            >>> await cache.warm(warmup)
        """
        cached = 0
        
        for api, operation, data, params in warmup_data:
            success = await self.set(api, operation, data, **params)
            if success:
                cached += 1
        
        logger.info(f"Warmed cache with {cached} entries")
        return cached
    
    async def get_stats(self) -> dict:
        """
        Get cache statistics.
        
        Returns:
            Dictionary with cache statistics
        """
        try:
            # Count API cache keys
            pattern = f"{self._config.prefix}:*"
            cursor = 0
            key_count = 0
            
            while True:
                cursor, keys = await self._redis.scan(
                    cursor,
                    match=pattern,
                    count=100,
                )
                key_count += len(keys)
                
                if cursor == 0:
                    break
            
            return {
                "enabled": self._config.enabled,
                "keys_count": key_count,
                "hits": self._stats.hits,
                "misses": self._stats.misses,
                "errors": self._stats.errors,
                "hit_rate": self._stats.hit_rate,
                "prefix": self._config.prefix,
            }
            
        except Exception as e:
            logger.error(f"Cache stats error: {e}")
            return {"error": str(e)}
    
    async def health_check(self) -> dict:
        """
        Check cache health.
        
        Returns:
            Health status dictionary
        """
        try:
            # Simple ping test
            await self._redis.ping()
            
            stats = await self.get_stats()
            
            return {
                "status": "healthy",
                "connected": True,
                **stats,
            }
            
        except Exception as e:
            return {
                "status": "unhealthy",
                "connected": False,
                "error": str(e),
            }


# ============================================================================
# Cached Client Decorators
# ============================================================================

def cached(
    api: str,
    operation: str,
    ttl: Optional[int] = None,
    key_params: Optional[list[str]] = None,
):
    """
    Decorator to add caching to API client methods.
    
    Args:
        api: API name for cache key
        operation: Operation name for cache key
        ttl: Optional custom TTL
        key_params: Parameter names to include in cache key
        
    Example:
        >>> class CachedCoinGeckoClient(CoinGeckoClient):
        ...     def __init__(self, api_key, cache: ExternalAPICache):
        ...         super().__init__(api_key)
        ...         self._cache = cache
        ...     
        ...     @cached("coingecko", "price", key_params=["coin_id"])
        ...     async def get_price(self, coin_id: str) -> Price:
        ...         return await super().get_price(coin_id)
    """
    def decorator(func):
        async def wrapper(self, *args, **kwargs):
            # Get cache from self (client must have _cache attribute)
            cache: Optional[ExternalAPICache] = getattr(self, "_cache", None)
            
            if not cache:
                # No cache, just call the function
                return await func(self, *args, **kwargs)
            
            # Build cache key params
            cache_params = {}
            if key_params:
                # Get params from kwargs or positional args
                func_params = func.__code__.co_varnames[1:]  # Skip 'self'
                for i, param_name in enumerate(func_params):
                    if param_name in key_params:
                        if param_name in kwargs:
                            cache_params[param_name] = kwargs[param_name]
                        elif i < len(args):
                            cache_params[param_name] = args[i]
            
            # Try cache first
            cached_data = await cache.get(api, operation, **cache_params)
            if cached_data is not None:
                return cached_data
            
            # Call function
            result = await func(self, *args, **kwargs)
            
            # Cache result (convert dataclass to dict if needed)
            cache_data = result
            if hasattr(result, "__dataclass_fields__"):
                from dataclasses import asdict
                cache_data = asdict(result)
            elif isinstance(result, list) and result and hasattr(result[0], "__dataclass_fields__"):
                from dataclasses import asdict
                cache_data = [asdict(item) for item in result]
            
            await cache.set(api, operation, cache_data, ttl=ttl, **cache_params)
            
            return result
        
        return wrapper
    return decorator
