"""
Instrumented Hyperliquid Client with Full Telemetry.

Provides complete observability for Hyperliquid API calls:
- Request timing and latency tracking
- Error categorization and rate tracking
- Distributed tracing with span propagation
- Perpetuals trading metrics
"""

from typing import Optional

from app.infrastructure.adapters.external.hyperliquid_client import (
    HyperliquidClient,
    OrderBook,
    FundingRate,
    Liquidation,
    Position,
    Order,
)
from app.infrastructure.telemetry.api_telemetry import (
    APITelemetry,
    APIStatus,
    get_api_telemetry,
)
from app.infrastructure.telemetry.tracing import (
    TracingService,
    SpanKind,
    SpanStatus,
    get_tracing_service,
)


class InstrumentedHyperliquidClient(HyperliquidClient):
    """
    Hyperliquid client with full telemetry instrumentation.

    Usage:
        client = InstrumentedHyperliquidClient()

        # All calls automatically instrumented
        order_book = await client.get_order_book("ETH-PERP")

        # Get metrics
        telemetry = get_api_telemetry()
        metrics = telemetry.get_metrics("hyperliquid")
    """

    API_NAME = "hyperliquid"

    def __init__(
        self,
        api_key: str | None = None,
        api_secret: str | None = None,
        testnet: bool = False,
        telemetry: Optional[APITelemetry] = None,
        tracing: Optional[TracingService] = None,
    ):
        super().__init__(api_key, api_secret, testnet)
        self._telemetry = telemetry or get_api_telemetry()
        self._tracing = tracing or get_tracing_service()

    async def get_order_book(self, symbol: str, depth: int = 20) -> OrderBook:
        """Get order book with telemetry."""
        ctx = self._telemetry.start_call(
            api=self.API_NAME,
            operation="get_order_book",
            symbol=symbol,
            depth=depth,
        )

        with self._tracing.start_span(
            name=f"{self.API_NAME}.get_order_book",
            kind=SpanKind.CLIENT,
            attributes={
                "api.name": self.API_NAME,
                "api.operation": "get_order_book",
                "symbol": symbol,
                "depth": depth,
            },
        ) as span:
            try:
                result = await super().get_order_book(symbol, depth)

                ctx.complete(status=APIStatus.SUCCESS, status_code=200)
                span.set_status(SpanStatus.OK)
                span.set_attribute("response.bid_count", len(result.bids))
                span.set_attribute("response.ask_count", len(result.asks))

                return result

            except Exception as e:
                error_type = self._classify_error(e)
                ctx.complete(
                    status=error_type,
                    error_message=str(e),
                    error_type=type(e).__name__,
                )
                span.set_status(SpanStatus.ERROR, str(e))
                raise

            finally:
                await self._telemetry.record(ctx)

    async def get_funding_rate(self, symbol: str) -> FundingRate:
        """Get funding rate with telemetry."""
        ctx = self._telemetry.start_call(
            api=self.API_NAME,
            operation="get_funding_rate",
            symbol=symbol,
        )

        with self._tracing.start_span(
            name=f"{self.API_NAME}.get_funding_rate",
            kind=SpanKind.CLIENT,
            attributes={
                "api.name": self.API_NAME,
                "api.operation": "get_funding_rate",
                "symbol": symbol,
            },
        ) as span:
            try:
                result = await super().get_funding_rate(symbol)

                ctx.complete(status=APIStatus.SUCCESS, status_code=200)
                span.set_status(SpanStatus.OK)
                span.set_attribute("response.funding_rate", result.funding_rate)

                return result

            except Exception as e:
                error_type = self._classify_error(e)
                ctx.complete(
                    status=error_type,
                    error_message=str(e),
                    error_type=type(e).__name__,
                )
                span.set_status(SpanStatus.ERROR, str(e))
                raise

            finally:
                await self._telemetry.record(ctx)

    async def get_liquidations(
        self,
        symbol: str | None = None,
        hours: int = 24,
    ) -> list[Liquidation]:
        """Get liquidations with telemetry."""
        ctx = self._telemetry.start_call(
            api=self.API_NAME,
            operation="get_liquidations",
            symbol=symbol or "all",
            hours=hours,
        )

        with self._tracing.start_span(
            name=f"{self.API_NAME}.get_liquidations",
            kind=SpanKind.CLIENT,
            attributes={
                "api.name": self.API_NAME,
                "api.operation": "get_liquidations",
                "symbol": symbol or "all",
                "hours": hours,
            },
        ) as span:
            try:
                result = await super().get_liquidations(symbol, hours)

                ctx.complete(status=APIStatus.SUCCESS, status_code=200)
                span.set_status(SpanStatus.OK)
                span.set_attribute("response.liquidation_count", len(result))

                return result

            except Exception as e:
                error_type = self._classify_error(e)
                ctx.complete(
                    status=error_type,
                    error_message=str(e),
                    error_type=type(e).__name__,
                )
                span.set_status(SpanStatus.ERROR, str(e))
                raise

            finally:
                await self._telemetry.record(ctx)

    async def get_user_positions(self, address: str) -> list[Position]:
        """Get user positions with telemetry."""
        ctx = self._telemetry.start_call(
            api=self.API_NAME,
            operation="get_user_positions",
            address=address[:10],
        )

        with self._tracing.start_span(
            name=f"{self.API_NAME}.get_user_positions",
            kind=SpanKind.CLIENT,
            attributes={
                "api.name": self.API_NAME,
                "api.operation": "get_user_positions",
                "address": address[:10] + "...",
            },
        ) as span:
            try:
                result = await super().get_user_positions(address)

                ctx.complete(status=APIStatus.SUCCESS, status_code=200)
                span.set_status(SpanStatus.OK)
                span.set_attribute("response.position_count", len(result))

                return result

            except Exception as e:
                error_type = self._classify_error(e)
                ctx.complete(
                    status=error_type,
                    error_message=str(e),
                    error_type=type(e).__name__,
                )
                span.set_status(SpanStatus.ERROR, str(e))
                raise

            finally:
                await self._telemetry.record(ctx)

    async def place_order(
        self,
        symbol: str,
        side: str,
        size: float,
        price: float | None = None,
        reduce_only: bool = False,
    ) -> Order:
        """Place order with telemetry."""
        ctx = self._telemetry.start_call(
            api=self.API_NAME,
            operation="place_order",
            symbol=symbol,
            side=side,
        )

        with self._tracing.start_span(
            name=f"{self.API_NAME}.place_order",
            kind=SpanKind.CLIENT,
            attributes={
                "api.name": self.API_NAME,
                "api.operation": "place_order",
                "symbol": symbol,
                "side": side,
                "size": size,
                "order_type": "limit" if price else "market",
            },
        ) as span:
            try:
                result = await super().place_order(
                    symbol, side, size, price, reduce_only
                )

                ctx.complete(status=APIStatus.SUCCESS, status_code=200)
                span.set_status(SpanStatus.OK)
                span.set_attribute("response.order_id", result.order_id)

                return result

            except Exception as e:
                error_type = self._classify_error(e)
                ctx.complete(
                    status=error_type,
                    error_message=str(e),
                    error_type=type(e).__name__,
                )
                span.set_status(SpanStatus.ERROR, str(e))
                raise

            finally:
                await self._telemetry.record(ctx)

    async def cancel_order(self, order_id: str, symbol: str) -> bool:
        """Cancel order with telemetry."""
        ctx = self._telemetry.start_call(
            api=self.API_NAME,
            operation="cancel_order",
            order_id=order_id,
            symbol=symbol,
        )

        with self._tracing.start_span(
            name=f"{self.API_NAME}.cancel_order",
            kind=SpanKind.CLIENT,
            attributes={
                "api.name": self.API_NAME,
                "api.operation": "cancel_order",
                "order_id": order_id,
                "symbol": symbol,
            },
        ) as span:
            try:
                result = await super().cancel_order(order_id, symbol)

                ctx.complete(status=APIStatus.SUCCESS, status_code=200)
                span.set_status(SpanStatus.OK)
                span.set_attribute("response.cancelled", result)

                return result

            except Exception as e:
                error_type = self._classify_error(e)
                ctx.complete(
                    status=error_type,
                    error_message=str(e),
                    error_type=type(e).__name__,
                )
                span.set_status(SpanStatus.ERROR, str(e))
                raise

            finally:
                await self._telemetry.record(ctx)

    def _classify_error(self, error: Exception) -> APIStatus:
        """Classify error type for telemetry."""
        import httpx

        if isinstance(error, httpx.TimeoutException):
            return APIStatus.TIMEOUT

        if isinstance(error, httpx.HTTPStatusError):
            if error.response.status_code == 429:
                return APIStatus.RATE_LIMITED
            if error.response.status_code in (401, 403):
                return APIStatus.AUTH_FAILURE

        return APIStatus.ERROR
