"""
Telemetry API Router.

Provides comprehensive observability endpoints:
- /telemetry/metrics - API telemetry metrics (JSON)
- /telemetry/prometheus - Prometheus-format metrics
- /telemetry/traces - Distributed trace listing
- /telemetry/traces/{trace_id} - Specific trace details
- /telemetry/health - System health check
- /telemetry/slow-calls - Slow API call analysis
- /telemetry/errors - Recent error analysis
- /telemetry/llm/* - LLM provider telemetry
- /telemetry/db/* - Database query telemetry
"""

from typing import Annotated, Optional

from dishka.integrations.fastapi import FromDishka, inject
from fastapi import APIRouter, Query, Security
from fastapi.responses import PlainTextResponse

from app.domain.exceptions import (
    TelemetryAccessDeniedError,
    InvalidTimeRangeError,
    MetricNotFoundError,
    TraceNotFoundError,
    TelemetryDisabledError,
)
from app.infrastructure.telemetry.api_telemetry import APITelemetry
from app.infrastructure.telemetry.metrics_exporter import MetricsExporter
from app.infrastructure.telemetry.tracing import TracingService
from app.infrastructure.telemetry.llm_telemetry import LLMTelemetry, AlertSeverity
from app.infrastructure.telemetry.db_telemetry import DatabaseTelemetry
from app.infrastructure.telemetry.feature_flags import (
    TelemetryFeatureFlags,
    get_feature_flags,
    save_flags_to_redis,
    load_flags_from_redis,
    delete_flags_from_redis,
)
from redis.asyncio import Redis
from app.presentation.http.auth.fastapi_openapi_markers import bearer_scheme

router = APIRouter(prefix="/telemetry", tags=["Telemetry"])


# ============================================================================
# FEATURE FLAGS ENDPOINTS
# ============================================================================


@router.get("/flags")
async def get_telemetry_flags() -> dict:
    """
    Get current telemetry feature flags.
    
    Returns the current state of all telemetry feature flags:
    - Global enable/disable
    - Component-level flags (API, LLM, DB, Tracing)
    - Sampling rates
    - Per-API and per-provider configurations
    
    Returns:
        Feature flags configuration dictionary
    """
    flags = get_feature_flags()
    return flags.to_dict()


@router.put("/flags")
async def update_telemetry_flags(
    authorization: Annotated[str, Security(bearer_scheme)],
    global_enabled: Annotated[Optional[bool], Query(description="Master telemetry switch")] = None,
    api_telemetry_enabled: Annotated[Optional[bool], Query(description="API telemetry")] = None,
    llm_telemetry_enabled: Annotated[Optional[bool], Query(description="LLM telemetry")] = None,
    db_telemetry_enabled: Annotated[Optional[bool], Query(description="Database telemetry")] = None,
    tracing_enabled: Annotated[Optional[bool], Query(description="Distributed tracing")] = None,
    api_sample_rate: Annotated[Optional[float], Query(description="API sampling rate (0.0-1.0)", ge=0.0, le=1.0)] = None,
    llm_sample_rate: Annotated[Optional[float], Query(description="LLM sampling rate (0.0-1.0)", ge=0.0, le=1.0)] = None,
    db_sample_rate: Annotated[Optional[float], Query(description="DB sampling rate (0.0-1.0)", ge=0.0, le=1.0)] = None,
) -> dict:
    """
    Update telemetry feature flags at runtime.
    
    Admin-only endpoint to toggle telemetry components dynamically.
    Changes take effect immediately but do not persist across restarts.
    
    Query parameters:
    - global_enabled: Master switch for all telemetry
    - api_telemetry_enabled: Toggle API telemetry
    - llm_telemetry_enabled: Toggle LLM telemetry
    - db_telemetry_enabled: Toggle database telemetry
    - tracing_enabled: Toggle distributed tracing
    - api_sample_rate: Set API sampling rate (0.0-1.0)
    - llm_sample_rate: Set LLM sampling rate (0.0-1.0)
    - db_sample_rate: Set database sampling rate (0.0-1.0)
    
    Returns:
        Updated feature flags configuration
    """
    flags = get_feature_flags()
    
    # Update flags that were provided
    if global_enabled is not None:
        flags.global_enabled = global_enabled
    if api_telemetry_enabled is not None:
        flags.api_telemetry_enabled = api_telemetry_enabled
    if llm_telemetry_enabled is not None:
        flags.llm_telemetry_enabled = llm_telemetry_enabled
    if db_telemetry_enabled is not None:
        flags.db_telemetry_enabled = db_telemetry_enabled
    if tracing_enabled is not None:
        flags.tracing_enabled = tracing_enabled
    if api_sample_rate is not None:
        flags.api_sample_rate = api_sample_rate
    if llm_sample_rate is not None:
        flags.llm_sample_rate = llm_sample_rate
    if db_sample_rate is not None:
        flags.db_sample_rate = db_sample_rate
    
    return {
        "status": "success",
        "message": "Telemetry flags updated",
        "flags": flags.to_dict(),
    }


