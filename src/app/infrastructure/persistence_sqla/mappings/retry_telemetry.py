"""
Retry telemetry table mappings.

SQLAlchemy table definitions for retry telemetry.
"""
from sqlalchemy import Table, Column, String, Integer, Boolean, DateTime, Float, Date, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func

from app.infrastructure.persistence_sqla.registry import mapper_registry

metadata = mapper_registry.metadata

# Table 1: retry_attempts
retry_attempts = Table(
    "retry_attempts",
    metadata,
    Column("id", UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid()),
    Column("service_name", String(255), nullable=False, index=True),
    Column("attempt_number", Integer, nullable=False),
    Column("request_context", JSONB, nullable=True),
    Column("error_type", String(100), nullable=True),
    Column("error_message", Text, nullable=True),
    Column("latency_ms", Integer, nullable=True),
    Column("success", Boolean, nullable=True),
    Column("created_at", DateTime, nullable=False, server_default=func.current_timestamp()),
)

# Table 2: circuit_breaker_events
circuit_breaker_events = Table(
    "circuit_breaker_events",
    metadata,
    Column("id", UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid()),
    Column("service_name", String(255), nullable=False, index=True),
    Column("from_state", String(20), nullable=False),
    Column("to_state", String(20), nullable=False),
    Column("reason", Text, nullable=True),
    Column("failure_count", Integer, nullable=True, server_default="0"),
    Column("success_count", Integer, nullable=True, server_default="0"),
    Column("created_at", DateTime, nullable=False, server_default=func.current_timestamp()),
)

# Table 3: service_override_events
service_override_events = Table(
    "service_override_events",
    metadata,
    Column("id", UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid()),
    Column("service_name", String(255), nullable=False, index=True),
    Column("action", String(20), nullable=False),  # 'disable' or 'enable'
    Column("user_id", UUID(as_uuid=True), nullable=False),
    Column("reason", Text, nullable=True),
    Column("duration_minutes", Integer, nullable=True),
    Column("created_at", DateTime, nullable=False, server_default=func.current_timestamp()),
)

# Table 4: retry_metrics_aggregate
retry_metrics_aggregate = Table(
    "retry_metrics_aggregate",
    metadata,
    Column("id", UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid()),
    Column("service_name", String(255), nullable=False),
    Column("date", Date, nullable=False),
    Column("total_requests", Integer, nullable=False, server_default="0"),
    Column("successful_requests", Integer, nullable=False, server_default="0"),
    Column("failed_requests", Integer, nullable=False, server_default="0"),
    Column("retry_attempts", Integer, nullable=False, server_default="0"),
    Column("avg_latency_ms", Float, nullable=True),
    Column("p50_latency_ms", Integer, nullable=True),
    Column("p95_latency_ms", Integer, nullable=True),
    Column("p99_latency_ms", Integer, nullable=True),
    Column("circuit_breaker_opens", Integer, nullable=False, server_default="0"),
    Column("created_at", DateTime, nullable=False, server_default=func.current_timestamp()),
    Column("updated_at", DateTime, nullable=False, server_default=func.current_timestamp()),
)
