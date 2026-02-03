"""Add distillation system schema

Revision ID: 20251201_001
Revises:
Create Date: 2025-12-01 12:00:00.000000

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "20251201_001"
down_revision = None  # Update this to the latest migration
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create distillation system tables."""

    # Enable pgvector extension
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    # ============================================================================
    # 1. distillation_config - Configuration for distillation system
    # ============================================================================
    op.create_table(
        "distillation_config",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("uuid_generate_v4()"),
        ),
        sa.Column("config_key", sa.String(100), nullable=False, unique=True),
        sa.Column("config_value", postgresql.JSONB, nullable=False),
        sa.Column("description", sa.Text),
        sa.Column("modified_by", postgresql.UUID(as_uuid=True)),
        sa.Column(
            "modified_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("NOW()")
        ),
    )

    # Insert default configuration
    op.execute("""
        INSERT INTO distillation_config (config_key, config_value, description) VALUES
        ('feature_flags', '{
            "enabled": true,
            "cache_enabled": true,
            "static_responses_enabled": true,
            "semantic_cache_enabled": true
        }'::jsonb, 'Feature toggles for distillation'),
        
        ('thresholds', '{
            "min_confidence": 0.7,
            "semantic_similarity": 0.95,
            "max_latency_ms": 100
        }'::jsonb, 'Classification thresholds'),
        
        ('routing_rules', '{
            "force_full_llm_intents": ["swap_request", "borrow_request", "risk_assessment"],
            "cache_ttl_by_intent": {
                "price_check": 60,
                "explain_concept": 3600,
                "how_to": 3600
            }
        }'::jsonb, 'Routing configuration')
    """)

    # ============================================================================
    # 2. distillation_static_responses - Static response templates
    # ============================================================================
    op.create_table(
        "distillation_static_responses",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("uuid_generate_v4()"),
        ),
        sa.Column("intent", sa.String(50), nullable=False),
        sa.Column("variant", sa.String(50), nullable=False, server_default="default"),
        # Response template
        sa.Column("response_template", sa.Text, nullable=False),
        sa.Column("template_variables", postgresql.JSONB, server_default="[]"),
        sa.Column("data_source", sa.String(100)),
        # Conditions
        sa.Column("conditions", postgresql.JSONB, server_default="{}"),
        sa.Column("priority", sa.Integer, server_default="1"),
        # Status
        sa.Column("is_active", sa.Boolean, server_default="true"),
        sa.Column(
            "created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("NOW()")
        ),
        sa.Column(
            "updated_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("NOW()")
        ),
        sa.UniqueConstraint(
            "intent", "variant", name="uq_static_response_intent_variant"
        ),
    )

    # Insert default static responses
    op.execute("""
        INSERT INTO distillation_static_responses (intent, variant, response_template, data_source) VALUES
        ('greeting', 'default', 'Hello! I''m Anvil, your DeFi assistant. How can I help you today?', NULL),
        ('greeting', 'morning', 'Good morning! Ready to help with your DeFi needs.', NULL),
        ('greeting', 'evening', 'Good evening! What can I help you with?', NULL),
        ('price_check', 'default', 'The current price of {token} is ${price} ({change_24h}% 24h).', 'coingecko_api'),
        ('gas_check', 'default', 'Current gas prices on {chain}:\n• Low: {low} gwei\n• Average: {avg} gwei\n• High: {high} gwei', 'gas_api'),
        ('balance_check', 'default', 'Your portfolio value: ${total_value}\n\nTop holdings:\n{holdings_list}', 'portfolio_service'),
        ('off_topic', 'default', 'I''m specialized in DeFi and crypto assistance. I can help you with swaps, staking, lending, and other DeFi operations. What would you like to do?', NULL)
    """)

    # ============================================================================
    # 3. distillation_cache_exact - Exact match cache
    # ============================================================================
    op.create_table(
        "distillation_cache_exact",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("uuid_generate_v4()"),
        ),
        sa.Column(
            "cache_key", sa.String(64), nullable=False, unique=True
        ),  # SHA256 hash
        # Request signature
        sa.Column("normalized_query", sa.Text, nullable=False),
        sa.Column("intent", sa.String(50)),
        sa.Column("entities", postgresql.JSONB, server_default="{}"),
        # Cached response
        sa.Column("response_content", sa.Text, nullable=False),
        sa.Column("response_metadata", postgresql.JSONB, server_default="{}"),
        # Statistics
        sa.Column("hit_count", sa.Integer, server_default="0"),
        sa.Column(
            "created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("NOW()")
        ),
        sa.Column("last_hit_at", sa.TIMESTAMP(timezone=True)),
        sa.Column("expires_at", sa.TIMESTAMP(timezone=True), nullable=False),
        # Source
        sa.Column("source_model", sa.String(100)),
        sa.Column("source_request_id", postgresql.UUID(as_uuid=True)),
    )

    op.create_index("idx_cache_exact_key", "distillation_cache_exact", ["cache_key"])
    op.create_index(
        "idx_cache_exact_expiry", "distillation_cache_exact", ["expires_at"]
    )

    # ============================================================================
    # 4. distillation_cache_semantic - Semantic cache with vector embeddings
    # ============================================================================
    op.create_table(
        "distillation_cache_semantic",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("uuid_generate_v4()"),
        ),
        # Embedding (OpenAI text-embedding-3-small dimension)
        sa.Column(
            "query_embedding", postgresql.ARRAY(sa.Float), nullable=False
        ),  # Will be cast to vector in raw SQL
        sa.Column("original_query", sa.Text, nullable=False),
        # Classification
        sa.Column("intent", sa.String(50)),
        sa.Column("entities", postgresql.JSONB, server_default="{}"),
        # Cached response
        sa.Column("response_content", sa.Text, nullable=False),
        sa.Column("response_metadata", postgresql.JSONB, server_default="{}"),
        # Statistics
        sa.Column("hit_count", sa.Integer, server_default="0"),
        sa.Column(
            "created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("NOW()")
        ),
        sa.Column("last_hit_at", sa.TIMESTAMP(timezone=True)),
        sa.Column("expires_at", sa.TIMESTAMP(timezone=True), nullable=False),
        # Source
        sa.Column("source_model", sa.String(100)),
        sa.Column("source_request_id", postgresql.UUID(as_uuid=True)),
    )

    # Alter column type to vector after table creation
    op.execute(
        "ALTER TABLE distillation_cache_semantic ALTER COLUMN query_embedding TYPE vector(1536) USING query_embedding::vector(1536)"
    )

    # Create vector index for similarity search (IVFFlat)
    op.execute("""
        CREATE INDEX idx_cache_semantic_embedding ON distillation_cache_semantic 
        USING ivfflat (query_embedding vector_cosine_ops) WITH (lists = 100)
    """)

    # ============================================================================
    # 5. distillation_requests - Request log (TimescaleDB hypertable)
    # ============================================================================
    op.create_table(
        "distillation_requests",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("uuid_generate_v4()"),
        ),
        sa.Column("request_id", sa.String(100), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True)),
        # Input
        sa.Column("original_query", sa.Text, nullable=False),
        sa.Column("normalized_query", sa.Text),
        # Classification Results
        sa.Column("intent", sa.String(50)),
        sa.Column("intent_confidence", sa.Numeric(4, 3)),
        sa.Column("complexity", sa.String(20)),
        sa.Column("entities", postgresql.JSONB, server_default="{}"),
        # Routing Decision
        sa.Column(
            "route_type", sa.String(20), nullable=False
        ),  # REJECT, CACHE, STATIC, LIGHT_LLM, FULL_LLM
        sa.Column("routing_reason", sa.Text),
        sa.Column("suggested_model_tier", sa.String(20)),
        sa.Column("suggested_agent", sa.String(50)),
        # Cache info
        sa.Column("cache_key", sa.String(64)),
        sa.Column("cache_hit", sa.Boolean, server_default="false"),
        sa.Column("cache_level", sa.String(20)),  # exact, semantic, none
        # Performance
        sa.Column("classification_latency_ms", sa.Integer),
        sa.Column("total_latency_ms", sa.Integer),
        # Outcome
        sa.Column("was_processed", sa.Boolean),
        sa.Column("llm_request_id", postgresql.UUID(as_uuid=True)),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
    )

    # Convert to TimescaleDB hypertable
    op.execute("""
        SELECT create_hypertable('distillation_requests', 'created_at',
            chunk_time_interval => INTERVAL '1 day',
            if_not_exists => TRUE
        )
    """)

    op.create_index(
        "idx_distill_requests_user",
        "distillation_requests",
        ["user_id", sa.text("created_at DESC")],
    )
    op.create_index(
        "idx_distill_requests_route",
        "distillation_requests",
        ["route_type", sa.text("created_at DESC")],
    )
    op.create_index(
        "idx_distill_requests_intent",
        "distillation_requests",
        ["intent", sa.text("created_at DESC")],
    )

    # ============================================================================
    # 6. distillation_telemetry_hourly - Hourly aggregation
    # ============================================================================
    op.create_table(
        "distillation_telemetry_hourly",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("uuid_generate_v4()"),
        ),
        sa.Column("hour_bucket", sa.TIMESTAMP(timezone=True), nullable=False),
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
        sa.Column("cache_hit_rate", sa.Numeric(5, 4)),
        # Classification metrics
        sa.Column("avg_classification_latency_ms", sa.Integer),
        sa.Column("avg_confidence", sa.Numeric(4, 3)),
        # Intent distribution
        sa.Column("intent_distribution", postgresql.JSONB, server_default="{}"),
        # Cost savings
        sa.Column("estimated_cost_saved_usd", sa.Numeric(10, 4), server_default="0"),
        sa.Column(
            "created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("NOW()")
        ),
        sa.UniqueConstraint("hour_bucket", name="uq_telemetry_hour_bucket"),
    )

    # Convert to TimescaleDB hypertable
    op.execute("""
        SELECT create_hypertable('distillation_telemetry_hourly', 'hour_bucket',
            chunk_time_interval => INTERVAL '1 day',
            if_not_exists => TRUE
        )
    """)

    # ============================================================================
    # VIEWS
    # ============================================================================

    # View: Distillation Summary (last 24 hours)
    op.execute("""
        CREATE VIEW v_distillation_summary AS
        SELECT 
            DATE_TRUNC('hour', created_at) as hour,
            COUNT(*) as total_requests,
            COUNT(*) FILTER (WHERE route_type = 'CACHE') as cache_hits,
            COUNT(*) FILTER (WHERE route_type = 'STATIC') as static_responses,
            COUNT(*) FILTER (WHERE route_type = 'LIGHT_LLM') as light_llm,
            COUNT(*) FILTER (WHERE route_type = 'FULL_LLM') as full_llm,
            COUNT(*) FILTER (WHERE route_type = 'REJECT') as rejected,
            AVG(classification_latency_ms) as avg_classification_ms,
            AVG(intent_confidence) as avg_confidence
        FROM distillation_requests
        WHERE created_at > NOW() - INTERVAL '24 hours'
        GROUP BY DATE_TRUNC('hour', created_at)
        ORDER BY hour DESC
    """)


def downgrade() -> None:
    """Drop distillation system tables."""

    # Drop views
    op.execute("DROP VIEW IF EXISTS v_distillation_summary")

    # Drop tables (in reverse order)
    op.drop_table("distillation_telemetry_hourly")
    op.drop_table("distillation_requests")
    op.drop_table("distillation_cache_semantic")
    op.drop_table("distillation_cache_exact")
    op.drop_table("distillation_static_responses")
    op.drop_table("distillation_config")

    # Note: pgvector extension is not dropped as it might be used elsewhere
