"""Add retry telemetry tables

Revision ID: retry_telemetry_001
Revises: llm_orchestration_schema
Create Date: 2025-12-01 15:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'retry_telemetry_001'
down_revision = 'llm_orchestration_schema'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create retry telemetry tables."""
    
    # Table 1: retry_attempts
    op.create_table(
        'retry_attempts',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('service_name', sa.String(255), nullable=False, index=True),
        sa.Column('attempt_number', sa.Integer(), nullable=False),
        sa.Column('request_context', postgresql.JSONB(), nullable=True),
        sa.Column('error_type', sa.String(100), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('latency_ms', sa.Integer(), nullable=True),
        sa.Column('success', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
    )
    
    # Create composite index for service_name + created_at
    op.create_index(
        'idx_retry_attempts_service_created',
        'retry_attempts',
        ['service_name', 'created_at']
    )
    
    # Create index for success column
    op.create_index(
        'idx_retry_attempts_success',
        'retry_attempts',
        ['success']
    )
    
    # Table 2: circuit_breaker_events
    op.create_table(
        'circuit_breaker_events',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('service_name', sa.String(255), nullable=False, index=True),
        sa.Column('from_state', sa.String(20), nullable=False),
        sa.Column('to_state', sa.String(20), nullable=False),
        sa.Column('reason', sa.Text(), nullable=True),
        sa.Column('failure_count', sa.Integer(), nullable=True, server_default=sa.text('0')),
        sa.Column('success_count', sa.Integer(), nullable=True, server_default=sa.text('0')),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
    )
    
    # Create composite index for service_name + to_state + created_at
    op.create_index(
        'idx_circuit_events_service_state',
        'circuit_breaker_events',
        ['service_name', 'to_state', 'created_at']
    )
    
    # Table 3: service_override_events
    op.create_table(
        'service_override_events',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('service_name', sa.String(255), nullable=False, index=True),
        sa.Column('action', sa.String(20), nullable=False),  # 'disable' or 'enable'
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('reason', sa.Text(), nullable=True),
        sa.Column('duration_minutes', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
    )
    
    # Create composite index for service_name + action + created_at
    op.create_index(
        'idx_override_events_service_action',
        'service_override_events',
        ['service_name', 'action', 'created_at']
    )
    
    # Table 4: retry_metrics_aggregate (daily rollup)
    op.create_table(
        'retry_metrics_aggregate',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('service_name', sa.String(255), nullable=False),
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('total_requests', sa.Integer(), nullable=False, server_default=sa.text('0')),
        sa.Column('successful_requests', sa.Integer(), nullable=False, server_default=sa.text('0')),
        sa.Column('failed_requests', sa.Integer(), nullable=False, server_default=sa.text('0')),
        sa.Column('retry_attempts', sa.Integer(), nullable=False, server_default=sa.text('0')),
        sa.Column('avg_latency_ms', sa.Float(), nullable=True),
        sa.Column('p50_latency_ms', sa.Integer(), nullable=True),
        sa.Column('p95_latency_ms', sa.Integer(), nullable=True),
        sa.Column('p99_latency_ms', sa.Integer(), nullable=True),
        sa.Column('circuit_breaker_opens', sa.Integer(), nullable=False, server_default=sa.text('0')),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
    )
    
    # Create unique constraint for service_name + date
    op.create_unique_constraint(
        'uq_retry_metrics_service_date',
        'retry_metrics_aggregate',
        ['service_name', 'date']
    )
    
    # Create composite index for service_name + date DESC
    op.create_index(
        'idx_retry_metrics_service_date',
        'retry_metrics_aggregate',
        ['service_name', sa.text('date DESC')]
    )


def downgrade() -> None:
    """Drop retry telemetry tables."""
    op.drop_table('retry_metrics_aggregate')
    op.drop_table('service_override_events')
    op.drop_table('circuit_breaker_events')
    op.drop_table('retry_attempts')
