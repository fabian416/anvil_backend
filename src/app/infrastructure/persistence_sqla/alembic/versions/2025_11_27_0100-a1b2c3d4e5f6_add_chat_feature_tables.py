"""Add chat feature tables

Revision ID: a1b2c3d4e5f6
Revises: f122cb03e498
Create Date: 2025-11-27 01:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, None] = "f122cb03e498"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    # Create Enums
    sa.Enum("user", "agent", "system", name="messagerole").create(op.get_bind())
    sa.Enum("trading", "yield_farming", "risk_analysis", "research", "portfolio", name="agenttype").create(op.get_bind())

    # Create Conversations Table
    op.create_table(
        "conversations",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name=op.f("fk_conversations_user_id_users")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_conversations")),
    )
    op.create_index(op.f("ix_conversations_user_id"), "conversations", ["user_id"], unique=False)

    # Create Messages Table
    op.create_table(
        "messages",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("conversation_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("role", sa.Enum("user", "agent", "system", name="messagerole"), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("agent_type", sa.Enum("trading", "yield_farming", "risk_analysis", "research", "portfolio", name="agenttype"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=True),
        sa.ForeignKeyConstraint(["conversation_id"], ["conversations.id"], name=op.f("fk_messages_conversation_id_conversations")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_messages")),
    )
    op.create_index(op.f("ix_messages_conversation_id"), "messages", ["conversation_id"], unique=False)

    # Create Agent Sessions Table
    op.create_table(
        "agent_sessions",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("conversation_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("agent_type", sa.Enum("trading", "yield_farming", "risk_analysis", "research", "portfolio", name="agenttype"), nullable=False),
        sa.Column("state", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=True),
        sa.ForeignKeyConstraint(["conversation_id"], ["conversations.id"], name=op.f("fk_agent_sessions_conversation_id_conversations")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_agent_sessions")),
    )
    op.create_index(op.f("ix_agent_sessions_conversation_id"), "agent_sessions", ["conversation_id"], unique=False)

def downgrade() -> None:
    op.drop_index(op.f("ix_agent_sessions_conversation_id"), table_name="agent_sessions")
    op.drop_table("agent_sessions")
    op.drop_index(op.f("ix_messages_conversation_id"), table_name="messages")
    op.drop_table("messages")
    op.drop_index(op.f("ix_conversations_user_id"), table_name="conversations")
    op.drop_table("conversations")
    sa.Enum(name="agenttype").drop(op.get_bind())
    sa.Enum(name="messagerole").drop(op.get_bind())
