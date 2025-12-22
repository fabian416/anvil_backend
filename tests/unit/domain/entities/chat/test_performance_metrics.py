"""
Unit tests for PerformanceMetrics entity.
"""

from datetime import datetime, timedelta
from uuid import uuid4
import pytest

from app.domain.entities.chat.performance_metrics import (
    PerformanceMetrics,
    ResponseTimeMetrics,
    ErrorMetrics,
    CostMetrics,
    CacheMetrics,
    AggregationPeriod,
    ErrorType,
    MetricType,
)


class TestResponseTimeMetrics:
    """Tests for ResponseTimeMetrics."""

    def test_create_response_time_metrics(self) -> None:
        """Test creating response time metrics."""
        metrics = ResponseTimeMetrics(
            p50_ms=100.0,
            p95_ms=250.0,
            p99_ms=400.0,
            min_ms=50.0,
            max_ms=500.0,
            avg_ms=150.0,
            total_requests=1000,
        )

        assert metrics.p50_ms == 100.0
        assert metrics.p95_ms == 250.0
        assert metrics.p99_ms == 400.0
        assert metrics.total_requests == 1000

    def test_is_within_sla_success(self) -> None:
        """Test SLA check when within limits."""
        metrics = ResponseTimeMetrics(
            p50_ms=100.0,
            p95_ms=250.0,
            p99_ms=400.0,
            min_ms=50.0,
            max_ms=500.0,
            avg_ms=150.0,
            total_requests=1000,
        )

        assert metrics.is_within_sla(300.0) is True

    def test_is_within_sla_failure(self) -> None:
        """Test SLA check when exceeding limits."""
        metrics = ResponseTimeMetrics(
            p50_ms=100.0,
            p95_ms=250.0,
            p99_ms=400.0,
            min_ms=50.0,
            max_ms=500.0,
            avg_ms=150.0,
            total_requests=1000,
        )

        assert metrics.is_within_sla(200.0) is False

    def test_to_dict(self) -> None:
        """Test conversion to dictionary."""
        metrics = ResponseTimeMetrics(
            p50_ms=100.0,
            p95_ms=250.0,
            p99_ms=400.0,
            min_ms=50.0,
            max_ms=500.0,
            avg_ms=150.0,
            total_requests=1000,
        )

        result = metrics.to_dict()

        assert result["p50_ms"] == 100.0
        assert result["p95_ms"] == 250.0
        assert result["total_requests"] == 1000


class TestErrorMetrics:
    """Tests for ErrorMetrics."""

    def test_create_error_metrics(self) -> None:
        """Test creating error metrics."""
        metrics = ErrorMetrics(
            total_errors=10,
            error_rate=0.05,
        )

        assert metrics.total_errors == 10
        assert metrics.error_rate == 0.05

    def test_increment_error(self) -> None:
        """Test incrementing error count."""
        metrics = ErrorMetrics(
            total_errors=0,
            error_rate=0.0,
        )

        metrics.increment_error(ErrorType.TIMEOUT)

        assert metrics.total_errors == 1
        assert metrics.errors_by_type[ErrorType.TIMEOUT] == 1
        assert metrics.last_error_timestamp is not None

    def test_increment_error_multiple_types(self) -> None:
        """Test incrementing multiple error types."""
        metrics = ErrorMetrics(
            total_errors=0,
            error_rate=0.0,
        )

        metrics.increment_error(ErrorType.TIMEOUT)
        metrics.increment_error(ErrorType.TIMEOUT)
        metrics.increment_error(ErrorType.RATE_LIMIT)

        assert metrics.total_errors == 3
        assert metrics.errors_by_type[ErrorType.TIMEOUT] == 2
        assert metrics.errors_by_type[ErrorType.RATE_LIMIT] == 1

    def test_get_most_common_error(self) -> None:
        """Test getting most common error type."""
        metrics = ErrorMetrics(
            total_errors=0,
            error_rate=0.0,
        )

        metrics.increment_error(ErrorType.TIMEOUT)
        metrics.increment_error(ErrorType.TIMEOUT)
        metrics.increment_error(ErrorType.RATE_LIMIT)

        assert metrics.get_most_common_error() == ErrorType.TIMEOUT

    def test_get_most_common_error_empty(self) -> None:
        """Test getting most common error when no errors."""
        metrics = ErrorMetrics(
            total_errors=0,
            error_rate=0.0,
        )

        assert metrics.get_most_common_error() is None

    def test_to_dict(self) -> None:
        """Test conversion to dictionary."""
        metrics = ErrorMetrics(
            total_errors=5,
            error_rate=0.02,
        )
        metrics.increment_error(ErrorType.TIMEOUT)

        result = metrics.to_dict()

        assert result["total_errors"] == 6
        assert result["error_rate"] == 0.02
        assert "errors_by_type" in result


