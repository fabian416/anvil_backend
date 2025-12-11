"""
Enterprise Telemetry & Analytics Module.

Provides comprehensive observability for all system components:
- External API metrics collection (Prometheus-compatible)
- LLM provider monitoring (tokens, cost, latency)
- Database query telemetry (slow queries, patterns)
- Distributed tracing (OpenTelemetry)
- Feature flags for granular control
- Cost tracking and budget alerting
"""

from app.infrastructure.telemetry.api_telemetry import (
    APITelemetry,
    APIMetrics,
    APICallContext,
    TelemetryConfig,
)
from app.infrastructure.telemetry.metrics_exporter import (
    MetricsExporter,
    PrometheusMetrics,
)
from app.infrastructure.telemetry.tracing import (
    TracingService,
    SpanContext,
)
from app.infrastructure.telemetry.llm_telemetry import (
    LLMTelemetry,
    LLMCallContext,
    LLMCallStatus,
    LLMProviderMetrics,
    LLMTelemetryConfig,
    LLMAlert,
    get_llm_telemetry,
)
from app.infrastructure.telemetry.db_telemetry import (
    DatabaseTelemetry,
    DbTelemetryConfig,
    QueryExecution,
    QueryPattern,
    QueryType,
    QueryStatus,
    DatabaseMetrics,
    ConnectionPoolStats,
    setup_engine_telemetry,
    get_db_telemetry,
)
from app.infrastructure.telemetry.feature_flags import (
    TelemetryFeatureFlags,
    get_feature_flags,
    set_feature_flags,
    load_feature_flags_from_env,
    save_flags_to_redis,
    load_flags_from_redis,
    delete_flags_from_redis,
    initialize_feature_flags,
)
from app.infrastructure.telemetry.alert_destinations import (
    AlertDispatcher,
    AlertDestinationConfig,
    TelemetryAlert,
    EmailAlertDestination,
    SlackAlertDestination,
    PagerDutyAlertDestination,
    ConsoleAlertDestination,
    get_alert_dispatcher,
)

__all__ = [
    # Feature Flags
    "TelemetryFeatureFlags",
    "get_feature_flags",
    "set_feature_flags",
    "load_feature_flags_from_env",
    "save_flags_to_redis",
    "load_flags_from_redis",
    "delete_flags_from_redis",
    "initialize_feature_flags",
    # Alert Destinations
    "AlertDispatcher",
    "AlertDestinationConfig",
    "TelemetryAlert",
    "EmailAlertDestination",
    "SlackAlertDestination",
    "PagerDutyAlertDestination",
    "ConsoleAlertDestination",
    "get_alert_dispatcher",
    # External API Telemetry
    "APITelemetry",
    "APIMetrics",
    "APICallContext",
    "TelemetryConfig",
    # Metrics Export
    "MetricsExporter",
    "PrometheusMetrics",
    # Tracing
    "TracingService",
    "SpanContext",
    # LLM Telemetry
    "LLMTelemetry",
    "LLMCallContext",
    "LLMCallStatus",
    "LLMProviderMetrics",
    "LLMTelemetryConfig",
    "LLMAlert",
    "get_llm_telemetry",
    # Database Telemetry
    "DatabaseTelemetry",
    "DbTelemetryConfig",
    "QueryExecution",
    "QueryPattern",
    "QueryType",
    "QueryStatus",
    "DatabaseMetrics",
    "ConnectionPoolStats",
    "setup_engine_telemetry",
    "get_db_telemetry",
]
