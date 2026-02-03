"""
Monitoring System Example Usage.

Demonstrates how to use the monitoring infrastructure:
- Metrics collection
- Alert configuration
- Health checks
- Background tasks
"""

import asyncio
import logging
import time
from datetime import datetime

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


async def example_metrics_collection():
    """Example: Collecting metrics."""
    from app.infrastructure.monitoring.metrics_collector import get_metrics_collector

    logger.info("=== Metrics Collection Example ===")

    collector = get_metrics_collector()

    # Simulate some requests
    for i in range(10):
        # Record request
        collector.increment_request_count(
            agent_name="code-expert",
            user_id=f"user_{i % 3}",
            endpoint="/chat/message",
            status="success" if i % 5 != 0 else "error",
        )

        # Record response time
        response_time = 0.1 + (i * 0.05)  # Gradually increasing
        collector.record_response_time(
            duration_seconds=response_time,
            agent_name="code-expert",
            endpoint="/chat/message",
        )

        # Record cost
        collector.record_cost(
            cost_usd=0.002 + (i * 0.001),
            agent_name="code-expert",
            prompt_tokens=100 + (i * 10),
            completion_tokens=200 + (i * 20),
            provider="openai",
        )

        # Record cache hit/miss
        if i % 3 == 0:
            collector.record_cache_hit(agent_name="code-expert")
        else:
            collector.record_cache_miss(agent_name="code-expert")

        # Record errors occasionally
        if i % 5 == 0:
            collector.increment_error_count(
                error_type="timeout",
                agent_name="code-expert",
                endpoint="/chat/message",
            )

    # Get metrics
    logger.info("\nMetrics Summary:")
    logger.info(f"Error Rate: {collector.get_error_rate():.2%}")
    logger.info(f"Cache Hit Rate: {collector.get_cache_hit_rate():.2%}")
    logger.info(f"Total Cost: ${collector.get_total_cost():.4f}")

    percentiles = collector.get_response_time_percentiles()
    logger.info(f"Response Time P50: {percentiles['p50']:.3f}s")
    logger.info(f"Response Time P95: {percentiles['p95']:.3f}s")
    logger.info(f"Response Time P99: {percentiles['p99']:.3f}s")

    # Export Prometheus metrics
    logger.info("\nPrometheus Metrics (first 500 chars):")
    metrics_text = collector.export_prometheus()
    logger.info(metrics_text[:500] + "...")


async def example_alerting():
    """Example: Setting up and evaluating alerts."""
    from app.infrastructure.monitoring.alerting import (
        AlertSeverity,
        BudgetAlert,
        ErrorSpikeAlert,
        PerformanceAlert,
        get_alert_manager,
    )
    from app.infrastructure.monitoring.metrics_collector import get_metrics_collector

    logger.info("\n=== Alerting Example ===")

    manager = get_alert_manager()
    metrics = get_metrics_collector()

    # Add alert rules
    manager.add_rule(
        PerformanceAlert(
            threshold_p95_ms=500.0,  # Will trigger
            threshold_p99_ms=1000.0,
            severity=AlertSeverity.WARNING,
            agent_name="code-expert",
        )
    )

    manager.add_rule(
        ErrorSpikeAlert(
            threshold_percentage=5.0,  # Will trigger
            critical_percentage=10.0,
        )
    )

    manager.add_rule(
        BudgetAlert(
            daily_budget_usd=0.01,  # Will trigger (set very low for demo)
            warning_threshold=0.5,
        )
    )

    # Evaluate alerts
    logger.info("Evaluating alert rules...")
    triggered_alerts = await manager.evaluate_all(metrics)

    if triggered_alerts:
        logger.info(f"\n{len(triggered_alerts)} alerts triggered:")
        for alert in triggered_alerts:
            logger.warning(
                f"[{alert.severity.value.upper()}] {alert.rule_name}: {alert.message}"
            )
    else:
        logger.info("No alerts triggered")

    # Get active alerts
    active_alerts = manager.get_active_alerts()
    logger.info(f"\nActive alerts: {len(active_alerts)}")

    # Resolve an alert
    if active_alerts:
        alert_to_resolve = active_alerts[0]
        manager.resolve_alert(alert_to_resolve.rule_name)
        logger.info(f"Resolved alert: {alert_to_resolve.rule_name}")


