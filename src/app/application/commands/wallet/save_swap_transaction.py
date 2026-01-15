"""
Save Swap Transaction Command Handler

Handles saving completed swap transactions to the database after successful
execution via Privy + 0x Protocol.
"""

import logging
from dataclasses import dataclass
from datetime import UTC, datetime

from app.domain.entities.transaction import Transaction, TransactionType
from app.domain.ports.repositories.transaction_repository import TransactionRepository
from app.domain.value_objects.transaction_id import TransactionId
from app.domain.value_objects.user_id import UserId

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class SaveSwapTransactionCommand:
    """Command to save a completed swap transaction."""

    user_id: int
    tx_hash: str
    chain: str
    from_token: str
    to_token: str
    from_amount: str
    to_amount: str
    conversation_id: str | None = None
    exchange_rate: str | None = None
    gas_fee_usd: str | None = None
    slippage: str | None = None


@dataclass(frozen=True)
class SaveSwapTransactionResult:
    """Result of saving swap transaction."""

    transaction_id: int
    tx_hash: str


class SaveSwapTransactionHandler:
    """Handler for save swap transaction command."""

    def __init__(self, transaction_repository: TransactionRepository):
        """
        Initialize handler.

        Args:
            transaction_repository: Transaction repository
        """
        self._transaction_repository = transaction_repository

    async def handle(
        self, command: SaveSwapTransactionCommand
    ) -> SaveSwapTransactionResult:
        """
        Handle save swap transaction command.

        Args:
            command: Save swap transaction command

        Returns:
            SaveSwapTransactionResult with transaction ID

        Raises:
            ValueError: If validation fails
        """
        logger.info(
            "[SAVE_SWAP] Saving swap transaction for user %d: %s %s → %s %s",
            command.user_id,
            command.from_amount,
            command.from_token,
            command.to_amount,
            command.to_token,
        )

        # Validate amounts
        try:
            from_amount_float = float(command.from_amount)
            to_amount_float = float(command.to_amount)
            if from_amount_float <= 0 or to_amount_float <= 0:
                raise ValueError("Amounts must be positive")
        except ValueError as e:
            logger.error("[SAVE_SWAP] Invalid amounts: %s", e)
            raise ValueError(f"Invalid amounts: {e}")

        # Build transaction metadata
        metadata = {
            "from_token": command.from_token,
            "to_token": command.to_token,
            "from_amount": command.from_amount,
            "to_amount": command.to_amount,
            "chain": command.chain,
        }

        if command.exchange_rate:
            metadata["exchange_rate"] = command.exchange_rate

        if command.gas_fee_usd:
            metadata["gas_fee_usd"] = command.gas_fee_usd

        if command.slippage:
            metadata["slippage"] = command.slippage

        if command.conversation_id:
            metadata["conversation_id"] = command.conversation_id

        # Create transaction entity
        # Note: We don't have TransactionId yet, will be assigned by repository
        transaction = Transaction(
            id_=TransactionId(0),  # Temporary, will be set by repository
            user_id=UserId(command.user_id),
            tx_hash=command.tx_hash,
            chain=command.chain,
            transaction_type=TransactionType.SWAP,
            status="confirmed",
            amount=command.from_amount,
            token_symbol=command.from_token,
            metadata=metadata,
            created_at=datetime.now(UTC),
        )

        # Save to repository
        saved_transaction = await self._transaction_repository.save(transaction)

        logger.info(
            "[SAVE_SWAP] ✅ Swap transaction saved: id=%d, tx_hash=%s",
            saved_transaction.id_.value,
            command.tx_hash[:10] + "...",
        )

        return SaveSwapTransactionResult(
            transaction_id=saved_transaction.id_.value,
            tx_hash=saved_transaction.tx_hash,
        )