@router.post("/flags/disable-api/{api_name}")
async def disable_api_telemetry(
    api_name: str,
    authorization: Annotated[str, Security(bearer_scheme)],
) -> dict:
    """
    Disable telemetry for a specific API.
    
    Admin-only endpoint to stop collecting telemetry for a specific API.
    
    Path parameters:
    - api_name: Name of the API to disable (e.g., "coingecko", "uniswap")
    
    Returns:
        Updated disabled APIs list
    """
    flags = get_feature_flags()
    flags.disabled_apis.add(api_name.lower())
    
    return {
        "status": "success",
        "message": f"Telemetry disabled for API: {api_name}",
        "disabled_apis": list(flags.disabled_apis),
    }


@router.post("/flags/enable-api/{api_name}")
async def enable_api_telemetry(
    api_name: str,
    authorization: Annotated[str, Security(bearer_scheme)],
) -> dict:
    """
    Re-enable telemetry for a specific API.
    
    Admin-only endpoint to resume collecting telemetry for a specific API.
    
    Path parameters:
    - api_name: Name of the API to enable (e.g., "coingecko", "uniswap")
    
    Returns:
        Updated disabled APIs list
    """
    flags = get_feature_flags()
    flags.disabled_apis.discard(api_name.lower())
    
    return {
        "status": "success",
        "message": f"Telemetry enabled for API: {api_name}",
        "disabled_apis": list(flags.disabled_apis),
    }


@router.post("/flags/disable-llm/{provider}")
async def disable_llm_telemetry(
    provider: str,
    authorization: Annotated[str, Security(bearer_scheme)],
) -> dict:
    """
    Disable telemetry for a specific LLM provider.
    
    Admin-only endpoint to stop collecting telemetry for a specific LLM provider.
    
    Path parameters:
    - provider: Name of the provider (e.g., "vertex_ai", "openai")
    
    Returns:
        Updated disabled providers list
    """
    flags = get_feature_flags()
    flags.disabled_llm_providers.add(provider.lower())
    
    return {
        "status": "success",
        "message": f"Telemetry disabled for LLM provider: {provider}",
        "disabled_llm_providers": list(flags.disabled_llm_providers),
    }


@router.post("/flags/enable-llm/{provider}")
async def enable_llm_telemetry(
    provider: str,
    authorization: Annotated[str, Security(bearer_scheme)],
) -> dict:
    """
    Re-enable telemetry for a specific LLM provider.
    
    Admin-only endpoint to resume collecting telemetry for a specific LLM provider.
    
    Path parameters:
    - provider: Name of the provider (e.g., "vertex_ai", "openai")
    
    Returns:
        Updated disabled providers list
    """
    flags = get_feature_flags()
    flags.disabled_llm_providers.discard(provider.lower())
    
    return {
        "status": "success",
        "message": f"Telemetry enabled for LLM provider: {provider}",
        "disabled_llm_providers": list(flags.disabled_llm_providers),
    }


@router.post("/flags/save")
@inject
async def save_telemetry_flags(
    authorization: Annotated[str, Security(bearer_scheme)],
    redis: FromDishka[Redis],
) -> dict:
    """
    Persist current telemetry flags to Redis.
    
    Admin-only endpoint to save current flag settings so they persist across restarts.
    
    Returns:
        Save confirmation
    """
    flags = get_feature_flags()
    success = await save_flags_to_redis(flags, redis)
    
    if success:
        return {
            "status": "success",
            "message": "Telemetry flags saved to Redis",
            "flags": flags.to_dict(),
        }
    else:
        raise TelemetryDisabledError(
            component="flags_persistence",
            reason="Failed to save to Redis",
        )


