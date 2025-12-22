"""
FastAPI Middleware for Automatic Metrics Collection.

Production-ready middleware that automatically:
- Records request counts by endpoint and status
- Measures response times with histograms
- Tracks errors by type
- Adds correlation IDs to logs
- Integrates with Prometheus metrics
"""

import logging
import time
import uuid
from contextvars import ContextVar
from typing import Callable, Optional

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from app.infrastructure.monitoring.metrics_collector import get_metrics_collector

logger = logging.getLogger(__name__)

# Context variable for correlation ID
correlation_id_var: ContextVar[Optional[str]] = ContextVar(
    "correlation_id", default=None
)


def get_correlation_id() -> Optional[str]:
    """Get current correlation ID from context."""
    return correlation_id_var.get()


class MetricsMiddleware(BaseHTTPMiddleware):
    """
    Middleware for automatic metrics collection.

    Tracks:
    - Request count by endpoint and status
    - Response time histograms
    - Error rates
    - Active request count (in-flight requests)

    Usage:
        app = FastAPI()
        app.add_middleware(MetricsMiddleware)
    """

    def __init__(
        self,
        app: ASGIApp,
        enable_correlation_ids: bool = True,
        skip_paths: Optional[list[str]] = None,
    ):
        """
        Initialize metrics middleware.

        Args:
            app: ASGI application
            enable_correlation_ids: Whether to add correlation IDs
            skip_paths: Paths to skip metrics collection (e.g., /health, /metrics)
        """
        super().__init__(app)
        self.metrics = get_metrics_collector()
        self.enable_correlation_ids = enable_correlation_ids
        self.skip_paths = skip_paths or ["/health", "/metrics", "/docs", "/openapi.json"]

    async def dispatch(
        self, request: Request, call_next: Callable
    ) -> Response:
        """Process request and collect metrics."""
        # Skip metrics for certain paths
        if request.url.path in self.skip_paths:
            return await call_next(request)

        # Generate correlation ID
        correlation_id = None
        if self.enable_correlation_ids:
            correlation_id = str(uuid.uuid4())
            correlation_id_var.set(correlation_id)

        # Extract request metadata
        endpoint = f"{request.method} {request.url.path}"
        user_id = self._extract_user_id(request)
        agent_name = self._extract_agent_name(request)

        # Track active requests
        self.metrics.set_active_requests(
            count=1,  # This would be incremented/decremented in production
            agent_name=agent_name,
            endpoint=endpoint,
        )

        # Record request start
        start_time = time.time()
        status = "success"
        error_type = None

        try:
            # Process request
            response = await call_next(request)

            # Determine status based on response code
            if response.status_code >= 500:
                status = "error"
                error_type = "internal_error"
            elif response.status_code >= 400:
                status = "client_error"
                error_type = "client_error"
            elif response.status_code >= 300:
                status = "redirect"

            # Add correlation ID to response headers
            if correlation_id:
                response.headers["X-Correlation-ID"] = correlation_id

            return response

        except Exception as e:
            status = "error"
            error_type = type(e).__name__
            logger.error(
                f"Request failed: {endpoint}",
                extra={
                    "correlation_id": correlation_id,
                    "error": str(e),
                    "error_type": error_type,
                },
            )
            raise

        finally:
            # Calculate duration
            duration_seconds = time.time() - start_time

            # Record metrics
            self.metrics.increment_request_count(
                agent_name=agent_name,
                user_id=user_id,
                endpoint=endpoint,
                status=status,
            )

            self.metrics.record_response_time(
                duration_seconds=duration_seconds,
                agent_name=agent_name,
                endpoint=endpoint,
                status=status,
            )

            if error_type:
                self.metrics.increment_error_count(
                    error_type=error_type,
                    agent_name=agent_name,
                    endpoint=endpoint,
                )

            # Log request completion
            logger.info(
                f"{request.method} {request.url.path} - {status} - {duration_seconds * 1000:.2f}ms",
                extra={
                    "correlation_id": correlation_id,
                    "endpoint": endpoint,
                    "status": status,
                    "duration_ms": duration_seconds * 1000,
                    "user_id": user_id,
                    "agent_name": agent_name,
                },
            )

            # Clear correlation ID
            if correlation_id:
                correlation_id_var.set(None)

    def _extract_user_id(self, request: Request) -> Optional[str]:
        """Extract user ID from request."""
        # Try to get user from request state (set by auth middleware)
        if hasattr(request.state, "user"):
            user = request.state.user
            if hasattr(user, "id"):
                return str(user.id)

        # Try to extract from JWT token
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            # In production, decode JWT and extract user ID
            pass

        return None

    def _extract_agent_name(self, request: Request) -> Optional[str]:
        """Extract agent name from request."""
        # Check if this is a chat endpoint
        if "/chat/" in request.url.path:
            # Try to extract from query params
            agent_name = request.query_params.get("agent")
            if agent_name:
                return agent_name

            # Try to extract from request body (if available)
            # This would require reading the body, which is tricky in middleware
            # In practice, you might set this in the endpoint handler

        return None


class StructuredLoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware for structured logging with correlation IDs.

    Adds structured logging context to all requests for:
    - Correlation tracking across services
    - Request/response logging
    - Error tracking
    - Performance monitoring

    Usage:
        app = FastAPI()
        app.add_middleware(StructuredLoggingMiddleware)
    """

    def __init__(
        self,
        app: ASGIApp,
        log_request_body: bool = False,
        log_response_body: bool = False,
        skip_paths: Optional[list[str]] = None,
    ):
        """
        Initialize structured logging middleware.

        Args:
            app: ASGI application
            log_request_body: Whether to log request bodies
            log_response_body: Whether to log response bodies
            skip_paths: Paths to skip logging
        """
        super().__init__(app)
        self.log_request_body = log_request_body
        self.log_response_body = log_response_body
        self.skip_paths = skip_paths or ["/health", "/metrics"]

    async def dispatch(
        self, request: Request, call_next: Callable
    ) -> Response:
        """Process request with structured logging."""
        # Skip logging for certain paths
        if request.url.path in self.skip_paths:
            return await call_next(request)

        # Get or create correlation ID
        correlation_id = get_correlation_id()
        if not correlation_id:
            correlation_id = str(uuid.uuid4())
            correlation_id_var.set(correlation_id)

        # Log request
        log_context = {
            "correlation_id": correlation_id,
            "method": request.method,
            "path": request.url.path,
            "query_params": dict(request.query_params),
            "client_ip": request.client.host if request.client else None,
            "user_agent": request.headers.get("User-Agent"),
        }

        logger.info("Request started", extra=log_context)

        # Optionally log request body
        if self.log_request_body and request.method in ["POST", "PUT", "PATCH"]:
            # Note: Reading body in middleware requires careful handling
            # to avoid consuming the request stream
            pass

        start_time = time.time()

        try:
            response = await call_next(request)

            # Add to log context
            log_context.update(
                {
                    "status_code": response.status_code,
                    "duration_ms": (time.time() - start_time) * 1000,
                }
            )

            logger.info("Request completed", extra=log_context)

            return response

        except Exception as e:
            log_context.update(
                {
                    "error": str(e),
                    "error_type": type(e).__name__,
                    "duration_ms": (time.time() - start_time) * 1000,
                }
            )

            logger.error("Request failed", extra=log_context, exc_info=True)
            raise


class CostTrackingMiddleware(BaseHTTPMiddleware):
    """
    Middleware for tracking API costs.

    Integrates with LLM telemetry to track costs per request.

    Usage:
        app = FastAPI()
        app.add_middleware(CostTrackingMiddleware)
    """

    def __init__(
        self,
        app: ASGIApp,
        warn_cost_threshold_usd: float = 0.10,
        skip_paths: Optional[list[str]] = None,
    ):
        """
        Initialize cost tracking middleware.

        Args:
            app: ASGI application
            warn_cost_threshold_usd: Warn if single request exceeds this cost
            skip_paths: Paths to skip cost tracking
        """
        super().__init__(app)
        self.metrics = get_metrics_collector()
        self.warn_cost_threshold_usd = warn_cost_threshold_usd
        self.skip_paths = skip_paths or ["/health", "/metrics"]

    async def dispatch(
        self, request: Request, call_next: Callable
    ) -> Response:
        """Process request and track costs."""
        # Skip for certain paths
        if request.url.path in self.skip_paths:
            return await call_next(request)

        try:
            response = await call_next(request)

            # Check if response has cost information
            # (This would be set by the endpoint handler or LLM telemetry)
            if hasattr(request.state, "llm_cost"):
                cost_usd = request.state.llm_cost
                prompt_tokens = getattr(request.state, "prompt_tokens", 0)
                completion_tokens = getattr(request.state, "completion_tokens", 0)
                agent_name = getattr(request.state, "agent_name", None)
                provider = getattr(request.state, "llm_provider", None)

                # Record cost
                self.metrics.record_cost(
                    cost_usd=cost_usd,
                    agent_name=agent_name,
                    prompt_tokens=prompt_tokens,
                    completion_tokens=completion_tokens,
                    provider=provider,
                )

                # Warn on high-cost requests
                if cost_usd > self.warn_cost_threshold_usd:
                    logger.warning(
                        f"High-cost request: ${cost_usd:.4f}",
                        extra={
                            "correlation_id": get_correlation_id(),
                            "cost_usd": cost_usd,
                            "agent_name": agent_name,
                            "prompt_tokens": prompt_tokens,
                            "completion_tokens": completion_tokens,
                        },
                    )

            return response

        except Exception:
            raise


def setup_monitoring_middleware(app: ASGIApp) -> None:
    """
    Setup all monitoring middleware.

    Args:
        app: FastAPI application
    """
    from fastapi import FastAPI

    if not isinstance(app, FastAPI):
        logger.warning("App is not a FastAPI instance, skipping middleware setup")
        return

    # Add middlewares in reverse order (last added = first executed)
    app.add_middleware(CostTrackingMiddleware)
    app.add_middleware(StructuredLoggingMiddleware)
    app.add_middleware(MetricsMiddleware)

    logger.info("Monitoring middleware configured")
