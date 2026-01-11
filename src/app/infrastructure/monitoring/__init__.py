"""Infrastructure monitoring module.

Provides error tracking (Sentry) and metrics collection (CloudWatch)
for the guest chat system and overall application.
"""
from .sentry_config import (
    SentryConfig,
    GuestChatMonitoring,
)
from .cloudwatch_metrics import (
    CloudWatchMetrics,
    init_metrics,
    get_metrics,
    track_response_time,
    track_cache_hit,
    track_hunter_ai_error,
    track_rate_limit_violation,
)

__all__ = [
    # Sentry
    "SentryConfig",
    "GuestChatMonitoring",
    # CloudWatch
    "CloudWatchMetrics",
    "init_metrics",
    "get_metrics",
    "track_response_time",
    "track_cache_hit",
    "track_hunter_ai_error",
    "track_rate_limit_violation",
]
