"""
Instrumented HTTP Client with Telemetry.

Provides automatic telemetry instrumentation for HTTP clients.
Wraps httpx.AsyncClient with:
- Automatic request/response timing
- Error categorization
- Rate limit detection
- Distributed tracing
- Prometheus metrics

Usage:
    client = InstrumentedClient(
        api_name="coingecko",
        base_url="https://api.coingecko.com/api/v3",
    )

    response = await client.get("/simple/price", params={"ids": "bitcoin"})
    # Telemetry automatically recorded
"""

import functools
import logging
from typing import Any, Callable, Optional, TypeVar

import httpx

from app.infrastructure.telemetry.api_telemetry import (
    APIStatus,
    APITelemetry,
    get_api_telemetry,
)
from app.infrastructure.telemetry.tracing import (
    SpanKind,
    SpanStatus,
    TracingService,
    get_tracing_service,
)

logger = logging.getLogger(__name__)

T = TypeVar("T")


class InstrumentedClient:
    """
    HTTP client with automatic telemetry instrumentation.

    Features:
    - Automatic timing and metrics recording
    - Error classification (timeout, rate limit, auth, etc.)
    - Distributed tracing integration
    - Retry tracking
    """

    def __init__(
        self,
        api_name: str,
        base_url: str,
        timeout: float = 30.0,
        headers: Optional[dict] = None,
        telemetry: Optional[APITelemetry] = None,
        tracing: Optional[TracingService] = None,
    ):
        """
        Initialize instrumented client.

        Args:
            api_name: Name of the API (for telemetry)
            base_url: Base URL for API
            timeout: Request timeout in seconds
            headers: Default headers
            telemetry: API telemetry instance
            tracing: Tracing service instance
        """
        self._api_name = api_name
        self._telemetry = telemetry or get_api_telemetry()
        self._tracing = tracing or get_tracing_service()

        self._client = httpx.AsyncClient(
            base_url=base_url,
            timeout=timeout,
            headers=headers or {},
        )

    async def close(self):
        """Close the HTTP client."""
        await self._client.aclose()

    async def request(
        self,
        method: str,
        url: str,
        operation: str = "",
        **kwargs,
    ) -> httpx.Response:
        """
        Make an instrumented HTTP request.

        Args:
            method: HTTP method
            url: Request URL (relative to base_url)
            operation: Operation name for telemetry
            **kwargs: Additional httpx request arguments

        Returns:
            httpx Response
        """
        operation = operation or f"{method}:{url}"

        # Start telemetry context
        ctx = self._telemetry.start_call(
            api=self._api_name,
            operation=operation,
            method=method,
            url=url,
            **{k: str(v)[:100] for k, v in kwargs.get("params", {}).items()},
        )

        # Start tracing span
        with self._tracing.start_span(
            name=f"{self._api_name}.{operation}",
            kind=SpanKind.CLIENT,
            attributes={
                "http.method": method,
                "http.url": url,
                "api.name": self._api_name,
                "api.operation": operation,
            },
        ) as span:
            try:
                # Inject trace context into headers
                headers = kwargs.pop("headers", {}) or {}
                headers = self._tracing.inject_context(headers)
                kwargs["headers"] = headers

                # Make request
                response = await self._client.request(method, url, **kwargs)

                # Record response info
                span.set_attribute("http.status_code", response.status_code)
                span.set_attribute("http.response_size", len(response.content))

                # Determine status
                if response.status_code == 429:
                    ctx.complete(
                        status=APIStatus.RATE_LIMITED,
                        status_code=response.status_code,
                        error_message="Rate limited",
                    )
                    span.set_status(SpanStatus.ERROR, "Rate limited")
                elif response.status_code == 401 or response.status_code == 403:
                    ctx.complete(
                        status=APIStatus.AUTH_FAILURE,
                        status_code=response.status_code,
                        error_message="Authentication failed",
                    )
                    span.set_status(SpanStatus.ERROR, "Auth failure")
                elif response.status_code >= 400:
                    ctx.complete(
                        status=APIStatus.ERROR,
                        status_code=response.status_code,
                        error_message=f"HTTP {response.status_code}",
                        error_type=f"http_{response.status_code}",
                    )
                    span.set_status(SpanStatus.ERROR, f"HTTP {response.status_code}")
                else:
                    ctx.complete(
                        status=APIStatus.SUCCESS,
                        status_code=response.status_code,
                    )
                    span.set_status(SpanStatus.OK)

                return response

            except httpx.TimeoutException as e:
                ctx.complete(
                    status=APIStatus.TIMEOUT,
                    error_message=str(e),
                    error_type="timeout",
                )
                span.set_status(SpanStatus.ERROR, "Timeout")
                raise

            except httpx.ConnectError as e:
                ctx.complete(
                    status=APIStatus.ERROR,
                    error_message=str(e),
                    error_type="connection_error",
                )
                span.set_status(SpanStatus.ERROR, "Connection error")
                raise

            except Exception as e:
                ctx.complete(
                    status=APIStatus.ERROR,
                    error_message=str(e),
                    error_type=type(e).__name__,
                )
                span.set_status(SpanStatus.ERROR, str(e))
                raise

            finally:
                # Record telemetry
                await self._telemetry.record(ctx)

    async def get(self, url: str, operation: str = "", **kwargs) -> httpx.Response:
        """Make GET request."""
        return await self.request("GET", url, operation=operation, **kwargs)

    async def post(self, url: str, operation: str = "", **kwargs) -> httpx.Response:
        """Make POST request."""
        return await self.request("POST", url, operation=operation, **kwargs)

    async def put(self, url: str, operation: str = "", **kwargs) -> httpx.Response:
        """Make PUT request."""
        return await self.request("PUT", url, operation=operation, **kwargs)

    async def delete(self, url: str, operation: str = "", **kwargs) -> httpx.Response:
        """Make DELETE request."""
        return await self.request("DELETE", url, operation=operation, **kwargs)

    async def patch(self, url: str, operation: str = "", **kwargs) -> httpx.Response:
        """Make PATCH request."""
        return await self.request("PATCH", url, operation=operation, **kwargs)


