"""Add projects system

Revision ID: 20251201_002
Revises: 20251201_001
Create Date: 2025-12-01 10:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "20251201_002"
down_revision: Union[str, None] = "20251201_001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade database schema - Add Projects System."""

    # ===================================================================
    # TABLE 1: projects
    # ===================================================================
    op.create_table(
        "projects",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("uuid_generate_v4()"),
        ),
        sa.Column("slug", sa.String(50), nullable=False, unique=True),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("description", sa.Text),
        # Branding
        sa.Column("icon", sa.String(50)),
        sa.Column("color", sa.String(7)),
        sa.Column("banner_url", sa.Text),
        # Status
        sa.Column("status", sa.String(20), nullable=False, server_default="draft"),
        sa.Column("visibility", sa.String(20), nullable=False, server_default="public"),
        # System Prompt
        sa.Column("system_prompt", sa.Text, nullable=False),
        sa.Column("welcome_message", sa.Text),
        # DeFi Configuration
        sa.Column("enabled_protocols", postgresql.ARRAY(sa.Text), server_default="{}"),
        sa.Column("enabled_chains", postgresql.ARRAY(sa.Text), server_default="{}"),
        sa.Column("enabled_tools", postgresql.ARRAY(sa.Text), server_default="{}"),
        # Risk Configuration
        sa.Column("risk_config", postgresql.JSONB, server_default="{}"),
        # User limits
        sa.Column("max_users", sa.Integer),
        # Display order
        sa.Column("display_order", sa.Integer, server_default="0"),
        sa.Column("is_featured", sa.Boolean, server_default="false"),
        # Audit
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("NOW()")
        ),
        sa.Column(
            "updated_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("NOW()")
        ),
        sa.CheckConstraint(
            "status IN ('draft', 'active', 'paused', 'archived')", name="valid_status"
        ),
        sa.CheckConstraint(
            "visibility IN ('public', 'private', 'invite_only')",
            name="valid_visibility",
        ),
    )

    op.create_index(
        "idx_projects_status",
        "projects",
        ["status"],
        postgresql_where=sa.text("status = 'active'"),
    )
    op.create_index("idx_projects_slug", "projects", ["slug"])

    # ===================================================================
    # TABLE 2: project_knowledge_bases
    # ===================================================================
    op.create_table(
        "project_knowledge_bases",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("uuid_generate_v4()"),
        ),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), nullable=False),
        # Configuration
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("description", sa.Text),
        # Embedding settings
        sa.Column(
            "embedding_model", sa.String(100), server_default="text-embedding-3-small"
        ),
        sa.Column("chunk_size", sa.Integer, server_default="500"),
        sa.Column("chunk_overlap", sa.Integer, server_default="50"),
        # Statistics
        sa.Column("total_documents", sa.Integer, server_default="0"),
        sa.Column("total_chunks", sa.Integer, server_default="0"),
        # Status
        sa.Column("status", sa.String(20), server_default="active"),
        sa.Column("last_indexed_at", sa.TIMESTAMP(timezone=True)),
        sa.Column(
            "created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("NOW()")
        ),
        sa.Column(
            "updated_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("NOW()")
        ),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("project_id"),
    )

    # ===================================================================
    # TABLE 3: project_knowledge_documents
    # ===================================================================
    op.create_table(
        "project_knowledge_documents",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("uuid_generate_v4()"),
        ),
        sa.Column("knowledge_base_id", postgresql.UUID(as_uuid=True), nullable=False),
        # Content
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("content", sa.Text, nullable=False),
        sa.Column("doc_type", sa.String(50), nullable=False),
        # Source
        sa.Column("source_url", sa.Text),
        sa.Column("source_type", sa.String(50), server_default="manual"),
        # Metadata
        sa.Column("tags", postgresql.ARRAY(sa.Text), server_default="{}"),
        sa.Column("priority", sa.Integer, server_default="1"),
        # Processing status
        sa.Column("is_processed", sa.Boolean, server_default="false"),
        sa.Column("chunk_count", sa.Integer, server_default="0"),
        sa.Column("processing_error", sa.Text),
        sa.Column(
            "created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("NOW()")
        ),
        sa.Column(
            "updated_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("NOW()")
        ),
        sa.ForeignKeyConstraint(
            ["knowledge_base_id"], ["project_knowledge_bases.id"], ondelete="CASCADE"
        ),
        sa.CheckConstraint(
            "doc_type IN ('guide', 'faq', 'reference', 'data', 'announcement')",
            name="valid_doc_type",
        ),
    )

    op.create_index(
        "idx_knowledge_docs_kb", "project_knowledge_documents", ["knowledge_base_id"]
    )

    # ===================================================================
    # TABLE 4: project_knowledge_chunks
    # ===================================================================
    op.create_table(
        "project_knowledge_chunks",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("uuid_generate_v4()"),
        ),
        sa.Column("document_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("knowledge_base_id", postgresql.UUID(as_uuid=True), nullable=False),
        # Content
        sa.Column("chunk_text", sa.Text, nullable=False),
        sa.Column("chunk_index", sa.Integer, nullable=False),
        # Embedding (placeholder, will be converted to vector)
        sa.Column("embedding", postgresql.ARRAY(sa.Float)),
        # Metadata
        sa.Column("metadata", postgresql.JSONB, server_default="{}"),
        sa.Column(
            "created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("NOW()")
        ),
        sa.ForeignKeyConstraint(
            ["document_id"], ["project_knowledge_documents.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["knowledge_base_id"], ["project_knowledge_bases.id"], ondelete="CASCADE"
        ),
    )

    # Convert embedding column to vector type
    op.execute(
        "ALTER TABLE project_knowledge_chunks ALTER COLUMN embedding TYPE vector(1536) USING embedding::vector(1536)"
    )

    # Create vector index
    op.execute("""
        CREATE INDEX idx_knowledge_chunks_embedding ON project_knowledge_chunks
        USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100)
    """)

    op.create_index(
        "idx_knowledge_chunks_kb", "project_knowledge_chunks", ["knowledge_base_id"]
    )

    # ===================================================================
    # TABLE 5: project_tool_configs
    # ===================================================================
    op.create_table(
        "project_tool_configs",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("uuid_generate_v4()"),
        ),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tool_id", sa.String(50), nullable=False),
        # Enablement
        sa.Column("is_enabled", sa.Boolean, server_default="true"),
        # Restrictions
        sa.Column("max_calls_per_session", sa.Integer),
        sa.Column("max_amount_per_call", sa.Numeric(20, 8)),
        sa.Column("requires_confirmation", sa.Boolean, server_default="true"),
        # Custom parameters
        sa.Column("default_params", postgresql.JSONB, server_default="{}"),
        sa.Column("locked_params", postgresql.JSONB, server_default="{}"),
        sa.Column(
            "created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("NOW()")
        ),
        sa.Column(
            "updated_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("NOW()")
        ),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("project_id", "tool_id"),
    )

    # ===================================================================
    # TABLE 6: user_project_assignments
    # ===================================================================
    op.create_table(
        "user_project_assignments",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("uuid_generate_v4()"),
        ),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), nullable=False),
        # Assignment type
        sa.Column("assignment_type", sa.String(20), nullable=False),
        sa.Column("assigned_by", postgresql.UUID(as_uuid=True)),
        sa.Column("assignment_reason", sa.Text),
        # Status
        sa.Column("is_active", sa.Boolean, server_default="true"),
        # Timestamps
        sa.Column(
            "assigned_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("NOW()")
        ),
        sa.Column("last_active_at", sa.TIMESTAMP(timezone=True)),
        sa.Column("removed_at", sa.TIMESTAMP(timezone=True)),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("user_id", "project_id"),
        sa.CheckConstraint(
            "assignment_type IN ('auto', 'manual', 'self')",
            name="valid_assignment_type",
        ),
    )

    op.create_index(
        "idx_assignments_user",
        "user_project_assignments",
        ["user_id"],
        postgresql_where=sa.text("is_active = true"),
    )
    op.create_index(
        "idx_assignments_project",
        "user_project_assignments",
        ["project_id"],
        postgresql_where=sa.text("is_active = true"),
    )

    # ===================================================================
    # TABLE 7: user_active_projects
    # ===================================================================
    op.create_table(
        "user_active_projects",
        sa.Column("user_id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "activated_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("NOW()")
        ),
        sa.Column("session_count", sa.Integer, server_default="0"),
        sa.Column(
            "updated_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("NOW()")
        ),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
    )

    # ===================================================================
    # TABLE 8: project_auto_assign_rules
    # ===================================================================
    op.create_table(
        "project_auto_assign_rules",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("uuid_generate_v4()"),
        ),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), nullable=False),
        # Rule definition
        sa.Column("rule_name", sa.String(100), nullable=False),
        sa.Column("condition_type", sa.String(50), nullable=False),
        sa.Column("condition_params", postgresql.JSONB, nullable=False),
        # Behavior
        sa.Column("priority", sa.Integer, server_default="1"),
        sa.Column("auto_switch", sa.Boolean, server_default="false"),
        # Status
        sa.Column("is_active", sa.Boolean, server_default="true"),
        sa.Column(
            "created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("NOW()")
        ),
        sa.Column(
            "updated_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("NOW()")
        ),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
    )

    # ===================================================================
    # TABLE 9: project_invitations
    # ===================================================================
    op.create_table(
        "project_invitations",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("uuid_generate_v4()"),
        ),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), nullable=False),
        # Invitation details
        sa.Column("email", sa.String(255)),
        sa.Column("invitation_code", sa.String(50), unique=True),
        # Status
        sa.Column("status", sa.String(20), server_default="pending"),
        # Timestamps
        sa.Column("invited_by", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "invited_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("NOW()")
        ),
        sa.Column("expires_at", sa.TIMESTAMP(timezone=True)),
        sa.Column("accepted_at", sa.TIMESTAMP(timezone=True)),
        sa.Column("accepted_by", postgresql.UUID(as_uuid=True)),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.CheckConstraint(
            "status IN ('pending', 'accepted', 'expired', 'revoked')",
            name="valid_invitation_status",
        ),
    )

    # ===================================================================
    # TABLE 10: project_chat_sessions
    # ===================================================================
    op.create_table(
        "project_chat_sessions",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("uuid_generate_v4()"),
        ),
        sa.Column(
            "session_id", postgresql.UUID(as_uuid=True), nullable=False, unique=True
        ),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        # Context used
        sa.Column("system_prompt_version", sa.Integer, server_default="1"),
        sa.Column("knowledge_chunks_used", sa.Integer, server_default="0"),
        sa.Column("tools_used", postgresql.ARRAY(sa.Text), server_default="{}"),
        # Metrics
        sa.Column("messages_count", sa.Integer, server_default="0"),
        sa.Column("tokens_used", sa.Integer, server_default="0"),
        sa.Column(
            "created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("NOW()")
        ),
        sa.Column("ended_at", sa.TIMESTAMP(timezone=True)),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
    )

    op.create_index(
        "idx_project_sessions_project",
        "project_chat_sessions",
        ["project_id", sa.text("created_at DESC")],
    )
    op.create_index(
        "idx_project_sessions_user",
        "project_chat_sessions",
        ["user_id", sa.text("created_at DESC")],
    )

    # ===================================================================
    # TABLE 11: project_analytics_daily (TimescaleDB hypertable)
    # ===================================================================
    op.create_table(
        "project_analytics_daily",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("uuid_generate_v4()"),
        ),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("date", sa.Date, nullable=False),
        # User metrics
        sa.Column("total_users", sa.Integer, server_default="0"),
        sa.Column("active_users", sa.Integer, server_default="0"),
        sa.Column("new_users", sa.Integer, server_default="0"),
        sa.Column("returning_users", sa.Integer, server_default="0"),
        # Session metrics
        sa.Column("total_sessions", sa.Integer, server_default="0"),
        sa.Column("total_messages", sa.Integer, server_default="0"),
        sa.Column("avg_session_duration_seconds", sa.Integer),
        sa.Column("avg_messages_per_session", sa.Numeric(6, 2)),
        # Engagement
        sa.Column("satisfaction_score_avg", sa.Numeric(3, 2)),
        sa.Column("helpful_rate", sa.Numeric(5, 4)),
        # Knowledge usage
        sa.Column("knowledge_queries", sa.Integer, server_default="0"),
        sa.Column("knowledge_hit_rate", sa.Numeric(5, 4)),
        sa.Column("top_queries", postgresql.JSONB, server_default="[]"),
        # Transactions
        sa.Column("total_transactions", sa.Integer, server_default="0"),
        sa.Column("total_volume_usd", sa.Numeric(20, 2), server_default="0"),
        sa.Column("transaction_success_rate", sa.Numeric(5, 4)),
        # Tools
        sa.Column("tool_usage", postgresql.JSONB, server_default="{}"),
        sa.Column(
            "created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("NOW()")
        ),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("project_id", "date"),
    )

    # Convert to TimescaleDB hypertable
    op.execute("""
        SELECT create_hypertable('project_analytics_daily', 'created_at',
            chunk_time_interval => INTERVAL '1 day',
            if_not_exists => TRUE
        )
    """)

    op.create_index(
        "idx_project_analytics_date",
        "project_analytics_daily",
        ["project_id", sa.text("date DESC")],
    )

    # ===================================================================
    # VIEW: v_projects_with_stats
    # ===================================================================
    op.execute("""
        CREATE VIEW v_projects_with_stats AS
        SELECT 
            p.*,
            COALESCE(ua.user_count, 0) as total_users,
            COALESCE(ua.active_count, 0) as active_users,
            kb.total_documents,
            kb.total_chunks
        FROM projects p
        LEFT JOIN (
            SELECT 
                project_id,
                COUNT(*) as user_count,
                COUNT(*) FILTER (WHERE last_active_at > NOW() - INTERVAL '7 days') as active_count
            FROM user_project_assignments
            WHERE is_active = true
            GROUP BY project_id
        ) ua ON ua.project_id = p.id
        LEFT JOIN project_knowledge_bases kb ON kb.project_id = p.id
        WHERE p.status = 'active'
    """)


def downgrade() -> None:
    """Downgrade database schema - Remove Projects System."""
    # Drop view
    op.execute("DROP VIEW IF EXISTS v_projects_with_stats")

    # Drop tables in reverse order
    op.drop_table("project_analytics_daily")
    op.drop_table("project_chat_sessions")
    op.drop_table("project_invitations")
    op.drop_table("project_auto_assign_rules")
    op.drop_table("user_active_projects")
    op.drop_table("user_project_assignments")
    op.drop_table("project_tool_configs")
    op.drop_table("project_knowledge_chunks")
    op.drop_table("project_knowledge_documents")
    op.drop_table("project_knowledge_bases")
    op.drop_table("projects")
