"""
LLM Orchestration System - SQLAlchemy Mappings.

Defines database tables for the Enterprise Multi-LLM Orchestration System.
"""

from sqlalchemy import (
    Table,
    Column,
    String,
    Integer,
    Float,
    Boolean,
    DateTime,
    Text,
    ForeignKey,
    CheckConstraint,
    Index,
    DECIMAL,
    ARRAY,
)
from sqlalchemy.dialects.postgresql import UUID, JSONB, INET
from sqlalchemy.sql import func
from uuid import uuid4

from app.infrastructure.persistence_sqla.registry import mapping_registry

metadata = mapping_registry.metadata


# ============================================================================
# MODULE: PROVIDER_MANAGEMENT - LLM Provider Configuration
# ============================================================================

llm_providers = Table(
    "llm_providers",
    metadata,
    Column("id", UUID(as_uuid=True), primary_key=True, default=uuid4),
    Column("name", String(50), nullable=False, unique=True),
    Column("display_name", String(100), nullable=False),
    Column("priority", Integer, nullable=False, default=1),
    Column("is_enabled", Boolean, default=True),
    Column("health_status", String(20), default="healthy"),
    Column("last_health_check", DateTime(timezone=True)),
    Column("health_check_interval_seconds", Integer, default=60),
    Column("config", JSONB, nullable=False, server_default="{}"),
    Column("rate_limits", JSONB, server_default="{}"),
    Column(
        "created_at", DateTime(timezone=True), nullable=False, server_default=func.now()
    ),
    Column(
        "updated_at",
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    ),
    CheckConstraint(
        "health_status IN ('healthy', 'degraded', 'down')",
        name="valid_health_status",
    ),
    CheckConstraint(
        "priority >= 1 AND priority <= 10",
        name="valid_priority",
    ),
)

Index(
    "idx_providers_priority",
    llm_providers.c.priority,
    postgresql_where=(llm_providers.c.is_enabled == True),
)


# ============================================================================
# MODULE: MODEL_CATALOG - Model Definitions and Capabilities
# ============================================================================

llm_models = Table(
    "llm_models",
    metadata,
    Column("id", UUID(as_uuid=True), primary_key=True, default=uuid4),
    Column(
        "provider_id",
        UUID(as_uuid=True),
        ForeignKey("llm_providers.id", ondelete="CASCADE"),
        nullable=False,
    ),
    Column("model_id", String(100), nullable=False),
    Column("display_name", String(100), nullable=False),
    Column("model_family", String(50)),
    Column("capabilities", JSONB, server_default="[]"),
    Column("context_window", Integer),
    Column("max_output_tokens", Integer),
    Column("supports_streaming", Boolean, default=True),
    Column("supports_tools", Boolean, default=True),
    Column("cost_per_1k_input", DECIMAL(10, 6)),
    Column("cost_per_1k_output", DECIMAL(10, 6)),
    Column("avg_latency_ms", Integer),
    Column("is_enabled", Boolean, default=True),
    Column("carousel_position", Integer, default=1),
    Column("tier", String(20), default="standard"),
    Column(
        "created_at", DateTime(timezone=True), nullable=False, server_default=func.now()
    ),
    Column(
        "updated_at",
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    ),
    CheckConstraint(
        "tier IN ('premium', 'standard', 'economy', 'experimental')",
        name="valid_tier",
    ),
)

Index(
    "idx_models_provider_enabled",
    llm_models.c.provider_id,
    llm_models.c.carousel_position,
    postgresql_where=(llm_models.c.is_enabled == True),
)

Index("idx_models_capabilities", llm_models.c.capabilities, postgresql_using="gin")


# ============================================================================
# MODULE: RANKING_SYSTEM - Adaptive Model Ranking
# ============================================================================

