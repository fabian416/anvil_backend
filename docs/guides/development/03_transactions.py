"""
Anvil Platform - SQLAlchemy Models
Section 3: Transaction Models

These models track all financial transactions including swaps, funding,
earn deposits, and save operations.
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


class TransactionType(enum.IntEnum):
    """Transaction type enum"""

    SWAP = 0  # Token swap via DEX
    FUND = 1  # Fiat to crypto (funding)
    EARN = 2  # Deposit/withdraw from yield protocol
    SAVE = 3  # Automated save (DCA)
    SUBSCRIPTION = 4  # Subscription payment


class TransactionStatus(enum.IntEnum):
    """Transaction status enum"""

    PENDING = 0
    SUCCESS = 1
    FAILED = 2


# ============================================================================
# Transaction Models
# ============================================================================


class Transaction(Base):
    """
    Universal transaction table for all transaction types

    This table records all user-initiated financial transactions across
    different operations (swaps, funding, earn, save).
    """

    __tablename__ = "transactions"

    # Primary Key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Foreign Keys
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    wallet_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("wallets.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Transaction Classification
    type: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        index=True,
        comment="0=SWAP, 1=FUND, 2=EARN, 3=SAVE, 4=SUBSCRIPTION",
    )
    chain: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
        comment="Blockchain network (arbitrum, base, hyperliquid)",
    )

    # Transaction Amounts (Input)
    asset_in: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        index=True,
        comment="Input asset symbol (e.g., USDC, ETH, USD for fiat)",
    )
    amount_in: Mapped[Decimal] = mapped_column(
        Numeric(36, 18), nullable=False, comment="Input amount"
    )
    amount_in_usd: Mapped[Decimal] = mapped_column(
        Numeric(20, 2),
        nullable=False,
        default=Decimal("0"),
        comment="USD value of input",
    )

    # Transaction Amounts (Output)
    asset_out: Mapped[Optional[str]] = mapped_column(
        String(20), nullable=True, index=True, comment="Output asset symbol"
    )
    amount_out: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(36, 18), nullable=True, comment="Output amount received"
    )
    amount_out_usd: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(20, 2), nullable=True, comment="USD value of output"
    )

    # Fees
    fee: Mapped[Decimal] = mapped_column(
        Numeric(36, 18),
        nullable=False,
        default=Decimal("0"),
        comment="Fee paid in native token",
    )
    fee_usd: Mapped[Decimal] = mapped_column(
        Numeric(10, 2), nullable=False, default=Decimal("0"), comment="Fee in USD"
    )

    # Blockchain Information
    tx_hash: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        unique=True,
        index=True,
        comment="Blockchain transaction hash",
    )
    block_number: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True, comment="Block number where transaction was confirmed"
    )
    nonce: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True, comment="Transaction nonce"
    )

    # Gas Information (for EVM chains)
    gas_used: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True, comment="Gas units consumed"
    )
    gas_price: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(20, 10), nullable=True, comment="Gas price in gwei"
    )

    # Status
    status: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=TransactionStatus.PENDING,
        index=True,
        comment="0=PENDING, 1=SUCCESS, 2=FAILED",
    )
    error_message: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, comment="Error message if transaction failed"
    )

    # DEX Information (for SWAP type)
    dex_aggregator: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True, comment="DEX aggregator used (e.g., '1inch', '0x')"
    )
    dex_route: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, comment="JSON: Route taken through DEX pools"
    )
    slippage: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(5, 2),
        nullable=True,
        comment="Slippage tolerance percentage (e.g., 0.5 for 0.5%)",
    )

    # Protocol Information (for EARN type)
    protocol: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True, comment="DeFi protocol (e.g., 'aave', 'compound')"
    )
    protocol_action: Mapped[Optional[str]] = mapped_column(
        String(20), nullable=True, comment="'deposit', 'withdraw', 'claim'"
    )

    # Related Records
    earn_position_id: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True, index=True, comment="Related earn position ID"
    )
    save_schedule_id: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True, index=True, comment="Related save schedule ID"
    )
    funding_transaction_id: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True, index=True, comment="Related funding transaction ID"
    )

    # Metadata
    metadata_json: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, comment="JSON: Additional transaction metadata"
    )

    # Timestamps
    confirmed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        nullable=True,
        index=True,
        comment="When transaction was confirmed on-chain",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now(), index=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    user = relationship("User", back_populates="transactions")
    wallet = relationship("Wallet", back_populates="transactions")

    # Indexes
    __table_args__ = (
        Index("idx_transaction_user_type", "user_id", "type"),
        Index("idx_transaction_user_status", "user_id", "status"),
        Index("idx_transaction_type_status", "type", "status"),
        Index("idx_transaction_chain_status", "chain", "status"),
        Index("idx_transaction_created", "created_at"),
        Index("idx_transaction_confirmed", "confirmed_at"),
        Index("idx_transaction_asset_in", "asset_in"),
        Index("idx_transaction_asset_out", "asset_out"),
    )

    def __repr__(self) -> str:
        return f"<Transaction(id={self.id}, type={self.type}, status={self.status}, amount_in={self.amount_in} {self.asset_in})>"

    @property
    def type_label(self) -> str:
        """Get human-readable transaction type"""
        type_map = {0: "SWAP", 1: "FUND", 2: "EARN", 3: "SAVE", 4: "SUBSCRIPTION"}
        return type_map.get(self.type, "UNKNOWN")

    @property
    def status_label(self) -> str:
        """Get human-readable status"""
        status_map = {0: "PENDING", 1: "SUCCESS", 2: "FAILED"}
        return status_map.get(self.status, "UNKNOWN")

    @property
    def is_pending(self) -> bool:
        """Check if transaction is pending"""
        return self.status == TransactionStatus.PENDING

    @property
    def is_success(self) -> bool:
        """Check if transaction succeeded"""
        return self.status == TransactionStatus.SUCCESS

    @property
    def is_failed(self) -> bool:
        """Check if transaction failed"""
        return self.status == TransactionStatus.FAILED

    @property
    def explorer_url(self) -> Optional[str]:
        """Get block explorer URL for this transaction"""
        if not self.tx_hash:
            return None

        explorer_map = {
            "arbitrum": f"https://arbiscan.io/tx/{self.tx_hash}",
            "base": f"https://basescan.org/tx/{self.tx_hash}",
            "hyperliquid": f"https://hyperliquid.xyz/tx/{self.tx_hash}",
        }
        return explorer_map.get(self.chain)


class FundingTransaction(Base):
    """
    Fiat-to-crypto funding transactions (Stripe payments)

    Tracks purchases of crypto using fiat currency through payment processors.
    """

    __tablename__ = "funding_transactions"

    # Primary Key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Foreign Keys
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    wallet_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("wallets.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Link to main transaction
    transaction_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("transactions.id", ondelete="SET NULL"),
        nullable=True,
        unique=True,
        index=True,
    )

    # Fiat Payment Information
    amount_fiat: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), nullable=False, comment="Amount in fiat currency (e.g., USD)"
    )
    currency_fiat: Mapped[str] = mapped_column(
        String(3),
        nullable=False,
        default="USD",
        comment="Fiat currency code (ISO 4217)",
    )

    # Crypto Output
    amount_crypto: Mapped[Decimal] = mapped_column(
        Numeric(36, 18), nullable=False, comment="Amount of crypto purchased"
    )
    asset_crypto: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        index=True,
        comment="Crypto asset symbol (e.g., USDC, ETH)",
    )
    chain: Mapped[str] = mapped_column(
        String(50), nullable=False, comment="Destination blockchain"
    )

    # Payment Method
    payment_method: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="'card', 'ach', 'wire', 'apple_pay', 'google_pay'",
    )
    payment_processor: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="stripe",
        comment="Payment processor (e.g., 'stripe')",
    )

    # Stripe Information
    stripe_payment_intent_id: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True, unique=True, index=True
    )
    stripe_charge_id: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True, unique=True, index=True
    )
    stripe_customer_id: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True, index=True
    )

    # Fees
    fee_stripe: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
        default=Decimal("0"),
        comment="Stripe processing fee",
    )
    fee_network: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
        default=Decimal("0"),
        comment="Blockchain network fee",
    )
    fee_total: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), nullable=False, default=Decimal("0"), comment="Total fees paid"
    )

    # Exchange Rate
    exchange_rate: Mapped[Decimal] = mapped_column(
        Numeric(20, 8),
        nullable=False,
        comment="Crypto/fiat exchange rate at time of purchase",
    )

    # Status
    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="pending",
        index=True,
        comment="'pending', 'processing', 'completed', 'failed', 'refunded'",
    )
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Blockchain Transaction
    transaction_hash: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True, index=True, comment="On-chain transaction hash"
    )

    # Refund Information
    refunded_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    refund_amount: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(12, 2), nullable=True
    )
    refund_reason: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Timestamps
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True, index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now(), index=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    user = relationship("User", back_populates="funding_transactions")
    wallet = relationship("Wallet", back_populates="funding_transactions")

    # Indexes
    __table_args__ = (
        Index("idx_funding_user_status", "user_id", "status"),
        Index("idx_funding_created", "created_at"),
        Index("idx_funding_completed", "completed_at"),
        Index("idx_funding_stripe_pi", "stripe_payment_intent_id"),
    )

    def __repr__(self) -> str:
        return f"<FundingTransaction(id={self.id}, amount_fiat={self.amount_fiat}, amount_crypto={self.amount_crypto}, status='{self.status}')>"

    @property
    def is_completed(self) -> bool:
        """Check if funding is completed"""
        return self.status == "completed"

    @property
    def total_cost(self) -> Decimal:
        """Calculate total cost including fees"""
        return self.amount_fiat + self.fee_total


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

    print("✅ Transaction tables created successfully!")
    print("\nTables created:")
    print("- transactions")
    print("- funding_transactions")
