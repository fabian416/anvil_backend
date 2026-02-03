"""
LLM Provider Telemetry & Analytics.

Enterprise-grade telemetry for LLM provider monitoring:
- Token usage tracking per provider and model
- Cost estimation and tracking
- Latency metrics and P50/P90/P99
- Request success/failure rates
- Rate limit detection
- Provider health monitoring
- Budget alerting

Usage:
    from app.infrastructure.telemetry.llm_telemetry import (
        LLMTelemetry,
        LLMCallContext,
        get_llm_telemetry,
    )

    telemetry = get_llm_telemetry()

    # Start tracking a call
    ctx = telemetry.start_call(
        provider="vertex_ai",
        model="gemini-1.5-pro",
        operation="chat",
    )

    # After completion
    ctx.complete(
        input_tokens=500,
        output_tokens=200,
        cost_usd=0.003,
    )

    await telemetry.record(ctx)

    # Get metrics
    metrics = telemetry.get_provider_metrics("vertex_ai")
"""

import asyncio
import logging
import time
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta, UTC
from enum import Enum
from typing import Any, Optional
from uuid import uuid4

logger = logging.getLogger(__name__)


# ============================================================================
# ENUMS
# ============================================================================


class LLMCallStatus(str, Enum):
    """Status of an LLM call."""

    SUCCESS = "success"
    ERROR = "error"
    TIMEOUT = "timeout"
    RATE_LIMITED = "rate_limited"
    AUTH_FAILURE = "auth_failure"
    VALIDATION_ERROR = "validation_error"
    CIRCUIT_BREAKER = "circuit_breaker"


class AlertSeverity(str, Enum):
    """Severity levels for alerts."""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


# ============================================================================
# DATA CLASSES
# ============================================================================


@dataclass
class LLMTelemetryConfig:
    """Configuration for LLM telemetry."""

    enabled: bool = True
    async_recording: bool = True
    retention_hours: int = 24
    max_records: int = 100000

    # Cost tracking
    enable_cost_tracking: bool = True
    monthly_budget_usd: float = 1000.0
    budget_alert_threshold: float = 0.8  # 80%

    # Error thresholds
    error_rate_threshold: float = 0.05  # 5%
    latency_threshold_ms: int = 30000  # 30s
    rate_limit_alert_count: int = 3

    # Model costs (per 1M tokens)
    model_costs: dict[str, dict[str, float]] = field(
        default_factory=lambda: {
            # Vertex AI / Google
            "gemini-1.5-pro": {"input": 1.25, "output": 5.00},
            "gemini-1.5-flash": {"input": 0.075, "output": 0.30},
            "gemini-1.0-pro": {"input": 0.50, "output": 1.50},
            # OpenAI
            "gpt-4o": {"input": 2.50, "output": 10.00},
            "gpt-4o-mini": {"input": 0.15, "output": 0.60},
            "gpt-4-turbo": {"input": 10.00, "output": 30.00},
            "gpt-3.5-turbo": {"input": 0.50, "output": 1.50},
            # Anthropic
            "claude-3-5-sonnet-latest": {"input": 3.00, "output": 15.00},
            "claude-3-opus-latest": {"input": 15.00, "output": 75.00},
            "claude-3-haiku-latest": {"input": 0.25, "output": 1.25},
            # DeepInfra (various models)
            "meta-llama/Llama-3.2-70B-Instruct": {"input": 0.52, "output": 0.75},
            "meta-llama/Llama-3.2-8B-Instruct": {"input": 0.06, "output": 0.06},
            "mistralai/Mixtral-8x7B-Instruct-v0.1": {"input": 0.27, "output": 0.27},
            # AWS Bedrock
            "anthropic.claude-3-5-sonnet-v2": {"input": 3.00, "output": 15.00},
            "anthropic.claude-3-haiku": {"input": 0.25, "output": 1.25},
        }
    )


