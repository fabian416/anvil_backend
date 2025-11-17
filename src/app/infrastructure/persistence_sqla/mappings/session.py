"""
SQLAlchemy mapping for Session table metadata.
"""

from datetime import datetime
from sqlalchemy import Integer, String, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import mapped_column

from app.infrastructure.persistence_sqla.registry import mapping_registry


def map_sessions_table() -> None:
    """Map Session entity to database table (idempotent)."""
    if "sessions" in mapping_registry.metadata.tables:
        return

    @mapping_registry.mapped
    class SessionsTable:
        __tablename__ = "sessions"
        __table_args__ = {"extend_existing": True}
        
        # Primary key
        id = mapped_column(Integer, primary_key=True, index=True)
        
        # Foreign key to users table
        user_id = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
        
        # Session information
        access_token = mapped_column(String(500), nullable=False)
        refresh_token = mapped_column(String(500), nullable=False)
        token_type = mapped_column(String(50), default="bearer")
        ip_address = mapped_column(String(50), nullable=True)
        user_agent = mapped_column(String(500), nullable=True)
        
        # Timestamps
        created_at = mapped_column(DateTime, default=datetime.utcnow)
        expires_at = mapped_column(DateTime, nullable=False)
        last_activity = mapped_column(DateTime, default=datetime.utcnow)
        is_active = mapped_column(Boolean, default=True)
    
    # See comment in user mapping: keep only table metadata for create_all
