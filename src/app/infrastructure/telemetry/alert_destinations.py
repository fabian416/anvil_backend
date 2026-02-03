"""
Alert Destinations for Telemetry.

Provides configurable alert destinations:
- Email notifications via Mailgun
- Slack webhooks
- PagerDuty integration
- Console logging (default)

Usage:
    from app.infrastructure.telemetry.alert_destinations import (
        AlertDispatcher,
        EmailAlertDestination,
        SlackAlertDestination,
    )

    dispatcher = AlertDispatcher()
    dispatcher.add_destination(EmailAlertDestination(config))
    dispatcher.add_destination(SlackAlertDestination(webhook_url))

    await dispatcher.send_alert(alert)
"""

import asyncio
import logging
import os
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional

import httpx

logger = logging.getLogger(__name__)


# ============================================================================
# CONFIGURATION
# ============================================================================


@dataclass
class AlertDestinationConfig:
    """Configuration for alert destinations."""

    # Email config
    email_enabled: bool = False
    email_recipients: list[str] = field(default_factory=list)
    mailgun_domain: str = ""
    mailgun_api_key: str = ""
    email_from: str = "alerts@anvil.defi"

    # Slack config
    slack_enabled: bool = False
    slack_webhook_url: str = ""
    slack_channel: str = "#alerts"

    # PagerDuty config
    pagerduty_enabled: bool = False
    pagerduty_routing_key: str = ""

    # General
    min_severity_for_email: str = "warning"  # info, warning, error, critical
    min_severity_for_slack: str = "warning"
    min_severity_for_pagerduty: str = "error"

    @classmethod
    def from_env(cls) -> "AlertDestinationConfig":
        """Load configuration from environment variables."""
        return cls(
            # Email
            email_enabled=os.getenv("TELEMETRY_ALERT_EMAIL_ENABLED", "false").lower()
            == "true",
            email_recipients=[
                r.strip()
                for r in os.getenv("TELEMETRY_ALERT_EMAIL_RECIPIENTS", "").split(",")
                if r.strip()
            ],
            mailgun_domain=os.getenv("MAILGUN_DOMAIN", ""),
            mailgun_api_key=os.getenv("MAILGUN_API_KEY", ""),
            email_from=os.getenv("TELEMETRY_ALERT_EMAIL_FROM", "alerts@anvil.defi"),
            # Slack
            slack_enabled=os.getenv("TELEMETRY_ALERT_SLACK_ENABLED", "false").lower()
            == "true",
            slack_webhook_url=os.getenv("TELEMETRY_ALERT_SLACK_WEBHOOK_URL", ""),
            slack_channel=os.getenv("TELEMETRY_ALERT_SLACK_CHANNEL", "#alerts"),
            # PagerDuty
            pagerduty_enabled=os.getenv(
                "TELEMETRY_ALERT_PAGERDUTY_ENABLED", "false"
            ).lower()
            == "true",
            pagerduty_routing_key=os.getenv(
                "TELEMETRY_ALERT_PAGERDUTY_ROUTING_KEY", ""
            ),
            # Severity thresholds
            min_severity_for_email=os.getenv(
                "TELEMETRY_ALERT_MIN_EMAIL_SEVERITY", "warning"
            ),
            min_severity_for_slack=os.getenv(
                "TELEMETRY_ALERT_MIN_SLACK_SEVERITY", "warning"
            ),
            min_severity_for_pagerduty=os.getenv(
                "TELEMETRY_ALERT_MIN_PAGERDUTY_SEVERITY", "error"
            ),
        )


@dataclass
class TelemetryAlert:
    """Alert data structure."""

    alert_id: str
    severity: str  # info, warning, error, critical
    title: str
    message: str
    source: str  # api, llm, db, system
    timestamp: datetime
    details: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "alert_id": self.alert_id,
            "severity": self.severity,
            "title": self.title,
            "message": self.message,
            "source": self.source,
            "timestamp": self.timestamp.isoformat(),
            "details": self.details,
        }


# ============================================================================
# SEVERITY LEVELS
# ============================================================================


SEVERITY_ORDER = ["info", "warning", "error", "critical"]