agent_model_rankings = Table(
    "agent_model_rankings",
    metadata,
    Column("id", UUID(as_uuid=True), primary_key=True, default=uuid4),
    Column("agent_type", String(50), nullable=False),
    Column(
        "model_id",
        UUID(as_uuid=True),
        ForeignKey("llm_models.id", ondelete="CASCADE"),
        nullable=False,
    ),
    Column("ranking_score", DECIMAL(5, 4), default=0.5000),
    Column("success_rate", DECIMAL(5, 4), default=0.0000),
    Column("latency_score", DECIMAL(5, 4), default=0.5000),
    Column("cost_score", DECIMAL(5, 4), default=0.5000),
    Column("total_requests", Integer, default=0),
    Column("successful_requests", Integer, default=0),
    Column("failed_requests", Integer, default=0),
    Column("timeout_requests", Integer, default=0),
    Column("avg_latency_ms", Integer, default=0),
    Column("p95_latency_ms", Integer, default=0),
    Column("avg_cost_per_request", DECIMAL(10, 6), default=0),
    Column("total_tokens_used", Integer, default=0),
    Column("last_used_at", DateTime(timezone=True)),
    Column("last_recalculated_at", DateTime(timezone=True), default=func.now()),
    Column(
        "updated_at",
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    ),
    CheckConstraint(
        "ranking_score >= 0 AND ranking_score <= 1 AND success_rate >= 0 AND success_rate <= 1",
        name="valid_scores",
    ),
)

Index(
    "idx_rankings_agent_score",
    agent_model_rankings.c.agent_type,
    agent_model_rankings.c.ranking_score.desc(),
)


ranking_weight_profiles = Table(
    "ranking_weight_profiles",
    metadata,
    Column("id", UUID(as_uuid=True), primary_key=True, default=uuid4),
    Column("agent_type", String(50), nullable=False, unique=True),
    Column("success_weight", DECIMAL(3, 2), default=0.50),
    Column("latency_weight", DECIMAL(3, 2), default=0.25),
    Column("cost_weight", DECIMAL(3, 2), default=0.15),
    Column("recency_weight", DECIMAL(3, 2), default=0.10),
    Column("min_requests_for_ranking", Integer, default=10),
    Column("recency_decay_hours", Integer, default=24),
    Column(
        "created_at", DateTime(timezone=True), nullable=False, server_default=func.now()
    ),
    Column(
        "updated_at",
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    ),
    CheckConstraint(
        "success_weight + latency_weight + cost_weight + recency_weight = 1.00",
        name="weights_sum_to_one",
    ),
)


ranking_overrides = Table(
    "ranking_overrides",
    metadata,
    Column("id", UUID(as_uuid=True), primary_key=True, default=uuid4),
    Column("agent_type", String(50), nullable=False),
    Column(
        "model_id",
        UUID(as_uuid=True),
        ForeignKey("llm_models.id", ondelete="CASCADE"),
        nullable=False,
    ),
    Column("override_score", DECIMAL(5, 4), nullable=False),
    Column("reason", Text),
    Column("created_by", UUID(as_uuid=True)),
    Column(
        "created_at", DateTime(timezone=True), nullable=False, server_default=func.now()
    ),
    Column("expires_at", DateTime(timezone=True)),
    CheckConstraint(
        "override_score >= 0 AND override_score <= 1",
        name="valid_override",
    ),
)


# ============================================================================
# MODULE: REQUEST_TRACKING - Full Request Lifecycle
# ============================================================================

llm_requests = Table(
    "llm_requests",
    metadata,
    Column("id", UUID(as_uuid=True), primary_key=True, default=uuid4),
    Column("request_id", String(100), unique=True, nullable=False),
    Column("user_id", UUID(as_uuid=True)),
    Column("agent_type", String(50), nullable=False),
    Column("session_id", UUID(as_uuid=True)),
    Column("prompt_hash", String(64)),
    Column("input_tokens", Integer),
    Column("max_output_tokens", Integer),
    Column("temperature", DECIMAL(3, 2)),
    Column("has_tools", Boolean, default=False),
    Column("is_streaming", Boolean, default=False),
    Column("status", String(30), nullable=False, default="pending"),
    Column("status_history", JSONB, server_default="[]"),
    Column("selected_provider_id", UUID(as_uuid=True), ForeignKey("llm_providers.id")),
    Column("selected_model_id", UUID(as_uuid=True), ForeignKey("llm_models.id")),
    Column("selection_reason", String(100)),
    Column("attempt_count", Integer, default=0),
    Column("total_latency_ms", Integer),
    Column("time_to_first_token_ms", Integer),
    Column("output_tokens", Integer),
    Column("estimated_cost_usd", DECIMAL(10, 6)),
    Column("actual_cost_usd", DECIMAL(10, 6)),
    Column("error_code", String(50)),
    Column("error_message", Text),
    Column(
        "created_at", DateTime(timezone=True), nullable=False, server_default=func.now()
    ),
    Column("started_at", DateTime(timezone=True)),
    Column("completed_at", DateTime(timezone=True)),
    CheckConstraint(
        "status IN ('pending', 'queued', 'selecting_model', 'executing', 'streaming', 'completed', 'failed', 'timeout', 'cancelled', 'retrying')",
        name="valid_status",
    ),
)

Index("idx_requests_status", llm_requests.c.status, llm_requests.c.created_at.desc())
Index("idx_requests_user", llm_requests.c.user_id, llm_requests.c.created_at.desc())
Index("idx_requests_agent", llm_requests.c.agent_type, llm_requests.c.created_at.desc())
Index(
    "idx_requests_model",
    llm_requests.c.selected_model_id,
    llm_requests.c.created_at.desc(),
)
Index(
    "idx_requests_provider",
    llm_requests.c.selected_provider_id,
    llm_requests.c.created_at.desc(),
)


llm_request_attempts = Table(
    "llm_request_attempts",
    metadata,
    Column("id", UUID(as_uuid=True), primary_key=True, default=uuid4),
    Column(
        "request_id",
        UUID(as_uuid=True),
        ForeignKey("llm_requests.id", ondelete="CASCADE"),
        nullable=False,
    ),
    Column("attempt_number", Integer, nullable=False),
    Column("provider_id", UUID(as_uuid=True), ForeignKey("llm_providers.id")),
    Column("model_id", UUID(as_uuid=True), ForeignKey("llm_models.id")),
    Column("status", String(30), nullable=False),
    Column("latency_ms", Integer),
    Column("input_tokens", Integer),
    Column("output_tokens", Integer),
    Column("cost_usd", DECIMAL(10, 6)),
    Column("error_type", String(50)),
    Column("error_code", String(50)),
    Column("error_message", Text),
    Column("started_at", DateTime(timezone=True), nullable=False),
    Column("completed_at", DateTime(timezone=True)),
    CheckConstraint(
        "status IN ('started', 'completed', 'failed', 'timeout', 'rate_limited', 'cancelled')",
        name="valid_attempt_status",
    ),
)

Index(
    "idx_attempts_request",
    llm_request_attempts.c.request_id,
    llm_request_attempts.c.attempt_number,
)


# ============================================================================
# MODULE: CIRCUIT_BREAKER - Failure Protection
# ============================================================================

circuit_breakers = Table(
    "circuit_breakers",
    metadata,
    Column("id", UUID(as_uuid=True), primary_key=True, default=uuid4),
    Column("entity_type", String(20), nullable=False),
    Column("entity_id", UUID(as_uuid=True), nullable=False),
    Column("entity_name", String(100)),
    Column("state", String(20), nullable=False, default="closed"),
    Column("failure_count", Integer, default=0),
    Column("success_count", Integer, default=0),
    Column("consecutive_failures", Integer, default=0),
    Column("last_failure_at", DateTime(timezone=True)),
    Column("last_success_at", DateTime(timezone=True)),
    Column("opened_at", DateTime(timezone=True)),
    Column("half_open_at", DateTime(timezone=True)),
    Column(
        "config",
        JSONB,
        server_default='{"failure_threshold": 5, "success_threshold": 3, "timeout_seconds": 60, "half_open_max_requests": 3}',
    ),
    Column(
        "updated_at",
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    ),
    CheckConstraint(
        "state IN ('closed', 'open', 'half_open')",
        name="valid_cb_state",
    ),
)

