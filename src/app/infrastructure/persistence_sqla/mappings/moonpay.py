"""
MoonPay Customer Tokens SQLAlchemy Mapping.

Stores MoonPay authentication tokens for users who have completed KYC.
These tokens are used to execute swaps via the MoonPay API.
"""

from datetime import datetime
from uuid import uuid4

from sqlalchemy import DateTime, ForeignKey, String, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.persistence_sqla.registry import mapping_registry


def map_moonpay_customer_tokens_table() -> None:
    """Map the moonpay_customer_tokens table for storing MoonPay auth tokens."""
    if "moonpay_customer_tokens" in mapping_registry.metadata.tables:
        return

    @mapping_registry.mapped
    class MoonPayCustomerTokensTable:
        """
        SQLAlchemy mapping for moonpay_customer_tokens table.

        Stores MoonPay authentication tokens received after user completes
        KYC via the swapsCustomerSetup widget flow.

        Attributes:
            id: Primary key UUID
            user_id: Foreign key to users table (unique - one token per user)
            moonpay_token: The Bearer token for MoonPay API calls
            moonpay_csrf_token: CSRF token received from MoonPay
            created_at: When the tokens were first stored
            updated_at: When the tokens were last updated
            expires_at: Optional expiration time for the tokens
        """

        __tablename__ = "moonpay_customer_tokens"
        __table_args__ = {"extend_existing": True}

        id: Mapped[uuid4] = mapped_column(
            UUID(as_uuid=True),
            primary_key=True,
            default=uuid4,
        )
        user_id: Mapped[uuid4] = mapped_column(
            UUID(as_uuid=True),
            ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
            unique=True,
            index=True,
        )
        moonpay_token: Mapped[str] = mapped_column(
            String(2048),
            nullable=False,
        )
        moonpay_csrf_token: Mapped[str] = mapped_column(
            String(2048),
            nullable=False,
        )
        created_at: Mapped[datetime] = mapped_column(
            DateTime,
            server_default=text("CURRENT_TIMESTAMP"),
            nullable=False,
        )
        updated_at: Mapped[datetime] = mapped_column(
            DateTime,
            server_default=text("CURRENT_TIMESTAMP"),
            nullable=False,
        )
        expires_at: Mapped[datetime | None] = mapped_column(
            DateTime,
            nullable=True,
        )
