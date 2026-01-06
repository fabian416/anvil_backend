"""add chat unified v2 tables

Revision ID: chat_unified_v2
Revises: 49606e4c6652
Create Date: 2026-01-06 15:00:00.000000

This migration creates the unified chat system tables:
- chat_users: Unified user table for guest + authenticated users
- chat_conversations: Conversations with full CRUD support
- chat_messages: Messages with enhanced metadata
- chat_rate_limits: Rate limiting tracking
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "chat_unified_v2"
down_revision: Union[str, None] = "49606e4c6652"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create unified chat system tables."""
    
    # ========================================
    # chat_users table
    # ========================================
    op.create_table(
        'chat_users',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('user_type', sa.String(20), nullable=False),
        sa.Column('identifier', sa.String(255), nullable=False),
        sa.Column('privy_id', sa.String(255), nullable=True),
        sa.Column('email', sa.String(255), nullable=True),
        sa.Column('preferred_language', sa.String(5), server_default='en'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('last_active_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('is_blocked', sa.Boolean, server_default='false'),
        sa.Column('metadata', postgresql.JSONB, server_default='{}'),
    )
    
    # Indexes for chat_users
    op.create_index(
        'idx_chat_users_identifier',
        'chat_users',
        ['user_type', 'identifier'],
        unique=True,
    )
    op.create_index(
        'idx_chat_users_privy_id',
        'chat_users',
        ['privy_id'],
        unique=True,
        postgresql_where=sa.text('privy_id IS NOT NULL'),
    )
    op.create_index(
        'idx_chat_users_user_type',
        'chat_users',
        ['user_type'],
    )
    
    # ========================================
    # chat_conversations table
    # ========================================
    op.create_table(
        'chat_conversations',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column(
            'user_id',
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey('chat_users.id', ondelete='CASCADE'),
            nullable=False,
        ),
        sa.Column('title', sa.String(255), nullable=True),
        sa.Column('status', sa.String(20), server_default='active'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('last_message_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('message_count', sa.Integer, server_default='0'),
        sa.Column('language', sa.String(5), server_default='en'),
        sa.Column('metadata', postgresql.JSONB, server_default='{}'),
    )
    
    # Indexes for chat_conversations
    op.create_index(
        'idx_chat_conversations_user_id',
        'chat_conversations',
        ['user_id'],
    )
    op.create_index(
        'idx_chat_conversations_user_status',
        'chat_conversations',
        ['user_id', 'status'],
    )
    op.create_index(
        'idx_chat_conversations_status',
        'chat_conversations',
        ['status'],
    )
    
    # ========================================
    # chat_messages table
    # ========================================
    op.create_table(
        'chat_messages',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column(
            'conversation_id',
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey('chat_conversations.id', ondelete='CASCADE'),
            nullable=False,
        ),
        sa.Column('role', sa.String(20), nullable=False),
        sa.Column('content', sa.Text, nullable=False),
        sa.Column('intent', sa.String(50), nullable=True),
        sa.Column('intent_confidence', sa.Float, nullable=True),
        sa.Column('handler', sa.String(100), nullable=True),
        sa.Column('is_restricted_action', sa.Boolean, server_default='false'),
        sa.Column('language', sa.String(5), server_default='en'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('metadata', postgresql.JSONB, server_default='{}'),
    )
    
    # Indexes for chat_messages
    op.create_index(
        'idx_chat_messages_conversation_id',
        'chat_messages',
        ['conversation_id'],
    )
    op.create_index(
        'idx_chat_messages_conversation_created',
        'chat_messages',
        ['conversation_id', 'created_at'],
    )
    
    # ========================================
    # chat_rate_limits table
    # ========================================
    op.create_table(
        'chat_rate_limits',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column(
            'user_id',
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey('chat_users.id', ondelete='CASCADE'),
            nullable=False,
        ),
        sa.Column('window_type', sa.String(20), nullable=False),
        sa.Column('window_start', sa.DateTime(timezone=True), nullable=False),
        sa.Column('message_count', sa.Integer, server_default='0'),
        sa.UniqueConstraint(
            'user_id', 'window_type', 'window_start',
            name='uq_rate_limits_user_window',
        ),
    )
    
    # Indexes for chat_rate_limits
    op.create_index(
        'idx_chat_rate_limits_user_id',
        'chat_rate_limits',
        ['user_id'],
    )


def downgrade() -> None:
    """Drop unified chat system tables."""
    # Drop in reverse order due to foreign key constraints
    op.drop_table('chat_rate_limits')
    op.drop_table('chat_messages')
    op.drop_table('chat_conversations')
    op.drop_table('chat_users')

