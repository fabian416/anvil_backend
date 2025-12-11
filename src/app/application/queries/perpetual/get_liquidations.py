"""
GetLiquidations Query.

Application query for retrieving liquidation events with analysis.
"""

from dataclasses import dataclass, field
from decimal import Decimal
from typing import Literal

from app.domain.entities.perpetual.liquidation import Liquidation
from app.domain.ports.perpetual_gateway import PerpetualGateway


# Threshold for cascade warning ($1M in 1 hour)
CASCADE_THRESHOLD = Decimal("1000000")


@dataclass
class LiquidationSummary:
    """Summary of liquidation data."""

    total_count: int
    total_volume_usd: Decimal
    long_volume_usd: Decimal
    short_volume_usd: Decimal
    largest_liquidation_usd: Decimal
    is_cascade: bool


@dataclass
class GetLiquidationsRequest:
    """Request parameters for GetLiquidations query."""

    symbol: str | None = None
    hours: int = 24
    sort_by: Literal["size", "time"] = "time"


@dataclass
class LiquidationsResponse:
    """Response for liquidations query with analysis."""

    liquidations: list[Liquidation]
    summary: LiquidationSummary
    warnings: list[str] = field(default_factory=list)


class GetLiquidations:
    """
    Query to get liquidations with market stress analysis.

    Detects liquidation cascades and provides breakdown.
    """

    def __init__(self, gateway: PerpetualGateway):
        """Initialize query."""
        self._gateway = gateway

    async def execute(self, request: GetLiquidationsRequest) -> LiquidationsResponse:
        """Execute query to get liquidations."""
        liquidations = await self._gateway.get_liquidations(
            symbol=request.symbol,
            hours=request.hours,
        )

        # Sort
        if request.sort_by == "size":
            liquidations.sort(key=lambda l: l.value_usd, reverse=True)
        else:  # time
            liquidations.sort(key=lambda l: l.timestamp, reverse=True)

        # Calculate summary
        summary = self._calculate_summary(liquidations, request.hours)

        # Generate warnings
        warnings = self._analyze_liquidations(summary, request.hours)

        return LiquidationsResponse(
            liquidations=liquidations,
            summary=summary,
            warnings=warnings,
        )

    def _calculate_summary(
        self, liquidations: list[Liquidation], hours: int
    ) -> LiquidationSummary:
        """Calculate liquidation summary statistics."""
        if not liquidations:
            return LiquidationSummary(
                total_count=0,
                total_volume_usd=Decimal("0"),
                long_volume_usd=Decimal("0"),
                short_volume_usd=Decimal("0"),
                largest_liquidation_usd=Decimal("0"),
                is_cascade=False,
            )

        total_volume = sum(l.value_usd for l in liquidations)
        long_volume = sum(l.value_usd for l in liquidations if l.side == "long")
        short_volume = sum(l.value_usd for l in liquidations if l.side == "short")
        largest = max(l.value_usd for l in liquidations)

        # Check for cascade (>$1M per hour average)
        is_cascade = (total_volume / hours) > CASCADE_THRESHOLD if hours > 0 else False

        return LiquidationSummary(
            total_count=len(liquidations),
            total_volume_usd=total_volume,
            long_volume_usd=long_volume,
            short_volume_usd=short_volume,
            largest_liquidation_usd=largest,
            is_cascade=is_cascade,
        )

    def _analyze_liquidations(
        self, summary: LiquidationSummary, hours: int
    ) -> list[str]:
        """Analyze liquidations for warnings."""
        warnings = []

        if summary.is_cascade:
            warnings.append(
                f"Liquidation cascade detected: ${summary.total_volume_usd:,.0f} "
                f"in {hours}h. Market may be highly volatile."
            )

        # Check for imbalance
        if summary.long_volume_usd > 0 and summary.short_volume_usd > 0:
            ratio = summary.long_volume_usd / summary.short_volume_usd
            if ratio > 3:
                warnings.append(
                    "Heavy long liquidations. Possible market top or leverage flush."
                )
            elif ratio < 0.33:
                warnings.append(
                    "Heavy short liquidations. Possible short squeeze in progress."
                )

        # Large single liquidation
        if summary.largest_liquidation_usd > Decimal("100000"):
            warnings.append(
                f"Large liquidation: ${summary.largest_liquidation_usd:,.0f}. "
                "Whale position liquidated."
            )

        return warnings
