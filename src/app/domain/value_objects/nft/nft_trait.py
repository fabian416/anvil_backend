"""
NFT Trait Value Object.

Immutable representation of an NFT attribute/trait.
"""

from dataclasses import dataclass
from decimal import Decimal
from typing import Any


@dataclass(frozen=True)
class NFTTrait:
    """
    NFT trait value object.

    Represents an attribute of an NFT.
    """

    trait_type: str
    value: str
    rarity_pct: Decimal | None = None  # Percentage of collection

    @property
    def is_rare(self) -> bool:
        """Check if trait is rare (<5% of collection)."""
        if self.rarity_pct:
            return self.rarity_pct < Decimal("5")
        return False

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "trait_type": self.trait_type,
            "value": self.value,
            "rarity_pct": str(self.rarity_pct) if self.rarity_pct else None,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "NFTTrait":
        """Deserialize from dictionary."""
        rarity = data.get("rarity_pct")
        return cls(
            trait_type=data.get("trait_type", ""),
            value=str(data.get("value", "")),
            rarity_pct=Decimal(str(rarity)) if rarity else None,
        )
