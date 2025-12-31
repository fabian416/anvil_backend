"""
Admin API endpoints for request distillation validation system.
"""
from datetime import datetime, timedelta
from typing import List, Optional
from fastapi import APIRouter, Query, Security, status
from dishka.integrations.fastapi import FromDishka, inject

from app.presentation.http.auth.fastapi_openapi_markers import bearer_scheme
from app.presentation.http.schemas.distillation import (
    DistillationMetricsResponse,
    ProviderStatusResponse,
    DistillationConfigResponse,
    DistillationConfigUpdateRequest,
    DistillationHealthResponse,
)
from app.application.distillation.get_metrics import GetDistillationMetrics
from app.application.distillation.get_provider_status import GetProviderStatus
from app.application.distillation.update_config import UpdateDistillationConfig
from app.application.distillation.get_health import GetDistillationHealth


router = APIRouter(
    prefix="/admin/distillation/validation",
    tags=["Admin - Distillation Validation"],
)


@router.get(
    "/metrics",
    response_model=List[DistillationMetricsResponse],
    status_code=status.HTTP_200_OK,
    dependencies=[Security(bearer_scheme)],
)
@inject
async def get_distillation_metrics(
    interactor: FromDishka[GetDistillationMetrics],
    days: int = Query(7, ge=1, le=90, description="Number of days to retrieve"),
    provider: Optional[str] = Query(None, description="Filter by provider"),
) -> List[DistillationMetricsResponse]:
    """
    Get distillation metrics.
    
    Returns aggregated daily metrics for distillation validation including:
    - Request counts (total, successful, failed)
    - Success rates
    - Latency statistics (avg, P95)
    - Cost analysis
    - Provider performance
    
    Requires admin authentication.
    """
    metrics = await interactor.execute(days=days, provider=provider)
    
    return [
        DistillationMetricsResponse(
            date=m.date,
            provider=m.provider,
            total_requests=m.total_requests,
            successful_requests=m.successful_requests,
            failed_requests=m.failed_requests,
            success_rate=m.success_rate,
            avg_latency_ms=m.avg_latency_ms,
            p95_latency_ms=m.p95_latency_ms,
            avg_confidence=m.avg_confidence,
            total_tokens=m.total_tokens,
            total_cost_usd=m.total_cost_usd,
            fallback_used_count=m.fallback_used_count,
        )
        for m in metrics
    ]


@router.get(
    "/providers",
    response_model=List[ProviderStatusResponse],
    status_code=status.HTTP_200_OK,
    dependencies=[Security(bearer_scheme)],
)
@inject
async def get_provider_status(
    interactor: FromDishka[GetProviderStatus],
) -> List[ProviderStatusResponse]:
    """
    Get provider health status.
    
    Returns current health status for all distillation providers:
    - Vertex AI (primary)
    - DeepInfra (fallback)
    
    Includes recent latency and error rates.
    
    Requires admin authentication.
    """
    providers = await interactor.execute()
    
    return [
        ProviderStatusResponse(
            provider=p.provider,
            healthy=p.healthy,
            latency_ms=p.latency_ms,
            error_rate=p.error_rate,
            last_check=p.last_check,
        )
        for p in providers
    ]


@router.get(
    "/config",
    response_model=DistillationConfigResponse,
    status_code=status.HTTP_200_OK,
    dependencies=[Security(bearer_scheme)],
)
@inject
async def get_distillation_config(
    interactor: FromDishka[GetProviderStatus],
) -> DistillationConfigResponse:
    """
    Get current distillation configuration.
    
    Returns system-wide configuration including:
    - Enabled/disabled status
    - Provider selection (primary/fallback)
    - LLM parameters (temperature, max_tokens)
    - Timeout settings
    - Fail-open mode
    
    Requires admin authentication.
    """
    # Get config from settings
    from app.setup.config.distillation import DistillationSettings
    from dishka import FromDishka
    
    # This would come from DI container
    # For now, return hardcoded response
    # In production, inject settings via Dishka
    
    return DistillationConfigResponse(
        enabled=True,  # From settings
        provider="vertex_ai",
        fallback_provider="deepinfra",
        temperature=0.3,
        max_tokens=200,
        timeout_seconds=5.0,
        fail_open=True,
    )


@router.patch(
    "/config",
    response_model=DistillationConfigResponse,
    status_code=status.HTTP_200_OK,
    dependencies=[Security(bearer_scheme)],
)
@inject
async def update_distillation_config(
    request: DistillationConfigUpdateRequest,
    interactor: FromDishka[UpdateDistillationConfig],
) -> DistillationConfigResponse:
    """
    Update distillation configuration.
    
    Allows updating system-wide distillation settings:
    - Enable/disable distillation
    - Change provider selection
    - Adjust LLM parameters
    - Modify timeout settings
    - Toggle fail-open mode
    
    Changes take effect immediately.
    
    Requires admin authentication.
    """
    config = await interactor.execute(
        enabled=request.enabled,
        provider=request.provider,
        fallback_provider=request.fallback_provider,
        temperature=request.temperature,
        max_tokens=request.max_tokens,
        timeout_seconds=request.timeout_seconds,
        fail_open=request.fail_open,
    )
    
    return DistillationConfigResponse(
        enabled=config.enabled,
        provider=config.provider,
        fallback_provider=config.fallback_provider,
        temperature=config.temperature,
        max_tokens=config.max_tokens,
        timeout_seconds=config.timeout_seconds,
        fail_open=config.fail_open,
    )


@router.get(
    "/health",
    response_model=DistillationHealthResponse,
    status_code=status.HTTP_200_OK,
    dependencies=[Security(bearer_scheme)],
)
@inject
async def get_distillation_health(
    interactor: FromDishka[GetDistillationHealth],
) -> DistillationHealthResponse:
    """
    Get overall distillation system health.
    
    Returns comprehensive health status:
    - Overall system health
    - Primary provider status (Vertex AI)
    - Fallback provider status (DeepInfra)
    - Telemetry system status
    
    Used for monitoring and alerting.
    
    Requires admin authentication.
    """
    health = await interactor.execute()
    
    return DistillationHealthResponse(
        healthy=health.healthy,
        primary_provider=ProviderStatusResponse(
            provider=health.primary_provider.provider,
            healthy=health.primary_provider.healthy,
            latency_ms=health.primary_provider.latency_ms,
            error_rate=health.primary_provider.error_rate,
            last_check=health.primary_provider.last_check,
        ),
        fallback_provider=ProviderStatusResponse(
            provider=health.fallback_provider.provider,
            healthy=health.fallback_provider.healthy,
            latency_ms=health.fallback_provider.latency_ms,
            error_rate=health.fallback_provider.error_rate,
            last_check=health.fallback_provider.last_check,
        ),
        telemetry_enabled=health.telemetry_enabled,
    )
