"""
Instrumented CoinGecko Client with Full Telemetry.

Provides complete observability for CoinGecko API calls:
- Request timing and latency tracking
- Error categorization and rate tracking
- Rate limit detection
- Distributed tracing with span propagation
- Cost estimation
"""

from dataclasses import asdict
from typing import Any, Optional

from app.infrastructure.adapters.external.coingecko_client import (
    CoinGeckoClient,
    Price,
    MarketChart,
    CoinDetails,
    TrendingCoin,
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


class InstrumentedCoinGeckoClient(CoinGeckoClient):
    """
    CoinGecko client with full telemetry instrumentation.
    
    Usage:
        client = InstrumentedCoinGeckoClient(api_key="your_key")
        
        # All calls automatically instrumented
        price = await client.get_price("ethereum")
        
        # Get metrics
        telemetry = get_api_telemetry()
        metrics = telemetry.get_metrics("coingecko")
    """
    
    API_NAME = "coingecko"
    
    def __init__(
        self,
        api_key: str | None = None,
        telemetry: Optional[APITelemetry] = None,
        tracing: Optional[TracingService] = None,
    ):
        """
        Initialize instrumented CoinGecko client.
        
        Args:
            api_key: CoinGecko API key
            telemetry: API telemetry instance
            tracing: Tracing service instance
        """
        super().__init__(api_key)
        self._telemetry = telemetry or get_api_telemetry()
        self._tracing = tracing or get_tracing_service()
    
    async def get_price(
        self,
        coin_id: str,
        vs_currency: str = "usd",
        include_market_cap: bool = True,
        include_24hr_vol: bool = True,
        include_24hr_change: bool = True,
    ) -> Price:
        """Get current price with telemetry."""
        ctx = self._telemetry.start_call(
            api=self.API_NAME,
            operation="get_price",
            coin_id=coin_id,
            vs_currency=vs_currency,
        )
        
        with self._tracing.start_span(
            name=f"{self.API_NAME}.get_price",
            kind=SpanKind.CLIENT,
            attributes={
                "api.name": self.API_NAME,
                "api.operation": "get_price",
                "coin_id": coin_id,
                "vs_currency": vs_currency,
            },
        ) as span:
            try:
                result = await super().get_price(
                    coin_id=coin_id,
                    vs_currency=vs_currency,
                    include_market_cap=include_market_cap,
                    include_24hr_vol=include_24hr_vol,
                    include_24hr_change=include_24hr_change,
                )
                
                ctx.complete(status=APIStatus.SUCCESS, status_code=200)
                span.set_status(SpanStatus.OK)
                span.set_attribute("response.price_usd", result.usd)
                
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
    
    async def get_prices_bulk(
        self,
        coin_ids: list[str],
        vs_currencies: list[str] | None = None,
    ) -> list[Price]:
        """Get prices for multiple coins with telemetry."""
        ctx = self._telemetry.start_call(
            api=self.API_NAME,
            operation="get_prices_bulk",
            coin_count=len(coin_ids),
        )
        
        with self._tracing.start_span(
            name=f"{self.API_NAME}.get_prices_bulk",
            kind=SpanKind.CLIENT,
            attributes={
                "api.name": self.API_NAME,
                "api.operation": "get_prices_bulk",
                "coin_count": len(coin_ids),
            },
        ) as span:
            try:
                result = await super().get_prices_bulk(
                    coin_ids=coin_ids,
                    vs_currencies=vs_currencies,
                )
                
                ctx.complete(status=APIStatus.SUCCESS, status_code=200)
                span.set_status(SpanStatus.OK)
                span.set_attribute("response.price_count", len(result))
                
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
    
    async def get_market_chart(
        self,
        coin_id: str,
        vs_currency: str = "usd",
        days: int = 30,
    ) -> MarketChart:
        """Get market chart data with telemetry."""
        ctx = self._telemetry.start_call(
            api=self.API_NAME,
            operation="get_market_chart",
            coin_id=coin_id,
            days=days,
        )
        
        with self._tracing.start_span(
            name=f"{self.API_NAME}.get_market_chart",
            kind=SpanKind.CLIENT,
            attributes={
                "api.name": self.API_NAME,
                "api.operation": "get_market_chart",
                "coin_id": coin_id,
                "days": days,
            },
        ) as span:
            try:
                result = await super().get_market_chart(
                    coin_id=coin_id,
                    vs_currency=vs_currency,
                    days=days,
                )
                
                ctx.complete(status=APIStatus.SUCCESS, status_code=200)
                span.set_status(SpanStatus.OK)
                span.set_attribute("response.data_points", len(result.prices))
                
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
    
    async def get_coin_details(self, coin_id: str) -> CoinDetails:
        """Get coin details with telemetry."""
        ctx = self._telemetry.start_call(
            api=self.API_NAME,
            operation="get_coin_details",
            coin_id=coin_id,
        )
        
        with self._tracing.start_span(
            name=f"{self.API_NAME}.get_coin_details",
            kind=SpanKind.CLIENT,
            attributes={
                "api.name": self.API_NAME,
                "api.operation": "get_coin_details",
                "coin_id": coin_id,
            },
        ) as span:
            try:
                result = await super().get_coin_details(coin_id=coin_id)
                
                ctx.complete(status=APIStatus.SUCCESS, status_code=200)
                span.set_status(SpanStatus.OK)
                span.set_attribute("response.coin_name", result.name)
                
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
    
    async def get_trending_coins(self) -> list[TrendingCoin]:
        """Get trending coins with telemetry."""
        ctx = self._telemetry.start_call(
            api=self.API_NAME,
            operation="get_trending_coins",
        )
        
        with self._tracing.start_span(
            name=f"{self.API_NAME}.get_trending_coins",
            kind=SpanKind.CLIENT,
            attributes={
                "api.name": self.API_NAME,
                "api.operation": "get_trending_coins",
            },
        ) as span:
            try:
                result = await super().get_trending_coins()
                
                ctx.complete(status=APIStatus.SUCCESS, status_code=200)
                span.set_status(SpanStatus.OK)
                span.set_attribute("response.coin_count", len(result))
                
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
    
    async def get_global_data(self) -> dict[str, Any]:
        """Get global market statistics with telemetry."""
        ctx = self._telemetry.start_call(
            api=self.API_NAME,
            operation="get_global_data",
        )
        
        with self._tracing.start_span(
            name=f"{self.API_NAME}.get_global_data",
            kind=SpanKind.CLIENT,
            attributes={
                "api.name": self.API_NAME,
                "api.operation": "get_global_data",
            },
        ) as span:
            try:
                result = await super().get_global_data()
                
                ctx.complete(status=APIStatus.SUCCESS, status_code=200)
                span.set_status(SpanStatus.OK)
                span.set_attribute("response.total_market_cap", result.get("total_market_cap", 0))
                
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
