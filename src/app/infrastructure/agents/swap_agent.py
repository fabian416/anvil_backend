"""
SwapAgent - Handles token swap operations via DEX aggregators.
"""

from typing import List, Dict, Any, Optional

from app.infrastructure.agents.base_defi_agent import BaseDeFiAgent


class SwapAgent(BaseDeFiAgent):
    """
    Specialized agent for DeFi token swaps.
    
    Capabilities:
    - Quote swap prices
    - Execute token swaps via DEX aggregators (1inch, 0x)
    - Provide swap recommendations
    - Explain swap mechanics
    """
    
    def __init__(self, model: str = "gpt-4-turbo"):
        """Initialize SwapAgent."""
        
        name = "SwapAgent"
        description = "Specialized agent for DeFi token swap operations"
        
        instructions = [
            "You are a DeFi swap specialist that helps users exchange tokens.",
            "Your primary role is to facilitate token swaps via DEX aggregators like 1inch and 0x.",
            "",
            "Key capabilities:",
            "1. Quote swap prices: Get the best rates across multiple DEXs",
            "2. Execute swaps: Help users swap tokens safely and efficiently",
            "3. Explain mechanics: Clarify how swaps work, slippage, gas fees, etc.",
            "4. Provide recommendations: Suggest optimal swap routes and timing",
            "",
            "Important guidelines:",
            "- Always quote from multiple DEXs to ensure best rates",
            "- Warn about slippage on large trades",
            "- Explain gas costs clearly",
            "- Verify token addresses to prevent scams",
            "- Recommend setting appropriate slippage tolerance (typically 0.5-1%)",
            "",
            "When a user asks to swap tokens:",
            "1. Confirm the exact tokens (from/to)",
            "2. Confirm the amount",
            "3. Quote the current rate and expected output",
            "4. Explain any fees or slippage",
            "5. Ask for confirmation before executing",
            "",
            "Safety first:",
            "- Always verify token contracts",
            "- Warn about price impact on large swaps",
            "- Suggest splitting large orders if needed",
            "- Never execute swaps without explicit user confirmation",
        ]
        
        super().__init__(
            name=name,
            description=description,
            instructions=instructions,
            model=model,
            tools=self.get_tools()
        )
    
    def get_intent_types(self) -> List[str]:
        """Get intent types handled by SwapAgent."""
        return ["trade_swap"]
    
    def get_tools(self) -> List[Any]:
        """
        Get tools for SwapAgent.
        
        Phase 2 implementation with real 1inch integration.
        """
        # Import tools here to avoid circular imports
        from app.infrastructure.defi.tools.swap_tools import (
            get_swap_quote_tool,
            explain_swap_tool,
            get_token_info_tool,
        )
        
        # In Phase 2, these will be actual callable tools
        # For now, we define tool metadata
        tools = [
            {
                "name": "get_swap_quote",
                "description": "Get a swap quote from 1inch DEX aggregator",
                "parameters": {
                    "src_token": "Source token symbol (USDC, ETH, etc.)",
                    "dst_token": "Destination token symbol",
                    "amount": "Amount to swap in human-readable format",
                },
                "function": get_swap_quote_tool,
            },
            {
                "name": "explain_swap",
                "description": "Explain how a token swap works",
                "parameters": {
                    "src_token": "Source token symbol",
                    "dst_token": "Destination token symbol",
                },
                "function": explain_swap_tool,
            },
            {
                "name": "get_token_info",
                "description": "Get information about a token",
                "parameters": {
                    "token": "Token symbol",
                },
                "function": get_token_info_tool,
            },
        ]
        
        return tools
    
    async def run(
        self,
        message: str,
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Process swap-related messages.
        
        Args:
            message: User message about swapping
            context: Optional conversation context
        
        Returns:
            Agent response with swap guidance/execution
        """
        # Add swap-specific context
        enhanced_context = context or {}
        enhanced_context["agent_type"] = "swap"
        
        # Call parent run method
        response = await super().run(message, enhanced_context)
        
        return response


def create_swap_agent(model: str = "gpt-4-turbo") -> SwapAgent:
    """
    Factory function to create a SwapAgent.
    
    Args:
        model: LLM model to use
    
    Returns:
        SwapAgent instance
    """
    return SwapAgent(model=model)
