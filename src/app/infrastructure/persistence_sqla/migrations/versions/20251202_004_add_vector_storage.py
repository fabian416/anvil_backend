"""Add vector storage for embeddings

Revision ID: 20251202_004
Revises: 20251202_003
Create Date: 2025-12-02 12:00:00.000000

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "20251202_004"
down_revision = "20251202_003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Add vector storage tables for hybrid retrieval.

    Tables:
    - protocol_embeddings: Store protocol embeddings
    - entity_embeddings: Store embeddings for other entities
    """

    # Create protocol_embeddings table
    op.create_table(
        "protocol_embeddings",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("protocol_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("protocol_name", sa.String(255), nullable=False),
        sa.Column("text_content", sa.Text, nullable=False),  # Text that was embedded
        sa.Column(
            "embedding", postgresql.ARRAY(sa.Float), nullable=False
        ),  # Vector embedding
        sa.Column("embedding_model", sa.String(100), nullable=False),
        sa.Column("embedding_dimensions", sa.Integer, nullable=False),
        sa.Column(
            "created_at", sa.DateTime, nullable=False, server_default=sa.text("NOW()")
        ),
        sa.Column(
            "updated_at", sa.DateTime, nullable=False, server_default=sa.text("NOW()")
        ),
        # Indexes
        sa.Index("idx_protocol_embeddings_protocol_id", "protocol_id"),
        sa.Index("idx_protocol_embeddings_created_at", "created_at"),
    )

    # Create entity_embeddings table (for chains, tokens, etc.)
    op.create_table(
        "entity_embeddings",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("entity_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "entity_type", sa.String(50), nullable=False
        ),  # 'Token', 'Chain', etc.
        sa.Column("entity_name", sa.String(255), nullable=False),
        sa.Column("text_content", sa.Text, nullable=False),
        sa.Column("embedding", postgresql.ARRAY(sa.Float), nullable=False),
        sa.Column("embedding_model", sa.String(100), nullable=False),
        sa.Column("embedding_dimensions", sa.Integer, nullable=False),
        sa.Column(
            "created_at", sa.DateTime, nullable=False, server_default=sa.text("NOW()")
        ),
        sa.Column(
            "updated_at", sa.DateTime, nullable=False, server_default=sa.text("NOW()")
        ),
        # Indexes
        sa.Index("idx_entity_embeddings_entity_id", "entity_id"),
        sa.Index("idx_entity_embeddings_type", "entity_type"),
        sa.Index("idx_entity_embeddings_created_at", "created_at"),
    )

    # Create pgvector index for similarity search on protocol_embeddings
    # Note: This uses PostgreSQL array operations for cosine similarity
    # For production, consider using pgvector extension with vector type
    op.execute("""
        CREATE OR REPLACE FUNCTION cosine_similarity(a float[], b float[])
        RETURNS float AS $$
        DECLARE
            dot_product float := 0;
            norm_a float := 0;
            norm_b float := 0;
            i integer;
        BEGIN
            FOR i IN 1..array_length(a, 1) LOOP
                dot_product := dot_product + (a[i] * b[i]);
                norm_a := norm_a + (a[i] * a[i]);
                norm_b := norm_b + (b[i] * b[i]);
            END LOOP;
            
            IF norm_a = 0 OR norm_b = 0 THEN
                RETURN 0;
            END IF;
            
            RETURN dot_product / (sqrt(norm_a) * sqrt(norm_b));
        END;
        $$ LANGUAGE plpgsql IMMUTABLE PARALLEL SAFE;
    """)

    # Create helper function to find similar protocols
    op.execute("""
        CREATE OR REPLACE FUNCTION find_similar_protocols(
            query_embedding float[],
            similarity_threshold float DEFAULT 0.7,
            limit_count integer DEFAULT 10
        )
        RETURNS TABLE(
            protocol_id uuid,
            protocol_name varchar,
            similarity float
        ) AS $$
        BEGIN
            RETURN QUERY
            SELECT
                pe.protocol_id,
                pe.protocol_name,
                cosine_similarity(pe.embedding, query_embedding) as similarity
            FROM protocol_embeddings pe
            WHERE cosine_similarity(pe.embedding, query_embedding) >= similarity_threshold
            ORDER BY similarity DESC
            LIMIT limit_count;
        END;
        $$ LANGUAGE plpgsql STABLE PARALLEL SAFE;
    """)

    # Create statistics table for tracking embeddings
    op.create_table(
        "embedding_stats",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("entity_type", sa.String(50), nullable=False),
        sa.Column("total_embeddings", sa.Integer, nullable=False, server_default="0"),
        sa.Column(
            "last_updated", sa.DateTime, nullable=False, server_default=sa.text("NOW()")
        ),
        # Unique constraint on entity_type
        sa.UniqueConstraint("entity_type", name="uq_embedding_stats_entity_type"),
    )


def downgrade() -> None:
    """Remove vector storage tables"""

    # Drop tables
    op.drop_table("embedding_stats")
    op.drop_table("entity_embeddings")
    op.drop_table("protocol_embeddings")

    # Drop functions
    op.execute(
        "DROP FUNCTION IF EXISTS find_similar_protocols(float[], float, integer)"
    )
    op.execute("DROP FUNCTION IF EXISTS cosine_similarity(float[], float[])")
