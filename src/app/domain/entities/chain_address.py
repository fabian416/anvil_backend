"""
Chain Address entity.
"""

from dataclasses import dataclass
from typing import Optional
from decimal import Decimal

from app.domain.entities.base import Entity
from app.domain.entities.wallet import WalletId
from app.domain.value_objects.base import ValueObject
from app.domain.enums.chain_type import ChainType
from app.domain.value_objects.created_at import CreatedAt


@dataclass(frozen=True, repr=False)
class ChainAddressId(ValueObject):
    value: int


@dataclass(eq=False, kw_only=True)
class ChainAddress(Entity[ChainAddressId]):
    wallet_id: WalletId
    chain: ChainType
    address: str
    is_active: bool
    balance_usd: Decimal
    last_balance_update: Optional[datetime]
    created_at: CreatedAt
