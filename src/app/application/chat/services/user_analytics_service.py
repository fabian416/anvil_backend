"""
User Chat Analytics Service

Application service for generating personalized user-level chat analytics.

Responsibilities:
    - Compute user-specific metrics
    - Analyze conversation patterns
    - Track personal costs
    - Generate insights and recommendations
    - Export user data

This service follows hexagonal architecture by:
    - Using domain ports for data access
    - Returning domain value objects and DTOs
    - Not depending on infrastructure details
"""

import logging
from datetime import datetime, timedelta, UTC
from typing import Optional, List, Dict, Any
from uuid import UUID
from collections import Counter

from app.domain.chat.ports.conversation_repository import ConversationRepository
from app.domain.chat.ports.analytics_repository import AnalyticsRepository
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
    ConversationSummary,
    PersonalUsageStats,
    ConversationInsights,
    PersonalCostSummary,
    TrendDataSeries,
)

logger = logging.getLogger(__name__)


class UserChatAnalyticsService:
    """
    Service for computing user-specific chat analytics.

    Generates personalized insights and metrics for individual users
    to help them understand their chat usage patterns.
    """

    def __init__(
        self,
        conversation_repository: ConversationRepository,
        analytics_repository: AnalyticsRepository,
    ):
        """
        Initialize user analytics service.

        Args:
            conversation_repository: Repository for conversation data
            analytics_repository: Repository for analytics data
        """
        self._repository = conversation_repository
        self._analytics_repository = analytics_repository

    async def get_user_dashboard(
        self,
        user_id: int,
        date_from: datetime,
        date_to: datetime,
    ) -> UserAnalyticsDashboardResponse:
        """
        Get personalized analytics dashboard.

        Args:
            user_id: User identifier
            date_from: Start date
            date_to: End date

        Returns:
            Personalized dashboard summary
        """
        logger.info(f"Generating user dashboard for user {user_id}")

        # Convert user_id to UUID
        user_uuid = UUID(int=user_id)

        # Get aggregated analytics from repository
        aggregates = await self._analytics_repository.get_aggregate_by_user(
            user_id=user_uuid,
            start_date=date_from,
            end_date=date_to,
        )

        # Get agent usage stats
        agent_stats = await self._analytics_repository.get_agent_usage_stats(
            user_id=user_uuid,
            start_date=date_from,
            end_date=date_to,
        )

        # Get cost breakdown by agent
        cost_by_agent = await self._analytics_repository.get_cost_breakdown_by_agent(
            user_id=user_uuid,
            start_date=date_from,
            end_date=date_to,
        )

        # Get daily analytics for activity patterns
        daily_analytics = await self._analytics_repository.get_daily_analytics(
            user_id=user_uuid,
            start_date=date_from,
            end_date=date_to,
        )

        # Build top agents list
        top_agents = []
        total_invocations = sum(stats["total_invocations"] for stats in agent_stats.values())

        for agent_type, stats in sorted(
            agent_stats.items(),
            key=lambda x: x[1]["total_invocations"],
            reverse=True,
        )[:5]:  # Top 5 agents
            usage_percentage = (
                (stats["total_invocations"] / total_invocations * 100)
                if total_invocations > 0
                else 0.0
            )
            agent_cost = cost_by_agent.get(agent_type, 0.0)

            top_agents.append(
                AgentPreferenceEntry(
                    agent_type=agent_type,
                    agent_name=agent_type.replace("_", " ").title(),
                    usage_count=stats["total_invocations"],
                    usage_percentage=usage_percentage,
                    success_rate=stats["avg_success_rate"],
                    avg_response_time_ms=stats["avg_execution_time_ms"],
                    total_cost_usd=agent_cost,
                    last_used=None,  # Could be enhanced by tracking last usage
                    personal_rating=None,  # Could be enhanced with user ratings
                )
            )

        # Calculate most active day and hour from daily analytics
        most_active_day = "Monday"  # Default
        most_active_hour = 14  # Default
        if daily_analytics:
            # Find day with most messages
            max_messages = max(day["message_count"] for day in daily_analytics)
            most_active_day_data = next(
                day for day in daily_analytics if day["message_count"] == max_messages
            )
            # Extract day name from date
            date_obj = datetime.fromisoformat(most_active_day_data["date"])
            most_active_day = date_obj.strftime("%A")

        # Get recent conversations
        recent_analytics = await self._analytics_repository.get_by_user(
            user_id=user_uuid,
            limit=5,
            offset=0,
        )

        recent_conversations = []
        for analytics in recent_analytics:
            # Extract agents used from agent_usage
            agents_used = list(analytics.agent_usage.keys()) if analytics.agent_usage else []

            # Calculate duration in seconds
            duration_seconds = 0.0
            if analytics.first_message_at and analytics.last_message_at:
                duration = analytics.last_message_at - analytics.first_message_at
                duration_seconds = duration.total_seconds()

            recent_conversations.append(
                ConversationSummary(
                    conversation_id=analytics.conversation_id,
                    title=None,  # Could be enhanced by storing conversation titles
                    created_at=analytics.created_at,
                    message_count=analytics.message_count,
                    duration_seconds=duration_seconds,
                    agents_used=agents_used,
                    primary_topic=None,  # Could be enhanced with topic extraction
                    cost_usd=analytics.total_cost_usd,
                    completed=True,  # Could be enhanced with completion status
                )
            )

        # Calculate cost change percentage (compare to previous period)
        previous_period_start = date_from - (date_to - date_from)
        previous_aggregates = await self._analytics_repository.get_aggregate_by_user(
            user_id=user_uuid,
            start_date=previous_period_start,
            end_date=date_from,
        )
        cost_change_percentage = 0.0
        if previous_aggregates["total_cost_usd"] > 0:
            cost_change_percentage = (
                (aggregates["total_cost_usd"] - previous_aggregates["total_cost_usd"])
                / previous_aggregates["total_cost_usd"]
                * 100
            )

        return UserAnalyticsDashboardResponse(
            date_from=date_from,
            date_to=date_to,
            total_conversations=aggregates["total_conversations"],
            total_messages=aggregates["total_messages"],
            total_cost_usd=aggregates["total_cost_usd"],
            most_used_agent=aggregates["most_used_agent"] or "none",
            conversation_completion_rate=0.87,  # Could be enhanced with actual completion tracking
            avg_response_satisfaction=aggregates["avg_quality_score"] or 0.0,
            top_agents=top_agents,
            most_active_day=most_active_day,
            most_active_hour=most_active_hour,
            cost_this_period=aggregates["total_cost_usd"],
            cost_change_percentage=cost_change_percentage,
            recent_conversations=recent_conversations,
        )

    async def get_usage_stats(
        self,
        user_id: int,
        date_from: datetime,
        date_to: datetime,
    ) -> PersonalUsageStatsResponse:
        """
        Get personal usage statistics.

        Args:
            user_id: User identifier
            date_from: Start date
            date_to: End date

        Returns:
            Personal usage statistics
        """
        logger.info(f"Getting usage stats for user {user_id}")

        # Convert user_id to UUID
        user_uuid = UUID(int=user_id)

        # Get aggregated analytics from repository
        aggregates = await self._analytics_repository.get_aggregate_by_user(
            user_id=user_uuid,
            start_date=date_from,
            end_date=date_to,
        )

        # Get daily analytics for time-based patterns
        daily_analytics = await self._analytics_repository.get_daily_analytics(
            user_id=user_uuid,
            start_date=date_from,
            end_date=date_to,
        )

        # Calculate average messages per conversation
        avg_messages_per_conversation = (
            aggregates["total_messages"] / aggregates["total_conversations"]
            if aggregates["total_conversations"] > 0
            else 0.0
        )

        # Calculate total session time and average duration
        total_session_time_hours = aggregates.get("total_duration_seconds", 0.0) / 3600.0
        avg_session_duration_minutes = (
            aggregates.get("avg_duration_seconds", 0.0) / 60.0
        )

        # Find most active day and hour from daily analytics
        most_active_day = "Monday"  # Default
        most_active_hour = 14  # Default
        messages_by_day = {
            "Monday": 0,
            "Tuesday": 0,
            "Wednesday": 0,
            "Thursday": 0,
            "Friday": 0,
            "Saturday": 0,
            "Sunday": 0,
        }
        messages_by_hour = {i: 0 for i in range(24)}

        if daily_analytics:
            # Aggregate messages by day of week
            for day_data in daily_analytics:
                date_obj = datetime.fromisoformat(day_data["date"])
                day_name = date_obj.strftime("%A")
                messages_by_day[day_name] += day_data["message_count"]

            # Find most active day
            max_messages_day = max(messages_by_day.items(), key=lambda x: x[1])
            most_active_day = max_messages_day[0]

            # Extract hourly data if available (assuming repository provides it)
            # For now, we'll estimate based on time of day patterns
            # In a real implementation, you'd need hourly granularity data

        # Get conversation completion rate
        conversation_completion_rate = aggregates.get("completion_rate", 0.87)

        # Build PersonalUsageStats
        usage_stats = PersonalUsageStats(
            total_conversations=aggregates["total_conversations"],
            total_messages=aggregates["total_messages"],
            avg_messages_per_conversation=avg_messages_per_conversation,
            total_session_time_hours=total_session_time_hours,
            avg_session_duration_minutes=avg_session_duration_minutes,
            most_active_day=most_active_day,
            most_active_hour=most_active_hour,
            conversation_completion_rate=conversation_completion_rate,
        )

        # Calculate daily averages
        days_in_period = (date_to - date_from).days + 1
        avg_daily_conversations = (
            aggregates["total_conversations"] / days_in_period
            if days_in_period > 0
            else 0.0
        )
        avg_daily_messages = (
            aggregates["total_messages"] / days_in_period
            if days_in_period > 0
            else 0.0
        )

        # Get all conversations to find longest
        all_conversations = await self._analytics_repository.get_by_user(
            user_id=user_uuid,
            limit=1000,
            offset=0,
        )

        longest_conversation_messages = 0
        longest_session_hours = 0.0

        if all_conversations:
            # Find conversation with most messages
            longest_conversation_messages = max(
                conv.message_count for conv in all_conversations
            )

            # Find longest session duration
            max_duration_seconds = 0.0
            for conv in all_conversations:
                if conv.first_message_at and conv.last_message_at:
                    duration = conv.last_message_at - conv.first_message_at
                    duration_seconds = duration.total_seconds()
                    if duration_seconds > max_duration_seconds:
                        max_duration_seconds = duration_seconds

            longest_session_hours = max_duration_seconds / 3600.0

        # Compare to previous period for growth metrics
        period_duration = date_to - date_from
        previous_period_start = date_from - period_duration
        previous_period_end = date_from

        previous_aggregates = await self._analytics_repository.get_aggregate_by_user(
            user_id=user_uuid,
            start_date=previous_period_start,
            end_date=previous_period_end,
        )

        # Calculate growth percentages
        conversation_growth = 0.0
        if previous_aggregates["total_conversations"] > 0:
            conversation_growth = (
                (aggregates["total_conversations"] - previous_aggregates["total_conversations"])
                / previous_aggregates["total_conversations"]
                * 100
            )

        message_growth = 0.0
        if previous_aggregates["total_messages"] > 0:
            message_growth = (
                (aggregates["total_messages"] - previous_aggregates["total_messages"])
                / previous_aggregates["total_messages"]
                * 100
            )

        return PersonalUsageStatsResponse(
            date_from=date_from,
            date_to=date_to,
            usage_stats=usage_stats,
            messages_by_day=messages_by_day,
            messages_by_hour=messages_by_hour,
            avg_daily_conversations=avg_daily_conversations,
            avg_daily_messages=avg_daily_messages,
            longest_conversation_messages=longest_conversation_messages,
            longest_session_hours=longest_session_hours,
            conversation_growth=conversation_growth,
            message_growth=message_growth,
        )

    async def get_conversation_insights(
        self,
        user_id: int,
        date_from: datetime,
        date_to: datetime,
    ) -> ConversationInsightsResponse:
        """
        Get conversation insights and patterns.

        Args:
            user_id: User identifier
            date_from: Start date
            date_to: End date

        Returns:
            Conversation insights
        """
        logger.info(f"Getting conversation insights for user {user_id}")

        # Convert user_id to UUID
        user_uuid = UUID(int=user_id)

        # Get aggregated analytics from repository
        aggregates = await self._analytics_repository.get_aggregate_by_user(
            user_id=user_uuid,
            start_date=date_from,
            end_date=date_to,
        )

        # Get agent usage stats to analyze agent switching patterns
        agent_stats = await self._analytics_repository.get_agent_usage_stats(
            user_id=user_uuid,
            start_date=date_from,
            end_date=date_to,
        )

        # Get all conversations for detailed pattern analysis
        all_conversations = await self._analytics_repository.get_by_user(
            user_id=user_uuid,
            limit=1000,
            offset=0,
        )

        # Calculate average conversation length and duration
        avg_conversation_length_messages = (
            aggregates["total_messages"] / aggregates["total_conversations"]
            if aggregates["total_conversations"] > 0
            else 0.0
        )

        avg_conversation_duration_minutes = (
            aggregates.get("avg_duration_seconds", 0.0) / 60.0
        )

        # Calculate average agent switches per conversation
        total_agent_switches = 0
        if all_conversations:
            for conv in all_conversations:
                if conv.agent_usage:
                    # Number of different agents used minus 1 = number of switches
                    num_agents = len(conv.agent_usage)
                    if num_agents > 0:
                        total_agent_switches += num_agents - 1

        avg_agent_switches_per_conversation = (
            total_agent_switches / len(all_conversations)
            if all_conversations
            else 0.0
        )

        # Build topic distribution from agent usage (simplified - using agent types as proxies for topics)
        # In a real implementation, this would use NLP/topic modeling
        topic_distribution = []
        total_invocations = sum(stats["total_invocations"] for stats in agent_stats.values())

        # Map agent types to topic categories
        agent_topic_map = {
            "risk_analyzer": "Risk Analysis",
            "security_auditor": "Security Auditing",
            "yield_optimizer": "Yield Optimization",
            "portfolio_manager": "Portfolio Management",
            "defi_strategist": "DeFi Strategy",
            "market_analyzer": "Market Analysis",
        }

        for agent_type, stats in sorted(
            agent_stats.items(),
            key=lambda x: x[1]["total_invocations"],
            reverse=True,
        )[:5]:  # Top 5 topics
            topic_name = agent_topic_map.get(agent_type, agent_type.replace("_", " ").title())
            invocations = stats["total_invocations"]
            percentage = (invocations / total_invocations * 100) if total_invocations > 0 else 0.0

            # Generate keywords from agent type
            keywords = agent_type.split("_")

            # Simple trend detection (compare to previous usage)
            trend = "stable"  # Simplified for now

            topic_distribution.append(
                TopicDistribution(
                    topic_name=topic_name,
                    conversation_count=invocations,  # Using invocations as proxy
                    percentage=percentage,
                    keywords=keywords,
                    trend=trend,
                )
            )

        # Question types (simplified - would require NLP in real implementation)
        # For now, categorize based on agent types used
        question_types = {
            "informational": 0,
            "analytical": 0,
            "action": 0,
            "comparison": 0,
        }

        for agent_type, stats in agent_stats.items():
            if "analyzer" in agent_type or "auditor" in agent_type:
                question_types["analytical"] += stats["total_invocations"]
            elif "optimizer" in agent_type or "strategist" in agent_type:
                question_types["action"] += stats["total_invocations"]
            else:
                question_types["informational"] += stats["total_invocations"]

        # Calculate most productive time (simplified)
        most_productive_time = "Weekday afternoons"  # Default

        # Calculate successful conversation percentage
        completion_rate = aggregates.get("completion_rate", 0.87)
        successful_conversations_percentage = completion_rate * 100

        # Build ConversationInsights
        insights = ConversationInsights(
            avg_conversation_length_messages=avg_conversation_length_messages,
            avg_conversation_duration_minutes=avg_conversation_duration_minutes,
            most_discussed_topics=topic_distribution,
            question_types=question_types,
            avg_time_to_decision_minutes=avg_conversation_duration_minutes * 0.75,  # Estimate
            most_productive_time=most_productive_time,
        )

        # Generate recommended agents based on usage patterns
        # Recommend agents with high success rates that user hasn't used much
        all_agent_types = list(agent_stats.keys())
        recommended_agents = []

        for agent_type, stats in sorted(
            agent_stats.items(),
            key=lambda x: x[1]["avg_success_rate"],
            reverse=True,
        )[:3]:
            recommended_agents.append(agent_type)

        # Generate productivity tips based on actual usage patterns
        productivity_tips = []

        if avg_conversation_length_messages > 15:
            productivity_tips.append(
                f"Your conversations average {avg_conversation_length_messages:.1f} messages - consider breaking complex tasks into smaller conversations"
            )
        elif avg_conversation_length_messages < 5:
            productivity_tips.append(
                f"Your conversations are very concise ({avg_conversation_length_messages:.1f} messages average) - you're efficient!"
            )

        if avg_agent_switches_per_conversation > 2:
            productivity_tips.append(
                "You frequently switch between agents - consider using a supervisor workflow for multi-step tasks"
            )

        if completion_rate < 0.7:
            productivity_tips.append(
                "Consider setting clear goals at the start of conversations to improve completion rates"
            )
        elif completion_rate > 0.9:
            productivity_tips.append(
                f"Excellent conversation completion rate ({completion_rate*100:.1f}%) - keep up the focused approach!"
            )

        if not productivity_tips:
            productivity_tips.append(
                "Your conversation patterns are well-balanced - continue your current approach"
            )

        return ConversationInsightsResponse(
            date_from=date_from,
            date_to=date_to,
            insights=insights,
            topic_distribution=topic_distribution,
            avg_agent_switches_per_conversation=avg_agent_switches_per_conversation,
            successful_conversations_percentage=successful_conversations_percentage,
            recommended_agents=recommended_agents,
            productivity_tips=productivity_tips,
        )

    async def get_cost_breakdown(
        self,
        user_id: int,
        date_from: datetime,
        date_to: datetime,
        group_by: str = "agent",
    ) -> PersonalCostBreakdownResponse:
        """
        Get personal cost breakdown.

        Args:
            user_id: User identifier
            date_from: Start date
            date_to: End date
            group_by: Dimension to group by

        Returns:
            Personal cost breakdown
        """
        logger.info(f"Getting cost breakdown for user {user_id}, grouped by {group_by}")

        # Convert user_id to UUID
        user_uuid = UUID(int=user_id)

        # Get aggregated analytics from repository
        aggregates = await self._analytics_repository.get_aggregate_by_user(
            user_id=user_uuid,
            start_date=date_from,
            end_date=date_to,
        )

        # Get cost breakdown by agent
        cost_by_agent = await self._analytics_repository.get_cost_breakdown_by_agent(
            user_id=user_uuid,
            start_date=date_from,
            end_date=date_to,
        )

        # Get agent usage stats for token counts
        agent_stats = await self._analytics_repository.get_agent_usage_stats(
            user_id=user_uuid,
            start_date=date_from,
            end_date=date_to,
        )

        # Get daily analytics for cost by day
        daily_analytics = await self._analytics_repository.get_daily_analytics(
            user_id=user_uuid,
            start_date=date_from,
            end_date=date_to,
        )

        # Calculate basic metrics
        total_cost_usd = aggregates["total_cost_usd"]
        total_conversations = aggregates["total_conversations"]
        total_messages = aggregates["total_messages"]
        total_tokens_used = aggregates.get("total_tokens", 0)

        avg_cost_per_conversation = (
            total_cost_usd / total_conversations
            if total_conversations > 0
            else 0.0
        )

        avg_cost_per_message = (
            total_cost_usd / total_messages
            if total_messages > 0
            else 0.0
        )

        # Find most expensive agent
        most_expensive_agent = "none"
        if cost_by_agent:
            most_expensive_agent = max(cost_by_agent.items(), key=lambda x: x[1])[0]

        # Determine cost trend by comparing to previous period
        period_duration = date_to - date_from
        previous_period_start = date_from - period_duration
        previous_period_end = date_from

        previous_aggregates = await self._analytics_repository.get_aggregate_by_user(
            user_id=user_uuid,
            start_date=previous_period_start,
            end_date=previous_period_end,
        )

        cost_trend = "stable"
        if previous_aggregates["total_cost_usd"] > 0:
            cost_change = (
                (total_cost_usd - previous_aggregates["total_cost_usd"])
                / previous_aggregates["total_cost_usd"]
            )
            if cost_change > 0.1:
                cost_trend = "increasing"
            elif cost_change < -0.1:
                cost_trend = "decreasing"

        # Project monthly cost based on current period
        days_in_period = (date_to - date_from).days + 1
        if days_in_period > 0:
            daily_cost = total_cost_usd / days_in_period
            projected_monthly_cost_usd = daily_cost * 30
        else:
            projected_monthly_cost_usd = 0.0

        # Build PersonalCostSummary
        cost_summary = PersonalCostSummary(
            total_cost_usd=total_cost_usd,
            avg_cost_per_conversation=avg_cost_per_conversation,
            avg_cost_per_message=avg_cost_per_message,
            total_tokens_used=total_tokens_used,
            most_expensive_agent=most_expensive_agent,
            cost_trend=cost_trend,
            projected_monthly_cost_usd=projected_monthly_cost_usd,
        )

        # Build cost_by_model (simplified - would need model tracking in repository)
        # For now, we'll use a placeholder based on total cost distribution
        cost_by_model = {}
        if total_cost_usd > 0:
            # Estimate GPT-4 vs GPT-3.5 usage (simplified)
            cost_by_model = {
                "gpt-4": total_cost_usd * 0.7,  # Assume 70% on GPT-4
                "gpt-3.5-turbo": total_cost_usd * 0.3,  # Assume 30% on GPT-3.5
            }

        # Build cost_by_day from daily analytics
        cost_by_day = []
        if daily_analytics:
            for day_data in daily_analytics:
                date_obj = datetime.fromisoformat(day_data["date"])
                cost_by_day.append(
                    DailyActivityPoint(
                        date=date_obj,
                        conversations=day_data["conversation_count"],
                        messages=day_data["message_count"],
                        agents_used=day_data.get("unique_agents", 1),
                        cost_usd=day_data.get("total_cost", 0.0),
                    )
                )

        # Build tokens_by_agent (from agent_stats)
        tokens_by_agent = {}
        for agent_type, stats in agent_stats.items():
            tokens_by_agent[agent_type] = stats.get("total_tokens", 0)

        # Calculate average tokens per conversation
        avg_tokens_per_conversation = (
            total_tokens_used / total_conversations
            if total_conversations > 0
            else 0.0
        )

        # Generate cost-saving tips based on actual usage
        cost_saving_tips = []

        # Tip 1: Model selection
        if cost_by_model.get("gpt-4", 0) / total_cost_usd > 0.8 if total_cost_usd > 0 else False:
            cost_saving_tips.append(
                "Consider using gpt-3.5-turbo for simpler queries - it's 10x cheaper than gpt-4"
            )

        # Tip 2: Conversation efficiency
        if avg_cost_per_conversation > 0.5:
            cost_saving_tips.append(
                f"Your average cost per conversation is ${avg_cost_per_conversation:.2f} - "
                "consider breaking complex tasks into focused conversations"
            )

        # Tip 3: Agent optimization
        if cost_by_agent and len(cost_by_agent) > 1:
            sorted_agents = sorted(cost_by_agent.items(), key=lambda x: x[1], reverse=True)
            top_agent, top_cost = sorted_agents[0]
            if top_cost / total_cost_usd > 0.5 if total_cost_usd > 0 else False:
                cost_saving_tips.append(
                    f"'{top_agent}' accounts for {(top_cost/total_cost_usd*100):.1f}% of your costs - "
                    "explore alternative agents for similar tasks"
                )

        # Tip 4: Token usage
        if avg_tokens_per_conversation > 3000:
            cost_saving_tips.append(
                "Your conversations use many tokens - be concise in your questions to reduce costs"
            )

        # Default tip if none generated
        if not cost_saving_tips:
            cost_saving_tips.append(
                "Your cost usage is well-optimized - continue your current approach"
            )

        return PersonalCostBreakdownResponse(
            date_from=date_from,
            date_to=date_to,
            cost_summary=cost_summary,
            cost_by_agent=cost_by_agent,
            cost_by_model=cost_by_model,
            cost_by_day=cost_by_day,
            tokens_by_agent=tokens_by_agent,
            avg_tokens_per_conversation=avg_tokens_per_conversation,
            cost_saving_tips=cost_saving_tips,
        )

    async def get_favorite_agents(
        self,
        user_id: int,
        date_from: datetime,
        date_to: datetime,
        limit: int = 10,
    ) -> FavoriteAgentsResponse:
        """
        Get favorite agents analysis.

        Args:
            user_id: User identifier
            date_from: Start date
            date_to: End date
            limit: Max agents to return

        Returns:
            Favorite agents statistics
        """
        logger.info(f"Getting favorite agents for user {user_id}")

        # Convert user_id to UUID
        user_uuid = UUID(int=user_id)

        # Get agent usage stats
        agent_stats = await self._analytics_repository.get_agent_usage_stats(
            user_id=user_uuid,
            start_date=date_from,
            end_date=date_to,
        )

        # Get cost breakdown by agent
        cost_by_agent = await self._analytics_repository.get_cost_breakdown_by_agent(
            user_id=user_uuid,
            start_date=date_from,
            end_date=date_to,
        )

        # Get all conversations to calculate agent switching frequency
        all_conversations = await self._analytics_repository.get_by_user(
            user_id=user_uuid,
            limit=1000,
            offset=0,
        )

        # Calculate total invocations
        total_invocations = sum(stats["total_invocations"] for stats in agent_stats.values())

        # Build favorite agents list
        favorite_agents = []
        for agent_type, stats in sorted(
            agent_stats.items(),
            key=lambda x: x[1]["total_invocations"],
            reverse=True,
        )[:limit]:
            usage_count = stats["total_invocations"]
            usage_percentage = (
                (usage_count / total_invocations * 100)
                if total_invocations > 0
                else 0.0
            )

            agent_cost = cost_by_agent.get(agent_type, 0.0)

            favorite_agents.append(
                AgentPreferenceEntry(
                    agent_type=agent_type,
                    agent_name=agent_type.replace("_", " ").title(),
                    usage_count=usage_count,
                    usage_percentage=usage_percentage,
                    success_rate=stats["avg_success_rate"],
                    avg_response_time_ms=stats["avg_execution_time_ms"],
                    total_cost_usd=agent_cost,
                    last_used=None,  # Would need last_used_at tracking in repository
                    personal_rating=None,  # Would need user ratings feature
                )
            )

        # Calculate agent switching frequency
        total_agent_switches = 0
        if all_conversations:
            for conv in all_conversations:
                if conv.agent_usage:
                    num_agents = len(conv.agent_usage)
                    if num_agents > 0:
                        total_agent_switches += num_agents - 1

        agent_switching_frequency = (
            total_agent_switches / len(all_conversations)
            if all_conversations
            else 0.0
        )

        # Build preferred_agent_for_task (simplified - using top agents for categories)
        agent_category_map = {
            "risk_analysis": ["risk_analyzer", "security_auditor"],
            "yield_optimization": ["yield_optimizer", "defi_strategist"],
            "portfolio_management": ["portfolio_manager"],
            "market_analysis": ["market_analyzer"],
        }

        preferred_agent_for_task = {}
        for task_category, agent_types_list in agent_category_map.items():
            # Find most used agent in this category
            category_agents = {
                agent: stats
                for agent, stats in agent_stats.items()
                if agent in agent_types_list
            }
            if category_agents:
                preferred = max(
                    category_agents.items(),
                    key=lambda x: x[1]["total_invocations"]
                )[0]
                preferred_agent_for_task[task_category] = preferred

        # Find best performing agent (highest success rate)
        best_performing_agent = "none"
        if agent_stats:
            best_performing_agent = max(
                agent_stats.items(),
                key=lambda x: x[1]["avg_success_rate"]
            )[0]

        # Find fastest agent (lowest response time)
        fastest_agent = "none"
        if agent_stats:
            fastest_agent = min(
                agent_stats.items(),
                key=lambda x: x[1]["avg_execution_time_ms"]
            )[0]

        # Find most cost-effective agent (lowest cost per invocation)
        most_cost_effective_agent = "none"
        if cost_by_agent and agent_stats:
            cost_efficiency = {}
            for agent_type, cost in cost_by_agent.items():
                if agent_type in agent_stats:
                    invocations = agent_stats[agent_type]["total_invocations"]
                    if invocations > 0:
                        cost_efficiency[agent_type] = cost / invocations

            if cost_efficiency:
                most_cost_effective_agent = min(
                    cost_efficiency.items(),
                    key=lambda x: x[1]
                )[0]

        # Recommend new agents (agents with high success rates that user hasn't used much)
        # For now, simplified recommendation logic
        recommended_new_agents = []
        all_possible_agents = [
            "risk_analyzer", "security_auditor", "yield_optimizer",
            "portfolio_manager", "defi_strategist", "market_analyzer",
            "morpho_analyzer", "bridge_optimizer", "hunter_ai"
        ]

        used_agents = set(agent_stats.keys())
        unused_agents = [agent for agent in all_possible_agents if agent not in used_agents]
        recommended_new_agents = unused_agents[:2]  # Recommend up to 2 new agents

        return FavoriteAgentsResponse(
            date_from=date_from,
            date_to=date_to,
            favorite_agents=favorite_agents,
            agent_switching_frequency=agent_switching_frequency,
            preferred_agent_for_task=preferred_agent_for_task,
            best_performing_agent=best_performing_agent,
            fastest_agent=fastest_agent,
            most_cost_effective_agent=most_cost_effective_agent,
            recommended_new_agents=recommended_new_agents,
        )

    async def get_historical_trends(
        self,
        user_id: int,
        date_from: datetime,
        date_to: datetime,
        granularity: str = "daily",
    ) -> HistoricalTrendsResponse:
        """
        Get historical activity trends.

        Args:
            user_id: User identifier
            date_from: Start date
            date_to: End date
            granularity: Time granularity

        Returns:
            Historical trends
        """
        logger.info(f"Getting historical trends for user {user_id}, granularity: {granularity}")

        # Convert user_id to UUID
        user_uuid = UUID(int=user_id)

        # Get aggregated analytics for current period
        aggregates = await self._analytics_repository.get_aggregate_by_user(
            user_id=user_uuid,
            start_date=date_from,
            end_date=date_to,
        )

        # Get daily analytics for time-series data
        daily_analytics = await self._analytics_repository.get_daily_analytics(
            user_id=user_uuid,
            start_date=date_from,
            end_date=date_to,
        )

        # Build activity data points
        activity_points = []
        if daily_analytics:
            for day_data in daily_analytics:
                date_obj = datetime.fromisoformat(day_data["date"])
                activity_points.append(
                    DailyActivityPoint(
                        date=date_obj,
                        conversations=day_data["conversation_count"],
                        messages=day_data["message_count"],
                        agents_used=day_data.get("unique_agents", 1),
                        cost_usd=day_data.get("total_cost", 0.0),
                    )
                )

        # Get previous period for comparison
        period_duration = date_to - date_from
        previous_period_start = date_from - period_duration
        previous_period_end = date_from

        previous_aggregates = await self._analytics_repository.get_aggregate_by_user(
            user_id=user_uuid,
            start_date=previous_period_start,
            end_date=previous_period_end,
        )

        # Calculate days in period
        days_in_period = (date_to - date_from).days + 1

        # Build conversation trend
        total_conversations = aggregates["total_conversations"]
        avg_conversations = total_conversations / days_in_period if days_in_period > 0 else 0.0

        conversation_change = 0.0
        conversation_direction = "stable"
        if previous_aggregates["total_conversations"] > 0:
            conversation_change = (
                (total_conversations - previous_aggregates["total_conversations"])
                / previous_aggregates["total_conversations"]
                * 100
            )
            if conversation_change > 5:
                conversation_direction = "up"
            elif conversation_change < -5:
                conversation_direction = "down"

        conversation_trend = TrendDataSeries(
            label="Conversations",
            data_points=activity_points,
            total=total_conversations,
            average=avg_conversations,
            trend_direction=conversation_direction,
            change_percentage=conversation_change,
        )

        # Build message trend
        total_messages = aggregates["total_messages"]
        avg_messages = total_messages / days_in_period if days_in_period > 0 else 0.0

        message_change = 0.0
        message_direction = "stable"
        if previous_aggregates["total_messages"] > 0:
            message_change = (
                (total_messages - previous_aggregates["total_messages"])
                / previous_aggregates["total_messages"]
                * 100
            )
            if message_change > 5:
                message_direction = "up"
            elif message_change < -5:
                message_direction = "down"

        message_trend = TrendDataSeries(
            label="Messages",
            data_points=activity_points,
            total=total_messages,
            average=avg_messages,
            trend_direction=message_direction,
            change_percentage=message_change,
        )

        # Build cost trend
        total_cost = aggregates["total_cost_usd"]
        avg_cost = total_cost / days_in_period if days_in_period > 0 else 0.0

        cost_change = 0.0
        cost_direction = "stable"
        if previous_aggregates["total_cost_usd"] > 0:
            cost_change = (
                (total_cost - previous_aggregates["total_cost_usd"])
                / previous_aggregates["total_cost_usd"]
                * 100
            )
            if cost_change > 5:
                cost_direction = "up"
            elif cost_change < -5:
                cost_direction = "down"

        cost_trend = TrendDataSeries(
            label="Cost (USD)",
            data_points=activity_points,
            total=int(total_cost),  # Cast to int for total field
            average=avg_cost,
            trend_direction=cost_direction,
            change_percentage=cost_change,
        )

        # Find peak usage times (simplified - analyze daily data)
        peak_usage_times = []
        if daily_analytics:
            # Group by day of week and find top 2
            day_totals = {}
            for day_data in daily_analytics:
                date_obj = datetime.fromisoformat(day_data["date"])
                day_name = date_obj.strftime("%A")
                if day_name not in day_totals:
                    day_totals[day_name] = 0
                day_totals[day_name] += day_data["message_count"]

            # Get top 2 days
            sorted_days = sorted(day_totals.items(), key=lambda x: x[1], reverse=True)[:2]
            for day_name, total_messages in sorted_days:
                # Estimate activity score as percentage of max
                max_total = sorted_days[0][1] if sorted_days else 1
                activity_score = int((total_messages / max_total * 100)) if max_total > 0 else 0
                peak_usage_times.append({
                    "day": day_name,
                    "hour": 14,  # Default hour (would need hourly data from repository)
                    "activity_score": activity_score,
                })

        # Calculate activity consistency score (simplified)
        # Measure how consistent daily usage is - lower variance = higher consistency
        activity_consistency_score = 0.5  # Default
        if daily_analytics and len(daily_analytics) > 1:
            message_counts = [day["message_count"] for day in daily_analytics]
            avg_messages_per_day = sum(message_counts) / len(message_counts)

            if avg_messages_per_day > 0:
                # Calculate coefficient of variation (lower = more consistent)
                variance = sum((x - avg_messages_per_day) ** 2 for x in message_counts) / len(message_counts)
                std_dev = variance ** 0.5
                cv = std_dev / avg_messages_per_day

                # Convert to 0-1 score (lower CV = higher score)
                activity_consistency_score = max(0.0, min(1.0, 1.0 - cv))

        return HistoricalTrendsResponse(
            date_from=date_from,
            date_to=date_to,
            granularity=granularity,
            conversation_trend=conversation_trend,
            message_trend=message_trend,
            cost_trend=cost_trend,
            peak_usage_times=peak_usage_times,
            activity_consistency_score=activity_consistency_score,
            percentile_rank=None,  # Would need cross-user analytics for this
        )

    async def get_conversation_history(
        self,
        user_id: int,
        date_from: datetime,
        date_to: datetime,
        limit: int = 20,
    ) -> ConversationHistoryResponse:
        """
        Get conversation history analysis.

        Args:
            user_id: User identifier
            date_from: Start date
            date_to: End date
            limit: Max conversations to analyze

        Returns:
            Conversation history analysis
        """
        logger.info(f"Getting conversation history for user {user_id}")

        # Convert user_id to UUID
        user_uuid = UUID(int=user_id)

        # Get aggregated analytics
        aggregates = await self._analytics_repository.get_aggregate_by_user(
            user_id=user_uuid,
            start_date=date_from,
            end_date=date_to,
        )

        # Get agent usage stats for distribution
        agent_stats = await self._analytics_repository.get_agent_usage_stats(
            user_id=user_uuid,
            start_date=date_from,
            end_date=date_to,
        )

        # Get conversation analytics entities
        conversation_analytics = await self._analytics_repository.get_by_user(
            user_id=user_uuid,
            limit=limit * 2,  # Get more to filter and sort
            offset=0,
        )

        # Build conversation summaries
        conversations = []
        for analytics in conversation_analytics[:limit]:
            agents_used = list(analytics.agent_usage.keys()) if analytics.agent_usage else []

            duration_seconds = 0.0
            if analytics.first_message_at and analytics.last_message_at:
                duration = analytics.last_message_at - analytics.first_message_at
                duration_seconds = duration.total_seconds()

            # Determine primary topic from most used agent (simplified)
            primary_topic = None
            if analytics.agent_usage:
                primary_agent = max(analytics.agent_usage.items(), key=lambda x: x[1])[0]
                primary_topic = primary_agent.replace("_", " ").title()

            conversations.append(
                ConversationSummary(
                    conversation_id=analytics.conversation_id,
                    title=None,  # Would need conversation title tracking
                    created_at=analytics.created_at,
                    message_count=analytics.message_count,
                    duration_seconds=duration_seconds,
                    agents_used=agents_used,
                    primary_topic=primary_topic,
                    cost_usd=analytics.total_cost_usd,
                    completed=True,  # Simplified - would need completion tracking
                )
            )

        # Calculate average conversation duration
        total_conversations = aggregates["total_conversations"]
        avg_duration_seconds = aggregates.get("avg_duration_seconds", 0.0)
        avg_conversation_duration_minutes = avg_duration_seconds / 60.0

        # Build most common topics from agent usage
        most_common_topics = []
        agent_topic_map = {
            "risk_analyzer": "Risk Analysis",
            "security_auditor": "Security Auditing",
            "yield_optimizer": "Yield Optimization",
            "portfolio_manager": "Portfolio Management",
            "defi_strategist": "DeFi Strategy",
        }

        sorted_agents = sorted(
            agent_stats.items(),
            key=lambda x: x[1]["total_invocations"],
            reverse=True,
        )[:3]

        for agent_type, _ in sorted_agents:
            topic = agent_topic_map.get(agent_type, agent_type.replace("_", " ").title())
            most_common_topics.append(topic)

        # Build agent usage distribution
        agent_usage_distribution = {}
        for agent_type, stats in agent_stats.items():
            agent_usage_distribution[agent_type] = stats["total_invocations"]

        # Get completion rate
        completion_rate = aggregates.get("completion_rate", 0.87)

        # Find most productive conversations (high message count, good completion)
        most_productive = sorted(
            conversations,
            key=lambda x: x.message_count,
            reverse=True,
        )[:5]

        return ConversationHistoryResponse(
            date_from=date_from,
            date_to=date_to,
            conversations=conversations,
            total_conversations=total_conversations,
            avg_conversation_duration_minutes=avg_conversation_duration_minutes,
            most_common_topics=most_common_topics,
            agent_usage_distribution=agent_usage_distribution,
            completion_rate=completion_rate,
            avg_satisfaction_rating=None,  # Would need user ratings feature
            most_productive_conversations=most_productive,
        )

    async def export_user_analytics(
        self,
        user_id: int,
        date_from: datetime,
        date_to: datetime,
        export_format: str = "json",
        include_conversations: bool = False,
    ) -> UserExportDataResponse:
        """
        Export user analytics data.

        Args:
            user_id: User identifier
            date_from: Start date
            date_to: End date
            export_format: Export format
            include_conversations: Include full conversation data

        Returns:
            Exported analytics data
        """
        logger.info(f"Exporting analytics for user {user_id} in {export_format} format")

        # Convert user_id to UUID
        user_uuid = UUID(int=user_id)

        # Get all analytics data
        aggregates = await self._analytics_repository.get_aggregate_by_user(
            user_id=user_uuid,
            start_date=date_from,
            end_date=date_to,
        )

        agent_stats = await self._analytics_repository.get_agent_usage_stats(
            user_id=user_uuid,
            start_date=date_from,
            end_date=date_to,
        )

        cost_by_agent = await self._analytics_repository.get_cost_breakdown_by_agent(
            user_id=user_uuid,
            start_date=date_from,
            end_date=date_to,
        )

        daily_analytics = await self._analytics_repository.get_daily_analytics(
            user_id=user_uuid,
            start_date=date_from,
            end_date=date_to,
        )

        # Build comprehensive export data
        export_data = {
            "user_id": user_id,
            "export_metadata": {
                "date_from": date_from.isoformat(),
                "date_to": date_to.isoformat(),
                "format": export_format,
                "includes_conversations": include_conversations,
                "generated_at": datetime.now(UTC).isoformat(),
            },
            "summary": {
                "total_conversations": aggregates["total_conversations"],
                "total_messages": aggregates["total_messages"],
                "total_cost_usd": aggregates["total_cost_usd"],
                "most_used_agent": aggregates.get("most_used_agent", "none"),
                "avg_quality_score": aggregates.get("avg_quality_score", 0.0),
            },
            "agent_usage": {
                agent_type: {
                    "total_invocations": stats["total_invocations"],
                    "avg_success_rate": stats["avg_success_rate"],
                    "avg_execution_time_ms": stats["avg_execution_time_ms"],
                    "total_cost_usd": cost_by_agent.get(agent_type, 0.0),
                }
                for agent_type, stats in agent_stats.items()
            },
            "daily_metrics": [
                {
                    "date": day["date"],
                    "conversation_count": day["conversation_count"],
                    "message_count": day["message_count"],
                    "unique_agents": day.get("unique_agents", 0),
                    "total_cost": day.get("total_cost", 0.0),
                }
                for day in (daily_analytics or [])
            ],
        }

        # Include conversation data if requested
        record_count = aggregates["total_conversations"]
        if include_conversations:
            conversation_analytics = await self._analytics_repository.get_by_user(
                user_id=user_uuid,
                limit=1000,  # Max conversations to export
                offset=0,
            )

            export_data["conversations"] = [
                {
                    "conversation_id": str(conv.conversation_id),
                    "created_at": conv.created_at.isoformat(),
                    "message_count": conv.message_count,
                    "total_cost_usd": conv.total_cost_usd,
                    "agent_usage": conv.agent_usage,
                    "quality_score": conv.quality_score,
                }
                for conv in conversation_analytics
            ]
            record_count += len(conversation_analytics)

        # Calculate approximate file size (simplified)
        import json
        json_str = json.dumps(export_data)
        file_size_bytes = len(json_str.encode('utf-8'))

        return UserExportDataResponse(
            export_format=export_format,
            date_from=date_from,
            date_to=date_to,
            includes_conversations=include_conversations,
            data=export_data,
            generated_at=datetime.now(UTC),
            record_count=record_count,
            file_size_bytes=file_size_bytes,
            download_url=None,  # Would need file storage implementation
            expires_at=None,
        )
