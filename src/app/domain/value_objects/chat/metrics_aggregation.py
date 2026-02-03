"""
Metrics aggregation value objects.

Value objects for metrics aggregation, rollups, and time-series analysis.
"""

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import List, Optional
from enum import Enum


class TimeGranularity(Enum):
    """Time granularity for metrics aggregation."""

    SECOND = "second"
    MINUTE = "minute"
    HOUR = "hour"
    DAY = "day"
    WEEK = "week"
    MONTH = "month"


class MetricAggregationType(Enum):
    """Types of metric aggregations."""

    SUM = "sum"
    AVG = "avg"
    MIN = "min"
    MAX = "max"
    COUNT = "count"
    PERCENTILE = "percentile"


@dataclass(frozen=True)
class TimeRange:
    """Time range for metrics queries."""

    start: datetime
    end: datetime

    def __post_init__(self) -> None:
        """Validate time range."""
        if self.end <= self.start:
            raise ValueError("End time must be after start time")

    def duration(self) -> timedelta:
        """Get duration of time range."""
        return self.end - self.start

    def duration_seconds(self) -> float:
        """Get duration in seconds."""
        return self.duration().total_seconds()

    def contains(self, timestamp: datetime) -> bool:
        """Check if timestamp is within range."""
        return self.start <= timestamp <= self.end

    def split_by_granularity(self, granularity: TimeGranularity) -> List["TimeRange"]:
        """
        Split time range into smaller ranges by granularity.

        Args:
            granularity: Time granularity for splitting

        Returns:
            List of TimeRange objects
        """
        ranges: List[TimeRange] = []
        current = self.start

        # Determine delta based on granularity
        if granularity == TimeGranularity.SECOND:
            delta = timedelta(seconds=1)
        elif granularity == TimeGranularity.MINUTE:
            delta = timedelta(minutes=1)
        elif granularity == TimeGranularity.HOUR:
            delta = timedelta(hours=1)
        elif granularity == TimeGranularity.DAY:
            delta = timedelta(days=1)
        elif granularity == TimeGranularity.WEEK:
            delta = timedelta(weeks=1)
        elif granularity == TimeGranularity.MONTH:
            delta = timedelta(days=30)  # Approximate
        else:
            delta = timedelta(hours=1)

        while current < self.end:
            next_time = min(current + delta, self.end)
            ranges.append(TimeRange(start=current, end=next_time))
            current = next_time

        return ranges

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "start": self.start.isoformat(),
            "end": self.end.isoformat(),
            "duration_seconds": self.duration_seconds(),
        }


@dataclass(frozen=True)
class MetricDataPoint:
    """Single data point in a time series."""

    timestamp: datetime
    value: float
    metadata: Optional[dict] = None

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "timestamp": self.timestamp.isoformat(),
            "value": self.value,
            "metadata": self.metadata,
        }


@dataclass(frozen=True)
class TimeSeries:
    """Time series of metric data points."""

    metric_name: str
    data_points: List[MetricDataPoint]
    unit: str  # "ms", "usd", "count", etc.
    aggregation_type: MetricAggregationType

    def get_values(self) -> List[float]:
        """Get all values from data points."""
        return [dp.value for dp in self.data_points]

    def get_timestamps(self) -> List[datetime]:
        """Get all timestamps from data points."""
        return [dp.timestamp for dp in self.data_points]

    def get_avg(self) -> float:
        """Calculate average value."""
        values = self.get_values()
        return sum(values) / len(values) if values else 0.0

    def get_sum(self) -> float:
        """Calculate sum of values."""
        return sum(self.get_values())

    def get_min(self) -> float:
        """Get minimum value."""
        values = self.get_values()
        return min(values) if values else 0.0

    def get_max(self) -> float:
        """Get maximum value."""
        values = self.get_values()
        return max(values) if values else 0.0

    def filter_by_time_range(self, time_range: TimeRange) -> "TimeSeries":
        """Filter data points by time range."""
        filtered_points = [
            dp for dp in self.data_points if time_range.contains(dp.timestamp)
        ]
        return TimeSeries(
            metric_name=self.metric_name,
            data_points=filtered_points,
            unit=self.unit,
            aggregation_type=self.aggregation_type,
        )

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "metric_name": self.metric_name,
            "unit": self.unit,
            "aggregation_type": self.aggregation_type.value,
            "data_points": [dp.to_dict() for dp in self.data_points],
            "summary": {
                "count": len(self.data_points),
                "avg": self.get_avg(),
                "sum": self.get_sum(),
                "min": self.get_min(),
                "max": self.get_max(),
            },
        }


@dataclass(frozen=True)
class MetricsRollup:
    """Aggregated metrics rollup for a time period."""

    time_range: TimeRange
    granularity: TimeGranularity
    agent_name: Optional[str]
    total_requests: int
    total_errors: int
    total_cost_usd: float
    avg_response_time_ms: float
    cache_hit_rate: float

    def get_error_rate(self) -> float:
        """Calculate error rate."""
        return (
            self.total_errors / self.total_requests if self.total_requests > 0 else 0.0
        )

    def get_requests_per_second(self) -> float:
        """Calculate requests per second."""
        duration = self.time_range.duration_seconds()
        return self.total_requests / duration if duration > 0 else 0.0

    def get_cost_per_request(self) -> float:
        """Calculate average cost per request."""
        return (
            self.total_cost_usd / self.total_requests
            if self.total_requests > 0
            else 0.0
        )

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "time_range": self.time_range.to_dict(),
            "granularity": self.granularity.value,
            "agent_name": self.agent_name,
            "total_requests": self.total_requests,
            "total_errors": self.total_errors,
            "total_cost_usd": self.total_cost_usd,
            "avg_response_time_ms": self.avg_response_time_ms,
            "cache_hit_rate": self.cache_hit_rate,
            "error_rate": self.get_error_rate(),
            "requests_per_second": self.get_requests_per_second(),
            "cost_per_request": self.get_cost_per_request(),
        }