def severity_meets_threshold(severity: str, threshold: str) -> bool:
    """Check if severity meets or exceeds threshold."""
    try:
        sev_idx = SEVERITY_ORDER.index(severity.lower())
        thresh_idx = SEVERITY_ORDER.index(threshold.lower())
        return sev_idx >= thresh_idx
    except ValueError:
        return True  # Default to sending if unknown severity


# ============================================================================
# ALERT DESTINATIONS
# ============================================================================


class AlertDestination(ABC):
    """Abstract base class for alert destinations."""

    @abstractmethod
    async def send(self, alert: TelemetryAlert) -> bool:
        """Send an alert to this destination."""
        ...

    @abstractmethod
    def should_send(self, alert: TelemetryAlert) -> bool:
        """Check if this alert should be sent to this destination."""
        ...


class ConsoleAlertDestination(AlertDestination):
    """Log alerts to console (default)."""

    def __init__(self, min_severity: str = "info"):
        self.min_severity = min_severity

    def should_send(self, alert: TelemetryAlert) -> bool:
        return severity_meets_threshold(alert.severity, self.min_severity)

    async def send(self, alert: TelemetryAlert) -> bool:
        log_method = {
            "info": logger.info,
            "warning": logger.warning,
            "error": logger.error,
            "critical": logger.critical,
        }.get(alert.severity.lower(), logger.warning)

        log_method(f"[ALERT][{alert.source.upper()}] {alert.title}: {alert.message}")
        return True


class EmailAlertDestination(AlertDestination):
    """Send alerts via email using Mailgun."""

    def __init__(
        self,
        recipients: list[str],
        mailgun_domain: str,
        mailgun_api_key: str,
        email_from: str = "alerts@anvil.defi",
        min_severity: str = "warning",
    ):
        self.recipients = recipients
        self.mailgun_domain = mailgun_domain
        self.mailgun_api_key = mailgun_api_key
        self.email_from = email_from
        self.min_severity = min_severity

    def should_send(self, alert: TelemetryAlert) -> bool:
        if not self.recipients or not self.mailgun_api_key:
            return False
        return severity_meets_threshold(alert.severity, self.min_severity)

    async def send(self, alert: TelemetryAlert) -> bool:
        if not self.recipients:
            return False

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"https://api.mailgun.net/v3/{self.mailgun_domain}/messages",
                    auth=("api", self.mailgun_api_key),
                    data={
                        "from": f"Anvil Alerts <{self.email_from}>",
                        "to": self.recipients,
                        "subject": f"[{alert.severity.upper()}] {alert.title}",
                        "text": self._format_text(alert),
                        "html": self._format_html(alert),
                    },
                    timeout=10.0,
                )

                if response.status_code == 200:
                    logger.info(
                        f"Email alert sent to {len(self.recipients)} recipients"
                    )
                    return True
                else:
                    logger.error(f"Failed to send email alert: {response.status_code}")
                    return False

        except Exception as e:
            logger.error(f"Error sending email alert: {e}")
            return False

    def _format_text(self, alert: TelemetryAlert) -> str:
        lines = [
            f"ANVIL TELEMETRY ALERT",
            f"=====================",
            f"",
            f"Severity: {alert.severity.upper()}",
            f"Source: {alert.source}",
            f"Time: {alert.timestamp.isoformat()}",
            f"",
            f"Title: {alert.title}",
            f"",
            f"Message:",
            alert.message,
            f"",
            f"Details:",
        ]

        for key, value in alert.details.items():
            lines.append(f"  {key}: {value}")

        return "\n".join(lines)

    def _format_html(self, alert: TelemetryAlert) -> str:
        severity_colors = {
            "info": "#17a2b8",
            "warning": "#ffc107",
            "error": "#dc3545",
            "critical": "#721c24",
        }
        color = severity_colors.get(alert.severity.lower(), "#6c757d")

        details_html = "".join(
            f"<tr><td><strong>{k}</strong></td><td>{v}</td></tr>"
            for k, v in alert.details.items()
        )

        return f"""
        <html>
        <body style="font-family: Arial, sans-serif; padding: 20px;">
            <div style="background-color: {color}; color: white; padding: 15px; border-radius: 5px;">
                <h2 style="margin: 0;">[{alert.severity.upper()}] {alert.title}</h2>
            </div>
            <div style="padding: 20px; background-color: #f8f9fa; border-radius: 5px; margin-top: 10px;">
                <p><strong>Source:</strong> {alert.source}</p>
                <p><strong>Time:</strong> {alert.timestamp.isoformat()}</p>
                <p><strong>Message:</strong></p>
                <p style="padding: 10px; background-color: white; border-radius: 3px;">{alert.message}</p>
                
                <h4>Details:</h4>
                <table style="width: 100%; border-collapse: collapse;">
                    {details_html}
                </table>
            </div>
        </body>
        </html>
        """


