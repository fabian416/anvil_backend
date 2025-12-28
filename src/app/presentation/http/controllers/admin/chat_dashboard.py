"""
Admin Chat Dashboard Router

Provides comprehensive analytics and monitoring endpoints for chat feature administration.

Features:
    - Real-time usage statistics
    - Agent performance leaderboards
    - Cache efficiency metrics
    - Cost tracking and analysis
    - Error rate monitoring
    - Active users and conversations
    - Data export capabilities
    - Time-range filtering

Admin-only endpoints for monitoring chat system health and performance.
"""

from datetime import datetime, timedelta
from typing import Optional, List
from uuid import UUID

from fastapi import APIRouter, Query, HTTPException, Depends
from dishka.integrations.fastapi import FromDishka, inject

from app.presentation.http.schemas.admin_chat_dashboard import (
    AdminChatDashboardSummaryResponse,
    AgentPerformanceResponse,
    CacheEfficiencyResponse,
    CostTrackingResponse,
    ErrorMonitoringResponse,
    ActiveUsersResponse,
    ConversationMetricsResponse,
    TimeSeriesDataPoint,
    ExportDataResponse,
    AgentLeaderboardEntry,
    CostBreakdownEntry,
)
from app.application.chat.services.admin_analytics_service import AdminChatAnalyticsService


router = APIRouter(
    prefix="/chat",
    tags=["admin", "chat", "analytics"],
)


@router.get(
    "/dashboard",
    response_model=AdminChatDashboardSummaryResponse,
    summary="Get admin chat dashboard summary",
    description="Get comprehensive overview of chat system performance and usage"
)
@inject
async def get_chat_dashboard(
    date_from: Optional[datetime] = Query(
        None,
        description="Start date for analytics (defaults to 30 days ago)"
    ),
    date_to: Optional[datetime] = Query(
        None,
        description="End date for analytics (defaults to now)"
    ),
    analytics_service: FromDishka[AdminChatAnalyticsService] = None,
) -> AdminChatDashboardSummaryResponse:
    """
    Get comprehensive admin dashboard for chat system.

    Provides high-level overview including:
    - Total conversations and messages
    - Active users count
    - Agent usage distribution
    - Cost summaries
    - Error rates
    - Cache hit rates

    Args:
        date_from: Start date for analytics period
        date_to: End date for analytics period
        analytics_service: Injected analytics service

    Returns:
        Complete dashboard summary with all key metrics
    """
    if not date_to:
        date_to = datetime.utcnow()
    if not date_from:
        date_from = date_to - timedelta(days=30)

    try:
        dashboard_data = await analytics_service.get_dashboard_summary(
            date_from=date_from,
            date_to=date_to
        )
        return dashboard_data
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving dashboard summary: {str(e)}"
        )


@router.get(
    "/dashboard/agents/performance",
    response_model=AgentPerformanceResponse,
    summary="Get agent performance metrics",
    description="Get detailed performance metrics for all agents with leaderboard rankings"
)
@inject
async def get_agent_performance(
    date_from: Optional[datetime] = Query(None, description="Start date"),
    date_to: Optional[datetime] = Query(None, description="End date"),
    agent_type: Optional[str] = Query(None, description="Filter by specific agent type"),
    sort_by: str = Query(
        "invocations",
        pattern="^(invocations|success_rate|avg_response_time|total_cost)$",
        description="Sort leaderboard by metric"
    ),
    limit: int = Query(10, ge=1, le=50, description="Number of agents to return"),
    analytics_service: FromDishka[AdminChatAnalyticsService] = None,
) -> AgentPerformanceResponse:
    """
    Get agent performance leaderboard.

    Includes:
    - Total invocations per agent
    - Success rates
    - Average response times
    - Cost per agent
    - Error counts
    - Performance trends

    Args:
        date_from: Start date for metrics
        date_to: End date for metrics
        agent_type: Optional filter for specific agent
        sort_by: Metric to sort by
        limit: Maximum number of agents to return
        analytics_service: Injected analytics service

    Returns:
        Agent performance metrics with leaderboard rankings
    """
    if not date_to:
        date_to = datetime.utcnow()
    if not date_from:
        date_from = date_to - timedelta(days=30)

    try:
        performance_data = await analytics_service.get_agent_performance(
            date_from=date_from,
            date_to=date_to,
            agent_type=agent_type,
            sort_by=sort_by,
            limit=limit
        )
        return performance_data
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving agent performance: {str(e)}"
        )


