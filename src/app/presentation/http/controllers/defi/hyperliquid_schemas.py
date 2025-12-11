"""
Hyperliquid Pydantic Schemas.

Request and response models for Hyperliquid API endpoints.
"""

from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field

from app.domain.entities.perpetual.liquidation import Liquidation
from app.domain.entities.perpetual.market import PerpMarket
from app.domain.entities.perpetual.position import Position
from app.domain.value_objects.perpetual.funding_rate import FundingRate
from app.domain.value_objects.perpetual.order_book import OrderBook
from app.domain.value_objects.perpetual.risk_metrics import RiskMetrics


# =============================================================================
# Request Models
# =============================================================================


class CalculateRiskRequestModel(BaseModel):
    """Request model for risk calculation."""

    entry_price: str = Field(..., description="Entry price")
    size: str = Field(..., description="Position size")
    leverage: str = Field(..., description="Leverage (e.g., '10' for 10x)")
    side: Literal["long", "short"] = Field(..., description="Position side")
    account_balance: str | None = Field(default=None, description="Account balance")


# =============================================================================
# Response Models
# =============================================================================


class MarketResponse(BaseModel):
    """Market response model."""

    symbol: str
    mark_price: str
    index_price: str
    funding_rate: str = Field(description="8-hour funding rate")
    open_interest: str
    volume_24h: str
    price_change_24h: str = Field(description="24h price change %")
    max_leverage: int

    @classmethod
    def from_domain(cls, market: PerpMarket) -> "MarketResponse":
        """Create from domain entity."""
        return cls(
            symbol=market.symbol,
            mark_price=str(market.mark_price),
            index_price=str(market.index_price),
            funding_rate=str(market.funding_rate),
            open_interest=str(market.open_interest),
            volume_24h=str(market.volume_24h),
            price_change_24h=str(market.price_change_24h),
            max_leverage=market.max_leverage,
        )


class MarketsResponse(BaseModel):
    """Markets list response model."""

    markets: list[MarketResponse]
    count: int

    @classmethod
    def from_domain(cls, markets: list[PerpMarket]) -> "MarketsResponse":
        """Create from domain entities."""
        return cls(
            markets=[MarketResponse.from_domain(m) for m in markets],
            count=len(markets),
        )


class OrderBookResponse(BaseModel):
    """Order book response model."""

    symbol: str
    bids: list[list[str]] = Field(description="[price, size] pairs")
    asks: list[list[str]]
    spread: str
    spread_pct: str
    mid_price: str
    warnings: list[str] = Field(default_factory=list)

    @classmethod
    def from_domain(
        cls, order_book: OrderBook, warnings: list[str] | None = None
    ) -> "OrderBookResponse":
        """Create from domain value object."""
        return cls(
            symbol=order_book.symbol,
            bids=[[str(p), str(s)] for p, s in order_book.bids],
            asks=[[str(p), str(s)] for p, s in order_book.asks],
            spread=str(order_book.spread),
            spread_pct=str(order_book.spread_pct),
            mid_price=str(order_book.mid_price),
            warnings=warnings or [],
        )


class FundingRateResponse(BaseModel):
    """Funding rate response model."""

    symbol: str
    rate: str = Field(description="8-hour rate")
    annualized_rate: str
    direction_bias: str = Field(description="BULLISH, BEARISH, or NEUTRAL")
    next_funding_time: str

    @classmethod
    def from_domain(cls, funding: FundingRate) -> "FundingRateResponse":
        """Create from domain value object."""
        return cls(
            symbol=funding.symbol,
            rate=str(funding.rate),
            annualized_rate=str(funding.annualized_rate),
            direction_bias=funding.direction_bias,
            next_funding_time=funding.next_funding_time.isoformat(),
        )


class FundingOpportunityResponse(BaseModel):
    """Funding opportunity response model."""

    symbol: str
    rate: str
    annualized_return: str
    direction: str
    strategy: str


class FundingRatesResponse(BaseModel):
    """Funding rates list response with opportunities."""

    rates: list[FundingRateResponse]
    opportunities: list[FundingOpportunityResponse]
    count: int


class LiquidationResponse(BaseModel):
    """Liquidation response model."""

    symbol: str
    side: str
    size: str
    price: str
    value_usd: str
    timestamp: str

    @classmethod
    def from_domain(cls, liq: Liquidation) -> "LiquidationResponse":
        """Create from domain entity."""
        return cls(
            symbol=liq.symbol,
            side=liq.side,
            size=str(liq.size),
            price=str(liq.price),
            value_usd=str(liq.value_usd),
            timestamp=liq.timestamp.isoformat(),
        )


class LiquidationSummaryResponse(BaseModel):
    """Liquidation summary response model."""

    total_count: int
    total_volume_usd: str
    long_volume_usd: str
    short_volume_usd: str
    largest_liquidation_usd: str
    is_cascade: bool


class LiquidationsResponse(BaseModel):
    """Liquidations response with summary."""

    liquidations: list[LiquidationResponse]
    summary: LiquidationSummaryResponse
    warnings: list[str]


class PositionResponse(BaseModel):
    """Position response model."""

    symbol: str
    side: str
    size: str
    entry_price: str
    mark_price: str
    unrealized_pnl: str
    pnl_pct: str
    leverage: str
    liquidation_price: str
    margin_ratio: str

    @classmethod
    def from_domain(cls, position: Position) -> "PositionResponse":
        """Create from domain entity."""
        return cls(
            symbol=position.symbol,
            side=position.side,
            size=str(position.size),
            entry_price=str(position.entry_price),
            mark_price=str(position.mark_price),
            unrealized_pnl=str(position.unrealized_pnl),
            pnl_pct=str(position.pnl_pct),
            leverage=str(position.leverage),
            liquidation_price=str(position.liquidation_price),
            margin_ratio=str(position.margin_ratio),
        )


class PositionsSummaryResponse(BaseModel):
    """Positions summary response model."""

    total_positions: int
    total_unrealized_pnl: str
    total_position_value: str
    long_exposure: str
    short_exposure: str


class PositionsResponse(BaseModel):
    """Positions response with summary."""

    positions: list[PositionResponse]
    summary: PositionsSummaryResponse
    warnings: list[str]


class RiskMetricsResponse(BaseModel):
    """Risk metrics response model."""

    liquidation_price: str
    margin_required: str
    max_loss: str
    distance_to_liquidation_pct: str
    risk_level: str = Field(description="LOW, MEDIUM, HIGH, or EXTREME")

    @classmethod
    def from_domain(cls, metrics: RiskMetrics) -> "RiskMetricsResponse":
        """Create from domain value object."""
        return cls(
            liquidation_price=str(metrics.liquidation_price),
            margin_required=str(metrics.margin_required),
            max_loss=str(metrics.max_loss),
            distance_to_liquidation_pct=str(metrics.distance_to_liquidation_pct),
            risk_level=metrics.risk_level,
        )
