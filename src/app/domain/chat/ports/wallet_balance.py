"""
Wallet Balance Port for Context-Aware Agents.

This port defines the interface for fetching wallet balances
to update the user_context_aware.portfolio_state classification.

Implementations:
- WalletBalanceDbAdapter: Uses local DB tables (wallets, chain_addresses, portfolio_snapshots)
- (Future) WalletBalanceExternalAdapter: Uses external APIs (DeBank, Zerion)
"""

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import Protocol
from uuid import UUID


@dataclass(frozen=True)
class ChainBalance:
    """Balance for a single blockchain."""

    chain: str  # e.g., "ethereum", "arbitrum", "polygon"
    balance_usd: Decimal
    native_balance: Decimal | None = None
    native_symbol: str | None = None
    token_count: int = 0
    last_updated: datetime | None = None


@dataclass(frozen=True)
class WalletBalanceSummary:
    """Aggregated wallet balance summary."""

    wallet_address: str
    total_balance_usd: Decimal
    chain_balances: list[ChainBalance] = field(default_factory=list)
    token_count: int = 0
    last_sync_at: datetime | None = None

    @property
    def primary_chain(self) -> str | None:
        """Get the chain with highest balance."""
        if not self.chain_balances:
            return None
        return max(self.chain_balances, key=lambda x: x.balance_usd).chain

    @property
    def chain_breakdown(self) -> dict[str, Decimal]:
        """Get balance breakdown by chain."""
        return {cb.chain: cb.balance_usd for cb in self.chain_balances}


@dataclass(frozen=True)
class UserWalletAggregate:
    """Aggregated balance across all user wallets."""

    user_id: int  # Legacy user_id from users table
    chat_user_id: UUID | None = None
    total_balance_usd: Decimal = Decimal("0")
    wallet_count: int = 0
    wallets: list[WalletBalanceSummary] = field(default_factory=list)
    primary_wallet_address: str | None = None
    last_sync_at: datetime | None = None

    @property
    def chain_breakdown(self) -> dict[str, Decimal]:
        """Get balance breakdown by chain across all wallets."""
        breakdown: dict[str, Decimal] = {}
        for wallet in self.wallets:
            for chain, balance in wallet.chain_breakdown.items():
                breakdown[chain] = breakdown.get(chain, Decimal("0")) + balance
        return breakdown


class WalletBalancePort(Protocol):
    """
    Port for fetching wallet balances.

    This is used by the context-aware system to classify users
    by their portfolio value (EMPTY, STARTER, ACTIVE, WHALE).
    """

    async def get_user_balance(self, user_id: int) -> UserWalletAggregate:
        """
        Get aggregated balance for a user across all their wallets.

        Args:
            user_id: Legacy user ID from users table

        Returns:
            UserWalletAggregate with total balance and wallet details
        """
        ...

    async def get_wallet_balance(self, wallet_address: str) -> WalletBalanceSummary:
        """
        Get balance for a specific wallet address.

        Args:
            wallet_address: Blockchain wallet address (0x...)

        Returns:
            WalletBalanceSummary with chain breakdown
        """
        ...

    async def get_user_balance_by_chat_user(
        self,
        chat_user_id: UUID,
    ) -> UserWalletAggregate | None:
        """
        Get aggregated balance for a user via their chat_user_id.

        This resolves chat_user_id → legacy user_id → wallets → balances.

        Args:
            chat_user_id: UUID from chat_users table

        Returns:
            UserWalletAggregate or None if user not found
        """
        ...
