"""
SQLAlchemy mapping for Agent Session table metadata.
"""

from sqlalchemy import DateTime, Enum, ForeignKey
from sqlalchemy.orm import mapped_column
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB
import uuid

from app.domain.enums.agent_type import AgentType
from app.infrastructure.persistence_sqla.registry import mapping_registry

def map_agent_session_table() -> None:
    """Map Agent Session entity to database table (idempotent)."""
    if "agent_sessions" in mapping_registry.metadata.tables:
        return

    @mapping_registry.mapped
    class AgentSessionsTable:
        __tablename__ = "agent_sessions"
        __table_args__ = {"extend_existing": True}
        
        # Primary key
        id = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
        
        # Relationships
        conversation_id = mapped_column(UUID(as_uuid=True), ForeignKey("conversations.id"), nullable=False, index=True)
        
        # Agent details
        agent_type = mapped_column(Enum(AgentType, values_callable=lambda x: [e.value for e in x], name="agenttype", create_type=False), nullable=False)
        
        # State
        state = mapped_column(JSONB, default={})
        
        # Timestamps
        created_at = mapped_column(DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'))
        updated_at = mapped_column(DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), onupdate=sa.text('CURRENT_TIMESTAMP'))
