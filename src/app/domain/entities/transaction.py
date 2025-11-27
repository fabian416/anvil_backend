"""
Transaction entity.
"""
from dataclasses import dataclass
from typing import Optional, Any
from decimal import Decimal
from datetime import datetime

from app.domain.entities.base import Entity
from app.domain.entities.wallet import WalletId
from app.domain.value_objects.user_id import UserId
from app.domain.value_objects.base import ValueObject
from app.domain.enums.transaction_type import TransactionType
from app.domain.enums.chain_type import ChainType
from app.domain.enums.transaction_status import TransactionStatus
from app.domain.value_objects.created_at import CreatedAt

@dataclass(frozen=True, repr=False)
class TransactionId(ValueObject):
    value: int

@dataclass(eq=False, kw_only=True)
class Transaction(Entity[TransactionId]):
    user_id: UserId
    wallet_id: WalletId
    type: TransactionType
    chain: ChainType
    asset_in: Optional[str]
    amount_in: Optional[Decimal]
    asset_out: Optional[str]
    amount_out: Optional[Decimal]
    fee: Optional[Decimal]
    fee_usd: Optional[Decimal]
    tx_hash: Optional[str]
    status: TransactionStatus
    dex_aggregator: Optional[str]
    dex_route: Optional[dict[str, Any]]
    slippage: Optional[Decimal]
    error_message: Optional[str]
    block_number: Optional[int]
    confirmed_at: Optional[datetime]
    created_at: CreatedAt

    @classmethod
    def create(
        cls,
        user_id: UserId,
        wallet_id: WalletId,
        type: TransactionType,
        chain: ChainType,
        status: TransactionStatus = TransactionStatus.PENDING
    ) -> "Transaction":
        return cls(
            id_=TransactionId(0),
            user_id=user_id,
            wallet_id=wallet_id,
            type=type,
            chain=chain,
            asset_in=None,
            amount_in=None,
            asset_out=None,
            amount_out=None,
            fee=None,
            fee_usd=None,
            tx_hash=None,
            status=status,
            dex_aggregator=None,
            dex_route=None,
            slippage=None,
            error_message=None,
            block_number=None,
            confirmed_at=None,
            created_at=CreatedAt.now()
        )
