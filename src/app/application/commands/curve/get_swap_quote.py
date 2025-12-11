"""
GetSwapQuote Command.

Application command for getting swap quotes with risk analysis.
"""

from dataclasses import dataclass
from decimal import Decimal

from app.domain.ports.curve_gateway import CurveGateway
from app.domain.value_objects.curve.swap_quote import SwapQuote


@dataclass
class SwapQuoteRequest:
    """Request parameters for GetSwapQuote command."""

    from_token: str
    to_token: str
    amount: str  # Amount in smallest unit (wei)
    chain: str = "ethereum"


# Price impact thresholds for warnings
HIGH_PRICE_IMPACT_THRESHOLD = Decimal("0.5")  # 0.5%
VERY_HIGH_PRICE_IMPACT_THRESHOLD = Decimal("1.0")  # 1%
DEPEG_THRESHOLD = Decimal("0.99")  # Exchange rate below 0.99 indicates depeg


class GetSwapQuote:
    """
    Command to get a swap quote with risk warnings.

    This interactor adds business logic on top of the raw quote:
    - High price impact warnings (>0.5%)
    - Depeg risk warnings
    - Slippage recommendations
    """

    def __init__(self, gateway: CurveGateway):
        """
        Initialize GetSwapQuote command.

        Args:
            gateway: CurveGateway port for data access
        """
        self._gateway = gateway

    async def execute(self, request: SwapQuoteRequest) -> SwapQuote:
        """
        Execute the command to get a swap quote.

        Args:
            request: Command parameters

        Returns:
            SwapQuote value object with quote and warnings
        """
        # Get raw quote from gateway
        quote = await self._gateway.get_swap_quote(
            from_token=request.from_token,
            to_token=request.to_token,
            amount=request.amount,
            chain=request.chain,
        )

        # Analyze quote and add warnings
        warnings = self._analyze_quote(quote)

        # Return quote with warnings
        if warnings:
            return quote.with_warnings(warnings)

        return quote

    def _analyze_quote(self, quote: SwapQuote) -> list[str]:
        """
        Analyze quote for potential risks.

        Args:
            quote: The swap quote to analyze

        Returns:
            List of warning messages
        """
        warnings = []

        # Check price impact
        if quote.price_impact >= VERY_HIGH_PRICE_IMPACT_THRESHOLD:
            warnings.append(
                f"Very high price impact: {quote.price_impact}%. "
                "Consider splitting into smaller trades."
            )
        elif quote.price_impact >= HIGH_PRICE_IMPACT_THRESHOLD:
            warnings.append(
                f"High price impact: {quote.price_impact}%. "
                "You may receive less than expected."
            )

        # Check for potential stablecoin depeg
        if quote.exchange_rate < DEPEG_THRESHOLD:
            warnings.append(
                f"Exchange rate ({quote.exchange_rate}) suggests potential depeg risk. "
                "Verify token prices before swapping."
            )

        # Check for very small output (potential issue)
        if quote.amount_out <= Decimal("0"):
            warnings.append(
                "Output amount is zero or negative. "
                "Check token addresses and amount."
            )

        return warnings
