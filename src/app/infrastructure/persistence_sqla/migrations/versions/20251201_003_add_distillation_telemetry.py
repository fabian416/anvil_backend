"""add distillation telemetry tables

Revision ID: 20251201_003
Revises: 20251201_002
Create Date: 2025-12-01 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '20251201_003'
down_revision = '20251201_002'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create distillation_telemetry table
    op.create_table(
        'distillation_telemetry',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('timestamp', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('conversation_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('request_hash', sa.String(64), nullable=False),
        sa.Column('detected_language', sa.String(10), nullable=True),
        sa.Column('provider', sa.String(50), nullable=False),
        sa.Column('model', sa.String(100), nullable=False),
        sa.Column('success', sa.Boolean, nullable=False),
        sa.Column('reason', sa.String(50), nullable=False),
        sa.Column('confidence', sa.Float, nullable=False),
        sa.Column('latency_ms', sa.Float, nullable=False),
        sa.Column('tokens_used', sa.Integer, nullable=False),
        sa.Column('cost_usd', sa.Numeric(10, 8), nullable=False),
        sa.Column('fallback_used', sa.Boolean, nullable=False, server_default='false'),
        sa.Column('error', sa.Text, nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('NOW()')),
    )
    
    # Create indexes for common queries
    op.create_index(
        'idx_distillation_telemetry_timestamp',
        'distillation_telemetry',
        ['timestamp'],
        postgresql_using='btree'
    )
    op.create_index(
        'idx_distillation_telemetry_user_id',
        'distillation_telemetry',
        ['user_id']
    )
    op.create_index(
        'idx_distillation_telemetry_success',
        'distillation_telemetry',
        ['success']
    )
    op.create_index(
        'idx_distillation_telemetry_provider',
        'distillation_telemetry',
        ['provider']
    )
    op.create_index(
        'idx_distillation_telemetry_created_at',
        'distillation_telemetry',
        ['created_at']
    )
    
    # Create materialized view for daily aggregations
    op.execute("""
        CREATE MATERIALIZED VIEW distillation_metrics_daily AS
        SELECT
            DATE(timestamp) as date,
            provider,
            COUNT(*) as total_requests,
            SUM(CASE WHEN success THEN 1 ELSE 0 END) as successful_requests,
            AVG(latency_ms) as avg_latency_ms,
            AVG(confidence) as avg_confidence,
            SUM(tokens_used) as total_tokens,
            SUM(cost_usd) as total_cost_usd,
            COUNT(DISTINCT user_id) as unique_users
        FROM distillation_telemetry
        GROUP BY DATE(timestamp), provider;
    """)
    
    # Create unique index on materialized view
    op.create_index(
        'idx_distillation_metrics_daily_date_provider',
        'distillation_metrics_daily',
        ['date', 'provider'],
        unique=True
    )


def downgrade() -> None:
    # Drop materialized view
    op.execute('DROP MATERIALIZED VIEW IF EXISTS distillation_metrics_daily')
    
    # Drop indexes
    op.drop_index('idx_distillation_telemetry_created_at', table_name='distillation_telemetry')
    op.drop_index('idx_distillation_telemetry_provider', table_name='distillation_telemetry')
    op.drop_index('idx_distillation_telemetry_success', table_name='distillation_telemetry')
    op.drop_index('idx_distillation_telemetry_user_id', table_name='distillation_telemetry')
    op.drop_index('idx_distillation_telemetry_timestamp', table_name='distillation_telemetry')
    
    # Drop table
    op.drop_table('distillation_telemetry')
