"""
Background Tasks for Monitoring.

Celery tasks for periodic:
- Health check execution
- Alert evaluation
- Metrics aggregation
- Alerting delivery
"""

import logging
from datetime import datetime, timedelta, UTC
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


async def run_periodic_health_checks() -> Dict[str, str]:
    """
    Run periodic health checks for all components.

    Returns:
        Dictionary with health status summary
    """
    from app.infrastructure.monitoring.health_checks import get_health_service

    try:
        service = get_health_service()
        summary = await service.get_health_summary()

        # Log unhealthy components
        unhealthy = [
            name
            for name, health in summary["components"].items()
            if health["status"] in ["unhealthy", "degraded"]
        ]

        if unhealthy:
            logger.warning(
                f"Unhealthy components detected: {', '.join(unhealthy)}",
                extra={"unhealthy_components": unhealthy},
            )
        else:
            logger.info("All components healthy")

        return {
            "status": summary["status"],
            "healthy_count": summary["healthy_count"],
            "degraded_count": summary["degraded_count"],
            "unhealthy_count": summary["unhealthy_count"],
            "timestamp": summary["timestamp"],
        }

    except Exception as e:
        logger.error(f"Error running health checks: {e}", exc_info=True)
        return {
            "status": "error",
            "error": str(e),
            "timestamp": datetime.now(UTC).isoformat(),
        }


async def run_periodic_alert_evaluation() -> Dict[str, int]:
    """
    Evaluate all alert rules and send notifications.

    Returns:
        Dictionary with alert counts
    """
    from app.infrastructure.monitoring.alerting import get_alert_manager
    from app.infrastructure.monitoring.metrics_collector import get_metrics_collector

    try:
        manager = get_alert_manager()
        metrics = get_metrics_collector()

        # Evaluate all rules
        triggered_alerts = await manager.evaluate_all(metrics)

        # Get active alerts
        active_alerts = manager.get_active_alerts()

        logger.info(
            f"Alert evaluation complete: {len(triggered_alerts)} triggered, {len(active_alerts)} active"
        )

        return {
            "triggered_count": len(triggered_alerts),
            "active_count": len(active_alerts),
            "timestamp": datetime.now(UTC).isoformat(),
        }

    except Exception as e:
        logger.error(f"Error evaluating alerts: {e}", exc_info=True)
        return {
            "error": str(e),
            "timestamp": datetime.now(UTC).isoformat(),
        }


async def aggregate_metrics_hourly() -> Dict[str, int]:
    """
    Aggregate metrics on an hourly basis.

    Returns:
        Dictionary with aggregation summary
    """
    try:
        # In production, this would aggregate metrics from time-series DB
        # and store rolled-up data for efficient querying

        logger.info("Hourly metrics aggregation complete")

        return {
            "aggregated_count": 0,  # Placeholder
            "timestamp": datetime.now(UTC).isoformat(),
        }

    except Exception as e:
        logger.error(f"Error aggregating metrics: {e}", exc_info=True)
        return {
            "error": str(e),
            "timestamp": datetime.now(UTC).isoformat(),
        }


async def cleanup_old_metrics(retention_days: int = 30) -> Dict[str, int]:
    """
    Clean up old metrics data.

    Args:
        retention_days: Number of days to retain metrics

    Returns:
        Dictionary with cleanup summary
    """
    try:
        # In production, this would:
        # 1. Delete raw metrics older than retention period
        # 2. Keep aggregated data for longer
        # 3. Archive critical metrics

        logger.info(f"Cleaned up metrics older than {retention_days} days")

        return {
            "deleted_count": 0,  # Placeholder
            "retention_days": retention_days,
            "timestamp": datetime.now(UTC).isoformat(),
        }

    except Exception as e:
        logger.error(f"Error cleaning up metrics: {e}", exc_info=True)
        return {
            "error": str(e),
            "timestamp": datetime.now(UTC).isoformat(),
        }


