"""Add audit logs table for compliance and security tracking

Revision ID: g8h9i0j1k2l3
Revises:
Create Date: 2025-12-16 00:01:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "g8h9i0j1k2l3"
down_revision: Union[str, None] = None  # Set this when running in production
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Create audit_logs table for compliance and security tracking.

    Includes optimized indexes for common query patterns:
    - User activity queries (user_id + created_at)
    - Event type queries with time range (event_type + created_at)
    - Security monitoring (event_type + outcome)
    - IP-based queries (ip_address + created_at)
    - Resource activity (resource_id + resource_type)
    """
    # Create audit_logs table
    op.create_table(
        "audit_logs",
        sa.Column("entry_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("event_type", sa.String(length=50), nullable=False),
        sa.Column("action", sa.String(length=200), nullable=False),
        sa.Column("outcome", sa.String(length=20), nullable=False),
        # Context
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("resource_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("resource_type", sa.String(length=50), nullable=True),
        # Additional Data
        sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("ip_address", sa.String(length=45), nullable=True),
        sa.Column("user_agent", sa.Text(), nullable=True),
        # Error details
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("error_code", sa.String(length=50), nullable=True),
        # Timestamp
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.PrimaryKeyConstraint("entry_id", name=op.f("pk_audit_logs")),
    )

    # Create single-column indexes
    op.create_index(
        op.f("ix_audit_logs_event_type"), "audit_logs", ["event_type"], unique=False
    )
    op.create_index(
        op.f("ix_audit_logs_outcome"), "audit_logs", ["outcome"], unique=False
    )
    op.create_index(
        op.f("ix_audit_logs_user_id"), "audit_logs", ["user_id"], unique=False
    )
    op.create_index(
        op.f("ix_audit_logs_resource_id"), "audit_logs", ["resource_id"], unique=False
    )
    op.create_index(
        op.f("ix_audit_logs_ip_address"), "audit_logs", ["ip_address"], unique=False
    )
    op.create_index(
        op.f("ix_audit_logs_created_at"), "audit_logs", ["created_at"], unique=False
    )

    # Create composite indexes for common query patterns
    # User activity queries
    op.create_index(
        "ix_audit_logs_user_created",
        "audit_logs",
        ["user_id", "created_at"],
        unique=False,
    )

    # Event type queries with time range
    op.create_index(
        "ix_audit_logs_event_created",
        "audit_logs",
        ["event_type", "created_at"],
        unique=False,
    )

    # Security monitoring
    op.create_index(
        "ix_audit_logs_event_outcome",
        "audit_logs",
        ["event_type", "outcome"],
        unique=False,
    )

    # IP-based queries
    op.create_index(
        "ix_audit_logs_ip_created",
        "audit_logs",
        ["ip_address", "created_at"],
        unique=False,
    )

    # Resource activity
    op.create_index(
        "ix_audit_logs_resource",
        "audit_logs",
        ["resource_id", "resource_type"],
        unique=False,
    )


def downgrade() -> None:
    """Drop audit_logs table and all indexes."""
    # Drop composite indexes
    op.drop_index("ix_audit_logs_resource", table_name="audit_logs")
    op.drop_index("ix_audit_logs_ip_created", table_name="audit_logs")
    op.drop_index("ix_audit_logs_event_outcome", table_name="audit_logs")
    op.drop_index("ix_audit_logs_event_created", table_name="audit_logs")
    op.drop_index("ix_audit_logs_user_created", table_name="audit_logs")

    # Drop single-column indexes
    op.drop_index(op.f("ix_audit_logs_created_at"), table_name="audit_logs")
    op.drop_index(op.f("ix_audit_logs_ip_address"), table_name="audit_logs")
    op.drop_index(op.f("ix_audit_logs_resource_id"), table_name="audit_logs")
    op.drop_index(op.f("ix_audit_logs_user_id"), table_name="audit_logs")
    op.drop_index(op.f("ix_audit_logs_outcome"), table_name="audit_logs")
    op.drop_index(op.f("ix_audit_logs_event_type"), table_name="audit_logs")

    # Drop table
    op.drop_table("audit_logs")
