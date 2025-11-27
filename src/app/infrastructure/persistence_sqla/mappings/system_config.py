"""
SQLAlchemy mapping for System Config tables metadata.
"""

from sqlalchemy import Integer, String, DateTime, Enum, ForeignKey, Text, Boolean
from sqlalchemy.orm import mapped_column
from sqlalchemy.dialects.postgresql import JSON
import sqlalchemy as sa

from app.domain.enums.system.setting_scope import SettingScope
from app.infrastructure.persistence_sqla.registry import mapping_registry

def map_system_config_tables() -> None:
    """Map System Config entities to database tables (idempotent)."""
    
    # --- Settings ---
    if "settings" not in mapping_registry.metadata.tables:
        @mapping_registry.mapped
        class SettingsTable:
            __tablename__ = "settings"
            __table_args__ = {"extend_existing": True}
            
            id = mapped_column(Integer, primary_key=True, autoincrement=True)
            key = mapped_column(String(100), unique=True, nullable=False, index=True)
            value = mapped_column(Text, nullable=True)
            scope = mapped_column(Integer, default=0, nullable=False, index=True) # Mapped to Enum value
            is_sensitive = mapped_column(Boolean, default=False, index=True)
            description = mapped_column(Text, nullable=True)
            
            updated_at = mapped_column(DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), onupdate=sa.text('CURRENT_TIMESTAMP'))
            updated_by = mapped_column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    # --- Audit Logs ---
    if "audit_logs" not in mapping_registry.metadata.tables:
        @mapping_registry.mapped
        class AuditLogsTable:
            __tablename__ = "audit_logs"
            __table_args__ = {"extend_existing": True}
            
            id = mapped_column(Integer, primary_key=True, autoincrement=True)
            actor_user_id = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
            
            action = mapped_column(String(100), nullable=False, index=True)
            entity = mapped_column(String(100), nullable=False, index=True)
            entity_id = mapped_column(String(100), nullable=True)
            payload_json = mapped_column(JSON, nullable=True)
            
            ip_address = mapped_column(String(45), nullable=True)
            user_agent = mapped_column(Text, nullable=True)
            
            created_at = mapped_column(DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), index=True)