class TestCostMetrics:
    """Tests for CostMetrics."""

    def test_create_cost_metrics(self) -> None:
        """Test creating cost metrics."""
        metrics = CostMetrics(
            total_cost_usd=10.50,
            token_count=5000,
            api_call_count=100,
            avg_cost_per_request_usd=0.105,
        )

        assert metrics.total_cost_usd == 10.50
        assert metrics.token_count == 5000
        assert metrics.api_call_count == 100

    def test_add_request_cost(self) -> None:
        """Test adding request cost."""
        metrics = CostMetrics(
            total_cost_usd=0.0,
            token_count=0,
            api_call_count=0,
            avg_cost_per_request_usd=0.0,
        )

        metrics.add_request_cost(0.15, prompt_tokens=100, completion_tokens=50)

        assert metrics.total_cost_usd == 0.15
        assert metrics.token_count == 150
        assert metrics.prompt_tokens == 100
        assert metrics.completion_tokens == 50
        assert metrics.api_call_count == 1
        assert metrics.avg_cost_per_request_usd == 0.15

    def test_add_request_cost_multiple(self) -> None:
        """Test adding multiple request costs."""
        metrics = CostMetrics(
            total_cost_usd=0.0,
            token_count=0,
            api_call_count=0,
            avg_cost_per_request_usd=0.0,
        )

        metrics.add_request_cost(0.10, prompt_tokens=100, completion_tokens=50)
        metrics.add_request_cost(0.20, prompt_tokens=200, completion_tokens=100)

        assert abs(metrics.total_cost_usd - 0.30) < 0.001
        assert metrics.token_count == 450
        assert metrics.api_call_count == 2
        assert abs(metrics.avg_cost_per_request_usd - 0.15) < 0.001

    def test_is_within_budget_success(self) -> None:
        """Test budget check when within limits."""
        metrics = CostMetrics(
            total_cost_usd=10.0,
            token_count=5000,
            api_call_count=100,
            avg_cost_per_request_usd=0.10,
        )

        assert metrics.is_within_budget(20.0) is True

    def test_is_within_budget_failure(self) -> None:
        """Test budget check when exceeding limits."""
        metrics = CostMetrics(
            total_cost_usd=10.0,
            token_count=5000,
            api_call_count=100,
            avg_cost_per_request_usd=0.10,
        )

        assert metrics.is_within_budget(5.0) is False

    def test_to_dict(self) -> None:
        """Test conversion to dictionary."""
        metrics = CostMetrics(
            total_cost_usd=10.50,
            token_count=5000,
            api_call_count=100,
            avg_cost_per_request_usd=0.105,
            prompt_tokens=3000,
            completion_tokens=2000,
        )

        result = metrics.to_dict()

        assert result["total_cost_usd"] == 10.50
        assert result["token_count"] == 5000
        assert result["prompt_tokens"] == 3000


class TestCacheMetrics:
    """Tests for CacheMetrics."""

    def test_create_cache_metrics(self) -> None:
        """Test creating cache metrics."""
        metrics = CacheMetrics(
            total_requests=100,
            cache_hits=75,
            cache_misses=25,
            hit_rate=0.75,
        )

        assert metrics.total_requests == 100
        assert metrics.cache_hits == 75
        assert metrics.hit_rate == 0.75

    def test_record_hit(self) -> None:
        """Test recording cache hit."""
        metrics = CacheMetrics(
            total_requests=0,
            cache_hits=0,
            cache_misses=0,
            hit_rate=0.0,
        )

        metrics.record_hit()

        assert metrics.total_requests == 1
        assert metrics.cache_hits == 1
        assert metrics.hit_rate == 1.0

    def test_record_miss(self) -> None:
        """Test recording cache miss."""
        metrics = CacheMetrics(
            total_requests=0,
            cache_hits=0,
            cache_misses=0,
            hit_rate=0.0,
        )

        metrics.record_miss()

        assert metrics.total_requests == 1
        assert metrics.cache_misses == 1
        assert metrics.hit_rate == 0.0

    def test_record_mixed(self) -> None:
        """Test recording mixed hits and misses."""
        metrics = CacheMetrics(
            total_requests=0,
            cache_hits=0,
            cache_misses=0,
            hit_rate=0.0,
        )

        metrics.record_hit()
        metrics.record_hit()
        metrics.record_hit()
        metrics.record_miss()

        assert metrics.total_requests == 4
        assert metrics.cache_hits == 3
        assert metrics.cache_misses == 1
        assert metrics.hit_rate == 0.75

    def test_to_dict(self) -> None:
        """Test conversion to dictionary."""
        metrics = CacheMetrics(
            total_requests=100,
            cache_hits=75,
            cache_misses=25,
            hit_rate=0.75,
        )

        result = metrics.to_dict()

        assert result["total_requests"] == 100
        assert result["cache_hits"] == 75
        assert result["hit_rate"] == 0.75


