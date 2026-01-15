"""
API Telemetry Service.

Enterprise-grade telemetry for all external API integrations.
Tracks metrics, errors, latency, costs, and provides alerting.

Features:
- Request/response tracking with timing
- Error categorization and rate tracking
- Rate limit detection and handling
- Cost estimation per API
- Percentile latency calculations (p50, p95, p99)
- Real-time alerting hooks
- Async recording for minimal overhead
"""

import asyncio
import logging
import time
import uuid
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta, UTC
from enum import Enum
from typing import Any, Callable, Optional

logger = logging.getLogger(__name__)


class APIStatus(Enum):
    """API call status."""
    SUCCESS = "success"
    ERROR = "error"
    TIMEOUT = "timeout"
    RATE_LIMITED = "rate_limited"
    AUTH_FAILURE = "auth_failure"
    VALIDATION_ERROR = "validation_error"


class AlertSeverity(Enum):
    """Alert severity levels."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class TelemetryConfig:
    """Configuration for API telemetry."""
    
    # General settings
    enabled: bool = True
    async_recording: bool = True
    retention_hours: int = 24
    max_records: int = 100000
    
    # Alerting thresholds
    error_rate_threshold: float = 0.05  # 5% error rate triggers alert
    latency_threshold_ms: float = 5000  # 5s latency triggers alert
    rate_limit_alert_count: int = 3  # N rate limits in window triggers alert
    
    # Cost tracking (estimated costs per 1000 requests)
    api_costs: dict = field(default_factory=lambda: {
        "coingecko": 0.0,  # Free tier
        "defillama": 0.0,  # Free
        "oneinch": 0.05,  # ~$49/mo for 10 req/sec
        "thegraph": 0.10,  # ~$99/mo
        "etherscan": 0.02,
        "hyperliquid": 0.0,
        "forta": 0.03,
        "chainalysis": 2.0,  # Enterprise pricing
        "trm_labs": 2.0,
        "opensea": 0.01,
        "snapshot": 0.0,
        "axelar": 0.0,
        "layerzero": 0.0,
        "twilio": 0.0075,  # Per SMS
        "privy": 0.01,
    })
    
    # Sampling
    sample_rate: float = 1.0  # 100% sampling by default


@dataclass
class APICallContext:
    """Context for a single API call."""
    
    call_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    api: str = ""
    operation: str = ""
    
    # Timing
    start_time: datetime = field(default_factory=lambda: datetime.now(UTC))
    end_time: Optional[datetime] = None
    duration_ms: float = 0.0
    
    # Request details
    request_params: dict = field(default_factory=dict)
    
    # Response details
    status: APIStatus = APIStatus.SUCCESS
    status_code: Optional[int] = None
    error_message: Optional[str] = None
    error_type: Optional[str] = None
    
    # Metadata
    cached: bool = False
    retry_count: int = 0
    
    def complete(
        self,
        status: APIStatus = APIStatus.SUCCESS,
        status_code: Optional[int] = None,
        error_message: Optional[str] = None,
        error_type: Optional[str] = None,
    ):
        """Complete the API call context."""
        self.end_time = datetime.now(UTC)
        self.duration_ms = (self.end_time - self.start_time).total_seconds() * 1000
        self.status = status
        self.status_code = status_code
        self.error_message = error_message
        self.error_type = error_type


@dataclass
class APIMetrics:
    """Aggregated metrics for an API."""
    
    api: str
    
    # Counts
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    cached_requests: int = 0
    rate_limited_requests: int = 0
    timeout_requests: int = 0
    
    # Latency (in ms)
    total_latency_ms: float = 0.0
    min_latency_ms: float = float('inf')
    max_latency_ms: float = 0.0
    latencies: list = field(default_factory=list)
    
    # Errors by type
    errors_by_type: dict = field(default_factory=lambda: defaultdict(int))
    errors_by_operation: dict = field(default_factory=lambda: defaultdict(int))
    
    # Rate limits
    rate_limit_events: list = field(default_factory=list)
    
    # Cost tracking
    estimated_cost_usd: float = 0.0
    
    # Time window
    window_start: datetime = field(default_factory=lambda: datetime.now(UTC))
    last_updated: datetime = field(default_factory=lambda: datetime.now(UTC))
    
    @property
    def avg_latency_ms(self) -> float:
        """Calculate average latency."""
        if self.total_requests == 0:
            return 0.0
        return self.total_latency_ms / self.total_requests
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate."""
        if self.total_requests == 0:
            return 1.0
        return self.successful_requests / self.total_requests
    
    @property
    def error_rate(self) -> float:
        """Calculate error rate."""
        return 1.0 - self.success_rate
    
    @property
    def cache_hit_rate(self) -> float:
        """Calculate cache hit rate."""
        if self.total_requests == 0:
            return 0.0
        return self.cached_requests / self.total_requests
    
    def get_percentile(self, percentile: float) -> float:
        """Get latency percentile."""
        if not self.latencies:
            return 0.0
        sorted_latencies = sorted(self.latencies)
        idx = int(len(sorted_latencies) * percentile)
        return sorted_latencies[min(idx, len(sorted_latencies) - 1)]
    
    @property
    def p50_latency_ms(self) -> float:
        return self.get_percentile(0.50)
    
    @property
    def p95_latency_ms(self) -> float:
        return self.get_percentile(0.95)
    
    @property
    def p99_latency_ms(self) -> float:
        return self.get_percentile(0.99)
    
    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            "api": self.api,
            "total_requests": self.total_requests,
            "successful_requests": self.successful_requests,
            "failed_requests": self.failed_requests,
            "cached_requests": self.cached_requests,
            "rate_limited_requests": self.rate_limited_requests,
            "timeout_requests": self.timeout_requests,
            "success_rate": round(self.success_rate * 100, 2),
            "error_rate": round(self.error_rate * 100, 2),
            "cache_hit_rate": round(self.cache_hit_rate * 100, 2),
            "latency_ms": {
                "avg": round(self.avg_latency_ms, 2),
                "min": round(self.min_latency_ms, 2) if self.min_latency_ms != float('inf') else 0,
                "max": round(self.max_latency_ms, 2),
                "p50": round(self.p50_latency_ms, 2),
                "p95": round(self.p95_latency_ms, 2),
                "p99": round(self.p99_latency_ms, 2),
            },
            "errors_by_type": dict(self.errors_by_type),
            "estimated_cost_usd": round(self.estimated_cost_usd, 4),
            "window_start": self.window_start.isoformat(),
            "last_updated": self.last_updated.isoformat(),
        }


