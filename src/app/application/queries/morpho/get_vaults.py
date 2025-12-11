"""
GetVaults Query.

Application query for retrieving Morpho vaults with filtering and enrichment.
"""

from dataclasses import dataclass, field
from decimal import Decimal
from typing import Literal

from app.domain.entities.lending.morpho_vault import MorphoVault
from app.domain.ports.morpho_gateway import MorphoGateway
from app.domain.value_objects.lending.risk_tier import RiskTier


@dataclass
class VaultOpportunity:
    """Top vault opportunity per risk tier."""

    vault_address: str
    vault_name: str
    asset: str
    apy: Decimal
    risk_tier: RiskTier


@dataclass
class GetVaultsRequest:
    """Request parameters for GetVaults query."""

    asset: str | None = None
    risk_tier: str | None = None
    min_apy: float | None = None
    sort_by: Literal["apy", "tvl", "risk"] = "apy"
    chain: str = "ethereum"
    limit: int = 50


@dataclass
class VaultsResponse:
    """Response for vaults query with opportunities."""

    vaults: list[MorphoVault]
    top_opportunities: list[VaultOpportunity] = field(default_factory=list)
    total_count: int = 0


class GetVaults:
    """
    Query to get Morpho vaults with filtering and opportunities.

    Enriches vaults with APY data and identifies top opportunities
    per risk tier.
    """

    def __init__(self, gateway: MorphoGateway):
        """Initialize query."""
        self._gateway = gateway

    async def execute(self, request: GetVaultsRequest) -> VaultsResponse:
        """Execute query to get vaults."""
        # Get base vaults
        vaults = await self._gateway.get_vaults(
            asset=request.asset,
            chain=request.chain,
        )

        # Enrich with APY
        for vault in vaults:
            try:
                apy = await self._gateway.get_vault_apy(
                    vault.address, request.chain
                )
                vault.apy = apy.total_apy
            except Exception:
                pass  # Keep default APY

        # Filter by risk tier
        if request.risk_tier:
            try:
                tier = RiskTier(request.risk_tier)
                vaults = [v for v in vaults if v.risk_tier == tier]
            except ValueError:
                pass  # Invalid tier, skip filter

        # Filter by minimum APY
        if request.min_apy is not None:
            min_apy = Decimal(str(request.min_apy))
            vaults = [v for v in vaults if v.apy >= min_apy]

        # Sort
        if request.sort_by == "apy":
            vaults.sort(key=lambda v: v.apy, reverse=True)
        elif request.sort_by == "tvl":
            vaults.sort(key=lambda v: v.total_assets, reverse=True)
        elif request.sort_by == "risk":
            # Sort by risk tier (low first)
            tier_order = {
                RiskTier.LOW: 0,
                RiskTier.MEDIUM: 1,
                RiskTier.HIGH: 2,
                RiskTier.VERY_HIGH: 3,
            }
            vaults.sort(key=lambda v: tier_order.get(v.risk_tier, 2))

        # Identify top opportunities per risk tier
        opportunities = self._identify_opportunities(vaults)

        return VaultsResponse(
            vaults=vaults[: request.limit],
            top_opportunities=opportunities,
            total_count=len(vaults),
        )

    def _identify_opportunities(
        self, vaults: list[MorphoVault]
    ) -> list[VaultOpportunity]:
        """Identify top vault per risk tier."""
        opportunities = []
        seen_tiers = set()

        # Vaults are already sorted by APY desc
        for vault in vaults:
            if vault.risk_tier not in seen_tiers:
                seen_tiers.add(vault.risk_tier)
                opportunities.append(
                    VaultOpportunity(
                        vault_address=vault.address,
                        vault_name=vault.name,
                        asset=vault.asset,
                        apy=vault.apy,
                        risk_tier=vault.risk_tier,
                    )
                )

        return opportunities
