"""
SQLAlchemy mapping for Conversation entity.
"""

from sqlalchemy import Table, Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
import sqlalchemy as sa

from app.domain.entities.conversation import Conversation
from app.infrastructure.persistence_sqla.registry import mapping_registry

conversations_table = Table(
    "conversations",
    mapping_registry.metadata,
    Column("id", UUID(as_uuid=True), primary_key=True),
    Column("user_id", Integer, ForeignKey("users.id"), nullable=False, index=True),
    Column("title", String(255), nullable=True),
    Column("project_id", UUID(as_uuid=True), nullable=True),
    Column("created_at", DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),
    Column("updated_at", DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), onupdate=sa.text('CURRENT_TIMESTAMP')),
)

def map_conversation_table() -> None:
    """Map Conversation entity to database table."""
    mapping_registry.map_imperatively(
        Conversation,
        conversations_table,
        properties={
            "id": conversations_table.c.id,
            "user_id": conversations_table.c.user_id,
            "title": conversations_table.c.title,
            "project_id": conversations_table.c.project_id,
            "created_at": conversations_table.c.created_at,
            "updated_at": conversations_table.c.updated_at,
        },
    )
