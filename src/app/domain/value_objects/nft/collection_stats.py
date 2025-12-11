"""
Collection Stats Value Object.

Immutable representation of NFT collection market statistics.
"""

from dataclasses import dataclass
from decimal import Decimal
from typing import Any


@dataclass(frozen=True)
class CollectionStats:
    """
    Collection statistics value object.

    Contains market data for an NFT collection.
    """

    slug: str
    floor_price: Decimal  # In ETH
    floor_price_usd: Decimal
    total_volume: Decimal
    total_sales: int
    num_owners: int
    average_price: Decimal
    market_cap: Decimal
    one_day_volume: Decimal
    one_day_change: Decimal  # Percentage
    seven_day_volume: Decimal
    seven_day_change: Decimal  # Percentage

    @property
    def is_trending(self) -> bool:
        """Check if collection is trending (positive 7d change)."""
        return self.seven_day_change > 0

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "slug": self.slug,
            "floor_price": str(self.floor_price),
            "floor_price_usd": str(self.floor_price_usd),
            "total_volume": str(self.total_volume),
            "total_sales": self.total_sales,
            "num_owners": self.num_owners,
            "average_price": str(self.average_price),
            "market_cap": str(self.market_cap),
            "one_day_volume": str(self.one_day_volume),
            "one_day_change": str(self.one_day_change),
            "seven_day_volume": str(self.seven_day_volume),
            "seven_day_change": str(self.seven_day_change),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "CollectionStats":
        """Deserialize from dictionary."""
        return cls(
            slug=data["slug"],
            floor_price=Decimal(str(data.get("floor_price", "0"))),
            floor_price_usd=Decimal(str(data.get("floor_price_usd", "0"))),
            total_volume=Decimal(str(data.get("total_volume", "0"))),
            total_sales=data.get("total_sales", 0),
            num_owners=data.get("num_owners", 0),
            average_price=Decimal(str(data.get("average_price", "0"))),
            market_cap=Decimal(str(data.get("market_cap", "0"))),
            one_day_volume=Decimal(str(data.get("one_day_volume", "0"))),
            one_day_change=Decimal(str(data.get("one_day_change", "0"))),
            seven_day_volume=Decimal(str(data.get("seven_day_volume", "0"))),
            seven_day_change=Decimal(str(data.get("seven_day_change", "0"))),
        )
