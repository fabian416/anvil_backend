"""
Analytics repository adapter implementation.

SQLAlchemy implementation of AnalyticsRepository port for PostgreSQL.
"""

from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime, timedelta

from sqlalchemy import select, func, and_, case, cast
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.postgresql import UUID as PGUUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, Integer, Float, DateTime, Index

from app.domain.ports.analytics_repository import AnalyticsRepository
from app.domain.entities.chat.conversation_analytics import ConversationAnalytics
from app.infrastructure.persistence_sqla.base import Base


class AnalyticsRepositoryAdapter(AnalyticsRepository):
    """
    SQLAlchemy adapter for conversation analytics.

    Implements persistence and aggregation for conversation analytics
    using PostgreSQL with JSONB for flexible data storage.
    """

    def __init__(self, session: AsyncSession) -> None:
        """
        Initialize repository adapter.

        Args:
            session: SQLAlchemy async session
        """
        self._session = session

    async def save(self, analytics: ConversationAnalytics) -> ConversationAnalytics:
        """
        Save or update analytics record.

        Args:
            analytics: Analytics entity to save

        Returns:
            Saved analytics entity
        """
        try:
            stmt = select(ConversationAnalyticsModel).where(
                ConversationAnalyticsModel.analytics_id == analytics.id
            )
            result = await self._session.execute(stmt)
            existing = result.scalar_one_or_none()

            if existing:
                self._update_model(existing, analytics)
            else:
                model = self._to_model(analytics)
                self._session.add(model)

            await self._session.commit()
            return analytics

        except Exception:
            await self._session.rollback()
            raise

    async def get_by_id(self, analytics_id: UUID) -> Optional[ConversationAnalytics]:
        """
        Get analytics by ID.

        Args:
            analytics_id: Analytics identifier

        Returns:
            ConversationAnalytics or None if not found
        """
        stmt = select(ConversationAnalyticsModel).where(
            ConversationAnalyticsModel.analytics_id == analytics_id
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()

        if not model:
            return None

        return self._to_domain(model)

    async def get_by_conversation(
        self, conversation_id: UUID
    ) -> Optional[ConversationAnalytics]:
        """
        Get analytics for a conversation.

        Args:
            conversation_id: Conversation identifier

        Returns:
            ConversationAnalytics or None if not found
        """
        stmt = select(ConversationAnalyticsModel).where(
            ConversationAnalyticsModel.conversation_id == conversation_id
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()

        if not model:
            return None

        return self._to_domain(model)

    async def get_by_user(
        self,
        user_id: UUID,
        limit: int = 50,
        offset: int = 0,
    ) -> List[ConversationAnalytics]:
        """
        Get analytics for user's conversations.

        Args:
            user_id: User identifier
            limit: Maximum number of records to return
            offset: Number of records to skip

        Returns:
            List of analytics records (most recent first)
        """
        stmt = (
            select(ConversationAnalyticsModel)
            .where(ConversationAnalyticsModel.user_id == user_id)
            .order_by(ConversationAnalyticsModel.updated_at.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await self._session.execute(stmt)
        models = result.scalars().all()

        return [self._to_domain(model) for model in models]

    async def get_by_user_date_range(
        self,
        user_id: UUID,
        start_date: datetime,
        end_date: datetime,
    ) -> List[ConversationAnalytics]:
        """
        Get analytics for user within date range.

        Args:
            user_id: User identifier
            start_date: Start of date range (inclusive)
            end_date: End of date range (inclusive)

        Returns:
            List of analytics records in date range
        """
        stmt = (
            select(ConversationAnalyticsModel)
            .where(
                and_(
                    ConversationAnalyticsModel.user_id == user_id,
                    ConversationAnalyticsModel.created_at >= start_date,
                    ConversationAnalyticsModel.created_at <= end_date,
                )
            )
            .order_by(ConversationAnalyticsModel.created_at.desc())
        )
        result = await self._session.execute(stmt)
        models = result.scalars().all()

        return [self._to_domain(model) for model in models]

    async def get_aggregate_by_user(
        self,
        user_id: UUID,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """
        Get aggregated analytics for a user.

        Args:
            user_id: User identifier
            start_date: Optional start date for filtering
            end_date: Optional end date for filtering

        Returns:
            Dictionary with aggregated metrics
        """
        # Build filter conditions
        conditions = [ConversationAnalyticsModel.user_id == user_id]
        if start_date:
            conditions.append(ConversationAnalyticsModel.created_at >= start_date)
        if end_date:
            conditions.append(ConversationAnalyticsModel.created_at <= end_date)

        # Aggregate query
        stmt = select(
            func.count(ConversationAnalyticsModel.analytics_id).label(
                "total_conversations"
            ),
            func.sum(ConversationAnalyticsModel.message_count).label("total_messages"),
            func.sum(ConversationAnalyticsModel.total_cost_usd).label("total_cost_usd"),
            func.avg(ConversationAnalyticsModel.message_count).label(
                "avg_messages_per_conversation"
            ),
            func.avg(ConversationAnalyticsModel.avg_response_time_ms).label(
                "avg_response_time_ms"
            ),
            func.avg(ConversationAnalyticsModel.sentiment_score).label(
                "avg_sentiment_score"
            ),
            func.avg(ConversationAnalyticsModel.quality_score).label("avg_quality_score"),
            func.sum(ConversationAnalyticsModel.total_tokens_used).label(
                "total_tokens_used"
            ),
        ).where(and_(*conditions))

        result = await self._session.execute(stmt)
        row = result.first()

        if not row:
            return {
                "total_conversations": 0,
                "total_messages": 0,
                "total_cost_usd": 0.0,
                "avg_messages_per_conversation": 0.0,
                "avg_response_time_ms": 0.0,
                "avg_sentiment_score": 0.0,
                "avg_quality_score": 0.0,
                "total_tokens_used": 0,
                "most_used_agent": None,
                "agent_usage_summary": {},
            }

        # Get agent usage summary
        agent_summary = await self.get_agent_usage_stats(user_id, start_date, end_date)

        # Find most used agent
        most_used_agent = None
        if agent_summary:
            most_used_agent = max(
                agent_summary.items(),
                key=lambda x: x[1]["total_invocations"],
            )[0]

        return {
            "total_conversations": row.total_conversations or 0,
            "total_messages": row.total_messages or 0,
            "total_cost_usd": float(row.total_cost_usd or 0.0),
            "avg_messages_per_conversation": float(
                row.avg_messages_per_conversation or 0.0
            ),
            "avg_response_time_ms": float(row.avg_response_time_ms or 0.0),
            "avg_sentiment_score": float(row.avg_sentiment_score or 0.0),
            "avg_quality_score": float(row.avg_quality_score or 0.0),
            "total_tokens_used": row.total_tokens_used or 0,
            "most_used_agent": most_used_agent,
            "agent_usage_summary": agent_summary,
        }

    async def get_aggregate_by_date_range(
        self,
        start_date: datetime,
        end_date: datetime,
        user_id: Optional[UUID] = None,
    ) -> Dict[str, Any]:
        """
        Get aggregated analytics for a date range.

        Args:
            start_date: Start of date range (inclusive)
            end_date: End of date range (inclusive)
            user_id: Optional user filter

        Returns:
            Dictionary with aggregated metrics for the time period
        """
        conditions = [
            ConversationAnalyticsModel.created_at >= start_date,
            ConversationAnalyticsModel.created_at <= end_date,
        ]
        if user_id:
            conditions.append(ConversationAnalyticsModel.user_id == user_id)

        stmt = select(
            func.count(ConversationAnalyticsModel.analytics_id).label(
                "total_conversations"
            ),
            func.sum(ConversationAnalyticsModel.message_count).label("total_messages"),
            func.sum(ConversationAnalyticsModel.total_cost_usd).label("total_cost_usd"),
            func.avg(ConversationAnalyticsModel.avg_response_time_ms).label(
                "avg_response_time_ms"
            ),
            func.avg(ConversationAnalyticsModel.sentiment_score).label(
                "avg_sentiment_score"
            ),
            func.sum(ConversationAnalyticsModel.total_tokens_used).label(
                "total_tokens_used"
            ),
        ).where(and_(*conditions))

        result = await self._session.execute(stmt)
        row = result.first()

        if not row:
            return {
                "total_conversations": 0,
                "total_messages": 0,
                "total_cost_usd": 0.0,
                "avg_response_time_ms": 0.0,
                "avg_sentiment_score": 0.0,
                "total_tokens_used": 0,
            }

        return {
            "total_conversations": row.total_conversations or 0,
            "total_messages": row.total_messages or 0,
            "total_cost_usd": float(row.total_cost_usd or 0.0),
            "avg_response_time_ms": float(row.avg_response_time_ms or 0.0),
            "avg_sentiment_score": float(row.avg_sentiment_score or 0.0),
            "total_tokens_used": row.total_tokens_used or 0,
        }

    async def get_top_conversations_by_cost(
        self,
        limit: int = 10,
        user_id: Optional[UUID] = None,
        start_date: Optional[datetime] = None,
    ) -> List[ConversationAnalytics]:
        """
        Get conversations with highest costs.

        Args:
            limit: Maximum number of conversations to return
            user_id: Optional user filter
            start_date: Optional start date filter

        Returns:
            List of analytics records ordered by cost (highest first)
        """
        conditions = []
        if user_id:
            conditions.append(ConversationAnalyticsModel.user_id == user_id)
        if start_date:
            conditions.append(ConversationAnalyticsModel.created_at >= start_date)

        stmt = (
            select(ConversationAnalyticsModel)
            .where(and_(*conditions) if conditions else True)
            .order_by(ConversationAnalyticsModel.total_cost_usd.desc())
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        models = result.scalars().all()

        return [self._to_domain(model) for model in models]

    async def get_top_conversations_by_messages(
        self,
        limit: int = 10,
        user_id: Optional[UUID] = None,
        start_date: Optional[datetime] = None,
    ) -> List[ConversationAnalytics]:
        """
        Get conversations with most messages.

        Args:
            limit: Maximum number of conversations to return
            user_id: Optional user filter
            start_date: Optional start date filter

        Returns:
            List of analytics records ordered by message count (highest first)
        """
        conditions = []
        if user_id:
            conditions.append(ConversationAnalyticsModel.user_id == user_id)
        if start_date:
            conditions.append(ConversationAnalyticsModel.created_at >= start_date)

        stmt = (
            select(ConversationAnalyticsModel)
            .where(and_(*conditions) if conditions else True)
            .order_by(ConversationAnalyticsModel.message_count.desc())
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        models = result.scalars().all()

        return [self._to_domain(model) for model in models]

    async def get_conversations_by_quality_score(
        self,
        min_score: float,
        max_score: float,
        user_id: Optional[UUID] = None,
        limit: int = 50,
    ) -> List[ConversationAnalytics]:
        """
        Get conversations within quality score range.

        Args:
            min_score: Minimum quality score (0.0 to 1.0)
            max_score: Maximum quality score (0.0 to 1.0)
            user_id: Optional user filter
            limit: Maximum number of conversations to return

        Returns:
            List of analytics records within quality range
        """
        conditions = [
            ConversationAnalyticsModel.quality_score >= min_score,
            ConversationAnalyticsModel.quality_score <= max_score,
            ConversationAnalyticsModel.quality_score.isnot(None),
        ]
        if user_id:
            conditions.append(ConversationAnalyticsModel.user_id == user_id)

        stmt = (
            select(ConversationAnalyticsModel)
            .where(and_(*conditions))
            .order_by(ConversationAnalyticsModel.quality_score.desc())
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        models = result.scalars().all()

        return [self._to_domain(model) for model in models]

    async def get_agent_usage_stats(
        self,
        user_id: Optional[UUID] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> Dict[str, Dict[str, Any]]:
        """
        Get aggregated agent usage statistics.

        Args:
            user_id: Optional user filter
            start_date: Optional start date filter
            end_date: Optional end date filter

        Returns:
            Dictionary mapping agent names to usage stats
        """
        conditions = []
        if user_id:
            conditions.append(ConversationAnalyticsModel.user_id == user_id)
        if start_date:
            conditions.append(ConversationAnalyticsModel.created_at >= start_date)
        if end_date:
            conditions.append(ConversationAnalyticsModel.created_at <= end_date)

        # Get all analytics records matching criteria
        stmt = select(ConversationAnalyticsModel).where(
            and_(*conditions) if conditions else True
        )
        result = await self._session.execute(stmt)
        models = result.scalars().all()

        # Aggregate agent usage across all conversations
        agent_stats: Dict[str, Dict[str, Any]] = {}

        for model in models:
            if not model.agent_usage:
                continue

            for agent_name, usage_data in model.agent_usage.items():
                if agent_name not in agent_stats:
                    agent_stats[agent_name] = {
                        "total_invocations": 0,
                        "total_execution_time": 0.0,
                        "total_success_rate": 0.0,
                        "total_conversations": 0,
                        "conversation_count": 0,
                    }

                stats = agent_stats[agent_name]
                invocations = usage_data.get("invocations", 0)
                avg_time = usage_data.get("avg_time_ms", 0.0)
                success_rate = usage_data.get("success_rate", 0.0)

                stats["total_invocations"] += invocations
                stats["total_execution_time"] += avg_time * invocations
                stats["total_success_rate"] += success_rate
                stats["conversation_count"] += 1

        # Calculate averages
        for agent_name, stats in agent_stats.items():
            total_invocations = stats["total_invocations"]
            conversation_count = stats["conversation_count"]

            agent_stats[agent_name] = {
                "total_invocations": total_invocations,
                "avg_execution_time_ms": (
                    stats["total_execution_time"] / total_invocations
                    if total_invocations > 0
                    else 0.0
                ),
                "avg_success_rate": (
                    stats["total_success_rate"] / conversation_count
                    if conversation_count > 0
                    else 0.0
                ),
                "total_conversations": conversation_count,
            }

        return agent_stats

    async def get_cost_breakdown_by_agent(
        self,
        user_id: Optional[UUID] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> Dict[str, float]:
        """
        Get cost breakdown by agent.

        Args:
            user_id: Optional user filter
            start_date: Optional start date filter
            end_date: Optional end date filter

        Returns:
            Dictionary mapping agent names to total costs in USD
        """
        conditions = []
        if user_id:
            conditions.append(ConversationAnalyticsModel.user_id == user_id)
        if start_date:
            conditions.append(ConversationAnalyticsModel.created_at >= start_date)
        if end_date:
            conditions.append(ConversationAnalyticsModel.created_at <= end_date)

        # Get all analytics records matching criteria
        stmt = select(ConversationAnalyticsModel).where(
            and_(*conditions) if conditions else True
        )
        result = await self._session.execute(stmt)
        models = result.scalars().all()

        # Aggregate costs by agent
        cost_by_agent: Dict[str, float] = {}

        for model in models:
            if not model.cost_by_agent:
                continue

            for agent_name, cost in model.cost_by_agent.items():
                if agent_name not in cost_by_agent:
                    cost_by_agent[agent_name] = 0.0
                cost_by_agent[agent_name] += cost

        return cost_by_agent

    async def get_daily_analytics(
        self,
        user_id: UUID,
        start_date: datetime,
        end_date: datetime,
    ) -> List[Dict[str, Any]]:
        """
        Get daily aggregated analytics for user.

        Args:
            user_id: User identifier
            start_date: Start of date range (inclusive)
            end_date: End of date range (inclusive)

        Returns:
            List of daily analytics dictionaries
        """
        # Use date truncation for daily grouping
        date_trunc = func.date_trunc("day", ConversationAnalyticsModel.created_at)

        stmt = (
            select(
                date_trunc.label("date"),
                func.count(ConversationAnalyticsModel.analytics_id).label(
                    "conversation_count"
                ),
                func.sum(ConversationAnalyticsModel.message_count).label("message_count"),
                func.sum(ConversationAnalyticsModel.total_cost_usd).label(
                    "total_cost_usd"
                ),
                func.avg(ConversationAnalyticsModel.avg_response_time_ms).label(
                    "avg_response_time_ms"
                ),
                func.avg(ConversationAnalyticsModel.sentiment_score).label(
                    "avg_sentiment_score"
                ),
            )
            .where(
                and_(
                    ConversationAnalyticsModel.user_id == user_id,
                    ConversationAnalyticsModel.created_at >= start_date,
                    ConversationAnalyticsModel.created_at <= end_date,
                )
            )
            .group_by(date_trunc)
            .order_by(date_trunc)
        )

        result = await self._session.execute(stmt)
        rows = result.all()

        return [
            {
                "date": row.date.strftime("%Y-%m-%d"),
                "conversation_count": row.conversation_count or 0,
                "message_count": row.message_count or 0,
                "total_cost_usd": float(row.total_cost_usd or 0.0),
                "avg_response_time_ms": float(row.avg_response_time_ms or 0.0),
                "avg_sentiment_score": float(row.avg_sentiment_score or 0.0),
            }
            for row in rows
        ]

    async def delete(self, analytics_id: UUID) -> bool:
        """
        Delete analytics record.

        Args:
            analytics_id: Analytics identifier

        Returns:
            True if deleted, False if not found
        """
        try:
            stmt = select(ConversationAnalyticsModel).where(
                ConversationAnalyticsModel.analytics_id == analytics_id
            )
            result = await self._session.execute(stmt)
            model = result.scalar_one_or_none()

            if model:
                await self._session.delete(model)
                await self._session.commit()
                return True

            return False

        except Exception:
            await self._session.rollback()
            return False

    async def delete_by_conversation(self, conversation_id: UUID) -> bool:
        """
        Delete analytics for a conversation.

        Args:
            conversation_id: Conversation identifier

        Returns:
            True if deleted, False if not found
        """
        try:
            stmt = select(ConversationAnalyticsModel).where(
                ConversationAnalyticsModel.conversation_id == conversation_id
            )
            result = await self._session.execute(stmt)
            model = result.scalar_one_or_none()

            if model:
                await self._session.delete(model)
                await self._session.commit()
                return True

            return False

        except Exception:
            await self._session.rollback()
            return False

    async def delete_old_analytics(self, days_to_keep: int = 90) -> int:
        """
        Delete analytics older than specified days.

        Args:
            days_to_keep: Number of days of analytics to retain

        Returns:
            Number of analytics records deleted
        """
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)

            stmt = select(ConversationAnalyticsModel).where(
                ConversationAnalyticsModel.created_at < cutoff_date
            )
            result = await self._session.execute(stmt)
            models = result.scalars().all()

            count = len(models)
            for model in models:
                await self._session.delete(model)

            await self._session.commit()
            return count

        except Exception:
            await self._session.rollback()
            return 0

    # =========================================================================
    # CONVERSION METHODS
    # =========================================================================

    def _to_domain(
        self, model: "ConversationAnalyticsModel"
    ) -> ConversationAnalytics:
        """
        Convert database model to domain entity.

        Args:
            model: Database model

        Returns:
            ConversationAnalytics domain entity
        """
        return ConversationAnalytics(
            id=model.analytics_id,
            conversation_id=model.conversation_id,
            user_id=model.user_id,
            message_count=model.message_count,
            user_message_count=model.user_message_count,
            agent_message_count=model.agent_message_count,
            agent_usage=model.agent_usage or {},
            avg_response_time_ms=model.avg_response_time_ms,
            median_response_time_ms=model.median_response_time_ms,
            p95_response_time_ms=model.p95_response_time_ms,
            min_response_time_ms=model.min_response_time_ms,
            max_response_time_ms=model.max_response_time_ms,
            total_cost_usd=model.total_cost_usd,
            avg_cost_per_message=model.avg_cost_per_message,
            cost_by_agent=model.cost_by_agent or {},
            sentiment_score=model.sentiment_score,
            quality_score=model.quality_score,
            user_satisfaction_score=model.user_satisfaction_score,
            total_tokens_used=model.total_tokens_used,
            input_tokens=model.input_tokens,
            output_tokens=model.output_tokens,
            first_message_at=model.first_message_at,
            last_message_at=model.last_message_at,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    def _to_model(
        self, analytics: ConversationAnalytics
    ) -> "ConversationAnalyticsModel":
        """
        Convert domain entity to database model.

        Args:
            analytics: Domain entity

        Returns:
            Database model
        """
        return ConversationAnalyticsModel(
            analytics_id=analytics.id,
            conversation_id=analytics.conversation_id,
            user_id=analytics.user_id,
            message_count=analytics.message_count,
            user_message_count=analytics.user_message_count,
            agent_message_count=analytics.agent_message_count,
            agent_usage=analytics.agent_usage,
            avg_response_time_ms=analytics.avg_response_time_ms,
            median_response_time_ms=analytics.median_response_time_ms,
            p95_response_time_ms=analytics.p95_response_time_ms,
            min_response_time_ms=analytics.min_response_time_ms,
            max_response_time_ms=analytics.max_response_time_ms,
            total_cost_usd=analytics.total_cost_usd,
            avg_cost_per_message=analytics.avg_cost_per_message,
            cost_by_agent=analytics.cost_by_agent,
            sentiment_score=analytics.sentiment_score,
            quality_score=analytics.quality_score,
            user_satisfaction_score=analytics.user_satisfaction_score,
            total_tokens_used=analytics.total_tokens_used,
            input_tokens=analytics.input_tokens,
            output_tokens=analytics.output_tokens,
            first_message_at=analytics.first_message_at,
            last_message_at=analytics.last_message_at,
            created_at=analytics.created_at,
            updated_at=analytics.updated_at,
        )

    def _update_model(
        self,
        model: "ConversationAnalyticsModel",
        analytics: ConversationAnalytics,
    ) -> None:
        """
        Update database model from domain entity.

        Args:
            model: Database model to update
            analytics: Domain entity
        """
        model.message_count = analytics.message_count
        model.user_message_count = analytics.user_message_count
        model.agent_message_count = analytics.agent_message_count
        model.agent_usage = analytics.agent_usage
        model.avg_response_time_ms = analytics.avg_response_time_ms
        model.median_response_time_ms = analytics.median_response_time_ms
        model.p95_response_time_ms = analytics.p95_response_time_ms
        model.min_response_time_ms = analytics.min_response_time_ms
        model.max_response_time_ms = analytics.max_response_time_ms
        model.total_cost_usd = analytics.total_cost_usd
        model.avg_cost_per_message = analytics.avg_cost_per_message
        model.cost_by_agent = analytics.cost_by_agent
        model.sentiment_score = analytics.sentiment_score
        model.quality_score = analytics.quality_score
        model.user_satisfaction_score = analytics.user_satisfaction_score
        model.total_tokens_used = analytics.total_tokens_used
        model.input_tokens = analytics.input_tokens
        model.output_tokens = analytics.output_tokens
        model.first_message_at = analytics.first_message_at
        model.last_message_at = analytics.last_message_at
        model.updated_at = analytics.updated_at


# =============================================================================
# DATABASE MODEL
# =============================================================================


class ConversationAnalyticsModel(Base):
    """
    SQLAlchemy model for conversation analytics.

    Maps to 'conversation_analytics' table in PostgreSQL.
    Uses JSONB for flexible agent usage and cost data storage.
    """

    __tablename__ = "conversation_analytics"

    analytics_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True)
    conversation_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), nullable=False, unique=True, index=True
    )
    user_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False, index=True)

    # Message metrics
    message_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    user_message_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    agent_message_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # Agent usage (JSONB)
    agent_usage: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)

    # Response time metrics (milliseconds)
    avg_response_time_ms: Mapped[float | None] = mapped_column(Float, nullable=True)
    median_response_time_ms: Mapped[float | None] = mapped_column(Float, nullable=True)
    p95_response_time_ms: Mapped[float | None] = mapped_column(Float, nullable=True)
    min_response_time_ms: Mapped[float | None] = mapped_column(Float, nullable=True)
    max_response_time_ms: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Cost metrics (USD)
    total_cost_usd: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    avg_cost_per_message: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    cost_by_agent: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)

    # Quality metrics (0.0 to 1.0)
    sentiment_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    quality_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    user_satisfaction_score: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Token usage
    total_tokens_used: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    input_tokens: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    output_tokens: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # Timestamps
    first_message_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    last_message_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    # Indexes for common queries
    __table_args__ = (
        Index("idx_analytics_user_created", "user_id", "created_at"),
        Index("idx_analytics_user_cost", "user_id", "total_cost_usd"),
        Index("idx_analytics_user_messages", "user_id", "message_count"),
        Index("idx_analytics_quality_score", "quality_score"),
        Index("idx_analytics_created_at", "created_at"),
    )
