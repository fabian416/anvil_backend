"""
Application metrics collection for monitoring.
"""

import logging
import time
from typing import Dict, Any, Optional
from collections import defaultdict
from datetime import datetime
import asyncio

logger = logging.getLogger(__name__)


class MetricsCollector:
    """
    Collects application metrics.
    
    Metrics:
    - Request count (by endpoint)
    - Request duration (by endpoint)
    - Error count (by type)
    - Cache hit rate
    - Agent invocations
    - Tool usage
    """
    
    def __init__(self):
        """Initialize metrics collector."""
        self._request_count: Dict[str, int] = defaultdict(int)
        self._request_duration: Dict[str, list] = defaultdict(list)
        self._error_count: Dict[str, int] = defaultdict(int)
        self._cache_hits = 0
        self._cache_misses = 0
        self._agent_invocations: Dict[str, int] = defaultdict(int)
        self._tool_usage: Dict[str, int] = defaultdict(int)
        self._start_time = time.time()
    
    def record_request(self, endpoint: str, duration: float) -> None:
        """
        Record HTTP request.
        
        Args:
            endpoint: API endpoint
            duration: Request duration in seconds
        """
        self._request_count[endpoint] += 1
        self._request_duration[endpoint].append(duration)
    
    def record_error(self, error_type: str) -> None:
        """
        Record error.
        
        Args:
            error_type: Type of error
        """
        self._error_count[error_type] += 1
    
    def record_cache_hit(self) -> None:
        """Record cache hit."""
        self._cache_hits += 1
    
    def record_cache_miss(self) -> None:
        """Record cache miss."""
        self._cache_misses += 1
    
    def record_agent_invocation(self, agent_name: str) -> None:
        """
        Record agent invocation.
        
        Args:
            agent_name: Name of agent
        """
        self._agent_invocations[agent_name] += 1
    
    def record_tool_usage(self, tool_name: str) -> None:
        """
        Record tool usage.
        
        Args:
            tool_name: Name of tool
        """
        self._tool_usage[tool_name] += 1
    
    def get_metrics(self) -> Dict[str, Any]:
        """
        Get current metrics.
        
        Returns:
            Dictionary of metrics
        """
        uptime = time.time() - self._start_time
        
        # Calculate averages
        avg_durations = {}
        for endpoint, durations in self._request_duration.items():
            avg_durations[endpoint] = sum(durations) / len(durations) if durations else 0
        
        # Cache hit rate
        total_cache = self._cache_hits + self._cache_misses
        cache_hit_rate = self._cache_hits / total_cache if total_cache > 0 else 0
        
        return {
            "uptime_seconds": uptime,
            "timestamp": datetime.utcnow().isoformat(),
            "requests": {
                "total": sum(self._request_count.values()),
                "by_endpoint": dict(self._request_count),
                "avg_duration_ms": {
                    endpoint: duration * 1000
                    for endpoint, duration in avg_durations.items()
                },
            },
            "errors": {
                "total": sum(self._error_count.values()),
                "by_type": dict(self._error_count),
            },
            "cache": {
                "hits": self._cache_hits,
                "misses": self._cache_misses,
                "hit_rate": cache_hit_rate,
            },
            "agents": {
                "total_invocations": sum(self._agent_invocations.values()),
                "by_agent": dict(self._agent_invocations),
            },
            "tools": {
                "total_usage": sum(self._tool_usage.values()),
                "by_tool": dict(self._tool_usage),
            },
        }
    
    def reset(self) -> None:
        """Reset all metrics."""
        self._request_count.clear()
        self._request_duration.clear()
        self._error_count.clear()
        self._cache_hits = 0
        self._cache_misses = 0
        self._agent_invocations.clear()
        self._tool_usage.clear()
        self._start_time = time.time()


# Global metrics collector
_collector: Optional[MetricsCollector] = None


def get_metrics_collector() -> MetricsCollector:
    """Get global metrics collector."""
    global _collector
    if _collector is None:
        _collector = MetricsCollector()
    return _collector


# Middleware for automatic request metrics

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
import time


class MetricsMiddleware(BaseHTTPMiddleware):
    """
    Middleware to automatically collect request metrics.
    
    Usage:
        app.add_middleware(MetricsMiddleware)
    """
    
    async def dispatch(self, request: Request, call_next):
        """Process request and collect metrics."""
        collector = get_metrics_collector()
        
        start_time = time.perf_counter()
        
        try:
            response = await call_next(request)
            duration = time.perf_counter() - start_time
            
            # Record request
            endpoint = f"{request.method} {request.url.path}"
            collector.record_request(endpoint, duration)
            
            # Record error if status >= 400
            if response.status_code >= 400:
                collector.record_error(f"HTTP_{response.status_code}")
            
            return response
        
        except Exception as e:
            duration = time.perf_counter() - start_time
            endpoint = f"{request.method} {request.url.path}"
            collector.record_request(endpoint, duration)
            collector.record_error(type(e).__name__)
            raise


# Metrics endpoint

from fastapi import APIRouter

metrics_router = APIRouter(tags=["metrics"])


@metrics_router.get("/metrics")
async def get_metrics():
    """
    Get application metrics.
    
    Returns current metrics for monitoring.
    """
    collector = get_metrics_collector()
    return collector.get_metrics()


@metrics_router.post("/metrics/reset")
async def reset_metrics():
    """
    Reset metrics (admin only).
    
    Useful for testing or after deployment.
    """
    collector = get_metrics_collector()
    collector.reset()
    return {"status": "metrics reset"}
