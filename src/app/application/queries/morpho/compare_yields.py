"""
CompareYields Query.

Application query for comparing Morpho yields with other protocols.
"""

from dataclasses import dataclass, field
from decimal import Decimal

from app.domain.ports.morpho_gateway import MorphoGateway
from app.domain.value_objects.lending.risk_tier import RiskTier


@dataclass
class YieldComparison:
    """Yield comparison for a single option."""

    protocol: str
    vault_name: str
    apy: Decimal
    risk_tier: RiskTier
    apy_advantage: Decimal = Decimal("0")  # vs next best


@dataclass
class CompareYieldsRequest:
    """Request parameters for CompareYields query."""

    asset: str
    protocols: list[str] = field(default_factory=lambda: ["morpho"])
    chain: str = "ethereum"


@dataclass
class YieldComparisonResponse:
    """Response for yield comparison query."""

    asset: str
    comparisons: list[YieldComparison]
    best_option: YieldComparison | None = None


class CompareYields:
    """
    Query to compare yields across protocols.

    Currently focuses on Morpho vaults but can be extended
    to include other protocols.
    """

    def __init__(self, gateway: MorphoGateway):
        """Initialize query."""
        self._gateway = gateway

    async def execute(self, request: CompareYieldsRequest) -> YieldComparisonResponse:
        """Execute query to compare yields."""
        comparisons = []

        # Get Morpho vaults for the asset
        if "morpho" in request.protocols:
            vaults = await self._gateway.get_vaults(
                asset=request.asset,
                chain=request.chain,
            )

            # Enrich and add top vaults
            for vault in vaults[:5]:  # Top 5 vaults
                try:
                    apy = await self._gateway.get_vault_apy(
                        vault.address, request.chain
                    )
                    comparisons.append(
                        YieldComparison(
                            protocol="Morpho",
                            vault_name=vault.name,
                            apy=apy.effective_apy,
                            risk_tier=vault.risk_tier,
                        )
                    )
                except Exception:
                    pass

        # Sort by APY
        comparisons.sort(key=lambda c: c.apy, reverse=True)

        # Calculate APY advantage
        if len(comparisons) >= 2:
            for i, comp in enumerate(comparisons):
                if i < len(comparisons) - 1:
                    comp.apy_advantage = comp.apy - comparisons[i + 1].apy

        best = comparisons[0] if comparisons else None

        return YieldComparisonResponse(
            asset=request.asset,
            comparisons=comparisons,
            best_option=best,
        )