@router.get(
    "/dashboard/cache/efficiency",
    response_model=CacheEfficiencyResponse,
    summary="Get cache efficiency metrics",
    description="Monitor cache performance including hit rates and memory usage"
)
@inject
async def get_cache_efficiency(
    date_from: Optional[datetime] = Query(None, description="Start date"),
    date_to: Optional[datetime] = Query(None, description="End date"),
    analytics_service: FromDishka[AdminChatAnalyticsService] = None,
) -> CacheEfficiencyResponse:
    """
    Get cache efficiency metrics.

    Includes:
    - Overall hit rate
    - Miss rate
    - Memory usage
    - Cache size
    - Eviction counts
    - Hit rate by cache type
    - Performance impact

    Args:
        date_from: Start date for metrics
        date_to: End date for metrics
        analytics_service: Injected analytics service

    Returns:
        Cache efficiency metrics and statistics
    """
    if not date_to:
        date_to = datetime.utcnow()
    if not date_from:
        date_from = date_to - timedelta(days=7)

    try:
        cache_data = await analytics_service.get_cache_efficiency(
            date_from=date_from,
            date_to=date_to
        )
        return cache_data
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving cache metrics: {str(e)}"
        )


@router.get(
    "/dashboard/costs",
    response_model=CostTrackingResponse,
    summary="Get cost tracking metrics",
    description="Monitor LLM API costs with breakdowns by agent, model, and time period"
)
@inject
async def get_cost_tracking(
    date_from: Optional[datetime] = Query(None, description="Start date"),
    date_to: Optional[datetime] = Query(None, description="End date"),
    group_by: str = Query(
        "agent",
        pattern="^(agent|model|day|user)$",
        description="Group costs by dimension"
    ),
    analytics_service: FromDishka[AdminChatAnalyticsService] = None,
) -> CostTrackingResponse:
    """
    Get comprehensive cost tracking.

    Includes:
    - Total spend for period
    - Cost per agent
    - Cost per model
    - Daily cost trends
    - Average cost per conversation
    - Token usage statistics
    - Cost projections

    Args:
        date_from: Start date for cost tracking
        date_to: End date for cost tracking
        group_by: Dimension to group costs by
        analytics_service: Injected analytics service

    Returns:
        Detailed cost tracking and analysis
    """
    if not date_to:
        date_to = datetime.utcnow()
    if not date_from:
        date_from = date_to - timedelta(days=30)

    try:
        cost_data = await analytics_service.get_cost_tracking(
            date_from=date_from,
            date_to=date_to,
            group_by=group_by
        )
        return cost_data
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving cost data: {str(e)}"
        )


@router.get(
    "/dashboard/errors",
    response_model=ErrorMonitoringResponse,
    summary="Get error monitoring metrics",
    description="Monitor error rates, types, and trends across the chat system"
)
@inject
async def get_error_monitoring(
    date_from: Optional[datetime] = Query(None, description="Start date"),
    date_to: Optional[datetime] = Query(None, description="End date"),
    severity: Optional[str] = Query(
        None,
        pattern="^(critical|high|medium|low)$",
        description="Filter by error severity"
    ),
    analytics_service: FromDishka[AdminChatAnalyticsService] = None,
) -> ErrorMonitoringResponse:
    """
    Get error monitoring metrics.

    Includes:
    - Total error count
    - Error rate (errors/total requests)
    - Errors by type
    - Errors by agent
    - Error trends over time
    - Most common error messages
    - Resolution status

    Args:
        date_from: Start date for error metrics
        date_to: End date for error metrics
        severity: Optional filter by severity
        analytics_service: Injected analytics service

    Returns:
        Error monitoring metrics and analysis
    """
    if not date_to:
        date_to = datetime.utcnow()
    if not date_from:
        date_from = date_to - timedelta(days=7)

    try:
        error_data = await analytics_service.get_error_monitoring(
            date_from=date_from,
            date_to=date_to,
            severity=severity
        )
        return error_data
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving error metrics: {str(e)}"
        )


