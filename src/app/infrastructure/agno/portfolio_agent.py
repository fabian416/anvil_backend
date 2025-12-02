"""Portfolio Agent - Specialized Portfolio Management & Tracking.

Handles all portfolio queries using Portfolio MCP server tools.
Provides balance tracking, position monitoring, and portfolio summaries.

Capabilities:
    - Check token balances across chains
    - Monitor DeFi positions (lending, LP, staking)
    - Generate portfolio summaries with USD valuation
    - Track portfolio performance
    - Multi-chain portfolio aggregation

Examples:
    - "Show me my portfolio"
    - "What's my ETH balance?"
    - "What positions do I have on Aave?"
    - "What's my total portfolio value?"
    - "Show my balances across all chains"
"""
from typing import Optional

from app.infrastructure.agno.base_agent import DeFiAgentBase
from app.setup.config.agno import AgnoConfig


class PortfolioAgent(DeFiAgentBase):
    """
    Portfolio management specialist agent.
    
    This agent is an expert at:
    - Tracking token balances across multiple chains
    - Monitoring DeFi positions (lending, liquidity, staking)
    - Calculating total portfolio value in USD
    - Identifying asset allocation
    
    It uses Portfolio MCP server tools for all operations.
    
    Usage:
        config = AgnoConfig(...)
        agent = PortfolioAgent(config)
        await agent.load_mcp_tools()
        
        result = await agent.run("Show me my portfolio for address 0x...")
        print(result.content)
    """
    
    def __init__(
        self,
        config: AgnoConfig,
        debug_mode: bool = False,
    ):
        """
        Initialize Portfolio Agent.
        
        Args:
            config: Agno configuration
            debug_mode: Enable debug logging
        """
        # Build specialized instructions
        portfolio_instructions = [
            # Core portfolio behavior
            "You specialize in portfolio management and tracking across DeFi protocols.",
            "You help users monitor their assets, positions, and overall portfolio health.",
            
            # Data presentation
            "Always show balances with both token amounts and USD values.",
            "Group assets by type: tokens, lending positions, liquidity positions, staking.",
            "Highlight the largest holdings and significant positions.",
            "Show total portfolio value prominently.",
            
            # Multi-chain awareness
            "Users often have assets across multiple chains (Ethereum, Polygon, Arbitrum, etc.).",
            "Always specify which chain each asset is on.",
            "Aggregate totals across all chains for complete picture.",
            
            # Position analysis
            "For lending positions: show supplied amount, collateral status, earning APY.",
            "For LP positions: show pool composition, IL risk, farming rewards.",
            "For staking: show staked amount, rewards earned, APY.",
            
            # Common queries
            "To check balances: use get_user_balance",
            "To check DeFi positions: use get_user_positions",
            "For complete overview: use get_portfolio_summary",
            
            # Insights and recommendations
            "Point out concentration risk if >50% in single asset.",
            "Suggest diversification if portfolio is heavily concentrated.",
            "Mention gas-efficient chains for small balance migrations.",
            "Identify idle assets that could be earning yield.",
            
            # Privacy and security
            "Never share or log user addresses or balances.",
            "Don't suggest specific investment actions - just present data.",
            "Remind users to verify balances on-chain themselves.",
            
            # Asset categories
            "Stablecoins: USDC, USDT, DAI, FRAX, etc.",
            "Blue-chip: ETH, WBTC, MATIC, AVAX, etc.",
            "DeFi tokens: AAVE, UNI, SUSHI, CRV, etc.",
            "LP tokens: Represent liquidity positions.",
            "aTokens/cTokens: Represent lending positions.",
        ]
        
        # Initialize base agent with Portfolio MCP tools
        super().__init__(
            name="Portfolio Agent",
            role="Portfolio management and asset tracking specialist",
            config=config,
            mcp_servers=["portfolio"],  # Only use Portfolio MCP server
            instructions=portfolio_instructions,
            debug_mode=debug_mode,
        )
    
    async def get_balances(
        self,
        user_id: str,
        chain_id: Optional[int] = None,
    ):
        """
        Helper method to get user balances.
        
        Args:
            user_id: User identifier
            chain_id: Specific chain (None = all chains)
        
        Returns:
            Balance information
        """
        chain_str = f" on chain {chain_id}" if chain_id else " across all chains"
        result = await self.run(
            f"What are the token balances for user {user_id}{chain_str}?",
            stream=False,
        )
        return result.content
    
    async def get_positions(
        self,
        user_id: str,
    ):
        """
        Helper method to get user's DeFi positions.
        
        Args:
            user_id: User identifier
        
        Returns:
            Position information
        """
        result = await self.run(
            f"What DeFi positions does user {user_id} have? "
            f"Include lending, liquidity, and staking positions.",
            stream=False,
        )
        return result.content
    
    async def get_portfolio_summary(
        self,
        user_id: str,
    ):
        """
        Helper method to get complete portfolio summary.
        
        Args:
            user_id: User identifier
        
        Returns:
            Complete portfolio summary
        """
        result = await self.run(
            f"Give me a complete portfolio summary for user {user_id}. "
            f"Include total value, asset allocation, and key insights.",
            stream=False,
        )
        return result.content
    
    async def analyze_diversification(
        self,
        user_id: str,
    ):
        """
        Helper method to analyze portfolio diversification.
        
        Args:
            user_id: User identifier
        
        Returns:
            Diversification analysis
        """
        result = await self.run(
            f"Analyze the diversification of user {user_id}'s portfolio. "
            f"Is it well-diversified or concentrated? Any recommendations?",
            stream=False,
        )
        return result.content


# Example usage
if __name__ == "__main__":
    import asyncio
    
    async def test_portfolio_agent():
        """Test portfolio agent with Portfolio MCP tools."""
        # Create config
        config = AgnoConfig(
            model_id="gpt-4-turbo",
            temperature=0.7,
            max_tokens=2000,
            show_tool_calls=True,
        )
        
        # Create portfolio agent
        agent = PortfolioAgent(config, debug_mode=True)
        
        # Load MCP tools
        print("\n🔧 Loading Portfolio MCP tools...")
        await agent.load_mcp_tools()
        
        print(f"\n✅ Loaded {len(agent.mcp_tools)} portfolio tools:")
        for tool in agent.get_available_tools():
            print(f"   • {tool['name']}")
        
        # Test queries
        test_queries = [
            "What portfolio management tools do you have?",
            "Explain what information you can show me about my portfolio.",
            "What types of DeFi positions can you track?",
            "How do you calculate portfolio value?",
            "What insights can you provide about asset allocation?",
        ]
        
        print("\n" + "="*70)
        print("PORTFOLIO AGENT TEST")
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
║          Portfolio Agent - Portfolio Tracking            ║
╚══════════════════════════════════════════════════════════╝
    """)
    
    asyncio.run(test_portfolio_agent())