class SlackAlertDestination(AlertDestination):
    """Send alerts to Slack via webhook."""

    def __init__(
        self,
        webhook_url: str,
        channel: str = "#alerts",
        min_severity: str = "warning",
    ):
        self.webhook_url = webhook_url
        self.channel = channel
        self.min_severity = min_severity

    def should_send(self, alert: TelemetryAlert) -> bool:
        if not self.webhook_url:
            return False
        return severity_meets_threshold(alert.severity, self.min_severity)

    async def send(self, alert: TelemetryAlert) -> bool:
        if not self.webhook_url:
            return False

        try:
            severity_emoji = {
                "info": ":information_source:",
                "warning": ":warning:",
                "error": ":x:",
                "critical": ":rotating_light:",
            }
            emoji = severity_emoji.get(alert.severity.lower(), ":bell:")

            blocks = [
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": f"{emoji} {alert.title}",
                    },
                },
                {
                    "type": "section",
                    "fields": [
                        {
                            "type": "mrkdwn",
                            "text": f"*Severity:*\n{alert.severity.upper()}",
                        },
                        {"type": "mrkdwn", "text": f"*Source:*\n{alert.source}"},
                        {
                            "type": "mrkdwn",
                            "text": f"*Time:*\n{alert.timestamp.strftime('%Y-%m-%d %H:%M:%S')}",
                        },
                    ],
                },
                {
                    "type": "section",
                    "text": {"type": "mrkdwn", "text": f"*Message:*\n{alert.message}"},
                },
            ]

            # Add details as fields
            if alert.details:
                detail_fields = [
                    {"type": "mrkdwn", "text": f"*{k}:*\n{v}"}
                    for k, v in list(alert.details.items())[:10]  # Max 10 fields
                ]
                blocks.append({
                    "type": "section",
                    "fields": detail_fields[:10],
                })

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.webhook_url,
                    json={
                        "channel": self.channel,
                        "blocks": blocks,
                    },
                    timeout=10.0,
                )

                if response.status_code == 200:
                    logger.info("Slack alert sent successfully")
                    return True
                else:
                    logger.error(f"Failed to send Slack alert: {response.status_code}")
                    return False

        except Exception as e:
            logger.error(f"Error sending Slack alert: {e}")
            return False


class PagerDutyAlertDestination(AlertDestination):
    """Send alerts to PagerDuty."""

    def __init__(
        self,
        routing_key: str,
        min_severity: str = "error",
    ):
        self.routing_key = routing_key
        self.min_severity = min_severity

    def should_send(self, alert: TelemetryAlert) -> bool:
        if not self.routing_key:
            return False
        return severity_meets_threshold(alert.severity, self.min_severity)

    async def send(self, alert: TelemetryAlert) -> bool:
        if not self.routing_key:
            return False

        try:
            severity_map = {
                "info": "info",
                "warning": "warning",
                "error": "error",
                "critical": "critical",
            }
            pd_severity = severity_map.get(alert.severity.lower(), "warning")

            payload = {
                "routing_key": self.routing_key,
                "event_action": "trigger",
                "dedup_key": alert.alert_id,
                "payload": {
                    "summary": f"[{alert.source.upper()}] {alert.title}",
                    "severity": pd_severity,
                    "source": "anvil-backend",
                    "timestamp": alert.timestamp.isoformat(),
                    "custom_details": {
                        "message": alert.message,
                        **alert.details,
                    },
                },
            }

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://events.pagerduty.com/v2/enqueue",
                    json=payload,
                    timeout=10.0,
                )

                if response.status_code in (200, 202):
                    logger.info("PagerDuty alert sent successfully")
                    return True
                else:
                    logger.error(
                        f"Failed to send PagerDuty alert: {response.status_code}"
                    )
                    return False

        except Exception as e:
            logger.error(f"Error sending PagerDuty alert: {e}")
            return False