Index(
    "idx_circuit_breakers_entity",
    circuit_breakers.c.entity_type,
    circuit_breakers.c.entity_id,
)
Index(
    "idx_circuit_breakers_state",
    circuit_breakers.c.state,
    postgresql_where=(circuit_breakers.c.state != "closed"),
)


# ============================================================================
# MODULE: TELEMETRY - Metrics and Aggregations
# ============================================================================

llm_telemetry_hourly = Table(
    "llm_telemetry_hourly",
    metadata,
    Column("id", UUID(as_uuid=True), primary_key=True, default=uuid4),
    Column("hour_bucket", DateTime(timezone=True), nullable=False),
    Column("provider_id", UUID(as_uuid=True), ForeignKey("llm_providers.id")),
    Column("model_id", UUID(as_uuid=True), ForeignKey("llm_models.id")),
    Column("agent_type", String(50)),
    Column("total_requests", Integer, default=0),
    Column("successful_requests", Integer, default=0),
    Column("failed_requests", Integer, default=0),
    Column("timeout_requests", Integer, default=0),
    Column("retried_requests", Integer, default=0),
    Column("cached_requests", Integer, default=0),
    Column("latency_p50_ms", Integer),
    Column("latency_p95_ms", Integer),
    Column("latency_p99_ms", Integer),
    Column("avg_latency_ms", Integer),
    Column("min_latency_ms", Integer),
    Column("max_latency_ms", Integer),
    Column("total_input_tokens", Integer, default=0),
    Column("total_output_tokens", Integer, default=0),
    Column("avg_input_tokens", Integer),
    Column("avg_output_tokens", Integer),
    Column("total_cost_usd", DECIMAL(12, 6), default=0),
    Column("avg_cost_per_request", DECIMAL(10, 6)),
    Column("avg_time_to_first_token_ms", Integer),
    Column("cache_hit_rate", DECIMAL(5, 4)),
    Column("retry_rate", DECIMAL(5, 4)),
    Column(
        "created_at", DateTime(timezone=True), nullable=False, server_default=func.now()
    ),
)

Index(
    "idx_telemetry_lookup",
    llm_telemetry_hourly.c.hour_bucket.desc(),
    llm_telemetry_hourly.c.provider_id,
    llm_telemetry_hourly.c.model_id,
)
Index(
    "idx_telemetry_agent",
    llm_telemetry_hourly.c.hour_bucket.desc(),
    llm_telemetry_hourly.c.agent_type,
)


llm_cost_daily = Table(
    "llm_cost_daily",
    metadata,
    Column("id", UUID(as_uuid=True), primary_key=True, default=uuid4),
    Column("date", DateTime(timezone=True), nullable=False),
    Column("provider_id", UUID(as_uuid=True), ForeignKey("llm_providers.id")),
    Column("total_cost_usd", DECIMAL(12, 6), default=0),
    Column("total_requests", Integer, default=0),
    Column("total_tokens", Integer, default=0),
    Column("premium_cost_usd", DECIMAL(12, 6), default=0),
    Column("standard_cost_usd", DECIMAL(12, 6), default=0),
    Column("economy_cost_usd", DECIMAL(12, 6), default=0),
    Column(
        "created_at", DateTime(timezone=True), nullable=False, server_default=func.now()
    ),
)


# ============================================================================
# MODULE: BUSINESS_CONFIG - Runtime Configuration
# ============================================================================

llm_business_config = Table(
    "llm_business_config",
    metadata,
    Column("id", UUID(as_uuid=True), primary_key=True, default=uuid4),
    Column("config_key", String(100), unique=True, nullable=False),
    Column("config_value", JSONB, nullable=False),
    Column("config_type", String(50)),
    Column("description", Text),
    Column("modified_by", UUID(as_uuid=True)),
    Column("modified_at", DateTime(timezone=True), default=func.now()),
    Column("previous_value", JSONB),
    Column("change_reason", Text),
    Column("validation_schema", JSONB),
    Column(
        "created_at", DateTime(timezone=True), nullable=False, server_default=func.now()
    ),
)


