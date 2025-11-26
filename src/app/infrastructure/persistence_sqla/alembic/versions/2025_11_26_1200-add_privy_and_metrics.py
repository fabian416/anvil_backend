"""Add Privy fields and user_events table

Revision ID: add_privy_and_metrics
Revises: f122cb03e498
Create Date: 2025-11-26 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'add_privy_and_metrics'
down_revision: Union[str, None] = 'f122cb03e498'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add Privy fields to users table
    op.add_column('users', sa.Column('privy_user_id', sa.String(255), nullable=True))
    op.add_column('users', sa.Column('primary_wallet_address', sa.String(255), nullable=True))
    op.add_column('users', sa.Column('auth_provider', sa.String(50), nullable=True, server_default='email'))
    
    # Create indexes for new columns
    op.create_index('ix_users_privy_user_id', 'users', ['privy_user_id'], unique=True)
    op.create_index('ix_users_primary_wallet_address', 'users', ['primary_wallet_address'], unique=False)
    
    # Make password nullable (for Privy-only users)
    op.alter_column('users', 'password',
                    existing_type=sa.String(255),
                    nullable=True)
    
    # Create user_events table
    op.create_table(
        'user_events',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('event_type', sa.String(100), nullable=False),
        sa.Column('event_category', sa.String(50), nullable=True),
        sa.Column('properties', postgresql.JSONB(astext_type=sa.Text()), nullable=True, server_default='{}'),
        sa.Column('device_type', sa.String(50), nullable=True),
        sa.Column('platform', sa.String(50), nullable=True),
        sa.Column('app_version', sa.String(20), nullable=True),
        sa.Column('session_id', sa.String(255), nullable=True),
        sa.Column('ip_address', sa.String(50), nullable=True),
        sa.Column('country_code', sa.String(10), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
    )
    
    # Create indexes for user_events
    op.create_index('ix_user_events_user_id', 'user_events', ['user_id'])
    op.create_index('ix_user_events_event_type', 'user_events', ['event_type'])
    op.create_index('ix_user_events_event_category', 'user_events', ['event_category'])
    op.create_index('ix_user_events_session_id', 'user_events', ['session_id'])
    op.create_index('ix_user_events_created_at', 'user_events', ['created_at'])
    op.create_index('ix_user_events_user_event_type', 'user_events', ['user_id', 'event_type'])


def downgrade() -> None:
    # Drop user_events table
    op.drop_index('ix_user_events_user_event_type', table_name='user_events')
    op.drop_index('ix_user_events_created_at', table_name='user_events')
    op.drop_index('ix_user_events_session_id', table_name='user_events')
    op.drop_index('ix_user_events_event_category', table_name='user_events')
    op.drop_index('ix_user_events_event_type', table_name='user_events')
    op.drop_index('ix_user_events_user_id', table_name='user_events')
    op.drop_table('user_events')
    
    # Make password non-nullable again
    op.alter_column('users', 'password',
                    existing_type=sa.String(255),
                    nullable=False)
    
    # Drop Privy indexes and columns
    op.drop_index('ix_users_primary_wallet_address', table_name='users')
    op.drop_index('ix_users_privy_user_id', table_name='users')
    op.drop_column('users', 'auth_provider')
    op.drop_column('users', 'primary_wallet_address')
    op.drop_column('users', 'privy_user_id')