@dataclass
class LLMCallContext:
    """Context for tracking an LLM call."""

    call_id: str
    provider: str
    model: str
    operation: str
    start_time: float

    # Completed fields
    end_time: Optional[float] = None
    status: Optional[LLMCallStatus] = None
    input_tokens: int = 0
    output_tokens: int = 0
    cost_usd: float = 0.0
    error_message: Optional[str] = None
    error_type: Optional[str] = None

    # Metadata
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def duration_ms(self) -> int:
        """Calculate call duration in milliseconds."""
        if self.end_time is None:
            return int((time.time() - self.start_time) * 1000)
        return int((self.end_time - self.start_time) * 1000)

    @property
    def total_tokens(self) -> int:
        """Total tokens used."""
        return self.input_tokens + self.output_tokens

    def complete(
        self,
        status: LLMCallStatus = LLMCallStatus.SUCCESS,
        input_tokens: int = 0,
        output_tokens: int = 0,
        cost_usd: float = 0.0,
        error_message: Optional[str] = None,
        error_type: Optional[str] = None,
    ) -> None:
        """Mark the call as complete."""
        self.end_time = time.time()
        self.status = status
        self.input_tokens = input_tokens
        self.output_tokens = output_tokens
        self.cost_usd = cost_usd
        self.error_message = error_message
        self.error_type = error_type


@dataclass
class LLMProviderMetrics:
    """Aggregated metrics for an LLM provider."""

    provider: str
    total_calls: int = 0
    successful_calls: int = 0
    failed_calls: int = 0
    rate_limited_calls: int = 0
    timeout_calls: int = 0

    # Token metrics
    total_input_tokens: int = 0
    total_output_tokens: int = 0

    # Cost metrics
    total_cost_usd: float = 0.0

    # Latency metrics (in ms)
    latencies: list[int] = field(default_factory=list)

    # Per-model breakdown
    model_usage: dict[str, dict[str, Any]] = field(default_factory=dict)

    # Timestamps
    first_call_at: Optional[datetime] = None
    last_call_at: Optional[datetime] = None

    @property
    def total_tokens(self) -> int:
        return self.total_input_tokens + self.total_output_tokens

    @property
    def success_rate(self) -> float:
        if self.total_calls == 0:
            return 1.0
        return self.successful_calls / self.total_calls

    @property
    def error_rate(self) -> float:
        return 1.0 - self.success_rate

    @property
    def avg_latency_ms(self) -> float:
        if not self.latencies:
            return 0.0
        return sum(self.latencies) / len(self.latencies)

    @property
    def p50_latency_ms(self) -> float:
        return self._percentile(50)

    @property
    def p90_latency_ms(self) -> float:
        return self._percentile(90)

    @property
    def p99_latency_ms(self) -> float:
        return self._percentile(99)

    def _percentile(self, p: int) -> float:
        if not self.latencies:
            return 0.0
        sorted_lat = sorted(self.latencies)
        idx = int(len(sorted_lat) * p / 100)
        return sorted_lat[min(idx, len(sorted_lat) - 1)]

    def to_dict(self) -> dict[str, Any]:
        return {
            "provider": self.provider,
            "total_calls": self.total_calls,
            "successful_calls": self.successful_calls,
            "failed_calls": self.failed_calls,
            "rate_limited_calls": self.rate_limited_calls,
            "timeout_calls": self.timeout_calls,
            "total_input_tokens": self.total_input_tokens,
            "total_output_tokens": self.total_output_tokens,
            "total_tokens": self.total_tokens,
            "total_cost_usd": round(self.total_cost_usd, 4),
            "success_rate": round(self.success_rate, 4),
            "error_rate": round(self.error_rate, 4),
            "avg_latency_ms": round(self.avg_latency_ms, 2),
            "p50_latency_ms": round(self.p50_latency_ms, 2),
            "p90_latency_ms": round(self.p90_latency_ms, 2),
            "p99_latency_ms": round(self.p99_latency_ms, 2),
            "model_usage": self.model_usage,
            "first_call_at": self.first_call_at.isoformat()
            if self.first_call_at
            else None,
            "last_call_at": self.last_call_at.isoformat()
            if self.last_call_at
            else None,
        }


@dataclass
class LLMAlert:
    """Alert generated by LLM telemetry."""

    alert_id: str
    severity: AlertSeverity
    provider: str
    message: str
    details: dict[str, Any]
    timestamp: datetime

    def to_dict(self) -> dict[str, Any]:
        return {
            "alert_id": self.alert_id,
            "severity": self.severity.value,
            "provider": self.provider,
            "message": self.message,
            "details": self.details,
            "timestamp": self.timestamp.isoformat(),
        }


# ============================================================================
# LLM TELEMETRY SERVICE
# ============================================================================


