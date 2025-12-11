"""
Vault APY Value Object.

Immutable representation of vault APY breakdown.
"""

from dataclasses import dataclass
from decimal import Decimal
from typing import Any


@dataclass(frozen=True)
class VaultAPY:
    """
    Vault APY value object.

    Contains APY breakdown with historical averages.
    """

    vault_address: str
    base_apy: Decimal  # From lending
    supply_apy: Decimal  # From supply rates
    reward_apy: Decimal  # From rewards/incentives
    fee_percentage: Decimal  # Performance fee

    # Historical data
    apy_7d_avg: Decimal = Decimal("0")
    apy_30d_avg: Decimal = Decimal("0")

    @property
    def total_apy(self) -> Decimal:
        """Calculate total gross APY."""
        return self.base_apy + self.supply_apy + self.reward_apy

    @property
    def effective_apy(self) -> Decimal:
        """Calculate effective APY after fees."""
        return self.total_apy * (1 - self.fee_percentage)

    @property
    def total_apy_pct(self) -> Decimal:
        """Get total APY as percentage."""
        return self.total_apy * 100

    @property
    def effective_apy_pct(self) -> Decimal:
        """Get effective APY as percentage."""
        return self.effective_apy * 100

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "vault_address": self.vault_address,
            "base_apy": str(self.base_apy),
            "supply_apy": str(self.supply_apy),
            "reward_apy": str(self.reward_apy),
            "fee_percentage": str(self.fee_percentage),
            "total_apy": str(self.total_apy),
            "effective_apy": str(self.effective_apy),
            "apy_7d_avg": str(self.apy_7d_avg),
            "apy_30d_avg": str(self.apy_30d_avg),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "VaultAPY":
        """Deserialize from dictionary."""
        return cls(
            vault_address=data["vault_address"],
            base_apy=Decimal(str(data.get("base_apy", "0"))),
            supply_apy=Decimal(str(data.get("supply_apy", "0"))),
            reward_apy=Decimal(str(data.get("reward_apy", "0"))),
            fee_percentage=Decimal(str(data.get("fee_percentage", "0"))),
            apy_7d_avg=Decimal(str(data.get("apy_7d_avg", "0"))),
            apy_30d_avg=Decimal(str(data.get("apy_30d_avg", "0"))),
        )
