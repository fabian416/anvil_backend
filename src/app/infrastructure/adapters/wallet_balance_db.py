"""
Database-based Wallet Balance Adapter.

Fetches wallet balances from local database tables:
- wallets: User wallet associations
- chain_addresses: Per-chain balances (balance_usd)
- portfolio_snapshots: Historical snapshots with total_usd

This adapter provides balance data for the context-aware agents
to classify users by their portfolio value.
"""

import logging
from datetime import datetime, UTC
from decimal import Decimal
from uuid import UUID

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.chat.ports.wallet_balance import (
    WalletBalancePort,
    ChainBalance,
    WalletBalanceSummary,
    UserWalletAggregate,
)
from app.infrastructure.persistence_sqla.registry import mapping_registry

logger = logging.getLogger(__name__)


class WalletBalanceDbAdapter(WalletBalancePort):
    """
    SQLAlchemy-based implementation of WalletBalancePort.
    
    Aggregates wallet balances from:
    1. chain_addresses.balance_usd (per-chain balances)
    2. portfolio_snapshots.total_usd (if chain_addresses empty)
    """
    
    def __init__(self, session: AsyncSession):
        self._session = session
    
    async def get_user_balance(self, user_id: int) -> UserWalletAggregate:
        """Get aggregated balance for a user across all wallets."""
        wallets_table = mapping_registry.metadata.tables.get("wallets")
        chain_addresses_table = mapping_registry.metadata.tables.get("chain_addresses")
        
        if wallets_table is None:
            logger.warning("wallets table not found")
            return UserWalletAggregate(user_id=user_id)
        
        # Get all wallets for this user
        wallets_stmt = (
            select(
                wallets_table.c.id,
                wallets_table.c.address,
                wallets_table.c.default_chain,
                wallets_table.c.provider,
            )
            .where(wallets_table.c.user_id == user_id)
            .where(wallets_table.c.status == 1)  # ACTIVE status
        )
        
        result = await self._session.execute(wallets_stmt)
        wallet_rows = result.fetchall()
        
        if not wallet_rows:
            return UserWalletAggregate(user_id=user_id, wallet_count=0)
        
        wallet_summaries: list[WalletBalanceSummary] = []
        total_balance = Decimal("0")
        primary_wallet_address: str | None = None
        max_balance = Decimal("-1")
        
        for wallet_row in wallet_rows:
            wallet_id = wallet_row[0]
            wallet_address = wallet_row[1]
            
            # Get chain balances for this wallet
            chain_balances: list[ChainBalance] = []
            wallet_total = Decimal("0")
            
            if chain_addresses_table is not None:
                chain_stmt = (
                    select(
                        chain_addresses_table.c.chain,
                        chain_addresses_table.c.balance_usd,
                        chain_addresses_table.c.last_balance_update,
                    )
                    .where(chain_addresses_table.c.wallet_id == wallet_id)
                    .where(chain_addresses_table.c.is_active == True)
                )
                
                chain_result = await self._session.execute(chain_stmt)
                chain_rows = chain_result.fetchall()
                
                for chain_row in chain_rows:
                    chain_name = str(chain_row[0]) if chain_row[0] else "unknown"
                    balance = Decimal(str(chain_row[1])) if chain_row[1] else Decimal("0")
                    last_updated = chain_row[2]
                    
                    chain_balances.append(ChainBalance(
                        chain=chain_name,
                        balance_usd=balance,
                        last_updated=last_updated,
                    ))
                    wallet_total += balance
            
            # If no chain_addresses, try portfolio_snapshots
            if not chain_balances:
                wallet_total = await self._get_latest_snapshot_balance(wallet_id)
            
            wallet_summary = WalletBalanceSummary(
                wallet_address=wallet_address,
                total_balance_usd=wallet_total,
                chain_balances=chain_balances,
                token_count=len(chain_balances),
            )
            wallet_summaries.append(wallet_summary)
            
            total_balance += wallet_total
            
            # Track primary wallet (highest balance)
            if wallet_total > max_balance:
                max_balance = wallet_total
                primary_wallet_address = wallet_address
        
        return UserWalletAggregate(
            user_id=user_id,
            total_balance_usd=total_balance,
            wallet_count=len(wallet_summaries),
            wallets=wallet_summaries,
            primary_wallet_address=primary_wallet_address,
            last_sync_at=datetime.now(UTC),
        )
    
    async def get_wallet_balance(self, wallet_address: str) -> WalletBalanceSummary:
        """Get balance for a specific wallet address."""
        wallets_table = mapping_registry.metadata.tables.get("wallets")
        chain_addresses_table = mapping_registry.metadata.tables.get("chain_addresses")
        
        if wallets_table is None:
            return WalletBalanceSummary(
                wallet_address=wallet_address,
                total_balance_usd=Decimal("0"),
            )
        
        # Find wallet by address
        wallet_stmt = (
            select(wallets_table.c.id)
            .where(wallets_table.c.address == wallet_address.lower())
            .limit(1)
        )
        
        result = await self._session.execute(wallet_stmt)
        wallet_row = result.fetchone()
        
        if not wallet_row:
            return WalletBalanceSummary(
                wallet_address=wallet_address,
                total_balance_usd=Decimal("0"),
            )
        
        wallet_id = wallet_row[0]
        chain_balances: list[ChainBalance] = []
        wallet_total = Decimal("0")
        
        if chain_addresses_table is not None:
            chain_stmt = (
                select(
                    chain_addresses_table.c.chain,
                    chain_addresses_table.c.balance_usd,
                    chain_addresses_table.c.last_balance_update,
                )
                .where(chain_addresses_table.c.wallet_id == wallet_id)
                .where(chain_addresses_table.c.is_active == True)
            )
            
            chain_result = await self._session.execute(chain_stmt)
            chain_rows = chain_result.fetchall()
            
            for chain_row in chain_rows:
                chain_name = str(chain_row[0]) if chain_row[0] else "unknown"
                balance = Decimal(str(chain_row[1])) if chain_row[1] else Decimal("0")
                last_updated = chain_row[2]
                
                chain_balances.append(ChainBalance(
                    chain=chain_name,
                    balance_usd=balance,
                    last_updated=last_updated,
                ))
                wallet_total += balance
        
        # Fallback to portfolio snapshots
        if not chain_balances:
            wallet_total = await self._get_latest_snapshot_balance(wallet_id)
        
        return WalletBalanceSummary(
            wallet_address=wallet_address,
            total_balance_usd=wallet_total,
            chain_balances=chain_balances,
            token_count=len(chain_balances),
            last_sync_at=datetime.now(UTC),
        )
    
    async def get_user_balance_by_chat_user(
        self,
        chat_user_id: UUID,
    ) -> UserWalletAggregate | None:
        """Get aggregated balance via chat_user_id."""
        chat_users_table = mapping_registry.metadata.tables.get("chat_users")
        
        if chat_users_table is None:
            logger.warning("chat_users table not found")
            return None
        
        # Resolve chat_user_id to legacy user_id via identifier column
        # chat_users.identifier contains the legacy user ID for authenticated users
        stmt = (
            select(chat_users_table.c.identifier, chat_users_table.c.user_type)
            .where(chat_users_table.c.id == chat_user_id)
        )
        
        result = await self._session.execute(stmt)
        row = result.fetchone()
        
        if not row or row[0] is None:
            logger.debug(f"No identifier found for chat_user_id={chat_user_id}")
            return None
        
        identifier = row[0]
        user_type = row[1]
        
        # Only authenticated users have legacy user IDs
        if user_type != "authenticated":
            logger.debug(f"chat_user_id={chat_user_id} is not authenticated (type={user_type})")
            return None
        
        # identifier is the legacy user ID as string
        try:
            legacy_user_id = int(identifier)
        except (ValueError, TypeError):
            logger.warning(f"Invalid identifier '{identifier}' for chat_user_id={chat_user_id}")
            return None
        
        # Get balance using legacy user_id
        aggregate = await self.get_user_balance(legacy_user_id)
        aggregate = UserWalletAggregate(
            user_id=aggregate.user_id,
            chat_user_id=chat_user_id,
            total_balance_usd=aggregate.total_balance_usd,
            wallet_count=aggregate.wallet_count,
            wallets=aggregate.wallets,
            primary_wallet_address=aggregate.primary_wallet_address,
            last_sync_at=aggregate.last_sync_at,
        )
        
        return aggregate
    
    async def _get_latest_snapshot_balance(self, wallet_id: int) -> Decimal:
        """Get the latest portfolio snapshot total for a wallet."""
        snapshots_table = mapping_registry.metadata.tables.get("portfolio_snapshots")
        
        if snapshots_table is None:
            return Decimal("0")
        
        # Get sum of latest snapshots per chain
        stmt = (
            select(func.sum(snapshots_table.c.total_usd))
            .where(snapshots_table.c.wallet_id == wallet_id)
            .where(
                snapshots_table.c.captured_at == (
                    select(func.max(snapshots_table.c.captured_at))
                    .where(snapshots_table.c.wallet_id == wallet_id)
                    .scalar_subquery()
                )
            )
        )
        
        result = await self._session.execute(stmt)
        total = result.scalar()
        
        return Decimal(str(total)) if total else Decimal("0")