class LLMTelemetry:
    """
    Enterprise telemetry service for LLM providers.

    Features:
    - Token usage and cost tracking
    - Latency metrics with percentiles
    - Provider health monitoring
    - Budget alerting
    - Rate limit detection
    """

    def __init__(self, config: Optional[LLMTelemetryConfig] = None):
        self.config = config or LLMTelemetryConfig()

        # In-memory storage
        self._calls: list[LLMCallContext] = []
        self._provider_metrics: dict[str, LLMProviderMetrics] = defaultdict(
            lambda: LLMProviderMetrics(provider="unknown")
        )
        self._alerts: list[LLMAlert] = []

        # Budget tracking
        self._monthly_cost: float = 0.0
        self._month_start: datetime = datetime.now(UTC).replace(
            day=1, hour=0, minute=0, second=0, microsecond=0
        )

        # Async recording
        self._record_queue: asyncio.Queue[LLMCallContext] = asyncio.Queue()
        self._recording_task: Optional[asyncio.Task[None]] = None

    def start_call(
        self,
        provider: str,
        model: str,
        operation: str = "generate",
        **metadata: Any,
    ) -> LLMCallContext:
        """
        Start tracking an LLM call.

        Args:
            provider: LLM provider name (e.g., "vertex_ai", "openai")
            model: Model name (e.g., "gemini-1.5-pro")
            operation: Operation type (e.g., "generate", "embed")
            **metadata: Additional metadata to track

        Returns:
            Call context for tracking
        """
        return LLMCallContext(
            call_id=str(uuid4()),
            provider=provider,
            model=model,
            operation=operation,
            start_time=time.time(),
            metadata=metadata,
        )

    async def record(self, ctx: LLMCallContext) -> None:
        """
        Record a completed LLM call.

        Args:
            ctx: Call context to record
        """
        if not self.config.enabled:
            return

        if self.config.async_recording:
            await self._record_queue.put(ctx)
            if self._recording_task is None or self._recording_task.done():
                self._recording_task = asyncio.create_task(self._process_queue())
        else:
            self._record_sync(ctx)

    def _record_sync(self, ctx: LLMCallContext) -> None:
        """Synchronous recording of a call."""
        # Store call
        self._calls.append(ctx)

        # Cleanup old calls
        self._cleanup_old_calls()

        # Update provider metrics
        self._update_provider_metrics(ctx)

        # Update budget
        self._update_budget(ctx)

        # Check for alerts
        self._check_alerts(ctx)

    async def _process_queue(self) -> None:
        """Process the recording queue."""
        while not self._record_queue.empty():
            try:
                ctx = await asyncio.wait_for(self._record_queue.get(), timeout=0.1)
                self._record_sync(ctx)
            except asyncio.TimeoutError:
                break
            except Exception as e:
                logger.error(f"Error processing LLM telemetry: {e}")

    def _update_provider_metrics(self, ctx: LLMCallContext) -> None:
        """Update aggregated metrics for a provider."""
        metrics = self._provider_metrics.get(ctx.provider)
        if metrics is None:
            metrics = LLMProviderMetrics(provider=ctx.provider)
            self._provider_metrics[ctx.provider] = metrics

        now = datetime.now(UTC)
        metrics.total_calls += 1

        if metrics.first_call_at is None:
            metrics.first_call_at = now
        metrics.last_call_at = now

        if ctx.status == LLMCallStatus.SUCCESS:
            metrics.successful_calls += 1
        elif ctx.status == LLMCallStatus.RATE_LIMITED:
            metrics.rate_limited_calls += 1
            metrics.failed_calls += 1
        elif ctx.status == LLMCallStatus.TIMEOUT:
            metrics.timeout_calls += 1
            metrics.failed_calls += 1
        else:
            metrics.failed_calls += 1

        # Token metrics
        metrics.total_input_tokens += ctx.input_tokens
        metrics.total_output_tokens += ctx.output_tokens

        # Cost
        cost = ctx.cost_usd or self._estimate_cost(ctx)
        metrics.total_cost_usd += cost

        # Latency
        if len(metrics.latencies) >= 10000:
            metrics.latencies = metrics.latencies[-5000:]
        metrics.latencies.append(ctx.duration_ms)

        # Model breakdown
        if ctx.model not in metrics.model_usage:
            metrics.model_usage[ctx.model] = {
                "calls": 0,
                "input_tokens": 0,
                "output_tokens": 0,
                "cost_usd": 0.0,
                "avg_latency_ms": 0.0,
            }

        model_stats = metrics.model_usage[ctx.model]
        model_stats["calls"] += 1
        model_stats["input_tokens"] += ctx.input_tokens
        model_stats["output_tokens"] += ctx.output_tokens
        model_stats["cost_usd"] += cost

        # Rolling average latency
        n = model_stats["calls"]
        old_avg = model_stats["avg_latency_ms"]
        model_stats["avg_latency_ms"] = old_avg + (ctx.duration_ms - old_avg) / n

    def _estimate_cost(self, ctx: LLMCallContext) -> float:
        """Estimate cost based on model costs config."""
        costs = self.config.model_costs.get(ctx.model)
        if not costs:
            # Try to find a partial match
            for model_pattern, cost_info in self.config.model_costs.items():
                if model_pattern in ctx.model or ctx.model in model_pattern:
                    costs = cost_info
                    break

        if not costs:
            # Default estimate
            costs = {"input": 1.0, "output": 2.0}

        input_cost = (ctx.input_tokens / 1_000_000) * costs["input"]
        output_cost = (ctx.output_tokens / 1_000_000) * costs["output"]

        return input_cost + output_cost

    def _update_budget(self, ctx: LLMCallContext) -> None:
        """Update monthly budget tracking."""
        # Reset budget on new month
        now = datetime.now(UTC)
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

        if month_start > self._month_start:
            self._month_start = month_start
            self._monthly_cost = 0.0

        cost = ctx.cost_usd or self._estimate_cost(ctx)
        self._monthly_cost += cost

    def _check_alerts(self, ctx: LLMCallContext) -> None:
        """Check for alert conditions."""
        metrics = self._provider_metrics.get(ctx.provider)
        if not metrics:
            return

        # Check error rate
        if (
            metrics.total_calls >= 10
            and metrics.error_rate > self.config.error_rate_threshold
        ):
            self._create_alert(
                severity=AlertSeverity.WARNING,
                provider=ctx.provider,
                message=f"High error rate for {ctx.provider}: {metrics.error_rate:.1%}",
                details={
                    "error_rate": metrics.error_rate,
                    "threshold": self.config.error_rate_threshold,
                    "total_calls": metrics.total_calls,
                    "failed_calls": metrics.failed_calls,
                },
            )

        # Check rate limiting
        if metrics.rate_limited_calls >= self.config.rate_limit_alert_count:
            self._create_alert(
                severity=AlertSeverity.ERROR,
                provider=ctx.provider,
                message=f"Rate limiting detected for {ctx.provider}",
                details={
                    "rate_limited_calls": metrics.rate_limited_calls,
                    "total_calls": metrics.total_calls,
                },
            )

        # Check latency
        if ctx.duration_ms > self.config.latency_threshold_ms:
            self._create_alert(
                severity=AlertSeverity.WARNING,
                provider=ctx.provider,
                message=f"High latency for {ctx.provider}: {ctx.duration_ms}ms",
                details={
                    "latency_ms": ctx.duration_ms,
                    "threshold_ms": self.config.latency_threshold_ms,
                    "model": ctx.model,
                },
            )

        # Check budget
        budget_used = self._monthly_cost / self.config.monthly_budget_usd
        if budget_used >= self.config.budget_alert_threshold:
            self._create_alert(
                severity=AlertSeverity.CRITICAL
                if budget_used >= 1.0
                else AlertSeverity.WARNING,
                provider="all",
                message=f"Monthly LLM budget at {budget_used:.1%}",
                details={
                    "monthly_cost_usd": round(self._monthly_cost, 2),
                    "budget_usd": self.config.monthly_budget_usd,
                    "budget_used_percent": round(budget_used * 100, 1),
                },
            )

    def _create_alert(
        self,
        severity: AlertSeverity,
        provider: str,
        message: str,
        details: dict[str, Any],
    ) -> None:
        """Create and store an alert."""
        # Deduplicate similar alerts
        for existing in self._alerts[-50:]:
            if (
                existing.provider == provider
                and existing.message == message
                and (datetime.now(UTC) - existing.timestamp).seconds < 300
            ):
                return  # Skip duplicate

        alert = LLMAlert(
            alert_id=str(uuid4()),
            severity=severity,
            provider=provider,
            message=message,
            details=details,
            timestamp=datetime.now(UTC),
        )

        self._alerts.append(alert)

        # Log alert
        log_method = {
            AlertSeverity.INFO: logger.info,
            AlertSeverity.WARNING: logger.warning,
            AlertSeverity.ERROR: logger.error,
            AlertSeverity.CRITICAL: logger.critical,
        }.get(severity, logger.warning)

        log_method(f"LLM Alert [{severity.value}]: {message}")

    def _cleanup_old_calls(self) -> None:
        """Remove old call records based on retention."""
        if len(self._calls) <= self.config.max_records:
            return

        cutoff = time.time() - (self.config.retention_hours * 3600)
        self._calls = [c for c in self._calls if c.start_time > cutoff]

        # Keep at least max_records most recent
        if len(self._calls) > self.config.max_records:
            self._calls = self._calls[-self.config.max_records :]

    # ========================================================================
    # PUBLIC API
    # ========================================================================

    def get_provider_metrics(self, provider: str) -> Optional[LLMProviderMetrics]:
        """Get metrics for a specific provider."""
        return self._provider_metrics.get(provider)

    def get_all_metrics(self) -> dict[str, LLMProviderMetrics]:
        """Get metrics for all providers."""
        return dict(self._provider_metrics)

    def get_summary(self) -> dict[str, Any]:
        """Get overall summary metrics."""
        total_calls = sum(m.total_calls for m in self._provider_metrics.values())
        total_cost = sum(m.total_cost_usd for m in self._provider_metrics.values())
        total_tokens = sum(m.total_tokens for m in self._provider_metrics.values())

        successful = sum(m.successful_calls for m in self._provider_metrics.values())

        return {
            "total_calls": total_calls,
            "total_cost_usd": round(total_cost, 4),
            "total_tokens": total_tokens,
            "success_rate": successful / total_calls if total_calls > 0 else 1.0,
            "monthly_cost_usd": round(self._monthly_cost, 2),
            "monthly_budget_usd": self.config.monthly_budget_usd,
            "budget_used_percent": round(
                (self._monthly_cost / self.config.monthly_budget_usd) * 100, 1
            ),
            "provider_count": len(self._provider_metrics),
            "providers": {
                name: metrics.to_dict()
                for name, metrics in self._provider_metrics.items()
            },
        }

    def get_alerts(
        self,
        severity: Optional[AlertSeverity] = None,
        hours: int = 24,
    ) -> list[LLMAlert]:
        """Get recent alerts."""
        cutoff = datetime.now(UTC) - timedelta(hours=hours)
        alerts = [a for a in self._alerts if a.timestamp > cutoff]

        if severity:
            alerts = [a for a in alerts if a.severity == severity]

        return sorted(alerts, key=lambda a: a.timestamp, reverse=True)

    def get_model_usage(self) -> dict[str, dict[str, Any]]:
        """Get aggregated model usage across all providers."""
        combined: dict[str, dict[str, Any]] = {}

        for provider_metrics in self._provider_metrics.values():
            for model, stats in provider_metrics.model_usage.items():
                if model not in combined:
                    combined[model] = {
                        "providers": [],
                        "calls": 0,
                        "input_tokens": 0,
                        "output_tokens": 0,
                        "cost_usd": 0.0,
                    }

                combined[model]["providers"].append(provider_metrics.provider)
                combined[model]["calls"] += stats["calls"]
                combined[model]["input_tokens"] += stats["input_tokens"]
                combined[model]["output_tokens"] += stats["output_tokens"]
                combined[model]["cost_usd"] += stats["cost_usd"]

        return combined

    def get_cost_breakdown(self) -> dict[str, Any]:
        """Get cost breakdown by provider and model."""
        return {
            "monthly_total_usd": round(self._monthly_cost, 2),
            "monthly_budget_usd": self.config.monthly_budget_usd,
            "budget_remaining_usd": round(
                self.config.monthly_budget_usd - self._monthly_cost, 2
            ),
            "by_provider": {
                name: round(metrics.total_cost_usd, 4)
                for name, metrics in self._provider_metrics.items()
            },
            "by_model": {
                model: round(stats["cost_usd"], 4)
                for model, stats in self.get_model_usage().items()
            },
        }

    def reset(self) -> None:
        """Reset all metrics and alerts."""
        self._calls.clear()
        self._provider_metrics.clear()
        self._alerts.clear()
        self._monthly_cost = 0.0


# ============================================================================
# SINGLETON & FACTORY
# ============================================================================

_llm_telemetry: Optional[LLMTelemetry] = None


def get_llm_telemetry() -> LLMTelemetry:
    """Get the global LLM telemetry instance."""
    global _llm_telemetry
    if _llm_telemetry is None:
        _llm_telemetry = LLMTelemetry()
    return _llm_telemetry


def set_llm_telemetry(telemetry: LLMTelemetry) -> None:
    """Set the global LLM telemetry instance."""
    global _llm_telemetry
    _llm_telemetry = telemetry
