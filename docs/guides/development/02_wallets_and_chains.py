"""
Anvil Platform - SQLAlchemy Models
Section 2: Wallet and Chain Models

These models handle wallet management and multi-chain address tracking.
"""

from datetime import datetime
from typing import Optional
from sqlalchemy import (
    Column,
    Integer,
    String,
    Numeric,
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Text,
    Enum as SQLEnum,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from decimal import Decimal
import enum

from .base_and_users import Base


# ============================================================================
# Enums
# ============================================================================


class WalletStatus(enum.IntEnum):
    """Wallet status enum"""

    INACTIVE = 0
    ACTIVE = 1
    SUSPENDED = 2


class ChainType(str, enum.Enum):
    """Supported blockchain networks"""

    ARBITRUM = "arbitrum"
    BASE = "base"
    HYPERLIQUID = "hyperliquid"


# ============================================================================
# Wallet Models
# ============================================================================


class Wallet(Base):
    """
    Primary wallet for each user (Privy embedded wallet)

    Each user has ONE primary wallet that is created during first login.
    This wallet is managed by Privy and provides multi-chain support.
    """

    __tablename__ = "wallets"

    # Primary Key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Foreign Key
    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,  # One wallet per user
        index=True,
    )

    # Wallet Identifiers
    address: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        unique=True,
        index=True,
        comment="Primary Ethereum-compatible address (checksummed)",
    )
    privy_wallet_id: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        unique=True,
        index=True,
        comment="Privy's internal wallet identifier",
    )

    # Wallet Configuration
    provider: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="privy",
        comment="Wallet provider (e.g., 'privy', 'metamask', 'walletconnect')",
    )
    wallet_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="embedded",
        comment="'embedded', 'external', 'custodial'",
    )
    default_chain: Mapped[str] = mapped_column(
        SQLEnum(ChainType),
        nullable=False,
        default=ChainType.ARBITRUM,
        comment="Default chain for operations",
    )

    # Status
    status: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=WalletStatus.ACTIVE,
        index=True,
        comment="0=INACTIVE, 1=ACTIVE, 2=SUSPENDED",
    )

    # Security
    is_recovery_enabled: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True
    )
    recovery_method: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True, comment="'email', 'sms', 'social'"
    )

    # Metadata
    metadata_json: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, comment="JSON: Additional wallet metadata from Privy"
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now(), index=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now(), onupdate=func.now()
    )
    last_activity_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True, index=True
    )

    # Relationships
    user = relationship("User", back_populates="wallets")
    chain_addresses = relationship(
        "ChainAddress",
        back_populates="wallet",
        lazy="select",
        cascade="all, delete-orphan",
    )
    transactions = relationship("Transaction", back_populates="wallet", lazy="select")
    earn_positions = relationship(
        "EarnPosition", back_populates="wallet", lazy="select"
    )
    save_schedules = relationship(
        "SaveSchedule", back_populates="wallet", lazy="select"
    )
    hyperliquid_positions = relationship(
        "HyperliquidPosition", back_populates="wallet", lazy="select"
    )
    funding_transactions = relationship(
        "FundingTransaction", back_populates="wallet", lazy="select"
    )

    # Indexes
    __table_args__ = (
        Index("idx_wallet_user_status", "user_id", "status"),
        Index("idx_wallet_address", "address"),
    )

    def __repr__(self) -> str:
        return f"<Wallet(id={self.id}, user_id={self.user_id}, address='{self.address[:10]}...')>"

    @property
    def status_label(self) -> str:
        """Get human-readable status label"""
        status_map = {0: "INACTIVE", 1: "ACTIVE", 2: "SUSPENDED"}
        return status_map.get(self.status, "UNKNOWN")

    @property
    def is_active(self) -> bool:
        """Check if wallet is active"""
        return self.status == WalletStatus.ACTIVE


