"""
Handler for logging transactions from the frontend.

When users send transactions via Privy on the frontend, we log them
in the backend for history, auditing, and display purposes.
"""

import contextlib
import logging
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal

from app.application.common.services.current_user import CurrentUserService
from app.domain.entities.transaction import Transaction, TransactionId
from app.domain.enums.chain_type import ChainType
from app.domain.enums.transaction_status import TransactionStatus
from app.domain.enums.transaction_type import TransactionType
from app.domain.ports.transaction.transaction_repository import TransactionRepository
from app.domain.ports.wallet.wallet_repository import WalletRepository
from app.domain.value_objects.created_at import CreatedAt
from app.domain.value_objects.user_id import UserId

logger = logging.getLogger(__name__)


# Chain ID to ChainType mapping
# Note: Bitcoin doesn't use chain IDs like EVM, but we define pseudo-IDs for consistency
CHAIN_ID_MAP: dict[int, ChainType] = {
    1: ChainType.ETHEREUM,
    10: ChainType.OPTIMISM,
    137: ChainType.POLYGON,
    8453: ChainType.BASE,
    42161: ChainType.ARBITRUM,
    11155111: ChainType.ETHEREUM,  # Sepolia testnet -> treat as Ethereum
    84532: ChainType.BASE,  # Base Sepolia
    # Bitcoin pseudo chain IDs (for API consistency)
    0: ChainType.BITCOIN,  # Bitcoin mainnet (0 = special for UTXO chains)
    -1: ChainType.BITCOIN_TESTNET,  # Bitcoin testnet
}

# Chain name to ChainType mapping (for Bitcoin string-based lookups)
CHAIN_NAME_MAP: dict[str, ChainType] = {
    "bitcoin": ChainType.BITCOIN,
    "btc": ChainType.BITCOIN,
    "bitcoin_testnet": ChainType.BITCOIN_TESTNET,
    "btc_testnet": ChainType.BITCOIN_TESTNET,
}

# Transaction type mapping from frontend strings
TX_TYPE_MAP: dict[str, TransactionType] = {
    "send": TransactionType.SEND,
    "transfer": TransactionType.SEND,
    "swap": TransactionType.SWAP,
    "approve": TransactionType.APPROVE,
    "fund": TransactionType.FUND,
    "earn": TransactionType.EARN,
    "contract_call": TransactionType.CONTRACT_CALL,
}


class TransactionLogError(Exception):
    """Error during transaction logging."""

    pass


class WalletNotFoundForTransactionError(TransactionLogError):
    """Wallet not found for the transaction sender."""

    pass


@dataclass
class LogTransactionInput:
    """Input data for logging a transaction."""

    tx_hash: str
    from_address: str
    to_address: str | None
    value: str  # Wei as string to preserve precision
    chain_id: int
    tx_type: str = "send"
    asset_symbol: str | None = None
    data: str | None = None  # Transaction data (for contract calls)


@dataclass
class LogTransactionResult:
    """Result of transaction logging."""

    id: int
    tx_hash: str
    status: str
    chain: str
    tx_type: str
    from_address: str
    to_address: str | None
    created_at: str


