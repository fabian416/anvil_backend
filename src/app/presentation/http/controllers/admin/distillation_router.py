"""Admin API endpoints for distillation management."""
from typing import List, Optional, Dict, Any
from uuid import UUID

from fastapi import APIRouter, Query, status
from dishka.integrations.fastapi import FromDishka, inject

from app.presentation.http.schemas.distillation import (
    StaticResponseCreate,
    StaticResponseUpdate,
    StaticResponseResponse,
    DistillationConfigResponse,
    DistillationConfigUpdate,
    CacheInvalidateRequest,
    CacheStatsResponse,
    DistillationTelemetryResponse,
    DistillationSummaryResponse,
)
from app.infrastructure.persistence_sqla.repositories.distillation_static_repository import (
    DistillationStaticRepositorySqla,
)
from app.infrastructure.persistence_sqla.repositories.distillation_config_repository import (
    DistillationConfigRepositorySqla,
)
from app.infrastructure.persistence_sqla.repositories.distillation_cache_repository import (
    DistillationCacheRepositorySqla,
)
from app.infrastructure.persistence_sqla.repositories.distillation_telemetry_repository import (
    DistillationTelemetryRepositorySqla,
)
from app.domain.value_objects.distillation import Intent


router = APIRouter(prefix="/admin/distillation", tags=["Admin - Distillation"])


# ==================== Static Responses ====================