@dataclass(frozen=True)
class MetricsTrend:
    """Trend analysis for metrics over time."""

    metric_name: str
    time_series: TimeSeries
    trend_direction: str  # "increasing", "decreasing", "stable"
    trend_percentage: float  # Percentage change
    is_anomaly: bool  # Whether trend represents an anomaly

    @classmethod
    def analyze(
        cls,
        metric_name: str,
        time_series: TimeSeries,
        baseline_avg: float,
        threshold_percentage: float = 20.0,
    ) -> "MetricsTrend":
        """
        Analyze trend from time series.

        Args:
            metric_name: Name of metric
            time_series: Time series data
            baseline_avg: Baseline average for comparison
            threshold_percentage: Threshold for anomaly detection

        Returns:
            MetricsTrend instance
        """
        current_avg = time_series.get_avg()

        if baseline_avg == 0:
            trend_percentage = 0.0
            trend_direction = "stable"
        else:
            trend_percentage = ((current_avg - baseline_avg) / baseline_avg) * 100

            if trend_percentage > 5:
                trend_direction = "increasing"
            elif trend_percentage < -5:
                trend_direction = "decreasing"
            else:
                trend_direction = "stable"

        is_anomaly = abs(trend_percentage) > threshold_percentage

        return cls(
            metric_name=metric_name,
            time_series=time_series,
            trend_direction=trend_direction,
            trend_percentage=trend_percentage,
            is_anomaly=is_anomaly,
        )

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "metric_name": self.metric_name,
            "trend_direction": self.trend_direction,
            "trend_percentage": self.trend_percentage,
            "is_anomaly": self.is_anomaly,
            "time_series": self.time_series.to_dict(),
        }


@dataclass(frozen=True)
class PercentileBreakdown:
    """Percentile breakdown for a metric."""

    metric_name: str
    p25: float
    p50: float
    p75: float
    p90: float
    p95: float
    p99: float
    min_value: float
    max_value: float
    sample_count: int

    def is_within_sla(self, sla_percentile: str, sla_value: float) -> bool:
        """
        Check if percentile is within SLA.

        Args:
            sla_percentile: Percentile to check (e.g., "p95")
            sla_value: SLA value

        Returns:
            True if within SLA
        """
        percentile_map = {
            "p25": self.p25,
            "p50": self.p50,
            "p75": self.p75,
            "p90": self.p90,
            "p95": self.p95,
            "p99": self.p99,
        }

        actual_value = percentile_map.get(sla_percentile)
        if actual_value is None:
            return False

        return actual_value <= sla_value

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "metric_name": self.metric_name,
            "percentiles": {
                "p25": self.p25,
                "p50": self.p50,
                "p75": self.p75,
                "p90": self.p90,
                "p95": self.p95,
                "p99": self.p99,
            },
            "min": self.min_value,
            "max": self.max_value,
            "sample_count": self.sample_count,
        }


@dataclass(frozen=True)
class AgentComparison:
    """Comparison of metrics across multiple agents."""

    metric_name: str
    agent_metrics: dict[str, float]  # agent_name -> metric_value
    best_agent: str
    worst_agent: str
    average_value: float
    variance: float

    @classmethod
    def create(
        cls,
        metric_name: str,
        agent_metrics: dict[str, float],
        higher_is_better: bool = True,
    ) -> "AgentComparison":
        """
        Create agent comparison.

        Args:
            metric_name: Name of metric
            agent_metrics: Dictionary mapping agent names to values
            higher_is_better: Whether higher values are better

        Returns:
            AgentComparison instance
        """
        if not agent_metrics:
            raise ValueError("Agent metrics cannot be empty")

        values = list(agent_metrics.values())
        avg_value = sum(values) / len(values)

        # Calculate variance
        variance = sum((v - avg_value) ** 2 for v in values) / len(values)

        # Find best and worst
        if higher_is_better:
            best_agent = max(agent_metrics, key=agent_metrics.get)  # type: ignore
            worst_agent = min(agent_metrics, key=agent_metrics.get)  # type: ignore
        else:
            best_agent = min(agent_metrics, key=agent_metrics.get)  # type: ignore
            worst_agent = max(agent_metrics, key=agent_metrics.get)  # type: ignore

        return cls(
            metric_name=metric_name,
            agent_metrics=agent_metrics,
            best_agent=best_agent,
            worst_agent=worst_agent,
            average_value=avg_value,
            variance=variance,
        )

    def get_agent_rank(self, agent_name: str) -> Optional[int]:
        """Get rank of agent (1-indexed, 1 is best)."""
        if agent_name not in self.agent_metrics:
            return None

        sorted_agents = sorted(
            self.agent_metrics.items(), key=lambda x: x[1], reverse=True
        )

        for rank, (name, _) in enumerate(sorted_agents, start=1):
            if name == agent_name:
                return rank

        return None

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "metric_name": self.metric_name,
            "agent_metrics": self.agent_metrics,
            "best_agent": self.best_agent,
            "worst_agent": self.worst_agent,
            "average_value": self.average_value,
            "variance": self.variance,
        }
