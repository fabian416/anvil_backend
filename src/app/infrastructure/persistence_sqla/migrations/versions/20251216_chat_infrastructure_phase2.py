"""
Add chat infrastructure tables for Phase 2

Revision ID: chat_phase2_001
Revises: <previous_revision>
Create Date: 2025-12-16

Creates tables for:
- User chat preferences
- Conversation templates and executions
- Conversation exports
- Agent voting rounds and debates
- Agent performance metrics
- Custom agent configurations
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY


# revision identifiers, used by Alembic
revision = "chat_phase2_001"
down_revision = None  # Update with actual previous revision
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create Phase 2 chat infrastructure tables."""

    # =========================================================================
    # USER CHAT PREFERENCES
    # =========================================================================

    op.create_table(
        "user_chat_preferences",
        sa.Column("user_id", UUID(as_uuid=True), nullable=False, primary_key=True),
        # Response preferences
        sa.Column("verbosity_level", sa.String(20), nullable=False),
        sa.Column("tone_style", sa.String(20), nullable=False),
        sa.Column("response_format", sa.String(20), nullable=False),
        sa.Column(
            "preferred_language", sa.String(10), nullable=False, server_default="en"
        ),
        sa.Column("timezone", sa.String(50), nullable=False, server_default="UTC"),
        sa.Column(
            "include_code_examples", sa.Boolean(), nullable=False, server_default="true"
        ),
        sa.Column(
            "include_references", sa.Boolean(), nullable=False, server_default="true"
        ),
        # Notification preferences
        sa.Column(
            "notification_conversation_updates",
            sa.Boolean(),
            nullable=False,
            server_default="true",
        ),
        sa.Column(
            "notification_agent_responses",
            sa.Boolean(),
            nullable=False,
            server_default="true",
        ),
        sa.Column(
            "notification_daily_summary",
            sa.Boolean(),
            nullable=False,
            server_default="false",
        ),
        sa.Column(
            "notification_insight_alerts",
            sa.Boolean(),
            nullable=False,
            server_default="true",
        ),
        # Display preferences
        sa.Column(
            "display_theme", sa.String(20), nullable=False, server_default="light"
        ),
        sa.Column(
            "display_font_size", sa.Integer(), nullable=False, server_default="14"
        ),
        sa.Column(
            "display_show_timestamps",
            sa.Boolean(),
            nullable=False,
            server_default="true",
        ),
        sa.Column(
            "display_show_agent_names",
            sa.Boolean(),
            nullable=False,
            server_default="true",
        ),
        sa.Column(
            "display_markdown_rendering",
            sa.Boolean(),
            nullable=False,
            server_default="true",
        ),
        # Agent preferences
        sa.Column("favorite_agents", ARRAY(sa.String()), nullable=True),
        sa.Column("blocked_agents", ARRAY(sa.String()), nullable=True),
        # Custom instructions
        sa.Column("custom_instructions", sa.Text(), nullable=True),
        # Timestamps
        sa.Column(
            "created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()
        ),
    )

    # =========================================================================
    # CONVERSATION TEMPLATES
    # =========================================================================

    op.create_table(
        "conversation_templates",
        sa.Column("template_id", UUID(as_uuid=True), nullable=False, primary_key=True),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("category", sa.String(50), nullable=False),
        sa.Column("is_system", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_by_user_id", UUID(as_uuid=True), nullable=False),
        # Steps stored as JSONB
        sa.Column("steps", JSONB, nullable=False),
        # Metadata
        sa.Column("tags", ARRAY(sa.String()), nullable=True),
        sa.Column("estimated_duration_minutes", sa.Integer(), nullable=True),
        sa.Column("difficulty_level", sa.String(20), nullable=True),
        # Usage stats
        sa.Column("usage_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "avg_completion_rate", sa.Float(), nullable=False, server_default="0.0"
        ),
        sa.Column("avg_user_rating", sa.Float(), nullable=True),
        # Timestamps
        sa.Column(
            "created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()
        ),
    )

    op.create_index("idx_templates_category", "conversation_templates", ["category"])
    op.create_index(
        "idx_templates_creator", "conversation_templates", ["created_by_user_id"]
    )
    op.create_index("idx_templates_active", "conversation_templates", ["is_active"])

    # =========================================================================
    # TEMPLATE EXECUTIONS
    # =========================================================================

    op.create_table(
        "template_executions",
        sa.Column("execution_id", UUID(as_uuid=True), nullable=False, primary_key=True),
        sa.Column("template_id", UUID(as_uuid=True), nullable=False),
        sa.Column("conversation_id", UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", UUID(as_uuid=True), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column(
            "current_step_index", sa.Integer(), nullable=False, server_default="0"
        ),
        # Execution data
        sa.Column("step_results", JSONB, nullable=False, server_default="[]"),
        sa.Column("execution_time_seconds", sa.Integer(), nullable=True),
        sa.Column("completion_rate", sa.Float(), nullable=True),
        # Timestamps
        sa.Column(
            "started_at", sa.DateTime(), nullable=False, server_default=sa.func.now()
        ),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.Column("paused_at", sa.DateTime(), nullable=True),
    )

    op.create_index("idx_executions_template", "template_executions", ["template_id"])
    op.create_index("idx_executions_user", "template_executions", ["user_id"])
    op.create_index("idx_executions_status", "template_executions", ["status"])

    # =========================================================================
    # CONVERSATION EXPORTS
    # =========================================================================

    op.create_table(
        "conversation_exports",
        sa.Column("export_id", UUID(as_uuid=True), nullable=False, primary_key=True),
        sa.Column("conversation_id", UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", UUID(as_uuid=True), nullable=False),
        sa.Column("format", sa.String(20), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        # Configuration
        sa.Column(
            "include_metadata", sa.Boolean(), nullable=False, server_default="true"
        ),
        sa.Column(
            "include_timestamps", sa.Boolean(), nullable=False, server_default="true"
        ),
        sa.Column(
            "include_agent_names", sa.Boolean(), nullable=False, server_default="true"
        ),
        sa.Column("redact_pii", sa.Boolean(), nullable=False, server_default="false"),
        # Output
        sa.Column("file_path", sa.Text(), nullable=True),
        sa.Column("file_size_bytes", sa.Integer(), nullable=True),
        sa.Column("download_url", sa.Text(), nullable=True),
        sa.Column("expires_at", sa.DateTime(), nullable=True),
        # Timestamps
        sa.Column(
            "requested_at", sa.DateTime(), nullable=False, server_default=sa.func.now()
        ),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
    )

    op.create_index(
        "idx_exports_conversation", "conversation_exports", ["conversation_id"]
    )
    op.create_index("idx_exports_user", "conversation_exports", ["user_id"])
    op.create_index("idx_exports_status", "conversation_exports", ["status"])

    # =========================================================================
    # VOTING ROUNDS
    # =========================================================================

    op.create_table(
        "voting_rounds",
        sa.Column("round_id", UUID(as_uuid=True), nullable=False, primary_key=True),
        sa.Column("conversation_id", UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", UUID(as_uuid=True), nullable=False),
        sa.Column("query", sa.Text(), nullable=False),
        sa.Column("strategy", sa.String(30), nullable=False),
        # Results
        sa.Column("winning_response", sa.Text(), nullable=True),
        sa.Column(
            "winning_vote_count", sa.Integer(), nullable=False, server_default="0"
        ),
        sa.Column("total_votes", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "consensus_confidence", sa.Float(), nullable=False, server_default="0.0"
        ),
        # Votes stored as JSONB
        sa.Column("votes", JSONB, nullable=False, server_default="[]"),
        # Timestamps
        sa.Column(
            "started_at", sa.DateTime(), nullable=False, server_default=sa.func.now()
        ),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
    )

    op.create_index("idx_voting_conversation", "voting_rounds", ["conversation_id"])
    op.create_index("idx_voting_user", "voting_rounds", ["user_id"])

    # =========================================================================
    # AGENT DEBATES
    # =========================================================================

    op.create_table(
        "agent_debates",
        sa.Column("debate_id", UUID(as_uuid=True), nullable=False, primary_key=True),
        sa.Column("conversation_id", UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", UUID(as_uuid=True), nullable=False),
        sa.Column("query", sa.Text(), nullable=False),
        sa.Column("participating_agents", ARRAY(sa.String()), nullable=False),
        sa.Column("current_phase", sa.String(30), nullable=False),
        sa.Column("consensus_status", sa.String(20), nullable=False),
        # Results
        sa.Column("final_consensus", sa.Text(), nullable=True),
        sa.Column(
            "consensus_confidence", sa.Float(), nullable=False, server_default="0.0"
        ),
        # Debate data
        sa.Column("statements", JSONB, nullable=False, server_default="[]"),
        sa.Column("max_rounds", sa.Integer(), nullable=False, server_default="3"),
        sa.Column("current_round", sa.Integer(), nullable=False, server_default="0"),
        # Timestamps
        sa.Column(
            "started_at", sa.DateTime(), nullable=False, server_default=sa.func.now()
        ),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
    )

    op.create_index("idx_debates_conversation", "agent_debates", ["conversation_id"])
    op.create_index("idx_debates_user", "agent_debates", ["user_id"])
    op.create_index("idx_debates_status", "agent_debates", ["consensus_status"])

    # =========================================================================
    # AGENT PERFORMANCE METRICS
    # =========================================================================

    op.create_table(
        "agent_performance_metrics",
        sa.Column("agent_name", sa.String(100), nullable=False, primary_key=True),
        sa.Column("total_requests", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "successful_requests", sa.Integer(), nullable=False, server_default="0"
        ),
        sa.Column("failed_requests", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "avg_response_time_ms", sa.Float(), nullable=False, server_default="0.0"
        ),
        sa.Column("avg_confidence", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("avg_cost_usd", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("total_cost_usd", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column(
            "uptime_percentage", sa.Float(), nullable=False, server_default="100.0"
        ),
        sa.Column(
            "last_24h_requests", sa.Integer(), nullable=False, server_default="0"
        ),
        sa.Column("last_error", sa.Text(), nullable=True),
        sa.Column("last_error_at", sa.DateTime(), nullable=True),
        # Timestamps
        sa.Column(
            "created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()
        ),
    )

    op.create_index(
        "idx_agent_metrics_updated",
        "agent_performance_metrics",
        [sa.text("updated_at DESC")],
    )

    # =========================================================================
    # CUSTOM AGENT CONFIGURATIONS
    # =========================================================================

    op.create_table(
        "custom_agent_configs",
        sa.Column("config_id", UUID(as_uuid=True), nullable=False, primary_key=True),
        sa.Column("created_by_user_id", UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("system_prompt", sa.Text(), nullable=False),
        # Configuration
        sa.Column("capabilities", ARRAY(sa.String()), nullable=False),
        sa.Column("temperature", sa.Float(), nullable=False, server_default="0.7"),
        sa.Column("max_tokens", sa.Integer(), nullable=False, server_default="1000"),
        sa.Column("personality_traits", JSONB, nullable=False, server_default="{}"),
        sa.Column("expertise_areas", ARRAY(sa.String()), nullable=True),
        sa.Column(
            "response_style", sa.String(20), nullable=False, server_default="balanced"
        ),
        # LLM settings
        sa.Column(
            "preferred_llm_provider",
            sa.String(50),
            nullable=False,
            server_default="openai",
        ),
        sa.Column("fallback_llm_provider", sa.String(50), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        # Timestamps
        sa.Column(
            "created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()
        ),
    )

    op.create_index(
        "idx_custom_agents_creator", "custom_agent_configs", ["created_by_user_id"]
    )
    op.create_index("idx_custom_agents_active", "custom_agent_configs", ["is_active"])

    # Create unique constraint for agent name per user
    op.create_unique_constraint(
        "unique_agent_name_per_user",
        "custom_agent_configs",
        ["created_by_user_id", "name"],
    )


def downgrade() -> None:
    """Drop Phase 2 chat infrastructure tables."""

    op.drop_table("custom_agent_configs")
    op.drop_table("agent_performance_metrics")
    op.drop_table("agent_debates")
    op.drop_table("voting_rounds")
    op.drop_table("conversation_exports")
    op.drop_table("template_executions")
    op.drop_table("conversation_templates")
    op.drop_table("user_chat_preferences")
