"""
Instrumented Uniswap Client with Full Telemetry.

Provides complete observability for Uniswap API calls:
- Request timing and latency tracking
- Error categorization and rate tracking
- Distributed tracing with span propagation
- GraphQL query metrics
"""

from typing import Any, Optional

from app.infrastructure.adapters.external.uniswap_client import (
    UniswapClient,
    PoolData,
    TokenPrice,
    SwapSimulation,
    PositionData,
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


class InstrumentedUniswapClient(UniswapClient):
    """
    Uniswap client with full telemetry instrumentation.

    Usage:
        client = InstrumentedUniswapClient(api_key="...", chain="ethereum")

        # All calls automatically instrumented
        pool = await client.get_pool_data("0x...")

        # Get metrics
        telemetry = get_api_telemetry()
        metrics = telemetry.get_metrics("uniswap")
    """

    API_NAME = "uniswap"

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

    async def get_pool_data(self, pool_address: str) -> PoolData:
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
                "chain": self._chain,
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

    async def get_token_price(self, token_address: str) -> TokenPrice:
        """Get token price with telemetry."""
        ctx = self._telemetry.start_call(
            api=self.API_NAME,
            operation="get_token_price",
            token=token_address[:10],
        )

        with self._tracing.start_span(
            name=f"{self.API_NAME}.get_token_price",
            kind=SpanKind.CLIENT,
            attributes={
                "api.name": self.API_NAME,
                "api.operation": "get_token_price",
                "token_address": token_address,
            },
        ) as span:
            try:
                result = await super().get_token_price(token_address)

                ctx.complete(status=APIStatus.SUCCESS, status_code=200)
                span.set_status(SpanStatus.OK)
                span.set_attribute("response.price_usd", result.price_usd)

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

    async def get_top_pools(
        self,
        limit: int = 10,
        order_by: str = "totalValueLockedUSD",
    ) -> list[PoolData]:
        """Get top pools with telemetry."""
        ctx = self._telemetry.start_call(
            api=self.API_NAME,
            operation="get_top_pools",
            limit=limit,
        )

        with self._tracing.start_span(
            name=f"{self.API_NAME}.get_top_pools",
            kind=SpanKind.CLIENT,
            attributes={
                "api.name": self.API_NAME,
                "api.operation": "get_top_pools",
                "limit": limit,
                "order_by": order_by,
            },
        ) as span:
            try:
                result = await super().get_top_pools(limit, order_by)

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

    async def simulate_swap(
        self,
        token_in: str,
        token_out: str,
        amount_in: str,
    ) -> SwapSimulation:
        """Simulate swap with telemetry."""
        ctx = self._telemetry.start_call(
            api=self.API_NAME,
            operation="simulate_swap",
            token_in=token_in[:10],
            token_out=token_out[:10],
        )

        with self._tracing.start_span(
            name=f"{self.API_NAME}.simulate_swap",
            kind=SpanKind.CLIENT,
            attributes={
                "api.name": self.API_NAME,
                "api.operation": "simulate_swap",
                "token_in": token_in,
                "token_out": token_out,
            },
        ) as span:
            try:
                result = await super().simulate_swap(token_in, token_out, amount_in)

                ctx.complete(status=APIStatus.SUCCESS, status_code=200)
                span.set_status(SpanStatus.OK)
                span.set_attribute("response.price_impact", result.price_impact)

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

    async def get_position(self, token_id: int) -> PositionData:
        """Get position with telemetry."""
        ctx = self._telemetry.start_call(
            api=self.API_NAME,
            operation="get_position",
            token_id=token_id,
        )

        with self._tracing.start_span(
            name=f"{self.API_NAME}.get_position",
            kind=SpanKind.CLIENT,
            attributes={
                "api.name": self.API_NAME,
                "api.operation": "get_position",
                "token_id": token_id,
            },
        ) as span:
            try:
                result = await super().get_position(token_id)

                ctx.complete(status=APIStatus.SUCCESS, status_code=200)
                span.set_status(SpanStatus.OK)
                span.set_attribute("response.liquidity", result.liquidity)

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

    async def get_factory_stats(self) -> dict[str, Any]:
        """Get factory stats with telemetry."""
        ctx = self._telemetry.start_call(
            api=self.API_NAME,
            operation="get_factory_stats",
        )

        with self._tracing.start_span(
            name=f"{self.API_NAME}.get_factory_stats",
            kind=SpanKind.CLIENT,
            attributes={
                "api.name": self.API_NAME,
                "api.operation": "get_factory_stats",
            },
        ) as span:
            try:
                result = await super().get_factory_stats()

                ctx.complete(status=APIStatus.SUCCESS, status_code=200)
                span.set_status(SpanStatus.OK)
                span.set_attribute("response.tvl_usd", result.get("tvl_usd", 0))

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

        if isinstance(error, ValueError) and "GraphQL error" in str(error):
            return APIStatus.VALIDATION_ERROR

        return APIStatus.ERROR
