"""
SQLAlchemy mapping for Conversation table metadata.
"""

from sqlalchemy import Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import mapped_column
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID
import uuid

from app.infrastructure.persistence_sqla.registry import mapping_registry

def map_conversation_table() -> None:
    """Map Conversation entity to database table (idempotent)."""
    if "conversations" in mapping_registry.metadata.tables:
        return

    @mapping_registry.mapped
    class ConversationsTable:
        __tablename__ = "conversations"
        __table_args__ = {"extend_existing": True}
        
        # Primary key
        id = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
        
        # User relationship
        user_id = mapped_column(Integer, ForeignKey("users.id"), nullable=False, index=True)
        
        # Metadata
        title = mapped_column(String(255), nullable=True)
        
        # Timestamps
        created_at = mapped_column(DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'))
        updated_at = mapped_column(DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), onupdate=sa.text('CURRENT_TIMESTAMP'))
