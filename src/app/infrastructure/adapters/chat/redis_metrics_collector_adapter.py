"""
Redis metrics collector adapter implementation.

Implements MetricsCollector port using Redis time-series data structures
(sorted sets) for high-performance metrics storage and aggregation.
"""

import json
from datetime import datetime, timedelta, UTC
from typing import List, Optional, Dict
from uuid import UUID
import statistics

from redis.asyncio import Redis

from app.domain.ports.metrics_collector import MetricsCollector
from app.domain.entities.chat.performance_metrics import (
    PerformanceMetrics,
    AggregationPeriod,
    ErrorType,
    ResponseTimeMetrics,
    ErrorMetrics,
    CostMetrics,
    CacheMetrics,
)


class RedisMetricsCollectorAdapter(MetricsCollector):
    """
    Redis implementation of metrics collector.

    Architecture:
    - Sorted Sets: Time-series data with timestamp scores
    - Hashes: Aggregated metrics by period
    - Keys: Structured with prefix:metric_type:agent:period pattern

    Features:
    - High-performance time-series storage
    - Efficient time-based queries
    - Automatic expiration with TTL
    - Support for hourly/daily/weekly rollups
    - Percentile calculations for response times
    """

    def __init__(
        self,
        redis_client: Redis,
        key_prefix: str = "metrics",
    ) -> None:
        """
        Initialize Redis metrics collector adapter.

        Args:
            redis_client: Redis async client
            key_prefix: Prefix for all metric keys
        """
        self._redis = redis_client
        self._prefix = key_prefix

    # =========================================================================
    # KEY GENERATION HELPERS
    # =========================================================================

    def _response_time_key(
        self, agent_name: Optional[str], period: AggregationPeriod
    ) -> str:
        """Generate key for response time sorted set."""
        agent = agent_name or "global"
        return f"{self._prefix}:response_time:{agent}:{period.value}"

    def _request_count_key(
        self, agent_name: Optional[str], period: AggregationPeriod
    ) -> str:
        """Generate key for request count sorted set."""
        agent = agent_name or "global"
        return f"{self._prefix}:request_count:{agent}:{period.value}"

    def _error_key(
        self,
        agent_name: Optional[str],
        error_type: ErrorType,
        period: AggregationPeriod,
    ) -> str:
        """Generate key for error tracking."""
        agent = agent_name or "global"
        return f"{self._prefix}:error:{agent}:{error_type.value}:{period.value}"

    def _cost_key(self, agent_name: Optional[str], period: AggregationPeriod) -> str:
        """Generate key for cost tracking hash."""
        agent = agent_name or "global"
        return f"{self._prefix}:cost:{agent}:{period.value}"

    def _cache_hit_key(
        self, agent_name: Optional[str], period: AggregationPeriod
    ) -> str:
        """Generate key for cache hit counter."""
        agent = agent_name or "global"
        return f"{self._prefix}:cache_hit:{agent}:{period.value}"

    def _cache_miss_key(
        self, agent_name: Optional[str], period: AggregationPeriod
    ) -> str:
        """Generate key for cache miss counter."""
        agent = agent_name or "global"
        return f"{self._prefix}:cache_miss:{agent}:{period.value}"

    def _user_set_key(
        self, agent_name: Optional[str], period: AggregationPeriod
    ) -> str:
        """Generate key for unique user tracking."""
        agent = agent_name or "global"
        return f"{self._prefix}:users:{agent}:{period.value}"

    def _aggregated_key(
        self, agent_name: Optional[str], period: AggregationPeriod, timestamp: datetime
    ) -> str:
        """Generate key for aggregated metrics hash."""
        agent = agent_name or "global"
        period_key = self._get_period_key(period, timestamp)
        return f"{self._prefix}:agg:{agent}:{period.value}:{period_key}"

    def _get_period_key(self, period: AggregationPeriod, timestamp: datetime) -> str:
        """Get period-specific key component from timestamp."""
        if period == AggregationPeriod.MINUTE:
            return timestamp.strftime("%Y%m%d%H%M")
        elif period == AggregationPeriod.HOURLY:
            return timestamp.strftime("%Y%m%d%H")
        elif period == AggregationPeriod.DAILY:
            return timestamp.strftime("%Y%m%d")
        elif period == AggregationPeriod.WEEKLY:
            # ISO week format
            return f"{timestamp.year}W{timestamp.isocalendar()[1]:02d}"
        elif period == AggregationPeriod.MONTHLY:
            return timestamp.strftime("%Y%m")
        return timestamp.strftime("%Y%m%d")

    def _get_ttl_seconds(self, period: AggregationPeriod) -> int:
        """Get TTL in seconds for a given period."""
        ttl_map = {
            AggregationPeriod.MINUTE: 3600,  # 1 hour
            AggregationPeriod.HOURLY: 86400 * 7,  # 7 days
            AggregationPeriod.DAILY: 86400 * 30,  # 30 days
            AggregationPeriod.WEEKLY: 86400 * 90,  # 90 days
            AggregationPeriod.MONTHLY: 86400 * 365,  # 1 year
        }
        return ttl_map.get(period, 86400)

    # =========================================================================
    # RECORDING METHODS
    # =========================================================================

    async def record_response_time(
        self,
        agent_name: Optional[str],
        response_time_ms: float,
        timestamp: Optional[datetime] = None,
    ) -> bool:
        """
        Record a response time measurement.

        Uses sorted sets with timestamp as score for time-series storage.
        """
        try:
            timestamp = timestamp or datetime.now(UTC)
            score = timestamp.timestamp()

            # Record in minute-level sorted set
            key = self._response_time_key(agent_name, AggregationPeriod.MINUTE)
            await self._redis.zadd(key, {str(response_time_ms): score})

            # Set expiration
            ttl = self._get_ttl_seconds(AggregationPeriod.MINUTE)
            await self._redis.expire(key, ttl)

            return True

        except Exception:
            return False

    async def record_request(
        self,
        agent_name: Optional[str],
        user_id: Optional[UUID] = None,
        timestamp: Optional[datetime] = None,
    ) -> bool:
        """
        Record a request occurrence.

        Increments request counter and tracks unique users.
        """
        try:
            timestamp = timestamp or datetime.now(UTC)
            score = timestamp.timestamp()

            # Increment request count in sorted set
            key = self._request_count_key(agent_name, AggregationPeriod.MINUTE)
            # Use timestamp as both value and score to enable counting
            await self._redis.zadd(key, {str(score): score})

            # Set expiration
            ttl = self._get_ttl_seconds(AggregationPeriod.MINUTE)
            await self._redis.expire(key, ttl)

            # Track unique user if provided
            if user_id:
                user_key = self._user_set_key(agent_name, AggregationPeriod.MINUTE)
                await self._redis.sadd(user_key, str(user_id))
                await self._redis.expire(user_key, ttl)

            return True

        except Exception:
            return False

    async def record_error(
        self,
        agent_name: Optional[str],
        error_type: ErrorType,
        error_message: Optional[str] = None,
        timestamp: Optional[datetime] = None,
    ) -> bool:
        """
        Record an error occurrence.

        Tracks errors by type in sorted sets.
        """
        try:
            timestamp = timestamp or datetime.now(UTC)
            score = timestamp.timestamp()

            # Record error in sorted set
            key = self._error_key(agent_name, error_type, AggregationPeriod.MINUTE)
            error_data = json.dumps({
                "timestamp": timestamp.isoformat(),
                "message": error_message,
            })
            await self._redis.zadd(key, {error_data: score})

            # Set expiration
            ttl = self._get_ttl_seconds(AggregationPeriod.MINUTE)
            await self._redis.expire(key, ttl)

            return True

        except Exception:
            return False

    async def record_cost(
        self,
        agent_name: Optional[str],
        cost_usd: float,
        prompt_tokens: int,
        completion_tokens: int,
        timestamp: Optional[datetime] = None,
    ) -> bool:
        """
        Record cost and token usage.

        Stores in hash with timestamp-based key.
        """
        try:
            timestamp = timestamp or datetime.now(UTC)
            key = self._cost_key(agent_name, AggregationPeriod.MINUTE)

            # Increment cost and token counters atomically
            cost_data = {
                "total_cost_usd": cost_usd,
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "api_calls": 1,
            }

            # Use Redis pipeline for atomic updates
            async with self._redis.pipeline(transaction=True) as pipe:
                for field, value in cost_data.items():
                    await pipe.hincrbyfloat(key, field, float(value))
                await pipe.expire(key, self._get_ttl_seconds(AggregationPeriod.MINUTE))
                await pipe.execute()

            return True

        except Exception:
            return False

    async def record_cache_hit(
        self,
        agent_name: Optional[str],
        timestamp: Optional[datetime] = None,
    ) -> bool:
        """Record a cache hit."""
        try:
            timestamp = timestamp or datetime.now(UTC)
            key = self._cache_hit_key(agent_name, AggregationPeriod.MINUTE)

            await self._redis.incr(key)
            await self._redis.expire(
                key, self._get_ttl_seconds(AggregationPeriod.MINUTE)
            )

            return True

        except Exception:
            return False

    async def record_cache_miss(
        self,
        agent_name: Optional[str],
        timestamp: Optional[datetime] = None,
    ) -> bool:
        """Record a cache miss."""
        try:
            timestamp = timestamp or datetime.now(UTC)
            key = self._cache_miss_key(agent_name, AggregationPeriod.MINUTE)

            await self._redis.incr(key)
            await self._redis.expire(
                key, self._get_ttl_seconds(AggregationPeriod.MINUTE)
            )

            return True

        except Exception:
            return False

    # =========================================================================
    # QUERY METHODS
    # =========================================================================

    async def get_metrics(
        self,
        agent_name: Optional[str],
        period: AggregationPeriod,
        start_time: datetime,
        end_time: datetime,
    ) -> Optional[PerformanceMetrics]:
        """
        Get aggregated metrics for a time period.

        Retrieves data from minute-level metrics and aggregates on-the-fly
        or fetches pre-aggregated data from rollup keys.
        """
        try:
            # Get response time metrics
            response_times_dict = await self.get_response_time_percentiles(
                agent_name, start_time, end_time
            )
            response_times = ResponseTimeMetrics(
                p50_ms=response_times_dict.get("p50", 0.0),
                p95_ms=response_times_dict.get("p95", 0.0),
                p99_ms=response_times_dict.get("p99", 0.0),
                min_ms=response_times_dict.get("min", 0.0),
                max_ms=response_times_dict.get("max", 0.0),
                avg_ms=response_times_dict.get("avg", 0.0),
                total_requests=response_times_dict.get("count", 0),
            )

            # Get error metrics
            error_counts = await self.get_error_counts_by_type(
                agent_name, start_time, end_time
            )
            total_errors = sum(error_counts.values())
            request_count = await self._get_request_count(
                agent_name, start_time, end_time
            )
            error_rate = total_errors / request_count if request_count > 0 else 0.0

            errors = ErrorMetrics(
                total_errors=total_errors,
                error_rate=error_rate,
                errors_by_type=error_counts,
            )

            # Get cost metrics
            cost_data = await self._get_cost_data(agent_name, start_time, end_time)
            costs = CostMetrics(
                total_cost_usd=cost_data["total_cost"],
                token_count=cost_data["total_tokens"],
                api_call_count=cost_data["api_calls"],
                avg_cost_per_request_usd=cost_data["avg_cost"],
                prompt_tokens=cost_data["prompt_tokens"],
                completion_tokens=cost_data["completion_tokens"],
            )

            # Get cache metrics
            cache_hit_rate = await self.get_cache_hit_rate(
                agent_name, start_time, end_time
            )
            cache_data = await self._get_cache_data(agent_name, start_time, end_time)
            cache = CacheMetrics(
                total_requests=cache_data["total"],
                cache_hits=cache_data["hits"],
                cache_misses=cache_data["misses"],
                hit_rate=cache_hit_rate,
            )

            # Get user count
            user_count = await self._get_unique_user_count(
                agent_name, start_time, end_time
            )

            # Create metrics entity
            metrics = PerformanceMetrics(
                id=UUID(int=0),  # Will be replaced by actual ID if persisted
                agent_name=agent_name,
                period=period,
                period_start=start_time,
                period_end=end_time,
                response_times=response_times,
                errors=errors,
                costs=costs,
                cache=cache,
                request_count=request_count,
                user_count=user_count,
            )

            return metrics

        except Exception:
            return None

    async def get_metrics_by_agent(
        self,
        period: AggregationPeriod,
        start_time: datetime,
        end_time: datetime,
        limit: int = 10,
    ) -> List[PerformanceMetrics]:
        """Get metrics for multiple agents."""
        try:
            # Get top agents by request count
            top_agents = await self.get_top_agents_by_requests(
                start_time, end_time, limit
            )

            # Fetch metrics for each agent
            metrics_list: List[PerformanceMetrics] = []
            for agent_name, _ in top_agents:
                metrics = await self.get_metrics(
                    agent_name, period, start_time, end_time
                )
                if metrics:
                    metrics_list.append(metrics)

            return metrics_list

        except Exception:
            return []

    async def get_response_time_percentiles(
        self,
        agent_name: Optional[str],
        start_time: datetime,
        end_time: datetime,
    ) -> Dict[str, float]:
        """
        Get response time percentiles for a period.

        Retrieves all response times from sorted set and calculates percentiles.
        """
        try:
            key = self._response_time_key(agent_name, AggregationPeriod.MINUTE)

            # Get all response times in time range
            start_score = start_time.timestamp()
            end_score = end_time.timestamp()

            response_times_raw = await self._redis.zrangebyscore(
                key, start_score, end_score
            )

            if not response_times_raw:
                return {
                    "p50": 0.0,
                    "p95": 0.0,
                    "p99": 0.0,
                    "min": 0.0,
                    "max": 0.0,
                    "avg": 0.0,
                    "count": 0,
                }

            # Convert to floats
            response_times = [float(rt.decode()) for rt in response_times_raw]

            # Calculate percentiles
            sorted_times = sorted(response_times)
            count = len(sorted_times)

            return {
                "p50": self._percentile(sorted_times, 50),
                "p95": self._percentile(sorted_times, 95),
                "p99": self._percentile(sorted_times, 99),
                "min": min(sorted_times),
                "max": max(sorted_times),
                "avg": statistics.mean(sorted_times),
                "count": count,
            }

        except Exception:
            return {
                "p50": 0.0,
                "p95": 0.0,
                "p99": 0.0,
                "min": 0.0,
                "max": 0.0,
                "avg": 0.0,
                "count": 0,
            }

    async def get_error_counts_by_type(
        self,
        agent_name: Optional[str],
        start_time: datetime,
        end_time: datetime,
    ) -> Dict[ErrorType, int]:
        """Get error counts by type for a period."""
        try:
            error_counts: Dict[ErrorType, int] = {}

            start_score = start_time.timestamp()
            end_score = end_time.timestamp()

            # Query each error type
            for error_type in ErrorType:
                key = self._error_key(agent_name, error_type, AggregationPeriod.MINUTE)
                count = await self._redis.zcount(key, start_score, end_score)
                if count > 0:
                    error_counts[error_type] = count

            return error_counts

        except Exception:
            return {}

    async def get_total_cost(
        self,
        agent_name: Optional[str],
        start_time: datetime,
        end_time: datetime,
    ) -> float:
        """Get total cost for a period."""
        try:
            cost_data = await self._get_cost_data(agent_name, start_time, end_time)
            return cost_data["total_cost"]

        except Exception:
            return 0.0

    async def get_cache_hit_rate(
        self,
        agent_name: Optional[str],
        start_time: datetime,
        end_time: datetime,
    ) -> float:
        """Get cache hit rate for a period."""
        try:
            cache_data = await self._get_cache_data(agent_name, start_time, end_time)
            total = cache_data["total"]
            if total == 0:
                return 0.0
            return cache_data["hits"] / total

        except Exception:
            return 0.0

    # =========================================================================
    # AGGREGATION METHODS
    # =========================================================================

    async def aggregate_hourly(
        self,
        start_time: datetime,
        end_time: datetime,
    ) -> int:
        """
        Aggregate minute-level data into hourly rollups.

        Groups minute data by hour and stores in aggregated hash keys.
        """
        try:
            hours_aggregated = 0
            current = start_time.replace(minute=0, second=0, microsecond=0)

            while current <= end_time:
                next_hour = current + timedelta(hours=1)

                # Get all agents with data in this hour
                agents = await self._get_agents_with_data(current, next_hour)

                for agent_name in agents:
                    # Aggregate metrics for this agent and hour
                    metrics = await self.get_metrics(
                        agent_name,
                        AggregationPeriod.HOURLY,
                        current,
                        next_hour,
                    )

                    if metrics:
                        # Store aggregated metrics
                        agg_key = self._aggregated_key(
                            agent_name, AggregationPeriod.HOURLY, current
                        )
                        await self._store_aggregated_metrics(agg_key, metrics)

                hours_aggregated += 1
                current = next_hour

            return hours_aggregated

        except Exception:
            return 0

    async def aggregate_daily(
        self,
        start_time: datetime,
        end_time: datetime,
    ) -> int:
        """Aggregate hourly data into daily rollups."""
        try:
            days_aggregated = 0
            current = start_time.replace(hour=0, minute=0, second=0, microsecond=0)

            while current <= end_time:
                next_day = current + timedelta(days=1)

                agents = await self._get_agents_with_data(current, next_day)

                for agent_name in agents:
                    metrics = await self.get_metrics(
                        agent_name,
                        AggregationPeriod.DAILY,
                        current,
                        next_day,
                    )

                    if metrics:
                        agg_key = self._aggregated_key(
                            agent_name, AggregationPeriod.DAILY, current
                        )
                        await self._store_aggregated_metrics(agg_key, metrics)

                days_aggregated += 1
                current = next_day

            return days_aggregated

        except Exception:
            return 0

    async def aggregate_weekly(
        self,
        start_time: datetime,
        end_time: datetime,
    ) -> int:
        """Aggregate daily data into weekly rollups."""
        try:
            weeks_aggregated = 0
            # Start from Monday of the week
            current = start_time - timedelta(days=start_time.weekday())
            current = current.replace(hour=0, minute=0, second=0, microsecond=0)

            while current <= end_time:
                next_week = current + timedelta(weeks=1)

                agents = await self._get_agents_with_data(current, next_week)

                for agent_name in agents:
                    metrics = await self.get_metrics(
                        agent_name,
                        AggregationPeriod.WEEKLY,
                        current,
                        next_week,
                    )

                    if metrics:
                        agg_key = self._aggregated_key(
                            agent_name, AggregationPeriod.WEEKLY, current
                        )
                        await self._store_aggregated_metrics(agg_key, metrics)

                weeks_aggregated += 1
                current = next_week

            return weeks_aggregated

        except Exception:
            return 0

    # =========================================================================
    # TOP AGENTS QUERIES
    # =========================================================================

    async def get_top_agents_by_requests(
        self,
        start_time: datetime,
        end_time: datetime,
        limit: int = 10,
    ) -> List[tuple[str, int]]:
        """Get top agents by request count."""
        try:
            # Scan for all agent request count keys
            pattern = f"{self._prefix}:request_count:*:minute"
            cursor = 0
            agent_counts: Dict[str, int] = {}

            while True:
                cursor, keys = await self._redis.scan(cursor, match=pattern, count=100)

                for key_bytes in keys:
                    key = key_bytes.decode()
                    # Extract agent name from key
                    parts = key.split(":")
                    if len(parts) >= 3:
                        agent_name = parts[2]

                        # Count requests in time range
                        count = await self._redis.zcount(
                            key, start_time.timestamp(), end_time.timestamp()
                        )
                        if count > 0:
                            agent_counts[agent_name] = (
                                agent_counts.get(agent_name, 0) + count
                            )

                if cursor == 0:
                    break

            # Sort by count and return top N
            sorted_agents = sorted(
                agent_counts.items(), key=lambda x: x[1], reverse=True
            )
            return sorted_agents[:limit]

        except Exception:
            return []

    async def get_top_agents_by_cost(
        self,
        start_time: datetime,
        end_time: datetime,
        limit: int = 10,
    ) -> List[tuple[str, float]]:
        """Get top agents by cost."""
        try:
            pattern = f"{self._prefix}:cost:*:minute"
            cursor = 0
            agent_costs: Dict[str, float] = {}

            while True:
                cursor, keys = await self._redis.scan(cursor, match=pattern, count=100)

                for key_bytes in keys:
                    key = key_bytes.decode()
                    parts = key.split(":")
                    if len(parts) >= 3:
                        agent_name = parts[2]

                        # Get total cost
                        cost_str = await self._redis.hget(key, "total_cost_usd")
                        if cost_str:
                            cost = float(cost_str)
                            agent_costs[agent_name] = (
                                agent_costs.get(agent_name, 0.0) + cost
                            )

                if cursor == 0:
                    break

            sorted_agents = sorted(
                agent_costs.items(), key=lambda x: x[1], reverse=True
            )
            return sorted_agents[:limit]

        except Exception:
            return []

    async def get_top_agents_by_errors(
        self,
        start_time: datetime,
        end_time: datetime,
        limit: int = 10,
    ) -> List[tuple[str, int]]:
        """Get top agents by error count."""
        try:
            pattern = f"{self._prefix}:error:*:minute"
            cursor = 0
            agent_errors: Dict[str, int] = {}

            while True:
                cursor, keys = await self._redis.scan(cursor, match=pattern, count=100)

                for key_bytes in keys:
                    key = key_bytes.decode()
                    parts = key.split(":")
                    if len(parts) >= 3:
                        agent_name = parts[2]

                        count = await self._redis.zcount(
                            key, start_time.timestamp(), end_time.timestamp()
                        )
                        if count > 0:
                            agent_errors[agent_name] = (
                                agent_errors.get(agent_name, 0) + count
                            )

                if cursor == 0:
                    break

            sorted_agents = sorted(
                agent_errors.items(), key=lambda x: x[1], reverse=True
            )
            return sorted_agents[:limit]

        except Exception:
            return []

    # =========================================================================
    # CLEANUP
    # =========================================================================

    async def cleanup_old_metrics(
        self,
        retention_days: int,
    ) -> int:
        """Clean up metrics older than retention period."""
        try:
            cutoff_timestamp = (
                datetime.now(UTC) - timedelta(days=retention_days)
            ).timestamp()

            pattern = f"{self._prefix}:*"
            cursor = 0
            deleted = 0

            while True:
                cursor, keys = await self._redis.scan(cursor, match=pattern, count=100)

                for key_bytes in keys:
                    key = key_bytes.decode()

                    # Check if it's a sorted set
                    key_type = await self._redis.type(key)
                    if key_type == b"zset":
                        # Remove old entries from sorted set
                        removed = await self._redis.zremrangebyscore(
                            key, 0, cutoff_timestamp
                        )
                        deleted += removed

                        # Delete empty sorted sets
                        if await self._redis.zcard(key) == 0:
                            await self._redis.delete(key)

                if cursor == 0:
                    break

            return deleted

        except Exception:
            return 0

    # =========================================================================
    # HELPER METHODS
    # =========================================================================

    async def _get_request_count(
        self,
        agent_name: Optional[str],
        start_time: datetime,
        end_time: datetime,
    ) -> int:
        """Get total request count for a period."""
        try:
            key = self._request_count_key(agent_name, AggregationPeriod.MINUTE)
            count = await self._redis.zcount(
                key, start_time.timestamp(), end_time.timestamp()
            )
            return count or 0

        except Exception:
            return 0

    async def _get_cost_data(
        self,
        agent_name: Optional[str],
        start_time: datetime,
        end_time: datetime,
    ) -> Dict[str, float]:
        """Get cost data for a period."""
        try:
            key = self._cost_key(agent_name, AggregationPeriod.MINUTE)

            # Get all cost fields
            cost_hash = await self._redis.hgetall(key)

            total_cost = float(cost_hash.get(b"total_cost_usd", 0))
            prompt_tokens = int(cost_hash.get(b"prompt_tokens", 0))
            completion_tokens = int(cost_hash.get(b"completion_tokens", 0))
            api_calls = int(cost_hash.get(b"api_calls", 0))

            avg_cost = total_cost / api_calls if api_calls > 0 else 0.0

            return {
                "total_cost": total_cost,
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "total_tokens": prompt_tokens + completion_tokens,
                "api_calls": api_calls,
                "avg_cost": avg_cost,
            }

        except Exception:
            return {
                "total_cost": 0.0,
                "prompt_tokens": 0,
                "completion_tokens": 0,
                "total_tokens": 0,
                "api_calls": 0,
                "avg_cost": 0.0,
            }

    async def _get_cache_data(
        self,
        agent_name: Optional[str],
        start_time: datetime,
        end_time: datetime,
    ) -> Dict[str, int]:
        """Get cache hit/miss data for a period."""
        try:
            hit_key = self._cache_hit_key(agent_name, AggregationPeriod.MINUTE)
            miss_key = self._cache_miss_key(agent_name, AggregationPeriod.MINUTE)

            hits = int(await self._redis.get(hit_key) or 0)
            misses = int(await self._redis.get(miss_key) or 0)

            return {
                "hits": hits,
                "misses": misses,
                "total": hits + misses,
            }

        except Exception:
            return {"hits": 0, "misses": 0, "total": 0}

    async def _get_unique_user_count(
        self,
        agent_name: Optional[str],
        start_time: datetime,
        end_time: datetime,
    ) -> int:
        """Get unique user count for a period."""
        try:
            key = self._user_set_key(agent_name, AggregationPeriod.MINUTE)
            count = await self._redis.scard(key)
            return count or 0

        except Exception:
            return 0

    async def _get_agents_with_data(
        self,
        start_time: datetime,
        end_time: datetime,
    ) -> List[str]:
        """Get list of agents with data in time range."""
        try:
            pattern = f"{self._prefix}:request_count:*:minute"
            cursor = 0
            agents: set[str] = set()

            while True:
                cursor, keys = await self._redis.scan(cursor, match=pattern, count=100)

                for key_bytes in keys:
                    key = key_bytes.decode()
                    parts = key.split(":")
                    if len(parts) >= 3:
                        agent_name = parts[2]
                        # Check if agent has data in range
                        count = await self._redis.zcount(
                            key, start_time.timestamp(), end_time.timestamp()
                        )
                        if count > 0:
                            agents.add(agent_name)

                if cursor == 0:
                    break

            return list(agents)

        except Exception:
            return []

    async def _store_aggregated_metrics(
        self,
        key: str,
        metrics: PerformanceMetrics,
    ) -> bool:
        """Store aggregated metrics in hash."""
        try:
            metrics_dict = metrics.to_dict()

            # Convert nested dicts to JSON strings for hash storage
            metrics_flat = {
                "agent_name": metrics.agent_name or "global",
                "period": metrics.period.value,
                "period_start": metrics.period_start.isoformat(),
                "period_end": metrics.period_end.isoformat(),
                "request_count": metrics.request_count,
                "user_count": metrics.user_count,
                "response_times": json.dumps(metrics_dict["response_times"]),
                "errors": json.dumps(metrics_dict["errors"]),
                "costs": json.dumps(metrics_dict["costs"]),
                "cache": json.dumps(metrics_dict["cache"]),
            }

            await self._redis.hset(key, mapping=metrics_flat)  # type: ignore

            # Set TTL based on period
            ttl = self._get_ttl_seconds(metrics.period)
            await self._redis.expire(key, ttl)

            return True

        except Exception:
            return False

    def _percentile(self, sorted_data: List[float], percentile: float) -> float:
        """Calculate percentile from sorted data."""
        if not sorted_data:
            return 0.0

        k = (len(sorted_data) - 1) * (percentile / 100)
        f = int(k)
        c = f + 1

        if c >= len(sorted_data):
            return sorted_data[-1]

        d0 = sorted_data[f]
        d1 = sorted_data[c]

        return d0 + (d1 - d0) * (k - f)
