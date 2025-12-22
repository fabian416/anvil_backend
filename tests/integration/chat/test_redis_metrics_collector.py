"""
Integration tests for RedisMetricsCollectorAdapter.

Tests Redis-based metrics collection and aggregation.
"""

import pytest
from datetime import datetime, timedelta
from uuid import uuid4

from redis.asyncio import Redis

from app.infrastructure.adapters.chat.redis_metrics_collector_adapter import (
    RedisMetricsCollectorAdapter,
)
from app.domain.entities.chat.performance_metrics import (
    AggregationPeriod,
    ErrorType,
)


@pytest.fixture
async def redis_client() -> Redis:
    """Get Redis client for testing."""
    # Create Redis client for testing
    redis = Redis(
        host="localhost",
        port=6379,
        db=15,  # Use separate DB for testing
        decode_responses=False,
    )

    # Ensure we can connect
    await redis.ping()

    yield redis

    # Cleanup: flush test database
    await redis.flushdb()
    await redis.close()


@pytest.fixture
async def metrics_collector(redis_client: Redis) -> RedisMetricsCollectorAdapter:
    """Get metrics collector adapter for testing."""
    return RedisMetricsCollectorAdapter(
        redis_client=redis_client,
        key_prefix="test:metrics",
    )


class TestRedisMetricsCollectorAdapter:
    """Tests for RedisMetricsCollectorAdapter."""

    @pytest.mark.asyncio
    async def test_record_response_time(
        self, metrics_collector: RedisMetricsCollectorAdapter
    ) -> None:
        """Test recording response time."""
        result = await metrics_collector.record_response_time(
            agent_name="test_agent",
            response_time_ms=150.0,
        )

        assert result is True

    @pytest.mark.asyncio
    async def test_record_request(
        self, metrics_collector: RedisMetricsCollectorAdapter
    ) -> None:
        """Test recording request."""
        user_id = uuid4()

        result = await metrics_collector.record_request(
            agent_name="test_agent",
            user_id=user_id,
        )

        assert result is True

    @pytest.mark.asyncio
    async def test_record_error(
        self, metrics_collector: RedisMetricsCollectorAdapter
    ) -> None:
        """Test recording error."""
        result = await metrics_collector.record_error(
            agent_name="test_agent",
            error_type=ErrorType.TIMEOUT,
            error_message="Request timed out",
        )

        assert result is True

    @pytest.mark.asyncio
    async def test_record_cost(
        self, metrics_collector: RedisMetricsCollectorAdapter
    ) -> None:
        """Test recording cost."""
        result = await metrics_collector.record_cost(
            agent_name="test_agent",
            cost_usd=0.05,
            prompt_tokens=100,
            completion_tokens=50,
        )

        assert result is True

    @pytest.mark.asyncio
    async def test_record_cache_hit(
        self, metrics_collector: RedisMetricsCollectorAdapter
    ) -> None:
        """Test recording cache hit."""
        result = await metrics_collector.record_cache_hit(
            agent_name="test_agent",
        )

        assert result is True

    @pytest.mark.asyncio
    async def test_record_cache_miss(
        self, metrics_collector: RedisMetricsCollectorAdapter
    ) -> None:
        """Test recording cache miss."""
        result = await metrics_collector.record_cache_miss(
            agent_name="test_agent",
        )

        assert result is True

    @pytest.mark.asyncio
    async def test_get_response_time_percentiles(
        self, metrics_collector: RedisMetricsCollectorAdapter
    ) -> None:
        """Test getting response time percentiles."""
        # Record multiple response times
        now = datetime.utcnow()

        for ms in [50.0, 100.0, 150.0, 200.0, 250.0, 300.0, 350.0, 400.0, 450.0, 500.0]:
            await metrics_collector.record_response_time(
                agent_name="test_agent",
                response_time_ms=ms,
                timestamp=now,
            )

        # Get percentiles
        end = now + timedelta(seconds=1)
        percentiles = await metrics_collector.get_response_time_percentiles(
            agent_name="test_agent",
            start_time=now - timedelta(seconds=1),
            end_time=end,
        )

        assert percentiles["count"] == 10
        assert percentiles["min"] == 50.0
        assert percentiles["max"] == 500.0
        assert percentiles["avg"] == 275.0
        assert 200.0 <= percentiles["p50"] <= 300.0
        assert 400.0 <= percentiles["p95"] <= 500.0

    @pytest.mark.asyncio
    async def test_get_error_counts_by_type(
        self, metrics_collector: RedisMetricsCollectorAdapter
    ) -> None:
        """Test getting error counts by type."""
        now = datetime.utcnow()

        # Record errors of different types
        await metrics_collector.record_error(
            agent_name="test_agent",
            error_type=ErrorType.TIMEOUT,
            timestamp=now,
        )
        await metrics_collector.record_error(
            agent_name="test_agent",
            error_type=ErrorType.TIMEOUT,
            timestamp=now,
        )
        await metrics_collector.record_error(
            agent_name="test_agent",
            error_type=ErrorType.RATE_LIMIT,
            timestamp=now,
        )

        # Get error counts
        end = now + timedelta(seconds=1)
        error_counts = await metrics_collector.get_error_counts_by_type(
            agent_name="test_agent",
            start_time=now - timedelta(seconds=1),
            end_time=end,
        )

        assert error_counts[ErrorType.TIMEOUT] == 2
        assert error_counts[ErrorType.RATE_LIMIT] == 1

    @pytest.mark.asyncio
    async def test_get_total_cost(
        self, metrics_collector: RedisMetricsCollectorAdapter
    ) -> None:
        """Test getting total cost."""
        now = datetime.utcnow()

        # Record costs
        await metrics_collector.record_cost(
            agent_name="test_agent",
            cost_usd=0.05,
            prompt_tokens=100,
            completion_tokens=50,
            timestamp=now,
        )
        await metrics_collector.record_cost(
            agent_name="test_agent",
            cost_usd=0.10,
            prompt_tokens=200,
            completion_tokens=100,
            timestamp=now,
        )

        # Get total cost
        end = now + timedelta(seconds=1)
        total_cost = await metrics_collector.get_total_cost(
            agent_name="test_agent",
            start_time=now - timedelta(seconds=1),
            end_time=end,
        )

        assert total_cost == 0.15

    @pytest.mark.asyncio
    async def test_get_cache_hit_rate(
        self, metrics_collector: RedisMetricsCollectorAdapter
    ) -> None:
        """Test getting cache hit rate."""
        now = datetime.utcnow()

        # Record cache hits and misses
        await metrics_collector.record_cache_hit(
            agent_name="test_agent",
            timestamp=now,
        )
        await metrics_collector.record_cache_hit(
            agent_name="test_agent",
            timestamp=now,
        )
        await metrics_collector.record_cache_hit(
            agent_name="test_agent",
            timestamp=now,
        )
        await metrics_collector.record_cache_miss(
            agent_name="test_agent",
            timestamp=now,
        )

        # Get hit rate
        end = now + timedelta(seconds=1)
        hit_rate = await metrics_collector.get_cache_hit_rate(
            agent_name="test_agent",
            start_time=now - timedelta(seconds=1),
            end_time=end,
        )

        assert hit_rate == 0.75

    @pytest.mark.asyncio
    async def test_get_metrics(
        self, metrics_collector: RedisMetricsCollectorAdapter
    ) -> None:
        """Test getting aggregated metrics."""
        now = datetime.utcnow()
        end = now + timedelta(hours=1)

        # Record various metrics
        await metrics_collector.record_response_time(
            agent_name="test_agent",
            response_time_ms=150.0,
            timestamp=now,
        )
        await metrics_collector.record_request(
            agent_name="test_agent",
            user_id=uuid4(),
            timestamp=now,
        )
        await metrics_collector.record_cost(
            agent_name="test_agent",
            cost_usd=0.05,
            prompt_tokens=100,
            completion_tokens=50,
            timestamp=now,
        )
        await metrics_collector.record_cache_hit(
            agent_name="test_agent",
            timestamp=now,
        )

        # Get aggregated metrics
        metrics = await metrics_collector.get_metrics(
            agent_name="test_agent",
            period=AggregationPeriod.HOURLY,
            start_time=now - timedelta(seconds=1),
            end_time=end,
        )

        assert metrics is not None
        assert metrics.agent_name == "test_agent"
        assert metrics.period == AggregationPeriod.HOURLY
        assert metrics.request_count >= 1
        assert metrics.costs.total_cost_usd == 0.05
        assert metrics.cache.hit_rate == 1.0

    @pytest.mark.asyncio
    async def test_get_top_agents_by_requests(
        self, metrics_collector: RedisMetricsCollectorAdapter
    ) -> None:
        """Test getting top agents by request count."""
        now = datetime.utcnow()

        # Record requests for different agents
        for _ in range(10):
            await metrics_collector.record_request(
                agent_name="agent_1",
                timestamp=now,
            )

        for _ in range(5):
            await metrics_collector.record_request(
                agent_name="agent_2",
                timestamp=now,
            )

        for _ in range(3):
            await metrics_collector.record_request(
                agent_name="agent_3",
                timestamp=now,
            )

        # Get top agents
        end = now + timedelta(seconds=1)
        top_agents = await metrics_collector.get_top_agents_by_requests(
            start_time=now - timedelta(seconds=1),
            end_time=end,
            limit=3,
        )

        assert len(top_agents) == 3
        assert top_agents[0][0] == "agent_1"
        assert top_agents[0][1] == 10
        assert top_agents[1][0] == "agent_2"
        assert top_agents[1][1] == 5

    @pytest.mark.asyncio
    async def test_get_top_agents_by_cost(
        self, metrics_collector: RedisMetricsCollectorAdapter
    ) -> None:
        """Test getting top agents by cost."""
        now = datetime.utcnow()

        # Record costs for different agents
        await metrics_collector.record_cost(
            agent_name="agent_1",
            cost_usd=1.00,
            prompt_tokens=1000,
            completion_tokens=500,
            timestamp=now,
        )

        await metrics_collector.record_cost(
            agent_name="agent_2",
            cost_usd=0.50,
            prompt_tokens=500,
            completion_tokens=250,
            timestamp=now,
        )

        # Get top agents
        end = now + timedelta(seconds=1)
        top_agents = await metrics_collector.get_top_agents_by_cost(
            start_time=now - timedelta(seconds=1),
            end_time=end,
            limit=2,
        )

        assert len(top_agents) == 2
        assert top_agents[0][0] == "agent_1"
        assert top_agents[0][1] == 1.00

    @pytest.mark.asyncio
    async def test_get_top_agents_by_errors(
        self, metrics_collector: RedisMetricsCollectorAdapter
    ) -> None:
        """Test getting top agents by error count."""
        now = datetime.utcnow()

        # Record errors for different agents
        for _ in range(5):
            await metrics_collector.record_error(
                agent_name="agent_1",
                error_type=ErrorType.TIMEOUT,
                timestamp=now,
            )

        for _ in range(2):
            await metrics_collector.record_error(
                agent_name="agent_2",
                error_type=ErrorType.RATE_LIMIT,
                timestamp=now,
            )

        # Get top agents
        end = now + timedelta(seconds=1)
        top_agents = await metrics_collector.get_top_agents_by_errors(
            start_time=now - timedelta(seconds=1),
            end_time=end,
            limit=2,
        )

        assert len(top_agents) == 2
        assert top_agents[0][0] == "agent_1"
        assert top_agents[0][1] == 5

    @pytest.mark.asyncio
    async def test_cleanup_old_metrics(
        self, metrics_collector: RedisMetricsCollectorAdapter
    ) -> None:
        """Test cleaning up old metrics."""
        now = datetime.utcnow()
        old_time = now - timedelta(days=10)

        # Record old metrics
        await metrics_collector.record_response_time(
            agent_name="test_agent",
            response_time_ms=150.0,
            timestamp=old_time,
        )

        # Record new metrics
        await metrics_collector.record_response_time(
            agent_name="test_agent",
            response_time_ms=200.0,
            timestamp=now,
        )

        # Cleanup old metrics (retain only last 7 days)
        deleted = await metrics_collector.cleanup_old_metrics(retention_days=7)

        assert deleted >= 1

        # Verify new metrics still exist
        percentiles = await metrics_collector.get_response_time_percentiles(
            agent_name="test_agent",
            start_time=now - timedelta(seconds=1),
            end_time=now + timedelta(seconds=1),
        )

        assert percentiles["count"] == 1
        assert percentiles["avg"] == 200.0

    @pytest.mark.asyncio
    async def test_global_metrics(
        self, metrics_collector: RedisMetricsCollectorAdapter
    ) -> None:
        """Test recording and retrieving global metrics (no agent)."""
        now = datetime.utcnow()

        # Record global metrics
        await metrics_collector.record_response_time(
            agent_name=None,
            response_time_ms=100.0,
            timestamp=now,
        )
        await metrics_collector.record_request(
            agent_name=None,
            timestamp=now,
        )

        # Get global metrics
        end = now + timedelta(hours=1)
        metrics = await metrics_collector.get_metrics(
            agent_name=None,
            period=AggregationPeriod.HOURLY,
            start_time=now - timedelta(seconds=1),
            end_time=end,
        )

        assert metrics is not None
        assert metrics.agent_name is None
        assert metrics.request_count >= 1

    @pytest.mark.asyncio
    async def test_concurrent_recordings(
        self, metrics_collector: RedisMetricsCollectorAdapter
    ) -> None:
        """Test concurrent metric recordings."""
        import asyncio

        now = datetime.utcnow()

        # Record metrics concurrently
        tasks = []
        for i in range(100):
            tasks.append(
                metrics_collector.record_response_time(
                    agent_name="test_agent",
                    response_time_ms=float(i),
                    timestamp=now,
                )
            )

        results = await asyncio.gather(*tasks)

        # All should succeed
        assert all(results)

        # Verify count
        end = now + timedelta(seconds=1)
        percentiles = await metrics_collector.get_response_time_percentiles(
            agent_name="test_agent",
            start_time=now - timedelta(seconds=1),
            end_time=end,
        )

        assert percentiles["count"] == 100

    @pytest.mark.asyncio
    async def test_metrics_isolation_by_agent(
        self, metrics_collector: RedisMetricsCollectorAdapter
    ) -> None:
        """Test that metrics are isolated by agent."""
        now = datetime.utcnow()

        # Record metrics for agent 1
        await metrics_collector.record_response_time(
            agent_name="agent_1",
            response_time_ms=100.0,
            timestamp=now,
        )

        # Record metrics for agent 2
        await metrics_collector.record_response_time(
            agent_name="agent_2",
            response_time_ms=200.0,
            timestamp=now,
        )

        # Get metrics for agent 1
        end = now + timedelta(seconds=1)
        percentiles_1 = await metrics_collector.get_response_time_percentiles(
            agent_name="agent_1",
            start_time=now - timedelta(seconds=1),
            end_time=end,
        )

        # Get metrics for agent 2
        percentiles_2 = await metrics_collector.get_response_time_percentiles(
            agent_name="agent_2",
            start_time=now - timedelta(seconds=1),
            end_time=end,
        )

        # Verify isolation
        assert percentiles_1["avg"] == 100.0
        assert percentiles_2["avg"] == 200.0
