"""
Monitoring HTTP Endpoints.

Exposes:
- /metrics - Prometheus metrics endpoint
- /health - Comprehensive health check
- /alerts - Alert status and history
"""

import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Query, Response, status
from pydantic import BaseModel, Field

from app.infrastructure.monitoring.alerting import AlertSeverity, get_alert_manager
from app.infrastructure.monitoring.health_checks import HealthStatus, get_health_service
from app.infrastructure.monitoring.metrics_collector import get_metrics_collector

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/monitoring", tags=["monitoring"])


# Response Models
class HealthCheckResponse(BaseModel):
    """Health check response."""

    status: str = Field(..., description="Overall health status")
    timestamp: str = Field(..., description="Check timestamp")
    components: Dict[str, Any] = Field(..., description="Component health details")
    healthy_count: int = Field(..., description="Number of healthy components")
    degraded_count: int = Field(..., description="Number of degraded components")
    unhealthy_count: int = Field(..., description="Number of unhealthy components")


class ComponentHealthResponse(BaseModel):
    """Individual component health response."""

    component: str
    status: str
    message: str
    latency_ms: Optional[float] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    checked_at: str


class AlertResponse(BaseModel):
    """Alert response."""

    id: str
    rule_name: str
    severity: str
    condition: str
    message: str
    context: Dict[str, Any]
    timestamp: str
    resolved: bool
    resolved_at: Optional[str] = None


class MetricsSummaryResponse(BaseModel):
    """Metrics summary response."""

    total_requests: int
    total_errors: int
    error_rate: float
    cache_hit_rate: float
    total_cost_usd: float
    response_time_p50: Optional[float] = None
    response_time_p95: Optional[float] = None
    response_time_p99: Optional[float] = None


class AgentMetricsResponse(BaseModel):
    """Agent-specific metrics response."""

    agent_name: str
    total_requests: int
    total_cost_usd: float
    total_tokens: int
    error_rate: float
    cache_hit_rate: float
    response_times: Dict[str, Optional[float]]
    available: bool


