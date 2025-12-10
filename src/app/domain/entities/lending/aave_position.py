"""
Aave Position Entity.

Represents a user's lending/borrowing position on Aave V3.
"""

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import Any


@dataclass
class AaveSupplyPosition:
    """
    Individual supply position for an asset.
    """

    asset_address: str
    symbol: str
    balance: Decimal
    balance_usd: Decimal
    apy: Decimal
    is_collateral: bool = True


@dataclass
class AaveBorrowPosition:
    """
    Individual borrow position for an asset.
    """

    asset_address: str
    symbol: str
    balance: Decimal
    balance_usd: Decimal
    apy: Decimal
    borrow_type: str = "variable"  # "variable" or "stable"


@dataclass
class AavePosition:
    """
    Complete user position entity.

    Represents a user's aggregated position on Aave V3
    including supplies, borrows, and health metrics.
    """

    user_address: str
    chain: str = "ethereum"

    # Aggregated values
    total_collateral_usd: Decimal = Decimal("0")
    total_debt_usd: Decimal = Decimal("0")
    available_borrow_usd: Decimal = Decimal("0")
    net_worth_usd: Decimal = Decimal("0")

    # Health metrics
    health_factor: Decimal = Decimal("inf")
    current_ltv: Decimal = Decimal("0")
    max_ltv: Decimal = Decimal("0")

    # E-mode
    e_mode_category: int = 0
    e_mode_label: str | None = None

    # Positions
    supplies: list[AaveSupplyPosition] = field(default_factory=list)
    borrows: list[AaveBorrowPosition] = field(default_factory=list)

    # Timestamps
    updated_at: datetime | None = None

    @property
    def is_healthy(self) -> bool:
        """Check if position is healthy (HF > 1)."""
        return self.health_factor > 1

    @property
    def is_at_risk(self) -> bool:
        """Check if position is at risk (1 < HF < 1.5)."""
        return Decimal("1") < self.health_factor < Decimal("1.5")

    @property
    def is_liquidatable(self) -> bool:
        """Check if position can be liquidated (HF < 1)."""
        return self.health_factor < 1

    @property
    def total_supply_apy(self) -> Decimal:
        """Calculate weighted average supply APY."""
        if self.total_collateral_usd == 0:
            return Decimal("0")
        weighted_sum = sum(
            s.apy * s.balance_usd for s in self.supplies
        )
        return weighted_sum / self.total_collateral_usd

    @property
    def total_borrow_apy(self) -> Decimal:
        """Calculate weighted average borrow APY."""
        if self.total_debt_usd == 0:
            return Decimal("0")
        weighted_sum = sum(
            b.apy * b.balance_usd for b in self.borrows
        )
        return weighted_sum / self.total_debt_usd

    @property
    def net_apy(self) -> Decimal:
        """Calculate net APY (supply earnings - borrow costs)."""
        if self.net_worth_usd == 0:
            return Decimal("0")
        supply_earnings = self.total_supply_apy * self.total_collateral_usd
        borrow_costs = self.total_borrow_apy * self.total_debt_usd
        return (supply_earnings - borrow_costs) / self.net_worth_usd

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "user_address": self.user_address,
            "chain": self.chain,
            "total_collateral_usd": str(self.total_collateral_usd),
            "total_debt_usd": str(self.total_debt_usd),
            "available_borrow_usd": str(self.available_borrow_usd),
            "net_worth_usd": str(self.net_worth_usd),
            "health_factor": str(self.health_factor) if self.health_factor != Decimal("inf") else "∞",
            "current_ltv": str(self.current_ltv),
            "max_ltv": str(self.max_ltv),
            "e_mode_category": self.e_mode_category,
            "e_mode_label": self.e_mode_label,
            "is_healthy": self.is_healthy,
            "is_at_risk": self.is_at_risk,
            "is_liquidatable": self.is_liquidatable,
            "supplies": [
                {
                    "asset_address": s.asset_address,
                    "symbol": s.symbol,
                    "balance": str(s.balance),
                    "balance_usd": str(s.balance_usd),
                    "apy": str(s.apy),
                    "is_collateral": s.is_collateral,
                }
                for s in self.supplies
            ],
            "borrows": [
                {
                    "asset_address": b.asset_address,
                    "symbol": b.symbol,
                    "balance": str(b.balance),
                    "balance_usd": str(b.balance_usd),
                    "apy": str(b.apy),
                    "borrow_type": b.borrow_type,
                }
                for b in self.borrows
            ],
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "AavePosition":
        """Deserialize from dictionary."""
        updated_at = data.get("updated_at")
        if isinstance(updated_at, str):
            updated_at = datetime.fromisoformat(updated_at)

        supplies = [
            AaveSupplyPosition(
                asset_address=s["asset_address"],
                symbol=s["symbol"],
                balance=Decimal(str(s.get("balance", "0"))),
                balance_usd=Decimal(str(s.get("balance_usd", "0"))),
                apy=Decimal(str(s.get("apy", "0"))),
                is_collateral=s.get("is_collateral", True),
            )
            for s in data.get("supplies", [])
        ]

        borrows = [
            AaveBorrowPosition(
                asset_address=b["asset_address"],
                symbol=b["symbol"],
                balance=Decimal(str(b.get("balance", "0"))),
                balance_usd=Decimal(str(b.get("balance_usd", "0"))),
                apy=Decimal(str(b.get("apy", "0"))),
                borrow_type=b.get("borrow_type", "variable"),
            )
            for b in data.get("borrows", [])
        ]

        # Handle infinity health factor
        hf_str = data.get("health_factor", "inf")
        if hf_str in ("∞", "inf", "Infinity"):
            health_factor = Decimal("inf")
        else:
            health_factor = Decimal(str(hf_str))

        return cls(
            user_address=data["user_address"],
            chain=data.get("chain", "ethereum"),
            total_collateral_usd=Decimal(str(data.get("total_collateral_usd", "0"))),
            total_debt_usd=Decimal(str(data.get("total_debt_usd", "0"))),
            available_borrow_usd=Decimal(str(data.get("available_borrow_usd", "0"))),
            net_worth_usd=Decimal(str(data.get("net_worth_usd", "0"))),
            health_factor=health_factor,
            current_ltv=Decimal(str(data.get("current_ltv", "0"))),
            max_ltv=Decimal(str(data.get("max_ltv", "0"))),
            e_mode_category=data.get("e_mode_category", 0),
            e_mode_label=data.get("e_mode_label"),
            supplies=supplies,
            borrows=borrows,
            updated_at=updated_at,
        )
