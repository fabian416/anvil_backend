"""
CalculateRisk Command.

Application command for calculating position risk metrics.
"""

from dataclasses import dataclass
from decimal import Decimal
from typing import Literal

from app.domain.ports.perpetual_gateway import PerpetualGateway
from app.domain.value_objects.perpetual.risk_metrics import RiskMetrics


@dataclass
class CalculateRiskRequest:
    """Request parameters for CalculateRisk command."""

    entry_price: Decimal
    size: Decimal
    leverage: Decimal
    side: Literal["long", "short"]
    account_balance: Decimal | None = None


class CalculateRisk:
    """
    Command to calculate position risk metrics.

    Calculates liquidation price, margin requirements,
    and risk level for a potential position.
    """

    def __init__(self, gateway: PerpetualGateway):
        """Initialize command."""
        self._gateway = gateway

    async def execute(self, request: CalculateRiskRequest) -> RiskMetrics:
        """
        Execute command to calculate risk.

        This is an async method for consistency with the protocol,
        but the actual calculation is synchronous.
        """
        return self._gateway.calculate_risk_metrics(
            entry_price=request.entry_price,
            size=request.size,
            leverage=request.leverage,
            side=request.side,
            account_balance=request.account_balance,
        )
