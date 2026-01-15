"""Agent Performance Monitoring.

Tracks and reports agent performance metrics.

Features:
    - Response time tracking
    - Success/failure rates
    - Tool usage statistics
    - Agent utilization
    - Real-time metrics
"""
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta, UTC
from collections import defaultdict
import logging
import time

from app.infrastructure.agno import AgentType


logger = logging.getLogger(__name__)


@dataclass
class AgentMetrics:
    """Metrics for a single agent execution."""
    
    agent_type: str
    query: str
    user_id: Optional[str]
    session_id: Optional[str]
    
    start_time: datetime = field(default_factory=lambda: datetime.now(UTC))
    end_time: Optional[datetime] = None
    duration_ms: float = 0.0
    
    success: bool = False
    error: Optional[str] = None
    
    tools_used: List[str] = field(default_factory=list)
    tool_call_count: int = 0
    tool_duration_ms: float = 0.0
    
    response_length: int = 0
    cached: bool = False
    
    def complete(self, success: bool = True, error: Optional[str] = None):
        """Mark execution as complete."""
        self.end_time = datetime.now(UTC)
        self.duration_ms = (self.end_time - self.start_time).total_seconds() * 1000
        self.success = success
        self.error = error


class AgentMonitor:
    """
    Monitors agent performance and tracks metrics.
    
    Usage:
        monitor = AgentMonitor()
        
        # Start tracking
        metrics = monitor.start_tracking(
            agent_type="trading",
            query="Swap ETH for USDC",
            user_id="user_123",
        )
        
        # Record tool calls
        metrics.tools_used.append("get_swap_quote")
        metrics.tool_call_count += 1
        
        # Complete tracking
        metrics.complete(success=True)
        monitor.record_metrics(metrics)
        
        # Get statistics
        stats = monitor.get_statistics()
    """
    
    def __init__(
        self,
        retention_hours: int = 24,
        max_metrics: int = 10000,
    ):
        """
        Initialize monitor.
        
        Args:
            retention_hours: How long to keep metrics
            max_metrics: Max metrics to store
        """
        self.retention_hours = retention_hours
        self.max_metrics = max_metrics
        
        # Store metrics
        self.metrics: List[AgentMetrics] = []
        
        # Aggregate stats
        self.stats = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "total_duration_ms": 0.0,
            "cache_hits": 0,
            "by_agent": defaultdict(lambda: {
                "requests": 0,
                "successful": 0,
                "failed": 0,
                "total_duration_ms": 0.0,
                "tools_used": defaultdict(int),
            }),
        }
    
    def start_tracking(
        self,
        agent_type: str,
        query: str,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
    ) -> AgentMetrics:
        """
        Start tracking a new agent execution.
        
        Args:
            agent_type: Agent type
            query: User query
            user_id: User ID
            session_id: Session ID
        
        Returns:
            AgentMetrics instance
        """
        return AgentMetrics(
            agent_type=agent_type,
            query=query,
            user_id=user_id,
            session_id=session_id,
        )
    
    def record_metrics(self, metrics: AgentMetrics):
        """
        Record completed metrics.
        
        Args:
            metrics: Completed metrics
        """
        # Add to storage
        self.metrics.append(metrics)
        
        # Update aggregate stats
        self.stats["total_requests"] += 1
        if metrics.success:
            self.stats["successful_requests"] += 1
        else:
            self.stats["failed_requests"] += 1
        
        self.stats["total_duration_ms"] += metrics.duration_ms
        
        if metrics.cached:
            self.stats["cache_hits"] += 1
        
        # Update agent-specific stats
        agent_stats = self.stats["by_agent"][metrics.agent_type]
        agent_stats["requests"] += 1
        if metrics.success:
            agent_stats["successful"] += 1
        else:
            agent_stats["failed"] += 1
        agent_stats["total_duration_ms"] += metrics.duration_ms
        
        for tool in metrics.tools_used:
            agent_stats["tools_used"][tool] += 1
        
        # Cleanup old metrics
        self._cleanup_old_metrics()
        
        logger.debug(
            f"Recorded metrics: {metrics.agent_type} "
            f"({metrics.duration_ms:.0f}ms, success={metrics.success})"
        )
    
    def _cleanup_old_metrics(self):
        """Remove old metrics beyond retention period."""
        if len(self.metrics) > self.max_metrics:
            # Keep only recent metrics
            self.metrics = self.metrics[-self.max_metrics:]
        
        # Remove metrics older than retention period
        cutoff = datetime.now(UTC) - timedelta(hours=self.retention_hours)
        self.metrics = [
            m for m in self.metrics
            if m.start_time > cutoff
        ]
    
    def get_statistics(
        self,
        agent_type: Optional[str] = None,
        time_window_minutes: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Get performance statistics.
        
        Args:
            agent_type: Filter by agent type (optional)
            time_window_minutes: Only include recent metrics (optional)
        
        Returns:
            Statistics dictionary
        """
        # Filter metrics
        metrics = self.metrics
        
        if time_window_minutes:
            cutoff = datetime.now(UTC) - timedelta(minutes=time_window_minutes)
            metrics = [m for m in metrics if m.start_time > cutoff]
        
        if agent_type:
            metrics = [m for m in metrics if m.agent_type == agent_type]
        
        if not metrics:
            return {
                "total_requests": 0,
                "message": "No metrics available for the specified filters",
            }
        
        # Calculate statistics
        total_requests = len(metrics)
        successful = sum(1 for m in metrics if m.success)
        failed = total_requests - successful
        
        durations = [m.duration_ms for m in metrics]
        avg_duration = sum(durations) / len(durations)
        min_duration = min(durations)
        max_duration = max(durations)
        
        # Calculate percentiles
        sorted_durations = sorted(durations)
        p50_idx = int(len(sorted_durations) * 0.5)
        p95_idx = int(len(sorted_durations) * 0.95)
        p99_idx = int(len(sorted_durations) * 0.99)
        
        cached = sum(1 for m in metrics if m.cached)
        
        # Tool usage
        tool_usage = defaultdict(int)
        for m in metrics:
            for tool in m.tools_used:
                tool_usage[tool] += 1
        
        return {
            "total_requests": total_requests,
            "successful_requests": successful,
            "failed_requests": failed,
            "success_rate": round(successful / total_requests * 100, 2),
            "cache_hit_rate": round(cached / total_requests * 100, 2),
            "duration_ms": {
                "avg": round(avg_duration, 2),
                "min": round(min_duration, 2),
                "max": round(max_duration, 2),
                "p50": round(sorted_durations[p50_idx], 2),
                "p95": round(sorted_durations[p95_idx], 2),
                "p99": round(sorted_durations[p99_idx], 2),
            },
            "tool_usage": dict(tool_usage),
            "time_window_minutes": time_window_minutes or "all",
            "agent_type": agent_type or "all",
        }
    
    def get_real_time_stats(self) -> Dict[str, Any]:
        """
        Get real-time statistics (last 5 minutes).
        
        Returns:
            Real-time statistics
        """
        return self.get_statistics(time_window_minutes=5)
    
    def get_agent_breakdown(self) -> Dict[str, Dict[str, Any]]:
        """
        Get statistics broken down by agent type.
        
        Returns:
            Statistics per agent type
        """
        return {
            agent_type: self.get_statistics(agent_type=agent_type)
            for agent_type in set(m.agent_type for m in self.metrics)
        }
    
    def get_slow_queries(
        self,
        threshold_ms: float = 5000,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """
        Get slowest queries.
        
        Args:
            threshold_ms: Minimum duration threshold
            limit: Max number of queries to return
        
        Returns:
            List of slow queries
        """
        slow_metrics = [
            m for m in self.metrics
            if m.duration_ms >= threshold_ms
        ]
        
        # Sort by duration
        slow_metrics.sort(key=lambda m: m.duration_ms, reverse=True)
        
        return [
            {
                "agent_type": m.agent_type,
                "query": m.query[:100] + "..." if len(m.query) > 100 else m.query,
                "duration_ms": round(m.duration_ms, 2),
                "tools_used": m.tools_used,
                "success": m.success,
                "timestamp": m.start_time.isoformat(),
            }
            for m in slow_metrics[:limit]
        ]
    
    def reset(self):
        """Reset all metrics and statistics."""
        self.metrics.clear()
        self.stats = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "total_duration_ms": 0.0,
            "cache_hits": 0,
            "by_agent": defaultdict(lambda: {
                "requests": 0,
                "successful": 0,
                "failed": 0,
                "total_duration_ms": 0.0,
                "tools_used": defaultdict(int),
            }),
        }
        logger.info("Metrics reset")


# Global monitor instance
_monitor: Optional[AgentMonitor] = None


def get_monitor() -> AgentMonitor:
    """
    Get global monitor instance.
    
    Returns:
        AgentMonitor instance
    """
    global _monitor
    if _monitor is None:
        _monitor = AgentMonitor()
    return _monitor
