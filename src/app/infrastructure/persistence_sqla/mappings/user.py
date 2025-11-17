"""
SQLAlchemy mapping for User table metadata.
"""

from sqlalchemy import Integer, String, DateTime, Boolean, Text, Enum, ForeignKey
from sqlalchemy.orm import mapped_column
import sqlalchemy as sa

from app.domain.enums.user_role import UserRole
from app.infrastructure.persistence_sqla.registry import mapping_registry


def map_users_table() -> None:
    """Map User entity to database table (idempotent)."""
    # Idempotency guard: don't remap if already present
    if "users" in mapping_registry.metadata.tables:
        return

    @mapping_registry.mapped
    class UsersTable:
        __tablename__ = "users"
        __table_args__ = {"extend_existing": True}
        
        # Primary key
        id = mapped_column(Integer, primary_key=True, index=True)
        
        # User information
        email = mapped_column(String(255), unique=True, index=True, nullable=False)
        first_name = mapped_column(String(100), nullable=False)
        last_name = mapped_column(String(100), nullable=False)
        role = mapped_column(Enum(UserRole, values_callable=lambda x: [e.value for e in x]), default=UserRole.USER)
        is_active = mapped_column(Boolean, default=True)
        is_blocked = mapped_column(Boolean, default=False)
        is_verified = mapped_column(Boolean, default=False)
        retry_count = mapped_column(Integer, default=0)
        password = mapped_column(String(255), nullable=False)
        
        # Timestamps
        created_at = mapped_column(DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'))
        updated_at = mapped_column(DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), onupdate=sa.text('CURRENT_TIMESTAMP'))
        last_login = mapped_column(DateTime, nullable=True)
        
        # Profile information 
        profile_picture = mapped_column(String(255), nullable=True)
        phone_number = mapped_column(String(20), nullable=True)
        language = mapped_column(String(10), default="en")
        address = mapped_column(Text, nullable=True)
        postal_code = mapped_column(String(20), nullable=True)
        
        # Foreign keys
        country_id = mapped_column(Integer, ForeignKey("countries.id"), nullable=True)
        city_id = mapped_column(Integer, ForeignKey("cities.id"), nullable=True)
        
        # Subscription
        subscription = mapped_column(String(50), nullable=True)
    
    # Note: We intentionally do not map the domain `User` entity here.
    # The purpose of this module during init_db is to define table metadata
    # via the mapped `UsersTable` so that `create_all` can create tables.
