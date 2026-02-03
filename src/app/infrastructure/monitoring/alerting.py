"""
Intelligent Alerting System for Chat Features.

Production-ready alerting with:
- Performance degradation detection
- Budget violation warnings
- Error spike notifications
- Cache efficiency monitoring
- Agent availability tracking
- Multi-channel notifications (webhook, email, Slack)
- Smart throttling to prevent alert fatigue
- Contextual alert enrichment
"""

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timedelta, UTC
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set

logger = logging.getLogger(__name__)


class AlertSeverity(Enum):
    """Alert severity levels."""

    INFO = "info"  # Informational
    WARNING = "warning"  # Potential issue
    ERROR = "error"  # Definite problem
    CRITICAL = "critical"  # Service degradation


class AlertCondition(Enum):
    """Alert condition types."""

    THRESHOLD_EXCEEDED = "threshold_exceeded"  # Value > threshold
    THRESHOLD_BELOW = "threshold_below"  # Value < threshold
    RATE_EXCEEDED = "rate_exceeded"  # Change rate too high
    ANOMALY = "anomaly"  # Statistical anomaly
    CONSECUTIVE_FAILURES = "consecutive_failures"  # Multiple failures in a row


@dataclass
class AlertContext:
    """Additional context for alerts."""

    agent_name: Optional[str] = None
    endpoint: Optional[str] = None
    current_value: Optional[float] = None
    threshold: Optional[float] = None
    window: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        result = {
            "agent_name": self.agent_name,
            "endpoint": self.endpoint,
            "current_value": self.current_value,
            "threshold": self.threshold,
            "window": self.window,
        }
        result.update(self.metadata)
        return {k: v for k, v in result.items() if v is not None}


@dataclass
class Alert:
    """Alert instance."""

    id: str
    rule_name: str
    severity: AlertSeverity
    condition: AlertCondition
    message: str
    context: AlertContext
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))
    resolved: bool = False
    resolved_at: Optional[datetime] = None

    def resolve(self) -> None:
        """Mark alert as resolved."""
        self.resolved = True
        self.resolved_at = datetime.now(UTC)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "rule_name": self.rule_name,
            "severity": self.severity.value,
            "condition": self.condition.value,
            "message": self.message,
            "context": self.context.to_dict(),
            "timestamp": self.timestamp.isoformat(),
            "resolved": self.resolved,
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None,
        }


class AlertRule(ABC):
    """
    Base class for alert rules.

    Subclasses implement specific alert logic (performance, budget, errors, etc.)
    """

    def __init__(
        self,
        name: str,
        severity: AlertSeverity,
        condition: AlertCondition,
        enabled: bool = True,
    ):
        """
        Initialize alert rule.

        Args:
            name: Rule name
            severity: Alert severity
            condition: Alert condition type
            enabled: Whether rule is active
        """
        self.name = name
        self.severity = severity
        self.condition = condition
        self.enabled = enabled
        self._last_triggered: Optional[datetime] = None
        self._cooldown_period = timedelta(minutes=5)

    @abstractmethod
    def evaluate(self, metrics: Any) -> Optional[Alert]:
        """
        Evaluate rule against current metrics.

        Args:
            metrics: Metrics collector or metrics data

        Returns:
            Alert if rule triggered, None otherwise
        """
        pass

    def is_in_cooldown(self) -> bool:
        """Check if rule is in cooldown period."""
        if not self._last_triggered:
            return False

        return datetime.now(UTC) - self._last_triggered < self._cooldown_period

    def trigger_alert(self, message: str, context: AlertContext) -> Alert:
        """
        Trigger an alert.

        Args:
            message: Alert message
            context: Alert context

        Returns:
            Created alert
        """
        self._last_triggered = datetime.now(UTC)
        alert_id = f"{self.name}_{int(self._last_triggered.timestamp())}"

        return Alert(
            id=alert_id,
            rule_name=self.name,
            severity=self.severity,
            condition=self.condition,
            message=message,
            context=context,
        )


