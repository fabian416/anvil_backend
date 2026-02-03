"""Sentry error tracking configuration for guest chat system.

This module provides comprehensive error tracking and performance monitoring
for the guest chat system using Sentry.

Features:
- Automatic error capture with context
- Performance monitoring (traces)
- Custom error filtering
- Hunter AI error tracking
- Cache error tracking
- Rate limiting violation tracking
"""

import logging
from typing import Any, Optional

import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
from sentry_sdk.integrations.redis import RedisIntegration
from sentry_sdk.integrations.celery import CeleryIntegration
from sentry_sdk.integrations.logging import LoggingIntegration

logger = logging.getLogger(__name__)


class SentryConfig:
    """Sentry configuration and initialization."""

    @staticmethod
    def init_sentry(
        dsn: str,
        environment: str,
        version: str = "1.0.0",
        traces_sample_rate: float = 0.1,
        profiles_sample_rate: float = 0.1,
    ) -> None:
        """Initialize Sentry error tracking.

        Args:
            dsn: Sentry DSN from project settings
            environment: Environment name (local, dev, staging, production)
            version: Application version/release
            traces_sample_rate: Percentage of traces to sample (0.0-1.0)
            profiles_sample_rate: Percentage of profiles to sample (0.0-1.0)
        """
        if not dsn:
            logger.warning("Sentry DSN not configured, error tracking disabled")
            return

        try:
            sentry_sdk.init(
                dsn=dsn,
                environment=environment,
                release=f"anvil-backend@{version}",
                # Integrations
                integrations=[
                    FastApiIntegration(transaction_style="endpoint"),
                    SqlalchemyIntegration(),
                    RedisIntegration(),
                    CeleryIntegration(),
                    LoggingIntegration(
                        level=logging.INFO,  # Capture info and above
                        event_level=logging.ERROR,  # Send errors to Sentry
                    ),
                ],
                # Performance monitoring
                traces_sample_rate=traces_sample_rate,
                profiles_sample_rate=profiles_sample_rate,
                # Error filtering
                before_send=SentryConfig._before_send_filter,
                # Request data
                send_default_pii=False,  # Don't send PII by default
                # Tags
                tags={
                    "service": "guest-chat",
                    "component": "api",
                },
            )

            logger.info(
                f"Sentry initialized for environment: {environment}, "
                f"traces_sample_rate: {traces_sample_rate}"
            )

        except Exception as e:
            logger.error(f"Failed to initialize Sentry: {e}")

    @staticmethod
    def _before_send_filter(event: dict, hint: dict) -> Optional[dict]:
        """Filter events before sending to Sentry.

        Args:
            event: Sentry event dict
            hint: Additional context about the event

        Returns:
            Modified event dict or None to drop the event
        """
        # Ignore rate limiting errors (expected behavior)
        if "exc_info" in hint:
            exc_type, exc_value, tb = hint["exc_info"]
            if exc_type.__name__ in ("RateLimitExceeded", "TooManyRequests"):
                return None

            # Ignore common client errors (4xx)
            if exc_type.__name__ in ("ValidationError", "HTTPException"):
                # Only track 4xx errors if they're unexpected
                status_code = getattr(exc_value, "status_code", None)
                if status_code and 400 <= status_code < 500:
                    return None

        # Add custom context
        event.setdefault("tags", {})
        event["tags"]["guest_system"] = "true"

        return event


