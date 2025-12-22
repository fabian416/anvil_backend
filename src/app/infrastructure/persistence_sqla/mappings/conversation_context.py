"""
SQLAlchemy mapping for ConversationContext entity.
"""

from sqlalchemy import Table, Column, String, Integer, Float, DateTime, JSON
from sqlalchemy.dialects.postgresql import UUID

from app.infrastructure.persistence_sqla.registry import mapping_registry


conversation_context_table = Table(
    "conversation_contexts",
    mapping_registry.metadata,
    Column("id", UUID(as_uuid=True), primary_key=True),
    Column("conversation_id", UUID(as_uuid=True), nullable=False, index=True),
    Column("user_id", UUID(as_uuid=True), nullable=False, index=True),
    
    # Context data
    Column("current_topic", String, nullable=True),
    Column("recent_intents", JSON, nullable=False, default=list),
    Column("mentioned_tokens", JSON, nullable=False, default=list),
    Column("mentioned_protocols", JSON, nullable=False, default=list),
    Column("active_positions", JSON, nullable=False, default=list),
    
    # User preferences
    Column("preferred_slippage", Float, nullable=True),
    Column("preferred_leverage", Integer, nullable=True),
    Column("risk_tolerance", String, nullable=True),
    Column("preferred_chains", JSON, nullable=False, default=list),
    
    # Historical patterns
    Column("frequent_operations", JSON, nullable=False, default=dict),
    Column("typical_trade_sizes", JSON, nullable=False, default=dict),
    Column("interaction_count", Integer, nullable=False, default=0),
    
    # Metadata
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("updated_at", DateTime(timezone=True), nullable=False),
)
