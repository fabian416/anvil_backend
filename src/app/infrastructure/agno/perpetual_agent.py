"""Perpetual Agent - Specialized Perpetual Futures Trading Operations.

Handles all perpetual futures queries using Hyperliquid DEX tools.
Provides market analysis, position management, risk calculations, and funding rate strategies.

Capabilities:
    - Discover perpetual markets
    - Analyze funding rates
    - Calculate liquidation prices
    - Monitor open positions
    - Track recent liquidations
    - Find funding arbitrage opportunities
    - Calculate position risk metrics

Examples:
    - "What's the funding rate on ETH perps?"
    - "Calculate liquidation price for 10x long ETH at $2000"
    - "Show me my Hyperliquid positions"
    - "Find funding arbitrage opportunities"
    - "What were recent liquidations on BTC?"
"""

from typing import Optional

from app.infrastructure.agno.base_agent import DeFiAgentBase
from app.setup.config.agno import AgnoConfig


class PerpetualAgent(DeFiAgentBase):
    """
    Perpetual futures specialist agent using Hyperliquid DEX.

    This agent is an expert at:
    - Analyzing perpetual markets and funding rates
    - Calculating liquidation prices and risk metrics
    - Identifying funding rate arbitrage opportunities
    - Monitoring positions and leverage
    - Tracking market liquidations

    It uses Hyperliquid MCP server tools for all perpetual trading operations.

    Usage:
        config = AgnoConfig(...)
        agent = PerpetualAgent(config)
        await agent.load_mcp_tools()

        result = await agent.run("What's the funding rate on ETH?")
        print(result.content)
    """

    def __init__(
        self,
        config: AgnoConfig,
        debug_mode: bool = False,
    ):
        """
        Initialize Perpetual Agent.

        Args:
            config: Agno configuration
            debug_mode: Enable debug logging
        """
        # Build specialized instructions
        perpetual_instructions = [
            # Core perpetual trading behavior
            "You specialize in perpetual futures trading on Hyperliquid DEX.",
            "You help users trade with leverage, manage risk, and optimize funding strategies.",
            # Safety & risk management - CRITICAL
            "ALWAYS calculate liquidation price before suggesting any leveraged position.",
            "NEVER recommend leverage above 5x without explicit risk warnings.",
            "Warn about liquidation risk: positions can be liquidated if price moves against you.",
            "ALWAYS explain margin requirements and potential losses.",
            # Leverage education
            "Higher leverage = Higher risk of liquidation.",
            "At 10x leverage, a 10% price move against you = liquidation.",
            "At 5x leverage, you need a 20% adverse move to get liquidated.",
            "Recommend 2-3x leverage for beginners, max 5x for most users.",
            # Funding rates
            "Funding rates are periodic payments between longs and shorts.",
            "Positive rate: Longs pay shorts (long interest > short interest).",
            "Negative rate: Shorts pay longs (short interest > long interest).",
            "Funding typically paid every 8 hours (3x per day).",
            "High funding rates (>0.01%) can erode profitability or create arbitrage opportunities.",
            # Position management
            "Always check current positions before suggesting new trades.",
            "Monitor unrealized PnL and distance to liquidation.",
            "Suggest taking profits when position is significantly in profit.",
            "Recommend adding margin or reducing leverage if close to liquidation.",
            # Liquidation monitoring
            "Track recent liquidations to understand market leverage and volatility.",
            "Large liquidations can cause cascading price movements.",
            "High liquidation activity = high risk environment.",
            # Risk calculations
            "Use calculate_liquidation_price to show exact liquidation level.",
            "Use calculate_risk_metrics for comprehensive position analysis.",
            "Always show: required margin, max loss, distance to liquidation.",
            # Common operations
            "To check markets: use hyperliquid_get_markets",
            "To check funding: use hyperliquid_get_funding_rate or hyperliquid_get_funding_rates",
            "To calculate risk: use hyperliquid_calculate_liquidation_price",
            "To check positions: use hyperliquid_get_positions",
            "To track liquidations: use hyperliquid_get_liquidations",
            "To find arbitrage: use hyperliquid_find_funding_arbitrage",
            "For order book: use hyperliquid_get_order_book",
            # Funding arbitrage strategy
            "Funding arbitrage = earn funding by taking opposite position in spot.",
            "Example: If ETH funding is +0.05%, short ETH perp + buy ETH spot.",
            "You collect funding payments while being market neutral.",
            "Works best with high funding rates (>0.02% per period).",
            "Explain both the strategy and the risks (basis risk, liquidation).",
            # Best practices
            "For leveraged positions, ALWAYS show liquidation price.",
            "When funding is extreme (>0.05%), suggest funding arbitrage.",
            "For beginners, recommend starting with 2-3x leverage max.",
            "Explain that perps are zero-sum: your gain = someone else's loss.",
            # Transaction execution
            "NEVER execute trades directly - Hyperliquid requires user signatures.",
            "Provide analysis and calculations, let user execute on Hyperliquid app.",
            "Always include disclaimer about trading risks.",
            # Market analysis
            "High funding + high OI = overcrowded trade, risk of reversal.",
            "Negative funding on downtrend = potential short squeeze.",
            "Volume spikes often precede liquidation cascades.",
            # Position sizing
            "Recommended position sizing: max 1-5% of account per trade.",
            "With 10x leverage, 1% account exposure = 10% position size.",
            "Always account for fees and funding costs in calculations.",
        ]

        # Initialize base agent with Hyperliquid MCP tools
        super().__init__(
            name="Perpetual Agent",
            role="Perpetual futures trading specialist with Hyperliquid expertise",
            config=config,
            mcp_servers=["hyperliquid"],  # Use Hyperliquid MCP server
            instructions=perpetual_instructions,
            debug_mode=debug_mode,
        )

    async def get_funding_rate(
        self,
        symbol: str,
    ):
        """
        Helper method to get funding rate for a symbol.

        Args:
            symbol: Trading pair symbol (e.g., 'ETH', 'BTC')

        Returns:
            Funding rate details
        """
        result = await self.run(
            f"What is the current funding rate for {symbol} perpetual futures?",
            stream=False,
        )
        return result.content

    async def calculate_liquidation_price(
        self,
        entry_price: float,
        leverage: float,
        side: str,
    ):
        """
        Helper method to calculate liquidation price.

        Args:
            entry_price: Entry price
            leverage: Leverage multiplier
            side: "long" or "short"

        Returns:
            Liquidation price analysis
        """
        result = await self.run(
            f"Calculate the liquidation price for a {side} position "
            f"with {leverage}x leverage at entry price ${entry_price}.",
            stream=False,
        )
        return result.content

    async def analyze_position_risk(
        self,
        entry_price: float,
        size: float,
        leverage: float,
        side: str,
        symbol: str = "ETH",
    ):
        """
        Helper method to analyze position risk.

        Args:
            entry_price: Entry price
            size: Position size
            leverage: Leverage
            side: "long" or "short"
            symbol: Trading symbol

        Returns:
            Risk analysis
        """
        result = await self.run(
            f"Analyze the risk for a {side} {symbol} position: "
            f"Entry ${entry_price}, Size {size}, Leverage {leverage}x. "
            f"Show liquidation price, required margin, and max loss.",
            stream=False,
        )
        return result.content

    async def find_funding_arbitrage(
        self,
        min_rate: float = 0.01,
    ):
        """
        Helper method to find funding arbitrage opportunities.

        Args:
            min_rate: Minimum funding rate threshold (e.g., 0.01 = 1%)

        Returns:
            Arbitrage opportunities
        """
        result = await self.run(
            f"Find funding rate arbitrage opportunities with minimum rate {min_rate * 100:.2f}%. "
            f"Explain the strategy for the best opportunities.",
            stream=False,
        )
        return result.content


