"""
Audit Log entity.
"""

from dataclasses import dataclass
from typing import Optional, Any
from datetime import datetime

from app.domain.entities.base import Entity
from app.domain.value_objects.base import ValueObject
from app.domain.value_objects.user_id import UserId
from app.domain.value_objects.created_at import CreatedAt


@dataclass(frozen=True, repr=False)
class AuditLogId(ValueObject):
    value: int


@dataclass(eq=False, kw_only=True)
class AuditLog(Entity[AuditLogId]):
    actor_user_id: UserId
    action: str
    entity: str
    entity_id: Optional[str]
    payload_json: Optional[dict[str, Any]]
    ip_address: Optional[str]
    user_agent: Optional[str]
    created_at: CreatedAt