# Endpoints
@router.get(
    "/metrics",
    response_class=Response,
    status_code=status.HTTP_200_OK,
    summary="Prometheus Metrics",
    description="Export metrics in Prometheus text format",
)
async def get_prometheus_metrics() -> Response:
    """
    Export metrics in Prometheus format.

    Returns metrics compatible with Prometheus scraping:
    - Request counts by agent, endpoint, status
    - Response time histograms
    - Error counts by type
    - Cache hit/miss rates
    - Cost metrics
    - Agent availability
    """
    try:
        collector = get_metrics_collector()
        metrics_text = collector.export_prometheus()

        return Response(
            content=metrics_text,
            media_type="text/plain; version=0.0.4; charset=utf-8",
        )

    except Exception as e:
        logger.error(f"Error exporting Prometheus metrics: {e}", exc_info=True)
        return Response(
            content=f"# Error exporting metrics: {str(e)}\n",
            media_type="text/plain",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@router.get(
    "/health",
    response_model=HealthCheckResponse,
    status_code=status.HTTP_200_OK,
    summary="Comprehensive Health Check",
    description="Check health of all system components",
)
async def get_health_status() -> HealthCheckResponse:
    """
    Get comprehensive health status.

    Checks:
    - Database connectivity and performance
    - Redis availability and latency
    - External API health
    - WebSocket connection pool
    - System resources (CPU, memory)

    Returns HTTP 200 with health details regardless of status.
    Use the 'status' field to determine overall health.
    """
    try:
        service = get_health_service()
        summary = await service.get_health_summary()

        return HealthCheckResponse(**summary)

    except Exception as e:
        logger.error(f"Error checking health: {e}", exc_info=True)
        return HealthCheckResponse(
            status="error",
            timestamp=str(e),
            components={},
            healthy_count=0,
            degraded_count=0,
            unhealthy_count=0,
        )


@router.get(
    "/health/{component}",
    response_model=ComponentHealthResponse,
    status_code=status.HTTP_200_OK,
    summary="Component Health Check",
    description="Check health of specific component",
)
async def get_component_health(component: str) -> ComponentHealthResponse:
    """
    Get health status of specific component.

    Args:
        component: Component name (e.g., 'database', 'redis', 'websocket')

    Returns:
        Component health details
    """
    try:
        service = get_health_service()
        health = await service.check_component(component)

        if not health:
            return ComponentHealthResponse(
                component=component,
                status=HealthStatus.UNKNOWN.value,
                message=f"Component '{component}' not found",
                checked_at="",
            )

        return ComponentHealthResponse(**health.to_dict())

    except Exception as e:
        logger.error(f"Error checking component health: {e}", exc_info=True)
        return ComponentHealthResponse(
            component=component,
            status=HealthStatus.UNHEALTHY.value,
            message=f"Error: {str(e)}",
            checked_at="",
        )


@router.get(
    "/alerts",
    response_model=List[AlertResponse],
    status_code=status.HTTP_200_OK,
    summary="Active Alerts",
    description="Get active (unresolved) alerts",
)
async def get_active_alerts() -> List[AlertResponse]:
    """
    Get all active alerts.

    Returns:
        List of active alerts sorted by severity
    """
    try:
        manager = get_alert_manager()
        alerts = manager.get_active_alerts()

        return [AlertResponse(**alert.to_dict()) for alert in alerts]

    except Exception as e:
        logger.error(f"Error getting active alerts: {e}", exc_info=True)
        return []


@router.get(
    "/alerts/history",
    response_model=List[AlertResponse],
    status_code=status.HTTP_200_OK,
    summary="Alert History",
    description="Get historical alerts",
)
async def get_alert_history(
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of alerts"),
    severity: Optional[str] = Query(None, description="Filter by severity"),
) -> List[AlertResponse]:
    """
    Get alert history.

    Args:
        limit: Maximum number of alerts to return
        severity: Filter by severity (info, warning, error, critical)

    Returns:
        List of historical alerts
    """
    try:
        manager = get_alert_manager()

        # Parse severity filter
        severity_enum = None
        if severity:
            try:
                severity_enum = AlertSeverity(severity.lower())
            except ValueError:
                logger.warning(f"Invalid severity filter: {severity}")

        alerts = manager.get_alert_history(limit=limit, severity=severity_enum)

        return [AlertResponse(**alert.to_dict()) for alert in alerts]

    except Exception as e:
        logger.error(f"Error getting alert history: {e}", exc_info=True)
        return []


@router.post(
    "/alerts/{rule_name}/resolve",
    status_code=status.HTTP_200_OK,
    summary="Resolve Alert",
    description="Mark alert as resolved",
)
async def resolve_alert(rule_name: str) -> Dict[str, Any]:
    """
    Resolve an active alert.

    Args:
        rule_name: Name of alert rule to resolve

    Returns:
        Success status
    """
    try:
        manager = get_alert_manager()
        resolved = manager.resolve_alert(rule_name)

        return {
            "success": resolved,
            "rule_name": rule_name,
            "message": "Alert resolved" if resolved else "Alert not found",
        }

    except Exception as e:
        logger.error(f"Error resolving alert: {e}", exc_info=True)
        return {
            "success": False,
            "rule_name": rule_name,
            "error": str(e),
        }


@router.get(
    "/metrics/summary",
    response_model=MetricsSummaryResponse,
    status_code=status.HTTP_200_OK,
    summary="Metrics Summary",
    description="Get overall metrics summary",
)
async def get_metrics_summary() -> MetricsSummaryResponse:
    """
    Get comprehensive metrics summary.

    Returns:
        Overall system metrics including:
        - Total requests and errors
        - Error rate
        - Cache hit rate
        - Total cost
        - Response time percentiles
    """
    try:
        collector = get_metrics_collector()

        # Get percentiles
        percentiles = collector.get_response_time_percentiles()

        return MetricsSummaryResponse(
            total_requests=0,  # TODO: Calculate from collector
            total_errors=0,
            error_rate=collector.get_error_rate(),
            cache_hit_rate=collector.get_cache_hit_rate(),
            total_cost_usd=collector.get_total_cost(),
            response_time_p50=percentiles.get("p50"),
            response_time_p95=percentiles.get("p95"),
            response_time_p99=percentiles.get("p99"),
        )

    except Exception as e:
        logger.error(f"Error getting metrics summary: {e}", exc_info=True)
        return MetricsSummaryResponse(
            total_requests=0,
            total_errors=0,
            error_rate=0.0,
            cache_hit_rate=0.0,
            total_cost_usd=0.0,
        )


@router.get(
    "/metrics/agent/{agent_name}",
    response_model=AgentMetricsResponse,
    status_code=status.HTTP_200_OK,
    summary="Agent Metrics",
    description="Get metrics for specific agent",
)
async def get_agent_metrics(agent_name: str) -> AgentMetricsResponse:
    """
    Get metrics for specific agent.

    Args:
        agent_name: Agent name

    Returns:
        Agent-specific metrics including:
        - Request count
        - Cost and token usage
        - Error rate
        - Cache efficiency
        - Response times
        - Availability
    """
    try:
        collector = get_metrics_collector()
        metrics = collector.get_agent_metrics(agent_name)

        return AgentMetricsResponse(**metrics)

    except Exception as e:
        logger.error(f"Error getting agent metrics: {e}", exc_info=True)
        return AgentMetricsResponse(
            agent_name=agent_name,
            total_requests=0,
            total_cost_usd=0.0,
            total_tokens=0,
            error_rate=0.0,
            cache_hit_rate=0.0,
            response_times={"p50": None, "p95": None, "p99": None},
            available=False,
        )


# Optional: Metrics export in JSON format
@router.get(
    "/metrics/export",
    status_code=status.HTTP_200_OK,
    summary="Export Metrics (JSON)",
    description="Export all metrics in JSON format",
)
async def export_metrics_json() -> Dict[str, Any]:
    """
    Export metrics in JSON format.

    Returns:
        All metrics in JSON format (alternative to Prometheus format)
    """
    try:
        collector = get_metrics_collector()

        return {
            "timestamp": collector._start_time,
            "uptime_seconds": collector._start_time,
            "error_rate": collector.get_error_rate(),
            "cache_hit_rate": collector.get_cache_hit_rate(),
            "total_cost_usd": collector.get_total_cost(),
            "response_time_percentiles": collector.get_response_time_percentiles(),
        }

    except Exception as e:
        logger.error(f"Error exporting metrics JSON: {e}", exc_info=True)
        return {"error": str(e)}
