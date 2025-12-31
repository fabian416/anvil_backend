"""
Security Dashboard API Router

Provides endpoints for viewing security scan results, vulnerability metrics,
and OWASP tool execution history.

Admin-only endpoints for monitoring security posture.
"""

from pathlib import Path
from typing import Optional

from dishka import FromDishka
from dishka.integrations.fastapi import inject
from fastapi import Depends, HTTPException, Query, Security, status
from fastapi_error_map import ErrorAwareRouter

from app.application.common.exceptions.authorization import AuthorizationError
from app.application.common.services.current_user import CurrentUserService
from app.domain.enums.user_role import UserRole
from app.domain.exceptions.auth import InsufficientPermissionsError
from app.infrastructure.auth.exceptions import AuthenticationError
from app.infrastructure.security.scan_result_aggregator import (
    ScanResultAggregator,
    SecurityScanResult,
    ToolScanResult
)
from app.presentation.http.auth.fastapi_openapi_markers import bearer_scheme
from app.presentation.http.errors.callbacks import log_info
from .security_dashboard_schemas import (
    SecurityScanResultSchema,
    ScanHistorySchema,
    VulnerabilityTrendsSchema,
    SecurityDashboardSummarySchema,
    ScanToolsSchema,
    ToolScanResultSchema,
    VulnerabilitySummarySchema,
    ErrorResponse
)


# Initialize router
router = ErrorAwareRouter(
    prefix="/admin/security",
    tags=["admin", "security"],
)


def get_scan_aggregator() -> ScanResultAggregator:
    """
    Dependency injection for ScanResultAggregator.

    In production, this would use Dishka DI container.
    For now, hardcoded to default reports directory.
    """
    # TODO: Inject via Dishka container with proper configuration
    reports_dir = Path(__file__).parent.parent.parent.parent.parent.parent / "security" / "reports"
    return ScanResultAggregator(reports_dir)


async def _ensure_admin(current_user_service: CurrentUserService) -> None:
    """
    Ensure the current user is an admin.

    Raises:
        AuthenticationError: if unauthenticated
        InsufficientPermissionsError: if authenticated but not admin
    """
    user = await current_user_service.get_current_user()
    if user.role != UserRole.ADMIN:
        raise InsufficientPermissionsError("Admin access required")


def convert_scan_result(result: SecurityScanResult) -> SecurityScanResultSchema:
    """Convert domain model to API schema"""
    return SecurityScanResultSchema(
        scan_id=result.scan_id,
        scan_date=result.scan_date,
        status=result.status.value,
        tools_executed=result.tools_executed,
        vulnerabilities=VulnerabilitySummarySchema(
            critical=result.vulnerabilities.critical,
            high=result.vulnerabilities.high,
            medium=result.vulnerabilities.medium,
            low=result.vulnerabilities.low,
            info=result.vulnerabilities.info,
            total=result.vulnerabilities.total
        ),
        reports_path=result.reports_path,
        duration_seconds=result.duration_seconds,
        errors=result.errors or []
    )


def convert_tool_result(result: ToolScanResult) -> ToolScanResultSchema:
    """Convert tool result domain model to API schema"""
    return ToolScanResultSchema(
        tool_name=result.tool_name,
        scan_date=result.scan_date,
        status=result.status,
        vulnerabilities_found=result.vulnerabilities_found,
        report_path=result.report_path,
        details=result.details
    )


@router.get(
    "/dashboard",
    response_model=SecurityDashboardSummarySchema,
    summary="Get security dashboard summary",
    description="Get overall security dashboard summary including latest scan and active tools",
    status_code=status.HTTP_200_OK,
    dependencies=[Security(bearer_scheme)],
    error_map={
        AuthenticationError: status.HTTP_401_UNAUTHORIZED,
        AuthorizationError: status.HTTP_403_FORBIDDEN,
        InsufficientPermissionsError: status.HTTP_403_FORBIDDEN,
    },
    default_on_error=log_info,
)
@inject
async def get_security_dashboard(
    current_user_service: FromDishka[CurrentUserService],
    aggregator: ScanResultAggregator = Depends(get_scan_aggregator),
) -> SecurityDashboardSummarySchema:
    """
    Get comprehensive security dashboard summary.

    Returns:
        Security dashboard with latest scan, total scans, and overall status
    """
    await _ensure_admin(current_user_service)
    try:
        latest_scan = aggregator.get_latest_scan()
        scan_history = aggregator.get_scan_history(limit=100)

        # Determine overall status
        if latest_scan:
            if latest_scan.vulnerabilities.critical > 0:
                overall_status = "critical"
            elif latest_scan.vulnerabilities.high > 0:
                overall_status = "warning"
            else:
                overall_status = "healthy"
        else:
            overall_status = "unknown"

        # Get unique list of active tools
        active_tools = list(set(
            tool
            for scan in scan_history
            for tool in scan.tools_executed
        )) if scan_history else []

        return SecurityDashboardSummarySchema(
            latest_scan=convert_scan_result(latest_scan) if latest_scan else None,
            total_scans=len(scan_history),
            active_tools=active_tools,
            overall_status=overall_status
        )

    except Exception:
        raise HTTPException(
            status_code=500,
            detail="Error retrieving dashboard summary",
        )


