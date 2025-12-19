"""
Handler for logging Bitcoin transactions from the frontend.

When users send BTC transactions via Privy on the frontend, we log them
in the backend for history, auditing, and metrics purposes.
"""

import logging
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from typing import Literal

from app.application.common.services.current_user import CurrentUserService
from app.domain.transactions.entities.transaction import Transaction, TransactionId
from app.domain.enums.chain_type import ChainType
from app.domain.enums.transaction_status import TransactionStatus
from app.domain.enums.transaction_type import TransactionType
from app.domain.transactions.ports.transaction.transaction_repository import TransactionRepository
from app.domain.ports.wallet.wallet_repository import WalletRepository
from app.domain.value_objects.created_at import CreatedAt
from app.domain.value_objects.user_id import UserId

logger = logging.getLogger(__name__)


# Bitcoin explorer URLs
BTC_EXPLORER_URLS = {
    "bitcoin": "https://mempool.space/tx/{tx_hash}",
    "bitcoin_testnet": "https://mempool.space/testnet/tx/{tx_hash}",
}


def get_btc_explorer_url(network: str, tx_hash: str | None) -> str | None:
    """Get Mempool.space explorer URL for a Bitcoin transaction."""
    if not tx_hash:
        return None
    template = BTC_EXPLORER_URLS.get(network)
    if not template:
        return None
    return template.format(tx_hash=tx_hash)


@dataclass
class LogBitcoinTransactionInput:
    """Input data for logging a Bitcoin transaction."""

    tx_hash: str
    from_address: str
    to_address: str
    amount_btc: str  # BTC as string for precision
    fee_btc: str | None = None
    network: Literal["bitcoin", "bitcoin_testnet"] = "bitcoin"


@dataclass
class LogBitcoinTransactionResult:
    """Result of Bitcoin transaction logging."""

    id: int
    tx_hash: str
    status: str
    chain: str
    from_address: str
    to_address: str
    amount_btc: str
    created_at: str
    explorer_url: str | None


