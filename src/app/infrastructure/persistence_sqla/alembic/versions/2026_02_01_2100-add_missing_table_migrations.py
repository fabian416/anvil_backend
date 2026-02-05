"""Add missing table migrations for existing tables

This migration adds the CREATE TABLE statements for tables that exist
in the database but were missing from the migration history:
- moonpay_customer_tokens
- portfolio_snapshots
- token_holdings

These tables already exist in the database, so this migration uses
IF NOT EXISTS to make it idempotent.

Revision ID: missing_tables_001
Revises: 96b8d2c88832
Create Date: 2026-02-01 21:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

# revision identifiers, used by Alembic.
revision: str = "missing_tables_001"
down_revision: Union[str, None] = "96b8d2c88832"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create missing tables if they don't exist."""
    
    # Check if chaintype enum exists, create if not
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE chaintype AS ENUM ('arbitrum', 'base', 'hyperliquid', 'ethereum');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)
    
    # =========================================================================
    # TABLE 1: moonpay_customer_tokens
    # =========================================================================
    op.execute("""
        CREATE TABLE IF NOT EXISTS moonpay_customer_tokens (
            id UUID NOT NULL,
            user_id INTEGER NOT NULL,
            moonpay_token VARCHAR(2048) NOT NULL,
            moonpay_csrf_token VARCHAR(2048) NOT NULL,
            created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
            expires_at TIMESTAMP WITHOUT TIME ZONE,
            CONSTRAINT pk_moonpay_customer_tokens PRIMARY KEY (id),
            CONSTRAINT fk_moonpay_customer_tokens_user_id_users 
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        );
    """)
    
    # Create index if not exists
    op.execute("""
        CREATE UNIQUE INDEX IF NOT EXISTS ix_moonpay_customer_tokens_user_id 
        ON moonpay_customer_tokens (user_id);
    """)
    
    # =========================================================================
    # TABLE 2: portfolio_snapshots
    # =========================================================================
    op.execute("""
        CREATE TABLE IF NOT EXISTS portfolio_snapshots (
            id SERIAL NOT NULL,
            wallet_id INTEGER NOT NULL,
            chain chaintype NOT NULL,
            total_usd NUMERIC(20, 8) NOT NULL,
            native_balance NUMERIC(36, 18) NOT NULL,
            native_usd_value NUMERIC(20, 8),
            captured_at TIMESTAMP WITH TIME ZONE NOT NULL,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            CONSTRAINT pk_portfolio_snapshots PRIMARY KEY (id),
            CONSTRAINT fk_portfolio_snapshots_wallet_id_wallets 
                FOREIGN KEY (wallet_id) REFERENCES wallets(id) ON DELETE CASCADE
        );
    """)
    
    # Create indexes if not exist
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_portfolio_snapshots_captured_at 
        ON portfolio_snapshots (captured_at);
    """)
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_portfolio_snapshots_chain 
        ON portfolio_snapshots (chain);
    """)
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_portfolio_snapshots_wallet_captured 
        ON portfolio_snapshots (wallet_id, captured_at);
    """)
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_portfolio_snapshots_wallet_id 
        ON portfolio_snapshots (wallet_id);
    """)
    
    # =========================================================================
    # TABLE 3: token_holdings
    # =========================================================================
    op.execute("""
        CREATE TABLE IF NOT EXISTS token_holdings (
            id SERIAL NOT NULL,
            snapshot_id INTEGER NOT NULL,
            token_address VARCHAR(42),
            symbol VARCHAR(20) NOT NULL,
            name VARCHAR(100) NOT NULL,
            decimals INTEGER NOT NULL,
            amount NUMERIC(36, 18) NOT NULL,
            usd_value NUMERIC(20, 8),
            usd_price NUMERIC(20, 8),
            percentage NUMERIC(10, 6) NOT NULL,
            CONSTRAINT pk_token_holdings PRIMARY KEY (id),
            CONSTRAINT fk_token_holdings_snapshot_id_portfolio_snapshots 
                FOREIGN KEY (snapshot_id) REFERENCES portfolio_snapshots(id) ON DELETE CASCADE
        );
    """)
    
    # Create indexes if not exist
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_token_holdings_snapshot_id 
        ON token_holdings (snapshot_id);
    """)
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_token_holdings_snapshot_token 
        ON token_holdings (snapshot_id, token_address);
    """)
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_token_holdings_token_address 
        ON token_holdings (token_address);
    """)


def downgrade() -> None:
    """Drop the tables in reverse order."""
    op.drop_table("token_holdings")
    op.drop_table("portfolio_snapshots")
    op.drop_table("moonpay_customer_tokens")
    
    # Note: We don't drop the chaintype enum as it may be used by other tables