@router.get(
    "/scans/latest",
    response_model=SecurityScanResultSchema,
    summary="Get latest security scan",
    description="Retrieve the most recent security scan results",
    status_code=status.HTTP_200_OK,
    dependencies=[Security(bearer_scheme)],
    error_map={
        AuthenticationError: status.HTTP_401_UNAUTHORIZED,
        AuthorizationError: status.HTTP_403_FORBIDDEN,
        InsufficientPermissionsError: status.HTTP_403_FORBIDDEN,
    },
    default_on_error=log_info,
)
@inject
async def get_latest_scan(
    current_user_service: FromDishka[CurrentUserService],
    aggregator: ScanResultAggregator = Depends(get_scan_aggregator),
) -> SecurityScanResultSchema:
    """
    Get the most recent security scan.

    Returns:
        Latest scan results with vulnerability summary

    Raises:
        404: If no scans are found
    """
    await _ensure_admin(current_user_service)
    latest_scan = aggregator.get_latest_scan()

    if not latest_scan:
        raise HTTPException(
            status_code=404,
            detail="No security scans found"
        )

    return convert_scan_result(latest_scan)


@router.get(
    "/scans/{scan_id}",
    response_model=SecurityScanResultSchema,
    summary="Get specific security scan",
    description="Retrieve security scan results by scan ID",
    status_code=status.HTTP_200_OK,
    dependencies=[Security(bearer_scheme)],
    error_map={
        AuthenticationError: status.HTTP_401_UNAUTHORIZED,
        AuthorizationError: status.HTTP_403_FORBIDDEN,
        InsufficientPermissionsError: status.HTTP_403_FORBIDDEN,
    },
    default_on_error=log_info,
)
@inject
async def get_scan_by_id(
    scan_id: str,
    current_user_service: FromDishka[CurrentUserService],
    aggregator: ScanResultAggregator = Depends(get_scan_aggregator),
) -> SecurityScanResultSchema:
    """
    Get a specific security scan by ID.

    Args:
        scan_id: Unique identifier for the scan (format: YYYYMMDD_HHMMSS)

    Returns:
        Scan results for the specified ID

    Raises:
        404: If scan with the given ID is not found
    """
    await _ensure_admin(current_user_service)
    scan_result = aggregator.get_scan_by_id(scan_id)

    if not scan_result:
        raise HTTPException(
            status_code=404,
            detail=f"Scan not found: {scan_id}"
        )

    return convert_scan_result(scan_result)


@router.get(
    "/scans",
    response_model=ScanHistorySchema,
    summary="Get scan history",
    description="Retrieve historical security scan results with pagination",
    status_code=status.HTTP_200_OK,
    dependencies=[Security(bearer_scheme)],
    error_map={
        AuthenticationError: status.HTTP_401_UNAUTHORIZED,
        AuthorizationError: status.HTTP_403_FORBIDDEN,
        InsufficientPermissionsError: status.HTTP_403_FORBIDDEN,
    },
    default_on_error=log_info,
)
@inject
async def get_scan_history(
    current_user_service: FromDishka[CurrentUserService],
    aggregator: ScanResultAggregator = Depends(get_scan_aggregator),
    limit: int = Query(10, ge=1, le=100, description="Maximum number of scans to return"),
) -> ScanHistorySchema:
    """
    Get historical security scans.

    Args:
        limit: Maximum number of scans to return (1-100)

    Returns:
        List of historical scans with pagination info
    """
    await _ensure_admin(current_user_service)
    scan_history = aggregator.get_scan_history(limit=limit)

    return ScanHistorySchema(
        scans=[convert_scan_result(scan) for scan in scan_history],
        total_scans=len(scan_history)
    )


