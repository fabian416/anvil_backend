"""
SQLAlchemy mapping for Transaction table metadata.
"""

from sqlalchemy import Integer, String, DateTime, Enum, ForeignKey, Numeric, Text, JSON
from sqlalchemy.orm import mapped_column
import sqlalchemy as sa

from app.domain.enums.chain_type import ChainType
from app.infrastructure.persistence_sqla.registry import mapping_registry

def map_transaction_table() -> None:
    """Map Transaction entity to database table (idempotent)."""
    if "transactions" in mapping_registry.metadata.tables:
        return

    @mapping_registry.mapped
    class TransactionsTable:
        __tablename__ = "transactions"
        __table_args__ = {"extend_existing": True}
        
        # Primary key
        id = mapped_column(Integer, primary_key=True, autoincrement=True)
        
        # Relationships
        user_id = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
        wallet_id = mapped_column(Integer, ForeignKey("wallets.id", ondelete="CASCADE"), nullable=False, index=True)
        
        # Transaction details
        type = mapped_column(Integer, nullable=False, index=True) # 0=SWAP, 1=FUND, etc.
        chain = mapped_column(Enum(ChainType, values_callable=lambda x: [e.value for e in x]), nullable=False, index=True)
        
        asset_in = mapped_column(String(20), nullable=True)
        amount_in = mapped_column(Numeric(30, 18), nullable=True)
        asset_out = mapped_column(String(20), nullable=True)
        amount_out = mapped_column(Numeric(30, 18), nullable=True)
        
        fee = mapped_column(Numeric(30, 18), nullable=True)
        fee_usd = mapped_column(Numeric(10, 2), nullable=True)
        
        tx_hash = mapped_column(String(66), unique=True, nullable=True, index=True)
        status = mapped_column(Integer, default=0, nullable=False, index=True) # 0=PENDING
        
        dex_aggregator = mapped_column(String(50), nullable=True)
        dex_route = mapped_column(JSON, nullable=True)
        slippage = mapped_column(Numeric(5, 2), nullable=True)
        error_message = mapped_column(Text, nullable=True)
        
        block_number = mapped_column(Integer, nullable=True)
        confirmed_at = mapped_column(DateTime(timezone=True), nullable=True)
        
        # Timestamps
        created_at = mapped_column(DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), index=True)
