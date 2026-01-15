"""
User Analytics Dashboard Router

Provides personalized analytics endpoints for individual users to track their chat usage.

Features:
    - Personal usage statistics
    - Conversation insights and patterns
    - Personal cost tracking
    - Favorite agents and success rates
    - Historical trends and charts
    - Conversation history analysis
    - Export capabilities

User-facing endpoints for self-service analytics.
"""

from datetime import datetime, timedelta, UTC
from typing import Optional, List
from uuid import UUID

from fastapi import APIRouter, Query, HTTPException, Depends
from dishka.integrations.fastapi import FromDishka, inject

from app.presentation.http.schemas.user_chat_analytics import (
    UserAnalyticsDashboardResponse,
    PersonalUsageStatsResponse,
    ConversationInsightsResponse,
    PersonalCostBreakdownResponse,
    FavoriteAgentsResponse,
    HistoricalTrendsResponse,
    ConversationHistoryResponse,
    UserExportDataResponse,
    AgentPreferenceEntry,
    TopicDistribution,
    DailyActivityPoint,
)
from app.application.chat.services.user_analytics_service import UserChatAnalyticsService
from app.infrastructure.auth.context import get_current_user_id


router = APIRouter(
    prefix="/user/chat",
    tags=["chat", "analytics", "user"],
)


@router.get(
    "/my-analytics",
    response_model=UserAnalyticsDashboardResponse,
    summary="Get my chat analytics dashboard",
    description="Get personalized analytics overview for your chat usage"
)
@inject
async def get_my_analytics(
    date_from: Optional[datetime] = Query(
        None,
        description="Start date for analytics (defaults to 30 days ago)"
    ),
    date_to: Optional[datetime] = Query(
        None,
        description="End date for analytics (defaults to now)"
    ),
    user_id: int = Depends(get_current_user_id),
    analytics_service: FromDishka[UserChatAnalyticsService] = None,
) -> UserAnalyticsDashboardResponse:
    """
    Get personalized chat analytics dashboard.

    Provides overview including:
    - Total conversations and messages
    - Most used agents
    - Personal spending
    - Conversation patterns
    - Success rates
    - Activity trends

    Args:
        date_from: Start date for analytics period
        date_to: End date for analytics period
        user_id: Current authenticated user ID
        analytics_service: Injected analytics service

    Returns:
        Personalized dashboard summary with key metrics
    """
    if not date_to:
        date_to = datetime.now(UTC)
    if not date_from:
        date_from = date_to - timedelta(days=30)

    try:
        dashboard_data = await analytics_service.get_user_dashboard(
            user_id=user_id,
            date_from=date_from,
            date_to=date_to
        )
        return dashboard_data
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving analytics dashboard: {str(e)}"
        )


@router.get(
    "/my-analytics/usage",
    response_model=PersonalUsageStatsResponse,
    summary="Get my usage statistics",
    description="Get detailed personal usage metrics"
)
@inject
async def get_my_usage_stats(
    date_from: Optional[datetime] = Query(None, description="Start date"),
    date_to: Optional[datetime] = Query(None, description="End date"),
    user_id: int = Depends(get_current_user_id),
    analytics_service: FromDishka[UserChatAnalyticsService] = None,
) -> PersonalUsageStatsResponse:
    """
    Get personal usage statistics.

    Includes:
    - Total conversations created
    - Total messages sent
    - Average messages per conversation
    - Most active days/times
    - Conversation completion rate
    - Session duration statistics
    - Engagement metrics

    Args:
        date_from: Start date for metrics
        date_to: End date for metrics
        user_id: Current authenticated user ID
        analytics_service: Injected analytics service

    Returns:
        Personal usage statistics
    """
    if not date_to:
        date_to = datetime.now(UTC)
    if not date_from:
        date_from = date_to - timedelta(days=30)

    try:
        usage_data = await analytics_service.get_usage_stats(
            user_id=user_id,
            date_from=date_from,
            date_to=date_to
        )
        return usage_data
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving usage stats: {str(e)}"
        )


