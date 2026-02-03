from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class PrivyPolicyDTO:
    """DTO for a Privy policy payload."""

    id: str
    name: str
    version: str
    chain_type: str
    rules: list[dict[str, Any]]
    owner_id: str | None = None

    @classmethod
    def from_api(cls, data: dict[str, Any]) -> "PrivyPolicyDTO":
        return cls(
            id=str(data.get("id", "")),
            name=str(data.get("name", "")),
            version=str(data.get("version", "")),
            chain_type=str(data.get("chain_type", "")),
            rules=list(data.get("rules", []) or []),
            owner_id=data.get("owner_id"),
        )