class APITelemetry:
    """
    Enterprise-grade API telemetry service.
    
    Provides comprehensive observability for all external API integrations.
    
    Usage:
        telemetry = APITelemetry()
        
        # Start tracking
        ctx = telemetry.start_call("coingecko", "get_price", coin_id="ethereum")
        
        try:
            result = await coingecko.get_price("ethereum")
            ctx.complete(status=APIStatus.SUCCESS, status_code=200)
        except Exception as e:
            ctx.complete(status=APIStatus.ERROR, error_message=str(e))
        finally:
            await telemetry.record(ctx)
        
        # Get metrics
        metrics = telemetry.get_metrics("coingecko")
    """
    
    def __init__(
        self,
        config: Optional[TelemetryConfig] = None,
        alert_callback: Optional[Callable] = None,
    ):
        """
        Initialize API telemetry.
        
        Args:
            config: Telemetry configuration
            alert_callback: Async function to call when alert is triggered
        """
        self._config = config or TelemetryConfig()
        self._alert_callback = alert_callback
        
        # Metrics storage per API
        self._metrics: dict[str, APIMetrics] = {}
        
        # Recent call records for detailed analysis
        self._recent_calls: list[APICallContext] = []
        
        # Alert tracking
        self._alerts_sent: dict[str, datetime] = {}
        self._alert_cooldown = timedelta(minutes=5)
        
        # Background task queue
        self._record_queue: asyncio.Queue = asyncio.Queue()
        self._background_task: Optional[asyncio.Task] = None
    
    def start_call(
        self,
        api: str,
        operation: str,
        **params,
    ) -> APICallContext:
        """
        Start tracking an API call.
        
        Args:
            api: API name (e.g., "coingecko")
            operation: Operation name (e.g., "get_price")
            **params: Request parameters for logging
            
        Returns:
            APICallContext to track the call
        """
        return APICallContext(
            api=api,
            operation=operation,
            request_params=params,
        )
    
    async def record(self, ctx: APICallContext):
        """
        Record a completed API call.
        
        Args:
            ctx: Completed API call context
        """
        if not self._config.enabled:
            return
        
        if self._config.async_recording:
            await self._record_queue.put(ctx)
            self._ensure_background_task()
        else:
            await self._process_record(ctx)
    
    def _ensure_background_task(self):
        """Ensure background processing task is running."""
        if self._background_task is None or self._background_task.done():
            self._background_task = asyncio.create_task(self._process_queue())
    
    async def _process_queue(self):
        """Process records from the queue."""
        while True:
            try:
                ctx = await asyncio.wait_for(
                    self._record_queue.get(),
                    timeout=1.0,
                )
                await self._process_record(ctx)
            except asyncio.TimeoutError:
                # Check if queue is empty and no more work
                if self._record_queue.empty():
                    break
            except Exception as e:
                logger.error(f"Error processing telemetry record: {e}")
    
    async def _process_record(self, ctx: APICallContext):
        """Process a single telemetry record."""
        # Get or create metrics for this API
        if ctx.api not in self._metrics:
            self._metrics[ctx.api] = APIMetrics(api=ctx.api)
        
        metrics = self._metrics[ctx.api]
        
        # Update counts
        metrics.total_requests += 1
        
        if ctx.status == APIStatus.SUCCESS:
            metrics.successful_requests += 1
        elif ctx.status == APIStatus.ERROR:
            metrics.failed_requests += 1
            if ctx.error_type:
                metrics.errors_by_type[ctx.error_type] += 1
            metrics.errors_by_operation[ctx.operation] += 1
        elif ctx.status == APIStatus.RATE_LIMITED:
            metrics.rate_limited_requests += 1
            metrics.rate_limit_events.append(ctx.start_time)
        elif ctx.status == APIStatus.TIMEOUT:
            metrics.timeout_requests += 1
        
        if ctx.cached:
            metrics.cached_requests += 1
        
        # Update latency
        metrics.total_latency_ms += ctx.duration_ms
        metrics.min_latency_ms = min(metrics.min_latency_ms, ctx.duration_ms)
        metrics.max_latency_ms = max(metrics.max_latency_ms, ctx.duration_ms)
        metrics.latencies.append(ctx.duration_ms)
        
        # Trim latencies to last 1000 for memory efficiency
        if len(metrics.latencies) > 1000:
            metrics.latencies = metrics.latencies[-1000:]
        
        # Update cost estimate
        cost_per_1k = self._config.api_costs.get(ctx.api, 0.0)
        metrics.estimated_cost_usd += cost_per_1k / 1000
        
        # Update timestamp
        metrics.last_updated = datetime.now(UTC)
        
        # Store recent call
        self._recent_calls.append(ctx)
        self._cleanup_old_records()
        
        # Check for alerts
        await self._check_alerts(ctx, metrics)
        
        # Log
        logger.debug(
            f"API Call: {ctx.api}/{ctx.operation} "
            f"status={ctx.status.value} "
            f"duration={ctx.duration_ms:.0f}ms"
        )
    
    def _cleanup_old_records(self):
        """Remove old records beyond retention period."""
        if len(self._recent_calls) > self._config.max_records:
            self._recent_calls = self._recent_calls[-self._config.max_records:]
        
        cutoff = datetime.now(UTC) - timedelta(hours=self._config.retention_hours)
        self._recent_calls = [
            c for c in self._recent_calls
            if c.start_time > cutoff
        ]
    
    async def _check_alerts(self, ctx: APICallContext, metrics: APIMetrics):
        """Check if any alert thresholds are exceeded."""
        alerts = []
        
        # Check error rate (need minimum requests for statistical significance)
        if metrics.total_requests >= 100 and metrics.error_rate > self._config.error_rate_threshold:
            alerts.append({
                "type": "high_error_rate",
                "severity": AlertSeverity.ERROR,
                "api": ctx.api,
                "message": f"Error rate {metrics.error_rate*100:.1f}% exceeds threshold {self._config.error_rate_threshold*100:.1f}%",
                "value": metrics.error_rate,
            })
        
        # Check latency
        if ctx.duration_ms > self._config.latency_threshold_ms:
            alerts.append({
                "type": "high_latency",
                "severity": AlertSeverity.WARNING,
                "api": ctx.api,
                "operation": ctx.operation,
                "message": f"Latency {ctx.duration_ms:.0f}ms exceeds threshold {self._config.latency_threshold_ms:.0f}ms",
                "value": ctx.duration_ms,
            })
        
        # Check rate limiting
        recent_rate_limits = [
            t for t in metrics.rate_limit_events
            if t > datetime.now(UTC) - timedelta(minutes=5)
        ]
        if len(recent_rate_limits) >= self._config.rate_limit_alert_count:
            alerts.append({
                "type": "rate_limit_exceeded",
                "severity": AlertSeverity.CRITICAL,
                "api": ctx.api,
                "message": f"Rate limited {len(recent_rate_limits)} times in last 5 minutes",
                "value": len(recent_rate_limits),
            })
        
        # Send alerts (with cooldown)
        for alert in alerts:
            alert_key = f"{alert['type']}:{alert['api']}"
            last_sent = self._alerts_sent.get(alert_key)
            
            if last_sent is None or datetime.now(UTC) - last_sent > self._alert_cooldown:
                self._alerts_sent[alert_key] = datetime.now(UTC)
                
                if self._alert_callback:
                    try:
                        await self._alert_callback(alert)
                    except Exception as e:
                        logger.error(f"Alert callback error: {e}")
                
                logger.warning(f"ALERT: {alert['message']}")
    
    def get_metrics(self, api: Optional[str] = None) -> dict:
        """
        Get metrics for an API or all APIs.
        
        Args:
            api: API name (None for all APIs)
            
        Returns:
            Metrics dictionary
        """
        if api:
            metrics = self._metrics.get(api)
            return metrics.to_dict() if metrics else {}
        
        return {
            name: m.to_dict()
            for name, m in self._metrics.items()
        }
    
    def get_all_metrics(self) -> dict:
        """Get comprehensive metrics summary."""
        total_requests = sum(m.total_requests for m in self._metrics.values())
        total_errors = sum(m.failed_requests for m in self._metrics.values())
        total_cost = sum(m.estimated_cost_usd for m in self._metrics.values())
        
        return {
            "summary": {
                "total_requests": total_requests,
                "total_errors": total_errors,
                "overall_error_rate": round(total_errors / total_requests * 100, 2) if total_requests else 0,
                "total_estimated_cost_usd": round(total_cost, 4),
                "apis_tracked": len(self._metrics),
            },
            "by_api": {
                name: m.to_dict()
                for name, m in self._metrics.items()
            },
        }
    
    def get_slow_calls(
        self,
        threshold_ms: float = 1000,
        limit: int = 10,
    ) -> list[dict]:
        """Get slowest API calls."""
        slow_calls = [
            c for c in self._recent_calls
            if c.duration_ms >= threshold_ms
        ]
        slow_calls.sort(key=lambda c: c.duration_ms, reverse=True)
        
        return [
            {
                "api": c.api,
                "operation": c.operation,
                "duration_ms": round(c.duration_ms, 2),
                "status": c.status.value,
                "timestamp": c.start_time.isoformat(),
                "params": {k: str(v)[:50] for k, v in c.request_params.items()},
            }
            for c in slow_calls[:limit]
        ]
    
    def get_errors(
        self,
        api: Optional[str] = None,
        limit: int = 20,
    ) -> list[dict]:
        """Get recent errors."""
        error_calls = [
            c for c in self._recent_calls
            if c.status in (APIStatus.ERROR, APIStatus.TIMEOUT, APIStatus.RATE_LIMITED)
            and (api is None or c.api == api)
        ]
        error_calls.sort(key=lambda c: c.start_time, reverse=True)
        
        return [
            {
                "api": c.api,
                "operation": c.operation,
                "status": c.status.value,
                "error_type": c.error_type,
                "error_message": c.error_message,
                "timestamp": c.start_time.isoformat(),
            }
            for c in error_calls[:limit]
        ]
    
    def reset(self, api: Optional[str] = None):
        """Reset metrics for an API or all APIs."""
        if api:
            if api in self._metrics:
                self._metrics[api] = APIMetrics(api=api)
        else:
            self._metrics.clear()
            self._recent_calls.clear()
        
        logger.info(f"Reset telemetry for {api or 'all APIs'}")


# Global telemetry instance
_telemetry: Optional[APITelemetry] = None


def get_api_telemetry() -> APITelemetry:
    """Get global API telemetry instance."""
    global _telemetry
    if _telemetry is None:
        _telemetry = APITelemetry()
    return _telemetry
