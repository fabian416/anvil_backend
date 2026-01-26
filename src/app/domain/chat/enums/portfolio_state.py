"""
Portfolio state classification for context-aware agents.

Classifies users based on their total portfolio value in USD.
"""

from decimal import Decimal
from enum import Enum


class PortfolioState(Enum):
    """
    Portfolio state classification based on total balance.
    
    States:
        EMPTY: $0 total value - needs onboarding, can't swap/lend
        STARTER: $0.01 - $99.99 - new user, warn about gas costs
        ACTIVE: $100 - $9,999.99 - regular user, full features
        WHALE: $10,000+ - high value, advanced strategies
    """
    
    EMPTY = "empty"
    STARTER = "starter"
    ACTIVE = "active"
    WHALE = "whale"
    
    @classmethod
    def from_balance(cls, balance_usd: Decimal | float | int) -> "PortfolioState":
        """
        Classify portfolio state from USD balance.
        
        Args:
            balance_usd: Total portfolio value in USD
            
        Returns:
            PortfolioState classification
        """
        balance = Decimal(str(balance_usd)) if not isinstance(balance_usd, Decimal) else balance_usd
        
        if balance <= 0:
            return cls.EMPTY
        if balance < 100:
            return cls.STARTER
        if balance < 10000:
            return cls.ACTIVE
        return cls.WHALE
    
    @property
    def can_swap(self) -> bool:
        """Check if user can perform swap operations."""
        return self != PortfolioState.EMPTY
    
    @property
    def can_lend(self) -> bool:
        """Check if user can perform lending operations."""
        return self != PortfolioState.EMPTY
    
    @property
    def needs_onboarding(self) -> bool:
        """Check if user needs onboarding guidance."""
        return self == PortfolioState.EMPTY
    
    @property
    def warn_gas_costs(self) -> bool:
        """Check if gas costs warning is relevant."""
        return self == PortfolioState.STARTER
    
    def get_prompt_enhancement(self) -> str:
        """Get LLM prompt enhancement for this state."""
        enhancements = {
            PortfolioState.EMPTY: """
⚠️ USER HAS EMPTY PORTFOLIO:
- Route swap/transfer/lending requests to their respective workflow agents
- The workflow agents will handle insufficient funds with helpful recommendations
- Do NOT redirect swap requests to buy_workflow - let swap_workflow handle it
- Be encouraging and educational
""",
            PortfolioState.STARTER: """
⚠️ USER IS NEW (< $100 portfolio):
- Suggest small, safe operations
- Warn about gas costs relative to balance
- Prioritize education alongside actions
- Consider if gas makes operation worthwhile
""",
            PortfolioState.ACTIVE: """
✅ USER HAS ACTIVE PORTFOLIO ($100-$10k):
- Full feature access
- Provide optimization suggestions
- Consider diversification recommendations
- Suggest yield opportunities based on holdings
""",
            PortfolioState.WHALE: """
✅ HIGH-VALUE USER (> $10k):
- Emphasize slippage protection for large trades
- Suggest gas optimization strategies
- Recommend advanced DeFi strategies
- Consider cross-chain opportunities
- Mention tax implications for large trades
""",
        }
        return enhancements.get(self, "")
