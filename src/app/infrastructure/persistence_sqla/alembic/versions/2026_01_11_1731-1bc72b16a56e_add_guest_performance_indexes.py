"""add_guest_performance_indexes

Revision ID: 1bc72b16a56e
Revises: 9331ebd70cc7
Create Date: 2026-01-11 17:31:48.294984

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "1bc72b16a56e"
down_revision: Union[str, None] = "9331ebd70cc7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add performance indexes for guest system queries."""
    # Guest users indexes
    # For rate limiting queries by last_seen_at
    op.create_index(
        "idx_guest_users_last_seen_at",
        "guest_users",
        ["last_seen_at"],
    )
    # For filtering blocked users
    op.create_index(
        "idx_guest_users_is_blocked",
        "guest_users",
        ["is_blocked"],
    )

    # Guest conversations indexes
    # For sorting conversations by creation time
    op.create_index(
        "idx_guest_conversations_created_at",
        "guest_conversations",
        ["created_at"],
    )
    # Composite index for active conversation queries with ordering
    op.create_index(
        "idx_guest_conversations_user_status_created",
        "guest_conversations",
        ["guest_user_id", "status", "created_at"],
    )

    # Guest messages indexes
    # For sorting messages chronologically
    op.create_index(
        "idx_guest_messages_created_at",
        "guest_messages",
        ["created_at"],
    )
    # For intent-based analytics queries
    op.create_index(
        "idx_guest_messages_intent",
        "guest_messages",
        ["intent"],
    )
    # For retrieving conversation messages in chronological order
    op.create_index(
        "idx_guest_messages_conversation_created",
        "guest_messages",
        ["conversation_id", "created_at"],
    )


def downgrade() -> None:
    """Remove performance indexes."""
    # Guest messages indexes
    op.drop_index("idx_guest_messages_conversation_created", "guest_messages")
    op.drop_index("idx_guest_messages_intent", "guest_messages")
    op.drop_index("idx_guest_messages_created_at", "guest_messages")

    # Guest conversations indexes
    op.drop_index("idx_guest_conversations_user_status_created", "guest_conversations")
    op.drop_index("idx_guest_conversations_created_at", "guest_conversations")

    # Guest users indexes
    op.drop_index("idx_guest_users_is_blocked", "guest_users")
    op.drop_index("idx_guest_users_last_seen_at", "guest_users")
