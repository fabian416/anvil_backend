"""
User Chat Analytics Response Schemas

Pydantic models for user-facing analytics endpoints.
"""

from datetime import datetime
from typing import List, Dict, Optional, Any
from uuid import UUID
from pydantic import BaseModel, Field


class DailyActivityPoint(BaseModel):
    """Daily activity data point."""

    date: datetime
    conversations: int
    messages: int
    agents_used: int
    cost_usd: float


class TopicDistribution(BaseModel):
    """Topic distribution data."""

    topic_name: str
    conversation_count: int
    percentage: float = Field(..., ge=0, le=100)
    keywords: List[str]
    trend: str = Field(..., pattern="^(rising|stable|declining)$")


class AgentPreferenceEntry(BaseModel):
    """Agent preference entry."""

    agent_type: str
    agent_name: str
    usage_count: int
    usage_percentage: float = Field(..., ge=0, le=100)
    success_rate: float = Field(..., ge=0, le=1)
    avg_response_time_ms: float
    total_cost_usd: float
    last_used: Optional[datetime] = None
    personal_rating: Optional[float] = Field(None, ge=1, le=5, description="User rating if available")


class ConversationSummary(BaseModel):
    """Summary of a single conversation."""

    conversation_id: UUID
    title: Optional[str]
    created_at: datetime
    message_count: int
    duration_seconds: float
    agents_used: List[str]
    primary_topic: Optional[str]
    cost_usd: float
    completed: bool


class PersonalUsageStats(BaseModel):
    """Personal usage statistics."""

    total_conversations: int
    total_messages: int
    avg_messages_per_conversation: float
    total_session_time_hours: float
    avg_session_duration_minutes: float
    most_active_day: str
    most_active_hour: int = Field(..., ge=0, le=23)
    conversation_completion_rate: float = Field(..., ge=0, le=1)


class ConversationInsights(BaseModel):
    """Conversation pattern insights."""

    avg_conversation_length_messages: float
    avg_conversation_duration_minutes: float
    most_discussed_topics: List[TopicDistribution]
    question_types: Dict[str, int] = Field(
        ...,
        description="Distribution of question types (informational, analytical, etc.)"
    )
    avg_time_to_decision_minutes: Optional[float] = None
    most_productive_time: str = Field(
        ...,
        description="Time period when conversations are most productive"
    )


class PersonalCostSummary(BaseModel):
    """Personal cost summary."""

    total_cost_usd: float
    avg_cost_per_conversation: float
    avg_cost_per_message: float
    total_tokens_used: int
    most_expensive_agent: str
    cost_trend: str = Field(..., pattern="^(increasing|stable|decreasing)$")
    projected_monthly_cost_usd: float


class TrendDataSeries(BaseModel):
    """Time series data for trends."""

    label: str
    data_points: List[DailyActivityPoint]
    total: int
    average: float
    trend_direction: str = Field(..., pattern="^(up|down|stable)$")
    change_percentage: float


class UserAnalyticsDashboardResponse(BaseModel):
    """User analytics dashboard summary."""

    # Time period
    date_from: datetime
    date_to: datetime

    # High-level personal metrics
    total_conversations: int
    total_messages: int
    total_cost_usd: float
    most_used_agent: str

    # Quick insights
    conversation_completion_rate: float = Field(..., ge=0, le=1)
    avg_response_satisfaction: Optional[float] = Field(
        None,
        ge=1,
        le=5,
        description="Average satisfaction rating if available"
    )

    # Top agents (condensed)
    top_agents: List[AgentPreferenceEntry] = Field(..., max_length=5)

    # Activity summary
    most_active_day: str
    most_active_hour: int = Field(..., ge=0, le=23)

    # Cost summary
    cost_this_period: float
    cost_change_percentage: float

    # Recent activity
    recent_conversations: List[ConversationSummary] = Field(..., max_length=5)


class PersonalUsageStatsResponse(BaseModel):
    """Personal usage statistics response."""

    date_from: datetime
    date_to: datetime

    # Detailed usage metrics
    usage_stats: PersonalUsageStats

    # Activity breakdown
    messages_by_day: Dict[str, int]
    messages_by_hour: Dict[int, int]

    # Engagement metrics
    avg_daily_conversations: float
    avg_daily_messages: float
    longest_conversation_messages: int
    longest_session_hours: float

    # Comparison to previous period
    conversation_growth: float = Field(..., description="% change from previous period")
    message_growth: float = Field(..., description="% change from previous period")


