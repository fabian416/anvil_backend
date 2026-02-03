"""
Instrumented 1inch Client with Full Telemetry.

Provides complete observability for 1inch API calls:
- Request timing and latency tracking
- Error categorization and rate tracking
- Rate limit detection (critical for 1inch)
- Distributed tracing with span propagation
- Cost estimation
"""

from typing import Optional

from app.infrastructure.adapters.external.oneinch_client import (
    OneInchClient,
    SwapQuote,
    SwapTransaction,
    Token,
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


class InstrumentedOneInchClient(OneInchClient):
    """
    1inch client with full telemetry instrumentation.

    Usage:
        client = InstrumentedOneInchClient(api_key="your_key")

        # All calls automatically instrumented
        quote = await client.get_swap_quote(...)

        # Get metrics
        telemetry = get_api_telemetry()
        metrics = telemetry.get_metrics("oneinch")
    """

    API_NAME = "oneinch"

    def __init__(
        self,
        api_key: str | None = None,
        telemetry: Optional[APITelemetry] = None,
        tracing: Optional[TracingService] = None,
    ):
        """
        Initialize instrumented 1inch client.

        Args:
            api_key: 1inch API key
            telemetry: API telemetry instance
            tracing: Tracing service instance
        """
        super().__init__(api_key)
        self._telemetry = telemetry or get_api_telemetry()
        self._tracing = tracing or get_tracing_service()

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
            from_token=from_token[:10],  # Truncate for logging
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
                result = await super().get_swap_quote(
                    from_token=from_token,
                    to_token=to_token,
                    amount=amount,
                )

                ctx.complete(status=APIStatus.SUCCESS, status_code=200)
                span.set_status(SpanStatus.OK)
                span.set_attribute("response.to_amount", str(result.to_amount))

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

    async def get_swap_data(
        self,
        from_token: str,
        to_token: str,
        amount: str,
        from_address: str,
        slippage: float = 1.0,
        disable_estimate: bool = False,
    ) -> SwapTransaction:
        """Get swap transaction data with telemetry."""
        ctx = self._telemetry.start_call(
            api=self.API_NAME,
            operation="get_swap_data",
            from_token=from_token[:10],
            to_token=to_token[:10],
            slippage=slippage,
        )

        with self._tracing.start_span(
            name=f"{self.API_NAME}.get_swap_data",
            kind=SpanKind.CLIENT,
            attributes={
                "api.name": self.API_NAME,
                "api.operation": "get_swap_data",
                "from_token": from_token,
                "to_token": to_token,
                "slippage": slippage,
            },
        ) as span:
            try:
                result = await super().get_swap_data(
                    from_token=from_token,
                    to_token=to_token,
                    amount=amount,
                    from_address=from_address,
                    slippage=slippage,
                    disable_estimate=disable_estimate,
                )

                ctx.complete(status=APIStatus.SUCCESS, status_code=200)
                span.set_status(SpanStatus.OK)
                span.set_attribute("response.to", result.to)

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

    async def get_tokens(self) -> list[Token]:
        """Get available tokens with telemetry."""
        ctx = self._telemetry.start_call(
            api=self.API_NAME,
            operation="get_tokens",
        )

        with self._tracing.start_span(
            name=f"{self.API_NAME}.get_tokens",
            kind=SpanKind.CLIENT,
            attributes={
                "api.name": self.API_NAME,
                "api.operation": "get_tokens",
            },
        ) as span:
            try:
                result = await super().get_tokens()

                ctx.complete(status=APIStatus.SUCCESS, status_code=200)
                span.set_status(SpanStatus.OK)
                span.set_attribute("response.token_count", len(result))

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

    async def get_protocols(self) -> list[dict]:
        """Get available protocols with telemetry."""
        ctx = self._telemetry.start_call(
            api=self.API_NAME,
            operation="get_protocols",
        )

        with self._tracing.start_span(
            name=f"{self.API_NAME}.get_protocols",
            kind=SpanKind.CLIENT,
            attributes={
                "api.name": self.API_NAME,
                "api.operation": "get_protocols",
            },
        ) as span:
            try:
                result = await super().get_protocols()

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

    async def get_token_price(
        self, token_address: str, vs_token: str | None = None
    ) -> float:
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
                result = await super().get_token_price(token_address, vs_token)

                ctx.complete(status=APIStatus.SUCCESS, status_code=200)
                span.set_status(SpanStatus.OK)
                span.set_attribute("response.price", result)

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
