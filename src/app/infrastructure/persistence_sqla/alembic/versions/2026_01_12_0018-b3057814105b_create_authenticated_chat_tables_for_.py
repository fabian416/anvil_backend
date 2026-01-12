"""create authenticated chat tables for unified chat system

Revision ID: b3057814105b
Revises: 1bc72b16a56e
Create Date: 2026-01-12 00:18:14.995900

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "b3057814105b"
down_revision: Union[str, None] = "1bc72b16a56e"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create authenticated chat tables for unified chat system.

    Creates three tables for authenticated user chat:
    - chat_users: Bridge between legacy users table and new chat system
    - chat_conversations: Authenticated user conversations
    - chat_messages: Messages in authenticated conversations

    These tables mirror the guest_* tables but with UUID-based user identification
    and permanent data retention.

    Note: This migration drops any existing chat_* tables from previous unified
    chat implementations to ensure a clean slate for the new architecture.
    """

    # Import JSONB for metadata column
    from sqlalchemy.dialects import postgresql

    # Drop old chat_* tables if they exist (from previous unified chat implementation)
    # This ensures a clean slate for the new guest_*/chat_* separation architecture
    op.execute("DROP TABLE IF EXISTS chat_rate_limits CASCADE")
    op.execute("DROP TABLE IF EXISTS chat_messages CASCADE")
    op.execute("DROP TABLE IF EXISTS chat_conversations CASCADE")
    op.execute("DROP TABLE IF EXISTS chat_users CASCADE")

    # ========================================
    # Table: chat_users
    # ========================================
    # Bridge table between legacy users (INTEGER id) and new chat system (UUID)
    op.create_table(
        "chat_users",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "user_id",
            sa.Integer,
            nullable=False,
            comment="Foreign key to legacy users table (INTEGER id)",
        ),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column(
            "subscription_tier",
            sa.String(20),
            server_default="'free'",
            comment="Subscription tier: free, premium, enterprise",
        ),
        sa.Column("total_messages", sa.Integer, server_default="0"),
        sa.Column(
            "language", sa.String(5), server_default="'en'", comment="Preferred language"
        ),
        sa.Column(
            "chat_preferences",
            postgresql.JSONB,
            nullable=True,
            server_default="{}",
            comment="User chat preferences (JSON)",
        ),
        sa.Column(
            "first_seen_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.Column(
            "last_seen_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            ondelete="CASCADE",
            name="fk_chat_users_user_id",
        ),
    )
    op.create_index(
        "ix_chat_users_user_id", "chat_users", ["user_id"], unique=True
    )
    op.create_index("ix_chat_users_email", "chat_users", ["email"])
    op.create_index(
        "ix_chat_users_subscription_tier", "chat_users", ["subscription_tier"]
    )
    op.create_index("ix_chat_users_last_seen_at", "chat_users", ["last_seen_at"])

    # ========================================
    # Table: chat_conversations
    # ========================================
    op.create_table(
        "chat_conversations",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "chat_user_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
            comment="Foreign key to chat_users table",
        ),
        sa.Column("title", sa.String(255), nullable=True),
        sa.Column(
            "status",
            sa.String(20),
            server_default="'active'",
            comment="Conversation status: active, archived",
        ),
        sa.Column("message_count", sa.Integer, server_default="0"),
        sa.Column(
            "language", sa.String(5), server_default="'en'", comment="Conversation language"
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.Column(
            "archived_at",
            sa.DateTime(timezone=True),
            nullable=True,
            comment="When conversation was archived",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(
            ["chat_user_id"],
            ["chat_users.id"],
            ondelete="CASCADE",
            name="fk_chat_conversations_chat_user_id",
        ),
    )
    op.create_index(
        "ix_chat_conversations_chat_user_id", "chat_conversations", ["chat_user_id"]
    )
    op.create_index("ix_chat_conversations_status", "chat_conversations", ["status"])
    op.create_index(
        "ix_chat_conversations_created_at", "chat_conversations", ["created_at"]
    )
    # Composite index for get_active_conversation query (most critical)
    op.create_index(
        "ix_chat_conversations_user_status_created",
        "chat_conversations",
        ["chat_user_id", "status", "created_at"],
        unique=False,
    )

    # ========================================
    # Table: chat_messages
    # ========================================
    op.create_table(
        "chat_messages",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "conversation_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
            comment="Foreign key to chat_conversations table",
        ),
        sa.Column(
            "role",
            sa.String(20),
            nullable=False,
            comment="Message role: user, assistant",
        ),
        sa.Column("content", sa.Text, nullable=False, comment="Message content"),
        sa.Column(
            "intent",
            sa.String(50),
            nullable=True,
            comment="Detected Hunter AI intent",
        ),
        sa.Column(
            "handler", sa.String(50), nullable=True, comment="Handler that processed message"
        ),
        sa.Column(
            "confidence",
            sa.Float,
            nullable=True,
            comment="Intent classification confidence",
        ),
        sa.Column(
            "language", sa.String(5), server_default="'en'", comment="Message language"
        ),
        sa.Column(
            "is_restricted_action",
            sa.Boolean,
            server_default="false",
            comment="Whether message triggered restricted action",
        ),
        sa.Column(
            "metadata",
            postgresql.JSONB,
            nullable=True,
            server_default="{}",
            comment="Hunter AI enrichment data (JSON)",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(
            ["conversation_id"],
            ["chat_conversations.id"],
            ondelete="CASCADE",
            name="fk_chat_messages_conversation_id",
        ),
    )
    op.create_index(
        "ix_chat_messages_conversation_id", "chat_messages", ["conversation_id"]
    )
    op.create_index("ix_chat_messages_created_at", "chat_messages", ["created_at"])
    op.create_index("ix_chat_messages_intent", "chat_messages", ["intent"])
    # Composite index for retrieving conversation messages in order
    op.create_index(
        "ix_chat_messages_conversation_created",
        "chat_messages",
        ["conversation_id", "created_at"],
        unique=False,
    )


def downgrade() -> None:
    """Drop authenticated chat tables."""
    op.drop_table("chat_messages")
    op.drop_table("chat_conversations")
    op.drop_table("chat_users")
