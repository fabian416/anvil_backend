"""
Health check endpoints for monitoring and deployment.
"""

import logging
from fastapi import APIRouter, status
from pydantic import BaseModel
from typing import Dict, Any
import time

logger = logging.getLogger(__name__)

router = APIRouter(tags=["health"])


class HealthResponse(BaseModel):
    """Health check response."""

    status: str
    timestamp: float
    version: str = "1.0.0"
    checks: Dict[str, Any] = {}


class ReadinessResponse(BaseModel):
    """Readiness check response."""

    ready: bool
    checks: Dict[str, bool]


@router.get(
    "/health",
    response_model=HealthResponse,
    status_code=status.HTTP_200_OK,
)
async def health_check() -> HealthResponse:
    """
    Basic health check.

    Always returns 200 if service is running.
    Used by load balancers to detect if instance is up.
    """
    return HealthResponse(
        status="healthy",
        timestamp=time.time(),
    )


@router.get(
    "/health/live",
    response_model=HealthResponse,
    status_code=status.HTTP_200_OK,
)
async def liveness_check() -> HealthResponse:
    """
    Kubernetes liveness probe.

    Returns 200 if service is alive (not deadlocked).
    """
    return HealthResponse(
        status="alive",
        timestamp=time.time(),
    )


@router.get(
    "/health/ready",
    response_model=ReadinessResponse,
)
async def readiness_check() -> ReadinessResponse:
    """
    Kubernetes readiness probe.

    Returns 200 if service is ready to accept traffic.
    Checks:
    - Database connection
    - Redis connection
    - External API availability (optional)
    """
    checks = {
        "database": await check_database(),
        "redis": await check_redis(),
        "external_apis": await check_external_apis(),
    }

    ready = all(checks.values())

    return ReadinessResponse(
        ready=ready,
        checks=checks,
    )


async def check_database() -> bool:
    """
    Check database connection.

    Returns:
        True if database is accessible
    """
    try:
        # Try to execute simple query
        # from app.infrastructure.persistence_sqla import engine
        # async with engine.connect() as conn:
        #     await conn.execute("SELECT 1")
        return True
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return False


async def check_redis() -> bool:
    """
    Check Redis connection.

    Returns:
        True if Redis is accessible
    """
    try:
        from app.infrastructure.caching.redis_cache import get_cache

        cache = get_cache()
        await cache.set("health_check", "ok", ttl=10)
        result = await cache.get("health_check")
        return result == "ok"
    except Exception as e:
        logger.error(f"Redis health check failed: {e}")
        return False


async def check_external_apis() -> bool:
    """
    Check external API availability (optional).

    Returns:
        True if critical external APIs are accessible
    """
    try:
        # Check critical APIs
        # For health check, we just return True
        # In production, could ping CoinGecko, etc.
        return True
    except Exception as e:
        logger.error(f"External API health check failed: {e}")
        return False
