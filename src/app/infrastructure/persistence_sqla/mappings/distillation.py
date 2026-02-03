"""SQLAlchemy mappings for distillation system."""

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import (
    Boolean,
    Column,
    Integer,
    Numeric,
    String,
    Table,
    Text,
    TIMESTAMP,
)
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID as PGUUID
from sqlalchemy.orm import registry

mapper_registry = registry()


# ============================================================================
# Distillation Config
# ============================================================================
distillation_config = Table(
    "distillation_config",
    mapper_registry.metadata,
    Column("id", PGUUID(as_uuid=True), primary_key=True, default=uuid4),
    Column("config_key", String(100), nullable=False, unique=True),
    Column("config_value", JSONB, nullable=False),
    Column("description", Text),
    Column("modified_by", PGUUID(as_uuid=True)),
    Column("modified_at", TIMESTAMP(timezone=True), default=datetime.utcnow),
)


# ============================================================================
# Static Responses
# ============================================================================
distillation_static_responses = Table(
    "distillation_static_responses",
    mapper_registry.metadata,
    Column("id", PGUUID(as_uuid=True), primary_key=True, default=uuid4),
    Column("intent", String(50), nullable=False),
    Column("variant", String(50), nullable=False, default="default"),
    # Response template
    Column("response_template", Text, nullable=False),
    Column("template_variables", JSONB, default=list),
    Column("data_source", String(100)),
    # Conditions
    Column("conditions", JSONB, default=dict),
    Column("priority", Integer, default=1),
    # Status
    Column("is_active", Boolean, default=True),
    Column("created_at", TIMESTAMP(timezone=True), default=datetime.utcnow),
    Column(
        "updated_at",
        TIMESTAMP(timezone=True),
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    ),
)


# ============================================================================
# Exact Cache
# ============================================================================
distillation_cache_exact = Table(
    "distillation_cache_exact",
    mapper_registry.metadata,
    Column("id", PGUUID(as_uuid=True), primary_key=True, default=uuid4),
    Column("cache_key", String(64), nullable=False, unique=True),
    # Request signature
    Column("normalized_query", Text, nullable=False),
    Column("intent", String(50)),
    Column("entities", JSONB, default=dict),
    # Cached response
    Column("response_content", Text, nullable=False),
    Column("response_metadata", JSONB, default=dict),
    # Statistics
    Column("hit_count", Integer, default=0),
    Column("created_at", TIMESTAMP(timezone=True), default=datetime.utcnow),
    Column("last_hit_at", TIMESTAMP(timezone=True)),
    Column("expires_at", TIMESTAMP(timezone=True), nullable=False),
    # Source
    Column("source_model", String(100)),
    Column("source_request_id", PGUUID(as_uuid=True)),
)


# ============================================================================
# Semantic Cache
# ============================================================================
distillation_cache_semantic = Table(
    "distillation_cache_semantic",
    mapper_registry.metadata,
    Column("id", PGUUID(as_uuid=True), primary_key=True, default=uuid4),
    # Embedding (stored as ARRAY, converted to vector by migration)
    Column("query_embedding", ARRAY(Numeric)),  # Will be vector(1536) in DB
    Column("original_query", Text, nullable=False),
    # Classification
    Column("intent", String(50)),
    Column("entities", JSONB, default=dict),
    # Cached response
    Column("response_content", Text, nullable=False),
    Column("response_metadata", JSONB, default=dict),
    # Statistics
    Column("hit_count", Integer, default=0),
    Column("created_at", TIMESTAMP(timezone=True), default=datetime.utcnow),
    Column("last_hit_at", TIMESTAMP(timezone=True)),
    Column("expires_at", TIMESTAMP(timezone=True), nullable=False),
    # Source
    Column("source_model", String(100)),
    Column("source_request_id", PGUUID(as_uuid=True)),
)


# ============================================================================
# Request Log (TimescaleDB)
# ============================================================================
distillation_requests = Table(
    "distillation_requests",
    mapper_registry.metadata,
    Column("id", PGUUID(as_uuid=True), primary_key=True, default=uuid4),
    Column("request_id", String(100), nullable=False),
    Column("user_id", PGUUID(as_uuid=True)),
    # Input
    Column("original_query", Text, nullable=False),
    Column("normalized_query", Text),
    # Classification Results
    Column("intent", String(50)),
    Column("intent_confidence", Numeric(4, 3)),
    Column("complexity", String(20)),
    Column("entities", JSONB, default=dict),
    # Routing Decision
    Column("route_type", String(20), nullable=False),
    Column("routing_reason", Text),
    Column("suggested_model_tier", String(20)),
    Column("suggested_agent", String(50)),
    # Cache info
    Column("cache_key", String(64)),
    Column("cache_hit", Boolean, default=False),
    Column("cache_level", String(20)),
    # Performance
    Column("classification_latency_ms", Integer),
    Column("total_latency_ms", Integer),
    # Outcome
    Column("was_processed", Boolean),
    Column("llm_request_id", PGUUID(as_uuid=True)),
    Column(
        "created_at", TIMESTAMP(timezone=True), nullable=False, default=datetime.utcnow
    ),
)


# ============================================================================
# Telemetry Hourly (TimescaleDB)
# ============================================================================
distillation_telemetry_hourly = Table(
    "distillation_telemetry_hourly",
    mapper_registry.metadata,
    Column("id", PGUUID(as_uuid=True), primary_key=True, default=uuid4),
    Column("hour_bucket", TIMESTAMP(timezone=True), nullable=False, unique=True),
    # Counts by route type
    Column("total_requests", Integer, default=0),
    Column("rejected_count", Integer, default=0),
    Column("cache_hit_count", Integer, default=0),
    Column("static_response_count", Integer, default=0),
    Column("light_llm_count", Integer, default=0),
    Column("full_llm_count", Integer, default=0),
    # Cache metrics
    Column("exact_cache_hits", Integer, default=0),
    Column("semantic_cache_hits", Integer, default=0),
    Column("cache_hit_rate", Numeric(5, 4)),
    # Classification metrics
    Column("avg_classification_latency_ms", Integer),
    Column("avg_confidence", Numeric(4, 3)),
    # Intent distribution
    Column("intent_distribution", JSONB, default=dict),
    # Cost savings
    Column("estimated_cost_saved_usd", Numeric(10, 4), default=0),
    Column("created_at", TIMESTAMP(timezone=True), default=datetime.utcnow),
)


def map_distillation_tables() -> None:
    """Register distillation system tables with SQLAlchemy."""
    # Tables are already defined above and registered with mapper_registry.metadata
    # This function exists to match the pattern used by other mappings
    pass
