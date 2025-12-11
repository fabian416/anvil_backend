"""
LayerZero Chain Value Object.

Immutable representation of a LayerZero-supported chain.
"""

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class LZChain:
    """
    LayerZero chain value object.

    Contains chain information for LayerZero endpoints.
    """

    endpoint_id: int  # LayerZero endpoint ID
    name: str
    network: str
    native_chain_id: int
    is_evm: bool = True

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "endpoint_id": self.endpoint_id,
            "name": self.name,
            "network": self.network,
            "native_chain_id": self.native_chain_id,
            "is_evm": self.is_evm,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "LZChain":
        """Deserialize from dictionary."""
        return cls(
            endpoint_id=data["endpoint_id"],
            name=data["name"],
            network=data.get("network", "mainnet"),
            native_chain_id=data["native_chain_id"],
            is_evm=data.get("is_evm", True),
        )