@router.post("/flags/load")
@inject
async def load_telemetry_flags(
    authorization: Annotated[str, Security(bearer_scheme)],
    redis: FromDishka[Redis],
) -> dict:
    """
    Load telemetry flags from Redis.
    
    Admin-only endpoint to reload flag settings from Redis storage.
    
    Returns:
        Load confirmation with current flags
    """
    from app.infrastructure.telemetry.feature_flags import set_feature_flags
    
    loaded_flags = await load_flags_from_redis(redis)
    
    if loaded_flags is not None:
        set_feature_flags(loaded_flags)
        return {
            "status": "success",
            "message": "Telemetry flags loaded from Redis",
            "flags": loaded_flags.to_dict(),
        }
    else:
        return {
            "status": "warning",
            "message": "No saved flags found in Redis, using current settings",
            "flags": get_feature_flags().to_dict(),
        }


@router.delete("/flags/saved")
@inject
async def delete_saved_telemetry_flags(
    authorization: Annotated[str, Security(bearer_scheme)],
    redis: FromDishka[Redis],
) -> dict:
    """
    Delete persisted telemetry flags from Redis.
    
    Admin-only endpoint to remove saved flags. After deletion, system will
    fall back to environment-based flags on next restart.
    
    Returns:
        Delete confirmation
    """
    success = await delete_flags_from_redis(redis)
    
    if success:
        return {
            "status": "success",
            "message": "Saved telemetry flags deleted from Redis",
        }
    else:
        raise TelemetryDisabledError(
            component="flags_persistence",
            reason="Failed to delete from Redis",
        )


# ============================================================================
# API METRICS ENDPOINTS
# ============================================================================


@router.get("/metrics")
@inject
async def get_api_metrics(
    telemetry: FromDishka[APITelemetry],
    api: Annotated[Optional[str], Query(description="Filter by API name")] = None,
) -> dict:
    """
    Get API telemetry metrics.
    
    Returns comprehensive metrics including:
    - Request counts (total, successful, failed, cached)
    - Latency statistics (avg, min, max, p50, p95, p99)
    - Error rates and error breakdown
    - Rate limit events
    - Estimated API costs
    
    Query parameters:
    - api: Filter by specific API name (optional)
    
    Returns:
        JSON metrics data
    """
    if api:
        return telemetry.get_metrics(api)
    return telemetry.get_all_metrics()


@router.get("/prometheus", response_class=PlainTextResponse)
@inject
async def get_prometheus_metrics(
    exporter: FromDishka[MetricsExporter],
) -> str:
    """
    Get metrics in Prometheus/OpenMetrics format.
    
    Returns metrics suitable for scraping by Prometheus:
    - anvil_api_requests_total
    - anvil_api_request_duration_seconds
    - anvil_api_errors_total
    - anvil_api_rate_limits_total
    - anvil_api_cache_hits_total
    - anvil_api_estimated_cost_usd
    
    Returns:
        Prometheus text format metrics
    """
    return exporter.export()


@router.get("/traces")
@inject
async def get_traces(
    tracing: FromDishka[TracingService],
    limit: Annotated[int, Query(description="Maximum traces to return", ge=1, le=100)] = 20,
) -> list[dict]:
    """
    Get recent distributed traces.
    
    Returns list of recent traces with:
    - trace_id
    - root_span name
    - duration
    - status
    - span count
    
    Query parameters:
    - limit: Maximum number of traces to return (1-100, default 20)
    
    Returns:
        List of trace summaries
    """
    return tracing.get_recent_traces(limit=limit)


@router.get("/traces/{trace_id}")
@inject
async def get_trace_details(
    trace_id: str,
    tracing: FromDishka[TracingService],
) -> list[dict]:
    """
    Get detailed spans for a specific trace.
    
    Returns all spans in a trace including:
    - span_id and parent_span_id
    - span name and kind
    - timing (start, end, duration)
    - attributes
    - events
    
    Path parameters:
    - trace_id: The trace ID to retrieve
    
    Returns:
        List of spans in the trace
    """
    trace = tracing.get_trace(trace_id)
    if not trace:
        raise TraceNotFoundError(trace_id=trace_id)
    return trace


