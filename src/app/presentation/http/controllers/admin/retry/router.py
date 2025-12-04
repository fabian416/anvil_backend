"""
Admin Retry System API Router.

Provides endpoints for monitoring and controlling the retry system.
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from fastapi.responses import JSONResponse
from dishka import FromDishka
from dishka.integrations.fastapi import inject

from app.presentation.http.controllers.admin.retry.schemas import (
    ServiceStatusResponse,
    ServiceListResponse,
    DisableServiceRequest,
    EnableServiceRequest,
    CircuitBreakerStatusResponse,
    ResetCircuitBreakerRequest,
    ServiceMetricsResponse,
)
from app.application.admin.retry.get_service_list import GetServiceList
from app.application.admin.retry.get_service_status import GetServiceStatus
from app.application.admin.retry.disable_service import DisableService
from app.application.admin.retry.enable_service import EnableService
from app.application.admin.retry.get_circuit_status import GetCircuitStatus
from app.application.admin.retry.reset_circuit_breaker import ResetCircuitBreaker
from app.application.admin.retry.get_service_metrics import GetServiceMetrics

router = APIRouter(
    prefix="/api/v1/admin/retry",
    tags=["Admin - Retry System"],
)


@router.get(
    "/services",
    response_model=ServiceListResponse,
    status_code=status.HTTP_200_OK,
    summary="List all services with retry status",
    description="Get comprehensive status of all services in the retry system",
)
@inject
async def list_services(
    interactor: FromDishka[GetServiceList],
) -> ServiceListResponse:
    """List all services with their retry status."""
    result = await interactor.execute()
    return ServiceListResponse(services=result)


@router.get(
    "/services/{service_name}",
    response_model=ServiceStatusResponse,
    status_code=status.HTTP_200_OK,
    summary="Get service status",
    description="Get detailed status for a specific service",
)
@inject
async def get_service_status(
    service_name: str,
    interactor: FromDishka[GetServiceStatus],
) -> ServiceStatusResponse:
    """Get detailed status for a specific service."""
    result = await interactor.execute(service_name)
    return ServiceStatusResponse(**result)


@router.post(
    "/services/{service_name}/disable",
    status_code=status.HTTP_200_OK,
    summary="Disable service",
    description="Manually disable a service (stops all retry attempts)",
)
@inject
async def disable_service(
    service_name: str,
    request: DisableServiceRequest,
    interactor: FromDishka[DisableService],
) -> JSONResponse:
    """Disable a service manually."""
    await interactor.execute(
        service_name=service_name,
        reason=request.reason,
        duration_minutes=request.duration_minutes,
    )
    return JSONResponse(
        content={
            "message": f"Service '{service_name}' disabled",
            "reason": request.reason,
            "duration_minutes": request.duration_minutes,
        }
    )


@router.post(
    "/services/{service_name}/enable",
    status_code=status.HTTP_200_OK,
    summary="Enable service",
    description="Manually enable a previously disabled service",
)
@inject
async def enable_service(
    service_name: str,
    request: EnableServiceRequest,
    interactor: FromDishka[EnableService],
) -> JSONResponse:
    """Enable a service manually."""
    await interactor.execute(
        service_name=service_name,
        reason=request.reason,
    )
    return JSONResponse(
        content={
            "message": f"Service '{service_name}' enabled",
            "reason": request.reason,
        }
    )


@router.get(
    "/circuit-breakers",
    response_model=List[CircuitBreakerStatusResponse],
    status_code=status.HTTP_200_OK,
    summary="Get circuit breaker statuses",
    description="Get circuit breaker status for all services",
)
@inject
async def get_circuit_breakers(
    interactor: FromDishka[GetCircuitStatus],
) -> List[CircuitBreakerStatusResponse]:
    """Get circuit breaker status for all services."""
    result = await interactor.execute()
    return [CircuitBreakerStatusResponse(**item) for item in result]


@router.post(
    "/circuit-breakers/{service_name}/reset",
    status_code=status.HTTP_200_OK,
    summary="Reset circuit breaker",
    description="Manually reset a circuit breaker to CLOSED state",
)
@inject
async def reset_circuit_breaker(
    service_name: str,
    request: ResetCircuitBreakerRequest,
    interactor: FromDishka[ResetCircuitBreaker],
) -> JSONResponse:
    """Reset a circuit breaker manually."""
    await interactor.execute(
        service_name=service_name,
        reason=request.reason,
    )
    return JSONResponse(
        content={
            "message": f"Circuit breaker for '{service_name}' reset to CLOSED",
            "reason": request.reason,
        }
    )


@router.get(
    "/metrics/{service_name}",
    response_model=ServiceMetricsResponse,
    status_code=status.HTTP_200_OK,
    summary="Get service metrics",
    description="Get aggregated metrics for a service over time",
)
@inject
async def get_service_metrics(
    service_name: str,
    days: int = Query(7, ge=1, le=90, description="Number of days to retrieve"),
    interactor: FromDishka[GetServiceMetrics],
) -> ServiceMetricsResponse:
    """Get aggregated metrics for a service."""
    result = await interactor.execute(service_name, days)
    return ServiceMetricsResponse(**result)
