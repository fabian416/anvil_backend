"""
Instrumented Gas Oracle Client with Full Telemetry.

Provides complete observability for Gas Oracle API calls:
- Request timing and latency tracking
- Error categorization and rate tracking
- Distributed tracing with span propagation
- Multi-source gas price aggregation metrics
"""

from datetime import datetime
from typing import Optional

from app.infrastructure.adapters.external.gas_oracle_client import (
    GasOracleClient,
    GasEstimate,
    GasPrice,
    GasPrediction,
    TransactionCost,
    GasSpeed,
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


class InstrumentedGasOracleClient(GasOracleClient):
    """
    Gas Oracle client with full telemetry instrumentation.

    Usage:
        client = InstrumentedGasOracleClient(
            blocknative_api_key="...",
            etherscan_api_key="...",
        )

        # All calls automatically instrumented
        prices = await client.get_gas_prices("ethereum")

        # Get metrics
        telemetry = get_api_telemetry()
        metrics = telemetry.get_metrics("gas_oracle")
    """

    API_NAME = "gas_oracle"

    def __init__(
        self,
        blocknative_api_key: str | None = None,
        etherscan_api_key: str | None = None,
        timeout: float = 10.0,
        telemetry: Optional[APITelemetry] = None,
        tracing: Optional[TracingService] = None,
    ):
        super().__init__(blocknative_api_key, etherscan_api_key, timeout)
        self._telemetry = telemetry or get_api_telemetry()
        self._tracing = tracing or get_tracing_service()

    async def get_gas_prices(
        self,
        chain: str = "ethereum",
    ) -> dict[str, GasEstimate]:
        """Get gas prices with telemetry."""
        ctx = self._telemetry.start_call(
            api=self.API_NAME,
            operation="get_gas_prices",
            chain=chain,
        )

        with self._tracing.start_span(
            name=f"{self.API_NAME}.get_gas_prices",
            kind=SpanKind.CLIENT,
            attributes={
                "api.name": self.API_NAME,
                "api.operation": "get_gas_prices",
                "chain": chain,
            },
        ) as span:
            try:
                result = await super().get_gas_prices(chain)

                ctx.complete(status=APIStatus.SUCCESS, status_code=200)
                span.set_status(SpanStatus.OK)

                # Log standard gas price
                if GasSpeed.STANDARD.value in result:
                    span.set_attribute(
                        "response.standard_gas_gwei",
                        result[GasSpeed.STANDARD.value].gas_price_gwei,
                    )

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

    async def get_current_price(
        self,
        chain: str = "ethereum",
    ) -> GasPrice:
        """Get current gas price with telemetry."""
        ctx = self._telemetry.start_call(
            api=self.API_NAME,
            operation="get_current_price",
            chain=chain,
        )

        with self._tracing.start_span(
            name=f"{self.API_NAME}.get_current_price",
            kind=SpanKind.CLIENT,
            attributes={
                "api.name": self.API_NAME,
                "api.operation": "get_current_price",
                "chain": chain,
            },
        ) as span:
            try:
                result = await super().get_current_price(chain)

                ctx.complete(status=APIStatus.SUCCESS, status_code=200)
                span.set_status(SpanStatus.OK)
                span.set_attribute(
                    "response.estimated_price_gwei", result.estimated_price_gwei
                )

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

    async def get_gas_prediction(
        self,
        chain: str = "ethereum",
        minutes_ahead: int = 15,
    ) -> GasPrediction:
        """Get gas prediction with telemetry."""
        ctx = self._telemetry.start_call(
            api=self.API_NAME,
            operation="get_gas_prediction",
            chain=chain,
            minutes_ahead=minutes_ahead,
        )

        with self._tracing.start_span(
            name=f"{self.API_NAME}.get_gas_prediction",
            kind=SpanKind.CLIENT,
            attributes={
                "api.name": self.API_NAME,
                "api.operation": "get_gas_prediction",
                "chain": chain,
                "minutes_ahead": minutes_ahead,
            },
        ) as span:
            try:
                result = await super().get_gas_prediction(chain, minutes_ahead)

                ctx.complete(status=APIStatus.SUCCESS, status_code=200)
                span.set_status(SpanStatus.OK)
                span.set_attribute(
                    "response.predicted_base_fee", result.predicted_base_fee
                )
                span.set_attribute("response.confidence", result.confidence)

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

    async def estimate_transaction_cost(
        self,
        gas_limit: int,
        speed: GasSpeed = GasSpeed.STANDARD,
        chain: str = "ethereum",
    ) -> TransactionCost:
        """Estimate transaction cost with telemetry."""
        ctx = self._telemetry.start_call(
            api=self.API_NAME,
            operation="estimate_transaction_cost",
            chain=chain,
            speed=speed.value,
            gas_limit=gas_limit,
        )

        with self._tracing.start_span(
            name=f"{self.API_NAME}.estimate_transaction_cost",
            kind=SpanKind.CLIENT,
            attributes={
                "api.name": self.API_NAME,
                "api.operation": "estimate_transaction_cost",
                "chain": chain,
                "speed": speed.value,
                "gas_limit": gas_limit,
            },
        ) as span:
            try:
                result = await super().estimate_transaction_cost(
                    gas_limit, speed, chain
                )

                ctx.complete(status=APIStatus.SUCCESS, status_code=200)
                span.set_status(SpanStatus.OK)
                span.set_attribute("response.cost_usd", result.cost_usd)
                span.set_attribute("response.cost_eth", result.cost_eth)

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

    async def get_optimal_time(
        self,
        target_gas_price: float,
        max_wait_hours: int = 24,
    ) -> datetime | None:
        """Get optimal time with telemetry."""
        ctx = self._telemetry.start_call(
            api=self.API_NAME,
            operation="get_optimal_time",
            target_gas_price=target_gas_price,
            max_wait_hours=max_wait_hours,
        )

        with self._tracing.start_span(
            name=f"{self.API_NAME}.get_optimal_time",
            kind=SpanKind.CLIENT,
            attributes={
                "api.name": self.API_NAME,
                "api.operation": "get_optimal_time",
                "target_gas_price": target_gas_price,
                "max_wait_hours": max_wait_hours,
            },
        ) as span:
            try:
                result = await super().get_optimal_time(
                    target_gas_price, max_wait_hours
                )

                ctx.complete(status=APIStatus.SUCCESS, status_code=200)
                span.set_status(SpanStatus.OK)
                span.set_attribute("response.found_time", result is not None)

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

    async def get_gas_history(
        self,
        chain: str = "ethereum",
        hours: int = 24,
    ) -> list[GasPrice]:
        """Get gas history with telemetry."""
        ctx = self._telemetry.start_call(
            api=self.API_NAME,
            operation="get_gas_history",
            chain=chain,
            hours=hours,
        )

        with self._tracing.start_span(
            name=f"{self.API_NAME}.get_gas_history",
            kind=SpanKind.CLIENT,
            attributes={
                "api.name": self.API_NAME,
                "api.operation": "get_gas_history",
                "chain": chain,
                "hours": hours,
            },
        ) as span:
            try:
                result = await super().get_gas_history(chain, hours)

                ctx.complete(status=APIStatus.SUCCESS, status_code=200)
                span.set_status(SpanStatus.OK)
                span.set_attribute("response.data_point_count", len(result))

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
