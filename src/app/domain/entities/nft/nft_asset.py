"""
NFT Asset Entity.

Represents an individual NFT token.
"""

from dataclasses import dataclass, field
from decimal import Decimal
from typing import Any

from app.domain.value_objects.nft.nft_trait import NFTTrait


@dataclass
class NFTAsset:
    """
    NFT asset entity.

    Represents an individual NFT with metadata and traits.
    """

    identifier: str  # Token ID
    collection_slug: str
    contract_address: str
    name: str | None = None
    description: str | None = None
    image_url: str | None = None
    animation_url: str | None = None
    traits: list[NFTTrait] = field(default_factory=list)
    rarity_rank: int | None = None
    last_sale_price: Decimal | None = None
    last_sale_currency: str | None = None

    @property
    def display_name(self) -> str:
        """Get display name."""
        return self.name or f"#{self.identifier}"

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "identifier": self.identifier,
            "collection_slug": self.collection_slug,
            "contract_address": self.contract_address,
            "name": self.name,
            "description": self.description,
            "image_url": self.image_url,
            "animation_url": self.animation_url,
            "traits": [t.to_dict() for t in self.traits],
            "rarity_rank": self.rarity_rank,
            "last_sale_price": str(self.last_sale_price) if self.last_sale_price else None,
            "last_sale_currency": self.last_sale_currency,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "NFTAsset":
        """Deserialize from dictionary."""
        traits_data = data.get("traits", [])
        traits = [NFTTrait.from_dict(t) for t in traits_data]

        last_sale = data.get("last_sale_price")

        return cls(
            identifier=data["identifier"],
            collection_slug=data["collection_slug"],
            contract_address=data["contract_address"],
            name=data.get("name"),
            description=data.get("description"),
            image_url=data.get("image_url"),
            animation_url=data.get("animation_url"),
            traits=traits,
            rarity_rank=data.get("rarity_rank"),
            last_sale_price=Decimal(str(last_sale)) if last_sale else None,
            last_sale_currency=data.get("last_sale_currency"),
        )
