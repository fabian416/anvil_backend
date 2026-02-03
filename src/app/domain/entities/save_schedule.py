"""
Save Schedule entity.
"""

from dataclasses import dataclass
from typing import Optional
from decimal import Decimal
from datetime import datetime

from app.domain.entities.base import Entity
from app.domain.entities.wallet import WalletId
from app.domain.value_objects.user_id import UserId
from app.domain.value_objects.base import ValueObject
from app.domain.enums.chain_type import ChainType
from app.domain.enums.frequency import Frequency
from app.domain.enums.schedule_status import ScheduleStatus
from app.domain.value_objects.created_at import CreatedAt
from app.domain.value_objects.updated_at import UpdatedAt


@dataclass(frozen=True, repr=False)
class SaveScheduleId(ValueObject):
    value: int


@dataclass(eq=False, kw_only=True)
class SaveSchedule(Entity[SaveScheduleId]):
    user_id: UserId
    wallet_id: WalletId
    chain: ChainType
    asset: str
    amount: Decimal
    frequency: Frequency
    day_of_week: Optional[int]
    day_of_month: Optional[int]
    destination_protocol: Optional[str]
    status: ScheduleStatus
    next_execution_at: datetime
    last_execution_at: Optional[datetime]
    total_saved: Decimal
    execution_count: int
    max_executions: Optional[int]
    created_at: CreatedAt
    updated_at: UpdatedAt