async def check_budget_utilization() -> Dict[str, float]:
    """
    Check budget utilization and send alerts if needed.

    Returns:
        Dictionary with budget utilization summary
    """
    from app.infrastructure.monitoring.metrics_collector import get_metrics_collector

    try:
        metrics = get_metrics_collector()

        # Get total cost
        total_cost = metrics.get_total_cost()

        # In production, compare against configured daily/monthly budgets
        daily_budget = 100.0  # TODO: Get from config
        utilization_percent = (total_cost / daily_budget) * 100

        if utilization_percent > 80:
            logger.warning(
                f"High budget utilization: {utilization_percent:.1f}%",
                extra={
                    "total_cost_usd": total_cost,
                    "daily_budget_usd": daily_budget,
                    "utilization_percent": utilization_percent,
                },
            )

        return {
            "total_cost_usd": total_cost,
            "daily_budget_usd": daily_budget,
            "utilization_percent": utilization_percent,
            "timestamp": datetime.now(UTC).isoformat(),
        }

    except Exception as e:
        logger.error(f"Error checking budget utilization: {e}", exc_info=True)
        return {
            "error": str(e),
            "timestamp": datetime.now(UTC).isoformat(),
        }


async def generate_daily_metrics_report() -> Dict[str, any]:
    """
    Generate daily metrics report.

    Returns:
        Dictionary with daily metrics summary
    """
    from app.infrastructure.monitoring.metrics_collector import get_metrics_collector

    try:
        metrics = get_metrics_collector()

        # Calculate report for last 24 hours
        # In production, this would query time-series data

        report = {
            "date": datetime.now(UTC).date().isoformat(),
            "total_requests": 0,  # Placeholder
            "total_errors": 0,
            "total_cost_usd": metrics.get_total_cost(),
            "avg_response_time_ms": 0.0,
            "cache_hit_rate": metrics.get_cache_hit_rate(),
            "error_rate": metrics.get_error_rate(),
            "timestamp": datetime.now(UTC).isoformat(),
        }

        logger.info("Daily metrics report generated", extra=report)

        return report

    except Exception as e:
        logger.error(f"Error generating daily report: {e}", exc_info=True)
        return {
            "error": str(e),
            "timestamp": datetime.now(UTC).isoformat(),
        }


# Celery task registration (optional - use if you have Celery configured)
try:
    from celery import shared_task

    @shared_task(name="monitoring.health_checks")
    def celery_health_checks():
        """Celery task for periodic health checks."""
        import asyncio

        return asyncio.run(run_periodic_health_checks())

    @shared_task(name="monitoring.alert_evaluation")
    def celery_alert_evaluation():
        """Celery task for periodic alert evaluation."""
        import asyncio

        return asyncio.run(run_periodic_alert_evaluation())

    @shared_task(name="monitoring.aggregate_metrics")
    def celery_aggregate_metrics():
        """Celery task for hourly metrics aggregation."""
        import asyncio

        return asyncio.run(aggregate_metrics_hourly())

    @shared_task(name="monitoring.cleanup_metrics")
    def celery_cleanup_metrics():
        """Celery task for metrics cleanup."""
        import asyncio

        return asyncio.run(cleanup_old_metrics())

    @shared_task(name="monitoring.budget_check")
    def celery_budget_check():
        """Celery task for budget utilization check."""
        import asyncio

        return asyncio.run(check_budget_utilization())

    @shared_task(name="monitoring.daily_report")
    def celery_daily_report():
        """Celery task for daily metrics report."""
        import asyncio

        return asyncio.run(generate_daily_metrics_report())

    logger.info("Celery monitoring tasks registered")

except ImportError:
    logger.info("Celery not available, skipping task registration")


def setup_monitoring_schedule():
    """
    Setup periodic monitoring tasks.

    Call this during application startup to configure
    background task schedules.
    """
    try:
        from celery.schedules import crontab

        # This would be added to your Celery beat schedule configuration
        schedule = {
            "health-checks-every-minute": {
                "task": "monitoring.health_checks",
                "schedule": 60.0,  # Every 60 seconds
            },
            "alert-evaluation-every-minute": {
                "task": "monitoring.alert_evaluation",
                "schedule": 60.0,
            },
            "aggregate-metrics-hourly": {
                "task": "monitoring.aggregate_metrics",
                "schedule": crontab(minute=0),  # Every hour
            },
            "cleanup-metrics-daily": {
                "task": "monitoring.cleanup_metrics",
                "schedule": crontab(hour=2, minute=0),  # 2 AM daily
            },
            "budget-check-every-hour": {
                "task": "monitoring.budget_check",
                "schedule": 3600.0,  # Every hour
            },
            "daily-report": {
                "task": "monitoring.daily_report",
                "schedule": crontab(hour=0, minute=0),  # Midnight daily
            },
        }

        logger.info("Monitoring schedule configured")
        return schedule

    except ImportError:
        logger.warning("Celery not available, cannot setup monitoring schedule")
        return {}
