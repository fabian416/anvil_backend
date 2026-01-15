"""
Save Swap Transaction Command Handler

Handles saving completed swap transactions to the database after successful
execution via Privy + 0x Protocol.
"""

import logging
from dataclasses import dataclass
from decimal import Decimal

from app.domain.entities.transaction import Transaction, TransactionId
from app.domain.entities.wallet import WalletId
from app.domain.enums.chain_type import ChainType
from app.domain.enums.transaction_status import TransactionStatus
from app.domain.enums.transaction_type import TransactionType
from app.domain.ports.transaction.transaction_repository import TransactionRepository
from app.domain.value_objects.created_at import CreatedAt
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
            from_amount_decimal = Decimal(command.from_amount)
            to_amount_decimal = Decimal(command.to_amount)
            if from_amount_decimal <= 0 or to_amount_decimal <= 0:
                raise ValueError("Amounts must be positive")
        except (ValueError, TypeError) as e:
            logger.error("[SAVE_SWAP] Invalid amounts: %s", e)
            raise ValueError(f"Invalid amounts: {e}")

        # Parse chain
        try:
            chain = ChainType[command.chain.upper()]
        except KeyError:
            # Fallback for common chain name variations
            chain_mapping = {
                "ethereum": ChainType.ETHEREUM,
                "base": ChainType.BASE,
                "polygon": ChainType.POLYGON,
                "arbitrum": ChainType.ARBITRUM,
                "optimism": ChainType.OPTIMISM,
            }
            chain = chain_mapping.get(command.chain.lower(), ChainType.BASE)

        # Build transaction metadata
        metadata = {
            "conversation_id": command.conversation_id,
        }

        if command.exchange_rate:
            metadata["exchange_rate"] = command.exchange_rate

        # Parse gas fee if provided
        fee_usd = None
        if command.gas_fee_usd:
            try:
                fee_usd = Decimal(command.gas_fee_usd)
            except (ValueError, TypeError):
                pass

        # Parse slippage if provided
        slippage = None
        if command.slippage:
            try:
                slippage = Decimal(command.slippage)
            except (ValueError, TypeError):
                pass

        # Create transaction entity
        # Note: wallet_id is set to 0 temporarily - will be resolved by repository
        transaction = Transaction(
            id_=TransactionId(0),
            user_id=UserId(command.user_id),
            wallet_id=WalletId(0),  # Will be resolved by repository based on user
            to_address=None,  # Not applicable for swaps
            type=TransactionType.SWAP,
            chain=chain,
            asset_in=command.from_token,
            amount_in=from_amount_decimal,
            asset_out=command.to_token,
            amount_out=to_amount_decimal,
            fee=None,
            fee_usd=fee_usd,
            tx_hash=command.tx_hash,
            status=TransactionStatus.SUCCESS,
            dex_aggregator="0x",  # Using 0x Protocol
            dex_route=None,
            slippage=slippage,
            error_message=None,
            block_number=None,
            confirmed_at=None,
            created_at=CreatedAt.now(),
            gas_used=None,
            gas_price=None,
            tx_metadata=metadata,
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
            tx_hash=saved_transaction.tx_hash or command.tx_hash,
        )
