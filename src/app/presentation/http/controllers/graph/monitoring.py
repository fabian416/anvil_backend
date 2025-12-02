"""
Graph Monitoring Controllers

Performance monitoring and metrics for GraphRAG.
"""

from typing import Annotated
from fastapi import APIRouter, Security, status
from dishka.integrations.fastapi import FromDishka
from pydantic import BaseModel

from app.presentation.http.auth.fastapi_openapi_markers import bearer_scheme
from app.infrastructure.cache.graph_cache import GraphQueryCache


router = APIRouter(prefix="/graph/monitoring", tags=["Graph Monitoring"])


class CacheStats(BaseModel):
    """Cache statistics"""
    graph_cache_keys: int
    total_keys: int
    hits: int
    misses: int
    hit_rate: float


class PerformanceMetrics(BaseModel):
    """Performance metrics"""
    cache_stats: CacheStats
    message: str


@router.get(
    "/cache-stats",
    response_model=PerformanceMetrics,
    status_code=status.HTTP_200_OK,
    summary="Get cache statistics",
    description="Get performance metrics for graph query caching",
)
async def get_cache_stats(
    authorization: Annotated[str, Security(bearer_scheme)],
    cache: FromDishka[GraphQueryCache],
) -> PerformanceMetrics:
    """
    Get cache performance statistics.
    
    Returns:
    - Number of cached graph queries
    - Cache hit/miss rates
    - Total Redis keys
    
    Use this to monitor cache effectiveness.
    """
    
    stats = await cache.get_stats()
    
    return PerformanceMetrics(
        cache_stats=CacheStats(**stats),
        message=f"Cache hit rate: {stats.get('hit_rate', 0):.1%}",
    )


@router.post(
    "/cache/clear",
    status_code=status.HTTP_200_OK,
    summary="Clear graph cache",
    description="Clear all cached graph queries (admin only)",
)
async def clear_cache(
    authorization: Annotated[str, Security(bearer_scheme)],
    cache: FromDishka[GraphQueryCache],
) -> dict:
    """
    Clear all graph caches.
    
    Use this after:
    - Data updates
    - Schema changes
    - Testing
    
    Note: This may temporarily increase query latency.
    """
    
    await cache.clear_all()
    
    return {
        "message": "Graph cache cleared successfully",
        "status": "ok",
    }
