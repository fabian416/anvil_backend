"""Morpho Position Entity.

Represents a user's position in a Morpho market.
"""

from dataclasses import dataclass
from decimal import Decimal


@dataclass
class MorphoPosition:
    """
    Represents a user's position in a Morpho market.

    Tracks both supply and borrow positions for a user in a specific market.
    """

    market_id: str
    user_address: str
    supply_shares: Decimal
    borrow_shares: Decimal
    collateral: Decimal

    @property
    def is_borrowing(self) -> bool:
        """Check if user has an active borrow position."""
        return self.borrow_shares > 0

    @property
    def is_supplying(self) -> bool:
        """Check if user has an active supply position."""
        return self.supply_shares > 0