@router.get(
    "/my-analytics/insights",
    response_model=ConversationInsightsResponse,
    summary="Get conversation insights",
    description="Get insights into your conversation patterns and topics"
)
@inject
async def get_conversation_insights(
    date_from: Optional[datetime] = Query(None, description="Start date"),
    date_to: Optional[datetime] = Query(None, description="End date"),
    user_id: int = Depends(get_current_user_id),
    analytics_service: FromDishka[UserChatAnalyticsService] = None,
) -> ConversationInsightsResponse:
    """
    Get conversation insights and patterns.

    Includes:
    - Average conversation length
    - Most discussed topics
    - Topic distribution
    - Conversation sentiment
    - Question types
    - Engagement patterns
    - Time-to-decision metrics

    Args:
        date_from: Start date for insights
        date_to: End date for insights
        user_id: Current authenticated user ID
        analytics_service: Injected analytics service

    Returns:
        Conversation insights and analysis
    """
    if not date_to:
        date_to = datetime.now(UTC)
    if not date_from:
        date_from = date_to - timedelta(days=30)

    try:
        insights_data = await analytics_service.get_conversation_insights(
            user_id=user_id,
            date_from=date_from,
            date_to=date_to
        )
        return insights_data
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving conversation insights: {str(e)}"
        )


@router.get(
    "/my-analytics/costs",
    response_model=PersonalCostBreakdownResponse,
    summary="Get my cost breakdown",
    description="Get detailed breakdown of your personal LLM API spending"
)
@inject
async def get_my_cost_breakdown(
    date_from: Optional[datetime] = Query(None, description="Start date"),
    date_to: Optional[datetime] = Query(None, description="End date"),
    group_by: str = Query(
        "agent",
        pattern="^(agent|model|day|conversation)$",
        description="Group costs by dimension"
    ),
    user_id: int = Depends(get_current_user_id),
    analytics_service: FromDishka[UserChatAnalyticsService] = None,
) -> PersonalCostBreakdownResponse:
    """
    Get personal cost breakdown.

    Includes:
    - Total personal spending
    - Cost per agent used
    - Cost per model
    - Daily cost trends
    - Average cost per conversation
    - Token usage
    - Cost-saving recommendations

    Args:
        date_from: Start date for cost tracking
        date_to: End date for cost tracking
        group_by: Dimension to group costs by
        user_id: Current authenticated user ID
        analytics_service: Injected analytics service

    Returns:
        Personal cost breakdown and analysis
    """
    if not date_to:
        date_to = datetime.now(UTC)
    if not date_from:
        date_from = date_to - timedelta(days=30)

    try:
        cost_data = await analytics_service.get_cost_breakdown(
            user_id=user_id,
            date_from=date_from,
            date_to=date_to,
            group_by=group_by
        )
        return cost_data
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving cost breakdown: {str(e)}"
        )


@router.get(
    "/my-analytics/agents/favorites",
    response_model=FavoriteAgentsResponse,
    summary="Get my favorite agents",
    description="Get statistics on your most-used agents and their performance"
)
@inject
async def get_favorite_agents(
    date_from: Optional[datetime] = Query(None, description="Start date"),
    date_to: Optional[datetime] = Query(None, description="End date"),
    limit: int = Query(10, ge=1, le=50, description="Number of agents to return"),
    user_id: int = Depends(get_current_user_id),
    analytics_service: FromDishka[UserChatAnalyticsService] = None,
) -> FavoriteAgentsResponse:
    """
    Get favorite agents analysis.

    Includes:
    - Most frequently used agents
    - Usage count per agent
    - Success rate per agent
    - Average response time
    - Personal satisfaction ratings (if available)
    - Cost per agent
    - Recommended agents

    Args:
        date_from: Start date for agent stats
        date_to: End date for agent stats
        limit: Maximum number of agents to return
        user_id: Current authenticated user ID
        analytics_service: Injected analytics service

    Returns:
        Favorite agents statistics and recommendations
    """
    if not date_to:
        date_to = datetime.now(UTC)
    if not date_from:
        date_from = date_to - timedelta(days=30)

    try:
        agents_data = await analytics_service.get_favorite_agents(
            user_id=user_id,
            date_from=date_from,
            date_to=date_to,
            limit=limit
        )
        return agents_data
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving favorite agents: {str(e)}"
        )


