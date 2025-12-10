"""Add analytics indexes for admin metrics.

Revision ID: i9j0k1l2m3n4
Revises: h8i9j0k1l2m3
Create Date: 2025-12-10 00:02:00.000000

This migration adds indexes optimized for analytics queries:
1. Composite index on wallets (user_id, created_at) for user wallet analytics
2. Composite index on wallets (provider, created_at) for provider distribution
3. Composite index on transactions (user_id, created_at) for user transaction history
4. Composite index on transactions (chain, created_at) for chain analytics
5. Composite index on transactions (status, created_at) for status tracking
6. Index on transactions (created_at) for time-series queries
"""

from typing import Sequence, Union

from alembic import op
from sqlalchemy import text


# revision identifiers, used by Alembic.
revision: str = "i9j0k1l2m3n4"
down_revision: Union[str, None] = "h8i9j0k1l2m3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def index_exists(connection, index_name: str) -> bool:
    """Check if an index exists in the database."""
    result = connection.execute(text(
        f"SELECT 1 FROM pg_indexes WHERE indexname = '{index_name}'"
    ))
    return result.fetchone() is not None


def upgrade() -> None:
    """Add analytics indexes."""
    connection = op.get_bind()
    
    # ============================================================
    # Wallet Analytics Indexes
    # ============================================================
    
    # Index for user wallet queries and user-level analytics
    if not index_exists(connection, "ix_wallets_user_id_created_at"):
        op.create_index(
            "ix_wallets_user_id_created_at",
            "wallets",
            ["user_id", "created_at"],
        )
    
    # Index for provider distribution queries
    if not index_exists(connection, "ix_wallets_provider_created_at"):
        op.create_index(
            "ix_wallets_provider_created_at",
            "wallets",
            ["provider", "created_at"],
        )
    
    # Index for status-based queries
    if not index_exists(connection, "ix_wallets_status"):
        op.create_index(
            "ix_wallets_status",
            "wallets",
            ["status"],
        )
    
    # ============================================================
    # Transaction Analytics Indexes
    # ============================================================
    
    # Index for user transaction history and analytics
    if not index_exists(connection, "ix_transactions_user_id_created_at"):
        op.create_index(
            "ix_transactions_user_id_created_at",
            "transactions",
            ["user_id", "created_at"],
        )
    
    # Index for chain-based analytics
    if not index_exists(connection, "ix_transactions_chain_created_at"):
        op.create_index(
            "ix_transactions_chain_created_at",
            "transactions",
            ["chain", "created_at"],
        )
    
    # Index for status tracking and analytics
    if not index_exists(connection, "ix_transactions_status_created_at"):
        op.create_index(
            "ix_transactions_status_created_at",
            "transactions",
            ["status", "created_at"],
        )
    
    # Index for transaction type analytics
    if not index_exists(connection, "ix_transactions_type_created_at"):
        op.create_index(
            "ix_transactions_type_created_at",
            "transactions",
            ["type", "created_at"],
        )
    
    # Index for time-series queries (daily counts, etc.)
    if not index_exists(connection, "ix_transactions_created_at"):
        op.create_index(
            "ix_transactions_created_at",
            "transactions",
            ["created_at"],
        )
    
    # Composite index for wallet-based transaction queries
    if not index_exists(connection, "ix_transactions_wallet_id_created_at"):
        op.create_index(
            "ix_transactions_wallet_id_created_at",
            "transactions",
            ["wallet_id", "created_at"],
        )


def downgrade() -> None:
    """Remove analytics indexes."""
    # Drop wallet indexes
    try:
        op.drop_index("ix_wallets_user_id_created_at", table_name="wallets")
    except Exception:
        pass
    
    try:
        op.drop_index("ix_wallets_provider_created_at", table_name="wallets")
    except Exception:
        pass
    
    try:
        op.drop_index("ix_wallets_status", table_name="wallets")
    except Exception:
        pass
    
    # Drop transaction indexes
    try:
        op.drop_index("ix_transactions_user_id_created_at", table_name="transactions")
    except Exception:
        pass
    
    try:
        op.drop_index("ix_transactions_chain_created_at", table_name="transactions")
    except Exception:
        pass
    
    try:
        op.drop_index("ix_transactions_status_created_at", table_name="transactions")
    except Exception:
        pass
    
    try:
        op.drop_index("ix_transactions_type_created_at", table_name="transactions")
    except Exception:
        pass
    
    try:
        op.drop_index("ix_transactions_created_at", table_name="transactions")
    except Exception:
        pass
    
    try:
        op.drop_index("ix_transactions_wallet_id_created_at", table_name="transactions")
    except Exception:
        pass
