"""
GetPositions Query.

Application query for retrieving user positions with risk analysis.
"""

from dataclasses import dataclass, field
from decimal import Decimal

from app.domain.entities.perpetual.position import Position
from app.domain.ports.perpetual_gateway import PerpetualGateway


# Risk thresholds
HIGH_LEVERAGE_THRESHOLD = Decimal("10")  # 10x
LOW_MARGIN_THRESHOLD = Decimal("20")  # 20% margin ratio


@dataclass
class PositionsSummary:
    """Summary of user positions."""

    total_positions: int
    total_unrealized_pnl: Decimal
    total_position_value: Decimal
    long_exposure: Decimal
    short_exposure: Decimal


@dataclass
class GetPositionsRequest:
    """Request parameters for GetPositions query."""

    address: str


@dataclass
class PositionsResponse:
    """Response for positions query with analysis."""

    positions: list[Position]
    summary: PositionsSummary
    warnings: list[str] = field(default_factory=list)


class GetPositions:
    """
    Query to get user positions with risk analysis.

    Provides PnL summary and risk warnings.
    """

    def __init__(self, gateway: PerpetualGateway):
        """Initialize query."""
        self._gateway = gateway

    async def execute(self, request: GetPositionsRequest) -> PositionsResponse:
        """Execute query to get positions."""
        positions = await self._gateway.get_positions(address=request.address)

        # Calculate summary
        summary = self._calculate_summary(positions)

        # Generate warnings
        warnings = self._analyze_positions(positions)

        return PositionsResponse(
            positions=positions,
            summary=summary,
            warnings=warnings,
        )

    def _calculate_summary(self, positions: list[Position]) -> PositionsSummary:
        """Calculate positions summary."""
        if not positions:
            return PositionsSummary(
                total_positions=0,
                total_unrealized_pnl=Decimal("0"),
                total_position_value=Decimal("0"),
                long_exposure=Decimal("0"),
                short_exposure=Decimal("0"),
            )

        total_pnl = sum(p.unrealized_pnl for p in positions)
        total_value = sum(p.position_value for p in positions)
        long_exposure = sum(p.position_value for p in positions if p.side == "long")
        short_exposure = sum(p.position_value for p in positions if p.side == "short")

        return PositionsSummary(
            total_positions=len(positions),
            total_unrealized_pnl=total_pnl,
            total_position_value=total_value,
            long_exposure=long_exposure,
            short_exposure=short_exposure,
        )

    def _analyze_positions(self, positions: list[Position]) -> list[str]:
        """Analyze positions for risk warnings."""
        warnings = []

        for position in positions:
            # High leverage warning
            if position.leverage >= HIGH_LEVERAGE_THRESHOLD:
                warnings.append(
                    f"{position.symbol}: High leverage ({position.leverage}x). "
                    "Consider reducing position size."
                )

            # Low margin warning
            if (
                position.margin_ratio > 0
                and position.margin_ratio < LOW_MARGIN_THRESHOLD
            ):
                warnings.append(
                    f"{position.symbol}: Low margin ratio ({position.margin_ratio}%). "
                    "Close to liquidation."
                )

            # Large unrealized loss
            if position.pnl_pct < Decimal("-20"):
                warnings.append(
                    f"{position.symbol}: Large unrealized loss ({position.pnl_pct}%). "
                    "Consider closing to limit losses."
                )

        return warnings