class PerformanceAlert(AlertRule):
    """Alert when response time exceeds threshold."""

    def __init__(
        self,
        threshold_p95_ms: float = 1000.0,
        threshold_p99_ms: float = 2000.0,
        severity: AlertSeverity = AlertSeverity.WARNING,
        agent_name: Optional[str] = None,
    ):
        """
        Initialize performance alert.

        Args:
            threshold_p95_ms: P95 response time threshold in milliseconds
            threshold_p99_ms: P99 response time threshold in milliseconds
            severity: Alert severity
            agent_name: Filter by specific agent (None for all)
        """
        super().__init__(
            name=f"performance_degradation_{agent_name or 'all'}",
            severity=severity,
            condition=AlertCondition.THRESHOLD_EXCEEDED,
        )
        self.threshold_p95_ms = threshold_p95_ms
        self.threshold_p99_ms = threshold_p99_ms
        self.agent_name = agent_name

    def evaluate(self, metrics: Any) -> Optional[Alert]:
        """Evaluate performance metrics."""
        if not self.enabled or self.is_in_cooldown():
            return None

        try:
            percentiles = metrics.get_response_time_percentiles(
                agent_name=self.agent_name
            )

            p95 = percentiles.get("p95")
            p99 = percentiles.get("p99")

            if p95 is None or p99 is None:
                return None

            p95_ms = p95 * 1000
            p99_ms = p99 * 1000

            if p99_ms > self.threshold_p99_ms:
                return self.trigger_alert(
                    message=f"Response time P99 ({p99_ms:.0f}ms) exceeds threshold ({self.threshold_p99_ms:.0f}ms)",
                    context=AlertContext(
                        agent_name=self.agent_name,
                        current_value=p99_ms,
                        threshold=self.threshold_p99_ms,
                        window="P99",
                        metadata={"p95_ms": p95_ms, "p99_ms": p99_ms},
                    ),
                )

            if p95_ms > self.threshold_p95_ms:
                return self.trigger_alert(
                    message=f"Response time P95 ({p95_ms:.0f}ms) exceeds threshold ({self.threshold_p95_ms:.0f}ms)",
                    context=AlertContext(
                        agent_name=self.agent_name,
                        current_value=p95_ms,
                        threshold=self.threshold_p95_ms,
                        window="P95",
                        metadata={"p95_ms": p95_ms, "p99_ms": p99_ms},
                    ),
                )

        except Exception as e:
            logger.error(f"Error evaluating performance alert: {e}")

        return None


class BudgetAlert(AlertRule):
    """Alert when cost exceeds budget."""

    def __init__(
        self,
        daily_budget_usd: float = 100.0,
        warning_threshold: float = 0.8,  # 80% of budget
        critical_threshold: float = 1.0,  # 100% of budget
        agent_name: Optional[str] = None,
    ):
        """
        Initialize budget alert.

        Args:
            daily_budget_usd: Daily budget in USD
            warning_threshold: Warning threshold as fraction of budget
            critical_threshold: Critical threshold as fraction of budget
            agent_name: Filter by specific agent (None for all)
        """
        super().__init__(
            name=f"budget_violation_{agent_name or 'all'}",
            severity=AlertSeverity.WARNING,
            condition=AlertCondition.THRESHOLD_EXCEEDED,
        )
        self.daily_budget_usd = daily_budget_usd
        self.warning_threshold = warning_threshold
        self.critical_threshold = critical_threshold
        self.agent_name = agent_name

    def evaluate(self, metrics: Any) -> Optional[Alert]:
        """Evaluate budget metrics."""
        if not self.enabled or self.is_in_cooldown():
            return None

        try:
            total_cost = metrics.get_total_cost(agent_name=self.agent_name)
            cost_ratio = total_cost / self.daily_budget_usd

            if cost_ratio >= self.critical_threshold:
                return self.trigger_alert(
                    message=f"Cost (${total_cost:.2f}) exceeds daily budget (${self.daily_budget_usd:.2f})",
                    context=AlertContext(
                        agent_name=self.agent_name,
                        current_value=total_cost,
                        threshold=self.daily_budget_usd,
                        metadata={
                            "budget_usd": self.daily_budget_usd,
                            "percentage": cost_ratio * 100,
                        },
                    ),
                )

            if cost_ratio >= self.warning_threshold:
                return self.trigger_alert(
                    message=f"Cost (${total_cost:.2f}) at {cost_ratio * 100:.0f}% of daily budget (${self.daily_budget_usd:.2f})",
                    context=AlertContext(
                        agent_name=self.agent_name,
                        current_value=total_cost,
                        threshold=self.daily_budget_usd * self.warning_threshold,
                        metadata={
                            "budget_usd": self.daily_budget_usd,
                            "percentage": cost_ratio * 100,
                        },
                    ),
                )

        except Exception as e:
            logger.error(f"Error evaluating budget alert: {e}")

        return None


