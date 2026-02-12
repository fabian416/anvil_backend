"""
SQLAlchemy mapping for user_sync_schedule table.

Tracks incremental sync backoff for users active in the last 24 hours.
A Celery task runs every minute, syncs users where next_sync_at <= now(),
then advances next_sync_at by 1 -> 3 -> 6 -> 12 min.
"""

import sqlalchemy as sa
from sqlalchemy import DateTime, ForeignKey, Integer
from sqlalchemy.orm import mapped_column

from app.infrastructure.persistence_sqla.registry import mapping_registry


def map_user_sync_schedule_table() -> None:
    """Map user_sync_schedule table (idempotent)."""
    if "user_sync_schedule" in mapping_registry.metadata.tables:
        return

    @mapping_registry.mapped
    class UserSyncScheduleTable:
        __tablename__ = "user_sync_schedule"
        __table_args__ = (
            sa.Index("idx_user_sync_schedule_due", "next_sync_at"),
            {"extend_existing": True},
        )

        user_id = mapped_column(
            Integer,
            ForeignKey("users.id", ondelete="CASCADE"),
            primary_key=True,
        )
        next_sync_at = mapped_column(DateTime(timezone=True), nullable=False, index=True)
        interval_index = mapped_column(Integer, nullable=False, server_default="0")
        last_synced_at = mapped_column(DateTime(timezone=True), nullable=True)
        created_at = mapped_column(
            DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        )
        updated_at = mapped_column(
            DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        )
