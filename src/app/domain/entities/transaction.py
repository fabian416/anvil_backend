"""
Transaction entity.

Represents an on-chain transaction initiated by a user via the frontend.
Supports logging for history, auditing, and analytics.

Fields for analytics (per TASKS.md):
- Minimum: tx_hash, from_address (wallet), to_address, value, chain_id, tx_type,
           asset_symbol, user_id, created_at, status
- Mid-term: gas_used, gas_price, fee_total, block_number, metadata JSON
"""

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Any

from app.domain.entities.base import Entity
from app.domain.entities.wallet import WalletId
from app.domain.enums.chain_type import ChainType
from app.domain.enums.transaction_status import TransactionStatus
from app.domain.enums.transaction_type import TransactionType
from app.domain.value_objects.base import ValueObject
from app.domain.value_objects.created_at import CreatedAt
from app.domain.value_objects.user_id import UserId


@dataclass(frozen=True, repr=False)
class TransactionId(ValueObject):
    value: int


@dataclass(eq=False, kw_only=True)
class Transaction(Entity[TransactionId]):
    """
    Transaction entity representing an on-chain operation.

    Core fields:
        user_id: User who initiated the transaction
        wallet_id: Source wallet (from_address comes from wallet)
        to_address: Recipient address (can be EOA, contract, or None for creation)
        type: Transaction type (SEND, SWAP, APPROVE, etc.)
        chain: Blockchain network
        asset_in/out, amount_in/out: Token details for swaps/transfers
        tx_hash: On-chain transaction hash
        status: PENDING, SUCCESS, or FAILED

    Analytics fields (mid-term):
        gas_used: Gas units consumed
        gas_price: Gas price in wei
        metadata: Additional context (contract address for swaps, etc.)
    """

    user_id: UserId
    wallet_id: WalletId
    to_address: str | None  # Recipient address (0x...)
    type: TransactionType
    chain: ChainType
    asset_in: str | None
    amount_in: Decimal | None
    asset_out: str | None
    amount_out: Decimal | None
    fee: Decimal | None
    fee_usd: Decimal | None
    tx_hash: str | None
    status: TransactionStatus
    dex_aggregator: str | None
    dex_route: dict[str, Any] | None
    slippage: Decimal | None
    error_message: str | None
    block_number: int | None
    confirmed_at: datetime | None
    created_at: CreatedAt
    # Analytics fields (mid-term)
    gas_used: int | None  # Gas units consumed
    gas_price: int | None  # Gas price in wei
    tx_metadata: dict[str, Any] | None  # Additional context (contract, protocol, etc.)

    @classmethod
    def create(
        cls,
        user_id: UserId,
        wallet_id: WalletId,
        type: TransactionType,
        chain: ChainType,
        status: TransactionStatus = TransactionStatus.PENDING,
        to_address: str | None = None,
    ) -> "Transaction":
        """Create a new transaction with default values."""
        return cls(
            id_=TransactionId(0),
            user_id=user_id,
            wallet_id=wallet_id,
            to_address=to_address,
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
            created_at=CreatedAt.now(),
            gas_used=None,
            gas_price=None,
            tx_metadata=None,
        )
