"""Celery background tasks for distillation system."""
import asyncio
from datetime import datetime, timedelta
from celery import Task
from celery.schedules import crontab

from app.infrastructure.celery.app import celery_app
from app.setup.config.settings import load_settings
from app.setup.ioc.container import create_async_ioc_container
from app.setup.ioc.provider_registry import get_providers


async def _run_task(coro_factory):
    """Helper to run async tasks with DI container."""
    settings = load_settings()
    container = create_async_ioc_container(
        providers=get_providers(),
        settings=settings,
    )
    try:
        async with container() as request_container:
            await coro_factory(request_container)
    finally:
        await container.close()


# ==================== Telemetry Aggregation ====================

@celery_app.task(name="aggregate_distillation_telemetry")
def aggregate_distillation_telemetry():
    """
    Aggregate distillation requests into hourly summaries.
    
    Runs every hour, aggregates the previous hour's data.
    """
    async def runner(container):
        from app.infrastructure.persistence_sqla.repositories.distillation_telemetry_repository import (
            DistillationTelemetryRepositorySqla,
        )
        from sqlalchemy import text
        from sqlalchemy.ext.asyncio import AsyncSession
        
        session = await container.get(AsyncSession)
        
        # Calculate the previous hour window
        now = datetime.utcnow()
        hour_start = now.replace(minute=0, second=0, microsecond=0) - timedelta(hours=1)
        hour_end = now.replace(minute=0, second=0, microsecond=0)
        
        # Aggregate query
        query = text("""
            INSERT INTO distillation_telemetry_hourly (
                hour,
                total_requests,
                cache_hits,
                static_responses,
                light_llm,
                full_llm,
                rejected,
                avg_classification_ms,
                avg_confidence,
                created_at
            )
            SELECT
                date_trunc('hour', created_at) as hour,
                COUNT(*) as total_requests,
                SUM(CASE WHEN cache_hit = true THEN 1 ELSE 0 END) as cache_hits,
                SUM(CASE WHEN route_type = 'STATIC' THEN 1 ELSE 0 END) as static_responses,
                SUM(CASE WHEN route_type = 'LIGHT_LLM' THEN 1 ELSE 0 END) as light_llm,
                SUM(CASE WHEN route_type = 'FULL_LLM' THEN 1 ELSE 0 END) as full_llm,
                SUM(CASE WHEN route_type = 'REJECT' THEN 1 ELSE 0 END) as rejected,
                AVG(classification_latency_ms) as avg_classification_ms,
                AVG(intent_confidence) as avg_confidence,
                NOW() as created_at
            FROM distillation_requests
            WHERE created_at >= :hour_start AND created_at < :hour_end
            GROUP BY date_trunc('hour', created_at)
            ON CONFLICT (hour) DO UPDATE SET
                total_requests = EXCLUDED.total_requests,
                cache_hits = EXCLUDED.cache_hits,
                static_responses = EXCLUDED.static_responses,
                light_llm = EXCLUDED.light_llm,
                full_llm = EXCLUDED.full_llm,
                rejected = EXCLUDED.rejected,
                avg_classification_ms = EXCLUDED.avg_classification_ms,
                avg_confidence = EXCLUDED.avg_confidence
        """)
        
        await session.execute(query, {"hour_start": hour_start, "hour_end": hour_end})
        await session.commit()
        
        print(f"[Telemetry] Aggregated distillation data for hour: {hour_start}")
    
    asyncio.run(_run_task(runner))


# ==================== Cache Cleanup ====================

@celery_app.task(name="cleanup_expired_cache")
def cleanup_expired_cache():
    """
    Clean up expired cache entries.
    
    Runs daily at 3 AM, removes cache entries that have expired.
    """
    async def runner(container):
        from app.infrastructure.persistence_sqla.repositories.distillation_cache_repository import (
            DistillationCacheRepositorySqla,
        )
        from sqlalchemy import text
        from sqlalchemy.ext.asyncio import AsyncSession
        
        session = await container.get(AsyncSession)
        
        # Delete expired exact cache
        exact_query = text("""
            DELETE FROM distillation_cache_exact
            WHERE expires_at < NOW()
        """)
        exact_result = await session.execute(exact_query)
        exact_deleted = exact_result.rowcount
        
        # Delete expired semantic cache
        semantic_query = text("""
            DELETE FROM distillation_cache_semantic
            WHERE expires_at < NOW()
        """)
        semantic_result = await session.execute(semantic_query)
        semantic_deleted = semantic_result.rowcount
        
        await session.commit()
        
        print(f"[Cache Cleanup] Deleted {exact_deleted} exact cache entries")
        print(f"[Cache Cleanup] Deleted {semantic_deleted} semantic cache entries")
    
    asyncio.run(_run_task(runner))


# ==================== LLM Cache Population ====================

@celery_app.task(name="cache_llm_response")
def cache_llm_response(
    query: str,
    query_hash: str,
    response: str,
    intent: str,
    entities: dict,
    source_model: str,
):
    """
    Cache LLM response after generation (called from distillation engine).
    
    This is a background task to avoid blocking the response.
    """
    async def runner(container):
        from app.infrastructure.persistence_sqla.repositories.distillation_cache_repository import (
            DistillationCacheRepositorySqla,
        )
        from app.domain.value_objects.distillation import CachedResponse
        from uuid import uuid4
        from datetime import timedelta
        
        cache_repo = await container.get(DistillationCacheRepositorySqla)
        
        # Create cached response
        cached = CachedResponse(
            id=uuid4(),
            query=query,
            query_hash=query_hash,
            response_content=response,
            intent=intent,
            entities=entities,
            source_model=source_model,
            hit_count=0,
            created_at=datetime.utcnow(),
            expires_at=datetime.utcnow() + timedelta(hours=24),  # 24 hour TTL
        )
        
        # Store in exact cache
        await cache_repo.set_exact(query_hash, cached)
        
        print(f"[Cache] Cached response for query: {query[:50]}...")
    
    asyncio.run(_run_task(runner))


# ==================== Register Periodic Tasks ====================

celery_app.conf.beat_schedule = {
    # Aggregate telemetry every hour
    "aggregate-distillation-telemetry": {
        "task": "aggregate_distillation_telemetry",
        "schedule": crontab(minute=5),  # Run at :05 of every hour
    },
    
    # Clean up expired cache daily at 3 AM
    "cleanup-expired-cache": {
        "task": "cleanup_expired_cache",
        "schedule": crontab(hour=3, minute=0),
    },
}