class ConversationInsightsResponse(BaseModel):
    """Conversation insights response."""

    date_from: datetime
    date_to: datetime

    # Pattern analysis
    insights: ConversationInsights

    # Topic analysis
    topic_distribution: List[TopicDistribution]

    # Conversation quality metrics
    avg_agent_switches_per_conversation: float
    successful_conversations_percentage: float = Field(..., ge=0, le=100)

    # Recommendations
    recommended_agents: List[str] = Field(
        ...,
        description="Agents recommended based on your patterns"
    )
    productivity_tips: List[str] = Field(
        ...,
        description="Tips to improve conversation productivity"
    )


class PersonalCostBreakdownResponse(BaseModel):
    """Personal cost breakdown response."""

    date_from: datetime
    date_to: datetime

    # Cost summary
    cost_summary: PersonalCostSummary

    # Detailed breakdown
    cost_by_agent: Dict[str, float]
    cost_by_model: Dict[str, float]
    cost_by_day: List[DailyActivityPoint]

    # Token usage
    tokens_by_agent: Dict[str, int]
    avg_tokens_per_conversation: float

    # Savings recommendations
    cost_saving_tips: List[str] = Field(
        ...,
        description="Tips to reduce costs while maintaining quality"
    )


class FavoriteAgentsResponse(BaseModel):
    """Favorite agents response."""

    date_from: datetime
    date_to: datetime

    # Agent preferences
    favorite_agents: List[AgentPreferenceEntry]

    # Usage patterns
    agent_switching_frequency: float
    preferred_agent_for_task: Dict[str, str] = Field(
        ...,
        description="Preferred agent by task type"
    )

    # Performance comparison
    best_performing_agent: str
    fastest_agent: str
    most_cost_effective_agent: str

    # Recommendations
    recommended_new_agents: List[str] = Field(
        ...,
        description="Agents you haven't tried that might be useful"
    )


class HistoricalTrendsResponse(BaseModel):
    """Historical trends response."""

    date_from: datetime
    date_to: datetime
    granularity: str = Field(..., pattern="^(hourly|daily|weekly)$")

    # Trend data
    conversation_trend: TrendDataSeries
    message_trend: TrendDataSeries
    cost_trend: TrendDataSeries

    # Activity patterns
    peak_usage_times: List[Dict[str, Any]]
    activity_consistency_score: float = Field(
        ...,
        ge=0,
        le=1,
        description="How consistent your usage pattern is (0.0-1.0)"
    )

    # Comparative metrics
    percentile_rank: Optional[int] = Field(
        None,
        ge=1,
        le=100,
        description="Your activity percentile among all users"
    )


class ConversationHistoryResponse(BaseModel):
    """Conversation history analysis response."""

    date_from: datetime
    date_to: datetime

    # Recent conversations
    conversations: List[ConversationSummary]
    total_conversations: int

    # Historical patterns
    avg_conversation_duration_minutes: float
    most_common_topics: List[str]
    agent_usage_distribution: Dict[str, int]

    # Quality metrics
    completion_rate: float = Field(..., ge=0, le=1)
    avg_satisfaction_rating: Optional[float] = Field(None, ge=1, le=5)

    # Insights
    most_productive_conversations: List[ConversationSummary] = Field(
        ...,
        max_length=5,
        description="Your most productive conversations"
    )


class UserExportDataResponse(BaseModel):
    """User analytics export response."""

    export_format: str = Field(..., pattern="^(json|csv)$")
    date_from: datetime
    date_to: datetime
    includes_conversations: bool

    # Export data
    data: Dict[str, Any] = Field(
        ...,
        description="Exported analytics data"
    )

    # Metadata
    generated_at: datetime
    record_count: int
    file_size_bytes: Optional[int] = None

    # Download info
    download_url: Optional[str] = Field(
        None,
        description="Temporary download URL if file is large"
    )
    expires_at: Optional[datetime] = Field(
        None,
        description="Expiration time for download URL"
    )
