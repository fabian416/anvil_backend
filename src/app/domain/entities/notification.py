"""
Notification entity for the hexagonal architecture.
Based on the BaseAPI Notification model with domain-driven design principles.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Dict, Any

from app.domain.entities.base import Entity
from app.domain.value_objects.notification_id import NotificationId
from app.domain.value_objects.user_id import UserId
from app.domain.value_objects.notification_title import NotificationTitle
from app.domain.value_objects.notification_action import NotificationAction
from app.domain.value_objects.notification_data import NotificationData
from app.domain.value_objects.read_status import ReadStatus
from app.domain.value_objects.created_at import CreatedAt
from app.domain.value_objects.updated_at import UpdatedAt


@dataclass(eq=False, kw_only=True)
class Notification(Entity[NotificationId]):
    """
    Notification entity representing a notification in the system.
    
    This is an anemic model following DDD principles where behavior
    is handled by domain services rather than the entity itself.
    """
    user_id: UserId
    title: NotificationTitle
    is_read: ReadStatus
    action: NotificationAction
    data_json: Optional[NotificationData]
    created_at: CreatedAt
    updated_at: UpdatedAt
