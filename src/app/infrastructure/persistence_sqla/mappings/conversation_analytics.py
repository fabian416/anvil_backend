"""
SQLAlchemy mapping for conversation analytics table metadata.

NOTE:
This model is used by the chat analytics repositories for both user and admin
dashboards. It must be registered at application startup (via `map_tables()`)
so `metadata.create_all()` can create the table in local/dev environments.
"""

from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, Float, Index, Integer
from sqlalchemy.dialects.postgresql import JSONB, UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.persistence_sqla.registry import mapping_registry


@mapping_registry.mapped
class ConversationAnalyticsModel:
    """
    SQLAlchemy model for conversation analytics.

    Maps to 'conversation_analytics' table in PostgreSQL.
    Uses JSONB for flexible agent usage and cost data storage.
    """

    __tablename__ = "conversation_analytics"
    __table_args__ = (
        Index("idx_analytics_user_created", "user_id", "created_at"),
        Index("idx_analytics_user_cost", "user_id", "total_cost_usd"),
        Index("idx_analytics_user_messages", "user_id", "message_count"),
        Index("idx_analytics_quality_score", "quality_score"),
        Index("idx_analytics_created_at", "created_at"),
    )

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


def map_conversation_analytics_table() -> None:
    """Register conversation analytics table mapping (idempotent)."""
    # Import side-effect above already registers the model; keep this for consistency
    # with other mapping modules and for `map_tables()` usage.
    return