class LogBitcoinTransactionHandler:
    """
    Handler to log a Bitcoin transaction sent from the frontend.

    This is called after a successful Privy BTC sendTransaction to persist
    the transaction details for history and auditing.
    """

    def __init__(
        self,
        current_user_service: CurrentUserService,
        transaction_repository: TransactionRepository,
        wallet_repository: WalletRepository,
    ):
        self._current_user_service = current_user_service
        self._transaction_repository = transaction_repository
        self._wallet_repository = wallet_repository

    async def execute(
        self, input_data: LogBitcoinTransactionInput
    ) -> LogBitcoinTransactionResult:
        """
        Log a Bitcoin transaction to the database.

        Args:
            input_data: Bitcoin transaction details from the frontend.

        Returns:
            LogBitcoinTransactionResult with the created transaction info.
        """
        # Get current user
        user = await self._current_user_service.get_current_user()
        user_id = UserId(user.id_.value)

        logger.info(
            f"Logging BTC transaction {input_data.tx_hash[:16]}... "
            f"for user {user.id_.value}"
        )

        # Check if transaction already exists for this user
        existing = await self._transaction_repository.get_by_user_and_tx_hash(
            user_id=user_id,
            tx_hash=input_data.tx_hash,
        )
        if existing:
            logger.info(
                f"BTC Transaction {input_data.tx_hash[:16]}... already exists for user "
                f"{user.id_.value}, returning existing record"
            )
            return LogBitcoinTransactionResult(
                id=existing.id_.value,
                tx_hash=existing.tx_hash or "",
                status=existing.status.name.lower(),
                chain=existing.chain.value,
                from_address=input_data.from_address,
                to_address=input_data.to_address,
                amount_btc=input_data.amount_btc,
                created_at=existing.created_at.value.isoformat(),
                explorer_url=get_btc_explorer_url(
                    input_data.network, existing.tx_hash
                ),
            )

        # Find or create wallet reference for user
        # For Bitcoin, we may not have wallet records yet, so we use a placeholder
        wallet = await self._wallet_repository.get_by_user_and_address(
            user_id=user_id,
            address=input_data.from_address,
        )

        # If wallet not found, try to find any wallet for the user
        # Bitcoin addresses might not be pre-registered like EVM addresses
        if not wallet:
            wallets = await self._wallet_repository.get_by_user_id(user_id)
            if wallets:
                wallet = wallets[0]  # Use first wallet as reference
            else:
                logger.warning(
                    f"No wallet found for user {user.id_.value}, "
                    f"BTC transaction logging requires at least one wallet"
                )
                raise ValueError(
                    "No wallet found for user. Please sync your wallets first."
                )

        # Determine chain type
        chain = (
            ChainType.BITCOIN
            if input_data.network == "bitcoin"
            else ChainType.BITCOIN_TESTNET
        )

        # Parse amount to Decimal
        try:
            amount_in = Decimal(input_data.amount_btc)
        except Exception:
            amount_in = None

        # Parse fee to Decimal
        fee = None
        if input_data.fee_btc:
            try:
                fee = Decimal(input_data.fee_btc)
            except (ValueError, ArithmeticError):
                logger.debug(f"Could not parse fee_btc: {input_data.fee_btc}")

        # Create transaction entity
        transaction = Transaction(
            id_=TransactionId(0),  # Will be assigned by DB
            user_id=user_id,
            wallet_id=wallet.id_,
            to_address=input_data.to_address,
            type=TransactionType.SEND,
            chain=chain,
            asset_in="BTC",
            amount_in=amount_in,
            asset_out=None,
            amount_out=None,
            fee=fee,
            fee_usd=None,
            tx_hash=input_data.tx_hash.lower(),
            status=TransactionStatus.PENDING,
            dex_aggregator=None,
            dex_route=None,
            slippage=None,
            error_message=None,
            block_number=None,
            confirmed_at=None,
            created_at=CreatedAt(datetime.now(UTC)),
            gas_used=None,
            gas_price=None,
            tx_metadata={
                "network_type": "bitcoin",
                "from_address": input_data.from_address,
            },
        )

        # Save transaction
        try:
            saved_tx = await self._transaction_repository.save(transaction)
            logger.info(
                f"BTC Transaction logged: id={saved_tx.id_.value}, "
                f"hash={input_data.tx_hash[:16]}..."
            )

            # Log receiver transaction if recipient is also a user
            await self._log_receiver_transaction(
                input_data=input_data,
                sender_user_id=user_id,
                chain=chain,
                amount_in=amount_in,
                fee=fee,
            )

            return LogBitcoinTransactionResult(
                id=saved_tx.id_.value,
                tx_hash=saved_tx.tx_hash or "",
                status=saved_tx.status.name.lower(),
                chain=saved_tx.chain.value,
                from_address=input_data.from_address,
                to_address=input_data.to_address,
                amount_btc=input_data.amount_btc,
                created_at=saved_tx.created_at.value.isoformat(),
                explorer_url=get_btc_explorer_url(
                    input_data.network, saved_tx.tx_hash
                ),
            )

        except Exception as e:
            logger.error(f"Failed to save BTC transaction: {e}")
            raise ValueError(f"Failed to log Bitcoin transaction: {e}") from e

    async def _log_receiver_transaction(
        self,
        *,
        input_data: LogBitcoinTransactionInput,
        sender_user_id: UserId,
        chain: ChainType,
        amount_in: Decimal | None,
        fee: Decimal | None,
    ) -> None:
        """Create a transaction record for the receiver if they're a registered user."""
        try:
            # Look up the receiver's wallet by address
            receiver_wallet = await self._wallet_repository.get_by_address(
                input_data.to_address
            )

            if not receiver_wallet:
                logger.debug(
                    f"BTC Receiver address {input_data.to_address[:10]}... not found, "
                    f"skipping receiver transaction log"
                )
                return

            receiver_user_id = receiver_wallet.user_id

            # Don't create duplicate if sender and receiver are same user
            if receiver_user_id.value == sender_user_id.value:
                return

            # Check if receiver already has this transaction
            existing = await self._transaction_repository.get_by_user_and_tx_hash(
                user_id=receiver_user_id,
                tx_hash=input_data.tx_hash,
            )
            if existing:
                return

            # Create transaction for receiver
            receiver_tx = Transaction(
                id_=TransactionId(0),
                user_id=receiver_user_id,
                wallet_id=receiver_wallet.id_,
                to_address=input_data.to_address,
                type=TransactionType.SEND,
                chain=chain,
                asset_in="BTC",
                amount_in=amount_in,
                asset_out=None,
                amount_out=None,
                fee=fee,
                fee_usd=None,
                tx_hash=input_data.tx_hash.lower(),
                status=TransactionStatus.PENDING,
                dex_aggregator=None,
                dex_route=None,
                slippage=None,
                error_message=None,
                block_number=None,
                confirmed_at=None,
                created_at=CreatedAt(datetime.now(UTC)),
                gas_used=None,
                gas_price=None,
                tx_metadata={
                    "receiver_view": True,
                    "from_address": input_data.from_address,
                    "network_type": "bitcoin",
                },
            )

            saved = await self._transaction_repository.save(receiver_tx)
            logger.info(
                f"BTC Transaction logged for receiver: id={saved.id_.value}, "
                f"user={receiver_user_id.value}"
            )

        except Exception as e:
            logger.warning(
                f"Failed to log receiver BTC transaction: {e}"
            )


# ============================================================
# Get Bitcoin Transaction History Handler
# ============================================================