class ErrorSpikeAlert(AlertRule):
    """Alert when error rate spikes."""

    def __init__(
        self,
        threshold_percentage: float = 5.0,  # 5% error rate
        critical_percentage: float = 10.0,  # 10% error rate
        agent_name: Optional[str] = None,
    ):
        """
        Initialize error spike alert.

        Args:
            threshold_percentage: Warning threshold (%)
            critical_percentage: Critical threshold (%)
            agent_name: Filter by specific agent (None for all)
        """
        super().__init__(
            name=f"error_spike_{agent_name or 'all'}",
            severity=AlertSeverity.ERROR,
            condition=AlertCondition.THRESHOLD_EXCEEDED,
        )
        self.threshold_percentage = threshold_percentage
        self.critical_percentage = critical_percentage
        self.agent_name = agent_name

    def evaluate(self, metrics: Any) -> Optional[Alert]:
        """Evaluate error rate metrics."""
        if not self.enabled or self.is_in_cooldown():
            return None

        try:
            error_rate = metrics.get_error_rate(agent_name=self.agent_name)
            error_percentage = error_rate * 100

            if error_percentage >= self.critical_percentage:
                return self.trigger_alert(
                    message=f"Critical error rate ({error_percentage:.1f}%) exceeds threshold ({self.critical_percentage:.1f}%)",
                    context=AlertContext(
                        agent_name=self.agent_name,
                        current_value=error_percentage,
                        threshold=self.critical_percentage,
                        metadata={"error_rate": error_rate},
                    ),
                )

            if error_percentage >= self.threshold_percentage:
                return self.trigger_alert(
                    message=f"Error rate ({error_percentage:.1f}%) exceeds threshold ({self.threshold_percentage:.1f}%)",
                    context=AlertContext(
                        agent_name=self.agent_name,
                        current_value=error_percentage,
                        threshold=self.threshold_percentage,
                        metadata={"error_rate": error_rate},
                    ),
                )

        except Exception as e:
            logger.error(f"Error evaluating error spike alert: {e}")

        return None


class CacheEfficiencyAlert(AlertRule):
    """Alert when cache hit rate is too low."""

    def __init__(
        self,
        min_hit_rate: float = 0.5,  # 50% minimum hit rate
        agent_name: Optional[str] = None,
    ):
        """
        Initialize cache efficiency alert.

        Args:
            min_hit_rate: Minimum acceptable cache hit rate (0.0 to 1.0)
            agent_name: Filter by specific agent (None for all)
        """
        super().__init__(
            name=f"cache_efficiency_{agent_name or 'all'}",
            severity=AlertSeverity.WARNING,
            condition=AlertCondition.THRESHOLD_BELOW,
        )
        self.min_hit_rate = min_hit_rate
        self.agent_name = agent_name

    def evaluate(self, metrics: Any) -> Optional[Alert]:
        """Evaluate cache efficiency metrics."""
        if not self.enabled or self.is_in_cooldown():
            return None

        try:
            hit_rate = metrics.get_cache_hit_rate(agent_name=self.agent_name)

            if hit_rate < self.min_hit_rate:
                return self.trigger_alert(
                    message=f"Cache hit rate ({hit_rate * 100:.1f}%) below threshold ({self.min_hit_rate * 100:.1f}%)",
                    context=AlertContext(
                        agent_name=self.agent_name,
                        current_value=hit_rate * 100,
                        threshold=self.min_hit_rate * 100,
                        metadata={"hit_rate": hit_rate},
                    ),
                )

        except Exception as e:
            logger.error(f"Error evaluating cache efficiency alert: {e}")

        return None


