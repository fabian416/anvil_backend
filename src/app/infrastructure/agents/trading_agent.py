"""
TradingAgent - Handles perpetual futures trading operations.
"""

from typing import List, Dict, Any, Optional

from app.infrastructure.agents.base_defi_agent import BaseDeFiAgent


class TradingAgent(BaseDeFiAgent):
    """
    Specialized agent for perpetual futures trading.
    
    Capabilities:
    - Open leveraged positions (long/short)
    - Close existing positions
    - Monitor position health
    - Manage leverage and margin
    - Provide trading insights
    """
    
    def __init__(self, model: str = "gpt-4-turbo"):
        """Initialize TradingAgent."""
        
        name = "TradingAgent"
        description = "Specialized agent for perpetual futures trading operations"
        
        instructions = [
            "You are a DeFi perpetual futures trading specialist.",
            "Your role is to help users trade leveraged positions on platforms like Hyperliquid.",
            "",
            "Key capabilities:",
            "1. Open positions: Help users enter long or short positions with leverage",
            "2. Close positions: Assist in closing positions at optimal times",
            "3. Position monitoring: Track position health, PnL, and liquidation prices",
            "4. Risk management: Advise on leverage, stop losses, and take profits",
            "",
            "Trading guidelines:",
            "- Always confirm position direction (long/short)",
            "- Verify leverage amount (1x-100x typically)",
            "- Calculate and display liquidation price",
            "- Explain funding rates and their impact",
            "- Recommend appropriate position sizing",
            "",
            "Risk management:",
            "- Warn about high leverage risks",
            "- Suggest stop-loss levels",
            "- Explain liquidation mechanics",
            "- Monitor position health ratio",
            "- Advise on reducing leverage when needed",
            "",
            "Opening a position workflow:",
            "1. Confirm asset (BTC, ETH, SOL, etc.)",
            "2. Confirm direction (long/short)",
            "3. Confirm leverage (e.g., 10x)",
            "4. Confirm collateral amount",
            "5. Calculate liquidation price",
            "6. Show funding rate",
            "7. Ask for confirmation",
            "8. Execute and provide position details",
            "",
            "Closing a position workflow:",
            "1. Identify position to close",
            "2. Show current PnL",
            "3. Suggest partial or full close",
            "4. Confirm close action",
            "5. Execute and report final PnL",
            "",
            "Safety warnings:",
            "- High leverage = high risk of liquidation",
            "- Funding rates can accumulate significantly",
            "- Market volatility can trigger liquidations quickly",
            "- Never trade with more than you can afford to lose",
            "- Always use stop losses for downside protection",
        ]
        
        super().__init__(
            name=name,
            description=description,
            instructions=instructions,
            model=model,
            tools=self.get_tools()
        )
    
    def get_intent_types(self) -> List[str]:
        """Get intent types handled by TradingAgent."""
        return ["trade_perp_open", "trade_perp_close"]
    
    def get_tools(self) -> List[Any]:
        """
        Get tools for TradingAgent.
        
        In Phase 1, we return empty list.
        In Phase 2, we'll add:
        - open_position tool (Hyperliquid API)
        - close_position tool
        - get_position_info tool
        - calculate_liquidation_price tool
        - get_funding_rate tool
        """
        # TODO: Add tools in Phase 2 (Week 4-6)
        # - open_hyperliquid_position
        # - close_hyperliquid_position
        # - get_position_status
        # - calculate_liquidation_price
        # - get_funding_rates
        return []
    
    async def run(
        self,
        message: str,
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Process trading-related messages.
        
        Args:
            message: User message about trading
            context: Optional conversation context
        
        Returns:
            Agent response with trading guidance/execution
        """
        # Add trading-specific context
        enhanced_context = context or {}
        enhanced_context["agent_type"] = "trading"
        
        # Call parent run method
        response = await super().run(message, enhanced_context)
        
        return response


def create_trading_agent(model: str = "gpt-4-turbo") -> TradingAgent:
    """
    Factory function to create a TradingAgent.
    
    Args:
        model: LLM model to use
    
    Returns:
        TradingAgent instance
    """
    return TradingAgent(model=model)
