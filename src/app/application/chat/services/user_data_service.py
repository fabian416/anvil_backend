"""
User Data Service for Authenticated Chat.

Provides access to user's wallet, portfolio, and transaction data
for the AuthenticatedSupervisorCoordinator and its agents.

This service aggregates data from multiple repositories and formats
it for use in chat context.

IMPORTANT: This service is designed to be NON-BLOCKING and NON-DESTRUCTIVE.
It catches all database errors gracefully and returns partial/empty data
rather than corrupting the shared database session.

The repositories used here share the same MainAsyncSession with the rest of
the request. If a query fails, PostgreSQL marks the transaction as "aborted"
and all subsequent queries will fail. To prevent this:
1. All database operations are wrapped in individual try/except blocks
2. Errors result in returning default/empty values
3. We NEVER let exceptions propagate that could corrupt the session
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta, UTC
from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:
    from app.domain.ports.wallet.wallet_repository import WalletRepository
    from app.domain.transactions.ports.transaction.transaction_repository import (
        TransactionRepository,
    )
    from app.domain.portfolio.ports.portfolio.portfolio_repository import (
        PortfolioRepository,
    )

from app.domain.value_objects.user_id import UserId
from app.domain.enums.chain_type import ChainType
from app.infrastructure.auth.handlers.transaction_log import get_explorer_url

logger = logging.getLogger(__name__)


@dataclass
class WalletSummary:
    """Summary of user's wallet information."""

    wallet_id: str
    address: str
    chain_type: str | None = None
    provider: str | None = None
    is_primary: bool = False
    # QR code fields (pre-generated)
    qr_image_url: str | None = None
    qr_data: str | None = None  # EIP-681 URI: ethereum:{chain_id}:{address}
    qr_chain_id: int = 8453  # Default: Base


@dataclass
class PortfolioSummary:
    """Summary of user's portfolio."""

    total_value_usd: float = 0.0
    token_count: int = 0
    top_holdings: list[dict[str, Any]] = field(default_factory=list)
    last_updated: datetime | None = None
    chains: list[str] = field(default_factory=list)


@dataclass
class TransactionSummary:
    """Summary of user's recent transactions."""

    total_count: int = 0
    recent_transactions: list[dict[str, Any]] = field(default_factory=list)
    volume_last_30_days: float = 0.0
    most_active_chain: str | None = None


@dataclass
class UserDataContext:
    """
    Complete user data context for authenticated chat.

    This object is injected into the supervisor's context to provide
    agents with access to user-specific data.
    """

    user_id: str
    wallets: list[WalletSummary] = field(default_factory=list)
    primary_wallet: WalletSummary | None = None
    portfolio: PortfolioSummary | None = None
    transactions: TransactionSummary | None = None

    def to_context_string(self) -> str:
        """Convert to a string for LLM context injection."""
        lines = []

        # Wallet info
        if self.primary_wallet:
            lines.append(
                f"**Connected Wallet:** {self.primary_wallet.address[:10]}...{self.primary_wallet.address[-6:]}"
            )
            if self.primary_wallet.chain_type:
                lines.append(f"  Chain: {self.primary_wallet.chain_type}")

        # Portfolio info
        if self.portfolio:
            lines.append(f"**Portfolio Value:** ${self.portfolio.total_value_usd:,.2f}")
            if self.portfolio.top_holdings:
                top_3 = self.portfolio.top_holdings[:3]
                holdings_str = ", ".join([f"{h['symbol']}" for h in top_3])
                lines.append(f"  Top Holdings: {holdings_str}")
            if self.portfolio.last_updated:
                lines.append(
                    f"  Last Updated: {self.portfolio.last_updated.strftime('%Y-%m-%d %H:%M')}"
                )

        # Transaction info
        if self.transactions:
            lines.append(
                f"**Transaction History:** {self.transactions.total_count} total"
            )
            if self.transactions.volume_last_30_days > 0:
                lines.append(
                    f"  30-Day Volume: ${self.transactions.volume_last_30_days:,.2f}"
                )
            if self.transactions.most_active_chain:
                lines.append(
                    f"  Most Active Chain: {self.transactions.most_active_chain}"
                )

        return "\n".join(lines) if lines else "No wallet connected"

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "user_id": self.user_id,
            "primary_wallet": {
                "address": self.primary_wallet.address if self.primary_wallet else None,
                "chain_type": self.primary_wallet.chain_type
                if self.primary_wallet
                else None,
            }
            if self.primary_wallet
            else None,
            "portfolio": {
                "total_value_usd": self.portfolio.total_value_usd
                if self.portfolio
                else 0,
                "token_count": self.portfolio.token_count if self.portfolio else 0,
                "top_holdings": self.portfolio.top_holdings if self.portfolio else [],
            }
            if self.portfolio
            else None,
            "transactions": {
                "total_count": self.transactions.total_count
                if self.transactions
                else 0,
                "volume_last_30_days": self.transactions.volume_last_30_days
                if self.transactions
                else 0,
            }
            if self.transactions
            else None,
        }


