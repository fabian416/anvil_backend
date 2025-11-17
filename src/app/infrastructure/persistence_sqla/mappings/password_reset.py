from sqlalchemy import Integer, String, DateTime, Boolean, ForeignKey, text
from sqlalchemy.orm import mapped_column

from app.infrastructure.persistence_sqla.registry import mapping_registry


def map_password_resets_table() -> None:
    """Map PasswordReset entity to database table."""
    # Idempotency guard
    if "password_resets" in mapping_registry.metadata.tables:
        return

    @mapping_registry.mapped
    class PasswordResetsTable:
        __tablename__ = "password_resets"
        
        # Primary key
        id = mapped_column(Integer, primary_key=True, index=True)
        
        # Foreign key to users table
        user_id = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
        
        # Reset information
        token = mapped_column(String(255), nullable=False)
        expires_at = mapped_column(DateTime(timezone=True), nullable=False)
        is_used = mapped_column(Boolean, default=False)
        
        # Timestamps
        created_at = mapped_column(
            DateTime(timezone=True), 
            server_default=text('CURRENT_TIMESTAMP')
        )
        updated_at = mapped_column(
            DateTime(timezone=True), 
            server_default=text('CURRENT_TIMESTAMP'), 
            onupdate=text('CURRENT_TIMESTAMP')
        )
    
    # Keep only table metadata for create_all