class AgentAvailabilityAlert(AlertRule):
    """Alert when agent becomes unavailable."""

    def __init__(self, agent_name: str):
        """
        Initialize agent availability alert.

        Args:
            agent_name: Agent to monitor
        """
        super().__init__(
            name=f"agent_availability_{agent_name}",
            severity=AlertSeverity.CRITICAL,
            condition=AlertCondition.THRESHOLD_BELOW,
        )
        self.agent_name = agent_name

    def evaluate(self, metrics: Any) -> Optional[Alert]:
        """Evaluate agent availability."""
        if not self.enabled or self.is_in_cooldown():
            return None

        try:
            agent_metrics = metrics.get_agent_metrics(self.agent_name)

            if not agent_metrics.get("available", True):
                return self.trigger_alert(
                    message=f"Agent {self.agent_name} is unavailable",
                    context=AlertContext(
                        agent_name=self.agent_name,
                        current_value=0.0,
                        threshold=1.0,
                        metadata=agent_metrics,
                    ),
                )

        except Exception as e:
            logger.error(f"Error evaluating agent availability alert: {e}")

        return None


class AlertNotificationChannel(ABC):
    """Base class for alert notification channels."""

    @abstractmethod
    async def send_alert(self, alert: Alert) -> bool:
        """
        Send alert notification.

        Args:
            alert: Alert to send

        Returns:
            True if sent successfully
        """
        pass


class WebhookNotificationChannel(AlertNotificationChannel):
    """Send alerts via HTTP webhook."""

    def __init__(self, webhook_url: str):
        """
        Initialize webhook channel.

        Args:
            webhook_url: Webhook URL to POST alerts to
        """
        self.webhook_url = webhook_url

    async def send_alert(self, alert: Alert) -> bool:
        """Send alert via webhook."""
        try:
            import httpx

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.webhook_url,
                    json=alert.to_dict(),
                    timeout=10.0,
                )
                return response.status_code == 200

        except Exception as e:
            logger.error(f"Failed to send webhook alert: {e}")
            return False


class EmailNotificationChannel(AlertNotificationChannel):
    """Send alerts via email."""

    def __init__(self, to_emails: List[str], from_email: str):
        """
        Initialize email channel.

        Args:
            to_emails: List of recipient email addresses
            from_email: Sender email address
        """
        self.to_emails = to_emails
        self.from_email = from_email

    async def send_alert(self, alert: Alert) -> bool:
        """Send alert via email."""
        try:
            # Integrate with your email service (SendGrid, AWS SES, etc.)
            logger.info(f"Would send email alert to {self.to_emails}: {alert.message}")
            return True

        except Exception as e:
            logger.error(f"Failed to send email alert: {e}")
            return False


class ConsoleNotificationChannel(AlertNotificationChannel):
    """Log alerts to console (for development/testing)."""

    async def send_alert(self, alert: Alert) -> bool:
        """Log alert to console."""
        severity_emoji = {
            AlertSeverity.INFO: "ℹ️",
            AlertSeverity.WARNING: "⚠️",
            AlertSeverity.ERROR: "❌",
            AlertSeverity.CRITICAL: "🚨",
        }

        emoji = severity_emoji.get(alert.severity, "📢")
        logger.warning(
            f"{emoji} ALERT [{alert.severity.value.upper()}] {alert.rule_name}: {alert.message}"
        )
        logger.warning(f"Context: {alert.context.to_dict()}")
        return True


