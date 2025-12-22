"""
Monitoring Providers for Dependency Injection.

Provides configured monitoring services:
- Metrics collector for chat features
- Alert manager with notification channels
- Health check service
- Background monitoring tasks
"""

from dishka import Provider, Scope, provide

from app.infrastructure.monitoring.alerting import (
    AlertManager,
    AlertNotificationChannel,
    BudgetAlert,
    CacheEfficiencyAlert,
    ConsoleNotificationChannel,
    EmailNotificationChannel,
    ErrorSpikeAlert,
    PerformanceAlert,
    WebhookNotificationChannel,
    get_alert_manager,
    setup_default_alerts,
)
from app.infrastructure.monitoring.health_checks import (
    DatabaseHealthCheck,
    HealthCheckService,
    RedisHealthCheck,
    SystemResourceHealthCheck,
    WebSocketHealthCheck,
    get_health_service,
    setup_default_health_checks,
)
from app.infrastructure.monitoring.metrics_collector import (
    ChatMetricsCollector,
    get_metrics_collector,
)


class MonitoringProvider(Provider):
    """Provider for monitoring infrastructure."""

    scope = Scope.APP

    # Metrics Collection

    @provide
    def provide_metrics_collector(self) -> ChatMetricsCollector:
        """
        Provide metrics collector.

        Returns:
            Global metrics collector instance
        """
        return get_metrics_collector()

    # Alert Management

    @provide
    def provide_alert_manager(self) -> AlertManager:
        """
        Provide alert manager.

        Returns:
            Global alert manager instance
        """
        return get_alert_manager()

    @provide
    def provide_console_notification_channel(self) -> ConsoleNotificationChannel:
        """
        Provide console notification channel.

        Returns:
            Console notification channel for development/testing
        """
        return ConsoleNotificationChannel()

    # Health Checks

    @provide
    def provide_health_service(self) -> HealthCheckService:
        """
        Provide health check service.

        Returns:
            Global health check service instance
        """
        return get_health_service()

    @provide
    def provide_database_health_check(self) -> DatabaseHealthCheck:
        """
        Provide database health check.

        Returns:
            Database health check instance
        """
        return DatabaseHealthCheck(
            name="database",
            slow_query_threshold_ms=100.0,
        )

    @provide
    def provide_redis_health_check(self) -> RedisHealthCheck:
        """
        Provide Redis health check.

        Returns:
            Redis health check instance
        """
        return RedisHealthCheck(
            name="redis",
            slow_operation_threshold_ms=50.0,
        )

    @provide
    def provide_websocket_health_check(self) -> WebSocketHealthCheck:
        """
        Provide WebSocket health check.

        Returns:
            WebSocket health check instance
        """
        return WebSocketHealthCheck(name="websocket")

    @provide
    def provide_system_resource_health_check(self) -> SystemResourceHealthCheck:
        """
        Provide system resource health check.

        Returns:
            System resource health check instance
        """
        return SystemResourceHealthCheck(
            name="system_resources",
            memory_threshold_percent=90.0,
            cpu_threshold_percent=90.0,
        )


def initialize_monitoring(
    daily_budget_usd: float = 100.0,
    response_time_p95_ms: float = 1000.0,
    webhook_url: str | None = None,
    alert_emails: list[str] | None = None,
) -> tuple[AlertManager, HealthCheckService]:
    """
    Initialize monitoring infrastructure.

    Args:
        daily_budget_usd: Daily budget limit in USD
        response_time_p95_ms: P95 response time threshold in ms
        webhook_url: Optional webhook URL for alerts
        alert_emails: Optional list of email addresses for alerts

    Returns:
        Tuple of (alert_manager, health_service)
    """
    import logging

    logger = logging.getLogger(__name__)

    # Setup metrics collector
    metrics = get_metrics_collector()
    logger.info("Initialized metrics collector")

    # Setup alert manager
    alert_manager = setup_default_alerts(
        metrics_collector=metrics,
        daily_budget_usd=daily_budget_usd,
        response_time_p95_ms=response_time_p95_ms,
    )

    # Add notification channels
    if webhook_url:
        alert_manager.add_notification_channel(
            WebhookNotificationChannel(webhook_url=webhook_url)
        )
        logger.info(f"Added webhook notification channel: {webhook_url}")

    if alert_emails:
        alert_manager.add_notification_channel(
            EmailNotificationChannel(
                to_emails=alert_emails,
                from_email="alerts@anvil.example.com",
            )
        )
        logger.info(f"Added email notification channel: {alert_emails}")

    # Setup health checks
    health_service = setup_default_health_checks()
    logger.info("Initialized health check service")

    return alert_manager, health_service
