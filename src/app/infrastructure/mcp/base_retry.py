"""
MCP Server Base with Enterprise Retry Support.

Provides base class for all MCP servers with built-in retry logic,
circuit breaker, and telemetry integration.
"""

import logging
from typing import Any, Dict, Optional
from abc import ABC

import httpx
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)

from app.domain.value_objects.retry_config import RetryConfig
from app.domain.services.retry import (
    EnterpriseRetryEngine,
    CircuitBreaker,
    ServiceRegistry,
)

logger = logging.getLogger(__name__)


class MCPServerBaseWithRetry(ABC):
    """
    Base class for MCP servers with enterprise retry support.

    Provides:
    - Automatic retry on HTTP errors
    - Circuit breaker integration
    - Telemetry tracking
    - Manual service override support

    Usage:
        class MyMCPServer(MCPServerBaseWithRetry):
            def __init__(self, api_key: str, ...):
                super().__init__(
                    service_name="my_mcp_server",
                    retry_config=RetryConfig.for_mcp_servers(),
                )
                self.api_key = api_key
                self.client = httpx.AsyncClient(...)

            async def get_data(self, params):
                # This will automatically have retry logic
                return await self._make_request("GET", "/endpoint", params=params)
    """

    def __init__(
        self,
        service_name: str,
        retry_config: Optional[RetryConfig] = None,
        circuit_breaker: Optional[CircuitBreaker] = None,
        service_registry: Optional[ServiceRegistry] = None,
        telemetry: Optional[Any] = None,
    ):
        """
        Initialize MCP server with retry support.

        Args:
            service_name: Unique service name (e.g., "defillama_mcp")
            retry_config: Retry configuration (defaults to MCP-optimized config)
            circuit_breaker: Circuit breaker instance (optional)
            service_registry: Service registry for manual override (optional)
            telemetry: Telemetry collector (optional)
        """
        self.service_name = service_name
        self.retry_config = retry_config or RetryConfig.for_mcp_servers()

        # Initialize retry engine
        self.retry_engine = EnterpriseRetryEngine(
            config=self.retry_config,
            circuit_breaker=circuit_breaker,
            telemetry=telemetry,
            service_registry=service_registry,
        )

        logger.info(
            f"Initialized {service_name} with retry support: "
            f"max_retries={self.retry_config.max_retries}, "
            f"circuit_breaker={'enabled' if circuit_breaker else 'disabled'}"
        )

    async def _make_request(
        self,
        method: str,
        url: str,
        context: Optional[Dict[str, Any]] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Make HTTP request with retry logic.

        This method wraps the actual HTTP call with enterprise retry logic,
        including circuit breaker and telemetry.

        Args:
            method: HTTP method (GET, POST, etc.)
            url: Request URL
            context: Additional context for telemetry (optional)
            **kwargs: Additional arguments for httpx (params, json, headers, etc.)

        Returns:
            Parsed JSON response

        Raises:
            ServiceDisabledError: If service is manually disabled
            CircuitBreakerOpenError: If circuit breaker is open
            AllRetriesExhaustedError: If all retries fail

        Example:
            response = await self._make_request(
                "GET",
                "https://api.example.com/data",
                params={"limit": 10},
                context={"user_id": user_id},
            )
        """

        async def make_http_call():
            """Inner function for retry engine."""
            # This assumes self.client is an httpx.AsyncClient
            # Subclasses must define self.client
            if not hasattr(self, "client"):
                raise AttributeError(
                    f"{self.__class__.__name__} must define self.client "
                    f"(httpx.AsyncClient) in __init__"
                )

            response = await self.client.request(method, url, **kwargs)
            response.raise_for_status()
            return response.json()

        # Execute with retry engine
        return await self.retry_engine.execute_with_retry(
            service_name=self.service_name,
            func=make_http_call,
            context=context or {},
        )

    def _create_retry_decorator(self):
        """
        Create a tenacity retry decorator for this service.

        This provides a decorator-based approach for methods that need retry
        but don't use _make_request.

        Returns:
            Tenacity retry decorator

        Example:
            class MyMCPServer(MCPServerBaseWithRetry):
                def __init__(self):
                    super().__init__("my_service")
                    self._retry = self._create_retry_decorator()

                async def custom_operation(self):
                    @self._retry
                    async def operation():
                        # ... custom logic
                        return result

                    return await operation()
        """
        return retry(
            stop=stop_after_attempt(self.retry_config.max_retries),
            wait=wait_exponential(
                multiplier=1,
                min=self.retry_config.initial_backoff_seconds,
                max=self.retry_config.max_backoff_seconds,
            ),
            retry=retry_if_exception_type((httpx.HTTPError, httpx.TimeoutException)),
            reraise=True,
        )


class MCPServerRetryMixin:
    """
    Mixin for adding retry support to existing MCP servers.

    This mixin can be added to existing MCP server classes without
    changing their inheritance hierarchy.

    Usage:
        class ExistingMCPServer(MCPServerRetryMixin, ExistingBase):
            def __init__(self, ...):
                self._init_retry_support(
                    service_name="my_service",
                    retry_config=RetryConfig.for_mcp_servers(),
                )
                # ... rest of init
    """

    def _init_retry_support(
        self,
        service_name: str,
        retry_config: Optional[RetryConfig] = None,
        circuit_breaker: Optional[CircuitBreaker] = None,
        service_registry: Optional[ServiceRegistry] = None,
        telemetry: Optional[Any] = None,
    ):
        """
        Initialize retry support for the mixin.

        Call this in your __init__ method before making any API calls.

        Args:
            service_name: Unique service name
            retry_config: Retry configuration (optional)
            circuit_breaker: Circuit breaker instance (optional)
            service_registry: Service registry (optional)
            telemetry: Telemetry collector (optional)
        """
        self.service_name = service_name
        self.retry_config = retry_config or RetryConfig.for_mcp_servers()

        self.retry_engine = EnterpriseRetryEngine(
            config=self.retry_config,
            circuit_breaker=circuit_breaker,
            telemetry=telemetry,
            service_registry=service_registry,
        )

        logger.info(f"Initialized retry support for {service_name}")

    async def _make_request_with_retry(
        self,
        method: str,
        url: str,
        context: Optional[Dict[str, Any]] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Make HTTP request with retry logic.

        Same as MCPServerBaseWithRetry._make_request.
        """

        async def make_http_call():
            if not hasattr(self, "client"):
                raise AttributeError(
                    f"{self.__class__.__name__} must define self.client"
                )

            response = await self.client.request(method, url, **kwargs)
            response.raise_for_status()
            return response.json()

        return await self.retry_engine.execute_with_retry(
            service_name=self.service_name,
            func=make_http_call,
            context=context or {},
        )


# Convenience function for creating retry decorator
def create_mcp_retry_decorator(
    service_name: str,
    retry_config: Optional[RetryConfig] = None,
):
    """
    Create a standalone retry decorator for MCP operations.

    This is useful for adding retry to individual functions without
    using the base class or mixin.

    Args:
        service_name: Service name for logging
        retry_config: Retry configuration (optional)

    Returns:
        Tenacity retry decorator

    Example:
        @create_mcp_retry_decorator("my_service")
        async def fetch_data():
            response = await client.get("/data")
            return response.json()
    """
    config = retry_config or RetryConfig.for_mcp_servers()

    return retry(
        stop=stop_after_attempt(config.max_retries),
        wait=wait_exponential(
            multiplier=1,
            min=config.initial_backoff_seconds,
            max=config.max_backoff_seconds,
        ),
        retry=retry_if_exception_type((httpx.HTTPError, httpx.TimeoutException)),
        reraise=True,
        before_sleep=lambda retry_state: logger.warning(
            f"Retrying {service_name} after {retry_state.outcome.exception()}"
        ),
    )
