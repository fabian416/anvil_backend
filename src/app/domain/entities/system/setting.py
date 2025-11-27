"""
Setting entity.
"""
from dataclasses import dataclass
from typing import Optional
from datetime import datetime

from app.domain.entities.base import Entity
from app.domain.value_objects.base import ValueObject
from app.domain.value_objects.user_id import UserId
from app.domain.enums.system.setting_scope import SettingScope
from app.domain.value_objects.updated_at import UpdatedAt

@dataclass(frozen=True, repr=False)
class SettingId(ValueObject):
    value: int

@dataclass(eq=False, kw_only=True)
class Setting(Entity[SettingId]):
    key: str
    value: Optional[str]
    scope: SettingScope
    is_sensitive: bool
    description: Optional[str]
    updated_at: UpdatedAt
    updated_by: Optional[UserId]
