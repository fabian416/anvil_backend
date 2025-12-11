"""
Cached External API Clients.

These clients wrap the base API clients with Redis caching
to reduce API calls and improve response times.
"""

from app.infrastructure.adapters.external.cached.cached_coingecko_client import (
    CachedCoinGeckoClient,
)
from app.infrastructure.adapters.external.cached.cached_defillama_client import (
    CachedDefiLlamaClient,
)
from app.infrastructure.adapters.external.cached.cached_oneinch_client import (
    CachedOneInchClient,
)

__all__ = [
    "CachedCoinGeckoClient",
    "CachedDefiLlamaClient",
    "CachedOneInchClient",
]
