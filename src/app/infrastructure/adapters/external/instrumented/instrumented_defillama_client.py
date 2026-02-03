"""
Instrumented DefiLlama Client with Full Telemetry.

Provides complete observability for DefiLlama API calls:
- Request timing and latency tracking
- Error categorization and rate tracking
- Distributed tracing with span propagation
- Protocol and yield metrics
"""

from typing import Optional

from app.infrastructure.adapters.external.defillama_client import (
    DefiLlamaClient,
    Protocol,
    ProtocolTVL,
    ChainTVL,
    YieldData,
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


class InstrumentedDefiLlamaClient(DefiLlamaClient):
    """
    DefiLlama client with full telemetry instrumentation.

    Usage:
        client = InstrumentedDefiLlamaClient()

        # All calls automatically instrumented
        protocols = await client.get_all_protocols()

        # Get metrics
        telemetry = get_api_telemetry()
        metrics = telemetry.get_metrics("defillama")
    """

    API_NAME = "defillama"

    def __init__(
        self,
        telemetry: Optional[APITelemetry] = None,
        tracing: Optional[TracingService] = None,
    ):
        """
        Initialize instrumented DefiLlama client.

        Args:
            telemetry: API telemetry instance
            tracing: Tracing service instance
        """
        super().__init__()
        self._telemetry = telemetry or get_api_telemetry()
        self._tracing = tracing or get_tracing_service()

    async def get_all_protocols(self) -> list[Protocol]:
        """Get all protocols with telemetry."""
        ctx = self._telemetry.start_call(
            api=self.API_NAME,
            operation="get_all_protocols",
        )

        with self._tracing.start_span(
            name=f"{self.API_NAME}.get_all_protocols",
            kind=SpanKind.CLIENT,
            attributes={
                "api.name": self.API_NAME,
                "api.operation": "get_all_protocols",
            },
        ) as span:
            try:
                result = await super().get_all_protocols()

                ctx.complete(status=APIStatus.SUCCESS, status_code=200)
                span.set_status(SpanStatus.OK)
                span.set_attribute("response.protocol_count", len(result))

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

    async def get_protocol_tvl(self, protocol: str) -> ProtocolTVL:
        """Get protocol TVL with telemetry."""
        ctx = self._telemetry.start_call(
            api=self.API_NAME,
            operation="get_protocol_tvl",
            protocol=protocol,
        )

        with self._tracing.start_span(
            name=f"{self.API_NAME}.get_protocol_tvl",
            kind=SpanKind.CLIENT,
            attributes={
                "api.name": self.API_NAME,
                "api.operation": "get_protocol_tvl",
                "protocol": protocol,
            },
        ) as span:
            try:
                result = await super().get_protocol_tvl(protocol=protocol)

                ctx.complete(status=APIStatus.SUCCESS, status_code=200)
                span.set_status(SpanStatus.OK)
                span.set_attribute("response.tvl", result.tvl)

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

    async def get_protocol_yields(
        self,
        protocol: str | None = None,
        chain: str | None = None,
    ) -> list[YieldData]:
        """Get protocol yields with telemetry."""
        ctx = self._telemetry.start_call(
            api=self.API_NAME,
            operation="get_protocol_yields",
            protocol=protocol or "all",
            chain=chain or "all",
        )

        with self._tracing.start_span(
            name=f"{self.API_NAME}.get_protocol_yields",
            kind=SpanKind.CLIENT,
            attributes={
                "api.name": self.API_NAME,
                "api.operation": "get_protocol_yields",
                "protocol": protocol or "all",
                "chain": chain or "all",
            },
        ) as span:
            try:
                result = await super().get_protocol_yields(
                    protocol=protocol, chain=chain
                )

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