@router.get("/slow-calls")
@inject
async def get_slow_calls(
    telemetry: FromDishka[APITelemetry],
    threshold_ms: Annotated[float, Query(description="Minimum latency threshold in ms")] = 1000,
    limit: Annotated[int, Query(description="Maximum calls to return", ge=1, le=100)] = 10,
) -> list[dict]:
    """
    Get slowest API calls.
    
    Returns slow API calls sorted by duration:
    - api and operation
    - duration in ms
    - status
    - timestamp
    - request parameters
    
    Query parameters:
    - threshold_ms: Minimum latency to include (default 1000ms)
    - limit: Maximum calls to return (1-100, default 10)
    
    Returns:
        List of slow API calls
    """
    return telemetry.get_slow_calls(threshold_ms=threshold_ms, limit=limit)


@router.get("/slow-traces")
@inject
async def get_slow_traces(
    tracing: FromDishka[TracingService],
    threshold_ms: Annotated[float, Query(description="Minimum latency threshold in ms")] = 1000,
    limit: Annotated[int, Query(description="Maximum traces to return", ge=1, le=100)] = 10,
) -> list[dict]:
    """
    Get slowest traces.
    
    Returns slow traces sorted by duration:
    - trace_id
    - root_span name
    - duration in ms
    - span count
    
    Query parameters:
    - threshold_ms: Minimum latency to include (default 1000ms)
    - limit: Maximum traces to return (1-100, default 10)
    
    Returns:
        List of slow traces
    """
    return tracing.get_slow_traces(threshold_ms=threshold_ms, limit=limit)


@router.get("/errors")
@inject
async def get_errors(
    telemetry: FromDishka[APITelemetry],
    api: Annotated[Optional[str], Query(description="Filter by API name")] = None,
    limit: Annotated[int, Query(description="Maximum errors to return", ge=1, le=100)] = 20,
) -> list[dict]:
    """
    Get recent API errors.
    
    Returns recent errors including:
    - api and operation
    - status (error, timeout, rate_limited)
    - error type and message
    - timestamp
    
    Query parameters:
    - api: Filter by specific API name (optional)
    - limit: Maximum errors to return (1-100, default 20)
    
    Returns:
        List of recent errors
    """
    return telemetry.get_errors(api=api, limit=limit)


@router.get("/health")
@inject
async def get_telemetry_health(
    telemetry: FromDishka[APITelemetry],
    tracing: FromDishka[TracingService],
) -> dict:
    """
    Get telemetry system health.
    
    Returns health status of telemetry components:
    - API telemetry status
    - Tracing service status
    - Current metrics summary
    
    Returns:
        Health status dictionary
    """
    all_metrics = telemetry.get_all_metrics()
    
    return {
        "status": "healthy",
        "components": {
            "api_telemetry": {
                "status": "active",
                "apis_tracked": all_metrics["summary"]["apis_tracked"],
                "total_requests": all_metrics["summary"]["total_requests"],
            },
            "tracing": {
                "status": "active",
                "recent_traces": len(tracing.get_recent_traces(limit=10)),
            },
        },
        "summary": all_metrics["summary"],
    }


@router.post("/reset")
@inject
async def reset_telemetry(
    authorization: Annotated[str, Security(bearer_scheme)],
    telemetry: FromDishka[APITelemetry],
    api: Annotated[Optional[str], Query(description="API to reset (all if not specified)")] = None,
) -> dict:
    """
    Reset telemetry metrics.
    
    Admin-only endpoint to reset collected metrics.
    
    Query parameters:
    - api: Reset only specific API (optional, all if not specified)
    
    Returns:
        Reset confirmation
    """
    telemetry.reset(api)
    return {
        "status": "success",
        "message": f"Reset telemetry for {api or 'all APIs'}",
    }


# ============================================================================
# LLM TELEMETRY ENDPOINTS
# ============================================================================


