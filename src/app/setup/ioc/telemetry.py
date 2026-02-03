"""
Telemetry Providers for Dependency Injection.

Provides configured telemetry services:
- Feature flags for granular telemetry control
- API telemetry for all external API integrations
- LLM telemetry for AI provider monitoring
- Database telemetry for query monitoring
- Distributed tracing service
- Prometheus metrics exporter
"""

from dishka import Provider, Scope, provide

from app.infrastructure.telemetry.api_telemetry import APITelemetry, TelemetryConfig
from app.infrastructure.telemetry.metrics_exporter import MetricsExporter
from app.infrastructure.telemetry.tracing import TracingService
from app.infrastructure.telemetry.llm_telemetry import LLMTelemetry, LLMTelemetryConfig
from app.infrastructure.telemetry.db_telemetry import (
    DatabaseTelemetry,
    DbTelemetryConfig,
)
from app.infrastructure.telemetry.feature_flags import (
    TelemetryFeatureFlags,
    get_feature_flags,
    load_feature_flags_from_env,
)


class TelemetryProvider(Provider):
    """Provider for telemetry infrastructure."""

    scope = Scope.APP

    @provide
    def provide_feature_flags(self) -> TelemetryFeatureFlags:
        """Provide telemetry feature flags."""
        return get_feature_flags()

    @provide
    def provide_telemetry_config(self) -> TelemetryConfig:
        """Provide telemetry configuration."""
        return TelemetryConfig(
            enabled=True,
            async_recording=True,
            retention_hours=24,
            max_records=100000,
            error_rate_threshold=0.05,
            latency_threshold_ms=5000,
            rate_limit_alert_count=3,
        )

    @provide
    def provide_api_telemetry(self, config: TelemetryConfig) -> APITelemetry:
        """Provide API telemetry service."""
        return APITelemetry(config=config)

    @provide
    def provide_tracing_service(self) -> TracingService:
        """Provide distributed tracing service."""
        return TracingService(
            service_name="anvil-backend",
            enabled=True,
            sample_rate=1.0,
            max_spans=10000,
        )

    @provide
    def provide_metrics_exporter(self, telemetry: APITelemetry) -> MetricsExporter:
        """Provide Prometheus metrics exporter."""
        return MetricsExporter(telemetry=telemetry)

    # LLM Telemetry

    @provide
    def provide_llm_telemetry_config(self) -> LLMTelemetryConfig:
        """Provide LLM telemetry configuration."""
        return LLMTelemetryConfig(
            enabled=True,
            async_recording=True,
            retention_hours=24,
            max_records=100000,
            enable_cost_tracking=True,
            monthly_budget_usd=1000.0,
            budget_alert_threshold=0.8,
            error_rate_threshold=0.05,
            latency_threshold_ms=30000,
            rate_limit_alert_count=3,
        )

    @provide
    def provide_llm_telemetry(self, config: LLMTelemetryConfig) -> LLMTelemetry:
        """Provide LLM telemetry service."""
        return LLMTelemetry(config=config)

    # Database Telemetry

    @provide
    def provide_db_telemetry_config(self) -> DbTelemetryConfig:
        """Provide database telemetry configuration."""
        return DbTelemetryConfig(
            enabled=True,
            slow_query_threshold_ms=100.0,
            very_slow_query_threshold_ms=1000.0,
            max_query_records=10000,
            retention_hours=24,
            track_query_patterns=True,
            track_connection_pool=True,
            log_slow_queries=True,
            log_errors=True,
        )

    @provide
    def provide_db_telemetry(self, config: DbTelemetryConfig) -> DatabaseTelemetry:
        """Provide database telemetry service."""
        return DatabaseTelemetry(config=config)
