"""
GetUserPositions Query.

Application query for retrieving user vault positions with earnings.
"""

from dataclasses import dataclass, field
from decimal import Decimal

from app.domain.entities.lending.morpho_position import MorphoPosition
from app.domain.ports.morpho_gateway import MorphoGateway


@dataclass
class PositionsSummary:
    """Summary of user positions."""

    total_positions: int
    total_deposited: Decimal
    total_current_value: Decimal
    total_earnings: Decimal
    average_apy: Decimal  # Weighted by deposit


@dataclass
class GetUserPositionsRequest:
    """Request parameters for GetUserPositions query."""

    user_address: str
    chain: str = "ethereum"


@dataclass
class UserPositionsResponse:
    """Response for user positions query."""

    positions: list[MorphoPosition]
    summary: PositionsSummary


class GetUserPositions:
    """
    Query to get user vault positions with earnings.

    Calculates total earnings and weighted average APY.
    """

    def __init__(self, gateway: MorphoGateway):
        """Initialize query."""
        self._gateway = gateway

    async def execute(self, request: GetUserPositionsRequest) -> UserPositionsResponse:
        """Execute query to get user positions."""
        positions = await self._gateway.get_user_positions(
            address=request.user_address,
            chain=request.chain,
        )

        # Enrich with current vault APY
        for position in positions:
            try:
                apy = await self._gateway.get_vault_apy(
                    position.vault_address, request.chain
                )
                position.apy = apy.effective_apy
            except Exception:
                pass  # Keep default APY

        # Calculate summary
        summary = self._calculate_summary(positions)

        return UserPositionsResponse(
            positions=positions,
            summary=summary,
        )

    def _calculate_summary(self, positions: list[MorphoPosition]) -> PositionsSummary:
        """Calculate positions summary."""
        if not positions:
            return PositionsSummary(
                total_positions=0,
                total_deposited=Decimal("0"),
                total_current_value=Decimal("0"),
                total_earnings=Decimal("0"),
                average_apy=Decimal("0"),
            )

        total_deposited = sum(p.deposited_assets for p in positions)
        total_current = sum(p.assets for p in positions)
        total_earnings = sum(p.earnings for p in positions)

        # Weighted average APY
        if total_deposited > 0:
            weighted_apy = (
                sum(p.apy * p.deposited_assets for p in positions) / total_deposited
            )
        else:
            weighted_apy = Decimal("0")

        return PositionsSummary(
            total_positions=len(positions),
            total_deposited=total_deposited,
            total_current_value=total_current,
            total_earnings=total_earnings,
            average_apy=weighted_apy,
        )
