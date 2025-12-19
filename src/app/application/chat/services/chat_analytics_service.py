"""
Chat Analytics Service - generates inline analytics responses.

Follows chat-orchestrated architecture: analytics accessed through conversation,
not separate REST endpoints.
"""

import logging
from typing import Optional, List
from datetime import datetime, timedelta
from uuid import UUID
from collections import Counter
import statistics

from app.domain.value_objects.chat.analytics import (
    ConversationTrends,
    AgentUsageStats,
    ResponseTimeMetrics,
    TopicCluster,
    DecisionVelocityMetrics,
    TeamCollaborationMetrics,
    CostMetrics,
)
from app.domain.chat.ports.conversation_repository import ConversationRepository

logger = logging.getLogger(__name__)


class ChatAnalyticsService:
    """
    Generate analytics inline in chat conversations.

    Instead of GET /api/v1/chat/analytics, users type "show analytics"
    and get formatted response in conversation.
    """

    def __init__(self, conversation_repository: ConversationRepository):
        """
        Initialize analytics service.

        Args:
            conversation_repository: Repository for conversation data
        """
        self._repository = conversation_repository

    async def generate_analytics_response(
        self,
        user_id: UUID,
        time_range: str = "30d",  # "7d", "30d", "90d"
        query_type: Optional[str] = None,  # specific metric or full dashboard
    ) -> str:
        """
        Generate formatted analytics response for chat.

        Args:
            user_id: User identifier
            time_range: Time range for analytics
            query_type: Specific analytics query or None for full dashboard

        Returns:
            Markdown-formatted analytics summary
        """
        # Calculate date range
        days = int(time_range.replace("d", ""))
        date_to = datetime.utcnow()
        date_from = date_to - timedelta(days=days)

        # Gather all metrics
        trends = await self._get_conversation_trends(user_id, date_from, date_to, time_range)
        agent_stats = await self._get_agent_usage_stats(user_id, date_from, date_to)
        response_times = await self._get_response_time_metrics(user_id, date_from, date_to)
        topics = await self._analyze_topic_clusters(user_id, date_from, date_to)
        decisions = await self._calculate_decision_velocity(user_id, date_from, date_to)
        collaboration = await self._get_team_collaboration_metrics(user_id, date_from, date_to)
        costs = await self._get_cost_metrics(user_id, date_from, date_to)

        # Generate formatted response
        return self._format_analytics_dashboard(
            trends=trends,
            agent_stats=agent_stats,
            response_times=response_times,
            topics=topics,
            decisions=decisions,
            collaboration=collaboration,
            costs=costs,
            time_range=time_range,
        )

    def _format_analytics_dashboard(
        self,
        trends: ConversationTrends,
        agent_stats: AgentUsageStats,
        response_times: ResponseTimeMetrics,
        topics: List[TopicCluster],
        decisions: DecisionVelocityMetrics,
        collaboration: TeamCollaborationMetrics,
        costs: CostMetrics,
        time_range: str,
    ) -> str:
        """
        Format analytics as markdown for chat display.

        Args:
            All analytics metrics
            time_range: Time range label

        Returns:
            Formatted markdown string
        """
        # Build formatted response
        lines = [
            "┌─ 📊 Chat Analytics: Last {} Days ─┐".format(time_range.replace("d", "")),
            "",
            "**Conversation Activity:**",
            f"  • Total conversations: {trends.total_conversations:,}",
            f"  • Total messages: {trends.total_messages:,}",
            f"  • Avg messages/conversation: {trends.avg_messages_per_conversation:.1f}",
        ]

        if trends.peak_activity_day:
            lines.append(f"  • Peak activity: {trends.peak_activity_day}s")

        if trends.conversation_growth_rate != 0:
            direction = "↑" if trends.conversation_growth_rate > 0 else "↓"
            lines.append(
                f"  • Growth rate: {direction} {abs(trends.conversation_growth_rate):.1f}%"
            )

        lines.extend([
            "",
            "**Agent Usage:**",
        ])

        # Top 5 agents
        sorted_agents = sorted(
            agent_stats.agent_invocations.items(),
            key=lambda x: x[1],
            reverse=True
        )[:5]

        medals = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣"]
        for idx, (agent, count) in enumerate(sorted_agents):
            pct = (count / agent_stats.total_invocations * 100) if agent_stats.total_invocations > 0 else 0
            lines.append(f"  {medals[idx]} {agent.replace('_', ' ').title()} - {pct:.0f}% ({count:,} invocations)")

        lines.extend([
            "",
            "**Response Performance:**",
            f"  • Median response time: {response_times.median_ms / 1000:.1f}s",
            f"  • 95th percentile: {response_times.p95_ms / 1000:.1f}s",
            f"  • 99th percentile: {response_times.p99_ms / 1000:.1f}s",
        ])

        if topics:
            lines.extend(["", "**Top Topics:**"])
            for topic in topics[:5]:
                emoji = "🔸" if topic.trend == "rising" else "🔹"
                lines.append(
                    f"  {emoji} {topic.topic_name} ({topic.conversation_count} conversations)"
                )

        if decisions.total_decisions > 0:
            lines.extend([
                "",
                "**Decision Velocity:**",
                f"  • Avg time to decision: {decisions.avg_time_to_decision_seconds / 60:.1f} minutes",
                f"  • Fastest decision: {decisions.fastest_decision_seconds:.0f} seconds",
                f"  • Slowest decision: {decisions.slowest_decision_seconds / 60:.0f} minutes",
            ])

        if collaboration.shared_conversations > 0:
            lines.extend([
                "",
                "**Team Collaboration:**",
                f"  • Shared conversations: {collaboration.shared_conversations}",
                f"  • Team members: {collaboration.team_members_count}",
                f"  • Mentions: {collaboration.total_mentions}",
            ])

        if costs.total_cost_usd > 0:
            lines.extend([
                "",
                "**Cost Analytics:**",
                f"  • Total LLM costs: ${costs.total_cost_usd:.2f}",
                f"  • Avg cost/conversation: ${costs.avg_cost_per_conversation:.3f}",
                f"  • Most expensive agent: {costs.most_expensive_agent}",
            ])

        lines.extend([
            "",
            "Want to see details for any specific metric? Just ask!",
            "└─────────────────────────────────────┘",
        ])

        return "\n".join(lines)

    async def _get_conversation_trends(
        self,
        user_id: UUID,
        date_from: datetime,
        date_to: datetime,
        time_range: str,
    ) -> ConversationTrends:
        """Get conversation trends."""
        # TODO: Implement actual database queries
        # Placeholder implementation
        return ConversationTrends(
            total_conversations=42,
            total_messages=1247,
            avg_messages_per_conversation=29.7,
            peak_activity_day="Thursday",
            peak_activity_time="2-4pm",
            conversation_growth_rate=15.3,
            time_range=time_range,
            date_from=date_from,
            date_to=date_to,
        )

    async def _get_agent_usage_stats(
        self,
        user_id: UUID,
        date_from: datetime,
        date_to: datetime,
    ) -> AgentUsageStats:
        """Get agent usage statistics."""
        # TODO: Implement actual database queries
        # Placeholder implementation
        return AgentUsageStats.create(
            agent_invocations={
                "risk_analyzer": 476,
                "yield_optimizer": 299,
                "portfolio_manager": 225,
                "security_auditor": 150,
                "hunter_ai": 97,
            },
            avg_execution_time_ms={
                "risk_analyzer": 8200,
                "yield_optimizer": 12400,
                "portfolio_manager": 15100,
                "security_auditor": 6800,
                "hunter_ai": 19500,
            },
            success_rates={
                "risk_analyzer": 0.98,
                "yield_optimizer": 0.96,
                "portfolio_manager": 0.99,
                "security_auditor": 0.97,
                "hunter_ai": 0.94,
            },
        )

    async def _get_response_time_metrics(
        self,
        user_id: UUID,
        date_from: datetime,
        date_to: datetime,
    ) -> ResponseTimeMetrics:
        """Get response time metrics."""
        # TODO: Implement actual database queries
        # Placeholder implementation
        return ResponseTimeMetrics(
            median_ms=2300,
            p95_ms=4800,
            p99_ms=7200,
            avg_ms=2850,
            min_ms=450,
            max_ms=15200,
            total_requests=1247,
        )

    async def _analyze_topic_clusters(
        self,
        user_id: UUID,
        date_from: datetime,
        date_to: datetime,
    ) -> List[TopicCluster]:
        """Analyze topic clusters."""
        # TODO: Implement actual ML-based topic clustering
        # Placeholder implementation
        return [
            TopicCluster(
                topic_name="Curve Finance risk",
                conversation_count=12,
                confidence_score=0.89,
                representative_keywords=["curve", "risk", "audit", "vulnerability"],
                trend="rising",
            ),
            TopicCluster(
                topic_name="Yield optimization",
                conversation_count=10,
                confidence_score=0.85,
                representative_keywords=["yield", "apy", "optimize", "returns"],
                trend="stable",
            ),
            TopicCluster(
                topic_name="Portfolio rebalancing",
                conversation_count=8,
                confidence_score=0.82,
                representative_keywords=["portfolio", "rebalance", "allocation"],
                trend="stable",
            ),
        ]

    async def _calculate_decision_velocity(
        self,
        user_id: UUID,
        date_from: datetime,
        date_to: datetime,
    ) -> DecisionVelocityMetrics:
        """Calculate decision velocity."""
        # TODO: Implement actual database queries
        # Placeholder implementation
        return DecisionVelocityMetrics(
            avg_time_to_decision_seconds=252,  # 4.2 minutes
            fastest_decision_seconds=45,
            slowest_decision_seconds=1080,  # 18 minutes
            total_decisions=34,
            decisions_by_type={
                "trade": 18,
                "rebalance": 8,
                "withdraw": 5,
                "deposit": 3,
            },
            avg_time_by_type={
                "trade": 180,
                "rebalance": 420,
                "withdraw": 240,
                "deposit": 150,
            },
        )

    async def _get_team_collaboration_metrics(
        self,
        user_id: UUID,
        date_from: datetime,
        date_to: datetime,
    ) -> TeamCollaborationMetrics:
        """Get team collaboration metrics."""
        # TODO: Implement actual database queries
        # Placeholder implementation
        return TeamCollaborationMetrics(
            shared_conversations=8,
            team_members_count=3,
            total_mentions=24,
            avg_response_time_hours=2.4,
            most_collaborative_member="Alice",
        )

    async def _get_cost_metrics(
        self,
        user_id: UUID,
        date_from: datetime,
        date_to: datetime,
    ) -> CostMetrics:
        """Get LLM API cost metrics."""
        # TODO: Implement actual cost tracking
        # Placeholder implementation
        return CostMetrics(
            total_cost_usd=12.45,
            cost_by_agent={
                "risk_analyzer": 4.32,
                "yield_optimizer": 3.89,
                "portfolio_manager": 2.54,
                "security_auditor": 1.12,
                "hunter_ai": 0.58,
            },
            cost_by_model={
                "gpt-4": 8.76,
                "gpt-3.5-turbo": 3.69,
            },
            total_tokens_used=875420,
            avg_cost_per_conversation=0.296,
            most_expensive_agent="risk_analyzer",
        )