# ============================================================================
# ALERT DISPATCHER
# ============================================================================


class AlertDispatcher:
    """
    Dispatches alerts to multiple destinations.

    Supports:
    - Multiple simultaneous destinations
    - Severity filtering per destination
    - Async delivery
    - Failure handling
    """

    def __init__(self, config: Optional[AlertDestinationConfig] = None):
        self.config = config or AlertDestinationConfig.from_env()
        self._destinations: list[AlertDestination] = []

        # Always add console
        self._destinations.append(ConsoleAlertDestination())

        # Add configured destinations
        self._setup_destinations()

    def _setup_destinations(self) -> None:
        """Setup destinations based on config."""
        # Email
        if self.config.email_enabled and self.config.email_recipients:
            self._destinations.append(
                EmailAlertDestination(
                    recipients=self.config.email_recipients,
                    mailgun_domain=self.config.mailgun_domain,
                    mailgun_api_key=self.config.mailgun_api_key,
                    email_from=self.config.email_from,
                    min_severity=self.config.min_severity_for_email,
                )
            )
            logger.info(
                f"Email alerts enabled for {len(self.config.email_recipients)} recipients"
            )

        # Slack
        if self.config.slack_enabled and self.config.slack_webhook_url:
            self._destinations.append(
                SlackAlertDestination(
                    webhook_url=self.config.slack_webhook_url,
                    channel=self.config.slack_channel,
                    min_severity=self.config.min_severity_for_slack,
                )
            )
            logger.info("Slack alerts enabled")

        # PagerDuty
        if self.config.pagerduty_enabled and self.config.pagerduty_routing_key:
            self._destinations.append(
                PagerDutyAlertDestination(
                    routing_key=self.config.pagerduty_routing_key,
                    min_severity=self.config.min_severity_for_pagerduty,
                )
            )
            logger.info("PagerDuty alerts enabled")

    def add_destination(self, destination: AlertDestination) -> None:
        """Add a custom alert destination."""
        self._destinations.append(destination)

    async def send_alert(self, alert: TelemetryAlert) -> dict[str, bool]:
        """
        Send alert to all configured destinations.

        Args:
            alert: The alert to send

        Returns:
            Dictionary of destination name -> success status
        """
        results = {}

        tasks = []
        for dest in self._destinations:
            if dest.should_send(alert):
                tasks.append((type(dest).__name__, dest.send(alert)))

        if not tasks:
            return results

        # Execute all sends concurrently
        task_results = await asyncio.gather(
            *[t[1] for t in tasks],
            return_exceptions=True,
        )

        for (dest_name, _), result in zip(tasks, task_results):
            if isinstance(result, Exception):
                logger.error(f"Alert destination {dest_name} failed: {result}")
                results[dest_name] = False
            else:
                results[dest_name] = result

        return results

    @property
    def destination_count(self) -> int:
        """Number of configured destinations."""
        return len(self._destinations)

    def get_config_summary(self) -> dict[str, Any]:
        """Get summary of alert configuration."""
        return {
            "email_enabled": self.config.email_enabled,
            "email_recipients_count": len(self.config.email_recipients),
            "slack_enabled": self.config.slack_enabled,
            "pagerduty_enabled": self.config.pagerduty_enabled,
            "total_destinations": self.destination_count,
        }


# ============================================================================
# SINGLETON
# ============================================================================


_dispatcher: Optional[AlertDispatcher] = None


def get_alert_dispatcher() -> AlertDispatcher:
    """Get the global alert dispatcher instance."""
    global _dispatcher
    if _dispatcher is None:
        _dispatcher = AlertDispatcher()
    return _dispatcher


def set_alert_dispatcher(dispatcher: AlertDispatcher) -> None:
    """Set the global alert dispatcher instance."""
    global _dispatcher
    _dispatcher = dispatcher
