"""
LLM Cost Alert entity.
"""

from dataclasses import dataclass
from typing import Optional
from decimal import Decimal
from datetime import datetime

from app.domain.entities.base import Entity
from app.domain.value_objects.user_id import UserId
from app.domain.value_objects.base import ValueObject
from app.domain.enums.ai.cost_alert_type import CostAlertType
from app.domain.value_objects.created_at import CreatedAt


@dataclass(frozen=True, repr=False)
class CostAlertId(ValueObject):
    value: int


@dataclass(eq=False, kw_only=True)
class LLMCostAlert(Entity[CostAlertId]):
    alert_type: CostAlertType
    threshold_usd: Decimal
    actual_cost_usd: Decimal
    time_period_start: datetime
    time_period_end: datetime
    user_id: Optional[UserId]
    provider: Optional[str]
    alert_sent: bool
    alert_sent_at: Optional[datetime]
    created_at: CreatedAt
