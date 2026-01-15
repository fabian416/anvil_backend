"""Add AI Telemetry tables

Revision ID: d4e5f6g7h8i9
Revises: c3d4e5f6g7h8
Create Date: 2025-11-27 04:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "d4e5f6g7h8i9"
down_revision: Union[str, None] = "c3d4e5f6g7h8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    # Create Enums using raw SQL to avoid duplication issues
    connection = op.get_bind()
    connection.execute(sa.text("""DO $$ BEGIN
        IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'llmprovider') THEN
            CREATE TYPE llmprovider AS ENUM ('vertex', 'bedrock', 'openai');
        END IF;
    END $$;"""))
    connection.execute(sa.text("""DO $$ BEGIN
        IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'llmstatus') THEN
            CREATE TYPE llmstatus AS ENUM ('success', 'failed', 'rate_limited', 'fallback');
        END IF;
    END $$;"""))
    connection.execute(sa.text("""DO $$ BEGIN
        IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'agentexecutionstatus') THEN
            CREATE TYPE agentexecutionstatus AS ENUM ('pending', 'running', 'completed', 'failed', 'canceled');
        END IF;
    END $$;"""))
    connection.execute(sa.text("""DO $$ BEGIN
        IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'agenttaskstatus') THEN
            CREATE TYPE agenttaskstatus AS ENUM ('pending', 'running', 'completed', 'failed', 'skipped');
        END IF;
    END $$;"""))
    connection.execute(sa.text("""DO $$ BEGIN
        IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'agenttoolstatus') THEN
            CREATE TYPE agenttoolstatus AS ENUM ('success', 'failed', 'timeout');
        END IF;
    END $$;"""))
    connection.execute(sa.text("""DO $$ BEGIN
        IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'ratelimiteventtype') THEN
            CREATE TYPE ratelimiteventtype AS ENUM ('rate_limit', 'quota_exceeded', 'throttle', 'timeout');
        END IF;
    END $$;"""))
    connection.execute(sa.text("""DO $$ BEGIN
        IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'costalerttype') THEN
            CREATE TYPE costalerttype AS ENUM ('daily_threshold', 'weekly_threshold', 'monthly_threshold', 'user_spike');
        END IF;
    END $$;"""))
    connection.execute(sa.text("""DO $$ BEGIN
        IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'feedbacktype') THEN
            CREATE TYPE feedbacktype AS ENUM ('helpful', 'not_helpful', 'incorrect', 'offensive', 'other');
        END IF;
    END $$;"""))
    connection.execute(sa.text("""DO $$ BEGIN
        IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'modelstatus') THEN
            CREATE TYPE modelstatus AS ENUM ('inactive', 'active', 'deprecated');
        END IF;
    END $$;"""))

    # --- Models ---
    op.create_table(
        "models",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("provider", postgresql.ENUM("vertex", "bedrock", "openai", name="llmprovider", create_type=False), nullable=False),
        sa.Column("model_name", sa.String(length=100), nullable=False),
        sa.Column("label", sa.String(length=255), nullable=False),
        sa.Column("is_default", sa.Boolean(), nullable=True, server_default='false'),
        sa.Column("is_available", sa.Boolean(), nullable=True, server_default='true'),
        sa.Column("cost_per_1k_input_tokens", sa.Numeric(precision=10, scale=8), nullable=False),
        sa.Column("cost_per_1k_output_tokens", sa.Numeric(precision=10, scale=8), nullable=False),
        sa.Column("max_tokens", sa.Integer(), nullable=True),
        sa.Column("status", postgresql.ENUM("inactive", "active", "deprecated", name="modelstatus", create_type=False), nullable=False, server_default='active'),
        sa.Column("request_count", sa.BigInteger(), nullable=True, server_default='0'),
        sa.Column("total_cost_usd", sa.Numeric(precision=12, scale=2), nullable=True, server_default='0'),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=True),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_models")),
        sa.UniqueConstraint("provider", "model_name", name="unique_provider_model"),
    )
    op.create_index(op.f("ix_models_provider"), "models", ["provider"], unique=False)
    op.create_index(op.f("ix_models_model_name"), "models", ["model_name"], unique=False)
    op.create_index(op.f("ix_models_is_default"), "models", ["is_default"], unique=False)
    op.create_index(op.f("ix_models_status"), "models", ["status"], unique=False)
    op.create_index(op.f("ix_models_is_available"), "models", ["is_available"], unique=False)

    # --- LLM Conversations ---
    op.create_table(
        "llm_conversations",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("session_id", sa.String(length=100), nullable=False),
        sa.Column("model_id", sa.BigInteger(), nullable=True),
        sa.Column("provider", postgresql.ENUM("vertex", "bedrock", "openai", name="llmprovider", create_type=False), nullable=False),
        sa.Column("model_name", sa.String(length=100), nullable=False),
        sa.Column("prompt_text", sa.Text(), nullable=False),
        sa.Column("response_text", sa.Text(), nullable=True),
        sa.Column("input_tokens", sa.Integer(), nullable=True),
        sa.Column("output_tokens", sa.Integer(), nullable=True),
        sa.Column("total_tokens", sa.Integer(), nullable=True),
        sa.Column("cost_usd", sa.Numeric(precision=10, scale=6), nullable=True),
        sa.Column("latency_ms", sa.Integer(), nullable=True),
        sa.Column("status", postgresql.ENUM("success", "failed", "rate_limited", "fallback", name="llmstatus", create_type=False), nullable=True, server_default='success'),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("ip_address", sa.String(length=45), nullable=True),
        sa.Column("user_agent", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=True),
        sa.ForeignKeyConstraint(["model_id"], ["models.id"], name=op.f("fk_llm_conversations_model_id_models"), ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name=op.f("fk_llm_conversations_user_id_users"), ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_llm_conversations")),
    )
    op.create_index(op.f("ix_llm_conversations_user_id"), "llm_conversations", ["user_id"], unique=False)
    op.create_index(op.f("ix_llm_conversations_session_id"), "llm_conversations", ["session_id"], unique=False)
    op.create_index(op.f("ix_llm_conversations_model_id"), "llm_conversations", ["model_id"], unique=False)
    op.create_index(op.f("ix_llm_conversations_provider"), "llm_conversations", ["provider"], unique=False)
    op.create_index(op.f("ix_llm_conversations_status"), "llm_conversations", ["status"], unique=False)
    op.create_index(op.f("ix_llm_conversations_created_at"), "llm_conversations", ["created_at"], unique=False)

    # --- Agent Executions ---
    op.create_table(
        "agent_executions",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("conversation_id", sa.BigInteger(), nullable=True),
        sa.Column("agent_type", sa.String(length=50), nullable=False),
        sa.Column("workflow_type", sa.String(length=50), nullable=False),
        sa.Column("status", postgresql.ENUM("pending", "running", "completed", "failed", "canceled", name="agentexecutionstatus", create_type=False), nullable=True, server_default='pending'),
        sa.Column("input_params", postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column("output_result", postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column("total_tasks", sa.Integer(), nullable=True, server_default='0'),
        sa.Column("completed_tasks", sa.Integer(), nullable=True, server_default='0'),
        sa.Column("failed_tasks", sa.Integer(), nullable=True, server_default='0'),
        sa.Column("total_cost_usd", sa.Numeric(precision=10, scale=6), nullable=True, server_default='0'),
        sa.Column("execution_time_ms", sa.Integer(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=True),
        sa.ForeignKeyConstraint(["conversation_id"], ["llm_conversations.id"], name=op.f("fk_agent_executions_conversation_id_llm_conversations"), ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name=op.f("fk_agent_executions_user_id_users"), ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_agent_executions")),
    )
    op.create_index(op.f("ix_agent_executions_user_id"), "agent_executions", ["user_id"], unique=False)
    op.create_index(op.f("ix_agent_executions_conversation_id"), "agent_executions", ["conversation_id"], unique=False)
    op.create_index(op.f("ix_agent_executions_agent_type"), "agent_executions", ["agent_type"], unique=False)
    op.create_index(op.f("ix_agent_executions_workflow_type"), "agent_executions", ["workflow_type"], unique=False)
    op.create_index(op.f("ix_agent_executions_status"), "agent_executions", ["status"], unique=False)
    op.create_index(op.f("ix_agent_executions_created_at"), "agent_executions", ["created_at"], unique=False)

    # --- Agent Tasks ---
    op.create_table(
        "agent_tasks",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("execution_id", sa.BigInteger(), nullable=False),
        sa.Column("task_name", sa.String(length=100), nullable=False),
        sa.Column("task_type", sa.String(length=50), nullable=False),
        sa.Column("status", postgresql.ENUM("pending", "running", "completed", "failed", "skipped", name="agenttaskstatus", create_type=False), nullable=True, server_default='pending'),
        sa.Column("input_data", postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column("output_data", postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("execution_time_ms", sa.Integer(), nullable=True),
        sa.Column("retry_count", sa.Integer(), nullable=True, server_default='0'),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=True),
        sa.ForeignKeyConstraint(["execution_id"], ["agent_executions.id"], name=op.f("fk_agent_tasks_execution_id_agent_executions"), ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_agent_tasks")),
    )
    op.create_index(op.f("ix_agent_tasks_execution_id"), "agent_tasks", ["execution_id"], unique=False)
    op.create_index(op.f("ix_agent_tasks_task_type"), "agent_tasks", ["task_type"], unique=False)
    op.create_index(op.f("ix_agent_tasks_status"), "agent_tasks", ["status"], unique=False)
    op.create_index(op.f("ix_agent_tasks_created_at"), "agent_tasks", ["created_at"], unique=False)

    # --- Agent Tools Usage ---
    op.create_table(
        "agent_tools_usage",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("execution_id", sa.BigInteger(), nullable=False),
        sa.Column("task_id", sa.BigInteger(), nullable=True),
        sa.Column("tool_name", sa.String(length=100), nullable=False),
        sa.Column("input_params", postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column("output_result", postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column("status", postgresql.ENUM("success", "failed", "timeout", name="agenttoolstatus", create_type=False), nullable=True, server_default='success'),
        sa.Column("execution_time_ms", sa.Integer(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=True),
        sa.ForeignKeyConstraint(["execution_id"], ["agent_executions.id"], name=op.f("fk_agent_tools_usage_execution_id_agent_executions"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["task_id"], ["agent_tasks.id"], name=op.f("fk_agent_tools_usage_task_id_agent_tasks"), ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_agent_tools_usage")),
    )
    op.create_index(op.f("ix_agent_tools_usage_execution_id"), "agent_tools_usage", ["execution_id"], unique=False)
    op.create_index(op.f("ix_agent_tools_usage_task_id"), "agent_tools_usage", ["task_id"], unique=False)
    op.create_index(op.f("ix_agent_tools_usage_tool_name"), "agent_tools_usage", ["tool_name"], unique=False)
    op.create_index(op.f("ix_agent_tools_usage_status"), "agent_tools_usage", ["status"], unique=False)
    op.create_index(op.f("ix_agent_tools_usage_created_at"), "agent_tools_usage", ["created_at"], unique=False)

    # --- LLM Rate Limit Events ---
    op.create_table(
        "llm_rate_limit_events",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("provider", postgresql.ENUM("vertex", "bedrock", "openai", name="llmprovider", create_type=False), nullable=False),
        sa.Column("model_name", sa.String(length=100), nullable=False),
        sa.Column("event_type", postgresql.ENUM("rate_limit", "quota_exceeded", "throttle", "timeout", name="ratelimiteventtype", create_type=False), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("error_code", sa.String(length=50), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("retry_after_seconds", sa.Integer(), nullable=True),
        sa.Column("fallback_used", sa.Boolean(), nullable=True, server_default='false'),
        sa.Column("fallback_provider", sa.String(length=20), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name=op.f("fk_llm_rate_limit_events_user_id_users"), ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_llm_rate_limit_events")),
    )
    op.create_index(op.f("ix_llm_rate_limit_events_provider"), "llm_rate_limit_events", ["provider"], unique=False)
    op.create_index(op.f("ix_llm_rate_limit_events_model_name"), "llm_rate_limit_events", ["model_name"], unique=False)
    op.create_index(op.f("ix_llm_rate_limit_events_event_type"), "llm_rate_limit_events", ["event_type"], unique=False)
    op.create_index(op.f("ix_llm_rate_limit_events_created_at"), "llm_rate_limit_events", ["created_at"], unique=False)

    # --- LLM Cost Alerts ---
    op.create_table(
        "llm_cost_alerts",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("alert_type", postgresql.ENUM("daily_threshold", "weekly_threshold", "monthly_threshold", "user_spike", name="costalerttype", create_type=False), nullable=False),
        sa.Column("threshold_usd", sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column("actual_cost_usd", sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column("time_period_start", sa.DateTime(timezone=True), nullable=False),
        sa.Column("time_period_end", sa.DateTime(timezone=True), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("provider", sa.String(length=20), nullable=True),
        sa.Column("alert_sent", sa.Boolean(), nullable=True, server_default='false'),
        sa.Column("alert_sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name=op.f("fk_llm_cost_alerts_user_id_users"), ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_llm_cost_alerts")),
    )
    op.create_index(op.f("ix_llm_cost_alerts_alert_type"), "llm_cost_alerts", ["alert_type"], unique=False)
    op.create_index(op.f("ix_llm_cost_alerts_time_period_start"), "llm_cost_alerts", ["time_period_start"], unique=False)
    op.create_index(op.f("ix_llm_cost_alerts_alert_sent"), "llm_cost_alerts", ["alert_sent"], unique=False)
    op.create_index(op.f("ix_llm_cost_alerts_created_at"), "llm_cost_alerts", ["created_at"], unique=False)

    # --- Vertex API Metrics ---
    op.create_table(
        "vertex_api_metrics",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("model_id", sa.BigInteger(), nullable=True),
        sa.Column("region", sa.String(length=50), nullable=False),
        sa.Column("requests_count", sa.Integer(), nullable=True, server_default='0'),
        sa.Column("tokens_consumed", sa.BigInteger(), nullable=True, server_default='0'),
        sa.Column("cost_usd", sa.Numeric(precision=10, scale=6), nullable=True, server_default='0'),
        sa.Column("quota_exceeded_count", sa.Integer(), nullable=True, server_default='0'),
        sa.Column("rate_limit_count", sa.Integer(), nullable=True, server_default='0'),
        sa.Column("avg_latency_ms", sa.Integer(), nullable=True),
        sa.Column("p95_latency_ms", sa.Integer(), nullable=True),
        sa.Column("p99_latency_ms", sa.Integer(), nullable=True),
        sa.Column("error_count", sa.Integer(), nullable=True, server_default='0'),
        sa.Column("success_rate", sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column("failover_to_bedrock_count", sa.Integer(), nullable=True, server_default='0'),
        sa.Column("time_window_start", sa.DateTime(timezone=True), nullable=False),
        sa.Column("time_window_end", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=True),
        sa.ForeignKeyConstraint(["model_id"], ["models.id"], name=op.f("fk_vertex_api_metrics_model_id_models"), ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_vertex_api_metrics")),
        sa.UniqueConstraint("model_id", "region", "time_window_start", name="unique_vertex_metric"),
    )
    op.create_index(op.f("ix_vertex_api_metrics_model_id"), "vertex_api_metrics", ["model_id"], unique=False)
    op.create_index(op.f("ix_vertex_api_metrics_region"), "vertex_api_metrics", ["region"], unique=False)
    op.create_index(op.f("ix_vertex_api_metrics_time_window_start"), "vertex_api_metrics", ["time_window_start"], unique=False)

    # --- Bedrock API Metrics ---
    op.create_table(
        "bedrock_api_metrics",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("model_id", sa.BigInteger(), nullable=True),
        sa.Column("region", sa.String(length=50), nullable=False),
        sa.Column("requests_count", sa.Integer(), nullable=True, server_default='0'),
        sa.Column("tokens_consumed", sa.BigInteger(), nullable=True, server_default='0'),
        sa.Column("cost_usd", sa.Numeric(precision=10, scale=6), nullable=True, server_default='0'),
        sa.Column("throttle_count", sa.Integer(), nullable=True, server_default='0'),
        sa.Column("model_not_ready_count", sa.Integer(), nullable=True, server_default='0'),
        sa.Column("avg_latency_ms", sa.Integer(), nullable=True),
        sa.Column("p95_latency_ms", sa.Integer(), nullable=True),
        sa.Column("p99_latency_ms", sa.Integer(), nullable=True),
        sa.Column("error_count", sa.Integer(), nullable=True, server_default='0'),
        sa.Column("success_rate", sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column("failover_from_vertex_count", sa.Integer(), nullable=True, server_default='0'),
        sa.Column("time_window_start", sa.DateTime(timezone=True), nullable=False),
        sa.Column("time_window_end", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=True),
        sa.ForeignKeyConstraint(["model_id"], ["models.id"], name=op.f("fk_bedrock_api_metrics_model_id_models"), ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_bedrock_api_metrics")),
        sa.UniqueConstraint("model_id", "region", "time_window_start", name="unique_bedrock_metric"),
    )
    op.create_index(op.f("ix_bedrock_api_metrics_model_id"), "bedrock_api_metrics", ["model_id"], unique=False)
    op.create_index(op.f("ix_bedrock_api_metrics_region"), "bedrock_api_metrics", ["region"], unique=False)
    op.create_index(op.f("ix_bedrock_api_metrics_time_window_start"), "bedrock_api_metrics", ["time_window_start"], unique=False)

    # --- Conversation Feedback ---
    op.create_table(
        "conversation_feedback",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("conversation_id", sa.BigInteger(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("rating", sa.Integer(), nullable=True),
        sa.Column("feedback_type", postgresql.ENUM("helpful", "not_helpful", "incorrect", "offensive", "other", name="feedbacktype", create_type=False), nullable=False),
        sa.Column("feedback_text", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=True),
        sa.ForeignKeyConstraint(["conversation_id"], ["llm_conversations.id"], name=op.f("fk_conversation_feedback_conversation_id_llm_conversations"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name=op.f("fk_conversation_feedback_user_id_users"), ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_conversation_feedback")),
    )
    op.create_index(op.f("ix_conversation_feedback_conversation_id"), "conversation_feedback", ["conversation_id"], unique=False)
    op.create_index(op.f("ix_conversation_feedback_user_id"), "conversation_feedback", ["user_id"], unique=False)
    op.create_index(op.f("ix_conversation_feedback_rating"), "conversation_feedback", ["rating"], unique=False)
    op.create_index(op.f("ix_conversation_feedback_feedback_type"), "conversation_feedback", ["feedback_type"], unique=False)
    op.create_index(op.f("ix_conversation_feedback_created_at"), "conversation_feedback", ["created_at"], unique=False)

def downgrade() -> None:
    op.drop_index(op.f("ix_conversation_feedback_created_at"), table_name="conversation_feedback")
    op.drop_index(op.f("ix_conversation_feedback_feedback_type"), table_name="conversation_feedback")
    op.drop_index(op.f("ix_conversation_feedback_rating"), table_name="conversation_feedback")
    op.drop_index(op.f("ix_conversation_feedback_user_id"), table_name="conversation_feedback")
    op.drop_index(op.f("ix_conversation_feedback_conversation_id"), table_name="conversation_feedback")
    op.drop_table("conversation_feedback")

    op.drop_index(op.f("ix_bedrock_api_metrics_time_window_start"), table_name="bedrock_api_metrics")
    op.drop_index(op.f("ix_bedrock_api_metrics_region"), table_name="bedrock_api_metrics")
    op.drop_index(op.f("ix_bedrock_api_metrics_model_id"), table_name="bedrock_api_metrics")
    op.drop_table("bedrock_api_metrics")

    op.drop_index(op.f("ix_vertex_api_metrics_time_window_start"), table_name="vertex_api_metrics")
    op.drop_index(op.f("ix_vertex_api_metrics_region"), table_name="vertex_api_metrics")
    op.drop_index(op.f("ix_vertex_api_metrics_model_id"), table_name="vertex_api_metrics")
    op.drop_table("vertex_api_metrics")

    op.drop_index(op.f("ix_llm_cost_alerts_created_at"), table_name="llm_cost_alerts")
    op.drop_index(op.f("ix_llm_cost_alerts_alert_sent"), table_name="llm_cost_alerts")
    op.drop_index(op.f("ix_llm_cost_alerts_time_period_start"), table_name="llm_cost_alerts")
    op.drop_index(op.f("ix_llm_cost_alerts_alert_type"), table_name="llm_cost_alerts")
    op.drop_table("llm_cost_alerts")

    op.drop_index(op.f("ix_llm_rate_limit_events_created_at"), table_name="llm_rate_limit_events")
    op.drop_index(op.f("ix_llm_rate_limit_events_event_type"), table_name="llm_rate_limit_events")
    op.drop_index(op.f("ix_llm_rate_limit_events_model_name"), table_name="llm_rate_limit_events")
    op.drop_index(op.f("ix_llm_rate_limit_events_provider"), table_name="llm_rate_limit_events")
    op.drop_table("llm_rate_limit_events")

    op.drop_index(op.f("ix_agent_tools_usage_created_at"), table_name="agent_tools_usage")
    op.drop_index(op.f("ix_agent_tools_usage_status"), table_name="agent_tools_usage")
    op.drop_index(op.f("ix_agent_tools_usage_tool_name"), table_name="agent_tools_usage")
    op.drop_index(op.f("ix_agent_tools_usage_task_id"), table_name="agent_tools_usage")
    op.drop_index(op.f("ix_agent_tools_usage_execution_id"), table_name="agent_tools_usage")
    op.drop_table("agent_tools_usage")

    op.drop_index(op.f("ix_agent_tasks_created_at"), table_name="agent_tasks")
    op.drop_index(op.f("ix_agent_tasks_status"), table_name="agent_tasks")
    op.drop_index(op.f("ix_agent_tasks_task_type"), table_name="agent_tasks")
    op.drop_index(op.f("ix_agent_tasks_execution_id"), table_name="agent_tasks")
    op.drop_table("agent_tasks")

    op.drop_index(op.f("ix_agent_executions_created_at"), table_name="agent_executions")
    op.drop_index(op.f("ix_agent_executions_status"), table_name="agent_executions")
    op.drop_index(op.f("ix_agent_executions_workflow_type"), table_name="agent_executions")
    op.drop_index(op.f("ix_agent_executions_agent_type"), table_name="agent_executions")
    op.drop_index(op.f("ix_agent_executions_conversation_id"), table_name="agent_executions")
    op.drop_index(op.f("ix_agent_executions_user_id"), table_name="agent_executions")
    op.drop_table("agent_executions")

    op.drop_index(op.f("ix_llm_conversations_created_at"), table_name="llm_conversations")
    op.drop_index(op.f("ix_llm_conversations_status"), table_name="llm_conversations")
    op.drop_index(op.f("ix_llm_conversations_provider"), table_name="llm_conversations")
    op.drop_index(op.f("ix_llm_conversations_model_id"), table_name="llm_conversations")
    op.drop_index(op.f("ix_llm_conversations_session_id"), table_name="llm_conversations")
    op.drop_index(op.f("ix_llm_conversations_user_id"), table_name="llm_conversations")
    op.drop_table("llm_conversations")

    op.drop_index(op.f("ix_models_is_available"), table_name="models")
    op.drop_index(op.f("ix_models_status"), table_name="models")
    op.drop_index(op.f("ix_models_is_default"), table_name="models")
    op.drop_index(op.f("ix_models_model_name"), table_name="models")
    op.drop_index(op.f("ix_models_provider"), table_name="models")
    op.drop_table("models")

    sa.Enum(name="modelstatus").drop(op.get_bind())
    sa.Enum(name="feedbacktype").drop(op.get_bind())
    sa.Enum(name="costalerttype").drop(op.get_bind())
    sa.Enum(name="ratelimiteventtype").drop(op.get_bind())
    sa.Enum(name="agenttoolstatus").drop(op.get_bind())
    sa.Enum(name="agenttaskstatus").drop(op.get_bind())
    sa.Enum(name="agentexecutionstatus").drop(op.get_bind())
    sa.Enum(name="llmstatus").drop(op.get_bind())
    sa.Enum(name="llmprovider").drop(op.get_bind())
