"""
SQLAlchemy mapping for Payment table metadata.
"""

from datetime import datetime
from sqlalchemy import Integer, String, Float, DateTime, ForeignKey, JSON, Boolean
from sqlalchemy.orm import mapped_column

from app.infrastructure.persistence_sqla.registry import mapping_registry


def map_payments_table() -> None:
    """Map Payment entity to database table (idempotent)."""
    if "payments" in mapping_registry.metadata.tables:
        return

    @mapping_registry.mapped
    class PaymentsTable:
        __tablename__ = "payments"
        __table_args__ = {"extend_existing": True}

        # Primary key
        id = mapped_column(Integer, primary_key=True, index=True)

        # Foreign keys
        user_id = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
        subscription_id = mapped_column(Integer, ForeignKey("subscriptions.id", ondelete="SET NULL"), nullable=True)
        subscription_user_id = mapped_column(Integer, ForeignKey("subscription_users.id", ondelete="SET NULL"), nullable=True)

        # Payment information
        amount = mapped_column(Float, nullable=True)
        currency = mapped_column(String(3), default="USD")
        status = mapped_column(String(50), nullable=False, default="pending")
        stripe_payment_intent_id = mapped_column(String(255), nullable=True)
        stripe_customer_id = mapped_column(String(255), nullable=True)
        payment_data = mapped_column(JSON, nullable=True)
        payment_method = mapped_column(String(50), nullable=True)
        payment_type = mapped_column(String(50), nullable=True)
        date = mapped_column(DateTime, nullable=True, default=datetime.utcnow)
        data_json = mapped_column(JSON, nullable=True)

        # Timestamps
        created_at = mapped_column(DateTime, default=datetime.utcnow)
        updated_at = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Keep only table metadata for create_all