class ChainAddress(Base):
    """
    Multi-chain address tracking

    Each wallet has addresses on multiple chains. This table tracks the
    address for each supported chain, along with balance and activity data.
    """

    __tablename__ = "chain_addresses"

    # Primary Key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Foreign Key
    wallet_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("wallets.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Chain Information
    chain: Mapped[str] = mapped_column(
        SQLEnum(ChainType),
        nullable=False,
        index=True,
        comment="Blockchain network identifier",
    )
    chain_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        comment="EVM chain ID (e.g., 42161 for Arbitrum, null for non-EVM)",
    )

    # Address
    address: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True,
        comment="Chain-specific address (may differ from primary wallet address)",
    )

    # Balance Tracking
    balance_native: Mapped[Decimal] = mapped_column(
        Numeric(36, 18),
        nullable=False,
        default=Decimal("0"),
        comment="Native token balance (e.g., ETH, HYPE)",
    )
    balance_usd: Mapped[Decimal] = mapped_column(
        Numeric(20, 2),
        nullable=False,
        default=Decimal("0"),
        comment="Total USD value of all assets on this chain",
    )

    # Activity Tracking
    transaction_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        comment="Total number of transactions on this chain",
    )
    last_balance_update: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        nullable=True,
        index=True,
        comment="Last time balance was refreshed from RPC",
    )
    last_transaction_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True, comment="Last transaction timestamp"
    )

    # Status
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        comment="Whether this chain address is active for use",
    )

    # RPC Configuration
    rpc_endpoint: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
        comment="Custom RPC endpoint for this chain (if any)",
    )
    explorer_url: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
        comment="Block explorer URL base (e.g., 'https://arbiscan.io')",
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    wallet = relationship("Wallet", back_populates="chain_addresses")

    # Indexes and Constraints
    __table_args__ = (
        Index("idx_chain_address_wallet", "wallet_id", "chain"),
        Index("idx_chain_address_chain", "chain", "is_active"),
        Index("idx_chain_address_address", "address"),
        Index("idx_chain_address_balance_update", "last_balance_update"),
        # Unique constraint: one address per wallet per chain
        Index("uq_wallet_chain", "wallet_id", "chain", unique=True),
    )

    def __repr__(self) -> str:
        return f"<ChainAddress(id={self.id}, wallet_id={self.wallet_id}, chain='{self.chain}', balance_usd={self.balance_usd})>"

    @property
    def chain_label(self) -> str:
        """Get human-readable chain label"""
        chain_map = {
            "arbitrum": "Arbitrum One",
            "base": "Base",
            "hyperliquid": "Hyperliquid",
        }
        return chain_map.get(self.chain, self.chain.upper())

    @property
    def explorer_address_url(self) -> Optional[str]:
        """Get full explorer URL for this address"""
        if not self.explorer_url or not self.address:
            return None
        return f"{self.explorer_url}/address/{self.address}"


class TokenBalance(Base):
    """
    Individual token balances per chain address

    Tracks specific ERC-20 token balances on each chain.
    Native tokens (ETH, etc.) are tracked in ChainAddress.balance_native.
    """

    __tablename__ = "token_balances"

    # Primary Key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Foreign Key
    chain_address_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("chain_addresses.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Token Information
    contract_address: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True,
        comment="Token contract address (0x0 for native token)",
    )
    token_symbol: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        index=True,
        comment="Token symbol (e.g., 'USDC', 'ETH')",
    )
    token_name: Mapped[str] = mapped_column(
        String(100), nullable=False, comment="Full token name"
    )
    token_decimals: Mapped[int] = mapped_column(
        Integer, nullable=False, default=18, comment="Token decimal places"
    )

    # Balance
    balance_raw: Mapped[str] = mapped_column(
        String(78),
        nullable=False,
        default="0",
        comment="Raw balance as string (to handle uint256)",
    )
    balance_formatted: Mapped[Decimal] = mapped_column(
        Numeric(36, 18),
        nullable=False,
        default=Decimal("0"),
        comment="Human-readable balance",
    )
    balance_usd: Mapped[Decimal] = mapped_column(
        Numeric(20, 2), nullable=False, default=Decimal("0"), comment="USD value"
    )

    # Price Information
    price_usd: Mapped[Decimal] = mapped_column(
        Numeric(20, 8),
        nullable=False,
        default=Decimal("0"),
        comment="Current token price in USD",
    )
    price_source: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        comment="Price oracle source (e.g., 'chainlink', 'coingecko')",
    )

    # Metadata
    is_native: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        comment="Is this the native chain token?",
    )
    is_verified: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, comment="Is token contract verified?"
    )
    logo_url: Mapped[Optional[str]] = mapped_column(
        String(500), nullable=True, comment="Token logo image URL"
    )

    # Timestamps
    last_updated: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
        index=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )

    # Indexes
    __table_args__ = (
        Index(
            "idx_token_balance_chain_address", "chain_address_id", "contract_address"
        ),
        Index("idx_token_balance_symbol", "token_symbol"),
        Index("idx_token_balance_updated", "last_updated"),
        # Unique: one record per token per chain address
        Index(
            "uq_chain_address_token",
            "chain_address_id",
            "contract_address",
            unique=True,
        ),
    )

    def __repr__(self) -> str:
        return f"<TokenBalance(id={self.id}, token='{self.token_symbol}', balance={self.balance_formatted})>"

    @property
    def balance_display(self) -> str:
        """Get formatted balance for display"""
        if self.balance_formatted >= 1000000:
            return f"{self.balance_formatted / 1000000:.2f}M"
        elif self.balance_formatted >= 1000:
            return f"{self.balance_formatted / 1000:.2f}K"
        else:
            return f"{self.balance_formatted:.4f}"


# ============================================================================
# Usage Example
# ============================================================================

if __name__ == "__main__":
    from sqlalchemy import create_engine
    from .base_and_users import Base

    DATABASE_URL = "mysql+pymysql://user:password@localhost:3306/anvil"
    engine = create_engine(DATABASE_URL)

    # Create all tables
    Base.metadata.create_all(engine)

    print("✅ Wallet and Chain tables created successfully!")
    print("\nTables created:")
    print("- wallets")
    print("- chain_addresses")
    print("- token_balances")
