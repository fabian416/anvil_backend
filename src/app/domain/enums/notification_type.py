"""
Notification type enumeration.

Defines the different types of notifications that can be sent.
"""

from enum import Enum


class NotificationType(str, Enum):
    """
    Notification type enumeration.

    Types:
    - CONVERSATION_UPDATE: New messages, agent responses
    - DAILY_SUMMARY: Analytics digest, daily reports
    - ALERT: Performance alerts, budget thresholds
    - TEMPLATE_EXECUTION: Template step completion updates
    - SYSTEM: System announcements, maintenance
    """

    CONVERSATION_UPDATE = "conversation_update"
    DAILY_SUMMARY = "daily_summary"
    ALERT = "alert"
    TEMPLATE_EXECUTION = "template_execution"
    SYSTEM = "system"
