"""
Hyperliquid Gateway Adapter.

Implements the PerpetualGateway port using the existing HyperliquidClient
with minimal caching for real-time data.
"""

import logging
import re
from datetime import datetime, UTC
from decimal import Decimal

from app.domain.entities.perpetual.liquidation import Liquidation
from app.domain.entities.perpetual.market import PerpMarket
from app.domain.entities.perpetual.position import Position
from app.domain.exceptions.perpetual import (
    HyperliquidAPIError,
    InvalidAddressError,
    SymbolNotFoundError,
)
from app.domain.ports.perpetual_gateway import PerpetualGateway
from app.domain.value_objects.perpetual.funding_rate import FundingRate
from app.domain.value_objects.perpetual.order_book import OrderBook
from app.domain.value_objects.perpetual.risk_metrics import (
    RiskMetrics,
    assess_risk_level,
)
from app.infrastructure.adapters.external.hyperliquid_client import (
    HyperliquidClient,
    FundingRate as ClientFundingRate,
    Liquidation as ClientLiquidation,
    OrderBook as ClientOrderBook,
    Position as ClientPosition,
)
from app.infrastructure.cache.external_api_cache import ExternalAPICache

logger = logging.getLogger(__name__)

# Ethereum address regex pattern
ETH_ADDRESS_PATTERN = re.compile(r"^0x[a-fA-F0-9]{40}$")