def instrumented(
    api_name: str,
    operation: Optional[str] = None,
    telemetry: Optional[APITelemetry] = None,
    tracing: Optional[TracingService] = None,
):
    """
    Decorator to add telemetry instrumentation to any async function.

    Usage:
        @instrumented("coingecko", "get_price")
        async def get_price(coin_id: str):
            ...

        # Or with automatic operation name from function
        @instrumented("coingecko")
        async def get_market_chart(coin_id: str, days: int):
            ...
    """
    _telemetry = telemetry or get_api_telemetry()
    _tracing = tracing or get_tracing_service()

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        op_name = operation or func.__name__

        @functools.wraps(func)
        async def wrapper(*args, **kwargs) -> T:
            # Start telemetry context
            ctx = _telemetry.start_call(
                api=api_name,
                operation=op_name,
                **{k: str(v)[:100] for k, v in kwargs.items()},
            )

            # Start tracing span
            with _tracing.start_span(
                name=f"{api_name}.{op_name}",
                kind=SpanKind.CLIENT,
                attributes={
                    "api.name": api_name,
                    "api.operation": op_name,
                },
            ) as span:
                try:
                    result = await func(*args, **kwargs)
                    ctx.complete(status=APIStatus.SUCCESS)
                    span.set_status(SpanStatus.OK)
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
                    await _telemetry.record(ctx)

        return wrapper

    return decorator


class TelemetryMixin:
    """
    Mixin class to add telemetry to existing API clients.

    Usage:
        class CoinGeckoClientWithTelemetry(TelemetryMixin, CoinGeckoClient):
            API_NAME = "coingecko"
    """

    API_NAME: str = "unknown"

    def __init__(self, *args, **kwargs):
        self._telemetry = kwargs.pop("telemetry", None) or get_api_telemetry()
        self._tracing = kwargs.pop("tracing", None) or get_tracing_service()
        super().__init__(*args, **kwargs)

    async def _with_telemetry(
        self,
        operation: str,
        func: Callable[..., T],
        *args,
        **kwargs,
    ) -> T:
        """Execute function with telemetry."""
        ctx = self._telemetry.start_call(
            api=self.API_NAME,
            operation=operation,
            **{k: str(v)[:100] for k, v in kwargs.items()},
        )

        with self._tracing.start_span(
            name=f"{self.API_NAME}.{operation}",
            kind=SpanKind.CLIENT,
            attributes={
                "api.name": self.API_NAME,
                "api.operation": operation,
            },
        ) as span:
            try:
                result = await func(*args, **kwargs)
                ctx.complete(status=APIStatus.SUCCESS)
                span.set_status(SpanStatus.OK)
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
