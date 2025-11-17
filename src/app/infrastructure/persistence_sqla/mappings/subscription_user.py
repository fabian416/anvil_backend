"""
SQLAlchemy mapping for SubscriptionUser table metadata.
"""

from datetime import datetime
from sqlalchemy import Integer, String, DateTime, Boolean, ForeignKey, JSON
from sqlalchemy.orm import mapped_column

from app.infrastructure.persistence_sqla.registry import mapping_registry


def map_subscription_users_table() -> None:
    """Map SubscriptionUser entity to database table (idempotent)."""
    if "subscription_users" in mapping_registry.metadata.tables:
        return

    @mapping_registry.mapped
    class SubscriptionUsersTable:
        __tablename__ = "subscription_users"
        __table_args__ = {"extend_existing": True}

        # Primary key
        id = mapped_column(Integer, primary_key=True, index=True)

        # Foreign keys
        user_id = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
        subscription_id = mapped_column(Integer, ForeignKey("subscriptions.id"), nullable=False)

        # Subscription user information
        status = mapped_column(String(50), nullable=False, default="pending")  # pending, cancelled, active
        start_date = mapped_column(DateTime(timezone=True), nullable=True)
        end_date = mapped_column(DateTime(timezone=True), nullable=True)
        stripe_subscription_id = mapped_column(String(255), nullable=True)
        stripe_customer_id = mapped_column(String(255), nullable=True)
        client_secret = mapped_column(String(255), nullable=True)
        subscription_data = mapped_column(JSON, nullable=True)
        data_json = mapped_column(JSON, nullable=True, default=dict)

        # Timestamps
        created_at = mapped_column(DateTime(timezone=True), server_default="now()")
        updated_at = mapped_column(DateTime(timezone=True), onupdate="now()")

    # Keep only table metadata for create_all
