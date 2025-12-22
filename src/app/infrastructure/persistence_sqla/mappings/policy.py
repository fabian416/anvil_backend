"""
SQLAlchemy mapping for Policy persistence (metadata + audit + cache).

We persist Privy policies locally to support:
- Historical audit: who created/updated what and when
- Cache: avoid repeated Privy calls by reading from DB first
- Advanced search: filter by custom metadata (JSONB)
"""

import sqlalchemy as sa
from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import mapped_column

from app.infrastructure.persistence_sqla.registry import mapping_registry


def map_policy_tables() -> None:
    """Map Policy tables to database metadata (idempotent)."""
    if "policies" in mapping_registry.metadata.tables:
        return

    @mapping_registry.mapped
    class PoliciesTable:
        __tablename__ = "policies"
        __table_args__ = {"extend_existing": True}

        # Privy policy id is a string, so we use it as the PK.
        id = mapped_column(String(255), primary_key=True)

        name = mapped_column(String(255), nullable=False, index=True)
        version = mapped_column(String(32), nullable=False)
        chain_type = mapped_column(String(32), nullable=False, index=True)

        owner_id = mapped_column(String(255), nullable=True, index=True)

        # Privy payload snapshots
        rules = mapped_column(JSONB, nullable=False, server_default=sa.text("'[]'::jsonb"))
        privy_raw = mapped_column(JSONB, nullable=True)

        # Custom, app-defined metadata (searchable)
        # NOTE: `metadata` is a reserved attribute name in SQLAlchemy Declarative.
        # We keep the DB column name as "metadata" but map it to a safe attribute name.
        metadata_ = mapped_column("metadata", JSONB, nullable=False, server_default=sa.text("'{}'::jsonb"))

        # Cache / sync tracking
        last_privy_sync_at = mapped_column(DateTime(timezone=True), nullable=True, index=True)

        # Soft delete (if a policy is removed upstream, we can keep history)
        is_deleted = mapped_column(sa.Boolean, nullable=False, server_default=sa.text("false"), index=True)

        # Audit (actor user id is our local user id)
        created_by_user_id = mapped_column(
            Integer,
            ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
            index=True,
        )
        updated_by_user_id = mapped_column(
            Integer,
            ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
            index=True,
        )

        created_at = mapped_column(
            DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
            index=True,
        )
        updated_at = mapped_column(
            DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            onupdate=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
            index=True,
        )

    @mapping_registry.mapped
    class PolicyAuditEventsTable:
        __tablename__ = "policy_audit_events"
        __table_args__ = {"extend_existing": True}

        id = mapped_column(Integer, primary_key=True, autoincrement=True)

        policy_id = mapped_column(
            String(255),
            ForeignKey("policies.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        )

        actor_user_id = mapped_column(
            Integer,
            ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
            index=True,
        )

        action = mapped_column(String(64), nullable=False, index=True)
        payload = mapped_column(JSONB, nullable=True)

        created_at = mapped_column(
            DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
            index=True,
        )

