"""
SQLAlchemy mappings for distillation telemetry.

Defines the database table structure for telemetry data.
"""
from sqlalchemy import (
    Table,
    Column,
    String,
    Boolean,
    Float,
    Integer,
    Text,
    TIMESTAMP,
    Numeric,
    Index,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from app.infrastructure.persistence_sqla.registry import mapping_registry

# Distillation telemetry table
distillation_telemetry_table = Table(
    "distillation_telemetry",
    mapping_registry.metadata,
    Column("id", UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid()),
    Column("timestamp", TIMESTAMP(timezone=True), nullable=False, server_default=func.now()),
    Column("user_id", UUID(as_uuid=True), nullable=False),
    Column("conversation_id", UUID(as_uuid=True), nullable=False),
    Column("request_hash", String(64), nullable=False),
    Column("detected_language", String(10), nullable=True),
    Column("provider", String(50), nullable=False),
    Column("model", String(100), nullable=False),
    Column("success", Boolean, nullable=False),
    Column("reason", String(50), nullable=False),
    Column("confidence", Float, nullable=False),
    Column("latency_ms", Float, nullable=False),
    Column("tokens_used", Integer, nullable=False),
    Column("cost_usd", Numeric(10, 8), nullable=False),
    Column("fallback_used", Boolean, nullable=False, server_default="false"),
    Column("error", Text, nullable=True),
    Column("created_at", TIMESTAMP(timezone=True), nullable=False, server_default=func.now()),
    
    # Indexes
    Index("idx_distillation_telemetry_timestamp", "timestamp"),
    Index("idx_distillation_telemetry_user_id", "user_id"),
    Index("idx_distillation_telemetry_success", "success"),
    Index("idx_distillation_telemetry_provider", "provider"),
    Index("idx_distillation_telemetry_created_at", "created_at"),
)
