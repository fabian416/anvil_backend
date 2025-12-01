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
        
        Phase 2 implementation with real Hyperliquid integration.
        """
        # Import tools here to avoid circular imports
        from app.infrastructure.defi.tools.trading_tools import (
            get_position_info_tool,
            explain_perp_trading_tool,
            calculate_pnl_tool,
        )
        from app.infrastructure.defi.tools.position_management_tools import (
            calculate_stop_loss_tool,
            calculate_take_profit_tool,
            analyze_position_health_tool,
        )
        
        # Tool metadata for Phase 2
        tools = [
            {
                "name": "get_position_info",
                "description": "Get information about opening a perpetual position",
                "parameters": {
                    "symbol": "Trading pair (BTC, ETH, etc.)",
                    "leverage": "Leverage multiplier (1-100)",
                    "collateral": "Collateral amount in USD",
                    "is_long": "True for long, False for short",
                },
                "function": get_position_info_tool,
            },
            {
                "name": "explain_perp_trading",
                "description": "Explain how perpetual futures trading works",
                "parameters": {
                    "symbol": "Trading pair symbol",
                },
                "function": explain_perp_trading_tool,
            },
            {
                "name": "calculate_pnl",
                "description": "Calculate profit/loss for a position",
                "parameters": {
                    "entry_price": "Entry price",
                    "current_price": "Current market price",
                    "position_size": "Position size in USD",
                    "is_long": "True for long, False for short",
                },
                "function": calculate_pnl_tool,
            },
            {
                "name": "calculate_stop_loss",
                "description": "Calculate optimal stop loss for a position",
                "parameters": {
                    "entry_price": "Entry price",
                    "position_size": "Position size in USD",
                    "is_long": "True for long, False for short",
                    "risk_percentage": "Risk as % of position (default 2%)",
                },
                "function": calculate_stop_loss_tool,
            },
            {
                "name": "calculate_take_profit",
                "description": "Calculate take profit levels",
                "parameters": {
                    "entry_price": "Entry price",
                    "position_size": "Position size in USD",
                    "is_long": "True for long, False for short",
                    "reward_ratio": "Reward/risk ratio (default 2:1)",
                },
                "function": calculate_take_profit_tool,
            },
            {
                "name": "analyze_position_health",
                "description": "Analyze position health and risk",
                "parameters": {
                    "entry_price": "Entry price",
                    "current_price": "Current market price",
                    "liquidation_price": "Liquidation price",
                    "position_size": "Position size in USD",
                    "is_long": "True for long, False for short",
                },
                "function": analyze_position_health_tool,
            },
        ]
        
        return tools
    
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
