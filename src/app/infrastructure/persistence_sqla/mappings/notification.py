"""
SQLAlchemy mapping for Notification table metadata.
"""

from datetime import datetime
from sqlalchemy import Integer, String, Boolean, DateTime, ForeignKey, JSON
from sqlalchemy.orm import mapped_column

from app.infrastructure.persistence_sqla.registry import mapping_registry


def map_notifications_table() -> None:
    """Map Notification entity to database table."""
    
    @mapping_registry.mapped
    class NotificationsTable:
        __tablename__ = "notifications"
        
        # Primary key
        id = mapped_column(Integer, primary_key=True, index=True)
        
        # Foreign key to users table
        user_id = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
        
        # Notification information
        title = mapped_column(String(255), nullable=False)
        is_read = mapped_column(Boolean, default=False)
        action = mapped_column(String(50), nullable=False)  # e.g., 'payment', 'subscription', 'system'
        data_json = mapped_column(JSON, nullable=True)
        
        # Timestamps
        created_at = mapped_column(DateTime, default=datetime.utcnow)
        updated_at = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Keep only table metadata for create_all
