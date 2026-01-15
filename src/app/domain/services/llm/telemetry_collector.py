"""
Telemetry Collector.

Collects, aggregates, and exposes LLM orchestration metrics.
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime, timedelta, UTC
from dataclasses import dataclass
from decimal import Decimal
from uuid import UUID

logger = logging.getLogger(__name__)


@dataclass
class RequestMetrics:
    """Metrics for a single request."""

    request_id: str
    agent_type: str
    user_id: Optional[UUID]
    session_id: Optional[str]
    provider_name: str
    model_name: str
    status: str
    attempt_count: int
    total_latency_ms: int
    time_to_first_token_ms: Optional[int]
    input_tokens: int
    output_tokens: int
    cost_usd: Decimal
    error_type: Optional[str]
    created_at: datetime


@dataclass
class MetricsSummary:
    """Aggregated metrics summary."""

    period: str
    total_requests: int
    successful_requests: int
    failed_requests: int
    success_rate: Decimal
    avg_latency_ms: int
    p50_latency_ms: Optional[int]
    p95_latency_ms: Optional[int]
    p99_latency_ms: Optional[int]
    total_cost_usd: Decimal
    avg_cost_per_request: Decimal
    total_input_tokens: int
    total_output_tokens: int
    retry_rate: Decimal
    cache_hit_rate: Optional[Decimal]


class TelemetryCollector:
    """
    Collects application metrics for LLM orchestration.

    Metrics:
    - Request count (by endpoint, provider, model)
    - Request duration (by endpoint)
    - Error count (by type)
    - Cost tracking
    - Token usage
    - Cache hit rate
    - Retry rate
    """

    def __init__(self):
        """Initialize telemetry collector."""
        # In-memory metrics (for current period)
        self._request_count: Dict[str, int] = {}
        self._request_durations: Dict[str, List[int]] = {}
        self._error_count: Dict[str, int] = {}
        self._cost_accumulator: Decimal = Decimal("0")
        self._token_count: Dict[str, int] = {"input": 0, "output": 0}
        self._cache_hits = 0
        self._cache_misses = 0
        self._retry_count = 0
        self._start_time = datetime.now(UTC)

    async def record_request(
        self,
        request_id: str,
        agent_type: str,
        provider_name: str,
        model_name: str,
        status: str,
        latency_ms: int,
        input_tokens: int,
        output_tokens: int,
        cost_usd: Decimal,
        attempt_count: int = 1,
        error_type: Optional[str] = None,
    ):
        """
        Record request metrics.

        Args:
            request_id: Request ID
            agent_type: Agent type
            provider_name: Provider name
            model_name: Model name
            status: Request status
            latency_ms: Total latency
            input_tokens: Input tokens
            output_tokens: Output tokens
            cost_usd: Request cost
            attempt_count: Number of attempts
            error_type: Error type if failed
        """
        # Increment counts
        key = f"{agent_type}:{provider_name}:{model_name}"
        self._request_count[key] = self._request_count.get(key, 0) + 1

        # Record duration
        if key not in self._request_durations:
            self._request_durations[key] = []
        self._request_durations[key].append(latency_ms)

        # Record errors
        if error_type:
            self._error_count[error_type] = self._error_count.get(error_type, 0) + 1

        # Accumulate cost
        self._cost_accumulator += cost_usd

        # Count tokens
        self._token_count["input"] += input_tokens
        self._token_count["output"] += output_tokens

        # Count retries
        if attempt_count > 1:
            self._retry_count += 1

        logger.debug(
            f"Recorded metrics for {request_id}: "
            f"{provider_name}/{model_name}, "
            f"latency={latency_ms}ms, "
            f"cost=${cost_usd}"
        )

    async def record_cache_hit(self):
        """Record cache hit."""
        self._cache_hits += 1

    async def record_cache_miss(self):
        """Record cache miss."""
        self._cache_misses += 1

    def get_metrics(self) -> Dict[str, Any]:
        """
        Get current metrics snapshot.

        Returns:
            Dictionary of metrics
        """
        total_requests = sum(self._request_count.values())
        uptime = (datetime.now(UTC) - self._start_time).total_seconds()

        # Calculate averages
        avg_durations = {}
        for key, durations in self._request_durations.items():
            avg_durations[key] = sum(durations) / len(durations) if durations else 0

        # Cache hit rate
        total_cache = self._cache_hits + self._cache_misses
        cache_hit_rate = self._cache_hits / total_cache if total_cache > 0 else 0

        # Retry rate
        retry_rate = self._retry_count / total_requests if total_requests > 0 else 0

        return {
            "uptime_seconds": uptime,
            "timestamp": datetime.now(UTC).isoformat(),
            "requests": {
                "total": total_requests,
                "by_key": dict(self._request_count),
                "avg_duration_ms": avg_durations,
            },
            "errors": {
                "total": sum(self._error_count.values()),
                "by_type": dict(self._error_count),
            },
            "cost": {
                "total_usd": float(self._cost_accumulator),
                "avg_per_request": (
                    float(self._cost_accumulator / total_requests)
                    if total_requests > 0
                    else 0
                ),
            },
            "tokens": {
                "input": self._token_count["input"],
                "output": self._token_count["output"],
                "total": self._token_count["input"] + self._token_count["output"],
            },
            "cache": {
                "hits": self._cache_hits,
                "misses": self._cache_misses,
                "hit_rate": cache_hit_rate,
            },
            "retry_rate": retry_rate,
        }

    def reset(self):
        """Reset all metrics."""
        self._request_count.clear()
        self._request_durations.clear()
        self._error_count.clear()
        self._cost_accumulator = Decimal("0")
        self._token_count = {"input": 0, "output": 0}
        self._cache_hits = 0
        self._cache_misses = 0
        self._retry_count = 0
        self._start_time = datetime.now(UTC)
        logger.info("Telemetry metrics reset")


# Global telemetry collector instance
_telemetry_collector: Optional[TelemetryCollector] = None


def get_telemetry_collector() -> TelemetryCollector:
    """Get global telemetry collector instance."""
    global _telemetry_collector
    if _telemetry_collector is None:
        _telemetry_collector = TelemetryCollector()
    return _telemetry_collector
