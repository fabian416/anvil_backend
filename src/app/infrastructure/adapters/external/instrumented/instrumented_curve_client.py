"""
Instrumented Curve Client with Full Telemetry.

Provides complete observability for Curve API calls:
- Request timing and latency tracking
- Error categorization and rate tracking
- Distributed tracing with span propagation
- Stablecoin swap metrics
"""

from typing import Optional

from app.infrastructure.adapters.external.curve_client import (
    CurveClient,
    CurvePool,
    PoolAPY,
    SwapQuote,
    GaugeData,
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


class InstrumentedCurveClient(CurveClient):
    """
    Curve client with full telemetry instrumentation.
    
    Usage:
        client = InstrumentedCurveClient(chain="ethereum")
        
        # All calls automatically instrumented
        pools = await client.get_pools()
        
        # Get metrics
        telemetry = get_api_telemetry()
        metrics = telemetry.get_metrics("curve")
    """
    
    API_NAME = "curve"
    
    def __init__(
        self,
        chain: str = "ethereum",
        telemetry: Optional[APITelemetry] = None,
        tracing: Optional[TracingService] = None,
    ):
        super().__init__(chain)
        self._telemetry = telemetry or get_api_telemetry()
        self._tracing = tracing or get_tracing_service()
    
    async def get_pools(self) -> list[CurvePool]:
        """Get all pools with telemetry."""
        ctx = self._telemetry.start_call(
            api=self.API_NAME,
            operation="get_pools",
            chain=self._chain,
        )
        
        with self._tracing.start_span(
            name=f"{self.API_NAME}.get_pools",
            kind=SpanKind.CLIENT,
            attributes={
                "api.name": self.API_NAME,
                "api.operation": "get_pools",
                "chain": self._chain,
            },
        ) as span:
            try:
                result = await super().get_pools()
                
                ctx.complete(status=APIStatus.SUCCESS, status_code=200)
                span.set_status(SpanStatus.OK)
                span.set_attribute("response.pool_count", len(result))
                
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
    
    async def get_pool_data(self, pool_address: str) -> CurvePool:
        """Get pool data with telemetry."""
        ctx = self._telemetry.start_call(
            api=self.API_NAME,
            operation="get_pool_data",
            pool=pool_address[:10],
        )
        
        with self._tracing.start_span(
            name=f"{self.API_NAME}.get_pool_data",
            kind=SpanKind.CLIENT,
            attributes={
                "api.name": self.API_NAME,
                "api.operation": "get_pool_data",
                "pool_address": pool_address,
            },
        ) as span:
            try:
                result = await super().get_pool_data(pool_address)
                
                ctx.complete(status=APIStatus.SUCCESS, status_code=200)
                span.set_status(SpanStatus.OK)
                span.set_attribute("response.tvl_usd", result.tvl_usd)
                
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
    
    async def get_pool_apy(self, pool_address: str) -> PoolAPY:
        """Get pool APY with telemetry."""
        ctx = self._telemetry.start_call(
            api=self.API_NAME,
            operation="get_pool_apy",
            pool=pool_address[:10],
        )
        
        with self._tracing.start_span(
            name=f"{self.API_NAME}.get_pool_apy",
            kind=SpanKind.CLIENT,
            attributes={
                "api.name": self.API_NAME,
                "api.operation": "get_pool_apy",
                "pool_address": pool_address,
            },
        ) as span:
            try:
                result = await super().get_pool_apy(pool_address)
                
                ctx.complete(status=APIStatus.SUCCESS, status_code=200)
                span.set_status(SpanStatus.OK)
                span.set_attribute("response.total_apy", result.total_apy)
                
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
    
    async def get_swap_quote(
        self,
        from_token: str,
        to_token: str,
        amount: str,
    ) -> SwapQuote:
        """Get swap quote with telemetry."""
        ctx = self._telemetry.start_call(
            api=self.API_NAME,
            operation="get_swap_quote",
            from_token=from_token[:10],
            to_token=to_token[:10],
        )
        
        with self._tracing.start_span(
            name=f"{self.API_NAME}.get_swap_quote",
            kind=SpanKind.CLIENT,
            attributes={
                "api.name": self.API_NAME,
                "api.operation": "get_swap_quote",
                "from_token": from_token,
                "to_token": to_token,
            },
        ) as span:
            try:
                result = await super().get_swap_quote(from_token, to_token, amount)
                
                ctx.complete(status=APIStatus.SUCCESS, status_code=200)
                span.set_status(SpanStatus.OK)
                span.set_attribute("response.exchange_rate", result.exchange_rate)
                
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
    
    async def get_gauges(self) -> list[GaugeData]:
        """Get gauges with telemetry."""
        ctx = self._telemetry.start_call(
            api=self.API_NAME,
            operation="get_gauges",
            chain=self._chain,
        )
        
        with self._tracing.start_span(
            name=f"{self.API_NAME}.get_gauges",
            kind=SpanKind.CLIENT,
            attributes={
                "api.name": self.API_NAME,
                "api.operation": "get_gauges",
                "chain": self._chain,
            },
        ) as span:
            try:
                result = await super().get_gauges()
                
                ctx.complete(status=APIStatus.SUCCESS, status_code=200)
                span.set_status(SpanStatus.OK)
                span.set_attribute("response.gauge_count", len(result))
                
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
    
    async def get_tvl(self) -> dict[str, float]:
        """Get TVL with telemetry."""
        ctx = self._telemetry.start_call(
            api=self.API_NAME,
            operation="get_tvl",
            chain=self._chain,
        )
        
        with self._tracing.start_span(
            name=f"{self.API_NAME}.get_tvl",
            kind=SpanKind.CLIENT,
            attributes={
                "api.name": self.API_NAME,
                "api.operation": "get_tvl",
                "chain": self._chain,
            },
        ) as span:
            try:
                result = await super().get_tvl()
                
                ctx.complete(status=APIStatus.SUCCESS, status_code=200)
                span.set_status(SpanStatus.OK)
                span.set_attribute("response.total_tvl", result.get("total", 0))
                
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
    
    async def get_factory_pools(self) -> list[CurvePool]:
        """Get factory pools with telemetry."""
        ctx = self._telemetry.start_call(
            api=self.API_NAME,
            operation="get_factory_pools",
            chain=self._chain,
        )
        
        with self._tracing.start_span(
            name=f"{self.API_NAME}.get_factory_pools",
            kind=SpanKind.CLIENT,
            attributes={
                "api.name": self.API_NAME,
                "api.operation": "get_factory_pools",
                "chain": self._chain,
            },
        ) as span:
            try:
                result = await super().get_factory_pools()
                
                ctx.complete(status=APIStatus.SUCCESS, status_code=200)
                span.set_status(SpanStatus.OK)
                span.set_attribute("response.pool_count", len(result))
                
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
    
    async def get_crv_price(self) -> float:
        """Get CRV price with telemetry."""
        ctx = self._telemetry.start_call(
            api=self.API_NAME,
            operation="get_crv_price",
        )
        
        with self._tracing.start_span(
            name=f"{self.API_NAME}.get_crv_price",
            kind=SpanKind.CLIENT,
            attributes={
                "api.name": self.API_NAME,
                "api.operation": "get_crv_price",
            },
        ) as span:
            try:
                result = await super().get_crv_price()
                
                ctx.complete(status=APIStatus.SUCCESS, status_code=200)
                span.set_status(SpanStatus.OK)
                span.set_attribute("response.crv_price", result)
                
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
