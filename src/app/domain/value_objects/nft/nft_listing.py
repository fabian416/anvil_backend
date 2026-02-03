"""
NFT Listing Value Object.

Immutable representation of an NFT marketplace listing.
"""

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Any


@dataclass(frozen=True)
class NFTListing:
    """
    NFT listing value object.

    Represents an active listing on the marketplace.
    """

    order_hash: str
    token_id: str
    collection_slug: str
    price: Decimal  # In ETH
    price_usd: Decimal
    currency: str
    seller: str
    created_date: datetime
    expiration_date: datetime | None = None

    @property
    def is_expired(self) -> bool:
        """Check if listing is expired."""
        if self.expiration_date:
            return datetime.now() > self.expiration_date
        return False

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "order_hash": self.order_hash,
            "token_id": self.token_id,
            "collection_slug": self.collection_slug,
            "price": str(self.price),
            "price_usd": str(self.price_usd),
            "currency": self.currency,
            "seller": self.seller,
            "created_date": self.created_date.isoformat(),
            "expiration_date": self.expiration_date.isoformat()
            if self.expiration_date
            else None,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "NFTListing":
        """Deserialize from dictionary."""
        created = data.get("created_date")
        if isinstance(created, str):
            created = datetime.fromisoformat(created)

        expiration = data.get("expiration_date")
        if isinstance(expiration, str):
            expiration = datetime.fromisoformat(expiration)

        return cls(
            order_hash=data["order_hash"],
            token_id=data["token_id"],
            collection_slug=data["collection_slug"],
            price=Decimal(str(data.get("price", "0"))),
            price_usd=Decimal(str(data.get("price_usd", "0"))),
            currency=data.get("currency", "ETH"),
            seller=data["seller"],
            created_date=created or datetime.now(),
            expiration_date=expiration,
        )
