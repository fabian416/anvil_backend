"""
SQLAlchemy mapping for hl_spot_tokens table.

Catalog of ALL Hyperliquid spot tokens with sentiment enrichment.
Seeded every 24h from spotMeta API; sentiment enriched every 1 min (rotating).
"""

from sqlalchemy import String, Numeric, DateTime, Integer, Boolean
from sqlalchemy.orm import mapped_column
import sqlalchemy as sa

from app.infrastructure.persistence_sqla.registry import mapping_registry


def map_hl_spot_tokens_table() -> None:
    """Map hl_spot_tokens table (idempotent)."""
    if "hl_spot_tokens" in mapping_registry.metadata.tables:
        return

    @mapping_registry.mapped
    class HlSpotTokensTable:
        """
        Table metadata for hl_spot_tokens.

        NOT mapped to a domain entity — Celery tasks use raw SQL
        for upserts and rotation queries (CQRS pattern).
        """

        __tablename__ = "hl_spot_tokens"
        __table_args__ = (
            sa.Index(
                "idx_hl_spot_tokens_enrich_rotation",
                "status",
                "sentiment_updated_at",
            ),
            sa.Index("idx_hl_spot_tokens_name", "name"),
            {"extend_existing": True},
        )

        id = mapped_column(Integer, primary_key=True, autoincrement=True)
        name = mapped_column(String(30), nullable=False, unique=True)
        token_id = mapped_column(String(66), nullable=False)
        token_index = mapped_column(Integer, nullable=False)
        sz_decimals = mapped_column(Integer, nullable=False, server_default="0")
        wei_decimals = mapped_column(Integer, nullable=False, server_default="18")
        is_canonical = mapped_column(
            Boolean, nullable=False, server_default="false"
        )
        status = mapped_column(
            String(20), nullable=False, server_default="pending", index=True
        )
        # Sentiment fields
        sentiment_score = mapped_column(Numeric(5, 1), nullable=True)
        sentiment_classification = mapped_column(String(20), nullable=True)
        sentiment_interpretation = mapped_column(String(50), nullable=True)
        sentiment_confidence = mapped_column(Numeric(4, 2), nullable=True)
        sentiment_source = mapped_column(String(30), nullable=True)
        sentiment_time_horizon = mapped_column(String(10), nullable=True)
        # Timestamps
        created_at = mapped_column(
            DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        )
        updated_at = mapped_column(
            DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        )
        sentiment_updated_at = mapped_column(
            DateTime(timezone=True), nullable=True
        )
