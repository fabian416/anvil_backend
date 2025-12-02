"""Trading Agent - Specialized DeFi Trading Operations.

Handles all trading-related queries using 1inch DEX aggregator tools.
Provides swap quotes, price checking, route comparison, and gas estimation.

Capabilities:
    - Get swap quotes across DEXes
    - Compare token prices
    - Analyze swap routes
    - Estimate gas costs
    - Execute swaps (with confirmation)
    - Check liquidity sources

Examples:
    - "Swap 1 ETH for USDC on Ethereum"
    - "What's the best price for USDC?"
    - "Compare routes for ETH to DAI"
    - "How much gas will this swap cost?"
"""
from typing import List, Optional

from app.infrastructure.agno.base_agent import DeFiAgentBase
from app.setup.config.agno import AgnoConfig


class TradingAgent(DeFiAgentBase):
    """
    Trading specialist agent using 1inch DEX aggregator.
    
    This agent is an expert at:
    - Finding best swap prices across DEXes
    - Comparing different trading routes
    - Estimating transaction costs
    - Executing trades safely
    
    It uses 1inch MCP server tools for all trading operations.
    
    Usage:
        config = AgnoConfig(...)
        agent = TradingAgent(config)
        await agent.load_mcp_tools()
        
        result = await agent.run("Swap 1 ETH for USDC on Ethereum")
        print(result.content)
    """
    
    def __init__(
        self,
        config: AgnoConfig,
        debug_mode: bool = False,
    ):
        """
        Initialize Trading Agent.
        
        Args:
            config: Agno configuration
            debug_mode: Enable debug logging
        """
        # Build specialized instructions
        trading_instructions = [
            # Core trading behavior
            "You specialize in DeFi token trading and swaps.",
            "You use 1inch DEX aggregator to find the best prices across multiple DEXes.",
            
            # Safety & confirmation
            "ALWAYS get a swap quote before suggesting any trade.",
            "ALWAYS show the user the full details: amounts, gas costs, price impact, route.",
            "NEVER execute a swap without explicit user confirmation.",
            "Warn users about high price impact (> 1%) and slippage risks.",
            
            # Best practices
            "For large trades, suggest splitting into smaller amounts to reduce price impact.",
            "Always mention gas costs in both native token and USD.",
            "Explain the DEX route being used (e.g., 'via Uniswap V3 + SushiSwap').",
            "Consider gas costs when recommending trades on expensive chains.",
            
            # Common queries
            "For price checks, use get_token_price.",
            "For swap quotes, use get_swap_quote with accurate amounts.",
            "For route comparison, use compare_swap_routes.",
            "For gas estimates, use estimate_gas.",
            
            # Chain-specific guidance
            "Ethereum (chain_id=1): High gas, best liquidity.",
            "Polygon (chain_id=137): Low gas, good liquidity.",
            "Arbitrum (chain_id=42161): Low gas, L2 benefits.",
            "Optimism (chain_id=10): Low gas, L2 benefits.",
            
            # Token addresses
            "Native ETH address: 0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE",
            "Remember: amounts should be in wei (1 ETH = 1000000000000000000 wei).",
            "For USDC/USDT (6 decimals): 1 USDC = 1000000.",
        ]
        
        # Initialize base agent with 1inch MCP tools
        super().__init__(
            name="Trading Agent",
            role="DeFi trading specialist and DEX aggregation expert",
            config=config,
            mcp_servers=["1inch"],  # Only use 1inch MCP server
            instructions=trading_instructions,
            debug_mode=debug_mode,
        )
    
    async def get_swap_quote(
        self,
        chain_id: int,
        from_token: str,
        to_token: str,
        amount: str,
        slippage: float = 1.0,
    ):
        """
        Helper method to get swap quote directly.
        
        Args:
            chain_id: Chain ID (1=Ethereum, 137=Polygon, etc.)
            from_token: From token address
            to_token: To token address
            amount: Amount in smallest unit (wei)
            slippage: Slippage tolerance (default 1.0%)
        
        Returns:
            Swap quote details
        """
        result = await self.run(
            f"Get a swap quote for swapping {amount} wei of {from_token} "
            f"to {to_token} on chain {chain_id} with {slippage}% slippage.",
            stream=False,
        )
        return result.content
    
    async def get_token_price(
        self,
        chain_id: int,
        token_address: str,
    ):
        """
        Helper method to get token price.
        
        Args:
            chain_id: Chain ID
            token_address: Token contract address
        
        Returns:
            Token price in USD
        """
        result = await self.run(
            f"What is the current USD price of token {token_address} on chain {chain_id}?",
            stream=False,
        )
        return result.content
    
    async def compare_routes(
        self,
        chain_id: int,
        from_token: str,
        to_token: str,
        amount: str,
    ):
        """
        Helper method to compare swap routes.
        
        Args:
            chain_id: Chain ID
            from_token: From token address
            to_token: To token address
            amount: Amount in smallest unit
        
        Returns:
            Route comparison analysis
        """
        result = await self.run(
            f"Compare different routes for swapping {amount} wei of {from_token} "
            f"to {to_token} on chain {chain_id}. Which is best?",
            stream=False,
        )
        return result.content


# Example usage
if __name__ == "__main__":
    import asyncio
    
    async def test_trading_agent():
        """Test trading agent with 1inch MCP tools."""
        # Create config
        config = AgnoConfig(
            model_id="gpt-4-turbo",
            temperature=0.7,
            max_tokens=2000,
            show_tool_calls=True,
        )
        
        # Create trading agent
        agent = TradingAgent(config, debug_mode=True)
        
        # Load MCP tools
        print("\n🔧 Loading 1inch MCP tools...")
        await agent.load_mcp_tools()
        
        print(f"\n✅ Loaded {len(agent.mcp_tools)} trading tools:")
        for tool in agent.get_available_tools():
            print(f"   • {tool['name']}")
        
        # Test queries
        test_queries = [
            "What tools do you have for trading?",
            "What's the current price of ETH?",
            "How would I swap 1 ETH for USDC on Ethereum? Show me a quote.",
            "What are the available DEXes on Polygon?",
            "Compare routes for swapping ETH to DAI on Ethereum.",
        ]
        
        print("\n" + "="*70)
        print("TRADING AGENT TEST")
        print("="*70)
        
        for query in test_queries:
            print(f"\n📝 User: {query}")
            print("-"*70)
            
            try:
                result = await agent.run(query)
                print(f"🤖 Agent: {result.content}")
            except Exception as e:
                print(f"❌ Error: {e}")
            
            print("-"*70)
    
    # Run test
    print("""
╔══════════════════════════════════════════════════════════╗
║            Trading Agent - 1inch Integration             ║
╚══════════════════════════════════════════════════════════╝
    """)
    
    asyncio.run(test_trading_agent())
