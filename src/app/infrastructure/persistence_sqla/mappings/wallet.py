"""
SQLAlchemy mapping for Wallet and ChainAddress tables metadata.

Wallet types:
- PRIVY: Privy embedded wallet (privy_wallet_id required)
- EXTERNAL: External wallet connected via browser extension
- IMPORTED: Wallet imported via private key (privy_wallet_id can be null or synthetic)

Privy Configuration Fields (for admin management):
- policy_ids: JSON array of policy IDs
- owner_type: Type of owner (user, authorization_key, etc.)
- owner_id: ID of the owner
- additional_signers: JSON array of additional signers
- exported_at: When the wallet was exported
- imported_at: When the wallet was imported
- last_privy_sync_at: Last time we synced with Privy API
"""

from sqlalchemy import Integer, String, DateTime, Enum, ForeignKey, Boolean, Numeric, UniqueConstraint, Index, JSON
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
        __table_args__ = (
            # Unique constraint for user_id + address to prevent duplicates
            UniqueConstraint('user_id', 'address', name='unique_user_wallet_address'),
            {"extend_existing": True},
        )
        
        # Primary key
        id = mapped_column(Integer, primary_key=True, autoincrement=True)
        
        # Relationships
        user_id = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
        
        # Wallet details
        # privy_wallet_id is nullable for imported wallets
        # For imported wallets, we use a synthetic ID like "imported:<address>"
        privy_wallet_id = mapped_column(String(255), unique=True, nullable=True, index=True)
        address = mapped_column(String(42), nullable=False, index=True)
        provider = mapped_column(Enum(WalletProvider, values_callable=lambda x: [e.value for e in x], name="walletprovider", create_type=False), default=WalletProvider.PRIVY, nullable=False)
        default_chain = mapped_column(Enum(ChainType, values_callable=lambda x: [e.value for e in x], name="chaintype", create_type=False), default=ChainType.ARBITRUM)
        status = mapped_column(Integer, default=WalletStatus.ACTIVE.value, nullable=False)
        
        # Privy configuration fields (for admin management)
        policy_ids = mapped_column(JSON, nullable=True, default=None)  # Array of policy IDs
        owner_type = mapped_column(String(50), nullable=True, default=None)  # e.g., "user", "authorization_key"
        owner_id = mapped_column(String(255), nullable=True, default=None)  # ID of the owner
        additional_signers = mapped_column(JSON, nullable=True, default=None)  # Array of signer objects
        exported_at = mapped_column(DateTime(timezone=True), nullable=True, default=None)
        imported_at = mapped_column(DateTime(timezone=True), nullable=True, default=None)
        last_privy_sync_at = mapped_column(DateTime(timezone=True), nullable=True, default=None)
        
        # Balance check tracking (for Celery background sync)
        last_balance_checked_at = mapped_column(DateTime(timezone=True), nullable=True, default=None, index=True)
        
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
        chain = mapped_column(Enum(ChainType, values_callable=lambda x: [e.value for e in x], name="chaintype", create_type=False), nullable=False, index=True)
        address = mapped_column(String(255), nullable=False, index=True)
        is_active = mapped_column(Boolean, default=True, index=True)
        
        # Balance
        balance_usd = mapped_column(Numeric(20, 2), default=0.00)
        eth_balance = mapped_column(Numeric(30, 18), nullable=True, default=0)  # Native token (ETH) for gas
        last_balance_update = mapped_column(DateTime(timezone=True), nullable=True)
        
        # Timestamps
        created_at = mapped_column(DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'))
