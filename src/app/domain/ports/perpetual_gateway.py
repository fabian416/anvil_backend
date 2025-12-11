"""
Perpetual Futures Gateway Port.

Defines the domain interface for perpetual futures operations.
Supports Hyperliquid and potentially other perp DEXs.
"""

from decimal import Decimal
from typing import Protocol

from app.domain.entities.perpetual.liquidation import Liquidation
from app.domain.entities.perpetual.market import PerpMarket
from app.domain.entities.perpetual.position import Position
from app.domain.value_objects.perpetual.funding_rate import FundingRate
from app.domain.value_objects.perpetual.order_book import OrderBook
from app.domain.value_objects.perpetual.risk_metrics import RiskMetrics


class PerpetualGateway(Protocol):
    """
    Port interface for perpetual futures operations.

    This protocol defines the contract for accessing perpetual
    futures data and calculations.
    """

    async def get_markets(self) -> list[PerpMarket]:
        """
        Get all perpetual markets.

        Returns:
            List of PerpMarket entities

        Raises:
            HyperliquidAPIError: If API is unavailable
        """
        ...

    async def get_order_book(
        self,
        symbol: str,
        depth: int = 20,
    ) -> OrderBook:
        """
        Get order book for a symbol.

        Args:
            symbol: Trading pair (e.g., "ETH")
            depth: Number of levels per side

        Returns:
            OrderBook value object

        Raises:
            SymbolNotFoundError: If symbol doesn't exist
            HyperliquidAPIError: If API is unavailable
        """
        ...

    async def get_funding_rate(
        self,
        symbol: str,
    ) -> FundingRate:
        """
        Get current funding rate for a symbol.

        Args:
            symbol: Trading pair

        Returns:
            FundingRate value object

        Raises:
            SymbolNotFoundError: If symbol doesn't exist
        """
        ...

    async def get_funding_rates(self) -> list[FundingRate]:
        """
        Get all funding rates.

        Returns:
            List of FundingRate value objects
        """
        ...

    async def get_liquidations(
        self,
        symbol: str | None = None,
        hours: int = 24,
    ) -> list[Liquidation]:
        """
        Get recent liquidations.

        Args:
            symbol: Filter by symbol (None = all)
            hours: Lookback period

        Returns:
            List of Liquidation entities
        """
        ...

    async def get_positions(
        self,
        address: str,
    ) -> list[Position]:
        """
        Get user's open positions.

        Args:
            address: Wallet address

        Returns:
            List of Position entities

        Raises:
            InvalidAddressError: If address format invalid
        """
        ...

    def calculate_liquidation_price(
        self,
        entry_price: Decimal,
        leverage: Decimal,
        side: str,
        maintenance_margin: Decimal = Decimal("0.005"),
    ) -> Decimal:
        """
        Calculate liquidation price for a position.

        Args:
            entry_price: Position entry price
            leverage: Position leverage
            side: "long" or "short"
            maintenance_margin: Maintenance margin rate

        Returns:
            Liquidation price
        """
        ...

    def calculate_risk_metrics(
        self,
        entry_price: Decimal,
        size: Decimal,
        leverage: Decimal,
        side: str,
        account_balance: Decimal | None = None,
    ) -> RiskMetrics:
        """
        Calculate comprehensive risk metrics.

        Args:
            entry_price: Entry price
            size: Position size
            leverage: Leverage used
            side: "long" or "short"
            account_balance: Optional account balance

        Returns:
            RiskMetrics value object
        """
        ...
