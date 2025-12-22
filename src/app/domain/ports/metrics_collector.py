"""
Metrics collector port.

Domain-defined interface for collecting and storing performance metrics.
"""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import List, Optional, Dict
from uuid import UUID

from app.domain.entities.chat.performance_metrics import (
    PerformanceMetrics,
    AggregationPeriod,
    ErrorType,
)


class MetricsCollector(ABC):
    """
    Port for performance metrics collection and storage.

    Abstracts integration with time-series databases and metrics storage
    backends (Redis, InfluxDB, Prometheus, etc.) for language-agnostic
    business logic.
    """

    @abstractmethod
    async def record_response_time(
        self,
        agent_name: Optional[str],
        response_time_ms: float,
        timestamp: Optional[datetime] = None,
    ) -> bool:
        """
        Record a response time measurement.

        Args:
            agent_name: Agent name (None for global metrics)
            response_time_ms: Response time in milliseconds
            timestamp: Timestamp of measurement (defaults to now)

        Returns:
            True if recorded successfully
        """
        pass

    @abstractmethod
    async def record_request(
        self,
        agent_name: Optional[str],
        user_id: Optional[UUID] = None,
        timestamp: Optional[datetime] = None,
    ) -> bool:
        """
        Record a request occurrence.

        Args:
            agent_name: Agent name
            user_id: User identifier
            timestamp: Timestamp of request (defaults to now)

        Returns:
            True if recorded successfully
        """
        pass

    @abstractmethod
    async def record_error(
        self,
        agent_name: Optional[str],
        error_type: ErrorType,
        error_message: Optional[str] = None,
        timestamp: Optional[datetime] = None,
    ) -> bool:
        """
        Record an error occurrence.

        Args:
            agent_name: Agent name
            error_type: Type of error
            error_message: Error message details
            timestamp: Timestamp of error (defaults to now)

        Returns:
            True if recorded successfully
        """
        pass

    @abstractmethod
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

        Args:
            agent_name: Agent name
            cost_usd: Cost in USD
            prompt_tokens: Number of prompt tokens
            completion_tokens: Number of completion tokens
            timestamp: Timestamp of measurement (defaults to now)

        Returns:
            True if recorded successfully
        """
        pass

    @abstractmethod
    async def record_cache_hit(
        self,
        agent_name: Optional[str],
        timestamp: Optional[datetime] = None,
    ) -> bool:
        """
        Record a cache hit.

        Args:
            agent_name: Agent name
            timestamp: Timestamp of hit (defaults to now)

        Returns:
            True if recorded successfully
        """
        pass

    @abstractmethod
    async def record_cache_miss(
        self,
        agent_name: Optional[str],
        timestamp: Optional[datetime] = None,
    ) -> bool:
        """
        Record a cache miss.

        Args:
            agent_name: Agent name
            timestamp: Timestamp of miss (defaults to now)

        Returns:
            True if recorded successfully
        """
        pass

    @abstractmethod
    async def get_metrics(
        self,
        agent_name: Optional[str],
        period: AggregationPeriod,
        start_time: datetime,
        end_time: datetime,
    ) -> Optional[PerformanceMetrics]:
        """
        Get aggregated metrics for a time period.

        Args:
            agent_name: Agent name (None for global metrics)
            period: Aggregation period
            start_time: Start of period
            end_time: End of period

        Returns:
            PerformanceMetrics or None if no data available
        """
        pass

    @abstractmethod
    async def get_metrics_by_agent(
        self,
        period: AggregationPeriod,
        start_time: datetime,
        end_time: datetime,
        limit: int = 10,
    ) -> List[PerformanceMetrics]:
        """
        Get metrics for multiple agents.

        Args:
            period: Aggregation period
            start_time: Start of period
            end_time: End of period
            limit: Maximum number of agents to return

        Returns:
            List of PerformanceMetrics for different agents
        """
        pass

    @abstractmethod
    async def get_response_time_percentiles(
        self,
        agent_name: Optional[str],
        start_time: datetime,
        end_time: datetime,
    ) -> Dict[str, float]:
        """
        Get response time percentiles for a period.

        Args:
            agent_name: Agent name (None for global metrics)
            start_time: Start of period
            end_time: End of period

        Returns:
            Dictionary with p50, p95, p99 values in milliseconds
        """
        pass

    @abstractmethod
    async def get_error_counts_by_type(
        self,
        agent_name: Optional[str],
        start_time: datetime,
        end_time: datetime,
    ) -> Dict[ErrorType, int]:
        """
        Get error counts by type for a period.

        Args:
            agent_name: Agent name (None for global metrics)
            start_time: Start of period
            end_time: End of period

        Returns:
            Dictionary mapping error types to counts
        """
        pass

    @abstractmethod
    async def get_total_cost(
        self,
        agent_name: Optional[str],
        start_time: datetime,
        end_time: datetime,
    ) -> float:
        """
        Get total cost for a period.

        Args:
            agent_name: Agent name (None for global metrics)
            start_time: Start of period
            end_time: End of period

        Returns:
            Total cost in USD
        """
        pass

    @abstractmethod
    async def get_cache_hit_rate(
        self,
        agent_name: Optional[str],
        start_time: datetime,
        end_time: datetime,
    ) -> float:
        """
        Get cache hit rate for a period.

        Args:
            agent_name: Agent name (None for global metrics)
            start_time: Start of period
            end_time: End of period

        Returns:
            Cache hit rate (0.0 to 1.0)
        """
        pass

    @abstractmethod
    async def aggregate_hourly(
        self,
        start_time: datetime,
        end_time: datetime,
    ) -> int:
        """
        Aggregate minute-level data into hourly rollups.

        Args:
            start_time: Start of period to aggregate
            end_time: End of period to aggregate

        Returns:
            Number of hours aggregated
        """
        pass

    @abstractmethod
    async def aggregate_daily(
        self,
        start_time: datetime,
        end_time: datetime,
    ) -> int:
        """
        Aggregate hourly data into daily rollups.

        Args:
            start_time: Start of period to aggregate
            end_time: End of period to aggregate

        Returns:
            Number of days aggregated
        """
        pass

    @abstractmethod
    async def aggregate_weekly(
        self,
        start_time: datetime,
        end_time: datetime,
    ) -> int:
        """
        Aggregate daily data into weekly rollups.

        Args:
            start_time: Start of period to aggregate
            end_time: End of period to aggregate

        Returns:
            Number of weeks aggregated
        """
        pass

    @abstractmethod
    async def cleanup_old_metrics(
        self,
        retention_days: int,
    ) -> int:
        """
        Clean up metrics older than retention period.

        Args:
            retention_days: Number of days to retain

        Returns:
            Number of metric entries deleted
        """
        pass

    @abstractmethod
    async def get_top_agents_by_requests(
        self,
        start_time: datetime,
        end_time: datetime,
        limit: int = 10,
    ) -> List[tuple[str, int]]:
        """
        Get top agents by request count.

        Args:
            start_time: Start of period
            end_time: End of period
            limit: Maximum number of agents to return

        Returns:
            List of tuples (agent_name, request_count)
        """
        pass

    @abstractmethod
    async def get_top_agents_by_cost(
        self,
        start_time: datetime,
        end_time: datetime,
        limit: int = 10,
    ) -> List[tuple[str, float]]:
        """
        Get top agents by cost.

        Args:
            start_time: Start of period
            end_time: End of period
            limit: Maximum number of agents to return

        Returns:
            List of tuples (agent_name, total_cost_usd)
        """
        pass

    @abstractmethod
    async def get_top_agents_by_errors(
        self,
        start_time: datetime,
        end_time: datetime,
        limit: int = 10,
    ) -> List[tuple[str, int]]:
        """
        Get top agents by error count.

        Args:
            start_time: Start of period
            end_time: End of period
            limit: Maximum number of agents to return

        Returns:
            List of tuples (agent_name, error_count)
        """
        pass