llm_cost_budgets = Table(
    "llm_cost_budgets",
    metadata,
    Column("id", UUID(as_uuid=True), primary_key=True, default=uuid4),
    Column("name", String(100), nullable=False),
    Column("budget_type", String(20), nullable=False),
    Column("budget_amount_usd", DECIMAL(12, 2), nullable=False),
    Column("warning_threshold_percent", Integer, default=80),
    Column("critical_threshold_percent", Integer, default=95),
    Column("current_spend_usd", DECIMAL(12, 2), default=0),
    Column("period_start", DateTime(timezone=True)),
    Column("period_end", DateTime(timezone=True)),
    Column("is_hard_limit", Boolean, default=False),
    Column("notify_emails", ARRAY(Text)),
    Column("notify_slack_channel", String(100)),
    Column("last_alert_sent_at", DateTime(timezone=True)),
    Column("created_by", UUID(as_uuid=True)),
    Column(
        "created_at", DateTime(timezone=True), nullable=False, server_default=func.now()
    ),
    Column(
        "updated_at",
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    ),
    CheckConstraint(
        "budget_type IN ('daily', 'weekly', 'monthly')",
        name="valid_budget_type",
    ),
)


llm_budget_alerts = Table(
    "llm_budget_alerts",
    metadata,
    Column("id", UUID(as_uuid=True), primary_key=True, default=uuid4),
    Column(
        "budget_id",
        UUID(as_uuid=True),
        ForeignKey("llm_cost_budgets.id", ondelete="CASCADE"),
        nullable=False,
    ),
    Column("alert_type", String(20), nullable=False),
    Column("threshold_percent", Integer),
    Column("current_spend_usd", DECIMAL(12, 2)),
    Column("budget_amount_usd", DECIMAL(12, 2)),
    Column("notified_at", DateTime(timezone=True), default=func.now()),
    Column("notification_channels", ARRAY(Text)),
)


# ============================================================================
# MODULE: AUDIT_LOG - Configuration Change Tracking
# ============================================================================

llm_audit_log = Table(
    "llm_audit_log",
    metadata,
    Column("id", UUID(as_uuid=True), primary_key=True, default=uuid4),
    Column("action_type", String(50), nullable=False),
    Column("entity_type", String(50), nullable=False),
    Column("entity_id", UUID(as_uuid=True)),
    Column("actor_id", UUID(as_uuid=True)),
    Column("actor_ip", INET),
    Column("before_value", JSONB),
    Column("after_value", JSONB),
    Column("change_reason", Text),
    Column(
        "timestamp", DateTime(timezone=True), nullable=False, server_default=func.now()
    ),
)

Index("idx_audit_actor", llm_audit_log.c.actor_id, llm_audit_log.c.timestamp.desc())
Index(
    "idx_audit_entity",
    llm_audit_log.c.entity_type,
    llm_audit_log.c.entity_id,
    llm_audit_log.c.timestamp.desc(),
)


# ============================================================================
# MODULE: CACHING - Response Caching (Optional)
# ============================================================================

llm_response_cache = Table(
    "llm_response_cache",
    metadata,
    Column("id", UUID(as_uuid=True), primary_key=True, default=uuid4),
    Column("cache_key", String(64), nullable=False, unique=True),
    Column("agent_type", String(50)),
    Column("prompt_hash", String(64)),
    Column("model_id", UUID(as_uuid=True), ForeignKey("llm_models.id")),
    Column("temperature", DECIMAL(3, 2)),
    Column("response_content", Text),
    Column("output_tokens", Integer),
    Column("hit_count", Integer, default=0),
    Column(
        "created_at", DateTime(timezone=True), nullable=False, server_default=func.now()
    ),
    Column("last_hit_at", DateTime(timezone=True)),
    Column("expires_at", DateTime(timezone=True)),
)

Index("idx_cache_key", llm_response_cache.c.cache_key)
Index(
    "idx_cache_expiry",
    llm_response_cache.c.expires_at,
    postgresql_where=(llm_response_cache.c.expires_at.isnot(None)),
)