async def example_health_checks():
    """Example: Running health checks."""
    from app.infrastructure.monitoring.health_checks import (
        DatabaseHealthCheck,
        HealthStatus,
        RedisHealthCheck,
        get_health_service,
    )

    logger.info("\n=== Health Checks Example ===")

    service = get_health_service()

    # Add health checks
    service.add_check(DatabaseHealthCheck())
    service.add_check(RedisHealthCheck())

    # Check all components
    logger.info("Running health checks...")
    summary = await service.get_health_summary()

    logger.info(f"\nOverall Status: {summary['status']}")
    logger.info(f"Healthy: {summary['healthy_count']}")
    logger.info(f"Degraded: {summary['degraded_count']}")
    logger.info(f"Unhealthy: {summary['unhealthy_count']}")

    logger.info("\nComponent Details:")
    for name, health in summary["components"].items():
        status_emoji = {
            "healthy": "✅",
            "degraded": "⚠️",
            "unhealthy": "❌",
            "unknown": "❓",
        }
        emoji = status_emoji.get(health["status"], "❓")
        latency = f" ({health['latency_ms']:.1f}ms)" if health.get("latency_ms") else ""
        logger.info(f"{emoji} {name}: {health['message']}{latency}")


async def example_agent_metrics():
    """Example: Getting agent-specific metrics."""
    from app.infrastructure.monitoring.metrics_collector import get_metrics_collector

    logger.info("\n=== Agent Metrics Example ===")

    collector = get_metrics_collector()

    # Get metrics for specific agent
    agent_metrics = collector.get_agent_metrics("code-expert")

    logger.info("\nCode Expert Agent Metrics:")
    logger.info(f"Total Requests: {agent_metrics['total_requests']}")
    logger.info(f"Total Cost: ${agent_metrics['total_cost_usd']:.4f}")
    logger.info(f"Total Tokens: {agent_metrics['total_tokens']}")
    logger.info(f"Error Rate: {agent_metrics['error_rate']:.2%}")
    logger.info(f"Cache Hit Rate: {agent_metrics['cache_hit_rate']:.2%}")
    logger.info(f"Available: {agent_metrics['available']}")


async def example_background_tasks():
    """Example: Running background monitoring tasks."""
    from app.infrastructure.monitoring.background_tasks import (
        check_budget_utilization,
        run_periodic_alert_evaluation,
        run_periodic_health_checks,
    )

    logger.info("\n=== Background Tasks Example ===")

    # Run health checks
    logger.info("Running periodic health checks...")
    health_result = await run_periodic_health_checks()
    logger.info(f"Health check result: {health_result}")

    # Run alert evaluation
    logger.info("\nRunning periodic alert evaluation...")
    alert_result = await run_periodic_alert_evaluation()
    logger.info(f"Alert evaluation result: {alert_result}")

    # Check budget
    logger.info("\nChecking budget utilization...")
    budget_result = await check_budget_utilization()
    logger.info(f"Budget check result: {budget_result}")


async def example_custom_alert():
    """Example: Creating a custom alert rule."""
    from app.infrastructure.monitoring.alerting import (
        Alert,
        AlertCondition,
        AlertContext,
        AlertRule,
        AlertSeverity,
        get_alert_manager,
    )

    logger.info("\n=== Custom Alert Example ===")

    class CustomTokenAlert(AlertRule):
        """Alert when token usage exceeds threshold."""

        def __init__(self, threshold_tokens: int = 10000):
            super().__init__(
                name="high_token_usage",
                severity=AlertSeverity.WARNING,
                condition=AlertCondition.THRESHOLD_EXCEEDED,
            )
            self.threshold_tokens = threshold_tokens

        async def evaluate(self, metrics) -> Alert | None:
            """Evaluate token usage."""
            if not self.enabled or self.is_in_cooldown():
                return None

            agent_metrics = metrics.get_agent_metrics("code-expert")
            total_tokens = agent_metrics.get("total_tokens", 0)

            if total_tokens > self.threshold_tokens:
                return self.trigger_alert(
                    message=f"Token usage ({total_tokens:,}) exceeds threshold ({self.threshold_tokens:,})",
                    context=AlertContext(
                        agent_name="code-expert",
                        current_value=float(total_tokens),
                        threshold=float(self.threshold_tokens),
                    ),
                )

            return None

    # Add custom alert rule
    manager = get_alert_manager()
    manager.add_rule(CustomTokenAlert(threshold_tokens=1000))  # Low threshold for demo

    # Evaluate
    from app.infrastructure.monitoring.metrics_collector import get_metrics_collector

    metrics = get_metrics_collector()
    triggered_alerts = await manager.evaluate_all(metrics)

    custom_alerts = [a for a in triggered_alerts if a.rule_name == "high_token_usage"]
    if custom_alerts:
        logger.info(f"Custom alert triggered: {custom_alerts[0].message}")
    else:
        logger.info("Custom alert did not trigger")


async def main():
    """Run all examples."""
    logger.info("Starting Monitoring System Examples\n")

    try:
        # Run examples
        await example_metrics_collection()
        await example_alerting()
        await example_health_checks()
        await example_agent_metrics()
        await example_background_tasks()
        await example_custom_alert()

        logger.info("\n=== All Examples Completed Successfully ===")

    except Exception as e:
        logger.error(f"Error running examples: {e}", exc_info=True)


if __name__ == "__main__":
    asyncio.run(main())
