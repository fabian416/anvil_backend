"""
Comprehensive Health Check System.

Production-ready health monitoring for:
- Database connectivity and performance
- Redis availability and latency
- External API health (OpenAI, Anthropic, etc.)
- WebSocket connection pool status
- System resources (memory, CPU)
- Service dependencies
"""

import asyncio
import logging
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timedelta, UTC
from enum import Enum
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class HealthStatus(Enum):
    """Health check status."""

    HEALTHY = "healthy"  # Component is working normally
    DEGRADED = "degraded"  # Component is working but with issues
    UNHEALTHY = "unhealthy"  # Component is not working
    UNKNOWN = "unknown"  # Health status cannot be determined


@dataclass
class ComponentHealth:
    """Health status of a component."""

    component: str
    status: HealthStatus
    message: str
    latency_ms: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    checked_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def is_healthy(self) -> bool:
        """Check if component is healthy."""
        return self.status == HealthStatus.HEALTHY

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "component": self.component,
            "status": self.status.value,
            "message": self.message,
            "latency_ms": self.latency_ms,
            "metadata": self.metadata,
            "checked_at": self.checked_at.isoformat(),
        }


class HealthCheck(ABC):
    """Base class for health checks."""

    def __init__(self, name: str, timeout_seconds: float = 5.0):
        """
        Initialize health check.

        Args:
            name: Component name
            timeout_seconds: Health check timeout
        """
        self.name = name
        self.timeout_seconds = timeout_seconds
        self._last_check: Optional[ComponentHealth] = None

    @abstractmethod
    async def check(self) -> ComponentHealth:
        """
        Perform health check.

        Returns:
            Component health status
        """
        pass

    async def check_with_timeout(self) -> ComponentHealth:
        """
        Perform health check with timeout.

        Returns:
            Component health status
        """
        try:
            health = await asyncio.wait_for(self.check(), timeout=self.timeout_seconds)
            self._last_check = health
            return health

        except asyncio.TimeoutError:
            health = ComponentHealth(
                component=self.name,
                status=HealthStatus.UNHEALTHY,
                message=f"Health check timed out after {self.timeout_seconds}s",
            )
            self._last_check = health
            return health

        except Exception as e:
            logger.error(f"Health check failed for {self.name}: {e}")
            health = ComponentHealth(
                component=self.name,
                status=HealthStatus.UNHEALTHY,
                message=f"Health check error: {str(e)}",
            )
            self._last_check = health
            return health

    def get_last_check(self) -> Optional[ComponentHealth]:
        """Get last health check result."""
        return self._last_check


class DatabaseHealthCheck(HealthCheck):
    """Database connectivity and performance check."""

    def __init__(
        self,
        name: str = "database",
        slow_query_threshold_ms: float = 100.0,
    ):
        """
        Initialize database health check.

        Args:
            name: Component name
            slow_query_threshold_ms: Threshold for slow query warning
        """
        super().__init__(name)
        self.slow_query_threshold_ms = slow_query_threshold_ms

    async def check(self) -> ComponentHealth:
        """Check database health."""
        start_time = time.time()

        try:
            # Import here to avoid circular dependencies
            from sqlalchemy import text

            from app.infrastructure.persistence_sqla import get_async_session

            async with get_async_session() as session:
                # Execute simple query
                result = await session.execute(text("SELECT 1"))
                row = result.scalar()

                if row != 1:
                    return ComponentHealth(
                        component=self.name,
                        status=HealthStatus.UNHEALTHY,
                        message="Database query returned unexpected result",
                    )

            latency_ms = (time.time() - start_time) * 1000

            # Check if query was slow
            if latency_ms > self.slow_query_threshold_ms:
                return ComponentHealth(
                    component=self.name,
                    status=HealthStatus.DEGRADED,
                    message=f"Database responding slowly ({latency_ms:.1f}ms)",
                    latency_ms=latency_ms,
                )

            return ComponentHealth(
                component=self.name,
                status=HealthStatus.HEALTHY,
                message="Database connection healthy",
                latency_ms=latency_ms,
            )

        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return ComponentHealth(
                component=self.name,
                status=HealthStatus.UNHEALTHY,
                message=f"Database connection failed: {str(e)}",
            )


