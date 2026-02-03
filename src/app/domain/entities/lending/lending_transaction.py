"""
Domain entity for lending transactions.

Tracks all lending operations with status and health factor impact.
"""

from dataclasses import dataclass
from decimal import Decimal
from datetime import datetime
from typing import Optional, Dict, Any
from uuid import UUID

__slots__ = (
    "id",
    "user_id",
    "protocol",
    "chain",
    "action_type",
    "asset_address",
    "asset_symbol",
    "amount",
    "transaction_hash",
    "status",
    "health_factor_before",
    "health_factor_after",
    "metadata",
    "created_at",
    "confirmed_at",
)


@dataclass(slots=True)
class LendingTransaction:
    """
    Lending transaction entity.

    Represents a single lending operation (supply, withdraw, borrow, repay, liquidate).
    """

    id: UUID
    user_id: UUID
    protocol: str  # 'aave' | 'morpho'
    chain: str
    action_type: str  # 'supply' | 'withdraw' | 'borrow' | 'repay' | 'liquidate'
    asset_address: str
    asset_symbol: str
    amount: Decimal
    transaction_hash: str
    status: str  # 'pending' | 'confirmed' | 'failed'
    health_factor_before: Optional[Decimal]
    health_factor_after: Optional[Decimal]
    metadata: Optional[Dict[str, Any]]
    created_at: datetime
    confirmed_at: Optional[datetime]

    def is_pending(self) -> bool:
        """Check if transaction is still pending."""
        return self.status == "pending"

    def is_confirmed(self) -> bool:
        """Check if transaction has been confirmed on-chain."""
        return self.status == "confirmed"

    def is_failed(self) -> bool:
        """Check if transaction failed."""
        return self.status == "failed"

    def is_supply_action(self) -> bool:
        """Check if this is a supply action."""
        return self.action_type == "supply"

    def is_borrow_action(self) -> bool:
        """Check if this is a borrow action."""
        return self.action_type == "borrow"

    def is_withdraw_action(self) -> bool:
        """Check if this is a withdraw action."""
        return self.action_type == "withdraw"

    def is_repay_action(self) -> bool:
        """Check if this is a repay action."""
        return self.action_type == "repay"

    def is_liquidate_action(self) -> bool:
        """Check if this is a liquidation action."""
        return self.action_type == "liquidate"

    def health_factor_improved(self) -> bool:
        """
        Check if health factor improved after transaction.

        Returns False if health factors are not tracked (supply-only positions).
        """
        if (
            self.health_factor_before is None
            or self.health_factor_after is None
        ):
            return False
        return self.health_factor_after > self.health_factor_before

    def health_factor_worsened(self) -> bool:
        """
        Check if health factor worsened after transaction.

        Returns False if health factors are not tracked.
        """
        if (
            self.health_factor_before is None
            or self.health_factor_after is None
        ):
            return False
        return self.health_factor_after < self.health_factor_before
