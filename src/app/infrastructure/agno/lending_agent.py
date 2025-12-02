"""Lending Agent - Specialized DeFi Lending & Borrowing Operations.

Handles all lending-related queries using Aave V3 protocol tools.
Provides market data, position management, health factor monitoring, and risk analysis.

Capabilities:
    - Check lending/borrowing rates
    - Manage supply positions
    - Execute borrow operations
    - Monitor health factors
    - Analyze liquidation risks
    - Calculate borrowing capacity

Examples:
    - "What are the current Aave rates for USDC?"
    - "Supply 1000 USDC to Aave"
    - "What's my health factor?"
    - "How much can I borrow?"
    - "Am I at risk of liquidation?"
"""
from typing import Optional

from app.infrastructure.agno.base_agent import DeFiAgentBase
from app.setup.config.agno import AgnoConfig


class LendingAgent(DeFiAgentBase):
    """
    Lending specialist agent using Aave V3 protocol.
    
    This agent is an expert at:
    - Analyzing lending and borrowing rates
    - Managing supply and borrow positions
    - Monitoring account health and liquidation risk
    - Optimizing collateral usage
    
    It uses Aave MCP server tools for all lending operations.
    
    Usage:
        config = AgnoConfig(...)
        agent = LendingAgent(config)
        await agent.load_mcp_tools()
        
        result = await agent.run("What are the Aave rates for USDC?")
        print(result.content)
    """
    
    def __init__(
        self,
        config: AgnoConfig,
        debug_mode: bool = False,
    ):
        """
        Initialize Lending Agent.
        
        Args:
            config: Agno configuration
            debug_mode: Enable debug logging
        """
        # Build specialized instructions
        lending_instructions = [
            # Core lending behavior
            "You specialize in DeFi lending and borrowing using Aave V3 protocol.",
            "You help users earn yield by supplying assets and borrow against collateral.",
            
            # Safety & risk management
            "ALWAYS check user's health factor before suggesting borrows.",
            "Health factor below 1.0 means liquidation risk - warn immediately!",
            "Recommend maintaining health factor above 1.5 for safety (2.0+ is ideal).",
            "NEVER suggest borrowing without checking available capacity first.",
            
            # Best practices
            "For supply operations, explain the APY users will earn.",
            "For borrow operations, explain interest rates and health factor impact.",
            "Always show both variable and stable rates when discussing borrowing.",
            "Explain that supplied assets can be used as collateral to borrow.",
            
            # Risk education
            "Explain liquidation risk: if HF < 1.0, up to 50% of debt can be liquidated.",
            "Price drops in collateral OR price increases in borrowed assets lower HF.",
            "Suggest diversifying collateral across multiple assets to reduce risk.",
            "For volatile assets (ETH, BTC), recommend higher health factor (2.0+).",
            
            # Common operations
            "To check rates: use get_market_data",
            "To check positions: use get_user_positions",
            "To check safety: use calculate_health_factor",
            "To check borrowing capacity: use get_available_to_borrow",
            "For risk analysis: use get_liquidation_risk",
            
            # Chain support
            "Aave V3 is available on: Ethereum, Polygon, Arbitrum, Optimism, Avalanche",
            "Each chain has different gas costs and available assets.",
            
            # Key concepts
            "LTV (Loan-to-Value): Max borrowing power as % of collateral (e.g., 75% LTV)",
            "Liquidation Threshold: When liquidation occurs (e.g., 80%)",
            "Health Factor = (Collateral * Liquidation Threshold) / Total Debt",
            
            # Transaction execution
            "For supply/borrow/repay/withdraw: ALWAYS get user confirmation first.",
            "Show full details: amounts, APY/interest, gas costs, health factor impact.",
        ]
        
        # Initialize base agent with Aave MCP tools
        super().__init__(
            name="Lending Agent",
            role="DeFi lending and borrowing specialist with Aave V3 expertise",
            config=config,
            mcp_servers=["aave"],  # Only use Aave MCP server
            instructions=lending_instructions,
            debug_mode=debug_mode,
        )
    
    async def get_market_rates(
        self,
        chain_id: int,
        assets: Optional[list] = None,
    ):
        """
        Helper method to get lending/borrowing rates.
        
        Args:
            chain_id: Chain ID (1=Ethereum, 137=Polygon, etc.)
            assets: List of asset symbols (e.g., ['USDC', 'ETH'])
        
        Returns:
            Market rates data
        """
        assets_str = f" for {', '.join(assets)}" if assets else ""
        result = await self.run(
            f"What are the current lending and borrowing rates on Aave{assets_str} "
            f"on chain {chain_id}?",
            stream=False,
        )
        return result.content
    
    async def check_health_factor(
        self,
        chain_id: int,
        user_address: str,
    ):
        """
        Helper method to check user's health factor.
        
        Args:
            chain_id: Chain ID
            user_address: User's wallet address
        
        Returns:
            Health factor analysis
        """
        result = await self.run(
            f"What is the health factor for user {user_address} on chain {chain_id}? "
            f"Are they at risk of liquidation?",
            stream=False,
        )
        return result.content
    
    async def calculate_borrow_capacity(
        self,
        chain_id: int,
        user_address: str,
        asset: str,
        target_health_factor: float = 1.5,
    ):
        """
        Helper method to calculate borrowing capacity.
        
        Args:
            chain_id: Chain ID
            user_address: User's wallet address
            asset: Asset to borrow (e.g., 'USDC')
            target_health_factor: Target HF after borrow (default 1.5)
        
        Returns:
            Borrowing capacity analysis
        """
        result = await self.run(
            f"How much {asset} can user {user_address} borrow on chain {chain_id} "
            f"while maintaining a health factor of {target_health_factor}?",
            stream=False,
        )
        return result.content
    
    async def analyze_liquidation_risk(
        self,
        chain_id: int,
        user_address: str,
    ):
        """
        Helper method to analyze liquidation risk.
        
        Args:
            chain_id: Chain ID
            user_address: User's wallet address
        
        Returns:
            Liquidation risk analysis
        """
        result = await self.run(
            f"Analyze the liquidation risk for user {user_address} on chain {chain_id}. "
            f"What price movements would trigger liquidation?",
            stream=False,
        )
        return result.content


# Example usage
if __name__ == "__main__":
    import asyncio
    
    async def test_lending_agent():
        """Test lending agent with Aave MCP tools."""
        # Create config
        config = AgnoConfig(
            model_id="gpt-4-turbo",
            temperature=0.7,
            max_tokens=2000,
            show_tool_calls=True,
        )
        
        # Create lending agent
        agent = LendingAgent(config, debug_mode=True)
        
        # Load MCP tools
        print("\n🔧 Loading Aave MCP tools...")
        await agent.load_mcp_tools()
        
        print(f"\n✅ Loaded {len(agent.mcp_tools)} lending tools:")
        for tool in agent.get_available_tools():
            print(f"   • {tool['name']}")
        
        # Test queries
        test_queries = [
            "What tools do you have for lending operations?",
            "What are the current Aave rates for USDC and ETH on Ethereum?",
            "Explain how health factor works.",
            "What's the difference between variable and stable rates?",
            "How can I check if my position is safe?",
        ]
        
        print("\n" + "="*70)
        print("LENDING AGENT TEST")
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
║            Lending Agent - Aave V3 Integration           ║
╚══════════════════════════════════════════════════════════╝
    """)
    
    asyncio.run(test_lending_agent())
