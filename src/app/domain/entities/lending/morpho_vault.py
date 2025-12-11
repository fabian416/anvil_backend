"""Morpho Vault Entity.

Represents a Morpho Blue vault for optimized lending.
"""

from dataclasses import dataclass
from decimal import Decimal


@dataclass
class MorphoVault:
    """
    Represents a Morpho Blue vault.

    Vaults aggregate liquidity and optimize allocation across multiple markets.
    """

    address: str
    name: str
    symbol: str
    asset: str  # Underlying asset address
    total_assets: Decimal
    total_shares: Decimal
    apy: Decimal
    curator: str

    @property
    def share_price(self) -> Decimal:
        """Calculate the price per share."""
        if self.total_shares == 0:
            return Decimal("1")
        return self.total_assets / self.total_shares
