"""
Domain entities for lending positions.

Represents supply and borrow positions across Aave and Morpho protocols.
"""

from dataclasses import dataclass
from decimal import Decimal
from datetime import datetime
from typing import Optional
from uuid import UUID

__slots__ = (
    "id",
    "user_id",
    "protocol",
    "chain",
    "position_type",
    "asset_address",
    "asset_symbol",
    "amount",
    "amount_usd",
    "health_factor",
    "apy",
    "status",
    "created_at",
    "updated_at",
)


@dataclass(slots=True)
class LendingPosition:
    """
    Base lending position entity.

    Represents a user's lending position (supply or borrow) on a protocol.
    """

    id: UUID
    user_id: UUID
    protocol: str  # 'aave' | 'morpho'
    chain: str  # 'ethereum', 'base', etc.
    position_type: str  # 'supply' | 'borrow'
    asset_address: str
    asset_symbol: str
    amount: Decimal  # Token amount (up to 78 decimals for Web3)
    amount_usd: Decimal  # USD value (2 decimal places)
    health_factor: Optional[Decimal]  # None for supply-only positions
    apy: Decimal  # Annual percentage yield
    status: str  # 'active' | 'closed' | 'liquidated'
    created_at: datetime
    updated_at: datetime

    def is_active(self) -> bool:
        """Check if position is currently active."""
        return self.status == "active"

    def is_supply(self) -> bool:
        """Check if this is a supply position."""
        return self.position_type == "supply"

    def is_borrow(self) -> bool:
        """Check if this is a borrow position."""
        return self.position_type == "borrow"

    def is_healthy(self) -> bool:
        """
        Check if position is healthy.

        For borrow positions, healthy means health_factor >= 1.5.
        Supply-only positions are always healthy.
        """
        if self.health_factor is None:
            return True  # Supply-only position
        return self.health_factor >= Decimal("1.5")

    def is_at_risk(self) -> bool:
        """
        Check if position is at risk of liquidation.

        At risk means health_factor < 1.5 but >= 1.2.
        """
        if self.health_factor is None:
            return False
        return Decimal("1.2") <= self.health_factor < Decimal("1.5")

    def is_critical(self) -> bool:
        """
        Check if position is in critical state.

        Critical means health_factor < 1.2 (near liquidation).
        """
        if self.health_factor is None:
            return False
        return self.health_factor < Decimal("1.2")


@dataclass(slots=True)
class SupplyPosition:
    """
    Supply position entity (subset of LendingPosition for supply operations).

    Used for CQRS write operations.
    """

    id: UUID
    position_id: UUID
    user_id: UUID
    protocol: str  # 'aave' | 'morpho'
    chain: str
    asset_address: str
    asset_symbol: str
    amount: Decimal
    apy: Decimal
    transaction_hash: str
    block_number: int
    gas_used: Decimal
    created_at: datetime


@dataclass(slots=True)
class BorrowPosition:
    """
    Borrow position entity (subset of LendingPosition for borrow operations).

    Used for CQRS write operations. Aave only.
    """

    id: UUID
    position_id: UUID
    user_id: UUID
    protocol: str  # 'aave'
    chain: str
    asset_address: str
    asset_symbol: str
    amount: Decimal
    interest_rate: Decimal
    variable_rate: bool
    health_factor_at_borrow: Decimal
    transaction_hash: str
    block_number: int
    created_at: datetime

    def is_variable_rate(self) -> bool:
        """Check if borrow uses variable interest rate."""
        return self.variable_rate

    def is_stable_rate(self) -> bool:
        """Check if borrow uses stable interest rate."""
        return not self.variable_rate
