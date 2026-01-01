"""Add guest chat tables for demo/unauthenticated users.

Tables:
- guest_users: Track guest users by IP address
- guest_conversations: Guest chat conversations
- guest_messages: Messages in guest conversations
- guest_telemetry: Analytics for guest interactions

Revision ID: guest_chat_20251229
Revises: ip_tracking_20251229
Create Date: 2025-12-29

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = 'guest_chat_20251229'
down_revision = 'ip_tracking_20251229'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create guest chat tables."""
    
    # ========================================
    # Table: guest_users
    # ========================================
    op.create_table(
        'guest_users',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text('gen_random_uuid()')),
        sa.Column('ip_address', sa.String(45), nullable=False),
        sa.Column('fingerprint', sa.String(255), nullable=True),
        sa.Column('first_seen_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('last_seen_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('total_messages', sa.Integer, server_default='0'),
        sa.Column('language', sa.String(5), server_default="'en'"),
        sa.Column('country_code', sa.String(2), nullable=True),
        sa.Column('is_blocked', sa.Boolean, server_default='false'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_guest_users_ip_address', 'guest_users', ['ip_address'], unique=True)
    op.create_index('ix_guest_users_last_seen_at', 'guest_users', ['last_seen_at'])
    
    # ========================================
    # Table: guest_conversations
    # ========================================
    op.create_table(
        'guest_conversations',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text('gen_random_uuid()')),
        sa.Column('guest_user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('title', sa.String(255), nullable=True),
        sa.Column('status', sa.String(20), server_default="'active'"),
        sa.Column('message_count', sa.Integer, server_default='0'),
        sa.Column('language', sa.String(5), server_default="'en'"),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('archived_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['guest_user_id'], ['guest_users.id'], ondelete='CASCADE'),
    )
    op.create_index('ix_guest_conversations_guest_user_id', 'guest_conversations', ['guest_user_id'])
    op.create_index('ix_guest_conversations_status', 'guest_conversations', ['status'])
    op.create_index('ix_guest_conversations_created_at', 'guest_conversations', ['created_at'])
    
    # ========================================
    # Table: guest_messages
    # ========================================
    op.create_table(
        'guest_messages',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text('gen_random_uuid()')),
        sa.Column('conversation_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('role', sa.String(20), nullable=False),
        sa.Column('content', sa.Text, nullable=False),
        sa.Column('intent', sa.String(50), nullable=True),
        sa.Column('handler', sa.String(50), nullable=True),
        sa.Column('confidence', sa.Float, nullable=True),
        sa.Column('language', sa.String(5), server_default="'en'"),
        sa.Column('is_restricted_action', sa.Boolean, server_default='false'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['conversation_id'], ['guest_conversations.id'], ondelete='CASCADE'),
    )
    op.create_index('ix_guest_messages_conversation_id', 'guest_messages', ['conversation_id'])
    op.create_index('ix_guest_messages_created_at', 'guest_messages', ['created_at'])
    
    # ========================================
    # Table: guest_telemetry
    # ========================================
    op.create_table(
        'guest_telemetry',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text('gen_random_uuid()')),
        sa.Column('guest_user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('conversation_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('event_type', sa.String(50), nullable=False),
        sa.Column('event_data', postgresql.JSONB, nullable=True),
        sa.Column('ip_address', sa.String(45), nullable=False),
        sa.Column('user_agent', sa.Text, nullable=True),
        sa.Column('referer', sa.Text, nullable=True),
        sa.Column('language', sa.String(5), server_default="'en'"),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['guest_user_id'], ['guest_users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['conversation_id'], ['guest_conversations.id'], ondelete='SET NULL'),
    )
    op.create_index('ix_guest_telemetry_guest_user_id', 'guest_telemetry', ['guest_user_id'])
    op.create_index('ix_guest_telemetry_event_type', 'guest_telemetry', ['event_type'])
    op.create_index('ix_guest_telemetry_created_at', 'guest_telemetry', ['created_at'])


def downgrade() -> None:
    """Drop guest chat tables."""
    op.drop_table('guest_telemetry')
    op.drop_table('guest_messages')
    op.drop_table('guest_conversations')
    op.drop_table('guest_users')
