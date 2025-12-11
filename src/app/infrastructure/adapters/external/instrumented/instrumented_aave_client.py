"""
Instrumented Aave Client with Full Telemetry.

Provides complete observability for Aave API calls:
- Request timing and latency tracking
- Error categorization and rate tracking
- Distributed tracing with span propagation
- Lending metrics tracking
"""

from typing import Any, Optional

from app.infrastructure.adapters.external.aave_client import (
    AaveClient,
    MarketData,
    UserPosition,
    ReserveData,
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


class InstrumentedAaveClient(AaveClient):
    """
    Aave client with full telemetry instrumentation.
    
    Usage:
        client = InstrumentedAaveClient(api_key="...", chain="ethereum")
        
        # All calls automatically instrumented
        markets = await client.get_market_data()
        
        # Get metrics
        telemetry = get_api_telemetry()
        metrics = telemetry.get_metrics("aave")
    """
    
    API_NAME = "aave"
    
    def __init__(
        self,
        api_key: str | None = None,
        chain: str = "ethereum",
        telemetry: Optional[APITelemetry] = None,
        tracing: Optional[TracingService] = None,
    ):
        super().__init__(api_key, chain)
        self._telemetry = telemetry or get_api_telemetry()
        self._tracing = tracing or get_tracing_service()
    
    async def get_market_data(self, asset: str | None = None) -> list[MarketData]:
        """Get market data with telemetry."""
        ctx = self._telemetry.start_call(
            api=self.API_NAME,
            operation="get_market_data",
            asset=asset or "all",
            chain=self._chain,
        )
        
        with self._tracing.start_span(
            name=f"{self.API_NAME}.get_market_data",
            kind=SpanKind.CLIENT,
            attributes={
                "api.name": self.API_NAME,
                "api.operation": "get_market_data",
                "asset": asset or "all",
                "chain": self._chain,
            },
        ) as span:
            try:
                result = await super().get_market_data(asset)
                
                ctx.complete(status=APIStatus.SUCCESS, status_code=200)
                span.set_status(SpanStatus.OK)
                span.set_attribute("response.market_count", len(result))
                
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
    
    async def get_user_position(self, user_address: str) -> UserPosition:
        """Get user position with telemetry."""
        ctx = self._telemetry.start_call(
            api=self.API_NAME,
            operation="get_user_position",
            user=user_address[:10],
        )
        
        with self._tracing.start_span(
            name=f"{self.API_NAME}.get_user_position",
            kind=SpanKind.CLIENT,
            attributes={
                "api.name": self.API_NAME,
                "api.operation": "get_user_position",
                "user_address": user_address[:10] + "...",
            },
        ) as span:
            try:
                result = await super().get_user_position(user_address)
                
                ctx.complete(status=APIStatus.SUCCESS, status_code=200)
                span.set_status(SpanStatus.OK)
                span.set_attribute("response.health_factor", result.health_factor)
                
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
    
    async def get_reserve_data(self, asset: str) -> ReserveData:
        """Get reserve data with telemetry."""
        ctx = self._telemetry.start_call(
            api=self.API_NAME,
            operation="get_reserve_data",
            asset=asset,
        )
        
        with self._tracing.start_span(
            name=f"{self.API_NAME}.get_reserve_data",
            kind=SpanKind.CLIENT,
            attributes={
                "api.name": self.API_NAME,
                "api.operation": "get_reserve_data",
                "asset": asset,
            },
        ) as span:
            try:
                result = await super().get_reserve_data(asset)
                
                ctx.complete(status=APIStatus.SUCCESS, status_code=200)
                span.set_status(SpanStatus.OK)
                span.set_attribute("response.symbol", result.symbol)
                
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
    
    async def get_protocol_stats(self) -> dict[str, Any]:
        """Get protocol stats with telemetry."""
        ctx = self._telemetry.start_call(
            api=self.API_NAME,
            operation="get_protocol_stats",
            chain=self._chain,
        )
        
        with self._tracing.start_span(
            name=f"{self.API_NAME}.get_protocol_stats",
            kind=SpanKind.CLIENT,
            attributes={
                "api.name": self.API_NAME,
                "api.operation": "get_protocol_stats",
                "chain": self._chain,
            },
        ) as span:
            try:
                result = await super().get_protocol_stats()
                
                ctx.complete(status=APIStatus.SUCCESS, status_code=200)
                span.set_status(SpanStatus.OK)
                span.set_attribute("response.total_tvl_usd", result.get("total_tvl_usd", 0))
                
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
    
    async def calculate_health_factor(
        self,
        collateral_usd: float,
        debt_usd: float,
        liquidation_threshold: float = 0.825,
    ) -> float:
        """Calculate health factor with telemetry."""
        ctx = self._telemetry.start_call(
            api=self.API_NAME,
            operation="calculate_health_factor",
        )
        
        with self._tracing.start_span(
            name=f"{self.API_NAME}.calculate_health_factor",
            kind=SpanKind.INTERNAL,
            attributes={
                "api.name": self.API_NAME,
                "api.operation": "calculate_health_factor",
                "collateral_usd": collateral_usd,
                "debt_usd": debt_usd,
            },
        ) as span:
            try:
                result = await super().calculate_health_factor(
                    collateral_usd, debt_usd, liquidation_threshold
                )
                
                ctx.complete(status=APIStatus.SUCCESS)
                span.set_status(SpanStatus.OK)
                span.set_attribute("response.health_factor", result)
                
                return result
                
            except Exception as e:
                ctx.complete(
                    status=APIStatus.ERROR,
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
        
        if isinstance(error, ValueError) and "GraphQL error" in str(error):
            return APIStatus.VALIDATION_ERROR
        
        return APIStatus.ERROR
