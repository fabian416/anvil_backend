"""
Handler for logging transactions from the frontend.

When users send transactions via Privy on the frontend, we log them
in the backend for history, auditing, and display purposes.
"""

import logging
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal

from app.application.common.services.current_user import CurrentUserService
from app.domain.entities.transaction import Transaction, TransactionId
from app.domain.entities.wallet import WalletId
from app.domain.enums.chain_type import ChainType
from app.domain.enums.transaction_status import TransactionStatus
from app.domain.enums.transaction_type import TransactionType
from app.domain.ports.transaction.transaction_repository import TransactionRepository
from app.domain.ports.wallet.wallet_repository import WalletRepository
from app.domain.value_objects.created_at import CreatedAt
from app.domain.value_objects.user_id import UserId

logger = logging.getLogger(__name__)


# Chain ID to ChainType mapping
CHAIN_ID_MAP: dict[int, ChainType] = {
    1: ChainType.ETHEREUM,
    10: ChainType.OPTIMISM,
    137: ChainType.POLYGON,
    8453: ChainType.BASE,
    42161: ChainType.ARBITRUM,
    11155111: ChainType.ETHEREUM,  # Sepolia testnet -> treat as Ethereum
    84532: ChainType.BASE,  # Base Sepolia
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

        # Check if transaction already exists
        existing = await self._transaction_repository.get_by_tx_hash(
            input_data.tx_hash
        )
        if existing:
            logger.info(
                f"Transaction {input_data.tx_hash[:16]}... already exists, "
                f"returning existing record"
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
        tx_type = TX_TYPE_MAP.get(
            input_data.tx_type.lower(),
            TransactionType.SEND
        )

        # Parse value (Wei) to Decimal
        try:
            amount_in = Decimal(input_data.value) if input_data.value else None
        except Exception:
            amount_in = None

        # Create transaction entity
        transaction = Transaction(
            id_=TransactionId(0),  # Will be assigned by DB
            user_id=user_id,
            wallet_id=wallet.id_,
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
        )

        # Save to database
        try:
            saved_tx = await self._transaction_repository.save(transaction)
            logger.info(
                f"Transaction logged: id={saved_tx.id_.value}, "
                f"hash={input_data.tx_hash[:16]}..."
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


@dataclass
class TransactionHistoryItem:
    """Single transaction in history list."""
    id: int
    tx_hash: str | None
    type: str
    chain: str
    status: str
    asset_in: str | None
    amount_in: str | None
    asset_out: str | None
    amount_out: str | None
    fee_usd: str | None
    block_number: int | None
    confirmed_at: str | None
    created_at: str
    explorer_url: str | None


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
            try:
                chain_filter = ChainType(chain.lower())
            except ValueError:
                pass

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
        items = [
            TransactionHistoryItem(
                id=tx.id_.value,
                tx_hash=tx.tx_hash,
                type=tx.type.name.lower(),
                chain=tx.chain.value,
                status=tx.status.name.lower(),
                asset_in=tx.asset_in,
                amount_in=str(tx.amount_in) if tx.amount_in else None,
                asset_out=tx.asset_out,
                amount_out=str(tx.amount_out) if tx.amount_out else None,
                fee_usd=str(tx.fee_usd) if tx.fee_usd else None,
                block_number=tx.block_number,
                confirmed_at=tx.confirmed_at.isoformat() if tx.confirmed_at else None,
                created_at=tx.created_at.value.isoformat(),
                explorer_url=get_explorer_url(tx.chain, tx.tx_hash),
            )
            for tx in transactions
        ]

        return TransactionHistoryResult(
            user_id=user.id_.value,
            transactions=items,
            total=total,
            limit=limit,
            offset=offset,
        )
