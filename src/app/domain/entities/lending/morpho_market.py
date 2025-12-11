"""Morpho Market Entity.

Represents a lending market in the Morpho protocol.
"""

from dataclasses import dataclass
from decimal import Decimal


@dataclass
class MorphoMarket:
    """
    Represents a Morpho lending market.

    Morpho is a peer-to-peer lending protocol that optimizes rates
    by matching lenders and borrowers directly.
    """

    id: str
    loan_token: str
    collateral_token: str
    oracle: str
    irm: str  # Interest Rate Model
    lltv: Decimal  # Liquidation Loan-to-Value ratio
    supply_apy: Decimal
    borrow_apy: Decimal
    total_supply: Decimal
    total_borrow: Decimal
    utilization: Decimal

    @property
    def available_liquidity(self) -> Decimal:
        """Calculate available liquidity."""
        return self.total_supply - self.total_borrow
