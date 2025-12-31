"""
Admin Chat Dashboard Response Schemas

Pydantic models for admin analytics endpoints.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class TimeSeriesDataPoint(BaseModel):
    """Single point in time series data."""

    timestamp: datetime
    value: float
    label: Optional[str] = None


class AgentLeaderboardEntry(BaseModel):
    """Entry in agent performance leaderboard."""

    agent_type: str = Field(..., description="Agent identifier")
    agent_name: str = Field(..., description="Human-readable agent name")
    rank: int = Field(..., description="Leaderboard rank")
    total_invocations: int = Field(..., description="Total times invoked")
    success_rate: float = Field(..., ge=0, le=1, description="Success rate (0.0-1.0)")
    avg_response_time_ms: float = Field(..., description="Average response time in milliseconds")
    total_cost_usd: float = Field(..., description="Total cost in USD")
    error_count: int = Field(..., description="Number of errors")
    last_used: Optional[datetime] = Field(None, description="Last time used")


class CostBreakdownEntry(BaseModel):
    """Entry in cost breakdown."""

    category: str = Field(..., description="Cost category (agent, model, user, etc.)")
    name: str = Field(..., description="Item name")
    cost_usd: float = Field(..., description="Cost in USD")
    percentage: float = Field(..., ge=0, le=100, description="Percentage of total")
    invocations: int = Field(..., description="Number of invocations")
    avg_cost_per_invocation: float = Field(..., description="Average cost per invocation")


class CacheStatistics(BaseModel):
    """Cache performance statistics."""

    cache_type: str
    hit_count: int
    miss_count: int
    hit_rate: float = Field(..., ge=0, le=1, description="Cache hit rate (0.0-1.0)")
    memory_usage_mb: float
    eviction_count: int
    avg_lookup_time_ms: float


class ErrorStatistics(BaseModel):
    """Error statistics."""

    error_type: str
    count: int
    percentage: float = Field(..., ge=0, le=100)
    severity: str = Field(..., pattern="^(critical|high|medium|low)$")
    most_common_message: Optional[str] = None
    affected_agents: List[str]
    first_occurrence: datetime
    last_occurrence: datetime


class UserEngagementMetrics(BaseModel):
    """User engagement metrics."""

    total_active_users: int
    daily_active_users: int
    weekly_active_users: int
    monthly_active_users: int
    new_users: int
    avg_sessions_per_user: float
    avg_messages_per_user: float
    user_retention_rate: float = Field(..., ge=0, le=1)


class ConversationStats(BaseModel):
    """Conversation statistics."""

    total_conversations: int
    total_messages: int
    avg_messages_per_conversation: float
    avg_conversation_duration_seconds: float
    completion_rate: float = Field(..., ge=0, le=1)
    peak_activity_hour: int = Field(..., ge=0, le=23)
    peak_activity_day: str


class AdminChatDashboardSummaryResponse(BaseModel):
    """Complete admin dashboard summary."""

    # Time period
    date_from: datetime
    date_to: datetime

    # High-level metrics
    total_conversations: int
    total_messages: int
    total_active_users: int
    total_cost_usd: float

    # Agent summary
    total_agent_invocations: int
    most_used_agent: str
    avg_success_rate: float = Field(..., ge=0, le=1)

    # Performance summary
    avg_response_time_ms: float
    error_rate: float = Field(..., ge=0, le=1)
    cache_hit_rate: float = Field(..., ge=0, le=1)

    # Top agents (condensed leaderboard)
    top_agents: List[AgentLeaderboardEntry] = Field(..., max_length=5)

    # Trends
    conversation_trend: List[TimeSeriesDataPoint]
    cost_trend: List[TimeSeriesDataPoint]


class AgentPerformanceResponse(BaseModel):
    """Agent performance metrics response."""

    date_from: datetime
    date_to: datetime
    total_agents: int

    # Leaderboard
    leaderboard: List[AgentLeaderboardEntry]

    # Aggregated metrics
    total_invocations: int
    overall_success_rate: float = Field(..., ge=0, le=1)
    avg_response_time_ms: float
    total_cost_usd: float

    # Performance trends
    invocation_trend: List[TimeSeriesDataPoint]
    response_time_trend: List[TimeSeriesDataPoint]


class CacheEfficiencyResponse(BaseModel):
    """Cache efficiency metrics response."""

    date_from: datetime
    date_to: datetime

    # Overall metrics
    overall_hit_rate: float = Field(..., ge=0, le=1)
    overall_miss_rate: float = Field(..., ge=0, le=1)
    total_memory_usage_mb: float
    total_cache_entries: int

    # Per-cache statistics
    cache_statistics: List[CacheStatistics]

    # Performance impact
    avg_cache_hit_time_ms: float
    avg_cache_miss_time_ms: float
    estimated_time_saved_seconds: float

    # Trends
    hit_rate_trend: List[TimeSeriesDataPoint]
    memory_usage_trend: List[TimeSeriesDataPoint]


class CostTrackingResponse(BaseModel):
    """Cost tracking metrics response."""

    date_from: datetime
    date_to: datetime

    # Total costs
    total_cost_usd: float
    avg_cost_per_conversation: float
    total_tokens_used: int

    # Breakdown
    cost_breakdown: List[CostBreakdownEntry]

    # Top spenders
    most_expensive_agent: str
    most_expensive_model: str
    highest_cost_user_id: Optional[int] = None

    # Projections
    projected_monthly_cost_usd: float
    cost_change_percentage: float = Field(..., description="% change from previous period")

    # Trends
    daily_cost_trend: List[TimeSeriesDataPoint]
    cost_by_agent_trend: Dict[str, List[TimeSeriesDataPoint]]


class ErrorMonitoringResponse(BaseModel):
    """Error monitoring metrics response."""

    date_from: datetime
    date_to: datetime

    # Overall error metrics
    total_errors: int
    error_rate: float = Field(..., ge=0, le=1, description="Errors per total requests")

    # Error breakdown
    errors_by_type: List[ErrorStatistics]
    errors_by_agent: Dict[str, int]
    errors_by_severity: Dict[str, int]

    # Critical errors
    critical_errors: int
    critical_error_messages: List[str]

    # Trends
    error_rate_trend: List[TimeSeriesDataPoint]
    errors_by_severity_trend: Dict[str, List[TimeSeriesDataPoint]]


class ActiveUsersResponse(BaseModel):
    """Active users metrics response."""

    date_from: datetime
    date_to: datetime

    # User engagement
    engagement_metrics: UserEngagementMetrics

    # Activity breakdown
    users_by_activity_level: Dict[str, int] = Field(
        ...,
        description="Users grouped by activity (power, regular, light, inactive)"
    )

    # Top users
    most_active_users: List[Dict[str, Any]] = Field(
        ...,
        max_length=10,
        description="Top users by message count (anonymized)"
    )

    # Trends
    dau_trend: List[TimeSeriesDataPoint]
    new_users_trend: List[TimeSeriesDataPoint]


class ConversationMetricsResponse(BaseModel):
    """Conversation metrics response."""

    date_from: datetime
    date_to: datetime

    # Basic statistics
    conversation_stats: ConversationStats

    # Topic distribution
    top_topics: List[Dict[str, Any]] = Field(
        ...,
        max_length=10,
        description="Most discussed topics with counts"
    )

    # Engagement patterns
    messages_by_hour: Dict[int, int] = Field(
        ...,
        description="Message distribution by hour (0-23)"
    )
    messages_by_day: Dict[str, int] = Field(
        ...,
        description="Message distribution by day of week"
    )

    # Trends
    conversation_trend: List[TimeSeriesDataPoint]
    message_trend: List[TimeSeriesDataPoint]


class ExportDataResponse(BaseModel):
    """Export data response."""

    export_format: str = Field(..., pattern="^(json|csv)$")
    date_from: datetime
    date_to: datetime
    sections_included: List[str]

    # Export data
    data: Dict[str, Any] = Field(
        ...,
        description="Exported data in requested format"
    )

    # Metadata
    generated_at: datetime
    record_count: int
    file_size_bytes: Optional[int] = None