class GuestChatMonitoring:
    """Guest chat specific monitoring utilities."""

    @staticmethod
    def set_guest_context(
        ip_address: str,
        conversation_id: Optional[str] = None,
        language: str = "en",
    ) -> None:
        """Set guest-specific context for error tracking.

        Args:
            ip_address: Guest user IP address (anonymized)
            conversation_id: Optional conversation ID
            language: User's preferred language
        """
        with sentry_sdk.configure_scope() as scope:
            # Anonymize IP (keep first 2 octets only)
            parts = ip_address.split(".")
            anonymized_ip = f"{parts[0]}.{parts[1]}.***" if len(parts) >= 2 else "***"

            scope.set_user({"ip_address": anonymized_ip})
            scope.set_tag("user_type", "guest")
            scope.set_tag("language", language)

            if conversation_id:
                scope.set_context(
                    "conversation",
                    {"id": conversation_id, "type": "guest_conversation"},
                )

    @staticmethod
    def capture_hunter_error(
        intent: str,
        token: str,
        error: Exception,
        language: str = "en",
        **extra_context: Any,
    ) -> None:
        """Capture Hunter AI errors with rich context.

        Args:
            intent: Hunter AI intent (sentiment, trading_signals, etc.)
            token: Cryptocurrency token (BTC, ETH, etc.)
            error: Exception that occurred
            language: User's language
            **extra_context: Additional context to include
        """
        with sentry_sdk.push_scope() as scope:
            scope.set_tag("hunter_intent", intent)
            scope.set_tag("token", token)
            scope.set_tag("language", language)
            scope.set_tag("error_source", "hunter_ai")

            scope.set_context(
                "hunter_ai",
                {
                    "intent": intent,
                    "token": token,
                    "language": language,
                    **extra_context,
                },
            )

            sentry_sdk.capture_exception(error)
            logger.error(
                f"Hunter AI error captured: {intent}/{token} - {error}",
                extra={"hunter_context": extra_context},
            )

    @staticmethod
    def capture_cache_error(operation: str, key: str, error: Exception) -> None:
        """Capture Redis cache errors.

        Args:
            operation: Cache operation (get, set, delete, etc.)
            key: Cache key that failed
            error: Exception that occurred
        """
        with sentry_sdk.push_scope() as scope:
            scope.set_tag("cache_operation", operation)
            scope.set_tag("error_source", "redis_cache")

            # Don't include full key (may contain sensitive data)
            key_pattern = key.split(":")[0] if ":" in key else "unknown"
            scope.set_tag("cache_key_pattern", key_pattern)

            scope.set_context(
                "cache",
                {"operation": operation, "key_pattern": key_pattern},
            )

            sentry_sdk.capture_exception(error)
            logger.error(
                f"Cache error captured: {operation} on {key_pattern} - {error}"
            )

    @staticmethod
    def capture_rate_limit_violation(
        ip_address: str, message_count: int, limit: int
    ) -> None:
        """Capture rate limit violations for analysis.

        Args:
            ip_address: IP address that exceeded limit
            message_count: Number of messages sent
            limit: Rate limit threshold
        """
        # Anonymize IP
        parts = ip_address.split(".")
        anonymized_ip = f"{parts[0]}.{parts[1]}.***" if len(parts) >= 2 else "***"

        with sentry_sdk.push_scope() as scope:
            scope.set_tag("violation_type", "rate_limit")
            scope.set_tag(
                "ip_subnet",
                f"{parts[0]}.{parts[1]}.0.0/16" if len(parts) >= 2 else "unknown",
            )

            scope.set_context(
                "rate_limit",
                {
                    "ip": anonymized_ip,
                    "message_count": message_count,
                    "limit": limit,
                    "exceeded_by": message_count - limit,
                },
            )

            sentry_sdk.capture_message(
                f"Rate limit exceeded: {anonymized_ip} ({message_count}/{limit})",
                level="warning",
            )

    @staticmethod
    def capture_external_api_error(
        service: str, endpoint: str, error: Exception, response_time_ms: float
    ) -> None:
        """Capture external API errors (CoinGecko, RSS feeds, etc.).

        Args:
            service: Service name (coingecko, rss_feed, etc.)
            endpoint: API endpoint that failed
            error: Exception that occurred
            response_time_ms: Response time before failure
        """
        with sentry_sdk.push_scope() as scope:
            scope.set_tag("external_service", service)
            scope.set_tag("error_source", "external_api")

            scope.set_context(
                "external_api",
                {
                    "service": service,
                    "endpoint": endpoint,
                    "response_time_ms": response_time_ms,
                },
            )

            sentry_sdk.capture_exception(error)
            logger.error(f"External API error: {service} - {endpoint} - {error}")

    @staticmethod
    def start_transaction(name: str, op: str) -> Any:
        """Start a performance monitoring transaction.

        Args:
            name: Transaction name
            op: Operation type (http.server, db.query, etc.)

        Returns:
            Transaction context manager

        Example:
            with start_transaction("guest_chat", "http.server"):
                # ... perform operations ...
                pass
        """
        return sentry_sdk.start_transaction(name=name, op=op)

    @staticmethod
    def capture_message(message: str, level: str = "info", **extra: Any) -> None:
        """Capture a custom message with context.

        Args:
            message: Message to capture
            level: Severity level (debug, info, warning, error, fatal)
            **extra: Additional context
        """
        with sentry_sdk.push_scope() as scope:
            for key, value in extra.items():
                scope.set_context(key, value)

            sentry_sdk.capture_message(message, level=level)