@router.post(
    "/static-responses",
    response_model=StaticResponseResponse,
    status_code=status.HTTP_201_CREATED,
)
@inject
async def create_static_response(
    data: StaticResponseCreate,
    repository: FromDishka[DistillationStaticRepositorySqla],
) -> StaticResponseResponse:
    """Create a new static response template."""
    from app.domain.entities.distillation import StaticResponse
    from uuid import uuid4
    from datetime import datetime
    
    static_response = StaticResponse(
        id=uuid4(),
        intent=Intent(data.intent),
        variant=data.variant,
        response_template=data.response_template,
        template_variables=data.template_variables,
        data_source=data.data_source,
        conditions=data.conditions,
        priority=data.priority,
        is_active=data.is_active,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    
    await repository.add_response(static_response)
    
    return StaticResponseResponse(
        id=static_response.id,
        intent=static_response.intent.value,
        variant=static_response.variant,
        response_template=static_response.response_template,
        template_variables=static_response.template_variables,
        data_source=static_response.data_source,
        conditions=static_response.conditions,
        priority=static_response.priority,
        is_active=static_response.is_active,
        created_at=static_response.created_at,
        updated_at=static_response.updated_at,
    )


@router.get(
    "/static-responses",
    response_model=List[StaticResponseResponse],
)
@inject
async def list_static_responses(
    intent: Optional[str] = Query(None),
    is_active: Optional[bool] = Query(None),
    repository: FromDishka[DistillationStaticRepositorySqla] = None,
) -> List[StaticResponseResponse]:
    """List all static response templates."""
    responses = await repository.list_responses(
        intent=Intent(intent) if intent else None,
        is_active=is_active,
    )
    
    return [
        StaticResponseResponse(
            id=r.id,
            intent=r.intent.value,
            variant=r.variant,
            response_template=r.response_template,
            template_variables=r.template_variables,
            data_source=r.data_source,
            conditions=r.conditions,
            priority=r.priority,
            is_active=r.is_active,
            created_at=r.created_at,
            updated_at=r.updated_at,
        )
        for r in responses
    ]


@router.patch(
    "/static-responses/{response_id}",
    response_model=StaticResponseResponse,
)
@inject
async def update_static_response(
    response_id: UUID,
    data: StaticResponseUpdate,
    repository: FromDishka[DistillationStaticRepositorySqla] = None,
) -> StaticResponseResponse:
    """Update a static response template."""
    response = await repository.get_response_by_id(response_id)
    if not response:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Static response not found")
    
    if data.response_template is not None:
        response.response_template = data.response_template
    if data.is_active is not None:
        response.is_active = data.is_active
    
    await repository.update_response(response)
    
    return StaticResponseResponse(
        id=response.id,
        intent=response.intent.value,
        variant=response.variant,
        response_template=response.response_template,
        template_variables=response.template_variables,
        data_source=response.data_source,
        conditions=response.conditions,
        priority=response.priority,
        is_active=response.is_active,
        created_at=response.created_at,
        updated_at=response.updated_at,
    )


@router.delete(
    "/static-responses/{response_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
@inject
async def delete_static_response(
    response_id: UUID,
    repository: FromDishka[DistillationStaticRepositorySqla] = None,
):
    """Delete a static response template."""
    await repository.delete_response(response_id)


# ==================== Configuration ====================

@router.get(
    "/config",
    response_model=DistillationConfigResponse,
)
@inject
async def get_distillation_config(
    repository: FromDishka[DistillationConfigRepositorySqla] = None,
) -> DistillationConfigResponse:
    """Get current distillation configuration."""
    config = await repository.get_config()
    
    return DistillationConfigResponse(
        enabled=config.enabled,
        cache_enabled=config.cache_enabled,
        static_responses_enabled=config.static_responses_enabled,
        semantic_cache_enabled=config.semantic_cache_enabled,
        min_confidence_threshold=config.min_confidence_threshold,
        semantic_similarity_threshold=config.semantic_similarity_threshold,
        max_classification_latency_ms=config.max_classification_latency_ms,
    )


@router.patch(
    "/config",
    response_model=DistillationConfigResponse,
)
@inject
async def update_distillation_config(
    data: DistillationConfigUpdate,
    repository: FromDishka[DistillationConfigRepositorySqla] = None,
) -> DistillationConfigResponse:
    """Update distillation configuration."""
    config = await repository.get_config()
    
    if data.enabled is not None:
        config.enabled = data.enabled
    if data.cache_enabled is not None:
        config.cache_enabled = data.cache_enabled
    if data.static_responses_enabled is not None:
        config.static_responses_enabled = data.static_responses_enabled
    if data.semantic_cache_enabled is not None:
        config.semantic_cache_enabled = data.semantic_cache_enabled
    if data.min_confidence_threshold is not None:
        config.min_confidence_threshold = data.min_confidence_threshold
    if data.semantic_similarity_threshold is not None:
        config.semantic_similarity_threshold = data.semantic_similarity_threshold
    if data.max_classification_latency_ms is not None:
        config.max_classification_latency_ms = data.max_classification_latency_ms
    
    await repository.update_config(config)
    
    return DistillationConfigResponse(
        enabled=config.enabled,
        cache_enabled=config.cache_enabled,
        static_responses_enabled=config.static_responses_enabled,
        semantic_cache_enabled=config.semantic_cache_enabled,
        min_confidence_threshold=config.min_confidence_threshold,
        semantic_similarity_threshold=config.semantic_similarity_threshold,
        max_classification_latency_ms=config.max_classification_latency_ms,
    )


# ==================== Cache Management ====================

@router.post(
    "/cache/invalidate",
    status_code=status.HTTP_204_NO_CONTENT,
)
@inject
async def invalidate_cache(
    data: CacheInvalidateRequest,
    repository: FromDishka[DistillationCacheRepositorySqla] = None,
):
    """Invalidate cache entries."""
    if data.cache_type == "exact":
        await repository.invalidate_exact_cache(data.filters or {})
    elif data.cache_type == "semantic":
        await repository.invalidate_semantic_cache(data.filters or {})
    elif data.cache_type == "all":
        await repository.invalidate_exact_cache(data.filters or {})
        await repository.invalidate_semantic_cache(data.filters or {})


@router.get(
    "/cache/stats",
    response_model=CacheStatsResponse,
)
@inject
async def get_cache_stats(
    repository: FromDishka[DistillationCacheRepositorySqla] = None,
) -> CacheStatsResponse:
    """Get cache statistics."""
    exact_stats = await repository.get_exact_cache_stats()
    semantic_stats = await repository.get_semantic_cache_stats()
    
    return CacheStatsResponse(
        exact_cache=exact_stats,
        semantic_cache=semantic_stats,
    )


# ==================== Telemetry ====================

@router.get(
    "/telemetry/requests",
    response_model=List[DistillationTelemetryResponse],
)
@inject
async def get_telemetry_requests(
    user_id: Optional[UUID] = Query(None),
    intent: Optional[str] = Query(None),
    route_type: Optional[str] = Query(None),
    limit: int = Query(100, le=1000),
    repository: FromDishka[DistillationTelemetryRepositorySqla] = None,
) -> List[DistillationTelemetryResponse]:
    """Get distillation telemetry requests."""
    requests = await repository.get_requests(
        user_id=user_id,
        intent=intent,
        route_type=route_type,
        limit=limit,
    )
    
    return [
        DistillationTelemetryResponse(
            request_id=str(r.request_id),
            user_id=r.user_id,
            original_query=r.original_query,
            intent=r.intent,
            complexity=r.complexity,
            route_type=r.route_type,
            cache_hit=r.cache_hit,
            cache_level=r.cache_level or "",
            classification_latency_ms=r.classification_latency_ms,
            created_at=r.created_at,
        )
        for r in requests
    ]


@router.get(
    "/telemetry/summary",
    response_model=List[DistillationSummaryResponse],
)
@inject
async def get_telemetry_summary(
    hours: int = Query(24, le=168),
    repository: FromDishka[DistillationTelemetryRepositorySqla] = None,
) -> List[DistillationSummaryResponse]:
    """Get hourly distillation telemetry summary."""
    summary = await repository.get_hourly_summary(hours=hours)
    
    return [
        DistillationSummaryResponse(
            hour=s.hour,
            total_requests=s.total_requests,
            cache_hits=s.cache_hits,
            static_responses=s.static_responses,
            light_llm=s.light_llm,
            full_llm=s.full_llm,
            rejected=s.rejected,
            avg_classification_ms=s.avg_classification_ms,
            avg_confidence=s.avg_confidence,
        )
        for s in summary
    ]
