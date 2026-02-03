"""
Morpho Position Entity.

Represents a user's position in a MetaMorpho vault.
"""

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Any


@dataclass
class MorphoPosition:
    """
    User position entity.

    Represents a user's deposit in a MetaMorpho vault
    with earnings tracking.
    """

    user_address: str
    vault_address: str
    vault_name: str
    asset_symbol: str
    shares: Decimal = Decimal("0")
    assets: Decimal = Decimal("0")  # Current value
    deposited_assets: Decimal = Decimal("0")  # Original deposit
    apy: Decimal = Decimal("0")  # Current vault APY
    deposited_at: datetime | None = None

    @property
    def earnings(self) -> Decimal:
        """Calculate earnings (current - deposited)."""
        return self.assets - self.deposited_assets

    @property
    def earnings_pct(self) -> Decimal:
        """Calculate earnings as percentage."""
        if self.deposited_assets == 0:
            return Decimal("0")
        return self.earnings / self.deposited_assets * 100

    @property
    def is_profitable(self) -> bool:
        """Check if position is profitable."""
        return self.earnings > 0

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "user_address": self.user_address,
            "vault_address": self.vault_address,
            "vault_name": self.vault_name,
            "asset_symbol": self.asset_symbol,
            "shares": str(self.shares),
            "assets": str(self.assets),
            "deposited_assets": str(self.deposited_assets),
            "apy": str(self.apy),
            "deposited_at": self.deposited_at.isoformat()
            if self.deposited_at
            else None,
            "earnings": str(self.earnings),
            "earnings_pct": str(self.earnings_pct),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "MorphoPosition":
        """Deserialize from dictionary."""
        deposited_at = data.get("deposited_at")
        if isinstance(deposited_at, str):
            deposited_at = datetime.fromisoformat(deposited_at)

        return cls(
            user_address=data["user_address"],
            vault_address=data["vault_address"],
            vault_name=data["vault_name"],
            asset_symbol=data.get("asset_symbol", ""),
            shares=Decimal(str(data.get("shares", "0"))),
            assets=Decimal(str(data.get("assets", "0"))),
            deposited_assets=Decimal(str(data.get("deposited_assets", "0"))),
            apy=Decimal(str(data.get("apy", "0"))),
            deposited_at=deposited_at,
        )
