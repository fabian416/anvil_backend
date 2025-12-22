"""
Comprehensive Monitoring & Alerting Infrastructure.

Production-ready monitoring system for chat features with:
- Prometheus-compatible metrics collection
- Intelligent alerting with multiple thresholds
- Comprehensive health checks
- Structured logging with correlation IDs
- Auto-instrumentation for FastAPI
- Background health check tasks
"""

from app.infrastructure.monitoring.metrics_collector import (
    ChatMetricsCollector,
    MetricType,
    get_metrics_collector,
)
from app.infrastructure.monitoring.alerting import (
    AlertManager,
    AlertRule,
    AlertSeverity,
    AlertCondition,
    PerformanceAlert,
    BudgetAlert,
    ErrorSpikeAlert,
    CacheEfficiencyAlert,
    AgentAvailabilityAlert,
    get_alert_manager,
)
from app.infrastructure.monitoring.health_checks import (
    HealthCheckService,
    HealthStatus,
    ComponentHealth,
    DatabaseHealthCheck,
    RedisHealthCheck,
    ExternalAPIHealthCheck,
    WebSocketHealthCheck,
    get_health_service,
)

__all__ = [
    # Metrics
    "ChatMetricsCollector",
    "MetricType",
    "get_metrics_collector",
    # Alerting
    "AlertManager",
    "AlertRule",
    "AlertSeverity",
    "AlertCondition",
    "PerformanceAlert",
    "BudgetAlert",
    "ErrorSpikeAlert",
    "CacheEfficiencyAlert",
    "AgentAvailabilityAlert",
    "get_alert_manager",
    # Health Checks
    "HealthCheckService",
    "HealthStatus",
    "ComponentHealth",
    "DatabaseHealthCheck",
    "RedisHealthCheck",
    "ExternalAPIHealthCheck",
    "WebSocketHealthCheck",
    "get_health_service",
]
