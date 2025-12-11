"""
Market Allocation Value Object.

Immutable representation of vault allocation to a market.
"""

from dataclasses import dataclass
from decimal import Decimal
from typing import Any


@dataclass(frozen=True)
class MarketAllocation:
    """
    Market allocation value object.

    Represents how a vault allocates funds to a specific market.
    """

    market_id: str
    collateral_asset: str  # Symbol
    loan_asset: str  # Symbol
    allocation_percentage: Decimal  # Percentage of vault allocated
    lltv: Decimal  # Liquidation LTV
    supply_apy: Decimal  # APY from this market

    @property
    def allocation_pct_display(self) -> Decimal:
        """Get allocation as display percentage."""
        return self.allocation_percentage * 100

    @property
    def lltv_pct(self) -> Decimal:
        """Get LLTV as percentage."""
        return self.lltv * 100

    @property
    def is_high_lltv(self) -> bool:
        """Check if LLTV is considered high (>85%)."""
        return self.lltv > Decimal("0.85")

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "market_id": self.market_id,
            "collateral_asset": self.collateral_asset,
            "loan_asset": self.loan_asset,
            "allocation_percentage": str(self.allocation_percentage),
            "lltv": str(self.lltv),
            "supply_apy": str(self.supply_apy),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "MarketAllocation":
        """Deserialize from dictionary."""
        return cls(
            market_id=data["market_id"],
            collateral_asset=data["collateral_asset"],
            loan_asset=data.get("loan_asset", ""),
            allocation_percentage=Decimal(str(data.get("allocation_percentage", "0"))),
            lltv=Decimal(str(data.get("lltv", "0"))),
            supply_apy=Decimal(str(data.get("supply_apy", "0"))),
        )
