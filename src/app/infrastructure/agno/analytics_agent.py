"""Analytics Agent - Specialized DeFi Protocol Analytics & Research.

Handles all analytics queries using DeFiLlama data.
Provides protocol research, yield discovery, TVL analysis, and market intelligence.

Capabilities:
    - Protocol TVL and growth tracking
    - Yield farming opportunity discovery
    - Protocol fee and revenue analysis
    - Stablecoin market analysis
    - Protocol comparison
    - Trending protocols identification

Examples:
    - "What's the TVL of Aave?"
    - "Find the best yield opportunities for stablecoins"
    - "Compare Aave vs Compound"
    - "What protocols are trending this week?"
    - "Show me stablecoin market dominance"
"""

from typing import Optional, List

from app.infrastructure.agno.base_agent import DeFiAgentBase
from app.setup.config.agno import AgnoConfig


class AnalyticsAgent(DeFiAgentBase):
    """
    Analytics specialist agent using DeFiLlama data.

    This agent is an expert at:
    - Researching DeFi protocols and their metrics
    - Finding yield farming opportunities
    - Analyzing protocol sustainability (fees, revenue)
    - Tracking stablecoin adoption
    - Identifying market trends

    It uses DeFiLlama MCP server tools for all analytics.

    Usage:
        config = AgnoConfig(...)
        agent = AnalyticsAgent(config)
        await agent.load_mcp_tools()

        result = await agent.run("What's the TVL of Aave?")
        print(result.content)
    """

    def __init__(
        self,
        config: AgnoConfig,
        debug_mode: bool = False,
    ):
        """
        Initialize Analytics Agent.

        Args:
            config: Agno configuration
            debug_mode: Enable debug logging
        """
        # Build specialized instructions
        analytics_instructions = [
            # Core analytics behavior
            "You specialize in DeFi protocol analytics and market research using DeFiLlama data.",
            "You help users discover opportunities, compare protocols, and understand market trends.",
            # Data interpretation
            "Always provide context with numbers (e.g., '$10B TVL is significant for lending protocols').",
            "Explain growth trends: is a protocol growing, stable, or declining?",
            "For yields, always mention the associated risks (IL risk, protocol risk, smart contract risk).",
            # Yield opportunities
            "When finding yields, consider: APY, TVL (safety), protocol reputation, audit status.",
            "Stablecoin pools are lower risk but lower APY.",
            "High APY often means higher risk - always warn users.",
            "Recommend minimum TVL thresholds (e.g., $1M+) for safety.",
            # Protocol analysis
            "TVL = Total Value Locked (how much capital is in the protocol)",
            "Higher TVL generally means more trust and liquidity.",
            "Protocol fees = revenue generated (shows real usage)",
            "Compare protocols on: TVL, fees, user count, chain distribution",
            # Common queries
            "For protocol metrics: use get_protocol_tvl",
            "For yield farming: use get_yields with appropriate filters",
            "For protocol revenue: use get_protocol_fees",
            "For comparisons: use compare_protocols",
            "For trends: use get_trending_protocols",
            "For stablecoins: use get_stablecoin_data",
            # Chain analysis
            "Ethereum has highest TVL but expensive gas.",
            "L2s (Arbitrum, Optimism) have growing TVL and cheap gas.",
            "Alternative L1s (Avalanche, BSC) have competitive yields.",
            # Risk education
            "DeFi risks: smart contract bugs, protocol hacks, impermanent loss, liquidations.",
            "Never financial advice: present data and let users decide.",
            "Recommend users DYOR (Do Your Own Research) before investing.",
            # Trending insights
            "Trending = high recent growth, not necessarily sustainable.",
            "New protocols may have high APY to attract users (farming incentives).",
            "Established protocols (Aave, Uniswap, Curve) are generally safer.",
        ]

        # Initialize base agent with DeFiLlama MCP tools
        super().__init__(
            name="Analytics Agent",
            role="DeFi protocol analyst and market research specialist",
            config=config,
            mcp_servers=["defillama"],  # Only use DeFiLlama MCP server
            instructions=analytics_instructions,
            debug_mode=debug_mode,
        )

    async def get_protocol_analysis(
        self,
        protocol: str,
    ):
        """
        Helper method to get complete protocol analysis.

        Args:
            protocol: Protocol slug (e.g., 'aave', 'uniswap')

        Returns:
            Protocol analysis
        """
        result = await self.run(
            f"Give me a complete analysis of {protocol} protocol including "
            f"TVL, growth trends, and market position.",
            stream=False,
        )
        return result.content

    async def find_yields(
        self,
        chain: Optional[str] = None,
        stablecoin_only: bool = False,
        min_tvl: float = 1000000,
        min_apy: float = 0,
    ):
        """
        Helper method to find yield opportunities.

        Args:
            chain: Filter by chain (e.g., 'Ethereum', 'Polygon')
            stablecoin_only: Only stablecoin pools
            min_tvl: Minimum TVL in USD
            min_apy: Minimum APY percentage

        Returns:
            Yield opportunities
        """
        filters = []
        if chain:
            filters.append(f"on {chain}")
        if stablecoin_only:
            filters.append("stablecoin pools only")
        if min_tvl:
            filters.append(f"minimum ${min_tvl:,.0f} TVL")
        if min_apy:
            filters.append(f"minimum {min_apy}% APY")

        filter_str = " with " + ", ".join(filters) if filters else ""

        result = await self.run(
            f"Find the best yield farming opportunities{filter_str}. "
            f"Show me the top 10 sorted by APY.",
            stream=False,
        )
        return result.content

    async def compare_protocols(
        self,
        protocols: List[str],
    ):
        """
        Helper method to compare protocols.

        Args:
            protocols: List of protocol slugs (e.g., ['aave', 'compound'])

        Returns:
            Protocol comparison
        """
        protocol_list = ", ".join(protocols)
        result = await self.run(
            f"Compare these protocols: {protocol_list}. "
            f"Which one is performing better and why?",
            stream=False,
        )
        return result.content

    async def get_trending(
        self,
        timeframe: str = "7d",
        limit: int = 10,
    ):
        """
        Helper method to get trending protocols.

        Args:
            timeframe: Timeframe ('1d', '7d', '30d')
            limit: Number of protocols to return

        Returns:
            Trending protocols analysis
        """
        result = await self.run(
            f"What are the top {limit} trending protocols over the last {timeframe}? "
            f"Why are they growing?",
            stream=False,
        )
        return result.content


# Example usage
if __name__ == "__main__":
    import asyncio

    async def test_analytics_agent():
        """Test analytics agent with DeFiLlama MCP tools."""
        # Create config
        config = AgnoConfig(
            model_id="gpt-4-turbo",
            temperature=0.7,
            max_tokens=2000,
            show_tool_calls=True,
        )

        # Create analytics agent
        agent = AnalyticsAgent(config, debug_mode=True)

        # Load MCP tools
        print("\n🔧 Loading DeFiLlama MCP tools...")
        await agent.load_mcp_tools()

        print(f"\n✅ Loaded {len(agent.mcp_tools)} analytics tools:")
        for tool in agent.get_available_tools():
            print(f"   • {tool['name']}")

        # Test queries
        test_queries = [
            "What analytics tools do you have?",
            "What's the current TVL of Aave protocol?",
            "Find the best yield opportunities for stablecoins.",
            "Compare Aave and Compound protocols.",
            "What protocols are trending this week?",
        ]

        print("\n" + "=" * 70)
        print("ANALYTICS AGENT TEST")
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
║        Analytics Agent - DeFiLlama Integration           ║
╚══════════════════════════════════════════════════════════╝
    """)

    asyncio.run(test_analytics_agent())
