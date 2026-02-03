"""Add graph schema for GraphRAG

Revision ID: 20251202_003
Revises: 20251201_002
Create Date: 2025-12-02 10:00:00.000000

This migration:
1. Installs Apache AGE extension for PostgreSQL
2. Creates the 'defi_knowledge_graph' graph
3. Creates performance indexes for common graph queries
4. Sets up metadata tables for graph management

Apache AGE (A Graph Extension) provides:
- Cypher query language support
- Native graph storage and traversal
- ACID transactions
- Integration with existing PostgreSQL data
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "20251202_003"
down_revision: Union[str, None] = "20251201_002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Install Apache AGE and create graph infrastructure.

    Prerequisites:
    - Apache AGE extension must be installed in PostgreSQL:
      sudo apt-get install postgresql-14-age  # Ubuntu/Debian
      brew install apache-age                 # macOS

    - Extension files must be in PostgreSQL extensions directory

    If AGE is not installed, this migration will fail with:
    "ERROR: could not open extension control file"
    """

    # =========================================================================
    # Step 1: Install Apache AGE Extension
    # =========================================================================

    # Create AGE extension (if not exists)
    op.execute("CREATE EXTENSION IF NOT EXISTS age;")

    # Load AGE into current session
    op.execute("LOAD 'age';")

    # Set search path to include ag_catalog (AGE's schema)
    op.execute("SET search_path = ag_catalog, '$user', public;")

    # =========================================================================
    # Step 2: Create DeFi Knowledge Graph
    # =========================================================================

    # Create the main graph for DeFi entities
    # This creates internal tables in ag_catalog schema
    op.execute("SELECT create_graph('defi_knowledge_graph');")

    # Note: AGE uses a schema-less model for nodes/edges
    # Labels and properties are stored as JSONB
    # No need to pre-define tables for each entity type

    # =========================================================================
    # Step 3: Create Metadata Tables
    # =========================================================================

    # Graph metadata table (tracks graph versions, stats, etc.)
    op.create_table(
        "graph_metadata",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("graph_name", sa.String(255), nullable=False, unique=True),
        sa.Column("version", sa.String(50), nullable=False, default="1.0.0"),
        sa.Column("node_count", sa.BigInteger, nullable=False, default=0),
        sa.Column("edge_count", sa.BigInteger, nullable=False, default=0),
        sa.Column("last_crawl_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "last_updated",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )

    # Seed initial metadata
    op.execute("""
        INSERT INTO graph_metadata (id, graph_name, version, node_count, edge_count)
        VALUES (
            gen_random_uuid(),
            'defi_knowledge_graph',
            '1.0.0',
            0,
            0
        );
    """)

    # Graph crawl history (tracks data ingestion runs)
    op.create_table(
        "graph_crawl_history",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("graph_name", sa.String(255), nullable=False),
        sa.Column(
            "data_source", sa.String(255), nullable=False
        ),  # e.g., 'defillama', 'immunefi'
        sa.Column(
            "crawl_type", sa.String(100), nullable=False
        ),  # e.g., 'full', 'incremental'
        sa.Column(
            "started_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "status", sa.String(50), nullable=False, default="in_progress"
        ),  # in_progress, completed, failed
        sa.Column("nodes_added", sa.Integer, nullable=False, default=0),
        sa.Column("edges_added", sa.Integer, nullable=False, default=0),
        sa.Column("nodes_updated", sa.Integer, nullable=False, default=0),
        sa.Column("errors", sa.JSON, nullable=True),
        sa.Column("metadata", sa.JSON, nullable=True),
    )

    # Create index on crawl history
    op.create_index(
        "idx_graph_crawl_history_started_at",
        "graph_crawl_history",
        ["started_at"],
        postgresql_using="btree",
    )

    # =========================================================================
    # Step 4: Create Performance Indexes
    # =========================================================================

    # Index on Protocol name (most common query)
    # Note: AGE stores properties as JSONB, so we use JSONB operators
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_protocol_name
        ON ag_catalog.ag_vertex ((properties->>'name'))
        WHERE label = (SELECT id FROM ag_catalog.ag_label WHERE name = 'Protocol');
    """)

    # Index on Protocol category
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_protocol_category
        ON ag_catalog.ag_vertex ((properties->>'category'))
        WHERE label = (SELECT id FROM ag_catalog.ag_label WHERE name = 'Protocol');
    """)

    # Index on Protocol TVL (for sorting)
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_protocol_tvl
        ON ag_catalog.ag_vertex (((properties->>'tvl')::numeric))
        WHERE label = (SELECT id FROM ag_catalog.ag_label WHERE name = 'Protocol');
    """)

    # Index on Token symbol and chain
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_token_symbol_chain
        ON ag_catalog.ag_vertex ((properties->>'symbol'), (properties->>'chain'))
        WHERE label = (SELECT id FROM ag_catalog.ag_label WHERE name = 'Token');
    """)

    # Index on Chain name
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_chain_name
        ON ag_catalog.ag_vertex ((properties->>'name'))
        WHERE label = (SELECT id FROM ag_catalog.ag_label WHERE name = 'Chain');
    """)

    # Index on Risk severity and active status
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_risk_severity_active
        ON ag_catalog.ag_vertex ((properties->>'severity'), ((properties->>'is_active')::boolean))
        WHERE label = (SELECT id FROM ag_catalog.ag_label WHERE name = 'Risk');
    """)

    # Index on Incident date and protocol
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_incident_date
        ON ag_catalog.ag_vertex (((properties->>'incident_date')::date))
        WHERE label = (SELECT id FROM ag_catalog.ag_label WHERE name = 'Incident');
    """)

    # Index on edge types (relationships)
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_edge_label
        ON ag_catalog.ag_edge (label);
    """)

    # =========================================================================
    # Step 5: Create Helper Functions
    # =========================================================================

    # Function to get node by ID
    op.execute("""
        CREATE OR REPLACE FUNCTION get_node_by_id(
            graph_name text,
            node_id text
        )
        RETURNS jsonb
        LANGUAGE plpgsql
        AS $$
        DECLARE
            result jsonb;
        BEGIN
            EXECUTE format(
                'SELECT * FROM cypher(%L, $$
                    MATCH (n {id: %L})
                    RETURN n
                $$) as (n agtype);',
                graph_name,
                node_id
            ) INTO result;
            
            RETURN result;
        END;
        $$;
    """)

    # Function to count nodes by label
    op.execute("""
        CREATE OR REPLACE FUNCTION count_nodes_by_label(
            graph_name text,
            label_name text
        )
        RETURNS bigint
        LANGUAGE plpgsql
        AS $$
        DECLARE
            result bigint;
        BEGIN
            EXECUTE format(
                'SELECT count(*) FROM cypher(%L, $$
                    MATCH (n:%I)
                    RETURN count(n)
                $$) as (count agtype);',
                graph_name,
                label_name
            ) INTO result;
            
            RETURN result;
        END;
        $$;
    """)

    # Function to update graph statistics
    op.execute("""
        CREATE OR REPLACE FUNCTION update_graph_stats(
            graph_name text
        )
        RETURNS void
        LANGUAGE plpgsql
        AS $$
        DECLARE
            total_nodes bigint;
            total_edges bigint;
        BEGIN
            -- Count nodes
            SELECT COUNT(*) INTO total_nodes
            FROM ag_catalog.ag_vertex
            WHERE graphid IN (
                SELECT graphid FROM ag_catalog.ag_graph WHERE name = graph_name
            );
            
            -- Count edges
            SELECT COUNT(*) INTO total_edges
            FROM ag_catalog.ag_edge
            WHERE graphid IN (
                SELECT graphid FROM ag_catalog.ag_graph WHERE name = graph_name
            );
            
            -- Update metadata
            UPDATE graph_metadata
            SET 
                node_count = total_nodes,
                edge_count = total_edges,
                last_updated = NOW()
            WHERE graph_metadata.graph_name = update_graph_stats.graph_name;
        END;
        $$;
    """)

    # =========================================================================
    # Step 6: Create Trigger for Auto-Updating Stats
    # =========================================================================

    # Note: AGE doesn't support triggers on ag_vertex/ag_edge directly
    # Stats will be updated via periodic Celery task instead

    # =========================================================================
    # Step 7: Grant Permissions
    # =========================================================================

    # Grant necessary permissions to application user
    # Adjust 'anvil_user' to match your application database user
    op.execute("""
        GRANT USAGE ON SCHEMA ag_catalog TO PUBLIC;
    """)

    op.execute("""
        GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA ag_catalog TO PUBLIC;
    """)

    print("✅ Graph schema migration complete!")
    print("📊 Created graph: defi_knowledge_graph")
    print("🔍 Created 7 performance indexes")
    print("🛠️  Created 3 helper functions")
    print("📝 Next steps:")
    print("   1. Run protocol crawler to populate graph")
    print("   2. Verify with: SELECT * FROM ag_catalog.ag_graph;")
    print(
        "   3. Test query: SELECT * FROM cypher('defi_knowledge_graph', $$ MATCH (n) RETURN n LIMIT 10 $$) as (n agtype);"
    )


def downgrade() -> None:
    """
    Remove graph infrastructure.

    WARNING: This will delete ALL graph data!
    """

    # Drop helper functions
    op.execute("DROP FUNCTION IF EXISTS get_node_by_id(text, text);")
    op.execute("DROP FUNCTION IF EXISTS count_nodes_by_label(text, text);")
    op.execute("DROP FUNCTION IF EXISTS update_graph_stats(text);")

    # Drop metadata tables
    op.drop_table("graph_crawl_history")
    op.drop_table("graph_metadata")

    # Drop the graph (this removes all nodes and edges)
    op.execute("SELECT drop_graph('defi_knowledge_graph', true);")

    # Note: We don't drop the AGE extension itself
    # as it might be used by other applications
    # To fully remove AGE: DROP EXTENSION age CASCADE;

    print("✅ Graph schema downgrade complete!")
    print("⚠️  All graph data has been deleted!")
