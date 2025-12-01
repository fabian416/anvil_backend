"""
PortfolioAgent - Handles portfolio viewing and analysis operations.
"""

from typing import List, Dict, Any, Optional

from app.infrastructure.agents.base_defi_agent import BaseDeFiAgent


class PortfolioAgent(BaseDeFiAgent):
    """
    Specialized agent for portfolio management and viewing.
    
    Capabilities:
    - View wallet balances
    - Show position summaries
    - Track portfolio performance
    - Analyze asset allocation
    - Provide portfolio insights
    """
    
    def __init__(self, model: str = "gpt-4-turbo"):
        """Initialize PortfolioAgent."""
        
        name = "PortfolioAgent"
        description = "Specialized agent for portfolio viewing and analysis"
        
        instructions = [
            "You are a DeFi portfolio analyst that helps users track and understand their holdings.",
            "Your role is to provide clear, actionable insights about their crypto portfolio.",
            "",
            "Key capabilities:",
            "1. View balances: Show token balances across wallets",
            "2. Position summary: Display active positions and their status",
            "3. Performance tracking: Calculate gains/losses over time",
            "4. Asset allocation: Show portfolio distribution",
            "5. Insights: Provide recommendations based on portfolio state",
            "",
            "Portfolio display guidelines:",
            "- Group by asset type (tokens, positions, LP tokens)",
            "- Show USD values alongside token amounts",
            "- Highlight significant holdings (> 5% of portfolio)",
            "- Display 24h/7d price changes",
            "- Calculate total portfolio value",
            "",
            "Performance analysis:",
            "- Track unrealized PnL on open positions",
            "- Show realized gains/losses from closed trades",
            "- Calculate overall portfolio return",
            "- Compare to relevant benchmarks (BTC, ETH)",
            "",
            "Asset allocation insights:",
            "- Show percentage breakdown by asset",
            "- Identify concentration risk (>30% in one asset)",
            "- Suggest diversification if needed",
            "- Highlight dormant assets",
            "",
            "When showing portfolio:",
            "1. Display total value prominently",
            "2. List assets by value (largest first)",
            "3. Show each asset with: symbol, amount, USD value, 24h change",
            "4. Summarize open positions separately",
            "5. Calculate and show total unrealized PnL",
            "",
            "Helpful recommendations:",
            "- Rebalancing suggestions if allocation is skewed",
            "- Risk reduction if leverage is high",
            "- Profit-taking opportunities on winning positions",
            "- Dollar-cost averaging for accumulation",
            "",
            "Important notes:",
            "- Always show timestamp of data",
            "- Clearly label unrealized vs realized PnL",
            "- Include gas costs in performance calculations",
            "- Respect user privacy - never share specific holdings publicly",
        ]
        
        super().__init__(
            name=name,
            description=description,
            instructions=instructions,
            model=model,
            tools=self.get_tools()
        )
    
    def get_intent_types(self) -> List[str]:
        """Get intent types handled by PortfolioAgent."""
        return ["portfolio_view"]
    
    def get_tools(self) -> List[Any]:
        """
        Get tools for PortfolioAgent.
        
        In Phase 1, we return empty list.
        In Phase 2, we'll add:
        - get_wallet_balances tool
        - get_position_summary tool
        - calculate_portfolio_value tool
        - get_token_prices tool
        """
        # TODO: Add tools in Phase 2 (Week 4-6)
        # - get_wallet_balances
        # - get_open_positions
        # - get_token_prices
        # - calculate_portfolio_metrics
        # - get_transaction_history
        return []
    
    async def run(
        self,
        message: str,
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Process portfolio-related messages.
        
        Args:
            message: User message about portfolio
            context: Optional conversation context
        
        Returns:
            Agent response with portfolio information
        """
        # Add portfolio-specific context
        enhanced_context = context or {}
        enhanced_context["agent_type"] = "portfolio"
        
        # Call parent run method
        response = await super().run(message, enhanced_context)
        
        return response


def create_portfolio_agent(model: str = "gpt-4-turbo") -> PortfolioAgent:
    """
    Factory function to create a PortfolioAgent.
    
    Args:
        model: LLM model to use
    
    Returns:
        PortfolioAgent instance
    """
    return PortfolioAgent(model=model)
