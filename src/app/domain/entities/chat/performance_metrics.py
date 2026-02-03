"""
Performance metrics entity for tracking chat system performance.

Tracks response times, request counts, error rates, costs, and cache hit rates
for monitoring and optimization of the chat system.
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta, UTC
from typing import Dict, Optional, List
from uuid import UUID, uuid4
from enum import Enum


class MetricType(Enum):
    """Types of performance metrics."""

    RESPONSE_TIME = "response_time"
    REQUEST_COUNT = "request_count"
    ERROR_RATE = "error_rate"
    COST = "cost"
    CACHE_HIT_RATE = "cache_hit_rate"
    TOKEN_USAGE = "token_usage"
    API_CALL_COUNT = "api_call_count"


class ErrorType(Enum):
    """Types of errors to track."""

    TIMEOUT = "timeout"
    RATE_LIMIT = "rate_limit"
    VALIDATION = "validation"
    AUTHENTICATION = "authentication"
    LLM_ERROR = "llm_error"
    NETWORK = "network"
    INTERNAL = "internal"
    UNKNOWN = "unknown"


class AggregationPeriod(Enum):
    """Time periods for metrics aggregation."""

    MINUTE = "minute"
    HOURLY = "hourly"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"


@dataclass
class ResponseTimeMetrics:
    """Response time statistics."""

    p50_ms: float
    p95_ms: float
    p99_ms: float
    min_ms: float
    max_ms: float
    avg_ms: float
    total_requests: int

    def is_within_sla(self, sla_p95_ms: float) -> bool:
        """Check if metrics meet SLA requirements."""
        return self.p95_ms <= sla_p95_ms

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "p50_ms": self.p50_ms,
            "p95_ms": self.p95_ms,
            "p99_ms": self.p99_ms,
            "min_ms": self.min_ms,
            "max_ms": self.max_ms,
            "avg_ms": self.avg_ms,
            "total_requests": self.total_requests,
        }


@dataclass
class ErrorMetrics:
    """Error tracking metrics."""

    total_errors: int
    error_rate: float
    errors_by_type: Dict[ErrorType, int] = field(default_factory=dict)
    last_error_timestamp: Optional[datetime] = None

    def increment_error(self, error_type: ErrorType) -> None:
        """Increment error count for a specific type."""
        self.total_errors += 1
        self.errors_by_type[error_type] = self.errors_by_type.get(error_type, 0) + 1
        self.last_error_timestamp = datetime.now(UTC)

    def get_most_common_error(self) -> Optional[ErrorType]:
        """Get the most frequently occurring error type."""
        if not self.errors_by_type:
            return None
        return max(self.errors_by_type, key=self.errors_by_type.get)  # type: ignore

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "total_errors": self.total_errors,
            "error_rate": self.error_rate,
            "errors_by_type": {
                error_type.value: count
                for error_type, count in self.errors_by_type.items()
            },
            "last_error_timestamp": (
                self.last_error_timestamp.isoformat()
                if self.last_error_timestamp
                else None
            ),
        }


@dataclass
class CostMetrics:
    """Cost tracking metrics."""

    total_cost_usd: float
    token_count: int
    api_call_count: int
    avg_cost_per_request_usd: float
    prompt_tokens: int = 0
    completion_tokens: int = 0

    def add_request_cost(
        self,
        cost_usd: float,
        prompt_tokens: int = 0,
        completion_tokens: int = 0,
    ) -> None:
        """Add cost for a single request."""
        self.total_cost_usd += cost_usd
        self.token_count += prompt_tokens + completion_tokens
        self.prompt_tokens += prompt_tokens
        self.completion_tokens += completion_tokens
        self.api_call_count += 1
        self.avg_cost_per_request_usd = (
            self.total_cost_usd / self.api_call_count if self.api_call_count > 0 else 0
        )

    def is_within_budget(self, budget_usd: float) -> bool:
        """Check if costs are within budget."""
        return self.total_cost_usd <= budget_usd

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "total_cost_usd": self.total_cost_usd,
            "token_count": self.token_count,
            "api_call_count": self.api_call_count,
            "avg_cost_per_request_usd": self.avg_cost_per_request_usd,
            "prompt_tokens": self.prompt_tokens,
            "completion_tokens": self.completion_tokens,
        }


@dataclass
class CacheMetrics:
    """Cache performance metrics."""

    total_requests: int
    cache_hits: int
    cache_misses: int
    hit_rate: float

    def record_hit(self) -> None:
        """Record a cache hit."""
        self.total_requests += 1
        self.cache_hits += 1
        self._update_hit_rate()

    def record_miss(self) -> None:
        """Record a cache miss."""
        self.total_requests += 1
        self.cache_misses += 1
        self._update_hit_rate()

    def _update_hit_rate(self) -> None:
        """Update hit rate calculation."""
        self.hit_rate = (
            self.cache_hits / self.total_requests if self.total_requests > 0 else 0.0
        )

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "total_requests": self.total_requests,
            "cache_hits": self.cache_hits,
            "cache_misses": self.cache_misses,
            "hit_rate": self.hit_rate,
        }


@dataclass
class PerformanceMetrics:
    """
    Comprehensive performance metrics for chat system monitoring.

    Tracks response times, error rates, costs, cache performance,
    and other key metrics per agent and time period.
    """

    id: UUID
    agent_name: Optional[str]
    period: AggregationPeriod
    period_start: datetime
    period_end: datetime
    response_times: ResponseTimeMetrics
    errors: ErrorMetrics
    costs: CostMetrics
    cache: CacheMetrics
    request_count: int = 0
    user_count: int = 0
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    @classmethod
    def create(
        cls,
        agent_name: Optional[str],
        period: AggregationPeriod,
        period_start: datetime,
        period_end: datetime,
    ) -> "PerformanceMetrics":
        """
        Create new performance metrics instance.

        Args:
            agent_name: Name of agent (None for global metrics)
            period: Aggregation period
            period_start: Start of period
            period_end: End of period

        Returns:
            PerformanceMetrics instance
        """
        return cls(
            id=uuid4(),
            agent_name=agent_name,
            period=period,
            period_start=period_start,
            period_end=period_end,
            response_times=ResponseTimeMetrics(
                p50_ms=0.0,
                p95_ms=0.0,
                p99_ms=0.0,
                min_ms=0.0,
                max_ms=0.0,
                avg_ms=0.0,
                total_requests=0,
            ),
            errors=ErrorMetrics(
                total_errors=0,
                error_rate=0.0,
            ),
            costs=CostMetrics(
                total_cost_usd=0.0,
                token_count=0,
                api_call_count=0,
                avg_cost_per_request_usd=0.0,
            ),
            cache=CacheMetrics(
                total_requests=0,
                cache_hits=0,
                cache_misses=0,
                hit_rate=0.0,
            ),
        )

    def record_request(
        self,
        response_time_ms: float,
        cost_usd: float,
        cache_hit: bool,
        error_type: Optional[ErrorType] = None,
        prompt_tokens: int = 0,
        completion_tokens: int = 0,
    ) -> None:
        """
        Record a single request's metrics.

        Args:
            response_time_ms: Response time in milliseconds
            cost_usd: Cost in USD
            cache_hit: Whether request was served from cache
            error_type: Type of error if request failed
            prompt_tokens: Number of prompt tokens used
            completion_tokens: Number of completion tokens used
        """
        self.request_count += 1

        # Update response time metrics (simplified - real implementation would use time-series)
        self.response_times = ResponseTimeMetrics(
            p50_ms=response_time_ms,  # Placeholder - would calculate from distribution
            p95_ms=response_time_ms,
            p99_ms=response_time_ms,
            min_ms=min(self.response_times.min_ms or float("inf"), response_time_ms),
            max_ms=max(self.response_times.max_ms, response_time_ms),
            avg_ms=(
                (
                    self.response_times.avg_ms * (self.request_count - 1)
                    + response_time_ms
                )
                / self.request_count
            ),
            total_requests=self.request_count,
        )

        # Update cost metrics
        self.costs.add_request_cost(cost_usd, prompt_tokens, completion_tokens)

        # Update cache metrics
        if cache_hit:
            self.cache.record_hit()
        else:
            self.cache.record_miss()

        # Update error metrics
        if error_type:
            self.errors.increment_error(error_type)
            self.errors.error_rate = self.errors.total_errors / self.request_count

        self.updated_at = datetime.now(UTC)

    def get_period_duration(self) -> timedelta:
        """Get duration of the metrics period."""
        return self.period_end - self.period_start

    def is_period_active(self) -> bool:
        """Check if metrics period is currently active."""
        now = datetime.now(UTC)
        return self.period_start <= now <= self.period_end

    def get_requests_per_second(self) -> float:
        """Calculate average requests per second."""
        duration_seconds = self.get_period_duration().total_seconds()
        return self.request_count / duration_seconds if duration_seconds > 0 else 0.0

    def get_error_percentage(self) -> float:
        """Get error percentage."""
        return (self.errors.error_rate * 100) if self.request_count > 0 else 0.0

    def get_avg_tokens_per_request(self) -> float:
        """Get average tokens per request."""
        return (
            self.costs.token_count / self.request_count
            if self.request_count > 0
            else 0.0
        )

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            "id": str(self.id),
            "agent_name": self.agent_name,
            "period": self.period.value,
            "period_start": self.period_start.isoformat(),
            "period_end": self.period_end.isoformat(),
            "request_count": self.request_count,
            "user_count": self.user_count,
            "response_times": self.response_times.to_dict(),
            "errors": self.errors.to_dict(),
            "costs": self.costs.to_dict(),
            "cache": self.cache.to_dict(),
            "requests_per_second": self.get_requests_per_second(),
            "error_percentage": self.get_error_percentage(),
            "avg_tokens_per_request": self.get_avg_tokens_per_request(),
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }
