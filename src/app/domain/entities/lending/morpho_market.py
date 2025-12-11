"""
Morpho Market Entity.

Represents a Morpho Blue market with its parameters and rates.
"""

from dataclasses import dataclass
from decimal import Decimal
from typing import Any


@dataclass
class MorphoMarket:
    """
    Morpho Blue market entity.

    Represents a single lending market with specific
    collateral and loan asset pair.
    """

    market_id: str
    collateral_asset: str  # Symbol
    collateral_address: str
    loan_asset: str  # Symbol
    loan_address: str
    lltv: Decimal  # Liquidation loan-to-value (e.g., 0.86)
    oracle: str | None
    irm_address: str | None  # Interest Rate Model
    total_supply: Decimal = Decimal("0")
    total_borrow: Decimal = Decimal("0")
    supply_apy: Decimal = Decimal("0")
    borrow_apy: Decimal = Decimal("0")

    @property
    def utilization(self) -> Decimal:
        """Calculate utilization rate."""
        if self.total_supply == 0:
            return Decimal("0")
        return self.total_borrow / self.total_supply

    @property
    def available_liquidity(self) -> Decimal:
        """Calculate available liquidity."""
        return self.total_supply - self.total_borrow

    @property
    def lltv_pct(self) -> Decimal:
        """Get LLTV as percentage."""
        return self.lltv * 100

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "market_id": self.market_id,
            "collateral_asset": self.collateral_asset,
            "collateral_address": self.collateral_address,
            "loan_asset": self.loan_asset,
            "loan_address": self.loan_address,
            "lltv": str(self.lltv),
            "oracle": self.oracle,
            "irm_address": self.irm_address,
            "total_supply": str(self.total_supply),
            "total_borrow": str(self.total_borrow),
            "supply_apy": str(self.supply_apy),
            "borrow_apy": str(self.borrow_apy),
            "utilization": str(self.utilization),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "MorphoMarket":
        """Deserialize from dictionary."""
        return cls(
            market_id=data["market_id"],
            collateral_asset=data["collateral_asset"],
            collateral_address=data.get("collateral_address", ""),
            loan_asset=data["loan_asset"],
            loan_address=data.get("loan_address", ""),
            lltv=Decimal(str(data.get("lltv", "0"))),
            oracle=data.get("oracle"),
            irm_address=data.get("irm_address"),
            total_supply=Decimal(str(data.get("total_supply", "0"))),
            total_borrow=Decimal(str(data.get("total_borrow", "0"))),
            supply_apy=Decimal(str(data.get("supply_apy", "0"))),
            borrow_apy=Decimal(str(data.get("borrow_apy", "0"))),
        )