@dataclass
class BitcoinTransactionHistoryItem:
    """Single Bitcoin transaction in history."""

    id: int
    tx_hash: str | None
    chain: str
    status: str
    from_address: str | None
    to_address: str | None
    amount_btc: str | None
    fee_btc: str | None
    confirmed_at: str | None
    created_at: str
    explorer_url: str | None
    is_incoming: bool


@dataclass
class BitcoinTransactionHistoryResult:
    """Result of Bitcoin transaction history query."""

    user_id: int
    transactions: list[BitcoinTransactionHistoryItem]
    total: int
    limit: int
    offset: int


class GetBitcoinTransactionHistoryHandler:
    """Handler to get Bitcoin transaction history for the current user."""

    def __init__(
        self,
        current_user_service: CurrentUserService,
        transaction_repository: TransactionRepository,
    ):
        self._current_user_service = current_user_service
        self._transaction_repository = transaction_repository

    async def execute(
        self,
        *,
        limit: int = 50,
        offset: int = 0,
        network: str | None = None,
        status: str | None = None,
    ) -> BitcoinTransactionHistoryResult:
        """
        Get Bitcoin transaction history for the current user.

        Args:
            limit: Maximum number of results.
            offset: Number of results to skip.
            network: Filter by network: bitcoin, bitcoin_testnet.
            status: Filter by status: pending, success, failed.

        Returns:
            BitcoinTransactionHistoryResult with paginated transactions.
        """
        user = await self._current_user_service.get_current_user()
        user_id = UserId(user.id_.value)

        # Parse filters
        chain_filter: ChainType | None = None
        if network:
            if network == "bitcoin":
                chain_filter = ChainType.BITCOIN
            elif network == "bitcoin_testnet":
                chain_filter = ChainType.BITCOIN_TESTNET
        else:
            # Default: get both Bitcoin chains
            # We'll handle this by making two queries or filtering in memory
            pass

        status_filter: TransactionStatus | None = None
        if status:
            status_map = {
                "pending": TransactionStatus.PENDING,
                "success": TransactionStatus.SUCCESS,
                "failed": TransactionStatus.FAILED,
            }
            status_filter = status_map.get(status.lower())

        # Get transactions - filter by Bitcoin chains
        # Since repo doesn't support OR on chains, we query both if no specific network
        transactions = []
        total = 0

        if chain_filter:
            transactions = await self._transaction_repository.get_by_user_id(
                user_id,
                limit=limit,
                offset=offset,
                chain=chain_filter,
                status=status_filter,
            )
            total = await self._transaction_repository.count_by_user_id(
                user_id,
                chain=chain_filter,
                status=status_filter,
            )
        else:
            # Get both Bitcoin mainnet and testnet
            btc_txs = await self._transaction_repository.get_by_user_id(
                user_id,
                limit=limit,
                offset=offset,
                chain=ChainType.BITCOIN,
                status=status_filter,
            )
            btc_testnet_txs = await self._transaction_repository.get_by_user_id(
                user_id,
                limit=limit,
                offset=offset,
                chain=ChainType.BITCOIN_TESTNET,
                status=status_filter,
            )

            # Merge and sort by created_at
            all_txs = btc_txs + btc_testnet_txs
            all_txs.sort(key=lambda x: x.created_at.value, reverse=True)
            transactions = all_txs[:limit]

            btc_count = await self._transaction_repository.count_by_user_id(
                user_id,
                chain=ChainType.BITCOIN,
                status=status_filter,
            )
            btc_testnet_count = await self._transaction_repository.count_by_user_id(
                user_id,
                chain=ChainType.BITCOIN_TESTNET,
                status=status_filter,
            )
            total = btc_count + btc_testnet_count

        # Convert to response items
        items = []
        for tx in transactions:
            is_incoming = bool(tx.tx_metadata and tx.tx_metadata.get("receiver_view"))
            from_address = (
                tx.tx_metadata.get("from_address")
                if tx.tx_metadata and is_incoming
                else tx.tx_metadata.get("from_address") if tx.tx_metadata else None
            )

            items.append(
                BitcoinTransactionHistoryItem(
                    id=tx.id_.value,
                    tx_hash=tx.tx_hash,
                    chain=tx.chain.value,
                    status=tx.status.name.lower(),
                    from_address=from_address,
                    to_address=tx.to_address,
                    amount_btc=str(tx.amount_in) if tx.amount_in else None,
                    fee_btc=str(tx.fee) if tx.fee else None,
                    confirmed_at=(
                        tx.confirmed_at.isoformat() if tx.confirmed_at else None
                    ),
                    created_at=tx.created_at.value.isoformat(),
                    explorer_url=get_btc_explorer_url(tx.chain.value, tx.tx_hash),
                    is_incoming=is_incoming,
                )
            )

        return BitcoinTransactionHistoryResult(
            user_id=user.id_.value,
            transactions=items,
            total=total,
            limit=limit,
            offset=offset,
        )
