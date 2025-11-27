"""
SQLAlchemy mapping for Wallet and ChainAddress tables metadata.
"""

from sqlalchemy import Integer, String, DateTime, Enum, ForeignKey, Boolean, Numeric, UniqueConstraint
from sqlalchemy.orm import mapped_column
import sqlalchemy as sa

from app.domain.enums.chain_type import ChainType
from app.domain.enums.wallet_provider import WalletProvider
from app.domain.enums.wallet_status import WalletStatus
from app.infrastructure.persistence_sqla.registry import mapping_registry

def map_wallet_tables() -> None:
    """Map Wallet and ChainAddress entities to database tables (idempotent)."""
    if "wallets" in mapping_registry.metadata.tables:
        return

    @mapping_registry.mapped
    class WalletsTable:
        __tablename__ = "wallets"
        __table_args__ = {"extend_existing": True}
        
        # Primary key
        id = mapped_column(Integer, primary_key=True, autoincrement=True)
        
        # Relationships
        user_id = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
        
        # Wallet details
        privy_wallet_id = mapped_column(String(255), unique=True, nullable=False, index=True)
        address = mapped_column(String(42), unique=True, nullable=False, index=True)
        provider = mapped_column(Enum(WalletProvider, values_callable=lambda x: [e.value for e in x]), default=WalletProvider.PRIVY, nullable=False)
        default_chain = mapped_column(Enum(ChainType, values_callable=lambda x: [e.value for e in x]), default=ChainType.ARBITRUM)
        status = mapped_column(Integer, default=WalletStatus.ACTIVE.value, nullable=False)
        
        # Timestamps
        created_at = mapped_column(DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'))
        updated_at = mapped_column(DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), onupdate=sa.text('CURRENT_TIMESTAMP'))

    @mapping_registry.mapped
    class ChainAddressesTable:
        __tablename__ = "chain_addresses"
        __table_args__ = (
            UniqueConstraint('wallet_id', 'chain', name='unique_wallet_chain'),
            {"extend_existing": True}
        )
        
        # Primary key
        id = mapped_column(Integer, primary_key=True, autoincrement=True)
        
        # Relationships
        wallet_id = mapped_column(Integer, ForeignKey("wallets.id", ondelete="CASCADE"), nullable=False, index=True)
        
        # Chain details
        chain = mapped_column(Enum(ChainType, values_callable=lambda x: [e.value for e in x]), nullable=False, index=True)
        address = mapped_column(String(255), nullable=False, index=True)
        is_active = mapped_column(Boolean, default=True, index=True)
        
        # Balance
        balance_usd = mapped_column(Numeric(20, 2), default=0.00)
        last_balance_update = mapped_column(DateTime(timezone=True), nullable=True)
        
        # Timestamps
        created_at = mapped_column(DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'))