class TestPerformanceMetrics:
    """Tests for PerformanceMetrics entity."""

    def test_create_performance_metrics(self) -> None:
        """Test creating performance metrics."""
        now = datetime.utcnow()
        end = now + timedelta(hours=1)

        metrics = PerformanceMetrics.create(
            agent_name="test_agent",
            period=AggregationPeriod.HOURLY,
            period_start=now,
            period_end=end,
        )

        assert metrics.agent_name == "test_agent"
        assert metrics.period == AggregationPeriod.HOURLY
        assert metrics.period_start == now
        assert metrics.period_end == end
        assert metrics.request_count == 0
        assert metrics.response_times.total_requests == 0

    def test_record_request(self) -> None:
        """Test recording a request."""
        now = datetime.utcnow()
        end = now + timedelta(hours=1)

        metrics = PerformanceMetrics.create(
            agent_name="test_agent",
            period=AggregationPeriod.HOURLY,
            period_start=now,
            period_end=end,
        )

        metrics.record_request(
            response_time_ms=150.0,
            cost_usd=0.05,
            cache_hit=False,
            prompt_tokens=100,
            completion_tokens=50,
        )

        assert metrics.request_count == 1
        assert metrics.costs.total_cost_usd == 0.05
        assert metrics.costs.token_count == 150
        assert metrics.cache.total_requests == 1
        assert metrics.cache.cache_misses == 1

    def test_record_request_with_error(self) -> None:
        """Test recording a request with error."""
        now = datetime.utcnow()
        end = now + timedelta(hours=1)

        metrics = PerformanceMetrics.create(
            agent_name="test_agent",
            period=AggregationPeriod.HOURLY,
            period_start=now,
            period_end=end,
        )

        metrics.record_request(
            response_time_ms=150.0,
            cost_usd=0.05,
            cache_hit=False,
            error_type=ErrorType.TIMEOUT,
        )

        assert metrics.request_count == 1
        assert metrics.errors.total_errors == 1
        assert metrics.errors.errors_by_type[ErrorType.TIMEOUT] == 1
        assert metrics.errors.error_rate == 1.0

    def test_record_request_with_cache_hit(self) -> None:
        """Test recording request with cache hit."""
        now = datetime.utcnow()
        end = now + timedelta(hours=1)

        metrics = PerformanceMetrics.create(
            agent_name="test_agent",
            period=AggregationPeriod.HOURLY,
            period_start=now,
            period_end=end,
        )

        metrics.record_request(
            response_time_ms=50.0,
            cost_usd=0.0,
            cache_hit=True,
        )

        assert metrics.cache.cache_hits == 1
        assert metrics.cache.hit_rate == 1.0

    def test_get_period_duration(self) -> None:
        """Test getting period duration."""
        now = datetime.utcnow()
        end = now + timedelta(hours=2)

        metrics = PerformanceMetrics.create(
            agent_name="test_agent",
            period=AggregationPeriod.HOURLY,
            period_start=now,
            period_end=end,
        )

        duration = metrics.get_period_duration()
        assert duration.total_seconds() == 7200.0

    def test_is_period_active(self) -> None:
        """Test checking if period is active."""
        now = datetime.utcnow()
        past = now - timedelta(hours=2)
        future = now + timedelta(hours=2)

        # Active period
        active_metrics = PerformanceMetrics.create(
            agent_name="test_agent",
            period=AggregationPeriod.HOURLY,
            period_start=past,
            period_end=future,
        )
        assert active_metrics.is_period_active() is True

        # Inactive period (in past)
        past_start = now - timedelta(hours=3)
        past_end = now - timedelta(hours=2)
        past_metrics = PerformanceMetrics.create(
            agent_name="test_agent",
            period=AggregationPeriod.HOURLY,
            period_start=past_start,
            period_end=past_end,
        )
        assert past_metrics.is_period_active() is False

    def test_get_requests_per_second(self) -> None:
        """Test calculating requests per second."""
        now = datetime.utcnow()
        end = now + timedelta(hours=1)

        metrics = PerformanceMetrics.create(
            agent_name="test_agent",
            period=AggregationPeriod.HOURLY,
            period_start=now,
            period_end=end,
        )

        # Record 3600 requests (1 per second)
        for _ in range(3600):
            metrics.record_request(
                response_time_ms=100.0,
                cost_usd=0.01,
                cache_hit=False,
            )

        rps = metrics.get_requests_per_second()
        assert rps == 1.0

    def test_get_error_percentage(self) -> None:
        """Test calculating error percentage."""
        now = datetime.utcnow()
        end = now + timedelta(hours=1)

        metrics = PerformanceMetrics.create(
            agent_name="test_agent",
            period=AggregationPeriod.HOURLY,
            period_start=now,
            period_end=end,
        )

        # Record 80 successful + 20 failed requests
        for _ in range(80):
            metrics.record_request(
                response_time_ms=100.0,
                cost_usd=0.01,
                cache_hit=False,
            )

        for _ in range(20):
            metrics.record_request(
                response_time_ms=100.0,
                cost_usd=0.01,
                cache_hit=False,
                error_type=ErrorType.TIMEOUT,
            )

        error_pct = metrics.get_error_percentage()
        assert error_pct == 20.0

    def test_get_avg_tokens_per_request(self) -> None:
        """Test calculating average tokens per request."""
        now = datetime.utcnow()
        end = now + timedelta(hours=1)

        metrics = PerformanceMetrics.create(
            agent_name="test_agent",
            period=AggregationPeriod.HOURLY,
            period_start=now,
            period_end=end,
        )

        metrics.record_request(
            response_time_ms=100.0,
            cost_usd=0.05,
            cache_hit=False,
            prompt_tokens=100,
            completion_tokens=50,
        )

        metrics.record_request(
            response_time_ms=100.0,
            cost_usd=0.10,
            cache_hit=False,
            prompt_tokens=200,
            completion_tokens=100,
        )

        avg_tokens = metrics.get_avg_tokens_per_request()
        assert avg_tokens == 225.0  # (150 + 300) / 2

    def test_to_dict(self) -> None:
        """Test conversion to dictionary."""
        now = datetime.utcnow()
        end = now + timedelta(hours=1)

        metrics = PerformanceMetrics.create(
            agent_name="test_agent",
            period=AggregationPeriod.HOURLY,
            period_start=now,
            period_end=end,
        )

        metrics.record_request(
            response_time_ms=150.0,
            cost_usd=0.05,
            cache_hit=True,
            prompt_tokens=100,
            completion_tokens=50,
        )

        result = metrics.to_dict()

        assert result["agent_name"] == "test_agent"
        assert result["period"] == "hourly"
        assert result["request_count"] == 1
        assert "response_times" in result
        assert "errors" in result
        assert "costs" in result
        assert "cache" in result


class TestEnums:
    """Tests for enums."""

    def test_metric_type_enum(self) -> None:
        """Test MetricType enum."""
        assert MetricType.RESPONSE_TIME.value == "response_time"
        assert MetricType.ERROR_RATE.value == "error_rate"
        assert MetricType.COST.value == "cost"

    def test_error_type_enum(self) -> None:
        """Test ErrorType enum."""
        assert ErrorType.TIMEOUT.value == "timeout"
        assert ErrorType.RATE_LIMIT.value == "rate_limit"
        assert ErrorType.LLM_ERROR.value == "llm_error"

    def test_aggregation_period_enum(self) -> None:
        """Test AggregationPeriod enum."""
        assert AggregationPeriod.MINUTE.value == "minute"
        assert AggregationPeriod.HOURLY.value == "hourly"
        assert AggregationPeriod.DAILY.value == "daily"
        assert AggregationPeriod.WEEKLY.value == "weekly"
