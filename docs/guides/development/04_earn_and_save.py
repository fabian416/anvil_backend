"""
Anvil Platform - SQLAlchemy Models
Section 4: Earn and Save Models

These models handle yield farming positions (Aave, Compound) and
automated savings schedules (DCA functionality).
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


class EarnPositionStatus(str, enum.Enum):
    """Earn position status"""

    ACTIVE = "active"
    WITHDRAWN = "withdrawn"
    FAILED = "failed"


class EarnTransactionProtocol(str, enum.Enum):
    """Earn transaction protocol"""

    AAVE = "aave"
    COMPOUND = "compound"


class EarnTransactionAction(str, enum.Enum):
    """Earn transaction action type"""

    SUPPLY = "supply"
    WITHDRAW = "withdraw"


class EarnTransactionStatus(str, enum.Enum):
    """Earn transaction status"""

    PENDING = "pending"
    CONFIRMED = "confirmed"
    FAILED = "failed"


class SaveScheduleStatus(str, enum.Enum):
    """Save schedule status"""

    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class SaveScheduleFrequency(str, enum.Enum):
    """Save schedule frequency"""

    DAILY = "daily"
    WEEKLY = "weekly"
    BIWEEKLY = "biweekly"
    MONTHLY = "monthly"


# ============================================================================
# Earn Models
# ============================================================================


class EarnPosition(Base):
    """
    Yield farming positions (Aave, Compound, Curve)

    Tracks deposits into DeFi lending/yield protocols. Users can deposit
    assets and earn interest over time.
    """

    __tablename__ = "earn_positions"

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

    # Protocol Information
    chain: Mapped[str] = mapped_column(
        String(50), nullable=False, index=True, comment="Blockchain network"
    )
    protocol: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
        comment="DeFi protocol (e.g., 'aave', 'compound', 'curve')",
    )
    protocol_pool_id: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True, comment="Protocol-specific pool/market identifier"
    )

    # Asset Information
    asset: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        index=True,
        comment="Deposited asset symbol (e.g., USDC, ETH)",
    )
    asset_contract_address: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True, comment="Token contract address"
    )

    # Position Amounts
    amount_deposited: Mapped[Decimal] = mapped_column(
        Numeric(36, 18), nullable=False, comment="Initial deposit amount"
    )
    amount_deposited_usd: Mapped[Decimal] = mapped_column(
        Numeric(20, 2), nullable=False, comment="USD value at deposit"
    )
    current_value: Mapped[Decimal] = mapped_column(
        Numeric(36, 18),
        nullable=False,
        default=Decimal("0"),
        comment="Current position value (principal + rewards)",
    )
    current_value_usd: Mapped[Decimal] = mapped_column(
        Numeric(20, 2),
        nullable=False,
        default=Decimal("0"),
        comment="Current USD value",
    )

    # Rewards Tracking
    rewards_earned: Mapped[Decimal] = mapped_column(
        Numeric(36, 18),
        nullable=False,
        default=Decimal("0"),
        comment="Total rewards earned in asset",
    )
    rewards_earned_usd: Mapped[Decimal] = mapped_column(
        Numeric(20, 2),
        nullable=False,
        default=Decimal("0"),
        comment="Total rewards in USD",
    )
    rewards_claimed: Mapped[Decimal] = mapped_column(
        Numeric(36, 18),
        nullable=False,
        default=Decimal("0"),
        comment="Total rewards claimed",
    )

    # APY Information
    apy: Mapped[Decimal] = mapped_column(
        Numeric(8, 4),
        nullable=False,
        default=Decimal("0"),
        comment="APY at time of deposit (%)",
    )
    current_apy: Mapped[Decimal] = mapped_column(
        Numeric(8, 4), nullable=False, default=Decimal("0"), comment="Current APY (%)"
    )

    # Status
    status: Mapped[str] = mapped_column(
        SQLEnum(EarnPositionStatus),
        nullable=False,
        default=EarnPositionStatus.ACTIVE,
        index=True,
    )

    # Blockchain Transactions
    deposit_tx_hash: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True, index=True, comment="Deposit transaction hash"
    )
    withdrawal_tx_hash: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True, index=True, comment="Withdrawal transaction hash"
    )

    # Money Market additions (Aave V3 / Compound V3)
    pool_address: Mapped[Optional[str]] = mapped_column(
        String(42),
        nullable=True,
        comment="Aave pool or Compound comet address",
    )
    wallet_address: Mapped[Optional[str]] = mapped_column(
        String(42),
        nullable=True,
        comment="User wallet address",
    )
    last_synced_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        nullable=True,
        comment="Last time position was synced from on-chain",
    )

    # Protocol-Specific Data
    receipt_token_address: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        comment="Receipt/LP token address (e.g., aUSDC for Aave)",
    )
    receipt_token_balance: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(36, 18), nullable=True, comment="Balance of receipt tokens"
    )

    # Metadata
    metadata_json: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, comment="JSON: Additional protocol-specific data"
    )

    # Timestamps
    deposited_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now(), index=True
    )
    withdrawn_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True, index=True
    )
    last_update: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
        comment="Last time position was updated/synced",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    user = relationship("User", back_populates="earn_positions")
    wallet = relationship("Wallet", back_populates="earn_positions")

    # Indexes
    __table_args__ = (
        Index("idx_earn_user_status", "user_id", "status"),
        Index("idx_earn_protocol", "protocol", "status"),
        Index("idx_earn_chain_protocol", "chain", "protocol"),
        Index("idx_earn_deposited", "deposited_at"),
    )

    def __repr__(self) -> str:
        return f"<EarnPosition(id={self.id}, protocol='{self.protocol}', asset='{self.asset}', amount={self.amount_deposited})>"

    @property
    def is_active(self) -> bool:
        """Check if position is active"""
        return self.status == EarnPositionStatus.ACTIVE

    @property
    def unrealized_gain(self) -> Decimal:
        """Calculate unrealized gain"""
        return self.current_value - self.amount_deposited

    @property
    def unrealized_gain_percent(self) -> Decimal:
        """Calculate unrealized gain percentage"""
        if self.amount_deposited == 0:
            return Decimal("0")
        return (self.unrealized_gain / self.amount_deposited) * Decimal("100")

    @property
    def days_active(self) -> int:
        """Calculate days position has been active"""
        if self.status == EarnPositionStatus.WITHDRAWN and self.withdrawn_at:
            delta = self.withdrawn_at - self.deposited_at
        else:
            delta = datetime.utcnow() - self.deposited_at
        return delta.days

    @property
    def daily_earnings(self) -> Decimal:
        """Calculate daily earnings based on current APY"""
        if self.current_apy == 0:
            return Decimal("0")
        return (self.current_value * self.current_apy / Decimal("100")) / Decimal("365")


# ============================================================================
# Earn Transaction Models (Aave V3 / Compound V3)
# ============================================================================


class EarnTransaction(Base):
    """
    Earn transactions (Aave V3 / Compound V3 supply/withdraw)

    Tracks all supply and withdraw operations for money market protocols.
    Mirrors the lending_transactions pattern but for earn operations.
    """

    __tablename__ = "earn_transactions"

    # Primary Key (UUID)
    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, comment="UUID primary key"
    )

    # Foreign Keys
    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="References chat_users.id in production",
    )

    # Protocol Information
    protocol: Mapped[str] = mapped_column(
        SQLEnum(EarnTransactionProtocol),
        nullable=False,
        comment="Protocol: aave or compound",
    )
    chain: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        comment="Blockchain network (e.g., base, ethereum)",
    )
    action_type: Mapped[str] = mapped_column(
        SQLEnum(EarnTransactionAction),
        nullable=False,
        comment="Action: supply or withdraw",
    )

    # Asset Information
    asset_address: Mapped[str] = mapped_column(
        String(42),
        nullable=False,
        comment="Token contract address",
    )
    asset_symbol: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        comment="Token symbol (e.g., USDC, ETH)",
    )
    amount: Mapped[Decimal] = mapped_column(
        Numeric(78, 18),
        nullable=False,
        comment="Amount in token units",
    )
    amount_usd: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(18, 2),
        nullable=True,
        comment="USD value at time of transaction",
    )
    apy_at_time: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(6, 2),
        nullable=True,
        comment="APY when transaction was made",
    )

    # Transaction Details
    transaction_hash: Mapped[str] = mapped_column(
        String(66),
        nullable=False,
        unique=True,
        index=True,
        comment="On-chain transaction hash",
    )
    status: Mapped[str] = mapped_column(
        SQLEnum(EarnTransactionStatus),
        nullable=False,
        default=EarnTransactionStatus.PENDING,
        index=True,
    )
    wallet_address: Mapped[Optional[str]] = mapped_column(
        String(42),
        nullable=True,
        index=True,
        comment="User wallet address",
    )
    pool_address: Mapped[Optional[str]] = mapped_column(
        String(42),
        nullable=True,
        comment="Aave pool or Compound comet address",
    )

    # Metadata
    metadata_json: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="JSON: Additional protocol-specific data",
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )
    confirmed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True, comment="When tx confirmed on-chain"
    )

    # Relationships
    user = relationship("User", back_populates="earn_transactions")

    # Indexes
    __table_args__ = (
        Index("idx_earn_transactions_user_id", "user_id"),
        Index("idx_earn_transactions_tx_hash", "transaction_hash"),
        Index("idx_earn_transactions_status", "status"),
        Index(
            "idx_earn_transactions_user_protocol_action",
            "user_id",
            "protocol",
            "action_type",
        ),
        Index("idx_earn_transactions_wallet", "wallet_address"),
    )

    def __repr__(self) -> str:
        return (
            f"<EarnTransaction(id={self.id}, protocol='{self.protocol}', "
            f"action='{self.action_type}', asset='{self.asset_symbol}', "
            f"amount={self.amount}, status='{self.status}')>"
        )

    @property
    def is_confirmed(self) -> bool:
        """Check if transaction is confirmed"""
        return self.status == EarnTransactionStatus.CONFIRMED

    @property
    def is_supply(self) -> bool:
        """Check if this is a supply transaction"""
        return self.action_type == EarnTransactionAction.SUPPLY

    @property
    def is_withdraw(self) -> bool:
        """Check if this is a withdraw transaction"""
        return self.action_type == EarnTransactionAction.WITHDRAW


# ============================================================================
# Save Models
# ============================================================================


class SaveSchedule(Base):
    """
    Automated savings schedules (Dollar-Cost Averaging)

    Allows users to set up recurring purchases/deposits of crypto assets
    at specified intervals (daily, weekly, monthly).
    """

    __tablename__ = "save_schedules"

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

    # Asset and Chain
    chain: Mapped[str] = mapped_column(
        String(50), nullable=False, comment="Blockchain network"
    )
    asset: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        index=True,
        comment="Asset to purchase/save (e.g., USDC, ETH)",
    )

    # Schedule Configuration
    amount: Mapped[Decimal] = mapped_column(
        Numeric(36, 18), nullable=False, comment="Amount per execution"
    )
    frequency: Mapped[str] = mapped_column(
        SQLEnum(SaveScheduleFrequency),
        nullable=False,
        index=True,
        comment="Execution frequency",
    )

    # Frequency Details
    day_of_week: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        comment="For weekly: 0=Sunday, 1=Monday, ..., 6=Saturday",
    )
    day_of_month: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True, comment="For monthly: 1-31"
    )
    hour: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, comment="Hour of day to execute (0-23, UTC)"
    )

    # Destination
    destination_protocol: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        comment="Where to deposit: 'aave', 'compound', 'wallet' (null = keep in wallet)",
    )

    # Status
    status: Mapped[str] = mapped_column(
        SQLEnum(SaveScheduleStatus),
        nullable=False,
        default=SaveScheduleStatus.ACTIVE,
        index=True,
    )

    # Execution Tracking
    next_execution_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, index=True, comment="Next scheduled execution time"
    )
    last_execution_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True, comment="Last execution time"
    )
    execution_count: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, comment="Number of times executed"
    )

    # Limits
    max_executions: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        comment="Maximum number of executions (null = unlimited)",
    )

    # Totals
    total_saved: Mapped[Decimal] = mapped_column(
        Numeric(36, 18),
        nullable=False,
        default=Decimal("0"),
        comment="Total amount saved through this schedule",
    )
    total_saved_usd: Mapped[Decimal] = mapped_column(
        Numeric(20, 2),
        nullable=False,
        default=Decimal("0"),
        comment="Total USD value saved",
    )

    # Failure Handling
    consecutive_failures: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        comment="Number of consecutive failed executions",
    )
    last_failure_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Notifications
    notify_on_execution: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        comment="Send notification after each execution",
    )
    notify_on_failure: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, comment="Send notification on failure"
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now(), onupdate=func.now()
    )
    paused_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    cancelled_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Relationships
    user = relationship("User", back_populates="save_schedules")
    wallet = relationship("Wallet", back_populates="save_schedules")

    # Indexes
    __table_args__ = (
        Index("idx_save_user_status", "user_id", "status"),
        Index("idx_save_next_execution", "next_execution_at", "status"),
        Index("idx_save_frequency", "frequency"),
    )

    def __repr__(self) -> str:
        return f"<SaveSchedule(id={self.id}, asset='{self.asset}', amount={self.amount}, frequency='{self.frequency}')>"

    @property
    def is_active(self) -> bool:
        """Check if schedule is active"""
        return self.status == SaveScheduleStatus.ACTIVE

    @property
    def is_completed(self) -> bool:
        """Check if schedule has reached max executions"""
        if self.max_executions is None:
            return False
        return self.execution_count >= self.max_executions

    @property
    def frequency_label(self) -> str:
        """Get human-readable frequency"""
        frequency_map = {
            "daily": "Every day",
            "weekly": "Every week",
            "biweekly": "Every 2 weeks",
            "monthly": "Every month",
        }
        return frequency_map.get(self.frequency, self.frequency)

    @property
    def day_of_week_label(self) -> Optional[str]:
        """Get human-readable day of week"""
        if self.day_of_week is None:
            return None
        days = [
            "Sunday",
            "Monday",
            "Tuesday",
            "Wednesday",
            "Thursday",
            "Friday",
            "Saturday",
        ]
        return days[self.day_of_week] if 0 <= self.day_of_week < 7 else None


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

    print("✅ Earn and Save tables created successfully!")
    print("\nTables created:")
    print("- earn_positions")
    print("- earn_transactions")
    print("- save_schedules")