class UserDataService:
    """
    Service for fetching aggregated user data.

    This service provides user context (wallet, portfolio, transactions) for
    the authenticated chat supervisor. It's designed to be:

    1. NON-BLOCKING: Always returns quickly, even if data isn't available
    2. NON-DESTRUCTIVE: Never corrupts the shared database session
    3. GRACEFUL: Returns partial/empty data on errors

    IMPORTANT: The repositories share the main database session. If a query
    fails, PostgreSQL marks the transaction as aborted. To prevent session
    corruption, this service does NOT inject repositories by default.
    Instead, use `set_repositories()` carefully or rely on defaults.

    Usage:
        service = UserDataService()
        context = await service.get_user_context(user_id="123")
    """

    def __init__(
        self,
        wallet_repository: "WalletRepository | None" = None,
        portfolio_repository: "PortfolioRepository | None" = None,
        transaction_repository: "TransactionRepository | None" = None,
    ):
        """
        Initialize with optional repositories.

        NOTE: Repositories are DISABLED by default to prevent session corruption.
        The UserDataService will return empty context when repositories are None.

        Args:
            wallet_repository: Optional wallet repository (disabled by default)
            portfolio_repository: Optional portfolio repository (disabled by default)
            transaction_repository: Optional transaction repository (disabled by default)
        """
        self._wallet_repo = wallet_repository
        self._portfolio_repo = portfolio_repository
        # Transaction repo re-enabled: _get_transaction_summary has comprehensive
        # try/except blocks that return empty TransactionSummary on failure,
        # preventing session corruption.
        self._tx_repo = transaction_repository
        self._tx_repo_enabled = transaction_repository is not None

    def enable_transaction_repo(self, tx_repo: "TransactionRepository") -> None:
        """
        Explicitly enable/replace transaction repository at runtime.

        The _get_transaction_summary method has comprehensive try/except
        blocks that return empty TransactionSummary on any failure.
        """
        self._tx_repo = tx_repo
        self._tx_repo_enabled = True
        logger.info("Transaction repository enabled for UserDataService")

    async def get_user_context(
        self,
        user_id: str,
        include_portfolio: bool = True,
        include_transactions: bool = True,
        transaction_limit: int = 10,
    ) -> UserDataContext:
        """
        Get complete user data context for chat.

        Args:
            user_id: The user's ID
            include_portfolio: Whether to fetch portfolio data
            include_transactions: Whether to fetch transaction history
            transaction_limit: Max transactions to include

        Returns:
            UserDataContext with aggregated user data
        """
        context = UserDataContext(user_id=user_id)

        # Fetch wallets - isolated to prevent session corruption
        try:
            wallets = await self._get_wallets(user_id)
            context.wallets = wallets
            if wallets:
                # Find primary wallet (first one or marked as primary)
                context.primary_wallet = wallets[0]
                for w in wallets:
                    if w.is_primary:
                        context.primary_wallet = w
                        break
        except Exception as e:
            logger.debug(f"Wallet data unavailable for user {user_id}: {e}")

        # Fetch portfolio - isolated to prevent session corruption
        if include_portfolio and context.primary_wallet:
            try:
                context.portfolio = await self._get_portfolio_summary(
                    context.primary_wallet.wallet_id
                )
            except Exception as e:
                logger.debug(f"Portfolio data unavailable for user {user_id}: {e}")

        # Fetch transactions - isolated to prevent session corruption
        # NOTE: Transaction fetching is known to sometimes fail due to schema differences.
        # We return partial data rather than failing the entire context.
        if include_transactions:
            try:
                context.transactions = await self._get_transaction_summary(
                    user_id,
                    limit=transaction_limit,
                )
            except Exception as e:
                logger.debug(f"Transaction data unavailable for user {user_id}: {e}")
                # Return empty summary instead of None to prevent NPE
                context.transactions = TransactionSummary()

        return context

    async def _get_wallets(self, user_id: str) -> list[WalletSummary]:
        """Fetch user's wallets with QR code information."""
        if not self._wallet_repo:
            return []

        try:
            user_id_vo = UserId(int(user_id))
            wallets = await self._wallet_repo.get_by_user_id(user_id_vo)

            result = []
            for w in wallets:
                # Get QR code chain ID (default to Base)
                qr_chain_id = getattr(w, "qr_chain_id", None) or 8453
                # Build EIP-681 QR data for client-side fallback
                qr_data = f"ethereum:{qr_chain_id}:{w.address}"

                result.append(
                    WalletSummary(
                        wallet_id=str(w.id_.value),
                        address=w.address,
                        chain_type=w.chain_type if hasattr(w, "chain_type") else None,
                        provider=w.provider.value if hasattr(w, "provider") else None,
                        is_primary=getattr(w, "is_primary", False),
                        # QR code fields from database
                        qr_image_url=getattr(w, "qr_image_url", None),
                        qr_data=qr_data,
                        qr_chain_id=qr_chain_id,
                    )
                )
            return result
        except Exception as e:
            logger.error(f"Error fetching wallets: {e}")
            return []

    async def _get_portfolio_summary(self, wallet_id: str) -> PortfolioSummary | None:
        """Fetch portfolio summary for a wallet."""
        if not self._portfolio_repo:
            return None

        try:
            from app.domain.entities.wallet import WalletId

            wallet_id_vo = WalletId(int(wallet_id))

            # Get latest snapshot
            snapshot = await self._portfolio_repo.get_latest_by_wallet(wallet_id_vo)

            if not snapshot:
                return PortfolioSummary()

            # Build top holdings
            top_holdings = []
            if hasattr(snapshot, "holdings") and snapshot.holdings:
                sorted_holdings = sorted(
                    snapshot.holdings, key=lambda h: h.value_usd or 0, reverse=True
                )[:5]

                for holding in sorted_holdings:
                    top_holdings.append({
                        "symbol": holding.token_symbol,
                        "amount": float(holding.amount) if holding.amount else 0,
                        "value_usd": float(holding.value_usd)
                        if holding.value_usd
                        else 0,
                    })

            return PortfolioSummary(
                total_value_usd=float(snapshot.total_usd)
                if hasattr(snapshot, "total_usd")
                else 0,
                token_count=len(snapshot.holdings)
                if hasattr(snapshot, "holdings")
                else 0,
                top_holdings=top_holdings,
                last_updated=snapshot.captured_at
                if hasattr(snapshot, "captured_at")
                else None,
                chains=[snapshot.chain.value]
                if hasattr(snapshot, "chain") and snapshot.chain
                else [],
            )
        except Exception as e:
            logger.error(f"Error fetching portfolio: {e}")
            return None

    async def _get_transaction_summary(
        self,
        user_id: str,
        limit: int = 10,
    ) -> TransactionSummary | None:
        """
        Fetch transaction summary for a user.

        NOTE: This method is designed to be non-destructive. If any database
        operation fails, it returns None without corrupting the session.
        """
        if not self._tx_repo:
            return None

        try:
            user_id_vo = UserId(int(user_id))

            # Get total count - wrapped individually to prevent cascade failures
            total_count = 0
            try:
                total_count = await self._tx_repo.count_by_user_id(user_id_vo)
            except Exception as count_err:
                logger.debug(f"Could not get transaction count: {count_err}")

            # Get recent transactions
            recent_txs = []
            try:
                recent_txs = await self._tx_repo.get_by_user_id(
                    user_id_vo,
                    limit=limit,
                )
            except Exception as tx_err:
                logger.debug(f"Could not get recent transactions: {tx_err}")

            # Calculate 30-day volume - optional, don't fail if unavailable
            volume_30d = 0.0
            try:
                thirty_days_ago = datetime.now(UTC) - timedelta(days=30)
                vol = await self._tx_repo.get_volume_by_user(
                    user_id_vo,
                    start_date=thirty_days_ago,
                )
                volume_30d = float(vol) if vol else 0.0
            except Exception as vol_err:
                logger.debug(f"Could not get 30-day volume: {vol_err}")

            # Get chain counts - optional
            most_active_chain = None
            try:
                chain_counts = await self._tx_repo.get_transaction_counts_by_chain()
                if chain_counts:
                    top_chain = max(chain_counts, key=chain_counts.get)
                    # Convert ChainType enum to string if needed
                    most_active_chain = (
                        top_chain.value if hasattr(top_chain, "value") else str(top_chain)
                    )
            except Exception as chain_err:
                logger.debug(f"Could not get chain counts: {chain_err}")

            # Format recent transactions (include full tx_hash and explorer_url for single-link display)
            recent_formatted = []
            for tx in recent_txs:
                try:
                    explorer_url = None
                    if tx.tx_hash and hasattr(tx, "chain") and tx.chain:
                        explorer_url = get_explorer_url(tx.chain, tx.tx_hash)

                    # Transaction entity uses .type (not .tx_type)
                    tx_type_val = None
                    if hasattr(tx, "type") and tx.type:
                        tx_type_val = tx.type.name if hasattr(tx.type, "name") else str(tx.type)

                    # Status: use .name for human-readable string
                    status_val = None
                    if hasattr(tx, "status") and tx.status:
                        status_val = tx.status.name.lower() if hasattr(tx.status, "name") else str(tx.status)

                    # Chain: use .value for string representation
                    chain_val = None
                    if hasattr(tx, "chain") and tx.chain:
                        chain_val = tx.chain.value if hasattr(tx.chain, "value") else str(tx.chain)

                    # created_at may be a CreatedAt value object wrapping datetime
                    created_at_str = None
                    if hasattr(tx, "created_at") and tx.created_at:
                        ca = tx.created_at
                        if hasattr(ca, "value"):
                            ca = ca.value  # Unwrap CreatedAt VO
                        if hasattr(ca, "isoformat"):
                            created_at_str = ca.isoformat()

                    # Build asset/amount display string
                    amount_display = float(tx.amount_in) if hasattr(tx, "amount_in") and tx.amount_in else 0
                    asset_in = getattr(tx, "asset_in", None) or ""
                    asset_out = getattr(tx, "asset_out", None) or ""
                    amount_out = float(tx.amount_out) if hasattr(tx, "amount_out") and tx.amount_out else 0

                    recent_formatted.append({
                        "id": str(tx.id_.value) if tx.id_ else None,
                        "tx_hash": tx.tx_hash[:16] + "..." if tx.tx_hash else None,
                        "tx_hash_full": tx.tx_hash,
                        "type": tx_type_val,
                        "status": status_val,
                        "chain": chain_val,
                        "amount": amount_display,
                        "asset_in": asset_in,
                        "asset_out": asset_out,
                        "amount_out": amount_out,
                        "created_at": created_at_str,
                        "explorer_url": explorer_url,
                    })
                except Exception as fmt_err:
                    logger.debug(f"Skipping malformed transaction: {fmt_err}")
                    continue

            return TransactionSummary(
                total_count=total_count,
                recent_transactions=recent_formatted,
                volume_last_30_days=volume_30d,
                most_active_chain=most_active_chain,
            )
        except Exception as e:
            # Catch-all to ensure we never corrupt the session
            logger.warning(f"Transaction summary unavailable: {e}")
            return TransactionSummary()

    async def get_wallet_balances(
        self,
        wallet_address: str,
        chain: ChainType | None = None,
    ) -> dict[str, Any]:
        """
        Get token balances for a wallet address.

        Note: This requires integration with blockchain RPC or indexer.
        For now, returns cached portfolio data.
        """
        # TODO: Integrate with on-chain balance fetching (e.g., Alchemy, Moralis)
        return {
            "address": wallet_address,
            "chain": chain.value if chain else "all",
            "balances": [],
            "note": "Real-time balance fetching requires blockchain integration",
        }

    async def get_transaction_history(
        self,
        user_id: str,
        limit: int = 50,
        chain: ChainType | None = None,
    ) -> list[dict[str, Any]]:
        """Get detailed transaction history for a user."""
        if not self._tx_repo:
            return []

        try:
            user_id_vo = UserId(int(user_id))
            txs = await self._tx_repo.get_by_user_id(
                user_id_vo,
                limit=limit,
                chain=chain,
            )

            return [
                {
                    "id": str(tx.id_.value) if tx.id_ else None,
                    "tx_hash": tx.tx_hash,
                    "type": tx.tx_type.value if tx.tx_type else None,
                    "status": tx.status.value if tx.status else None,
                    "chain": tx.chain.value if tx.chain else None,
                    "from_address": tx.from_address
                    if hasattr(tx, "from_address")
                    else None,
                    "to_address": tx.to_address if hasattr(tx, "to_address") else None,
                    "amount_in": float(tx.amount_in) if tx.amount_in else 0,
                    "token_in": tx.token_in if hasattr(tx, "token_in") else None,
                    "created_at": tx.created_at.isoformat() if tx.created_at else None,
                    "confirmed_at": tx.confirmed_at.isoformat()
                    if hasattr(tx, "confirmed_at") and tx.confirmed_at
                    else None,
                }
                for tx in txs
            ]
        except Exception as e:
            logger.error(f"Error fetching transaction history: {e}")
            return []
