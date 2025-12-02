"""
Add LLM Orchestration System schema.

Revision ID: llm_orchestration_v1
Revises: f6g7h8i9j0k1
Create Date: 2025-12-01 12:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "llm_orchestration_v1"
down_revision: Union[str, None] = "f6g7h8i9j0k1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create LLM orchestration tables."""

    # ========================================================================
    # MODULE: PROVIDER_MANAGEMENT
    # ========================================================================

    # Create llm_providers table
    op.create_table(
        "llm_providers",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=50), nullable=False),
        sa.Column("display_name", sa.String(length=100), nullable=False),
        sa.Column("priority", sa.Integer(), nullable=False),
        sa.Column("is_enabled", sa.Boolean(), nullable=True),
        sa.Column("health_status", sa.String(length=20), nullable=True),
        sa.Column("last_health_check", sa.DateTime(timezone=True), nullable=True),
        sa.Column("health_check_interval_seconds", sa.Integer(), nullable=True),
        sa.Column("config", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("rate_limits", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint("health_status IN ('healthy', 'degraded', 'down')", name="valid_health_status"),
        sa.CheckConstraint("priority >= 1 AND priority <= 10", name="valid_priority"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )
    op.create_index("idx_providers_priority", "llm_providers", ["priority"], unique=False, postgresql_where=sa.text("is_enabled = true"))

    # Create llm_models table
    op.create_table(
        "llm_models",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("provider_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("model_id", sa.String(length=100), nullable=False),
        sa.Column("display_name", sa.String(length=100), nullable=False),
        sa.Column("model_family", sa.String(length=50), nullable=True),
        sa.Column("capabilities", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("context_window", sa.Integer(), nullable=True),
        sa.Column("max_output_tokens", sa.Integer(), nullable=True),
        sa.Column("supports_streaming", sa.Boolean(), nullable=True),
        sa.Column("supports_tools", sa.Boolean(), nullable=True),
        sa.Column("cost_per_1k_input", sa.DECIMAL(precision=10, scale=6), nullable=True),
        sa.Column("cost_per_1k_output", sa.DECIMAL(precision=10, scale=6), nullable=True),
        sa.Column("avg_latency_ms", sa.Integer(), nullable=True),
        sa.Column("is_enabled", sa.Boolean(), nullable=True),
        sa.Column("carousel_position", sa.Integer(), nullable=True),
        sa.Column("tier", sa.String(length=20), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint("tier IN ('premium', 'standard', 'economy', 'experimental')", name="valid_tier"),
        sa.ForeignKeyConstraint(["provider_id"], ["llm_providers.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_models_provider_enabled", "llm_models", ["provider_id", "carousel_position"], unique=False, postgresql_where=sa.text("is_enabled = true"))
    op.create_index("idx_models_capabilities", "llm_models", ["capabilities"], unique=False, postgresql_using="gin")

    # ========================================================================
    # MODULE: RANKING_SYSTEM
    # ========================================================================

    # Create ranking_weight_profiles table
    op.create_table(
        "ranking_weight_profiles",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("agent_type", sa.String(length=50), nullable=False),
        sa.Column("success_weight", sa.DECIMAL(precision=3, scale=2), nullable=True),
        sa.Column("latency_weight", sa.DECIMAL(precision=3, scale=2), nullable=True),
        sa.Column("cost_weight", sa.DECIMAL(precision=3, scale=2), nullable=True),
        sa.Column("recency_weight", sa.DECIMAL(precision=3, scale=2), nullable=True),
        sa.Column("min_requests_for_ranking", sa.Integer(), nullable=True),
        sa.Column("recency_decay_hours", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint("success_weight + latency_weight + cost_weight + recency_weight = 1.00", name="weights_sum_to_one"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("agent_type"),
    )

    # Create agent_model_rankings table
    op.create_table(
        "agent_model_rankings",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("agent_type", sa.String(length=50), nullable=False),
        sa.Column("model_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("ranking_score", sa.DECIMAL(precision=5, scale=4), nullable=True),
        sa.Column("success_rate", sa.DECIMAL(precision=5, scale=4), nullable=True),
        sa.Column("latency_score", sa.DECIMAL(precision=5, scale=4), nullable=True),
        sa.Column("cost_score", sa.DECIMAL(precision=5, scale=4), nullable=True),
        sa.Column("total_requests", sa.Integer(), nullable=True),
        sa.Column("successful_requests", sa.Integer(), nullable=True),
        sa.Column("failed_requests", sa.Integer(), nullable=True),
        sa.Column("timeout_requests", sa.Integer(), nullable=True),
        sa.Column("avg_latency_ms", sa.Integer(), nullable=True),
        sa.Column("p95_latency_ms", sa.Integer(), nullable=True),
        sa.Column("avg_cost_per_request", sa.DECIMAL(precision=10, scale=6), nullable=True),
        sa.Column("total_tokens_used", sa.Integer(), nullable=True),
        sa.Column("last_used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_recalculated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint("ranking_score >= 0 AND ranking_score <= 1 AND success_rate >= 0 AND success_rate <= 1", name="valid_scores"),
        sa.ForeignKeyConstraint(["model_id"], ["llm_models.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_rankings_agent_score", "agent_model_rankings", ["agent_type", sa.text("ranking_score DESC")], unique=False)

    # Create ranking_overrides table
    op.create_table(
        "ranking_overrides",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("agent_type", sa.String(length=50), nullable=False),
        sa.Column("model_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("override_score", sa.DECIMAL(precision=5, scale=4), nullable=False),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint("override_score >= 0 AND override_score <= 1", name="valid_override"),
        sa.ForeignKeyConstraint(["model_id"], ["llm_models.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    # ========================================================================
    # MODULE: REQUEST_TRACKING
    # ========================================================================

    # Create llm_requests table
    op.create_table(
        "llm_requests",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("request_id", sa.String(length=100), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("agent_type", sa.String(length=50), nullable=False),
        sa.Column("session_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("prompt_hash", sa.String(length=64), nullable=True),
        sa.Column("input_tokens", sa.Integer(), nullable=True),
        sa.Column("max_output_tokens", sa.Integer(), nullable=True),
        sa.Column("temperature", sa.DECIMAL(precision=3, scale=2), nullable=True),
        sa.Column("has_tools", sa.Boolean(), nullable=True),
        sa.Column("is_streaming", sa.Boolean(), nullable=True),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("status_history", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("selected_provider_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("selected_model_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("selection_reason", sa.String(length=100), nullable=True),
        sa.Column("attempt_count", sa.Integer(), nullable=True),
        sa.Column("total_latency_ms", sa.Integer(), nullable=True),
        sa.Column("time_to_first_token_ms", sa.Integer(), nullable=True),
        sa.Column("output_tokens", sa.Integer(), nullable=True),
        sa.Column("estimated_cost_usd", sa.DECIMAL(precision=10, scale=6), nullable=True),
        sa.Column("actual_cost_usd", sa.DECIMAL(precision=10, scale=6), nullable=True),
        sa.Column("error_code", sa.String(length=50), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint(
            "status IN ('pending', 'queued', 'selecting_model', 'executing', 'streaming', 'completed', 'failed', 'timeout', 'cancelled', 'retrying')",
            name="valid_status",
        ),
        sa.ForeignKeyConstraint(["selected_provider_id"], ["llm_providers.id"]),
        sa.ForeignKeyConstraint(["selected_model_id"], ["llm_models.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("request_id"),
    )
    op.create_index("idx_requests_status", "llm_requests", ["status", sa.text("created_at DESC")], unique=False)
    op.create_index("idx_requests_user", "llm_requests", ["user_id", sa.text("created_at DESC")], unique=False)
    op.create_index("idx_requests_agent", "llm_requests", ["agent_type", sa.text("created_at DESC")], unique=False)
    op.create_index("idx_requests_model", "llm_requests", ["selected_model_id", sa.text("created_at DESC")], unique=False)
    op.create_index("idx_requests_provider", "llm_requests", ["selected_provider_id", sa.text("created_at DESC")], unique=False)

    # Create llm_request_attempts table
    op.create_table(
        "llm_request_attempts",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("request_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("attempt_number", sa.Integer(), nullable=False),
        sa.Column("provider_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("model_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("latency_ms", sa.Integer(), nullable=True),
        sa.Column("input_tokens", sa.Integer(), nullable=True),
        sa.Column("output_tokens", sa.Integer(), nullable=True),
        sa.Column("cost_usd", sa.DECIMAL(precision=10, scale=6), nullable=True),
        sa.Column("error_type", sa.String(length=50), nullable=True),
        sa.Column("error_code", sa.String(length=50), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint(
            "status IN ('started', 'completed', 'failed', 'timeout', 'rate_limited', 'cancelled')",
            name="valid_attempt_status",
        ),
        sa.ForeignKeyConstraint(["request_id"], ["llm_requests.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["provider_id"], ["llm_providers.id"]),
        sa.ForeignKeyConstraint(["model_id"], ["llm_models.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_attempts_request", "llm_request_attempts", ["request_id", "attempt_number"], unique=False)

    # ========================================================================
    # MODULE: CIRCUIT_BREAKER
    # ========================================================================

    # Create circuit_breakers table
    op.create_table(
        "circuit_breakers",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("entity_type", sa.String(length=20), nullable=False),
        sa.Column("entity_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("entity_name", sa.String(length=100), nullable=True),
        sa.Column("state", sa.String(length=20), nullable=False),
        sa.Column("failure_count", sa.Integer(), nullable=True),
        sa.Column("success_count", sa.Integer(), nullable=True),
        sa.Column("consecutive_failures", sa.Integer(), nullable=True),
        sa.Column("last_failure_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_success_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("opened_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("half_open_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "config",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint("state IN ('closed', 'open', 'half_open')", name="valid_cb_state"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_circuit_breakers_entity", "circuit_breakers", ["entity_type", "entity_id"], unique=False)
    op.create_index("idx_circuit_breakers_state", "circuit_breakers", ["state"], unique=False, postgresql_where=sa.text("state != 'closed'"))

    # ========================================================================
    # MODULE: TELEMETRY
    # ========================================================================

    # Create llm_telemetry_hourly table
    op.create_table(
        "llm_telemetry_hourly",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("hour_bucket", sa.DateTime(timezone=True), nullable=False),
        sa.Column("provider_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("model_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("agent_type", sa.String(length=50), nullable=True),
        sa.Column("total_requests", sa.Integer(), nullable=True),
        sa.Column("successful_requests", sa.Integer(), nullable=True),
        sa.Column("failed_requests", sa.Integer(), nullable=True),
        sa.Column("timeout_requests", sa.Integer(), nullable=True),
        sa.Column("retried_requests", sa.Integer(), nullable=True),
        sa.Column("cached_requests", sa.Integer(), nullable=True),
        sa.Column("latency_p50_ms", sa.Integer(), nullable=True),
        sa.Column("latency_p95_ms", sa.Integer(), nullable=True),
        sa.Column("latency_p99_ms", sa.Integer(), nullable=True),
        sa.Column("avg_latency_ms", sa.Integer(), nullable=True),
        sa.Column("min_latency_ms", sa.Integer(), nullable=True),
        sa.Column("max_latency_ms", sa.Integer(), nullable=True),
        sa.Column("total_input_tokens", sa.Integer(), nullable=True),
        sa.Column("total_output_tokens", sa.Integer(), nullable=True),
        sa.Column("avg_input_tokens", sa.Integer(), nullable=True),
        sa.Column("avg_output_tokens", sa.Integer(), nullable=True),
        sa.Column("total_cost_usd", sa.DECIMAL(precision=12, scale=6), nullable=True),
        sa.Column("avg_cost_per_request", sa.DECIMAL(precision=10, scale=6), nullable=True),
        sa.Column("avg_time_to_first_token_ms", sa.Integer(), nullable=True),
        sa.Column("cache_hit_rate", sa.DECIMAL(precision=5, scale=4), nullable=True),
        sa.Column("retry_rate", sa.DECIMAL(precision=5, scale=4), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["provider_id"], ["llm_providers.id"]),
        sa.ForeignKeyConstraint(["model_id"], ["llm_models.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_telemetry_lookup", "llm_telemetry_hourly", [sa.text("hour_bucket DESC"), "provider_id", "model_id"], unique=False)
    op.create_index("idx_telemetry_agent", "llm_telemetry_hourly", [sa.text("hour_bucket DESC"), "agent_type"], unique=False)

    # Create llm_cost_daily table
    op.create_table(
        "llm_cost_daily",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("date", sa.DateTime(timezone=True), nullable=False),
        sa.Column("provider_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("total_cost_usd", sa.DECIMAL(precision=12, scale=6), nullable=True),
        sa.Column("total_requests", sa.Integer(), nullable=True),
        sa.Column("total_tokens", sa.Integer(), nullable=True),
        sa.Column("premium_cost_usd", sa.DECIMAL(precision=12, scale=6), nullable=True),
        sa.Column("standard_cost_usd", sa.DECIMAL(precision=12, scale=6), nullable=True),
        sa.Column("economy_cost_usd", sa.DECIMAL(precision=12, scale=6), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["provider_id"], ["llm_providers.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    # ========================================================================
    # MODULE: BUSINESS_CONFIG
    # ========================================================================

    # Create llm_business_config table
    op.create_table(
        "llm_business_config",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("config_key", sa.String(length=100), nullable=False),
        sa.Column("config_value", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("config_type", sa.String(length=50), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("modified_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("modified_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("previous_value", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("change_reason", sa.Text(), nullable=True),
        sa.Column("validation_schema", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("config_key"),
    )

    # Create llm_cost_budgets table
    op.create_table(
        "llm_cost_budgets",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("budget_type", sa.String(length=20), nullable=False),
        sa.Column("budget_amount_usd", sa.DECIMAL(precision=12, scale=2), nullable=False),
        sa.Column("warning_threshold_percent", sa.Integer(), nullable=True),
        sa.Column("critical_threshold_percent", sa.Integer(), nullable=True),
        sa.Column("current_spend_usd", sa.DECIMAL(precision=12, scale=2), nullable=True),
        sa.Column("period_start", sa.DateTime(timezone=True), nullable=True),
        sa.Column("period_end", sa.DateTime(timezone=True), nullable=True),
        sa.Column("is_hard_limit", sa.Boolean(), nullable=True),
        sa.Column("notify_emails", postgresql.ARRAY(sa.Text()), nullable=True),
        sa.Column("notify_slack_channel", sa.String(length=100), nullable=True),
        sa.Column("last_alert_sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint("budget_type IN ('daily', 'weekly', 'monthly')", name="valid_budget_type"),
        sa.PrimaryKeyConstraint("id"),
    )

    # Create llm_budget_alerts table
    op.create_table(
        "llm_budget_alerts",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("budget_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("alert_type", sa.String(length=20), nullable=False),
        sa.Column("threshold_percent", sa.Integer(), nullable=True),
        sa.Column("current_spend_usd", sa.DECIMAL(precision=12, scale=2), nullable=True),
        sa.Column("budget_amount_usd", sa.DECIMAL(precision=12, scale=2), nullable=True),
        sa.Column("notified_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("notification_channels", postgresql.ARRAY(sa.Text()), nullable=True),
        sa.ForeignKeyConstraint(["budget_id"], ["llm_cost_budgets.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    # ========================================================================
    # MODULE: AUDIT_LOG
    # ========================================================================

    # Create llm_audit_log table
    op.create_table(
        "llm_audit_log",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("action_type", sa.String(length=50), nullable=False),
        sa.Column("entity_type", sa.String(length=50), nullable=False),
        sa.Column("entity_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("actor_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("actor_ip", postgresql.INET(), nullable=True),
        sa.Column("before_value", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("after_value", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("change_reason", sa.Text(), nullable=True),
        sa.Column("timestamp", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_audit_actor", "llm_audit_log", ["actor_id", sa.text("timestamp DESC")], unique=False)
    op.create_index("idx_audit_entity", "llm_audit_log", ["entity_type", "entity_id", sa.text("timestamp DESC")], unique=False)

    # ========================================================================
    # MODULE: CACHING
    # ========================================================================

    # Create llm_response_cache table
    op.create_table(
        "llm_response_cache",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("cache_key", sa.String(length=64), nullable=False),
        sa.Column("agent_type", sa.String(length=50), nullable=True),
        sa.Column("prompt_hash", sa.String(length=64), nullable=True),
        sa.Column("model_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("temperature", sa.DECIMAL(precision=3, scale=2), nullable=True),
        sa.Column("response_content", sa.Text(), nullable=True),
        sa.Column("output_tokens", sa.Integer(), nullable=True),
        sa.Column("hit_count", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("last_hit_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["model_id"], ["llm_models.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("cache_key"),
    )
    op.create_index("idx_cache_key", "llm_response_cache", ["cache_key"], unique=False)
    op.create_index("idx_cache_expiry", "llm_response_cache", ["expires_at"], unique=False, postgresql_where=sa.text("expires_at IS NOT NULL"))

    # ========================================================================
    # SEED DATA
    # ========================================================================

    # Insert default providers
    op.execute(
        """
        INSERT INTO llm_providers (id, name, display_name, priority, config, is_enabled) VALUES
        (gen_random_uuid(), 'vertex_ai', 'Google Vertex AI', 1, '{"region": "us-central1"}'::jsonb, true),
        (gen_random_uuid(), 'deepinfra', 'DeepInfra', 2, '{"base_url": "https://api.deepinfra.com/v1/openai"}'::jsonb, true),
        (gen_random_uuid(), 'bedrock', 'AWS Bedrock', 3, '{"region": "us-east-1"}'::jsonb, true)
        """
    )

    # Insert default ranking weight profiles
    op.execute(
        """
        INSERT INTO ranking_weight_profiles (id, agent_type, success_weight, latency_weight, cost_weight, recency_weight) VALUES
        (gen_random_uuid(), 'swap_agent', 0.60, 0.25, 0.10, 0.05),
        (gen_random_uuid(), 'trading_agent', 0.55, 0.30, 0.10, 0.05),
        (gen_random_uuid(), 'portfolio_agent', 0.45, 0.20, 0.25, 0.10),
        (gen_random_uuid(), 'researcher', 0.40, 0.15, 0.30, 0.15),
        (gen_random_uuid(), 'risk_analyzer', 0.65, 0.20, 0.10, 0.05),
        (gen_random_uuid(), 'default', 0.50, 0.25, 0.15, 0.10)
        """
    )

    # Insert default business config
    op.execute(
        """
        INSERT INTO llm_business_config (id, config_key, config_value, config_type, description) VALUES
        (gen_random_uuid(), 'retry_config', '{"max_retries_per_provider": 2, "max_total_retries": 6, "initial_delay_ms": 100, "max_delay_ms": 5000, "backoff_multiplier": 2, "jitter": true}'::jsonb, 'threshold', 'Retry behavior configuration'),
        (gen_random_uuid(), 'timeout_config', '{"per_attempt_ms": 30000, "total_request_ms": 120000, "streaming_idle_ms": 10000}'::jsonb, 'threshold', 'Timeout configuration'),
        (gen_random_uuid(), 'rate_limits', '{"default_requests_per_minute": 60, "premium_requests_per_minute": 200, "burst_multiplier": 2}'::jsonb, 'limit', 'Rate limiting configuration'),
        (gen_random_uuid(), 'feature_flags', '{"enable_caching": true, "enable_streaming": true, "enable_cost_tracking": true, "enable_ranking": true}'::jsonb, 'feature_flag', 'Feature toggles')
        """
    )

    # Insert default budgets
    op.execute(
        """
        INSERT INTO llm_cost_budgets (id, name, budget_type, budget_amount_usd, warning_threshold_percent, critical_threshold_percent, is_hard_limit, current_spend_usd, period_start, period_end) VALUES
        (gen_random_uuid(), 'Daily Operations', 'daily', 500.00, 80, 95, false, 0, CURRENT_DATE, CURRENT_DATE + INTERVAL '1 day'),
        (gen_random_uuid(), 'Monthly Total', 'monthly', 10000.00, 80, 95, true, 0, DATE_TRUNC('month', CURRENT_DATE), DATE_TRUNC('month', CURRENT_DATE) + INTERVAL '1 month')
        """
    )


def downgrade() -> None:
    """Drop LLM orchestration tables."""

    # Drop tables in reverse order (respecting foreign keys)
    op.drop_table("llm_response_cache")
    op.drop_table("llm_audit_log")
    op.drop_table("llm_budget_alerts")
    op.drop_table("llm_cost_budgets")
    op.drop_table("llm_business_config")
    op.drop_table("llm_cost_daily")
    op.drop_table("llm_telemetry_hourly")
    op.drop_table("circuit_breakers")
    op.drop_table("llm_request_attempts")
    op.drop_table("llm_requests")
    op.drop_table("ranking_overrides")
    op.drop_table("agent_model_rankings")
    op.drop_table("ranking_weight_profiles")
    op.drop_table("llm_models")
    op.drop_table("llm_providers")