@router.get(
    "/dashboard/users/active",
    response_model=ActiveUsersResponse,
    summary="Get active users metrics",
    description="Monitor active users and conversation statistics"
)
@inject
async def get_active_users(
    date_from: Optional[datetime] = Query(None, description="Start date"),
    date_to: Optional[datetime] = Query(None, description="End date"),
    analytics_service: FromDishka[AdminChatAnalyticsService] = None,
) -> ActiveUsersResponse:
    """
    Get active users metrics.

    Includes:
    - Total active users
    - Daily active users (DAU)
    - Weekly active users (WAU)
    - Monthly active users (MAU)
    - New users
    - User retention rates
    - Average sessions per user
    - Average messages per user

    Args:
        date_from: Start date for user metrics
        date_to: End date for user metrics
        analytics_service: Injected analytics service

    Returns:
        Active users metrics and engagement data
    """
    if not date_to:
        date_to = datetime.utcnow()
    if not date_from:
        date_from = date_to - timedelta(days=30)

    try:
        users_data = await analytics_service.get_active_users(
            date_from=date_from,
            date_to=date_to
        )
        return users_data
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving user metrics: {str(e)}"
        )


@router.get(
    "/dashboard/conversations/metrics",
    response_model=ConversationMetricsResponse,
    summary="Get conversation metrics",
    description="Monitor conversation statistics and engagement patterns"
)
@inject
async def get_conversation_metrics(
    date_from: Optional[datetime] = Query(None, description="Start date"),
    date_to: Optional[datetime] = Query(None, description="End date"),
    analytics_service: FromDishka[AdminChatAnalyticsService] = None,
) -> ConversationMetricsResponse:
    """
    Get conversation metrics.

    Includes:
    - Total conversations
    - Total messages
    - Average messages per conversation
    - Average conversation duration
    - Conversation completion rate
    - Peak activity times
    - Conversation topics distribution

    Args:
        date_from: Start date for conversation metrics
        date_to: End date for conversation metrics
        analytics_service: Injected analytics service

    Returns:
        Conversation metrics and engagement patterns
    """
    if not date_to:
        date_to = datetime.utcnow()
    if not date_from:
        date_from = date_to - timedelta(days=30)

    try:
        conversation_data = await analytics_service.get_conversation_metrics(
            date_from=date_from,
            date_to=date_to
        )
        return conversation_data
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving conversation metrics: {str(e)}"
        )


@router.get(
    "/dashboard/export",
    response_model=ExportDataResponse,
    summary="Export dashboard data",
    description="Export analytics data in various formats (JSON, CSV)"
)
@inject
async def export_dashboard_data(
    date_from: Optional[datetime] = Query(None, description="Start date"),
    date_to: Optional[datetime] = Query(None, description="End date"),
    format: str = Query(
        "json",
        pattern="^(json|csv)$",
        description="Export format"
    ),
    include_sections: Optional[List[str]] = Query(
        None,
        description="Sections to include (agents, costs, errors, users, conversations)"
    ),
    analytics_service: FromDishka[AdminChatAnalyticsService] = None,
) -> ExportDataResponse:
    """
    Export dashboard data for external analysis.

    Supports exporting:
    - Agent performance data
    - Cost tracking data
    - Error logs
    - User metrics
    - Conversation data

    Args:
        date_from: Start date for export
        date_to: End date for export
        format: Export format (json or csv)
        include_sections: Specific sections to include
        analytics_service: Injected analytics service

    Returns:
        Exported data in requested format
    """
    if not date_to:
        date_to = datetime.utcnow()
    if not date_from:
        date_from = date_to - timedelta(days=30)

    try:
        export_data = await analytics_service.export_dashboard_data(
            date_from=date_from,
            date_to=date_to,
            export_format=format,
            include_sections=include_sections
        )
        return export_data
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error exporting dashboard data: {str(e)}"
        )
