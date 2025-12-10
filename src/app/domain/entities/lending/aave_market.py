"""
Aave Market Entity.

Represents an Aave V3 lending market with its rates and configuration.
"""

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Any


@dataclass
class AaveMarket:
    """
    Aave V3 market entity.

    Represents a lending/borrowing market for an asset
    with current rates, utilization, and configuration.
    """

    asset_address: str
    symbol: str
    name: str
    chain: str = "ethereum"
    decimals: int = 18

    # Supply metrics
    supply_apy: Decimal = Decimal("0")
    total_supplied: Decimal = Decimal("0")
    total_supplied_usd: Decimal = Decimal("0")
    supply_cap: Decimal = Decimal("0")

    # Borrow metrics
    borrow_apy_variable: Decimal = Decimal("0")
    borrow_apy_stable: Decimal = Decimal("0")
    total_borrowed: Decimal = Decimal("0")
    total_borrowed_usd: Decimal = Decimal("0")
    borrow_cap: Decimal = Decimal("0")

    # Utilization
    utilization_rate: Decimal = Decimal("0")  # Percentage
    liquidity_available: Decimal = Decimal("0")

    # Collateral parameters
    ltv: Decimal = Decimal("0")  # Loan-to-value ratio (max collateral)
    liquidation_threshold: Decimal = Decimal("0")
    liquidation_bonus: Decimal = Decimal("0")

    # Market status
    is_active: bool = True
    is_frozen: bool = False
    is_paused: bool = False
    can_use_as_collateral: bool = True
    can_borrow: bool = True

    # E-mode
    e_mode_category: int = 0
    e_mode_label: str | None = None

    # Price
    price_usd: Decimal = Decimal("0")

    # Timestamps
    updated_at: datetime | None = None

    @property
    def available_liquidity_usd(self) -> Decimal:
        """Get available liquidity in USD."""
        return self.liquidity_available * self.price_usd

    @property
    def is_borrowable(self) -> bool:
        """Check if asset can be borrowed."""
        return self.can_borrow and not self.is_frozen and not self.is_paused

    @property
    def is_suppliable(self) -> bool:
        """Check if asset can be supplied."""
        return self.is_active and not self.is_paused

    @property
    def supply_cap_remaining(self) -> Decimal:
        """Get remaining supply capacity."""
        if self.supply_cap == 0:
            return Decimal("999999999")  # No cap
        return max(Decimal("0"), self.supply_cap - self.total_supplied)

    @property
    def borrow_cap_remaining(self) -> Decimal:
        """Get remaining borrow capacity."""
        if self.borrow_cap == 0:
            return Decimal("999999999")  # No cap
        return max(Decimal("0"), self.borrow_cap - self.total_borrowed)

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "asset_address": self.asset_address,
            "symbol": self.symbol,
            "name": self.name,
            "chain": self.chain,
            "decimals": self.decimals,
            "supply_apy": str(self.supply_apy),
            "total_supplied": str(self.total_supplied),
            "total_supplied_usd": str(self.total_supplied_usd),
            "supply_cap": str(self.supply_cap),
            "borrow_apy_variable": str(self.borrow_apy_variable),
            "borrow_apy_stable": str(self.borrow_apy_stable),
            "total_borrowed": str(self.total_borrowed),
            "total_borrowed_usd": str(self.total_borrowed_usd),
            "borrow_cap": str(self.borrow_cap),
            "utilization_rate": str(self.utilization_rate),
            "liquidity_available": str(self.liquidity_available),
            "ltv": str(self.ltv),
            "liquidation_threshold": str(self.liquidation_threshold),
            "liquidation_bonus": str(self.liquidation_bonus),
            "is_active": self.is_active,
            "is_frozen": self.is_frozen,
            "is_paused": self.is_paused,
            "can_use_as_collateral": self.can_use_as_collateral,
            "can_borrow": self.can_borrow,
            "e_mode_category": self.e_mode_category,
            "e_mode_label": self.e_mode_label,
            "price_usd": str(self.price_usd),
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "AaveMarket":
        """Deserialize from dictionary."""
        updated_at = data.get("updated_at")
        if isinstance(updated_at, str):
            updated_at = datetime.fromisoformat(updated_at)

        return cls(
            asset_address=data["asset_address"],
            symbol=data["symbol"],
            name=data.get("name", data["symbol"]),
            chain=data.get("chain", "ethereum"),
            decimals=data.get("decimals", 18),
            supply_apy=Decimal(str(data.get("supply_apy", "0"))),
            total_supplied=Decimal(str(data.get("total_supplied", "0"))),
            total_supplied_usd=Decimal(str(data.get("total_supplied_usd", "0"))),
            supply_cap=Decimal(str(data.get("supply_cap", "0"))),
            borrow_apy_variable=Decimal(str(data.get("borrow_apy_variable", "0"))),
            borrow_apy_stable=Decimal(str(data.get("borrow_apy_stable", "0"))),
            total_borrowed=Decimal(str(data.get("total_borrowed", "0"))),
            total_borrowed_usd=Decimal(str(data.get("total_borrowed_usd", "0"))),
            borrow_cap=Decimal(str(data.get("borrow_cap", "0"))),
            utilization_rate=Decimal(str(data.get("utilization_rate", "0"))),
            liquidity_available=Decimal(str(data.get("liquidity_available", "0"))),
            ltv=Decimal(str(data.get("ltv", "0"))),
            liquidation_threshold=Decimal(str(data.get("liquidation_threshold", "0"))),
            liquidation_bonus=Decimal(str(data.get("liquidation_bonus", "0"))),
            is_active=data.get("is_active", True),
            is_frozen=data.get("is_frozen", False),
            is_paused=data.get("is_paused", False),
            can_use_as_collateral=data.get("can_use_as_collateral", True),
            can_borrow=data.get("can_borrow", True),
            e_mode_category=data.get("e_mode_category", 0),
            e_mode_label=data.get("e_mode_label"),
            price_usd=Decimal(str(data.get("price_usd", "0"))),
            updated_at=updated_at,
        )