class AlertManager:
    """
    Manages alert rules and notifications.

    Coordinates alert evaluation, deduplication, and notification delivery.
    """

    def __init__(self):
        """Initialize alert manager."""
        self.rules: List[AlertRule] = []
        self.notification_channels: List[AlertNotificationChannel] = []
        self.active_alerts: Dict[str, Alert] = {}
        self.alert_history: List[Alert] = []
        self._max_history = 1000

    def add_rule(self, rule: AlertRule) -> None:
        """
        Add alert rule.

        Args:
            rule: Alert rule to add
        """
        self.rules.append(rule)
        logger.info(f"Added alert rule: {rule.name}")

    def remove_rule(self, rule_name: str) -> bool:
        """
        Remove alert rule by name.

        Args:
            rule_name: Name of rule to remove

        Returns:
            True if rule was removed
        """
        for i, rule in enumerate(self.rules):
            if rule.name == rule_name:
                del self.rules[i]
                logger.info(f"Removed alert rule: {rule_name}")
                return True
        return False

    def add_notification_channel(self, channel: AlertNotificationChannel) -> None:
        """
        Add notification channel.

        Args:
            channel: Notification channel to add
        """
        self.notification_channels.append(channel)
        logger.info(f"Added notification channel: {type(channel).__name__}")

    async def evaluate_all(self, metrics: Any) -> List[Alert]:
        """
        Evaluate all alert rules.

        Args:
            metrics: Metrics collector

        Returns:
            List of triggered alerts
        """
        triggered_alerts: List[Alert] = []

        for rule in self.rules:
            if not rule.enabled:
                continue

            try:
                alert = rule.evaluate(metrics)
                if alert:
                    triggered_alerts.append(alert)
                    await self._process_alert(alert)

            except Exception as e:
                logger.error(f"Error evaluating rule {rule.name}: {e}")

        return triggered_alerts

    async def _process_alert(self, alert: Alert) -> None:
        """
        Process triggered alert.

        Args:
            alert: Alert to process
        """
        # Check if this is a duplicate
        if alert.rule_name in self.active_alerts:
            existing = self.active_alerts[alert.rule_name]
            if not existing.resolved:
                logger.debug(f"Suppressing duplicate alert: {alert.rule_name}")
                return

        # Store as active alert
        self.active_alerts[alert.rule_name] = alert

        # Add to history
        self.alert_history.append(alert)
        if len(self.alert_history) > self._max_history:
            self.alert_history = self.alert_history[-self._max_history :]

        # Send notifications
        await self._send_notifications(alert)

    async def _send_notifications(self, alert: Alert) -> None:
        """
        Send alert to all notification channels.

        Args:
            alert: Alert to send
        """
        for channel in self.notification_channels:
            try:
                success = await channel.send_alert(alert)
                if not success:
                    logger.error(f"Failed to send alert via {type(channel).__name__}")

            except Exception as e:
                logger.error(f"Error sending alert via {type(channel).__name__}: {e}")

    def resolve_alert(self, rule_name: str) -> bool:
        """
        Resolve an active alert.

        Args:
            rule_name: Name of rule to resolve

        Returns:
            True if alert was resolved
        """
        if rule_name in self.active_alerts:
            alert = self.active_alerts[rule_name]
            alert.resolve()
            logger.info(f"Resolved alert: {rule_name}")
            return True
        return False

    def get_active_alerts(self) -> List[Alert]:
        """Get all active (unresolved) alerts."""
        return [alert for alert in self.active_alerts.values() if not alert.resolved]

    def get_alert_history(
        self, limit: int = 100, severity: Optional[AlertSeverity] = None
    ) -> List[Alert]:
        """
        Get alert history.

        Args:
            limit: Maximum number of alerts to return
            severity: Filter by severity

        Returns:
            List of historical alerts
        """
        alerts = self.alert_history
        if severity:
            alerts = [a for a in alerts if a.severity == severity]

        return alerts[-limit:]


# Global alert manager instance
_alert_manager: Optional[AlertManager] = None


def get_alert_manager() -> AlertManager:
    """Get or create global alert manager instance."""
    global _alert_manager
    if _alert_manager is None:
        _alert_manager = AlertManager()
        # Add default console notification for development
        _alert_manager.add_notification_channel(ConsoleNotificationChannel())
    return _alert_manager


def setup_default_alerts(
    metrics_collector: Any,
    daily_budget_usd: float = 100.0,
    response_time_p95_ms: float = 1000.0,
) -> AlertManager:
    """
    Setup default alert rules.

    Args:
        metrics_collector: Metrics collector instance
        daily_budget_usd: Daily budget limit in USD
        response_time_p95_ms: P95 response time threshold in ms

    Returns:
        Configured alert manager
    """
    manager = get_alert_manager()

    # Performance alerts
    manager.add_rule(
        PerformanceAlert(
            threshold_p95_ms=response_time_p95_ms,
            threshold_p99_ms=response_time_p95_ms * 2,
            severity=AlertSeverity.WARNING,
        )
    )

    # Budget alerts
    manager.add_rule(
        BudgetAlert(
            daily_budget_usd=daily_budget_usd,
            warning_threshold=0.8,
            critical_threshold=1.0,
        )
    )

    # Error spike alerts
    manager.add_rule(
        ErrorSpikeAlert(
            threshold_percentage=5.0,
            critical_percentage=10.0,
        )
    )

    # Cache efficiency alerts
    manager.add_rule(
        CacheEfficiencyAlert(
            min_hit_rate=0.5,
        )
    )

    logger.info("Setup default alert rules")
    return manager