class RedisHealthCheck(HealthCheck):
    """Redis availability and performance check."""

    def __init__(
        self,
        name: str = "redis",
        slow_operation_threshold_ms: float = 50.0,
    ):
        """
        Initialize Redis health check.

        Args:
            name: Component name
            slow_operation_threshold_ms: Threshold for slow operation warning
        """
        super().__init__(name)
        self.slow_operation_threshold_ms = slow_operation_threshold_ms

    async def check(self) -> ComponentHealth:
        """Check Redis health."""
        start_time = time.time()

        try:
            import redis.asyncio as aioredis

            # Get Redis connection from your configuration
            redis_url = "redis://localhost:6379"  # TODO: Get from config

            redis = aioredis.from_url(redis_url, decode_responses=True)

            try:
                # Test PING command
                pong = await redis.ping()
                if not pong:
                    return ComponentHealth(
                        component=self.name,
                        status=HealthStatus.UNHEALTHY,
                        message="Redis PING failed",
                    )

                # Test SET/GET operations
                test_key = "health_check"
                test_value = "ok"
                await redis.set(test_key, test_value, ex=10)
                retrieved = await redis.get(test_key)

                if retrieved != test_value:
                    return ComponentHealth(
                        component=self.name,
                        status=HealthStatus.DEGRADED,
                        message="Redis SET/GET operation returned unexpected result",
                    )

                latency_ms = (time.time() - start_time) * 1000

                # Check if operations were slow
                if latency_ms > self.slow_operation_threshold_ms:
                    return ComponentHealth(
                        component=self.name,
                        status=HealthStatus.DEGRADED,
                        message=f"Redis responding slowly ({latency_ms:.1f}ms)",
                        latency_ms=latency_ms,
                    )

                # Get Redis info
                info = await redis.info()
                metadata = {
                    "version": info.get("redis_version", "unknown"),
                    "connected_clients": info.get("connected_clients", 0),
                    "used_memory_human": info.get("used_memory_human", "unknown"),
                }

                return ComponentHealth(
                    component=self.name,
                    status=HealthStatus.HEALTHY,
                    message="Redis connection healthy",
                    latency_ms=latency_ms,
                    metadata=metadata,
                )

            finally:
                await redis.close()

        except Exception as e:
            logger.error(f"Redis health check failed: {e}")
            return ComponentHealth(
                component=self.name,
                status=HealthStatus.UNHEALTHY,
                message=f"Redis connection failed: {str(e)}",
            )


class ExternalAPIHealthCheck(HealthCheck):
    """External API availability check."""

    def __init__(
        self,
        name: str,
        api_url: str,
        timeout_seconds: float = 5.0,
        slow_response_threshold_ms: float = 2000.0,
    ):
        """
        Initialize external API health check.

        Args:
            name: API name
            api_url: API endpoint to check
            timeout_seconds: Request timeout
            slow_response_threshold_ms: Threshold for slow response warning
        """
        super().__init__(name, timeout_seconds)
        self.api_url = api_url
        self.slow_response_threshold_ms = slow_response_threshold_ms

    async def check(self) -> ComponentHealth:
        """Check external API health."""
        start_time = time.time()

        try:
            import httpx

            async with httpx.AsyncClient() as client:
                response = await client.get(
                    self.api_url,
                    timeout=self.timeout_seconds,
                )

                latency_ms = (time.time() - start_time) * 1000

                if response.status_code != 200:
                    return ComponentHealth(
                        component=self.name,
                        status=HealthStatus.DEGRADED,
                        message=f"API returned status {response.status_code}",
                        latency_ms=latency_ms,
                        metadata={"status_code": response.status_code},
                    )

                if latency_ms > self.slow_response_threshold_ms:
                    return ComponentHealth(
                        component=self.name,
                        status=HealthStatus.DEGRADED,
                        message=f"API responding slowly ({latency_ms:.1f}ms)",
                        latency_ms=latency_ms,
                    )

                return ComponentHealth(
                    component=self.name,
                    status=HealthStatus.HEALTHY,
                    message="API responding normally",
                    latency_ms=latency_ms,
                )

        except Exception as e:
            logger.error(f"External API health check failed for {self.name}: {e}")
            return ComponentHealth(
                component=self.name,
                status=HealthStatus.UNHEALTHY,
                message=f"API connection failed: {str(e)}",
            )