# Example usage
if __name__ == "__main__":
    import asyncio

    async def test_perpetual_agent():
        """Test perpetual agent with Hyperliquid MCP tools."""
        # Create config
        config = AgnoConfig(
            model_id="gpt-4-turbo",
            temperature=0.7,
            max_tokens=2000,
            show_tool_calls=True,
        )

        # Create perpetual agent
        agent = PerpetualAgent(config, debug_mode=True)

        # Load MCP tools
        print("\n🔧 Loading Hyperliquid MCP tools...")
        await agent.load_mcp_tools()

        print(f"\n✅ Loaded {len(agent.mcp_tools)} perpetual trading tools:")
        for tool in agent.get_available_tools():
            print(f"   • {tool['name']}")

        # Test queries
        test_queries = [
            "What tools do you have for perpetual futures trading?",
            "What's the current funding rate on ETH?",
            "Calculate liquidation price for 10x long ETH at $2000",
            "Explain how funding rates work",
            "Find funding arbitrage opportunities",
            "What's the risk of 20x leverage?",
        ]

        print("\n" + "=" * 70)
        print("PERPETUAL AGENT TEST")
        print("=" * 70)

        for query in test_queries:
            print(f"\n📝 User: {query}")
            print("-" * 70)

            try:
                result = await agent.run(query)
                print(f"🤖 Agent: {result.content}")
            except Exception as e:
                print(f"❌ Error: {e}")

            print("-" * 70)

    # Run test
    print("""
╔══════════════════════════════════════════════════════════╗
║     Perpetual Agent - Hyperliquid Integration            ║
╚══════════════════════════════════════════════════════════╝
    """)

    asyncio.run(test_perpetual_agent())
