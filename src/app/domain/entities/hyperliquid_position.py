"""
Hyperliquid Position entity.
"""
from dataclasses import dataclass
from typing import Optional
from decimal import Decimal
from datetime import datetime

from app.domain.entities.base import Entity
from app.domain.entities.wallet import WalletId
from app.domain.value_objects.user_id import UserId
from app.domain.value_objects.base import ValueObject
from app.domain.enums.side import Side
from app.domain.enums.position_status import PositionStatus
from app.domain.value_objects.created_at import CreatedAt

@dataclass(frozen=True, repr=False)
class HyperliquidPositionId(ValueObject):
    value: int

@dataclass(eq=False, kw_only=True)
class HyperliquidPosition(Entity[HyperliquidPositionId]):
    user_id: UserId
    wallet_id: WalletId
    symbol: str
    side: Side
    leverage: Decimal
    size: Decimal
    entry_price: Decimal
    mark_price: Optional[Decimal]
    liquidation_price: Optional[Decimal]
    unrealized_pnl: Optional[Decimal]
    realized_pnl: Decimal
    margin: Decimal
    funding_rate: Optional[Decimal]
    last_funding_payment: Optional[Decimal]
    status: PositionStatus
    hyperliquid_order_id: Optional[str]
    opened_at: CreatedAt
    closed_at: Optional[datetime]
    created_at: CreatedAt
