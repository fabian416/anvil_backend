"""
Earn Position entity.
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
from app.domain.enums.earn_status import EarnStatus
from app.domain.value_objects.created_at import CreatedAt


@dataclass(frozen=True, repr=False)
class EarnPositionId(ValueObject):
    value: int


@dataclass(eq=False, kw_only=True)
class EarnPosition(Entity[EarnPositionId]):
    user_id: UserId
    wallet_id: WalletId
    chain: ChainType
    protocol: str
    asset: str
    amount_deposited: Decimal
    current_value: Optional[Decimal]
    apy: Optional[Decimal]
    current_apy: Optional[Decimal]
    rewards_earned: Decimal
    rewards_earned_usd: Decimal
    status: EarnStatus
    transaction_hash: Optional[str]
    deposit_tx_hash: Optional[str]
    withdraw_tx_hash: Optional[str]
    deposited_at: CreatedAt
    withdrawn_at: Optional[datetime]
    created_at: CreatedAt