@router.get(
    "/my-analytics/trends",
    response_model=HistoricalTrendsResponse,
    summary="Get my historical trends",
    description="Get historical activity trends with daily/weekly breakdown"
)
@inject
async def get_historical_trends(
    date_from: Optional[datetime] = Query(None, description="Start date"),
    date_to: Optional[datetime] = Query(None, description="End date"),
    granularity: str = Query(
        "daily",
        pattern="^(hourly|daily|weekly)$",
        description="Time granularity for trends"
    ),
    user_id: int = Depends(get_current_user_id),
    analytics_service: FromDishka[UserChatAnalyticsService] = None,
) -> HistoricalTrendsResponse:
    """
    Get historical activity trends.

    Includes:
    - Daily/weekly conversation count
    - Daily/weekly message count
    - Activity patterns over time
    - Peak usage hours
    - Growth trends
    - Engagement changes
    - Comparative metrics

    Args:
        date_from: Start date for trends
        date_to: End date for trends
        granularity: Time granularity (hourly, daily, weekly)
        user_id: Current authenticated user ID
        analytics_service: Injected analytics service

    Returns:
        Historical trends with time-series data
    """
    if not date_to:
        date_to = datetime.now(UTC)
    if not date_from:
        date_from = date_to - timedelta(days=30)

    try:
        trends_data = await analytics_service.get_historical_trends(
            user_id=user_id,
            date_from=date_from,
            date_to=date_to,
            granularity=granularity
        )
        return trends_data
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving historical trends: {str(e)}"
        )


@router.get(
    "/my-analytics/conversations/history",
    response_model=ConversationHistoryResponse,
    summary="Get conversation history analysis",
    description="Get detailed analysis of your conversation history"
)
@inject
async def get_conversation_history_analysis(
    date_from: Optional[datetime] = Query(None, description="Start date"),
    date_to: Optional[datetime] = Query(None, description="End date"),
    limit: int = Query(20, ge=1, le=100, description="Number of conversations to analyze"),
    user_id: int = Depends(get_current_user_id),
    analytics_service: FromDishka[UserChatAnalyticsService] = None,
) -> ConversationHistoryResponse:
    """
    Get conversation history analysis.

    Includes:
    - Recent conversations summary
    - Conversation duration statistics
    - Topic distribution
    - Success/completion rates
    - Most productive conversations
    - Conversation quality metrics

    Args:
        date_from: Start date for history
        date_to: End date for history
        limit: Maximum conversations to analyze
        user_id: Current authenticated user ID
        analytics_service: Injected analytics service

    Returns:
        Conversation history analysis
    """
    if not date_to:
        date_to = datetime.now(UTC)
    if not date_from:
        date_from = date_to - timedelta(days=30)

    try:
        history_data = await analytics_service.get_conversation_history(
            user_id=user_id,
            date_from=date_from,
            date_to=date_to,
            limit=limit
        )
        return history_data
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving conversation history: {str(e)}"
        )


@router.get(
    "/my-analytics/export",
    response_model=UserExportDataResponse,
    summary="Export my analytics data",
    description="Export your personal analytics data in JSON or CSV format"
)
@inject
async def export_my_analytics(
    date_from: Optional[datetime] = Query(None, description="Start date"),
    date_to: Optional[datetime] = Query(None, description="End date"),
    format: str = Query(
        "json",
        pattern="^(json|csv)$",
        description="Export format"
    ),
    include_conversations: bool = Query(
        False,
        description="Include full conversation data"
    ),
    user_id: int = Depends(get_current_user_id),
    analytics_service: FromDishka[UserChatAnalyticsService] = None,
) -> UserExportDataResponse:
    """
    Export personal analytics data.

    Supports exporting:
    - Usage statistics
    - Cost breakdown
    - Agent preferences
    - Conversation summaries
    - Historical trends
    - Full conversation data (optional)

    Args:
        date_from: Start date for export
        date_to: End date for export
        format: Export format (json or csv)
        include_conversations: Include full conversation data
        user_id: Current authenticated user ID
        analytics_service: Injected analytics service

    Returns:
        Exported analytics data in requested format
    """
    if not date_to:
        date_to = datetime.now(UTC)
    if not date_from:
        date_from = date_to - timedelta(days=30)

    try:
        export_data = await analytics_service.export_user_analytics(
            user_id=user_id,
            date_from=date_from,
            date_to=date_to,
            export_format=format,
            include_conversations=include_conversations
        )
        return export_data
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error exporting analytics data: {str(e)}"
        )
