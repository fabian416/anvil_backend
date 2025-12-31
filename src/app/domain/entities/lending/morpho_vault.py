"""
Morpho Vault Entity.

Represents a MetaMorpho vault with its configuration and allocations.
"""

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import Any

from app.domain.value_objects.lending.market_allocation import MarketAllocation
from app.domain.value_objects.lending.risk_tier import RiskTier


@dataclass
class MorphoVault:
    """
    MetaMorpho vault entity.

    Represents a lending vault that allocates funds
    across multiple Morpho Blue markets.
    
    Supports multiple chains:
    - Ethereum (chain_id: 1)
    - Base (chain_id: 8453)
    """

    address: str
    name: str
    symbol: str
    asset: str  # Underlying asset symbol (e.g., USDC)
    asset_address: str
    asset_decimals: int = 18
    total_assets: Decimal = Decimal("0")  # Total deposited
    total_shares: Decimal = Decimal("0")  # Shares outstanding
    apy: Decimal = Decimal("0")  # Current APY
    fee_percentage: Decimal = Decimal("0")  # Performance fee
    curator_address: str | None = None
    guardian_address: str | None = None
    risk_tier: RiskTier = RiskTier.MEDIUM
    market_allocations: list[MarketAllocation] = field(default_factory=list)
    created_at: datetime | None = None
    chain: str = "ethereum"  # blockchain network
    whitelisted: bool = False  # curated/whitelisted vault

    @property
    def tvl_raw(self) -> Decimal:
        """Get total value locked in raw token units."""
        return self.total_assets

    @property
    def share_price(self) -> Decimal:
        """Calculate share price."""
        if self.total_shares == 0:
            return Decimal("1")
        return self.total_assets / self.total_shares

    @property
    def net_apy(self) -> Decimal:
        """Calculate net APY after fees."""
        return self.apy * (1 - self.fee_percentage)

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "address": self.address,
            "name": self.name,
            "symbol": self.symbol,
            "asset": self.asset,
            "asset_address": self.asset_address,
            "asset_decimals": self.asset_decimals,
            "total_assets": str(self.total_assets),
            "total_shares": str(self.total_shares),
            "apy": str(self.apy),
            "fee_percentage": str(self.fee_percentage),
            "curator_address": self.curator_address,
            "guardian_address": self.guardian_address,
            "risk_tier": self.risk_tier.value,
            "market_allocations": [a.to_dict() for a in self.market_allocations],
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "chain": self.chain,
            "whitelisted": self.whitelisted,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "MorphoVault":
        """Deserialize from dictionary."""
        created_at = data.get("created_at")
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at)

        allocations = [
            MarketAllocation.from_dict(a)
            for a in data.get("market_allocations", [])
        ]

        return cls(
            address=data["address"],
            name=data["name"],
            symbol=data.get("symbol", data["name"]),
            asset=data["asset"],
            asset_address=data.get("asset_address", ""),
            asset_decimals=data.get("asset_decimals", 18),
            total_assets=Decimal(str(data.get("total_assets", "0"))),
            total_shares=Decimal(str(data.get("total_shares", "0"))),
            apy=Decimal(str(data.get("apy", "0"))),
            fee_percentage=Decimal(str(data.get("fee_percentage", "0"))),
            curator_address=data.get("curator_address"),
            guardian_address=data.get("guardian_address"),
            risk_tier=RiskTier(data.get("risk_tier", "medium")),
            market_allocations=allocations,
            created_at=created_at,
            chain=data.get("chain", "ethereum"),
            whitelisted=data.get("whitelisted", False),
        )
