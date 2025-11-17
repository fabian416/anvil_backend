"""
SQLAlchemy mapping for Subscription table metadata.
"""

from datetime import datetime
from sqlalchemy import Integer, String, DateTime, Boolean, Float, JSON
from sqlalchemy.orm import mapped_column

from app.infrastructure.persistence_sqla.registry import mapping_registry


def map_subscriptions_table() -> None:
    """Map Subscription entity to database table (idempotent)."""
    if "subscriptions" in mapping_registry.metadata.tables:
        return

    @mapping_registry.mapped
    class SubscriptionsTable:
        __tablename__ = "subscriptions"
        __table_args__ = {"extend_existing": True}

        # Primary key
        id = mapped_column(Integer, primary_key=True, index=True)

        # Subscription information
        name = mapped_column(String(100), nullable=False)
        price = mapped_column(Float, nullable=False)
        subscription_type = mapped_column(String(100), nullable=False, default="month")
        currency = mapped_column(String(3), default="USD")
        duration = mapped_column(Integer, nullable=False)  # Duration in days
        features = mapped_column(JSON, nullable=True)
        is_active = mapped_column(Boolean, default=True)
        stripe_price_id = mapped_column(String(255), nullable=True)
        stripe_product_id = mapped_column(String(255), nullable=True)

        # Timestamps
        created_at = mapped_column(DateTime, default=datetime.utcnow)
        updated_at = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Keep only table metadata for create_all