class LogTransactionHandler:
    """
    Handler to log a transaction sent from the frontend.

    This is called after a successful Privy sendTransaction to persist
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

    async def execute(self, input_data: LogTransactionInput) -> LogTransactionResult:
        """
        Log a transaction to the database.

        This logs the transaction for the sender (current user). Additionally,
        if the recipient (to_address) is a registered user with a wallet in our
        system, we create a second transaction record for them so they can see
        the transaction in their history as well.

        Args:
            input_data: Transaction details from the frontend.

        Returns:
            LogTransactionResult with the created transaction info.

        Raises:
            WalletNotFoundForTransactionError: If sender wallet not found.
            TransactionLogError: If logging fails.
        """
        # Get current user
        user = await self._current_user_service.get_current_user()
        user_id = UserId(user.id_.value)

        logger.info(
            f"Logging transaction {input_data.tx_hash[:16]}... "
            f"for user {user.id_.value}"
        )

        # Check if transaction already exists FOR THIS USER
        # (same tx_hash can exist for multiple users now)
        existing = await self._transaction_repository.get_by_user_and_tx_hash(
            user_id=user_id,
            tx_hash=input_data.tx_hash,
        )
        if existing:
            logger.info(
                f"Transaction {input_data.tx_hash[:16]}... already exists for user "
                f"{user.id_.value}, returning existing record"
            )
            return LogTransactionResult(
                id=existing.id_.value,
                tx_hash=existing.tx_hash or "",
                status=existing.status.name.lower(),
                chain=existing.chain.value,
                tx_type=existing.type.name.lower(),
                from_address=input_data.from_address,
                to_address=input_data.to_address,
                created_at=existing.created_at.value.isoformat(),
            )

        # Find the wallet by address and user
        wallet = await self._wallet_repository.get_by_user_and_address(
            user_id=user_id,
            address=input_data.from_address,
        )

        # If wallet not found, try to find by address alone (might be synced)
        if not wallet:
            wallet = await self._wallet_repository.get_by_address(
                input_data.from_address
            )

        if not wallet:
            logger.warning(
                f"Wallet not found for address {input_data.from_address[:10]}... "
                f"Creating transaction with temporary wallet reference"
            )
            # We'll create a placeholder - the sync mechanism should fix this
            # For now, raise an error that the frontend should handle
            raise WalletNotFoundForTransactionError(
                f"Wallet {input_data.from_address[:10]}... not found. "
                f"Please sync your wallets first."
            )

        # Map chain ID to ChainType
        chain = CHAIN_ID_MAP.get(input_data.chain_id, ChainType.ETHEREUM)

        # Map transaction type
        tx_type = TX_TYPE_MAP.get(input_data.tx_type.lower(), TransactionType.SEND)

        # Parse value (Wei) to ETH as Decimal
        # The database column has precision (30, 18) which only supports up to 10^12 before decimal
        # So we convert from Wei to ETH (divide by 10^18)
        try:
            if input_data.value:
                wei_value = Decimal(input_data.value)
                # Convert Wei to ETH: 1 ETH = 10^18 Wei
                amount_in = wei_value / Decimal("1000000000000000000")
            else:
                amount_in = None
        except Exception:
            amount_in = None

        # Normalize to_address (lowercase if provided)
        to_address = input_data.to_address.lower() if input_data.to_address else None

        # Create transaction entity for SENDER
        transaction = Transaction(
            id_=TransactionId(0),  # Will be assigned by DB
            user_id=user_id,
            wallet_id=wallet.id_,
            to_address=to_address,  # Store recipient address for analytics
            type=tx_type,
            chain=chain,
            asset_in=input_data.asset_symbol or "ETH",
            amount_in=amount_in,
            asset_out=None,
            amount_out=None,
            fee=None,
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
            gas_used=None,  # Will be populated on confirmation
            gas_price=None,  # Will be populated on confirmation
            tx_metadata=None,  # Can be populated for contract calls
        )

        # Save sender's transaction to database
        try:
            saved_tx = await self._transaction_repository.save(transaction)
            logger.info(
                f"Transaction logged for sender: id={saved_tx.id_.value}, "
                f"hash={input_data.tx_hash[:16]}..."
            )

            # ============================================================
            # Also log the transaction for the RECEIVER if they're a registered user
            # ============================================================
            await self._log_receiver_transaction(
                input_data=input_data,
                sender_user_id=user_id,
                to_address=to_address,
                chain=chain,
                tx_type=tx_type,
                amount_in=amount_in,
            )

            return LogTransactionResult(
                id=saved_tx.id_.value,
                tx_hash=saved_tx.tx_hash or "",
                status=saved_tx.status.name.lower(),
                chain=saved_tx.chain.value,
                tx_type=saved_tx.type.name.lower(),
                from_address=input_data.from_address,
                to_address=input_data.to_address,
                created_at=saved_tx.created_at.value.isoformat(),
            )

        except Exception as e:
            logger.error(f"Failed to save transaction: {e}")
            raise TransactionLogError(f"Failed to log transaction: {e}") from e

    async def _log_receiver_transaction(
        self,
        *,
        input_data: LogTransactionInput,
        sender_user_id: UserId,
        to_address: str | None,
        chain: ChainType,
        tx_type: TransactionType,
        amount_in: Decimal | None,
    ) -> None:
        """
        Create a transaction record for the receiver if they're a registered user.

        This allows the same on-chain transaction to appear in both the sender's
        and receiver's transaction history.

        Args:
            input_data: Original transaction input data.
            sender_user_id: The sender's user ID (to avoid creating duplicate).
            to_address: The recipient address (normalized, lowercase).
            chain: The blockchain network.
            tx_type: The transaction type.
            amount_in: The transaction amount in ETH.
        """
        # Skip if no recipient address
        if not to_address:
            return

        try:
            # Look up the receiver's wallet by address
            receiver_wallet = await self._wallet_repository.get_by_address(to_address)

            if not receiver_wallet:
                # Receiver is not a registered user in our system, skip
                logger.debug(
                    f"Receiver address {to_address[:10]}... not found in system, "
                    f"skipping receiver transaction log"
                )
                return

            # Get the receiver's user ID
            receiver_user_id = receiver_wallet.user_id

            # Don't create a duplicate if sender and receiver are the same user
            if receiver_user_id.value == sender_user_id.value:
                logger.debug(
                    f"Sender and receiver are the same user ({sender_user_id.value}), "
                    f"skipping duplicate receiver transaction"
                )
                return

            # Check if the receiver already has this transaction logged
            existing_receiver_tx = (
                await self._transaction_repository.get_by_user_and_tx_hash(
                    user_id=receiver_user_id,
                    tx_hash=input_data.tx_hash,
                )
            )
            if existing_receiver_tx:
                logger.debug(
                    f"Transaction {input_data.tx_hash[:16]}... already exists for "
                    f"receiver user {receiver_user_id.value}, skipping"
                )
                return

            # Create transaction entity for RECEIVER
            # The receiver sees the same transaction but from their perspective
            receiver_tx = Transaction(
                id_=TransactionId(0),  # Will be assigned by DB
                user_id=receiver_user_id,
                wallet_id=receiver_wallet.id_,  # The receiver's wallet
                to_address=to_address,  # Keep the to_address for consistency
                type=tx_type,  # Same transaction type
                chain=chain,
                asset_in=input_data.asset_symbol or "ETH",
                amount_in=amount_in,
                asset_out=None,
                amount_out=None,
                fee=None,
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
                    "from_address": input_data.from_address.lower(),
                },
            )

            # Save receiver's transaction to database
            saved_receiver_tx = await self._transaction_repository.save(receiver_tx)
            logger.info(
                f"Transaction logged for receiver: id={saved_receiver_tx.id_.value}, "
                f"user={receiver_user_id.value}, hash={input_data.tx_hash[:16]}..."
            )

        except Exception as e:
            # Log the error but don't fail the main sender flow
            # The receiver transaction is a nice-to-have, not critical
            logger.warning(
                f"Failed to log receiver transaction for {to_address[:10]}...: {e}"
            )


@dataclass
class TransactionHistoryItem:
    """Single transaction in history list."""

    id: int
    tx_hash: str | None
    type: str
    chain: str
    status: str
    to_address: str | None  # Recipient address
    asset_in: str | None
    amount_in: str | None
    asset_out: str | None
    amount_out: str | None
    fee_usd: str | None
    block_number: int | None
    confirmed_at: str | None
    created_at: str
    explorer_url: str | None
    # Analytics fields
    gas_used: int | None
    gas_price: int | None
    # Direction fields (for dual transaction display)
    is_incoming: bool  # True if user is the receiver
    from_address: str | None  # Sender address (for incoming transactions)


@dataclass
class TransactionHistoryResult:
    """Result of transaction history query."""

    user_id: int
    transactions: list[TransactionHistoryItem]
    total: int
    limit: int
    offset: int


# Explorer URL templates by chain
EXPLORER_URLS: dict[ChainType, str] = {
    ChainType.ETHEREUM: "https://etherscan.io/tx/{tx_hash}",
    ChainType.ARBITRUM: "https://arbiscan.io/tx/{tx_hash}",
    ChainType.BASE: "https://basescan.org/tx/{tx_hash}",
    ChainType.POLYGON: "https://polygonscan.com/tx/{tx_hash}",
    ChainType.OPTIMISM: "https://optimistic.etherscan.io/tx/{tx_hash}",
    # Bitcoin explorers
    ChainType.BITCOIN: "https://mempool.space/tx/{tx_hash}",
    ChainType.BITCOIN_TESTNET: "https://mempool.space/testnet/tx/{tx_hash}",
}


def get_explorer_url(chain: ChainType, tx_hash: str | None) -> str | None:
    """Get block explorer URL for a transaction."""
    if not tx_hash:
        return None
    template = EXPLORER_URLS.get(chain)
    if not template:
        return None
    return template.format(tx_hash=tx_hash)


class GetTransactionHistoryHandler:
    """
    Handler to get transaction history for the current user.

    Supports filtering by chain, status, and transaction type.
    """

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
        chain: str | None = None,
        status: str | None = None,
        tx_type: str | None = None,
    ) -> TransactionHistoryResult:
        """
        Get transaction history for the current user.

        Args:
            limit: Maximum number of results (default 50).
            offset: Number of results to skip (default 0).
            chain: Filter by blockchain name (optional).
            status: Filter by status: pending, success, failed (optional).
            tx_type: Filter by type: send, swap, etc. (optional).

        Returns:
            TransactionHistoryResult with paginated transactions.
        """
        user = await self._current_user_service.get_current_user()
        user_id = UserId(user.id_.value)

        # Parse filters
        chain_filter: ChainType | None = None
        if chain:
            with contextlib.suppress(ValueError):
                chain_filter = ChainType(chain.lower())

        status_filter: TransactionStatus | None = None
        if status:
            status_map = {
                "pending": TransactionStatus.PENDING,
                "success": TransactionStatus.SUCCESS,
                "failed": TransactionStatus.FAILED,
            }
            status_filter = status_map.get(status.lower())

        type_filter: TransactionType | None = None
        if tx_type:
            type_filter = TX_TYPE_MAP.get(tx_type.lower())

        # Get transactions
        transactions = await self._transaction_repository.get_by_user_id(
            user_id,
            limit=limit,
            offset=offset,
            chain=chain_filter,
            status=status_filter,
            tx_type=type_filter,
        )

        # Get total count
        total = await self._transaction_repository.count_by_user_id(
            user_id,
            chain=chain_filter,
            status=status_filter,
            tx_type=type_filter,
        )

        # Convert to response items
        items = []
        for tx in transactions:
            # Determine if this is an incoming transaction (receiver's view)
            is_incoming = bool(tx.tx_metadata and tx.tx_metadata.get("receiver_view"))
            # Get the sender's address from metadata (for incoming transactions)
            from_address = (
                tx.tx_metadata.get("from_address")
                if tx.tx_metadata and is_incoming
                else None
            )

            items.append(
                TransactionHistoryItem(
                    id=tx.id_.value,
                    tx_hash=tx.tx_hash,
                    type=tx.type.name.lower(),
                    chain=tx.chain.value,
                    status=tx.status.name.lower(),
                    to_address=tx.to_address,
                    asset_in=tx.asset_in,
                    amount_in=str(tx.amount_in) if tx.amount_in else None,
                    asset_out=tx.asset_out,
                    amount_out=str(tx.amount_out) if tx.amount_out else None,
                    fee_usd=str(tx.fee_usd) if tx.fee_usd else None,
                    block_number=tx.block_number,
                    confirmed_at=(
                        tx.confirmed_at.isoformat() if tx.confirmed_at else None
                    ),
                    created_at=tx.created_at.value.isoformat(),
                    explorer_url=get_explorer_url(tx.chain, tx.tx_hash),
                    gas_used=tx.gas_used,
                    gas_price=tx.gas_price,
                    is_incoming=is_incoming,
                    from_address=from_address,
                )
            )

        return TransactionHistoryResult(
            user_id=user.id_.value,
            transactions=items,
            total=total,
            limit=limit,
            offset=offset,
        )
