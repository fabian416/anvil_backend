"""
SQLAlchemy mapping for Message table metadata.
"""

from sqlalchemy import String, DateTime, Enum, ForeignKey, Text
from sqlalchemy.orm import mapped_column
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID
import uuid

from app.domain.enums.message_role import MessageRole
from app.domain.enums.agent_type import AgentType
from app.infrastructure.persistence_sqla.registry import mapping_registry

def map_message_table() -> None:
    """Map Message entity to database table (idempotent)."""
    if "messages" in mapping_registry.metadata.tables:
        return

    @mapping_registry.mapped
    class MessagesTable:
        __tablename__ = "messages"
        __table_args__ = {"extend_existing": True}
        
        # Primary key
        id = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
        
        # Conversation relationship
        conversation_id = mapped_column(UUID(as_uuid=True), ForeignKey("conversations.id"), nullable=False, index=True)
        
        # Message details
        role = mapped_column(Enum(MessageRole, values_callable=lambda x: [e.value for e in x]), nullable=False)
        content = mapped_column(Text, nullable=False)
        agent_type = mapped_column(Enum(AgentType, values_callable=lambda x: [e.value for e in x]), nullable=True)
        
        # Timestamps
        created_at = mapped_column(DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'))
