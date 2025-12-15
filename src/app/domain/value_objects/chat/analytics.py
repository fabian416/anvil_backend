"""
Chat analytics value objects.
"""

from dataclasses import dataclass
from typing import List, Dict, Optional
from datetime import datetime


@dataclass(frozen=True)
class ConversationTrends:
    """Conversation activity trends over time."""

    total_conversations: int
    total_messages: int
    avg_messages_per_conversation: float
    peak_activity_day: Optional[str]
    peak_activity_time: Optional[str]
    conversation_growth_rate: float  # percentage
    time_range: str  # "daily", "weekly", "monthly"
    date_from: datetime
    date_to: datetime

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "total_conversations": self.total_conversations,
            "total_messages": self.total_messages,
            "avg_messages_per_conversation": self.avg_messages_per_conversation,
            "peak_activity_day": self.peak_activity_day,
            "peak_activity_time": self.peak_activity_time,
            "conversation_growth_rate": self.conversation_growth_rate,
            "time_range": self.time_range,
            "date_from": self.date_from.isoformat(),
            "date_to": self.date_to.isoformat(),
        }


@dataclass(frozen=True)
class AgentUsageStats:
    """Agent usage statistics."""

    agent_invocations: Dict[str, int]  # agent_name -> count
    total_invocations: int
    most_used_agent: str
    most_used_agent_percentage: float
    avg_execution_time_ms: Dict[str, float]  # agent_name -> avg_time
    success_rates: Dict[str, float]  # agent_name -> success_rate

    @classmethod
    def create(
        cls,
        agent_invocations: Dict[str, int],
        avg_execution_time_ms: Dict[str, float],
        success_rates: Dict[str, float],
    ) -> "AgentUsageStats":
        """Create agent usage stats with calculated fields."""
        total = sum(agent_invocations.values())
        most_used = max(agent_invocations.items(), key=lambda x: x[1])

        return cls(
            agent_invocations=agent_invocations,
            total_invocations=total,
            most_used_agent=most_used[0],
            most_used_agent_percentage=(most_used[1] / total * 100) if total > 0 else 0,
            avg_execution_time_ms=avg_execution_time_ms,
            success_rates=success_rates,
        )

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "agent_invocations": self.agent_invocations,
            "total_invocations": self.total_invocations,
            "most_used_agent": self.most_used_agent,
            "most_used_agent_percentage": self.most_used_agent_percentage,
            "avg_execution_time_ms": self.avg_execution_time_ms,
            "success_rates": self.success_rates,
        }


@dataclass(frozen=True)
class ResponseTimeMetrics:
    """Response time performance metrics."""

    median_ms: float
    p95_ms: float
    p99_ms: float
    avg_ms: float
    min_ms: float
    max_ms: float
    total_requests: int

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "median_ms": self.median_ms,
            "p95_ms": self.p95_ms,
            "p99_ms": self.p99_ms,
            "avg_ms": self.avg_ms,
            "min_ms": self.min_ms,
            "max_ms": self.max_ms,
            "total_requests": self.total_requests,
        }


@dataclass(frozen=True)
class TopicCluster:
    """Discovered topic cluster from conversations."""

    topic_name: str
    conversation_count: int
    confidence_score: float
    representative_keywords: List[str]
    trend: str  # "rising", "stable", "declining"

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "topic_name": self.topic_name,
            "conversation_count": self.conversation_count,
            "confidence_score": self.confidence_score,
            "representative_keywords": self.representative_keywords,
            "trend": self.trend,
        }


@dataclass(frozen=True)
class DecisionVelocityMetrics:
    """Decision velocity metrics."""

    avg_time_to_decision_seconds: float
    fastest_decision_seconds: float
    slowest_decision_seconds: float
    total_decisions: int
    decisions_by_type: Dict[str, int]  # decision_type -> count
    avg_time_by_type: Dict[str, float]  # decision_type -> avg_seconds

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "avg_time_to_decision_seconds": self.avg_time_to_decision_seconds,
            "fastest_decision_seconds": self.fastest_decision_seconds,
            "slowest_decision_seconds": self.slowest_decision_seconds,
            "total_decisions": self.total_decisions,
            "decisions_by_type": self.decisions_by_type,
            "avg_time_by_type": self.avg_time_by_type,
        }


@dataclass(frozen=True)
class TeamCollaborationMetrics:
    """Team collaboration metrics."""

    shared_conversations: int
    team_members_count: int
    total_mentions: int
    avg_response_time_hours: float
    most_collaborative_member: Optional[str]

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "shared_conversations": self.shared_conversations,
            "team_members_count": self.team_members_count,
            "total_mentions": self.total_mentions,
            "avg_response_time_hours": self.avg_response_time_hours,
            "most_collaborative_member": self.most_collaborative_member,
        }


@dataclass(frozen=True)
class CostMetrics:
    """LLM API cost metrics."""

    total_cost_usd: float
    cost_by_agent: Dict[str, float]  # agent_name -> cost
    cost_by_model: Dict[str, float]  # model_name -> cost
    total_tokens_used: int
    avg_cost_per_conversation: float
    most_expensive_agent: str

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "total_cost_usd": self.total_cost_usd,
            "cost_by_agent": self.cost_by_agent,
            "cost_by_model": self.cost_by_model,
            "total_tokens_used": self.total_tokens_used,
            "avg_cost_per_conversation": self.avg_cost_per_conversation,
            "most_expensive_agent": self.most_expensive_agent,
        }
