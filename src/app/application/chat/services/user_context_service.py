"""
User Context Service for Context-Aware Agents.

This service manages user context data used for context-aware agent responses.
It aggregates data from multiple sources and maintains the user_context_aware table.

Key responsibilities:
1. Create context for new users (called from privy-login)
2. Update context periodically (called from Celery task)
3. Provide context for chat sessions
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta, UTC
from decimal import Decimal
from typing import Any
from uuid import UUID

from app.domain.chat.entities.user_context_aware import UserContextAware
from app.domain.chat.enums.portfolio_state import PortfolioState
from app.domain.chat.enums.activity_level import ActivityLevel
from app.domain.chat.enums.user_type import UserType
from app.domain.chat.ports.user_context_repository import UserContextRepository

logger = logging.getLogger(__name__)


@dataclass
class ChatStats:
    """Aggregated chat statistics for a user."""
    
    conversation_count: int = 0
    message_count: int = 0
    messages_7d: int = 0
    messages_30d: int = 0
    sessions_7d: int = 0
    sessions_30d: int = 0
    shortcuts_used: int = 0
    multi_step_completed: int = 0
    avg_messages_per_session: Decimal = field(default=Decimal("0.00"))
    last_message_at: datetime | None = None
    most_common_language: str = "en"
    agent_usage_top_5: list[str] = field(default_factory=list)
    agent_usage_counts: dict[str, int] = field(default_factory=dict)


@dataclass
class ExecutionStats:
    """Aggregated execution statistics for a user."""
    
    swap_count: int = 0
    buy_count: int = 0
    cashout_count: int = 0
    lending_count: int = 0
    money_market_count: int = 0
    transfer_count: int = 0
    total: int = 0
    failed: int = 0
    success_rate: Decimal = field(default=Decimal("0.00"))


@dataclass
class WalletStats:
    """Aggregated wallet statistics for a user."""
    
    wallet_count: int = 0
    has_wallet: bool = False
    primary_address: str | None = None
    provider: str | None = None
    primary_chain: str | None = None
    total_balance_usd: Decimal = field(default=Decimal("0.00"))
    token_count: int = 0
    chain_breakdown: dict[str, float] = field(default_factory=dict)
    last_sync_at: datetime | None = None


class UserContextService:
    """
    Service for managing user context awareness data.
    
    This service:
    1. Creates context for new users during privy-login
    2. Updates context periodically via Celery task
    3. Provides context for authenticated supervisor
    
    Usage:
        service = UserContextService(context_repo, chat_repo, wallet_repo)
        
        # For new users (privy-login)
        context = await service.create_for_new_user(chat_user_id, ...)
        
        # For Celery task
        users = await service.get_users_for_update(limit=100)
        for user in users:
            await service.update_user_context(user.chat_user_id)
        
        # For chat sessions
        context = await service.get_context(chat_user_id)
    """
    
    def __init__(
        self,
        context_repository: UserContextRepository,
        # Optional repositories for aggregation (can be None)
        chat_message_repository: Any | None = None,
        chat_conversation_repository: Any | None = None,
        wallet_repository: Any | None = None,
        # Wallet balance adapter (for accurate portfolio_state)
        wallet_balance_adapter: Any | None = None,
    ):
        """
        Initialize service with repositories.
        
        Args:
            context_repository: Required - UserContextRepository for persistence
            chat_message_repository: Optional - For aggregating chat stats
            chat_conversation_repository: Optional - For aggregating session stats
            wallet_repository: Optional - For aggregating wallet/balance stats
            wallet_balance_adapter: Optional - WalletBalancePort for balance aggregation
        """
        self._context_repo = context_repository
        self._chat_message_repo = chat_message_repository
        self._chat_conversation_repo = chat_conversation_repository
        self._wallet_repo = wallet_repository
        self._wallet_balance_adapter = wallet_balance_adapter
    
    # ═══════════════════════════════════════════════════════════════
    # CONTEXT RETRIEVAL
    # ═══════════════════════════════════════════════════════════════
    
    async def get_context(self, chat_user_id: UUID) -> UserContextAware | None:
        """
        Get user context by chat user ID.
        
        Args:
            chat_user_id: The chat user's UUID
            
        Returns:
            UserContextAware entity or None if not found
        """
        return await self._context_repo.get_by_chat_user_id(chat_user_id)
    
    async def get_context_by_legacy_id(self, legacy_user_id: int) -> UserContextAware | None:
        """
        Get user context by legacy user ID.
        
        Args:
            legacy_user_id: The legacy user's INTEGER ID
            
        Returns:
            UserContextAware entity or None if not found
        """
        return await self._context_repo.get_by_legacy_user_id(legacy_user_id)
    
    async def exists(self, chat_user_id: UUID) -> bool:
        """
        Check if context exists for a chat user.
        
        Args:
            chat_user_id: The chat user's UUID
            
        Returns:
            True if context exists
        """
        return await self._context_repo.exists_for_chat_user(chat_user_id)
    
    # ═══════════════════════════════════════════════════════════════
    # CONTEXT CREATION (for privy-login)
    # ═══════════════════════════════════════════════════════════════
    
    async def create_for_new_user(
        self,
        chat_user_id: UUID,
        legacy_user_id: int | None = None,
        wallet_address: str | None = None,
        wallet_provider: str | None = None,
        language: str = "en",
    ) -> UserContextAware:
        """
        Create context entry for a new user.
        
        Called from privy-login endpoint when a new user registers.
        Initializes with default values (empty portfolio, new user type).
        
        Args:
            chat_user_id: The chat user's UUID (from chat_users table)
            legacy_user_id: Optional legacy user ID (from users table)
            wallet_address: Optional wallet address if connected
            wallet_provider: Optional wallet provider (privy, metamask, etc.)
            language: User's preferred language (default: en)
            
        Returns:
            Created UserContextAware entity
        """
        now = datetime.now(UTC)
        
        context = UserContextAware(
            chat_user_id=chat_user_id,
            legacy_user_id=legacy_user_id,
            # Portfolio state - empty for new users
            portfolio_state=PortfolioState.EMPTY.value,
            total_balance_usd=Decimal("0.00"),
            token_count=0,
            primary_chain=None,
            # Activity level - new for new users
            activity_level=ActivityLevel.NEW.value,
            last_active_at=now,
            first_active_at=now,
            chat_sessions_30d=0,
            messages_sent_30d=0,
            # User type - new user
            user_type=UserType.NEW_USER.value,
            # Execution history - all zeros
            swap_count=0,
            buy_count=0,
            cashout_count=0,
            lending_count=0,
            money_market_count=0,
            transfer_count=0,
            total_executions=0,
            failed_executions=0,
            execution_success_rate=Decimal("0.00"),
            # Chat interactions - all zeros
            total_conversations=0,
            total_messages=0,
            shortcuts_used_count=0,
            multi_step_completed_count=0,
            avg_messages_per_session=Decimal("0.00"),
            detected_language=language,
            language_history=[language],
            most_used_agents=[],
            agent_usage_counts={},
            # Wallet data
            wallet_count=1 if wallet_address else 0,
            has_connected_wallet=wallet_address is not None,
            primary_wallet_address=wallet_address,
            wallet_provider=wallet_provider,
            # Processing metadata
            context_updated_at=now,
            next_update_eligible_at=now + timedelta(hours=1),
            update_count=0,
            created_at=now,
            updated_at=now,
        )
        
        saved = await self._context_repo.save(context)
        
        logger.info(
            f"✅ Created user context for new user",
            extra={
                "chat_user_id": str(chat_user_id),
                "has_wallet": wallet_address is not None,
            }
        )
        
        return saved
    
    # ═══════════════════════════════════════════════════════════════
    # CONTEXT UPDATE (for Celery task)
    # ═══════════════════════════════════════════════════════════════
    
    async def get_users_for_update(
        self,
        limit: int = 100,
        cooldown_hours: int = 1,
    ) -> list[UserContextAware]:
        """
        Get users eligible for context update.
        
        Returns users where next_update_eligible_at is in the past,
        ordered by oldest update first.
        
        Args:
            limit: Maximum users to return (default: 100)
            cooldown_hours: Hours since last update to be eligible (default: 1)
            
        Returns:
            List of UserContextAware entities eligible for update
        """
        cutoff = datetime.now(UTC)
        return await self._context_repo.get_eligible_for_update(
            before=cutoff,
            limit=limit,
        )
    
    async def update_user_context(
        self,
        chat_user_id: UUID,
        cooldown_hours: int = 1,
    ) -> UserContextAware | None:
        """
        Update context for a single user.
        
        Aggregates data from multiple sources:
        - chat_messages (interaction counts)
        - chat_conversations (session counts)
        - wallets (balance, chain)
        - message metadata (execution counts)
        
        Args:
            chat_user_id: The chat user's UUID
            cooldown_hours: Hours until next update eligible (default: 1)
            
        Returns:
            Updated UserContextAware entity, or None if user not found
        """
        # Get existing context
        context = await self._context_repo.get_by_chat_user_id(chat_user_id)
        if not context:
            logger.warning(f"No context found for chat_user_id={chat_user_id}")
            return None
        
        try:
            # Aggregate chat stats
            chat_stats = await self._aggregate_chat_stats(chat_user_id)
            
            # Update chat interaction fields
            context.total_conversations = chat_stats.conversation_count
            context.total_messages = chat_stats.message_count
            context.messages_sent_30d = chat_stats.messages_30d
            context.chat_sessions_30d = chat_stats.sessions_30d
            context.shortcuts_used_count = chat_stats.shortcuts_used
            context.multi_step_completed_count = chat_stats.multi_step_completed
            context.avg_messages_per_session = chat_stats.avg_messages_per_session
            context.most_used_agents = chat_stats.agent_usage_top_5
            context.agent_usage_counts = chat_stats.agent_usage_counts
            context.detected_language = chat_stats.most_common_language
            
            if chat_stats.last_message_at:
                context.last_active_at = chat_stats.last_message_at
            
            # Aggregate wallet stats (including balance from WalletBalancePort)
            wallet_stats = await self._aggregate_wallet_stats(chat_user_id)
            context.wallet_count = wallet_stats.wallet_count
            context.has_connected_wallet = wallet_stats.has_wallet
            context.primary_wallet_address = wallet_stats.primary_address
            context.wallet_provider = wallet_stats.provider
            context.primary_chain = wallet_stats.primary_chain
            context.token_count = wallet_stats.token_count
            
            # Wallet balance aggregation (from WalletBalancePort)
            context.wallet_total_usd = wallet_stats.total_balance_usd
            context.wallet_chain_breakdown = wallet_stats.chain_breakdown
            context.wallet_last_sync_at = wallet_stats.last_sync_at
            
            # Sync total_balance_usd with wallet_total_usd
            if wallet_stats.total_balance_usd > 0:
                context.total_balance_usd = wallet_stats.total_balance_usd
            
            # Aggregate execution stats from message metadata
            exec_stats = await self._aggregate_execution_stats(chat_user_id)
            context.swap_count = exec_stats.swap_count
            context.buy_count = exec_stats.buy_count
            context.cashout_count = exec_stats.cashout_count
            context.lending_count = exec_stats.lending_count
            context.money_market_count = exec_stats.money_market_count
            context.transfer_count = exec_stats.transfer_count
            context.total_executions = exec_stats.total
            context.failed_executions = exec_stats.failed
            context.execution_success_rate = exec_stats.success_rate
            
            # Recalculate classifications
            was_inactive = context.activity_level == ActivityLevel.INACTIVE.value
            
            context.portfolio_state = PortfolioState.from_balance(
                context.total_balance_usd
            ).value
            
            context.activity_level = ActivityLevel.calculate(
                days_since_registration=context.days_since_registration,
                sessions_7d=chat_stats.sessions_7d,
                sessions_30d=context.chat_sessions_30d,
                was_inactive=was_inactive,
            ).value
            
            context.user_type = UserType.calculate(
                total_messages=context.total_messages,
                total_executions=context.total_executions,
                swap_count=context.swap_count,
                buy_count=context.buy_count,
                lending_count=context.lending_count,
                money_market_count=context.money_market_count,
                cashout_count=context.cashout_count,
                transfer_count=context.transfer_count,
            ).value
            
            # Mark updated with cooldown
            context.mark_updated(cooldown_hours=cooldown_hours)
            
            # Save
            saved = await self._context_repo.save(context)
            
            logger.debug(
                f"Updated user context",
                extra={
                    "chat_user_id": str(chat_user_id),
                    "portfolio_state": saved.portfolio_state,
                    "activity_level": saved.activity_level,
                    "user_type": saved.user_type,
                }
            )
            
            return saved
            
        except Exception as e:
            logger.error(f"Failed to update context for {chat_user_id}: {e}")
            return None
    
    # ═══════════════════════════════════════════════════════════════
    # AGGREGATION HELPERS
    # ═══════════════════════════════════════════════════════════════
    
    async def _aggregate_chat_stats(self, chat_user_id: UUID) -> ChatStats:
        """
        Aggregate chat statistics for a user.
        
        Queries chat_messages and chat_conversations tables.
        """
        stats = ChatStats()
        
        # If no chat repos, return defaults
        if not self._chat_message_repo or not self._chat_conversation_repo:
            return stats
        
        try:
            # Get conversation count
            conversations = await self._chat_conversation_repo.get_by_user_id(
                user_id=chat_user_id,
                limit=1000,
            )
            stats.conversation_count = len(conversations) if conversations else 0
            
            # Get message stats from messages
            # Note: This is a simplified implementation
            # In production, you'd use aggregate queries
            if hasattr(self._chat_message_repo, 'get_user_stats'):
                msg_stats = await self._chat_message_repo.get_user_stats(chat_user_id)
                if msg_stats:
                    stats.message_count = msg_stats.get('total', 0)
                    stats.messages_7d = msg_stats.get('last_7d', 0)
                    stats.messages_30d = msg_stats.get('last_30d', 0)
                    stats.last_message_at = msg_stats.get('last_at')
            
            # Calculate sessions (approximate from conversations)
            stats.sessions_30d = stats.conversation_count
            stats.sessions_7d = stats.conversation_count // 4  # Rough estimate
            
            # Calculate average messages per session
            if stats.conversation_count > 0:
                stats.avg_messages_per_session = Decimal(
                    str(stats.message_count / stats.conversation_count)
                ).quantize(Decimal("0.01"))
                
        except Exception as e:
            logger.warning(f"Failed to aggregate chat stats: {e}")
        
        return stats
    
    async def _aggregate_wallet_stats(self, chat_user_id: UUID) -> WalletStats:
        """
        Aggregate wallet statistics for a user.
        
        Uses WalletBalancePort if available for accurate balance data,
        otherwise falls back to basic wallet repository queries.
        """
        stats = WalletStats()
        
        # Try wallet balance adapter first (preferred - has balance data)
        if self._wallet_balance_adapter:
            try:
                aggregate = await self._wallet_balance_adapter.get_user_balance_by_chat_user(
                    chat_user_id
                )
                
                if aggregate:
                    stats.wallet_count = aggregate.wallet_count
                    stats.has_wallet = aggregate.wallet_count > 0
                    stats.primary_address = aggregate.primary_wallet_address
                    stats.total_balance_usd = aggregate.total_balance_usd
                    stats.last_sync_at = aggregate.last_sync_at
                    
                    # Chain breakdown as dict[str, float]
                    stats.chain_breakdown = {
                        chain: float(balance)
                        for chain, balance in aggregate.chain_breakdown.items()
                    }
                    
                    # Get primary chain (highest balance)
                    if aggregate.chain_breakdown:
                        stats.primary_chain = max(
                            aggregate.chain_breakdown,
                            key=lambda x: aggregate.chain_breakdown[x]
                        )
                    
                    # Count tokens from chain addresses
                    stats.token_count = sum(
                        w.token_count for w in aggregate.wallets
                    ) if aggregate.wallets else 0
                    
                    logger.debug(
                        f"Aggregated wallet balance for {chat_user_id}: "
                        f"${float(stats.total_balance_usd):,.2f}"
                    )
                    return stats
                    
            except Exception as e:
                logger.warning(f"Wallet balance adapter failed: {e}")
                # Fall through to basic wallet repo
        
        # Fallback: basic wallet repository (no balance data)
        if not self._wallet_repo:
            return stats
        
        try:
            # Note: wallet_repo uses UserId, but we have chat_user_id (UUID)
            # Try to use get_by_chat_user_id if available
            
            if hasattr(self._wallet_repo, 'get_by_chat_user_id'):
                wallets = await self._wallet_repo.get_by_chat_user_id(chat_user_id)
            else:
                wallets = []
            
            stats.wallet_count = len(wallets) if wallets else 0
            stats.has_wallet = stats.wallet_count > 0
            
            if wallets:
                # Get primary wallet (first one or marked as primary)
                primary = wallets[0]
                for w in wallets:
                    if getattr(w, 'is_primary', False):
                        primary = w
                        break
                
                stats.primary_address = getattr(primary, 'address', None)
                stats.provider = getattr(primary, 'provider', None)
                stats.primary_chain = getattr(primary, 'chain_type', None)
                
                # No balance data from basic wallet repo
                stats.total_balance_usd = Decimal("0.00")
                stats.token_count = 0
                
        except Exception as e:
            logger.warning(f"Failed to aggregate wallet stats: {e}")
        
        return stats
    
    async def _aggregate_execution_stats(self, chat_user_id: UUID) -> ExecutionStats:
        """
        Aggregate execution statistics from message metadata.
        
        Counts workflow completions from chat_messages metadata.
        """
        stats = ExecutionStats()
        
        if not self._chat_message_repo:
            return stats
        
        try:
            # Check if repo has execution stats method
            if hasattr(self._chat_message_repo, 'get_execution_stats'):
                exec_data = await self._chat_message_repo.get_execution_stats(chat_user_id)
                if exec_data:
                    stats.swap_count = exec_data.get('swap', 0)
                    stats.buy_count = exec_data.get('buy', 0)
                    stats.cashout_count = exec_data.get('cashout', 0)
                    stats.lending_count = exec_data.get('lending', 0)
                    stats.money_market_count = exec_data.get('money_market', 0)
                    stats.transfer_count = exec_data.get('transfer', 0)
                    stats.total = exec_data.get('total', 0)
                    stats.failed = exec_data.get('failed', 0)
            
            # Calculate success rate
            if stats.total > 0:
                success = stats.total - stats.failed
                stats.success_rate = Decimal(
                    str((success / stats.total) * 100)
                ).quantize(Decimal("0.01"))
                
        except Exception as e:
            logger.warning(f"Failed to aggregate execution stats: {e}")
        
        return stats
    
    # ═══════════════════════════════════════════════════════════════
    # ANALYTICS
    # ═══════════════════════════════════════════════════════════════
    
    async def get_distribution_stats(self) -> dict[str, dict[str, int]]:
        """
        Get distribution of users by classification.
        
        Returns:
            Dictionary with counts by portfolio_state, activity_level, user_type
        """
        return {
            "portfolio_state": await self._context_repo.count_by_portfolio_state(),
            "activity_level": await self._context_repo.count_by_activity_level(),
            "user_type": await self._context_repo.count_by_user_type(),
        }
    
    async def get_inactive_users(
        self,
        days_inactive: int = 30,
        limit: int = 100,
    ) -> list[UserContextAware]:
        """
        Get inactive users for re-engagement.
        
        Args:
            days_inactive: Minimum days since last activity
            limit: Maximum users to return
            
        Returns:
            List of inactive UserContextAware entities
        """
        return await self._context_repo.get_inactive_users(
            days_inactive=days_inactive,
            limit=limit,
        )