@router.get("/llm/metrics")
@inject
async def get_llm_metrics(
    llm_telemetry: FromDishka[LLMTelemetry],
    provider: Annotated[Optional[str], Query(description="Filter by provider name")] = None,
) -> dict:
    """
    Get LLM provider telemetry metrics.
    
    Returns comprehensive LLM metrics including:
    - Token usage (input, output, total)
    - Cost tracking (per provider, per model)
    - Latency statistics (avg, p50, p90, p99)
    - Error rates and breakdown
    - Monthly budget tracking
    
    Query parameters:
    - provider: Filter by specific provider (optional)
    
    Returns:
        JSON LLM metrics data
    """
    if provider:
        metrics = llm_telemetry.get_provider_metrics(provider)
        if metrics:
            return metrics.to_dict()
        raise MetricNotFoundError(
            metric_name=f"provider:{provider}",
            reason="Provider not found in telemetry data",
        )
    
    return llm_telemetry.get_summary()


@router.get("/llm/costs")
@inject
async def get_llm_costs(
    llm_telemetry: FromDishka[LLMTelemetry],
) -> dict:
    """
    Get LLM cost breakdown.
    
    Returns detailed cost analysis:
    - Monthly total and budget
    - Cost by provider
    - Cost by model
    - Budget alerts status
    
    Returns:
        Cost breakdown dictionary
    """
    return llm_telemetry.get_cost_breakdown()


@router.get("/llm/models")
@inject
async def get_llm_model_usage(
    llm_telemetry: FromDishka[LLMTelemetry],
) -> dict:
    """
    Get LLM model usage statistics.
    
    Returns usage breakdown by model:
    - Call counts
    - Token usage
    - Cost per model
    - Provider distribution
    
    Returns:
        Model usage dictionary
    """
    return llm_telemetry.get_model_usage()


@router.get("/llm/alerts")
@inject
async def get_llm_alerts(
    llm_telemetry: FromDishka[LLMTelemetry],
    severity: Annotated[Optional[str], Query(description="Filter by severity: info, warning, error, critical")] = None,
    hours: Annotated[int, Query(description="Look back hours", ge=1, le=168)] = 24,
) -> list[dict]:
    """
    Get LLM telemetry alerts.
    
    Returns alerts including:
    - Budget warnings
    - Error rate spikes
    - Rate limiting events
    - High latency alerts
    
    Query parameters:
    - severity: Filter by severity level (optional)
    - hours: Look back period (default 24, max 168)
    
    Returns:
        List of alerts
    """
    # Validate hours is within bounds
    if hours < 1 or hours > 168:
        raise InvalidTimeRangeError(
            start_time="now",
            end_time=f"now-{hours}h",
            reason="Hours must be between 1 and 168",
        )
    
    sev = AlertSeverity(severity) if severity else None
    alerts = llm_telemetry.get_alerts(severity=sev, hours=hours)
    return [a.to_dict() for a in alerts]


@router.get("/llm/providers")
@inject
async def get_llm_providers(
    llm_telemetry: FromDishka[LLMTelemetry],
) -> dict:
    """
    Get list of tracked LLM providers with basic metrics.
    
    Returns for each provider:
    - Total calls
    - Success rate
    - Average latency
    - Total cost
    
    Returns:
        Provider summary dictionary
    """
    all_metrics = llm_telemetry.get_all_metrics()
    
    return {
        provider: {
            "total_calls": metrics.total_calls,
            "success_rate": round(metrics.success_rate, 4),
            "avg_latency_ms": round(metrics.avg_latency_ms, 2),
            "total_cost_usd": round(metrics.total_cost_usd, 4),
            "models_used": list(metrics.model_usage.keys()),
        }
        for provider, metrics in all_metrics.items()
    }


@router.post("/llm/reset")
@inject
async def reset_llm_telemetry(
    authorization: Annotated[str, Security(bearer_scheme)],
    llm_telemetry: FromDishka[LLMTelemetry],
) -> dict:
    """
    Reset LLM telemetry metrics.
    
    Admin-only endpoint to reset all LLM metrics and alerts.
    Note: This does NOT reset the monthly budget tracker.
    
    Returns:
        Reset confirmation
    """
    llm_telemetry.reset()
    return {
        "status": "success",
        "message": "LLM telemetry reset successfully",
    }


# ============================================================================
# DATABASE TELEMETRY ENDPOINTS
# ============================================================================


@router.get("/db/metrics")
@inject
async def get_db_metrics(
    db_telemetry: FromDishka[DatabaseTelemetry],
) -> dict:
    """
    Get database query telemetry metrics.
    
    Returns comprehensive database metrics including:
    - Total query counts (by type)
    - Success/error rates
    - Duration statistics
    - Queries by table
    - Slow query counts
    
    Returns:
        JSON database metrics
    """
    return db_telemetry.get_metrics()


