"""
Create lending tables for Aave and Morpho positions

Revision ID: lending_core_001
Revises: 1372dec32558
Create Date: 2026-01-27

Creates core lending tables:
- lending_positions: Main lending positions across protocols
- lending_supplies: Individual supply positions per asset
- lending_borrows: Individual borrow positions per asset (Aave only)
- lending_transactions: Transaction history with status tracking
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB

# revision identifiers, used by Alembic
revision = "lending_core_001"
down_revision = "1372dec32558"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create lending tables."""

    # =========================================================================
    # CREATE POSTGRESQL ENUMS (with idempotent DO $$ block)
    # =========================================================================

    # Use DO $$ blocks for idempotent enum creation
    op.execute("""
        DO $$ BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'protocol_enum') THEN
                CREATE TYPE protocol_enum AS ENUM ('aave', 'morpho');
            END IF;
        END $$;
    """)

    op.execute("""
        DO $$ BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'position_type_enum') THEN
                CREATE TYPE position_type_enum AS ENUM ('supply', 'borrow');
            END IF;
        END $$;
    """)

    op.execute("""
        DO $$ BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'lending_status_enum') THEN
                CREATE TYPE lending_status_enum AS ENUM ('active', 'closed', 'liquidated');
            END IF;
        END $$;
    """)

    op.execute("""
        DO $$ BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'lending_action_enum') THEN
                CREATE TYPE lending_action_enum AS ENUM ('supply', 'withdraw', 'borrow', 'repay', 'liquidate');
            END IF;
        END $$;
    """)

    op.execute("""
        DO $$ BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'transaction_status_enum') THEN
                CREATE TYPE transaction_status_enum AS ENUM ('pending', 'confirmed', 'failed');
            END IF;
        END $$;
    """)

    # =========================================================================
    # TABLE: lending_positions
    # =========================================================================

    op.create_table(
        "lending_positions",
        # Primary Key
        sa.Column(
            "id",
            UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        # User Reference
        sa.Column(
            "user_id",
            UUID(as_uuid=True),
            sa.ForeignKey("chat_users.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        # Protocol Information
        sa.Column(
            "protocol",
            sa.Enum("aave", "morpho", name="protocol_enum", create_type=False),
            nullable=False,
        ),
        sa.Column("chain", sa.String(20), nullable=False),
        # Position Type
        sa.Column(
            "position_type",
            sa.Enum("supply", "borrow", name="position_type_enum", create_type=False),
            nullable=False,
        ),
        # Asset Information
        sa.Column("asset_address", sa.String(42), nullable=False),
        sa.Column("asset_symbol", sa.String(20), nullable=False),
        # Amount Details
        sa.Column("amount", sa.Numeric(78, 18), nullable=False),
        sa.Column("amount_usd", sa.Numeric(18, 2), nullable=False),
        # Health Metrics (nullable for supply-only positions)
        sa.Column("health_factor", sa.Numeric(10, 2), nullable=True),
        # APY
        sa.Column("apy", sa.Numeric(6, 2), nullable=False),
        # Status
        sa.Column(
            "status",
            sa.Enum(
                "active",
                "closed",
                "liquidated",
                name="lending_status_enum",
                create_type=False,
            ),
            nullable=False,
            server_default="active",
        ),
        # Timestamps
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.Column(
            "updated_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
    )

    # Indexes for lending_positions
    op.create_index(
        "idx_lending_positions_user_protocol",
        "lending_positions",
        ["user_id", "protocol"],
    )
    op.create_index("idx_lending_positions_status", "lending_positions", ["status"])
    op.create_index(
        "idx_lending_positions_user_protocol_status",
        "lending_positions",
        ["user_id", "protocol", "status"],
    )

    # =========================================================================
    # TABLE: lending_supplies
    # =========================================================================

    op.create_table(
        "lending_supplies",
        # Primary Key
        sa.Column(
            "id",
            UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        # Position Reference
        sa.Column(
            "position_id",
            UUID(as_uuid=True),
            sa.ForeignKey("lending_positions.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        # User Reference
        sa.Column(
            "user_id",
            UUID(as_uuid=True),
            sa.ForeignKey("chat_users.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        # Protocol Information
        sa.Column(
            "protocol",
            sa.Enum("aave", "morpho", name="protocol_enum", create_type=False),
            nullable=False,
        ),
        sa.Column("chain", sa.String(20), nullable=False),
        # Asset Information
        sa.Column("asset_address", sa.String(42), nullable=False),
        sa.Column("asset_symbol", sa.String(20), nullable=False),
        # Supply Details
        sa.Column("amount", sa.Numeric(78, 18), nullable=False),
        sa.Column("apy", sa.Numeric(6, 2), nullable=False),
        # Transaction Details
        sa.Column("transaction_hash", sa.String(66), nullable=False, unique=True),
        sa.Column("block_number", sa.BigInteger, nullable=False),
        sa.Column("gas_used", sa.Numeric(78, 0), nullable=False),
        # Timestamps
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
    )

    # Indexes for lending_supplies
    op.create_index(
        "idx_lending_supplies_transaction_hash",
        "lending_supplies",
        ["transaction_hash"],
    )

    # =========================================================================
    # TABLE: lending_borrows
    # =========================================================================

    op.create_table(
        "lending_borrows",
        # Primary Key
        sa.Column(
            "id",
            UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        # Position Reference
        sa.Column(
            "position_id",
            UUID(as_uuid=True),
            sa.ForeignKey("lending_positions.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        # User Reference
        sa.Column(
            "user_id",
            UUID(as_uuid=True),
            sa.ForeignKey("chat_users.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        # Protocol Information
        sa.Column(
            "protocol",
            sa.Enum("aave", "morpho", name="protocol_enum", create_type=False),
            nullable=False,
        ),
        sa.Column("chain", sa.String(20), nullable=False),
        # Asset Information
        sa.Column("asset_address", sa.String(42), nullable=False),
        sa.Column("asset_symbol", sa.String(20), nullable=False),
        # Borrow Details
        sa.Column("amount", sa.Numeric(78, 18), nullable=False),
        sa.Column("interest_rate", sa.Numeric(6, 2), nullable=False),
        sa.Column("variable_rate", sa.Boolean, nullable=False, server_default="true"),
        # Health Factor at Time of Borrow
        sa.Column("health_factor_at_borrow", sa.Numeric(10, 2), nullable=False),
        # Transaction Details
        sa.Column("transaction_hash", sa.String(66), nullable=False, unique=True),
        sa.Column("block_number", sa.BigInteger, nullable=False),
        # Timestamps
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
    )

    # Indexes for lending_borrows
    op.create_index(
        "idx_lending_borrows_transaction_hash",
        "lending_borrows",
        ["transaction_hash"],
    )

    # =========================================================================
    # TABLE: lending_transactions
    # =========================================================================

    op.create_table(
        "lending_transactions",
        # Primary Key
        sa.Column(
            "id",
            UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        # User Reference
        sa.Column(
            "user_id",
            UUID(as_uuid=True),
            sa.ForeignKey("chat_users.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        # Protocol Information
        sa.Column(
            "protocol",
            sa.Enum("aave", "morpho", name="protocol_enum", create_type=False),
            nullable=False,
        ),
        sa.Column("chain", sa.String(20), nullable=False),
        # Action Type
        sa.Column(
            "action_type",
            sa.Enum(
                "supply",
                "withdraw",
                "borrow",
                "repay",
                "liquidate",
                name="lending_action_enum",
                create_type=False,
            ),
            nullable=False,
        ),
        # Asset Information
        sa.Column("asset_address", sa.String(42), nullable=False),
        sa.Column("asset_symbol", sa.String(20), nullable=False),
        sa.Column("amount", sa.Numeric(78, 18), nullable=False),
        # Transaction Details
        sa.Column("transaction_hash", sa.String(66), nullable=False, unique=True),
        # Status
        sa.Column(
            "status",
            sa.Enum(
                "pending",
                "confirmed",
                "failed",
                name="transaction_status_enum",
                create_type=False,
            ),
            nullable=False,
            server_default="pending",
        ),
        # Health Factor Impact (nullable for supply/withdraw)
        sa.Column("health_factor_before", sa.Numeric(10, 2), nullable=True),
        sa.Column("health_factor_after", sa.Numeric(10, 2), nullable=True),
        # Metadata
        sa.Column("metadata", JSONB, nullable=True),
        # Timestamps
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.Column("confirmed_at", sa.TIMESTAMP(timezone=True), nullable=True),
    )

    # Indexes for lending_transactions
    op.create_index(
        "idx_lending_transactions_transaction_hash",
        "lending_transactions",
        ["transaction_hash"],
    )
    op.create_index(
        "idx_lending_transactions_status", "lending_transactions", ["status"]
    )
    op.create_index(
        "idx_lending_transactions_user_protocol_action",
        "lending_transactions",
        ["user_id", "protocol", "action_type"],
    )


def downgrade() -> None:
    """Drop lending tables and enums."""

    # Drop tables in reverse order (respecting foreign keys)
    op.drop_table("lending_transactions")
    op.drop_table("lending_borrows")
    op.drop_table("lending_supplies")
    op.drop_table("lending_positions")

    # Drop enums
    op.execute("DROP TYPE IF EXISTS transaction_status_enum")
    op.execute("DROP TYPE IF EXISTS lending_action_enum")
    op.execute("DROP TYPE IF EXISTS lending_status_enum")
    op.execute("DROP TYPE IF EXISTS position_type_enum")
    op.execute("DROP TYPE IF EXISTS protocol_enum")
