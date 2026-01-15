"""CloudWatch custom metrics for guest chat system.

This module provides CloudWatch metrics collection for monitoring
guest chat performance, cache efficiency, and error rates.

Metrics Namespace: AnvilBackend/GuestChat

Features:
- Response time tracking by intent
- Cache hit/miss tracking
- Error rate monitoring
- Hunter AI performance metrics
- Rate limiting violation tracking
"""
import logging
from datetime import datetime, UTC
from typing import Any, Dict, Optional

import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)


class CloudWatchMetrics:
    """CloudWatch custom metrics client for guest chat."""

    NAMESPACE = "AnvilBackend/GuestChat"

    def __init__(self, region: str = "us-east-1", enabled: bool = True):
        """Initialize CloudWatch metrics client.

        Args:
            region: AWS region
            enabled: Whether metrics are enabled (disable for local development)
        """
        self.enabled = enabled
        self.region = region

        if self.enabled:
            try:
                self.client = boto3.client("cloudwatch", region_name=region)
                logger.info(f"CloudWatch metrics initialized (region: {region})")
            except Exception as e:
                logger.warning(
                    f"Failed to initialize CloudWatch client: {e}. "
                    "Metrics will be disabled."
                )
                self.enabled = False
        else:
            logger.info("CloudWatch metrics disabled")

    def put_metric(
        self,
        metric_name: str,
        value: float,
        unit: str = "None",
        dimensions: Optional[Dict[str, str]] = None,
    ) -> None:
        """Send a custom metric to CloudWatch.

        Args:
            metric_name: Name of the metric
            value: Metric value
            unit: CloudWatch unit (None, Milliseconds, Count, Percent, etc.)
            dimensions: Additional dimensions for the metric
        """
        if not self.enabled:
            return

        try:
            metric_data = {
                "MetricName": metric_name,
                "Value": value,
                "Unit": unit,
                "Timestamp": datetime.now(UTC),
            }

            if dimensions:
                metric_data["Dimensions"] = [
                    {"Name": k, "Value": v} for k, v in dimensions.items()
                ]

            self.client.put_metric_data(
                Namespace=self.NAMESPACE, MetricData=[metric_data]
            )

            logger.debug(
                f"CloudWatch metric sent: {metric_name}={value} {unit} "
                f"(dimensions: {dimensions})"
            )

        except ClientError as e:
            logger.error(f"Failed to send CloudWatch metric: {e}")
        except Exception as e:
            logger.error(f"Unexpected error sending metric: {e}")

    # Response Time Metrics

    def track_response_time(
        self, intent: str, duration_ms: float, cached: bool = False
    ) -> None:
        """Track response time by intent.

        Args:
            intent: Hunter AI intent (sentiment, trading_signals, etc.)
            duration_ms: Response time in milliseconds
            cached: Whether the response was cached
        """
        dimensions = {"Intent": intent, "Cached": str(cached)}

        self.put_metric(
            "ResponseTime", duration_ms, "Milliseconds", dimensions
        )

        # Also track overall response time
        self.put_metric("ResponseTimeOverall", duration_ms, "Milliseconds")

    # Cache Performance Metrics

    def track_cache_hit(self, intent: str, token: str, hit: bool) -> None:
        """Track cache hit/miss.

        Args:
            intent: Hunter AI intent
            token: Cryptocurrency token
            hit: True if cache hit, False if miss
        """
        dimensions = {"Intent": intent, "Token": token}

        # Track as 1.0 for hit, 0.0 for miss (so we can calculate %)
        self.put_metric("CacheHit", 1.0 if hit else 0.0, "None", dimensions)

        # Track overall cache performance
        self.put_metric("CacheHitOverall", 1.0 if hit else 0.0, "None")

    def track_cache_error(self, operation: str, error_type: str) -> None:
        """Track cache errors.

        Args:
            operation: Cache operation (get, set, delete)
            error_type: Type of error
        """
        dimensions = {"Operation": operation, "ErrorType": error_type}

        self.put_metric("CacheErrors", 1.0, "Count", dimensions)

    # Error Metrics

    def track_error(
        self, error_type: str, intent: Optional[str] = None
    ) -> None:
        """Track application errors.

        Args:
            error_type: Type/category of error
            intent: Optional Hunter AI intent
        """
        dimensions: Dict[str, str] = {"ErrorType": error_type}
        if intent:
            dimensions["Intent"] = intent

        self.put_metric("Errors", 1.0, "Count", dimensions)

        # Track overall error count
        self.put_metric("ErrorsOverall", 1.0, "Count")

    def track_hunter_ai_error(
        self, intent: str, error_type: str, token: str
    ) -> None:
        """Track Hunter AI specific errors.

        Args:
            intent: Hunter AI intent
            error_type: Type of error
            token: Cryptocurrency token
        """
        dimensions = {
            "Intent": intent,
            "ErrorType": error_type,
            "Token": token,
        }

        self.put_metric("HunterAIErrors", 1.0, "Count", dimensions)

    def track_external_api_error(
        self, service: str, endpoint: str, response_time_ms: float
    ) -> None:
        """Track external API errors.

        Args:
            service: Service name (coingecko, rss_feed)
            endpoint: API endpoint
            response_time_ms: Response time before error
        """
        dimensions = {"Service": service, "Endpoint": endpoint}

        self.put_metric("ExternalAPIErrors", 1.0, "Count", dimensions)
        self.put_metric(
            "ExternalAPIResponseTime",
            response_time_ms,
            "Milliseconds",
            dimensions,
        )

    # Rate Limiting Metrics

    def track_rate_limit_violation(self, ip_subnet: str) -> None:
        """Track rate limit violations.

        Args:
            ip_subnet: IP subnet (e.g., "192.168.0.0/16") for anonymization
        """
        dimensions = {"IPSubnet": ip_subnet}

        self.put_metric("RateLimitViolations", 1.0, "Count", dimensions)

        # Track overall violations
        self.put_metric("RateLimitViolationsOverall", 1.0, "Count")

    def track_blocked_user(self, reason: str) -> None:
        """Track user blocks.

        Args:
            reason: Reason for blocking (rate_limit, abuse, spam)
        """
        dimensions = {"Reason": reason}

        self.put_metric("BlockedUsers", 1.0, "Count", dimensions)

    # Database Metrics

    def track_database_query(
        self, table: str, operation: str, duration_ms: float
    ) -> None:
        """Track database query performance.

        Args:
            table: Table name
            operation: SQL operation (SELECT, INSERT, UPDATE)
            duration_ms: Query duration in milliseconds
        """
        dimensions = {"Table": table, "Operation": operation}

        self.put_metric(
            "DatabaseQueryTime", duration_ms, "Milliseconds", dimensions
        )

    def track_database_connection_error(self) -> None:
        """Track database connection errors."""
        self.put_metric("DatabaseErrors", 1.0, "Count")

    # Business Metrics

    def track_conversation_created(self, language: str) -> None:
        """Track new conversation creation.

        Args:
            language: User's preferred language
        """
        dimensions = {"Language": language}

        self.put_metric("ConversationsCreated", 1.0, "Count", dimensions)

    def track_message_sent(
        self, intent: str, language: str, authenticated: bool
    ) -> None:
        """Track messages sent.

        Args:
            intent: Message intent
            language: User's language
            authenticated: Whether user is authenticated
        """
        dimensions = {
            "Intent": intent,
            "Language": language,
            "UserType": "authenticated" if authenticated else "guest",
        }

        self.put_metric("MessagesSent", 1.0, "Count", dimensions)

    # System Health Metrics

    def track_memory_usage(self, usage_mb: float) -> None:
        """Track application memory usage.

        Args:
            usage_mb: Memory usage in megabytes
        """
        self.put_metric("MemoryUsage", usage_mb, "Megabytes")

    def track_cpu_usage(self, usage_percent: float) -> None:
        """Track CPU usage.

        Args:
            usage_percent: CPU usage percentage (0-100)
        """
        self.put_metric("CPUUsage", usage_percent, "Percent")


