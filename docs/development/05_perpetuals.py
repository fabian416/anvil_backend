"""
Anvil Platform - SQLAlchemy Models
Section 5: Perpetuals Models (Hyperliquid)

These models handle perpetual futures trading on Hyperliquid.
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

class PositionSide(str, enum.Enum):
    """Position side"""
    LONG = "long"
    SHORT = "short"


class PositionStatus(str, enum.Enum):
    """Position status"""
    OPEN = "open"
    CLOSED = "closed"
    LIQUIDATED = "liquidated"


# ============================================================================
# Perpetuals Models
# ============================================================================

class HyperliquidPosition(Base):
    """
    Perpetual futures positions on Hyperliquid
    
    Tracks leveraged trading positions including entry/exit prices,
    PnL, funding payments, and liquidation parameters.
    """
    
    __tablename__ = "hyperliquid_positions"
    
    # Primary Key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    
    # Foreign Keys
    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    wallet_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("wallets.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # Symbol Information
    symbol: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
        comment="Trading pair symbol (e.g., 'ETH-USD', 'BTC-USD')"
    )
    base_asset: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        comment="Base asset (e.g., 'ETH', 'BTC')"
    )
    quote_asset: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="USD",
        comment="Quote asset (typically 'USD')"
    )
    
    # Position Details
    side: Mapped[str] = mapped_column(
        SQLEnum(PositionSide),
        nullable=False,
        index=True,
        comment="Position direction: long or short"
    )
    leverage: Mapped[Decimal] = mapped_column(
        Numeric(8, 2),
        nullable=False,
        comment="Leverage multiplier (e.g., 5.0 for 5x)"
    )
    size: Mapped[Decimal] = mapped_column(
        Numeric(36, 18),
        nullable=False,
        comment="Position size in base asset"
    )
    
    # Pricing
    entry_price: Mapped[Decimal] = mapped_column(
        Numeric(20, 8),
        nullable=False,
        comment="Average entry price"
    )
    exit_price: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(20, 8),
        nullable=True,
        comment="Exit price (when closed)"
    )
    mark_price: Mapped[Decimal] = mapped_column(
        Numeric(20, 8),
        nullable=False,
        default=Decimal("0"),
        comment="Current mark price (updated periodically)"
    )
    liquidation_price: Mapped[Decimal] = mapped_column(
        Numeric(20, 8),
        nullable=False,
        comment="Liquidation price"
    )
    
    # Margin
    margin: Mapped[Decimal] = mapped_column(
        Numeric(20, 8),
        nullable=False,
        comment="Initial margin (collateral) in USDC"
    )
    maintenance_margin: Mapped[Decimal] = mapped_column(
        Numeric(20, 8),
        nullable=False,
        default=Decimal("0"),
        comment="Minimum margin required to maintain position"
    )
    
    # PnL Tracking
    unrealized_pnl: Mapped[Decimal] = mapped_column(
        Numeric(20, 8),
        nullable=False,
        default=Decimal("0"),
        comment="Current unrealized profit/loss"
    )
    realized_pnl: Mapped[Decimal] = mapped_column(
        Numeric(20, 8),
        nullable=False,
        default=Decimal("0"),
        comment="Realized profit/loss (after close)"
    )
    
    # Funding
    funding_rate: Mapped[Decimal] = mapped_column(
        Numeric(10, 8),
        nullable=False,
        default=Decimal("0"),
        comment="Current funding rate (%)"
    )
    total_funding_paid: Mapped[Decimal] = mapped_column(
        Numeric(20, 8),
        nullable=False,
        default=Decimal("0"),
        comment="Total funding fees paid (negative = received)"
    )
    last_funding_payment: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(20, 8),
        nullable=True,
        comment="Last funding payment amount"
    )
    last_funding_time: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        nullable=True,
        comment="Last funding payment timestamp"
    )
    
    # Status
    status: Mapped[str] = mapped_column(
        SQLEnum(PositionStatus),
        nullable=False,
        default=PositionStatus.OPEN,
        index=True
    )
    
    # Hyperliquid IDs
    hyperliquid_order_id: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        unique=True,
        index=True,
        comment="Hyperliquid's internal order ID"
    )
    hyperliquid_position_id: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        index=True,
        comment="Hyperliquid's internal position ID"
    )
    
    # Risk Metrics
    liquidation_distance_percent: Mapped[Decimal] = mapped_column(
        Numeric(8, 4),
        nullable=False,
        default=Decimal("0"),
        comment="Distance to liquidation as percentage"
    )
    
    # Metadata
    metadata_json: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="JSON: Additional Hyperliquid data"
    )
    
    # Timestamps
    opened_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        server_default=func.now(),
        index=True
    )
    closed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        nullable=True,
        index=True
    )
    liquidated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        nullable=True
    )
    last_update: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
        comment="Last time position data was synced"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        server_default=func.now(),
        onupdate=func.now()
    )
    
    # Relationships
    user = relationship("User", back_populates="hyperliquid_positions")
    wallet = relationship("Wallet", back_populates="hyperliquid_positions")
    orders = relationship("HyperliquidOrder", back_populates="position", lazy="select")
    
    # Indexes
    __table_args__ = (
        Index("idx_perp_user_status", "user_id", "status"),
        Index("idx_perp_symbol_status", "symbol", "status"),
        Index("idx_perp_opened", "opened_at"),
        Index("idx_perp_side", "side"),
    )
    
    def __repr__(self) -> str:
        return f"<HyperliquidPosition(id={self.id}, symbol='{self.symbol}', side='{self.side}', size={self.size}, pnl={self.unrealized_pnl})>"
    
    @property
    def is_open(self) -> bool:
        """Check if position is open"""
        return self.status == PositionStatus.OPEN
    
    @property
    def is_long(self) -> bool:
        """Check if position is long"""
        return self.side == PositionSide.LONG
    
    @property
    def is_short(self) -> bool:
        """Check if position is short"""
        return self.side == PositionSide.SHORT
    
    @property
    def notional_value(self) -> Decimal:
        """Calculate notional position value"""
        return self.size * self.mark_price
    
    @property
    def unrealized_pnl_percent(self) -> Decimal:
        """Calculate unrealized PnL as percentage"""
        if self.margin == 0:
            return Decimal("0")
        return (self.unrealized_pnl / self.margin) * Decimal("100")
    
    @property
    def realized_pnl_percent(self) -> Decimal:
        """Calculate realized PnL as percentage"""
        if self.margin == 0:
            return Decimal("0")
        return (self.realized_pnl / self.margin) * Decimal("100")
    
    def calculate_unrealized_pnl(self) -> Decimal:
        """Calculate current unrealized PnL"""
        if self.is_long:
            return (self.mark_price - self.entry_price) * self.size
        else:  # short
            return (self.entry_price - self.mark_price) * self.size


class HyperliquidOrder(Base):
    """
    Individual orders for Hyperliquid positions
    
    Tracks order history including fills, cancellations, and modifications.
    """
    
    __tablename__ = "hyperliquid_orders"
    
    # Primary Key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    
    # Foreign Keys
    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    position_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("hyperliquid_positions.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    
    # Order Information
    hyperliquid_order_id: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        unique=True,
        index=True
    )
    symbol: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True
    )
    
    # Order Details
    order_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        comment="'market', 'limit', 'stop_market', 'stop_limit'"
    )
    side: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
        comment="'buy' or 'sell'"
    )
    size: Mapped[Decimal] = mapped_column(
        Numeric(36, 18),
        nullable=False,
        comment="Order size"
    )
    price: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(20, 8),
        nullable=True,
        comment="Limit price (null for market orders)"
    )
    
    # Fill Information
    filled_size: Mapped[Decimal] = mapped_column(
        Numeric(36, 18),
        nullable=False,
        default=Decimal("0"),
        comment="Amount filled"
    )
    average_fill_price: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(20, 8),
        nullable=True,
        comment="Average price of fills"
    )
    
    # Status
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        index=True,
        comment="'open', 'filled', 'cancelled', 'rejected'"
    )
    
    # Timestamps
    placed_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        server_default=func.now(),
        index=True
    )
    filled_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        nullable=True
    )
    cancelled_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        server_default=func.now()
    )
    
    # Relationships
    position = relationship("HyperliquidPosition", back_populates="orders")
    
    # Indexes
    __table_args__ = (
        Index("idx_order_user_status", "user_id", "status"),
        Index("idx_order_symbol", "symbol"),
        Index("idx_order_placed", "placed_at"),
    )
    
    def __repr__(self) -> str:
        return f"<HyperliquidOrder(id={self.id}, symbol='{self.symbol}', side='{self.side}', size={self.size}, status='{self.status}')>"
    
    @property
    def is_filled(self) -> bool:
        """Check if order is completely filled"""
        return self.status == "filled"
    
    @property
    def is_open(self) -> bool:
        """Check if order is still open"""
        return self.status == "open"
    
    @property
    def fill_percent(self) -> Decimal:
        """Calculate fill percentage"""
        if self.size == 0:
            return Decimal("0")
        return (self.filled_size / self.size) * Decimal("100")


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
    
    print("✅ Perpetuals tables created successfully!")
    print("\nTables created:")
    print("- hyperliquid_positions")
    print("- hyperliquid_orders")