class HyperliquidAdapter(PerpetualGateway):
    """
    Hyperliquid implementation of PerpetualGateway.

    Uses minimal caching due to real-time nature of trading data:
    - Markets: 5s cache
    - Funding: 30s cache
    - Order book: No cache
    - Positions: 10s cache
    """

    DEFAULT_MARKET_CACHE_TTL = 5  # 5 seconds
    DEFAULT_FUNDING_CACHE_TTL = 30  # 30 seconds
    DEFAULT_POSITION_CACHE_TTL = 10  # 10 seconds
    DEFAULT_LIQUIDATION_CACHE_TTL = 60  # 1 minute
    DEFAULT_MAINTENANCE_MARGIN = Decimal("0.005")  # 0.5%

    def __init__(
        self,
        client: HyperliquidClient,
        cache: ExternalAPICache,
        market_cache_ttl: int = DEFAULT_MARKET_CACHE_TTL,
        funding_cache_ttl: int = DEFAULT_FUNDING_CACHE_TTL,
        position_cache_ttl: int = DEFAULT_POSITION_CACHE_TTL,
        liquidation_cache_ttl: int = DEFAULT_LIQUIDATION_CACHE_TTL,
    ):
        """Initialize HyperliquidAdapter."""
        self._client = client
        self._cache = cache
        self._market_cache_ttl = market_cache_ttl
        self._funding_cache_ttl = funding_cache_ttl
        self._position_cache_ttl = position_cache_ttl
        self._liquidation_cache_ttl = liquidation_cache_ttl

    async def get_markets(self) -> list[PerpMarket]:
        """Get all perpetual markets with caching."""
        cache_key_params = {"type": "markets"}

        cached = await self._cache.get("hyperliquid", "markets", **cache_key_params)
        if cached:
            logger.debug("Cache hit for Hyperliquid markets")
            return [PerpMarket.from_dict(m) for m in cached]

        try:
            # Get meta and asset contexts from API
            response = await self._client._client.post(
                "/info", json={"type": "metaAndAssetCtxs"}
            )
            response.raise_for_status()
            data = response.json()

            markets = self._transform_markets(data)

            await self._cache.set(
                "hyperliquid",
                "markets",
                [m.to_dict() for m in markets],
                ttl=self._market_cache_ttl,
                **cache_key_params,
            )

            logger.debug(f"Fetched {len(markets)} Hyperliquid markets")
            return markets

        except Exception as e:
            logger.error(f"Error fetching Hyperliquid markets: {e}")
            raise HyperliquidAPIError(str(e)) from e

    async def get_order_book(self, symbol: str, depth: int = 20) -> OrderBook:
        """Get order book (no caching - real-time)."""
        try:
            raw = await self._client.get_order_book(symbol, depth)
            return self._transform_order_book(raw)
        except ValueError as e:
            raise SymbolNotFoundError(symbol) from e
        except Exception as e:
            logger.error(f"Error fetching order book: {e}")
            raise HyperliquidAPIError(str(e)) from e

    async def get_funding_rate(self, symbol: str) -> FundingRate:
        """Get funding rate for a symbol with caching."""
        cache_key_params = {"symbol": symbol}

        cached = await self._cache.get("hyperliquid", "funding", **cache_key_params)
        if cached:
            return FundingRate.from_dict(cached)

        try:
            raw = await self._client.get_funding_rate(symbol)
            funding = self._transform_funding_rate(raw)

            await self._cache.set(
                "hyperliquid",
                "funding",
                funding.to_dict(),
                ttl=self._funding_cache_ttl,
                **cache_key_params,
            )

            return funding

        except ValueError as e:
            raise SymbolNotFoundError(symbol) from e
        except Exception as e:
            logger.error(f"Error fetching funding rate: {e}")
            raise HyperliquidAPIError(str(e)) from e

    async def get_funding_rates(self) -> list[FundingRate]:
        """Get all funding rates."""
        cache_key_params = {"type": "all_funding"}

        cached = await self._cache.get("hyperliquid", "funding_all", **cache_key_params)
        if cached:
            return [FundingRate.from_dict(f) for f in cached]

        try:
            # Get markets first to get all symbols and their funding
            markets = await self.get_markets()

            funding_rates = []
            for market in markets:
                funding_rate = FundingRate(
                    symbol=market.symbol,
                    rate=market.funding_rate,
                    annualized_rate=market.funding_rate * 3 * 365,  # 8h -> annual
                    next_funding_time=datetime.now(UTC),  # Would need actual data
                    timestamp=datetime.now(UTC),
                )
                funding_rates.append(funding_rate)

            await self._cache.set(
                "hyperliquid",
                "funding_all",
                [f.to_dict() for f in funding_rates],
                ttl=self._funding_cache_ttl,
                **cache_key_params,
            )

            return funding_rates

        except Exception as e:
            logger.error(f"Error fetching funding rates: {e}")
            raise HyperliquidAPIError(str(e)) from e

    async def get_liquidations(
        self,
        symbol: str | None = None,
        hours: int = 24,
    ) -> list[Liquidation]:
        """Get recent liquidations."""
        cache_key_params = {"symbol": symbol or "all", "hours": hours}

        cached = await self._cache.get(
            "hyperliquid", "liquidations", **cache_key_params
        )
        if cached:
            return [Liquidation.from_dict(l) for l in cached]

        try:
            raw_liqs = await self._client.get_liquidations(symbol, hours)
            liquidations = [self._transform_liquidation(l) for l in raw_liqs]

            await self._cache.set(
                "hyperliquid",
                "liquidations",
                [l.to_dict() for l in liquidations],
                ttl=self._liquidation_cache_ttl,
                **cache_key_params,
            )

            return liquidations

        except Exception as e:
            logger.error(f"Error fetching liquidations: {e}")
            raise HyperliquidAPIError(str(e)) from e

    async def get_positions(self, address: str) -> list[Position]:
        """Get user positions."""
        # Validate address format
        if not ETH_ADDRESS_PATTERN.match(address):
            raise InvalidAddressError(address, "Invalid Ethereum address format")

        cache_key_params = {"address": address}

        cached = await self._cache.get("hyperliquid", "positions", **cache_key_params)
        if cached:
            return [Position.from_dict(p) for p in cached]

        try:
            raw_positions = await self._client.get_user_positions(address)
            positions = [self._transform_position(p) for p in raw_positions]

            await self._cache.set(
                "hyperliquid",
                "positions",
                [p.to_dict() for p in positions],
                ttl=self._position_cache_ttl,
                **cache_key_params,
            )

            return positions

        except Exception as e:
            logger.error(f"Error fetching positions: {e}")
            raise HyperliquidAPIError(str(e)) from e

    def calculate_liquidation_price(
        self,
        entry_price: Decimal,
        leverage: Decimal,
        side: str,
        maintenance_margin: Decimal = DEFAULT_MAINTENANCE_MARGIN,
    ) -> Decimal:
        """Calculate liquidation price for a position."""
        if leverage <= 0:
            return Decimal("0")

        # Liquidation occurs when position loss = initial margin - maintenance margin
        # For long: liq_price = entry * (1 - (1/leverage) + maintenance_margin)
        # For short: liq_price = entry * (1 + (1/leverage) - maintenance_margin)

        margin_fraction = Decimal("1") / leverage

        if side.lower() == "long":
            liq_price = entry_price * (1 - margin_fraction + maintenance_margin)
        else:
            liq_price = entry_price * (1 + margin_fraction - maintenance_margin)

        return liq_price.quantize(Decimal("0.01"))

    def calculate_risk_metrics(
        self,
        entry_price: Decimal,
        size: Decimal,
        leverage: Decimal,
        side: str,
        account_balance: Decimal | None = None,
    ) -> RiskMetrics:
        """Calculate comprehensive risk metrics."""
        liq_price = self.calculate_liquidation_price(entry_price, leverage, side)

        position_value = entry_price * size
        margin_required = position_value / leverage
        max_loss = margin_required

        # Calculate distance to liquidation
        if side.lower() == "long":
            distance_pct = (entry_price - liq_price) / entry_price * 100
        else:
            distance_pct = (liq_price - entry_price) / entry_price * 100

        risk_level = assess_risk_level(distance_pct)

        return RiskMetrics(
            liquidation_price=liq_price,
            margin_required=margin_required.quantize(Decimal("0.01")),
            max_loss=max_loss.quantize(Decimal("0.01")),
            distance_to_liquidation_pct=distance_pct.quantize(Decimal("0.01")),
            risk_level=risk_level,
        )

    # =========================================================================
    # Transformation Methods
    # =========================================================================

    def _transform_markets(self, data: list) -> list[PerpMarket]:
        """Transform API response to domain markets."""
        markets = []

        if len(data) < 2:
            return markets

        meta = data[0]  # Contains universe info
        asset_ctxs = data[1]  # Contains current market data

        universe = meta.get("universe", [])

        for i, asset in enumerate(asset_ctxs):
            if i >= len(universe):
                continue

            symbol = universe[i].get("name", f"UNKNOWN_{i}")

            mark_price = Decimal(str(asset.get("markPx", "0")))
            oracle_price = Decimal(str(asset.get("oraclePx", "0")))
            funding = Decimal(str(asset.get("funding", "0")))
            open_interest = Decimal(str(asset.get("openInterest", "0")))

            # Volume from 24h data if available
            day_ntl_vlm = Decimal(str(asset.get("dayNtlVlm", "0")))
            prev_day_px = Decimal(str(asset.get("prevDayPx", "0")))

            # Price change
            price_change = Decimal("0")
            if prev_day_px > 0:
                price_change = (mark_price - prev_day_px) / prev_day_px * 100

            max_leverage = universe[i].get("maxLeverage", 50)
            if isinstance(max_leverage, float):
                max_leverage = int(max_leverage)

            markets.append(
                PerpMarket(
                    symbol=symbol,
                    mark_price=mark_price,
                    index_price=oracle_price,
                    funding_rate=funding,
                    open_interest=open_interest,
                    volume_24h=day_ntl_vlm,
                    price_change_24h=price_change,
                    max_leverage=max_leverage,
                )
            )

        return markets

    def _transform_order_book(self, raw: ClientOrderBook) -> OrderBook:
        """Transform client order book to domain value object."""
        bids = tuple((Decimal(str(p)), Decimal(str(s))) for p, s in raw.bids)
        asks = tuple((Decimal(str(p)), Decimal(str(s))) for p, s in raw.asks)

        return OrderBook(
            symbol=raw.symbol,
            bids=bids,
            asks=asks,
            timestamp=datetime.fromtimestamp(raw.timestamp / 1000),
        )

    def _transform_funding_rate(self, raw: ClientFundingRate) -> FundingRate:
        """Transform client funding rate to domain value object."""
        rate = Decimal(str(raw.funding_rate))
        # Annualize: 8h rate * 3 * 365 days
        annualized = rate * 3 * 365

        return FundingRate(
            symbol=raw.symbol,
            rate=rate,
            annualized_rate=annualized,
            next_funding_time=datetime.fromtimestamp(raw.next_funding_time / 1000),
            timestamp=datetime.fromtimestamp(raw.timestamp / 1000),
        )

    def _transform_liquidation(self, raw: ClientLiquidation) -> Liquidation:
        """Transform client liquidation to domain entity."""
        return Liquidation(
            symbol=raw.symbol,
            side=raw.side,
            size=Decimal(str(raw.size)),
            price=Decimal(str(raw.price)),
            timestamp=datetime.fromtimestamp(raw.timestamp / 1000),
        )

    def _transform_position(self, raw: ClientPosition) -> Position:
        """Transform client position to domain entity."""
        return Position(
            symbol=raw.symbol,
            side=raw.side,
            size=Decimal(str(raw.size)),
            entry_price=Decimal(str(raw.entry_price)),
            mark_price=Decimal(str(raw.mark_price)),
            unrealized_pnl=Decimal(str(raw.unrealized_pnl)),
            leverage=Decimal(str(raw.leverage)),
            liquidation_price=Decimal(str(raw.liquidation_price)),
            margin_ratio=Decimal("0"),  # Would need additional calculation
        )
