"""
User Context Aware entity for context-aware agent responses.

This entity stores pre-computed user context data that is updated
periodically by a Celery background task. It provides fast access
to user classification data for routing and response customization.
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta, UTC
from decimal import Decimal
from typing import Any
from uuid import UUID, uuid4

from app.domain.chat.enums.portfolio_state import PortfolioState
from app.domain.chat.enums.activity_level import ActivityLevel
from app.domain.chat.enums.user_type import UserType


@dataclass
class UserContextAware:
    """
    User context entity for context-aware agent responses.
    
    This entity aggregates user data from multiple sources:
    - chat_messages (interaction counts)
    - chat_conversations (session counts)
    - wallets (balance, chain)
    - transactions (execution counts)
    
    The data is pre-computed by a Celery task and cached in the
    user_context_aware table for fast access during chat sessions.
    
    Attributes:
        id: Unique identifier for this context record
        chat_user_id: Foreign key to chat_users table (UUID)
        legacy_user_id: Optional foreign key to legacy users table (INTEGER)
        
        Portfolio State:
            portfolio_state: Classified state (empty/starter/active/whale)
            total_balance_usd: Total portfolio value in USD
            token_count: Number of distinct tokens held
            primary_chain: Most used blockchain
            
        Activity Level:
            activity_level: Classified level (very_active/active/etc.)
            last_active_at: Last interaction timestamp
            first_active_at: First interaction timestamp
            chat_sessions_30d: Sessions in last 30 days
            messages_sent_30d: Messages in last 30 days
            
        User Type:
            user_type: Classified type (new_user/casual/trader/etc.)
            
        Execution History:
            swap_count: Total swap operations
            buy_count: Total buy operations
            cashout_count: Total cashout operations
            lending_count: Total lending operations
            money_market_count: Total money market operations
            transfer_count: Total transfer operations
            total_executions: Total successful executions
            failed_executions: Total failed executions
            execution_success_rate: Success rate percentage
            
        Chat Interactions:
            total_conversations: Total conversations
            total_messages: Total messages sent
            shortcuts_used_count: Number of shortcuts used
            multi_step_completed_count: Multi-step workflows completed
            avg_messages_per_session: Average messages per session
            detected_language: Most common language used
            language_history: List of languages used
            most_used_agents: Top agents by usage
            agent_usage_counts: Agent usage counts dict
            
        Wallet Data:
            wallet_count: Number of connected wallets
            has_connected_wallet: Whether any wallet is connected
            primary_wallet_address: Primary wallet address
            wallet_provider: Wallet provider (privy/metamask/etc.)
            
        Processing Metadata:
            context_updated_at: Last context update timestamp
            next_update_eligible_at: When next update is allowed
            update_count: Number of context updates
            created_at: Record creation timestamp
            updated_at: Record update timestamp
    """
    
    # Primary key
    id: UUID = field(default_factory=uuid4)
    
    # Foreign keys
    chat_user_id: UUID = field(default_factory=uuid4)
    legacy_user_id: int | None = None
    
    # ═══════════════════════════════════════════════════════════════
    # PORTFOLIO STATE
    # ═══════════════════════════════════════════════════════════════
    portfolio_state: str = field(default=PortfolioState.EMPTY.value)
    total_balance_usd: Decimal = field(default=Decimal("0.00"))
    token_count: int = 0
    primary_chain: str | None = None
    
    # ═══════════════════════════════════════════════════════════════
    # ACTIVITY LEVEL
    # ═══════════════════════════════════════════════════════════════
    activity_level: str = field(default=ActivityLevel.NEW.value)
    last_active_at: datetime | None = None
    first_active_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    chat_sessions_30d: int = 0
    messages_sent_30d: int = 0
    
    # ═══════════════════════════════════════════════════════════════
    # USER TYPE
    # ═══════════════════════════════════════════════════════════════
    user_type: str = field(default=UserType.NEW_USER.value)
    
    # ═══════════════════════════════════════════════════════════════
    # EXECUTION HISTORY
    # ═══════════════════════════════════════════════════════════════
    swap_count: int = 0
    buy_count: int = 0
    cashout_count: int = 0
    lending_count: int = 0
    money_market_count: int = 0
    transfer_count: int = 0
    total_executions: int = 0
    failed_executions: int = 0
    execution_success_rate: Decimal = field(default=Decimal("0.00"))
    
    # ═══════════════════════════════════════════════════════════════
    # CHAT INTERACTIONS
    # ═══════════════════════════════════════════════════════════════
    total_conversations: int = 0
    total_messages: int = 0
    shortcuts_used_count: int = 0
    multi_step_completed_count: int = 0
    avg_messages_per_session: Decimal = field(default=Decimal("0.00"))
    detected_language: str = "en"
    language_history: list[str] = field(default_factory=list)
    most_used_agents: list[str] = field(default_factory=list)
    agent_usage_counts: dict[str, int] = field(default_factory=dict)
    
    # ═══════════════════════════════════════════════════════════════
    # WALLET DATA
    # ═══════════════════════════════════════════════════════════════
    wallet_count: int = 0
    has_connected_wallet: bool = False
    primary_wallet_address: str | None = None
    wallet_provider: str | None = None
    
    # Wallet balance aggregation (for accurate portfolio_state)
    wallet_total_usd: Decimal = field(default=Decimal("0.00"))
    wallet_chain_breakdown: dict[str, float] = field(default_factory=dict)
    wallet_last_sync_at: datetime | None = None
    
    # ═══════════════════════════════════════════════════════════════
    # PROCESSING METADATA
    # ═══════════════════════════════════════════════════════════════
    context_updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    next_update_eligible_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    update_count: int = 0
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    
    # ═══════════════════════════════════════════════════════════════
    # COMPUTED PROPERTIES
    # ═══════════════════════════════════════════════════════════════
    
    @property
    def portfolio_state_enum(self) -> PortfolioState:
        """Get portfolio state as enum."""
        return PortfolioState(self.portfolio_state)
    
    @property
    def activity_level_enum(self) -> ActivityLevel:
        """Get activity level as enum."""
        return ActivityLevel(self.activity_level)
    
    @property
    def user_type_enum(self) -> UserType:
        """Get user type as enum."""
        return UserType(self.user_type)
    
    @property
    def days_since_registration(self) -> int:
        """Get days since user first registered."""
        return (datetime.now(UTC) - self.first_active_at).days
    
    @property
    def can_execute_swap(self) -> bool:
        """Check if user can execute swap operations."""
        return self.portfolio_state_enum.can_swap
    
    @property
    def can_execute_lending(self) -> bool:
        """Check if user can execute lending operations."""
        return self.portfolio_state_enum.can_lend
    
    @property
    def needs_onboarding(self) -> bool:
        """Check if user needs onboarding guidance."""
        return self.portfolio_state_enum.needs_onboarding
    
    @property
    def is_engaged(self) -> bool:
        """Check if user is considered engaged."""
        return self.activity_level_enum.is_engaged
    
    @property
    def needs_reengagement(self) -> bool:
        """Check if user needs re-engagement."""
        return self.activity_level_enum.needs_reengagement
    
    # ═══════════════════════════════════════════════════════════════
    # METHODS
    # ═══════════════════════════════════════════════════════════════
    
    def recalculate_classifications(self) -> None:
        """
        Recalculate all classification fields based on current data.
        
        Call this after updating metrics to ensure classifications
        are consistent with the underlying data.
        """
        # Portfolio state - use wallet_total_usd if available, else total_balance_usd
        balance_for_classification = self.wallet_total_usd if self.wallet_total_usd > 0 else self.total_balance_usd
        self.portfolio_state = PortfolioState.from_balance(balance_for_classification).value
        
        # Sync total_balance_usd with wallet_total_usd if wallet data is fresher
        if self.wallet_total_usd > 0:
            self.total_balance_usd = self.wallet_total_usd
        
        # Activity level
        was_inactive = self.activity_level == ActivityLevel.INACTIVE.value
        sessions_7d = self.chat_sessions_30d // 4  # Approximate
        self.activity_level = ActivityLevel.calculate(
            days_since_registration=self.days_since_registration,
            sessions_7d=sessions_7d,
            sessions_30d=self.chat_sessions_30d,
            was_inactive=was_inactive,
        ).value
        
        # User type
        self.user_type = UserType.calculate(
            total_messages=self.total_messages,
            total_executions=self.total_executions,
            swap_count=self.swap_count,
            buy_count=self.buy_count,
            lending_count=self.lending_count,
            money_market_count=self.money_market_count,
            cashout_count=self.cashout_count,
            transfer_count=self.transfer_count,
        ).value
    
    def get_combined_prompt_enhancement(self) -> str:
        """
        Get combined LLM prompt enhancement for all classifications.
        
        Returns:
            Combined prompt enhancement string
        """
        parts = []
        
        # Portfolio state enhancement (most important)
        portfolio_enhancement = self.portfolio_state_enum.get_prompt_enhancement()
        if portfolio_enhancement:
            parts.append(portfolio_enhancement)
        
        # Activity level enhancement
        activity_enhancement = self.activity_level_enum.get_prompt_enhancement()
        if activity_enhancement:
            parts.append(activity_enhancement)
        
        # User type enhancement
        user_type_enhancement = self.user_type_enum.get_prompt_enhancement()
        if user_type_enhancement:
            parts.append(user_type_enhancement)
        
        return "\n".join(parts)
    
    def mark_updated(self, cooldown_hours: int = 1) -> None:
        """
        Mark context as updated and set next eligible update time.
        
        Args:
            cooldown_hours: Hours until next update is allowed
        """
        now = datetime.now(UTC)
        self.context_updated_at = now
        self.next_update_eligible_at = now + timedelta(hours=cooldown_hours)
        self.update_count += 1
        self.updated_at = now
    
    def is_eligible_for_update(self) -> bool:
        """Check if context is eligible for update."""
        return datetime.now(UTC) >= self.next_update_eligible_at
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "id": str(self.id),
            "chat_user_id": str(self.chat_user_id),
            "legacy_user_id": self.legacy_user_id,
            "portfolio_state": self.portfolio_state,
            "total_balance_usd": float(self.total_balance_usd),
            "wallet_total_usd": float(self.wallet_total_usd),
            "wallet_chain_breakdown": self.wallet_chain_breakdown,
            "wallet_count": self.wallet_count,
            "token_count": self.token_count,
            "primary_chain": self.primary_chain,
            "activity_level": self.activity_level,
            "user_type": self.user_type,
            "total_executions": self.total_executions,
            "total_messages": self.total_messages,
            "has_connected_wallet": self.has_connected_wallet,
            "primary_wallet_address": self.primary_wallet_address,
            "wallet_last_sync_at": self.wallet_last_sync_at.isoformat() if self.wallet_last_sync_at else None,
            "context_updated_at": self.context_updated_at.isoformat() if self.context_updated_at else None,
        }
    
    def to_context_string(self) -> str:
        """
        Convert to a context string for LLM injection.
        
        Returns:
            Formatted context string for supervisor prompt
        """
        lines = [
            f"**User Context:**",
            f"- Portfolio: {self.portfolio_state.upper()} (${float(self.total_balance_usd):,.2f})",
            f"- Activity: {self.activity_level.replace('_', ' ').title()}",
            f"- Type: {self.user_type.replace('_', ' ').title()}",
        ]
        
        if self.has_connected_wallet and self.primary_wallet_address:
            short_addr = f"{self.primary_wallet_address[:6]}...{self.primary_wallet_address[-4:]}"
            lines.append(f"- Wallet: {short_addr}")
        
        if self.total_executions > 0:
            lines.append(f"- Executions: {self.total_executions} total")
            if self.swap_count > 0:
                lines.append(f"  - Swaps: {self.swap_count}")
            if self.buy_count > 0:
                lines.append(f"  - Buys: {self.buy_count}")
            if self.lending_count > 0:
                lines.append(f"  - Lending: {self.lending_count}")
        
        return "\n".join(lines)