# Global metrics instance (initialized in application startup)
_metrics: Optional[CloudWatchMetrics] = None


def init_metrics(region: str = "us-east-1", enabled: bool = True) -> None:
    """Initialize global CloudWatch metrics client.

    Args:
        region: AWS region
        enabled: Whether metrics are enabled
    """
    global _metrics
    _metrics = CloudWatchMetrics(region=region, enabled=enabled)


def get_metrics() -> CloudWatchMetrics:
    """Get the global CloudWatch metrics client.

    Returns:
        CloudWatchMetrics instance

    Raises:
        RuntimeError: If metrics not initialized
    """
    if _metrics is None:
        raise RuntimeError(
            "CloudWatch metrics not initialized. Call init_metrics() first."
        )
    return _metrics


# Convenience functions that use the global instance

def track_response_time(intent: str, duration_ms: float, cached: bool = False) -> None:
    """Track response time (uses global metrics instance)."""
    if _metrics:
        _metrics.track_response_time(intent, duration_ms, cached)


def track_cache_hit(intent: str, token: str, hit: bool) -> None:
    """Track cache hit/miss (uses global metrics instance)."""
    if _metrics:
        _metrics.track_cache_hit(intent, token, hit)


def track_hunter_ai_error(intent: str, error_type: str, token: str) -> None:
    """Track Hunter AI error (uses global metrics instance)."""
    if _metrics:
        _metrics.track_hunter_ai_error(intent, error_type, token)


def track_rate_limit_violation(ip_subnet: str) -> None:
    """Track rate limit violation (uses global metrics instance)."""
    if _metrics:
        _metrics.track_rate_limit_violation(ip_subnet)
