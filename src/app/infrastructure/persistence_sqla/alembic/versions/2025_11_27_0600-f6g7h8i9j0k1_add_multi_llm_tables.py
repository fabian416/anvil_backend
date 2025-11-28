"""
Add Multi-LLM tables (DeepInfra, AgentModelConfigs, AgentPerformanceStats).

Revision ID: f6g7h8i9j0k1
Revises: e5f6g7h8i9j0
Create Date: 2025-11-27 06:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'f6g7h8i9j0k1'
down_revision: Union[str, None] = 'e5f6g7h8i9j0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    # --- Create Agent Model Configs ---
    op.create_table(
        'agent_model_configs',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('agent_type', sa.String(length=50), nullable=False),
        sa.Column('provider', postgresql.ENUM('OPENAI', 'ANTHROPIC', 'VERTEX', 'BEDROCK', 'DEEPINFRA', 'OTHER', name='llmprovider', create_type=False), nullable=False),
        sa.Column('model_name', sa.String(length=100), nullable=False),
        sa.Column('priority', sa.Integer(), nullable=False),
        sa.Column('weight', sa.Integer(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('cost_per_1k_input_override', sa.Numeric(precision=10, scale=8), nullable=True),
        sa.Column('cost_per_1k_output_override', sa.Numeric(precision=10, scale=8), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('agent_type', 'provider', 'model_name', name='unique_agent_model')
    )
    op.create_index(op.f('ix_agent_model_configs_agent_type'), 'agent_model_configs', ['agent_type'], unique=False)
    op.create_index(op.f('ix_agent_model_configs_is_active'), 'agent_model_configs', ['is_active'], unique=False)

    # --- Create Agent Performance Stats ---
    op.create_table(
        'agent_performance_stats',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('agent_type', sa.String(length=50), nullable=False),
        sa.Column('time_window', sa.String(length=20), nullable=False),
        sa.Column('total_requests', sa.Integer(), nullable=True),
        sa.Column('successful_requests', sa.Integer(), nullable=True),
        sa.Column('failed_requests', sa.Integer(), nullable=True),
        sa.Column('canceled_requests', sa.Integer(), nullable=True),
        sa.Column('avg_latency_ms', sa.Integer(), nullable=True),
        sa.Column('avg_cost_usd', sa.Numeric(precision=10, scale=6), nullable=True),
        sa.Column('total_cost_usd', sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column('last_updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('agent_type', 'time_window', name='unique_agent_stats_window')
    )
    op.create_index(op.f('ix_agent_performance_stats_agent_type'), 'agent_performance_stats', ['agent_type'], unique=False)
    op.create_index(op.f('ix_agent_performance_stats_time_window'), 'agent_performance_stats', ['time_window'], unique=False)

    # --- Create DeepInfra API Metrics ---
    op.create_table(
        'deepinfra_api_metrics',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('model_id', sa.BigInteger(), nullable=True),
        sa.Column('requests_count', sa.Integer(), nullable=True),
        sa.Column('tokens_consumed', sa.BigInteger(), nullable=True),
        sa.Column('cost_usd', sa.Numeric(precision=10, scale=6), nullable=True),
        sa.Column('avg_latency_ms', sa.Integer(), nullable=True),
        sa.Column('p95_latency_ms', sa.Integer(), nullable=True),
        sa.Column('error_count', sa.Integer(), nullable=True),
        sa.Column('success_rate', sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column('time_window_start', sa.DateTime(timezone=True), nullable=False),
        sa.Column('time_window_end', sa.DateTime(timezone=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.ForeignKeyConstraint(['model_id'], ['models.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('model_id', 'time_window_start', name='unique_deepinfra_metric')
    )
    op.create_index(op.f('ix_deepinfra_api_metrics_model_id'), 'deepinfra_api_metrics', ['model_id'], unique=False)
    op.create_index(op.f('ix_deepinfra_api_metrics_time_window_start'), 'deepinfra_api_metrics', ['time_window_start'], unique=False)

    # --- Update LLMProvider Enum (if needed, usually handled by sync logic or recreation, here we assume it might need raw SQL if not handled) ---
    # Note: In Postgres, adding a value to an ENUM inside a transaction can be tricky if not committed.
    # We use a safe approach "ALTER TYPE ... ADD VALUE IF NOT EXISTS"
    op.execute("ALTER TYPE llmprovider ADD VALUE IF NOT EXISTS 'DEEPINFRA'")


def downgrade() -> None:
    op.drop_index(op.f('ix_deepinfra_api_metrics_time_window_start'), table_name='deepinfra_api_metrics')
    op.drop_index(op.f('ix_deepinfra_api_metrics_model_id'), table_name='deepinfra_api_metrics')
    op.drop_table('deepinfra_api_metrics')
    
    op.drop_index(op.f('ix_agent_performance_stats_time_window'), table_name='agent_performance_stats')
    op.drop_index(op.f('ix_agent_performance_stats_agent_type'), table_name='agent_performance_stats')
    op.drop_table('agent_performance_stats')
    
    op.drop_index(op.f('ix_agent_model_configs_is_active'), table_name='agent_model_configs')
    op.drop_index(op.f('ix_agent_model_configs_agent_type'), table_name='agent_model_configs')
    op.drop_table('agent_model_configs')
