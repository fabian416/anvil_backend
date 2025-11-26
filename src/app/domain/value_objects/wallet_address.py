"""
Value object for Blockchain Wallet Address.
"""

import re
from dataclasses import dataclass

from app.domain.value_objects.base import ValueObject


@dataclass(frozen=True, slots=True)
class WalletAddress(ValueObject[str]):
    """
    Represents a blockchain wallet address.
    Supports Ethereum-style addresses (0x...) and other formats.
    """
    value: str

    def __post_init__(self) -> None:
        if self.value:
            # Basic validation for Ethereum addresses
            if self.value.startswith("0x"):
                if len(self.value) != 42:
                    raise ValueError("Ethereum address must be 42 characters (including 0x)")
                if not re.match(r"^0x[a-fA-F0-9]{40}$", self.value):
                    raise ValueError("Invalid Ethereum address format")
            # Allow other formats (Solana, etc.) up to 255 chars
            elif len(self.value) > 255:
                raise ValueError("Wallet address must be 255 characters or less")

    @property
    def is_ethereum(self) -> bool:
        """Check if this is an Ethereum-style address."""
        return self.value.startswith("0x") if self.value else False

    @property
    def checksum_address(self) -> str:
        """Return the address (for Ethereum, this would be checksummed)."""
        return self.value

