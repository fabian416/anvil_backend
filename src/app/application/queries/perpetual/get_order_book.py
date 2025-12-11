"""
GetOrderBook Query.

Application query for retrieving order book with spread analysis.
"""

from dataclasses import dataclass, field
from decimal import Decimal

from app.domain.ports.perpetual_gateway import PerpetualGateway
from app.domain.value_objects.perpetual.order_book import OrderBook


# Spread threshold for warnings
HIGH_SPREAD_THRESHOLD = Decimal("0.1")  # 0.1%


@dataclass
class GetOrderBookRequest:
    """Request parameters for GetOrderBook query."""

    symbol: str
    depth: int = 20


@dataclass
class OrderBookResponse:
    """Response for order book query with analysis."""

    order_book: OrderBook
    warnings: list[str] = field(default_factory=list)


class GetOrderBook:
    """
    Query to get order book with liquidity analysis.

    Includes spread warnings and depth analysis.
    """

    def __init__(self, gateway: PerpetualGateway):
        """Initialize query."""
        self._gateway = gateway

    async def execute(self, request: GetOrderBookRequest) -> OrderBookResponse:
        """Execute query to get order book."""
        order_book = await self._gateway.get_order_book(
            symbol=request.symbol,
            depth=request.depth,
        )

        warnings = self._analyze_order_book(order_book)

        return OrderBookResponse(
            order_book=order_book,
            warnings=warnings,
        )

    def _analyze_order_book(self, order_book: OrderBook) -> list[str]:
        """Analyze order book for potential issues."""
        warnings = []

        # Check spread
        if order_book.spread_pct > HIGH_SPREAD_THRESHOLD:
            warnings.append(
                f"High spread: {order_book.spread_pct:.4f}%. "
                "Consider using limit orders."
            )

        # Check depth imbalance
        if abs(order_book.imbalance) > Decimal("0.5"):
            direction = "buy" if order_book.imbalance > 0 else "sell"
            warnings.append(
                f"Order book imbalanced toward {direction} side. "
                "Price may move in that direction."
            )

        # Check for thin liquidity
        if order_book.bid_depth < Decimal("100") or order_book.ask_depth < Decimal("100"):
            warnings.append(
                "Low liquidity detected. Large orders may have significant slippage."
            )

        return warnings
