"""
NFT Collection Entity.

Represents an NFT collection with metadata.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class NFTCollection:
    """
    NFT collection entity.

    Represents a collection of NFTs with metadata.
    """

    slug: str
    name: str
    description: str | None = None
    image_url: str | None = None
    banner_image_url: str | None = None
    total_supply: int = 0
    created_date: datetime | None = None
    contracts: list[dict[str, str]] = field(default_factory=list)

    @property
    def primary_contract(self) -> str | None:
        """Get primary contract address."""
        if self.contracts:
            return self.contracts[0].get("address")
        return None

    @property
    def chain(self) -> str | None:
        """Get primary chain."""
        if self.contracts:
            return self.contracts[0].get("chain")
        return None

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "slug": self.slug,
            "name": self.name,
            "description": self.description,
            "image_url": self.image_url,
            "banner_image_url": self.banner_image_url,
            "total_supply": self.total_supply,
            "created_date": self.created_date.isoformat() if self.created_date else None,
            "contracts": self.contracts,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "NFTCollection":
        """Deserialize from dictionary."""
        created = data.get("created_date")
        if isinstance(created, str):
            created = datetime.fromisoformat(created)

        return cls(
            slug=data["slug"],
            name=data["name"],
            description=data.get("description"),
            image_url=data.get("image_url"),
            banner_image_url=data.get("banner_image_url"),
            total_supply=data.get("total_supply", 0),
            created_date=created,
            contracts=data.get("contracts", []),
        )
