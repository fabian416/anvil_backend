"""create_projects_and_distillation_tables

Create missing tables for projects and distillation systems:
- project_knowledge_bases: Knowledge base configuration
- project_knowledge_documents: Knowledge documents with processing status
- project_analytics_daily: Daily analytics aggregation
- distillation_cache_exact: Exact match cache
- distillation_cache_semantic: Semantic similarity cache
- distillation_requests: Request logging
- distillation_telemetry_hourly: Hourly telemetry aggregation

Revision ID: 227b2c9cb872
Revises: money_market_core_001
Create Date: 2026-01-28 16:08:47.827815

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY, NUMERIC


# revision identifiers, used by Alembic.
revision: str = "227b2c9cb872"
down_revision: Union[str, None] = "money_market_core_001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create projects and distillation tables."""
    
    # Check if tables exist before creating (idempotent migration)
    from sqlalchemy import inspect
    conn = op.get_bind()
    inspector = inspect(conn)
    existing_tables = inspector.get_table_names()
    
    # =========================================================================
    # PROJECT KNOWLEDGE BASES
    # =========================================================================
    if "project_knowledge_bases" not in existing_tables:
        op.create_table(
        "project_knowledge_bases",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("project_id", UUID(as_uuid=True), nullable=False),
        
        # Configuration
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("description", sa.Text),
        
        # Embedding settings
        sa.Column("embedding_model", sa.String(100), server_default="text-embedding-3-small"),
        sa.Column("chunk_size", sa.Integer, server_default="500"),
        sa.Column("chunk_overlap", sa.Integer, server_default="50"),
        
        # Statistics
        sa.Column("total_documents", sa.Integer, server_default="0"),
        sa.Column("total_chunks", sa.Integer, server_default="0"),
        
        # Status
        sa.Column("status", sa.String(20), server_default="active"),
        sa.Column("last_indexed_at", sa.TIMESTAMP(timezone=True)),
        
            sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
            sa.Column("updated_at", sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
        )
        
        op.create_index(
            "ix_project_knowledge_bases_project_id",
            "project_knowledge_bases",
            ["project_id"],
        )
    
    # =========================================================================
    # PROJECT KNOWLEDGE DOCUMENTS
    # =========================================================================
    if "project_knowledge_documents" not in existing_tables:
        op.create_table(
        "project_knowledge_documents",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("knowledge_base_id", UUID(as_uuid=True), nullable=False),
        
        # Content
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("content", sa.Text, nullable=False),
        sa.Column("doc_type", sa.String(50), nullable=False),
        
        # Source
        sa.Column("source_url", sa.Text),
        sa.Column("source_type", sa.String(50), server_default="manual"),
        
        # Metadata
        sa.Column("tags", ARRAY(sa.Text), server_default="{}"),
        sa.Column("priority", sa.Integer, server_default="1"),
        
        # Processing status
        sa.Column("is_processed", sa.Boolean, server_default="false"),
        sa.Column("chunk_count", sa.Integer, server_default="0"),
        sa.Column("processing_error", sa.Text),
        
            sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
            sa.Column("updated_at", sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
        )
        
        op.create_index(
            "ix_project_knowledge_documents_knowledge_base_id",
            "project_knowledge_documents",
            ["knowledge_base_id"],
        )
        op.create_index(
            "ix_project_knowledge_documents_is_processed",
            "project_knowledge_documents",
            ["is_processed"],
        )
    
    # =========================================================================
    # PROJECT ANALYTICS DAILY
    # =========================================================================
    if "project_analytics_daily" not in existing_tables:
        op.create_table(
        "project_analytics_daily",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("project_id", UUID(as_uuid=True), nullable=False),
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
        sa.Column("avg_messages_per_session", NUMERIC(6, 2)),
        
        # Engagement
        sa.Column("satisfaction_score_avg", NUMERIC(3, 2)),
        sa.Column("helpful_rate", NUMERIC(5, 4)),
        
        # Knowledge usage
        sa.Column("knowledge_queries", sa.Integer, server_default="0"),
        sa.Column("knowledge_hit_rate", NUMERIC(5, 4)),
        sa.Column("top_queries", JSONB, server_default="[]"),
        
        # Transactions
        sa.Column("total_transactions", sa.Integer, server_default="0"),
        sa.Column("total_volume_usd", NUMERIC(20, 2), server_default="0"),
        sa.Column("transaction_success_rate", NUMERIC(5, 4)),
        
        # Tools
        sa.Column("tool_usage", JSONB, server_default="{}"),
        
            sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
        )
        
        op.create_index(
            "ix_project_analytics_daily_project_date",
            "project_analytics_daily",
            ["project_id", "date"],
            unique=True,
        )
    
    # =========================================================================
    # DISTILLATION CACHE EXACT
    # =========================================================================
    if "distillation_cache_exact" not in existing_tables:
        op.create_table(
        "distillation_cache_exact",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("cache_key", sa.String(64), nullable=False, unique=True),
        
        # Request signature
        sa.Column("normalized_query", sa.Text, nullable=False),
        sa.Column("intent", sa.String(50)),
        sa.Column("entities", JSONB, server_default="{}"),
        
        # Cached response
        sa.Column("response_content", sa.Text, nullable=False),
        sa.Column("response_metadata", JSONB, server_default="{}"),
        
        # Statistics
        sa.Column("hit_count", sa.Integer, server_default="0"),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
        sa.Column("last_hit_at", sa.TIMESTAMP(timezone=True)),
        sa.Column("expires_at", sa.TIMESTAMP(timezone=True), nullable=False),
        
        # Source
            sa.Column("source_model", sa.String(100)),
            sa.Column("source_request_id", UUID(as_uuid=True)),
        )
        
        op.create_index(
            "ix_distillation_cache_exact_cache_key",
            "distillation_cache_exact",
            ["cache_key"],
            unique=True,
        )
        op.create_index(
            "ix_distillation_cache_exact_expires_at",
            "distillation_cache_exact",
            ["expires_at"],
        )
    
    # =========================================================================
    # DISTILLATION CACHE SEMANTIC
    # =========================================================================
    if "distillation_cache_semantic" not in existing_tables:
        op.create_table(
        "distillation_cache_semantic",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        
        # Embedding (stored as ARRAY)
        sa.Column("query_embedding", ARRAY(NUMERIC), nullable=True),
        sa.Column("original_query", sa.Text, nullable=False),
        
        # Classification
        sa.Column("intent", sa.String(50)),
        sa.Column("entities", JSONB, server_default="{}"),
        
        # Cached response
        sa.Column("response_content", sa.Text, nullable=False),
        sa.Column("response_metadata", JSONB, server_default="{}"),
        
        # Statistics
        sa.Column("hit_count", sa.Integer, server_default="0"),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
        sa.Column("last_hit_at", sa.TIMESTAMP(timezone=True)),
        sa.Column("expires_at", sa.TIMESTAMP(timezone=True), nullable=False),
        
        # Source
            sa.Column("source_model", sa.String(100)),
            sa.Column("source_request_id", UUID(as_uuid=True)),
        )
        
        op.create_index(
            "ix_distillation_cache_semantic_expires_at",
            "distillation_cache_semantic",
            ["expires_at"],
        )
    
    # =========================================================================
    # DISTILLATION REQUESTS
    # =========================================================================
    if "distillation_requests" not in existing_tables:
        op.create_table(
        "distillation_requests",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("request_id", sa.String(100), nullable=False),
        sa.Column("user_id", UUID(as_uuid=True)),
        
        # Input
        sa.Column("original_query", sa.Text, nullable=False),
        sa.Column("normalized_query", sa.Text),
        
        # Classification Results
        sa.Column("intent", sa.String(50)),
        sa.Column("intent_confidence", NUMERIC(4, 3)),
        sa.Column("complexity", sa.String(20)),
        sa.Column("entities", JSONB, server_default="{}"),
        
        # Routing Decision
        sa.Column("route_type", sa.String(20), nullable=False),
        sa.Column("routing_reason", sa.Text),
        sa.Column("suggested_model_tier", sa.String(20)),
        sa.Column("suggested_agent", sa.String(50)),
        
        # Cache info
        sa.Column("cache_key", sa.String(64)),
        sa.Column("cache_hit", sa.Boolean, server_default="false"),
        sa.Column("cache_level", sa.String(20)),
        
        # Performance
        sa.Column("classification_latency_ms", sa.Integer),
        sa.Column("total_latency_ms", sa.Integer),
        
        # Outcome
        sa.Column("was_processed", sa.Boolean),
        sa.Column("llm_request_id", UUID(as_uuid=True)),
        
            sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now()),
        )
        
        op.create_index(
            "idx_distill_requests_created_at",
            "distillation_requests",
            ["created_at"],
        )
        op.create_index(
            "idx_distill_requests_intent",
            "distillation_requests",
            ["intent"],
        )
        op.create_index(
            "idx_distill_requests_route",
            "distillation_requests",
            ["route_type"],
        )
        op.create_index(
            "idx_distill_requests_user",
            "distillation_requests",
            ["user_id"],
        )
    
    # =========================================================================
    # DISTILLATION TELEMETRY HOURLY
    # =========================================================================
    if "distillation_telemetry_hourly" not in existing_tables:
        op.create_table(
        "distillation_telemetry_hourly",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("hour_bucket", sa.TIMESTAMP(timezone=True), nullable=False, unique=True),
        
        # Counts by route type
        sa.Column("total_requests", sa.Integer, server_default="0"),
        sa.Column("rejected_count", sa.Integer, server_default="0"),
        sa.Column("cache_hit_count", sa.Integer, server_default="0"),
        sa.Column("static_response_count", sa.Integer, server_default="0"),
        sa.Column("light_llm_count", sa.Integer, server_default="0"),
        sa.Column("full_llm_count", sa.Integer, server_default="0"),
        
        # Cache metrics
        sa.Column("exact_cache_hits", sa.Integer, server_default="0"),
        sa.Column("semantic_cache_hits", sa.Integer, server_default="0"),
        sa.Column("cache_hit_rate", NUMERIC(5, 4)),
        
        # Classification metrics
        sa.Column("avg_classification_latency_ms", sa.Integer),
        sa.Column("avg_confidence", NUMERIC(4, 3)),
        
        # Intent distribution
        sa.Column("intent_distribution", JSONB, server_default="{}"),
        
        # Cost savings
        sa.Column("estimated_cost_saved_usd", NUMERIC(10, 4), server_default="0"),
        
            sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
        )
        
        op.create_index(
            "idx_distillation_telemetry_hourly_hour_bucket",
            "distillation_telemetry_hourly",
            ["hour_bucket"],
            unique=True,
        )


def downgrade() -> None:
    """Drop projects and distillation tables."""
    
    op.drop_index("idx_distillation_telemetry_hourly_hour_bucket", table_name="distillation_telemetry_hourly")
    op.drop_table("distillation_telemetry_hourly")
    
    op.drop_index("idx_distill_requests_user", table_name="distillation_requests")
    op.drop_index("idx_distill_requests_route", table_name="distillation_requests")
    op.drop_index("idx_distill_requests_intent", table_name="distillation_requests")
    op.drop_index("idx_distill_requests_created_at", table_name="distillation_requests")
    op.drop_table("distillation_requests")
    
    op.drop_index("ix_distillation_cache_semantic_expires_at", table_name="distillation_cache_semantic")
    op.drop_table("distillation_cache_semantic")
    
    op.drop_index("ix_distillation_cache_exact_expires_at", table_name="distillation_cache_exact")
    op.drop_index("ix_distillation_cache_exact_cache_key", table_name="distillation_cache_exact")
    op.drop_table("distillation_cache_exact")
    
    op.drop_index("ix_project_analytics_daily_project_date", table_name="project_analytics_daily")
    op.drop_table("project_analytics_daily")
    
    op.drop_index("ix_project_knowledge_documents_is_processed", table_name="project_knowledge_documents")
    op.drop_index("ix_project_knowledge_documents_knowledge_base_id", table_name="project_knowledge_documents")
    op.drop_table("project_knowledge_documents")
    
    op.drop_index("ix_project_knowledge_bases_project_id", table_name="project_knowledge_bases")
    op.drop_table("project_knowledge_bases")