@router.get(
    "/scans/{scan_id}/tools",
    response_model=ScanToolsSchema,
    summary="Get tool results for a scan",
    description="Retrieve individual tool results for a specific security scan",
    status_code=status.HTTP_200_OK,
    dependencies=[Security(bearer_scheme)],
    error_map={
        AuthenticationError: status.HTTP_401_UNAUTHORIZED,
        AuthorizationError: status.HTTP_403_FORBIDDEN,
        InsufficientPermissionsError: status.HTTP_403_FORBIDDEN,
    },
    default_on_error=log_info,
)
@inject
async def get_scan_tools(
    scan_id: str,
    current_user_service: FromDishka[CurrentUserService],
    aggregator: ScanResultAggregator = Depends(get_scan_aggregator),
) -> ScanToolsSchema:
    """
    Get individual tool results for a scan.

    Args:
        scan_id: Unique identifier for the scan

    Returns:
        Results from each security tool in the scan

    Raises:
        404: If scan with the given ID is not found
    """
    await _ensure_admin(current_user_service)
    tool_results = aggregator.get_tool_results(scan_id)

    if not tool_results:
        # Check if scan exists
        scan = aggregator.get_scan_by_id(scan_id)
        if not scan:
            raise HTTPException(
                status_code=404,
                detail=f"Scan not found: {scan_id}"
            )

        # Scan exists but has no tool results
        return ScanToolsSchema(
            scan_id=scan_id,
            tools=[]
        )

    return ScanToolsSchema(
        scan_id=scan_id,
        tools=[convert_tool_result(tool) for tool in tool_results]
    )


@router.get(
    "/trends",
    response_model=VulnerabilityTrendsSchema,
    summary="Get vulnerability trends",
    description="Retrieve vulnerability count trends over time",
    status_code=status.HTTP_200_OK,
    dependencies=[Security(bearer_scheme)],
    error_map={
        AuthenticationError: status.HTTP_401_UNAUTHORIZED,
        AuthorizationError: status.HTTP_403_FORBIDDEN,
        InsufficientPermissionsError: status.HTTP_403_FORBIDDEN,
    },
    default_on_error=log_info,
)
@inject
async def get_vulnerability_trends(
    current_user_service: FromDishka[CurrentUserService],
    aggregator: ScanResultAggregator = Depends(get_scan_aggregator),
    days: int = Query(30, ge=1, le=90, description="Number of days to include in trends"),
) -> VulnerabilityTrendsSchema:
    """
    Get vulnerability trends over time.

    Args:
        days: Number of days to include (1-90)

    Returns:
        Time-series data of vulnerability counts by severity
    """
    await _ensure_admin(current_user_service)
    trends = aggregator.get_vulnerability_trends(days=days)

    return VulnerabilityTrendsSchema(
        dates=trends.get("dates", []),
        critical=trends.get("critical", []),
        high=trends.get("high", []),
        medium=trends.get("medium", []),
        low=trends.get("low", [])
    )


@router.get(
    "/health",
    summary="Security system health check",
    description="Check if security scanning infrastructure is operational",
    status_code=status.HTTP_200_OK,
    dependencies=[Security(bearer_scheme)],
    error_map={
        AuthenticationError: status.HTTP_401_UNAUTHORIZED,
        AuthorizationError: status.HTTP_403_FORBIDDEN,
        InsufficientPermissionsError: status.HTTP_403_FORBIDDEN,
    },
    default_on_error=log_info,
)
@inject
async def security_health_check(
    current_user_service: FromDishka[CurrentUserService],
    aggregator: ScanResultAggregator = Depends(get_scan_aggregator),
) -> dict:
    """
    Health check for security scanning system.

    Returns:
        Health status and basic metrics
    """
    await _ensure_admin(current_user_service)
    try:
        latest_scan = aggregator.get_latest_scan()

        return {
            "status": "healthy",
            "reports_directory_exists": aggregator.reports_base_dir.exists(),
            "latest_scan_id": latest_scan.scan_id if latest_scan else None,
            "latest_scan_date": latest_scan.scan_date.isoformat() if latest_scan else None
        }

    except Exception:
        return {
            "status": "unhealthy",
            "error": "Error checking security system health",
        }