@router.get("/db/slow-queries")
@inject
async def get_db_slow_queries(
    db_telemetry: FromDishka[DatabaseTelemetry],
    threshold_ms: Annotated[float, Query(description="Minimum latency threshold in ms")] = 100,
    limit: Annotated[int, Query(description="Maximum queries to return", ge=1, le=100)] = 10,
) -> list[dict]:
    """
    Get slow database queries.
    
    Returns slow queries sorted by duration:
    - Query text (truncated)
    - Query type
    - Duration in ms
    - Tables involved
    - Row count
    - Error message (if any)
    
    Query parameters:
    - threshold_ms: Minimum latency to include (default 100ms)
    - limit: Maximum queries to return (1-100, default 10)
    
    Returns:
        List of slow queries
    """
    return db_telemetry.get_slow_queries(limit=limit, threshold_ms=threshold_ms)


@router.get("/db/patterns")
@inject
async def get_db_query_patterns(
    db_telemetry: FromDishka[DatabaseTelemetry],
    order_by: Annotated[str, Query(description="Order by: execution_count, avg_duration, max_duration, error_rate")] = "execution_count",
    limit: Annotated[int, Query(description="Maximum patterns to return", ge=1, le=100)] = 20,
) -> list[dict]:
    """
    Get database query patterns.
    
    Returns aggregated statistics for normalized query patterns:
    - Normalized query template
    - Execution count
    - Average/min/max duration
    - Error rate
    - Total rows affected
    
    Query parameters:
    - order_by: Sort metric (default: execution_count)
    - limit: Maximum patterns to return (1-100, default 20)
    
    Returns:
        List of query patterns with statistics
    """
    return db_telemetry.get_query_patterns(order_by=order_by, limit=limit)


@router.get("/db/pool")
@inject
async def get_db_pool_stats(
    db_telemetry: FromDishka[DatabaseTelemetry],
) -> dict:
    """
    Get database connection pool statistics.
    
    Returns pool metrics:
    - Pool size and overflow
    - Checked out/in connections
    - Checkout/checkin counts
    - Connect/disconnect counts
    
    Returns:
        Connection pool statistics
    """
    return db_telemetry.get_pool_stats()


@router.get("/db/tables/{table}")
@inject
async def get_db_table_stats(
    table: str,
    db_telemetry: FromDishka[DatabaseTelemetry],
) -> dict:
    """
    Get query statistics for a specific table.
    
    Returns for the specified table:
    - Total query count
    - Average duration
    - Error count
    - Query type breakdown
    
    Path parameters:
    - table: Table name to get statistics for
    
    Returns:
        Table-specific query statistics
    """
    return db_telemetry.get_queries_by_table(table)


@router.get("/db/errors")
@inject
async def get_db_errors(
    db_telemetry: FromDishka[DatabaseTelemetry],
    limit: Annotated[int, Query(description="Maximum errors to return", ge=1, le=100)] = 20,
) -> list[dict]:
    """
    Get recent database query errors.
    
    Returns recent errors including:
    - Query text
    - Error type (error, timeout, deadlock)
    - Error message
    - Duration
    - Timestamp
    
    Query parameters:
    - limit: Maximum errors to return (1-100, default 20)
    
    Returns:
        List of recent query errors
    """
    return db_telemetry.get_recent_errors(limit=limit)


@router.get("/db/summary")
@inject
async def get_db_summary(
    db_telemetry: FromDishka[DatabaseTelemetry],
) -> dict:
    """
    Get comprehensive database telemetry summary.
    
    Returns combined metrics:
    - Overall metrics
    - Connection pool stats
    - Top query patterns
    - Slow query count
    
    Returns:
        Comprehensive summary dictionary
    """
    return db_telemetry.get_summary()


@router.post("/db/reset")
@inject
async def reset_db_telemetry(
    authorization: Annotated[str, Security(bearer_scheme)],
    db_telemetry: FromDishka[DatabaseTelemetry],
) -> dict:
    """
    Reset database telemetry metrics.
    
    Admin-only endpoint to reset all database metrics and patterns.
    
    Returns:
        Reset confirmation
    """
    db_telemetry.reset()
    return {
        "status": "success",
        "message": "Database telemetry reset successfully",
    }