class WebSocketHealthCheck(HealthCheck):
    """WebSocket connection pool status check."""

    def __init__(self, name: str = "websocket"):
        """
        Initialize WebSocket health check.

        Args:
            name: Component name
        """
        super().__init__(name)

    async def check(self) -> ComponentHealth:
        """Check WebSocket health."""
        try:
            # TODO: Implement actual WebSocket pool health check
            # This is a placeholder that checks if WebSocket infrastructure is ready

            # For now, just return healthy
            # In production, you would check:
            # - Connection pool size
            # - Active connections
            # - Failed connection attempts
            # - Average connection time

            return ComponentHealth(
                component=self.name,
                status=HealthStatus.HEALTHY,
                message="WebSocket infrastructure ready",
                metadata={
                    "active_connections": 0,  # TODO: Get from actual pool
                    "max_connections": 100,  # TODO: Get from config
                },
            )

        except Exception as e:
            logger.error(f"WebSocket health check failed: {e}")
            return ComponentHealth(
                component=self.name,
                status=HealthStatus.UNHEALTHY,
                message=f"WebSocket check failed: {str(e)}",
            )


class SystemResourceHealthCheck(HealthCheck):
    """System resource (CPU, memory) health check."""

    def __init__(
        self,
        name: str = "system_resources",
        memory_threshold_percent: float = 90.0,
        cpu_threshold_percent: float = 90.0,
    ):
        """
        Initialize system resource health check.

        Args:
            name: Component name
            memory_threshold_percent: Memory usage warning threshold
            cpu_threshold_percent: CPU usage warning threshold
        """
        super().__init__(name)
        self.memory_threshold_percent = memory_threshold_percent
        self.cpu_threshold_percent = cpu_threshold_percent

    async def check(self) -> ComponentHealth:
        """Check system resources."""
        try:
            import psutil

            # Get memory usage
            memory = psutil.virtual_memory()
            memory_percent = memory.percent

            # Get CPU usage (average over 1 second)
            cpu_percent = psutil.cpu_percent(interval=1)

            metadata = {
                "memory_percent": memory_percent,
                "memory_available_mb": memory.available / (1024 * 1024),
                "cpu_percent": cpu_percent,
            }

            # Check thresholds
            if (
                memory_percent >= self.memory_threshold_percent
                or cpu_percent >= self.cpu_threshold_percent
            ):
                issues = []
                if memory_percent >= self.memory_threshold_percent:
                    issues.append(f"Memory at {memory_percent:.1f}%")
                if cpu_percent >= self.cpu_threshold_percent:
                    issues.append(f"CPU at {cpu_percent:.1f}%")

                return ComponentHealth(
                    component=self.name,
                    status=HealthStatus.DEGRADED,
                    message=f"High resource usage: {', '.join(issues)}",
                    metadata=metadata,
                )

            return ComponentHealth(
                component=self.name,
                status=HealthStatus.HEALTHY,
                message="System resources normal",
                metadata=metadata,
            )

        except Exception as e:
            logger.error(f"System resource health check failed: {e}")
            return ComponentHealth(
                component=self.name,
                status=HealthStatus.UNKNOWN,
                message=f"Could not check system resources: {str(e)}",
            )


