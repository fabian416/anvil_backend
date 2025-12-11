"""
EstimateTransfer Query.

Application query for estimating transfer costs.
"""

from dataclasses import dataclass
from decimal import Decimal

from app.domain.ports.axelar_gateway import AxelarGateway
from app.domain.value_objects.bridge.transfer_estimate import TransferEstimate


@dataclass
class EstimateTransferRequest:
    """Request parameters for EstimateTransfer query."""

    source_chain: str
    destination_chain: str
    token: str
    amount: str
    include_express: bool = True


@dataclass
class TransferEstimateResponse:
    """Response for transfer estimate query."""

    standard: TransferEstimate
    express: TransferEstimate | None = None
    recommendation: str | None = None  # "STANDARD" or "EXPRESS"


class EstimateTransfer:
    """
    Query to estimate transfer costs.

    Returns both standard and express estimates with recommendation.
    """

    # Thresholds for express recommendation
    TIME_SAVINGS_THRESHOLD = 600  # 10 minutes
    COST_THRESHOLD = Decimal("5.0")  # $5

    def __init__(self, gateway: AxelarGateway):
        """Initialize query."""
        self._gateway = gateway

    async def execute(self, request: EstimateTransferRequest) -> TransferEstimateResponse:
        """Execute query to estimate transfer."""
        # Get standard estimate
        standard = await self._gateway.estimate_transfer(
            source_chain=request.source_chain,
            destination_chain=request.destination_chain,
            token=request.token,
            amount=request.amount,
            express=False,
        )

        response = TransferEstimateResponse(
            standard=standard,
            express=None,
            recommendation=None,
        )

        # Get express estimate if requested
        if request.include_express:
            express = await self._gateway.estimate_transfer(
                source_chain=request.source_chain,
                destination_chain=request.destination_chain,
                token=request.token,
                amount=request.amount,
                express=True,
            )
            response.express = express
            response.recommendation = self._recommend(standard, express)

        return response

    def _recommend(
        self,
        standard: TransferEstimate,
        express: TransferEstimate,
    ) -> str:
        """Recommend standard or express based on trade-offs."""
        time_savings = standard.estimated_time_seconds - express.estimated_time_seconds
        cost_diff = express.total_cost_usd - standard.total_cost_usd

        # Recommend express if time savings > 10 min and cost < $5
        if time_savings > self.TIME_SAVINGS_THRESHOLD and cost_diff < self.COST_THRESHOLD:
            return "EXPRESS"
        return "STANDARD"
