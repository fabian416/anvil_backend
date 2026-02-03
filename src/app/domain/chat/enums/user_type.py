"""
User type classification for context-aware agents.

Classifies users based on their behavior patterns and execution history.
"""

from enum import Enum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.domain.chat.entities.user_context_aware import UserContextAware


class UserType(Enum):
    """
    User type classification based on behavior patterns.

    Types:
        NEW_USER: Less than 5 total interactions
        CASUAL: Uses chat for questions, rarely executes transactions
        TRADER: Primarily swaps and buys
        YIELD_FARMER: Focuses on lending/money market operations
        POWER_USER: High activity across all categories
    """

    NEW_USER = "new_user"
    CASUAL = "casual"
    TRADER = "trader"
    YIELD_FARMER = "yield_farmer"
    POWER_USER = "power_user"

    @classmethod
    def calculate(
        cls,
        total_messages: int,
        total_executions: int,
        swap_count: int,
        buy_count: int,
        lending_count: int,
        money_market_count: int,
        cashout_count: int = 0,
        transfer_count: int = 0,
    ) -> "UserType":
        """
        Calculate user type from interaction and execution metrics.

        Args:
            total_messages: Total chat messages sent
            total_executions: Total successful executions
            swap_count: Number of swap operations
            buy_count: Number of buy operations
            lending_count: Number of lending operations
            money_market_count: Number of money market operations
            cashout_count: Number of cashout operations
            transfer_count: Number of transfer operations

        Returns:
            UserType classification
        """
        # New users: < 5 total interactions
        if total_messages < 5:
            return cls.NEW_USER

        # Count execution categories used
        execution_types = sum([
            1 if swap_count > 0 else 0,
            1 if buy_count > 0 else 0,
            1 if lending_count > 0 else 0,
            1 if money_market_count > 0 else 0,
            1 if cashout_count > 0 else 0,
            1 if transfer_count > 0 else 0,
        ])

        # Power users: 3+ execution types AND 10+ total executions
        if execution_types >= 3 and total_executions >= 10:
            return cls.POWER_USER

        # Yield farmers: primarily lending/money market
        defi_executions = lending_count + money_market_count
        trading_executions = swap_count + buy_count

        if defi_executions > trading_executions and defi_executions >= 3:
            return cls.YIELD_FARMER

        # Traders: primarily swaps/buys
        if trading_executions >= 3:
            return cls.TRADER

        # Default: casual user (mostly chat, few executions)
        return cls.CASUAL

    @classmethod
    def from_context(cls, context: "UserContextAware") -> "UserType":
        """
        Calculate user type from UserContextAware entity.

        Args:
            context: User context entity with all metrics

        Returns:
            UserType classification
        """
        return cls.calculate(
            total_messages=context.total_messages,
            total_executions=context.total_executions,
            swap_count=context.swap_count,
            buy_count=context.buy_count,
            lending_count=context.lending_count,
            money_market_count=context.money_market_count,
            cashout_count=context.cashout_count,
            transfer_count=context.transfer_count,
        )

    @property
    def is_execution_focused(self) -> bool:
        """Check if user type is focused on executing transactions."""
        return self in (UserType.TRADER, UserType.YIELD_FARMER, UserType.POWER_USER)

    @property
    def prefers_defi(self) -> bool:
        """Check if user prefers DeFi operations."""
        return self in (UserType.YIELD_FARMER, UserType.POWER_USER)

    @property
    def prefers_trading(self) -> bool:
        """Check if user prefers trading operations."""
        return self in (UserType.TRADER, UserType.POWER_USER)

    def get_prompt_enhancement(self) -> str:
        """Get LLM prompt enhancement for this user type."""
        enhancements = {
            UserType.NEW_USER: """
🆕 NEW USER (< 5 interactions):
- Be extra helpful and patient
- Explain DeFi concepts
- Guide step by step
- Suggest simple first actions
""",
            UserType.CASUAL: """
💬 CASUAL USER (Chat-focused):
- Answer questions thoroughly
- Educational approach
- Don't push transactions
- Respect their pace
""",
            UserType.TRADER: """
📈 TRADER (Swap/Buy focused):
- Emphasize price and timing
- Show slippage and fees clearly
- Quick execution is priority
- Suggest trading opportunities
""",
            UserType.YIELD_FARMER: """
🌾 YIELD FARMER (DeFi focused):
- Prioritize APY comparisons
- Highlight new yield opportunities
- Warn about impermanent loss risks
- Track lending positions
- Suggest protocol diversification
""",
            UserType.POWER_USER: """
🚀 POWER USER (Multi-category):
- Minimal hand-holding needed
- Show advanced analytics
- Suggest cross-protocol strategies
- Multi-step workflow optimization
- Assume high DeFi knowledge
""",
        }
        return enhancements.get(self, "")