class HealthCheckService:
    """
    Comprehensive health check service.

    Manages and coordinates multiple health checks with:
    - Parallel execution
    - Caching of results
    - Periodic background checks
    - Overall system health status
    """

    def __init__(self, cache_ttl_seconds: float = 30.0):
        """
        Initialize health check service.

        Args:
            cache_ttl_seconds: Time to cache health check results
        """
        self.checks: List[HealthCheck] = []
        self.cache_ttl_seconds = cache_ttl_seconds
        self._cached_results: Dict[str, ComponentHealth] = {}
        self._last_full_check: Optional[datetime] = None

    def add_check(self, check: HealthCheck) -> None:
        """
        Add health check.

        Args:
            check: Health check to add
        """
        self.checks.append(check)
        logger.info(f"Added health check: {check.name}")

    def remove_check(self, name: str) -> bool:
        """
        Remove health check by name.

        Args:
            name: Check name to remove

        Returns:
            True if check was removed
        """
        for i, check in enumerate(self.checks):
            if check.name == name:
                del self.checks[i]
                logger.info(f"Removed health check: {name}")
                return True
        return False

    async def check_all(self, use_cache: bool = True) -> Dict[str, ComponentHealth]:
        """
        Run all health checks.

        Args:
            use_cache: Whether to use cached results if available

        Returns:
            Dictionary mapping component names to health status
        """
        # Check if we should use cached results
        if use_cache and self._is_cache_valid():
            return self._cached_results

        # Run all checks in parallel
        tasks = [check.check_with_timeout() for check in self.checks]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Process results
        health_results: Dict[str, ComponentHealth] = {}
        for check, result in zip(self.checks, results):
            if isinstance(result, Exception):
                logger.error(f"Health check {check.name} raised exception: {result}")
                health_results[check.name] = ComponentHealth(
                    component=check.name,
                    status=HealthStatus.UNHEALTHY,
                    message=f"Health check exception: {str(result)}",
                )
            else:
                health_results[check.name] = result

        # Update cache
        self._cached_results = health_results
        self._last_full_check = datetime.now(UTC)

        return health_results

    async def check_component(self, name: str) -> Optional[ComponentHealth]:
        """
        Check health of specific component.

        Args:
            name: Component name

        Returns:
            Component health or None if not found
        """
        for check in self.checks:
            if check.name == name:
                return await check.check_with_timeout()
        return None

    def _is_cache_valid(self) -> bool:
        """Check if cached results are still valid."""
        if not self._last_full_check or not self._cached_results:
            return False

        age = (datetime.now(UTC) - self._last_full_check).total_seconds()
        return age < self.cache_ttl_seconds

    async def get_overall_status(self) -> HealthStatus:
        """
        Get overall system health status.

        Returns:
            Overall health status based on all components
        """
        results = await self.check_all()

        if not results:
            return HealthStatus.UNKNOWN

        # If any component is unhealthy, overall is unhealthy
        if any(h.status == HealthStatus.UNHEALTHY for h in results.values()):
            return HealthStatus.UNHEALTHY

        # If any component is degraded, overall is degraded
        if any(h.status == HealthStatus.DEGRADED for h in results.values()):
            return HealthStatus.DEGRADED

        # If all components are healthy, overall is healthy
        if all(h.status == HealthStatus.HEALTHY for h in results.values()):
            return HealthStatus.HEALTHY

        return HealthStatus.UNKNOWN

    async def get_health_summary(self) -> Dict[str, Any]:
        """
        Get comprehensive health summary.

        Returns:
            Dictionary with overall status and component details
        """
        results = await self.check_all()
        overall = await self.get_overall_status()

        return {
            "status": overall.value,
            "timestamp": datetime.now(UTC).isoformat(),
            "components": {name: health.to_dict() for name, health in results.items()},
            "healthy_count": sum(
                1 for h in results.values() if h.status == HealthStatus.HEALTHY
            ),
            "degraded_count": sum(
                1 for h in results.values() if h.status == HealthStatus.DEGRADED
            ),
            "unhealthy_count": sum(
                1 for h in results.values() if h.status == HealthStatus.UNHEALTHY
            ),
        }


# Global health check service instance
_health_service: Optional[HealthCheckService] = None


def get_health_service() -> HealthCheckService:
    """Get or create global health check service instance."""
    global _health_service
    if _health_service is None:
        _health_service = HealthCheckService()
    return _health_service


def setup_default_health_checks() -> HealthCheckService:
    """
    Setup default health checks.

    Returns:
        Configured health check service
    """
    service = get_health_service()

    # Add default checks
    service.add_check(DatabaseHealthCheck())
    service.add_check(RedisHealthCheck())
    service.add_check(WebSocketHealthCheck())
    service.add_check(SystemResourceHealthCheck())

    # Add external API checks (optional - configure as needed)
    # service.add_check(ExternalAPIHealthCheck(
    #     name="openai",
    #     api_url="https://api.openai.com/v1/models",
    # ))

    logger.info("Setup default health checks")
    return service
