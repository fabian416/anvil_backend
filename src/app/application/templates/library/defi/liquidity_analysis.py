"""Liquidity Analysis Template

Analyzes liquidity depth, slippage, and market impact for DeFi trading pairs
to optimize trade execution and identify liquidity risks.
"""

from uuid import UUID

from app.domain.entities.chat.conversation_template import (
    AgentStep,
    ConversationTemplate,
    InputSpec,
)


def create_liquidity_analysis_template(created_by: UUID) -> ConversationTemplate:
    """Create liquidity analysis template.

    Comprehensive liquidity assessment including:
    - Pool depth and liquidity distribution
    - Slippage calculations for various trade sizes
    - Market impact analysis
    - Liquidity provider composition
    - Historical liquidity trends
    - Optimal execution strategies

    Args:
        created_by: User ID creating the template

    Returns:
        Configured ConversationTemplate instance
    """

    agent_sequence = [
        AgentStep(
            agent_name="@defi-specialist",
            prompt_template=(
                "Identify liquidity venues for {{trading_pair}}: "
                "Search across: "
                "- DEXes: Uniswap V2/V3, Curve, Balancer, SushiSwap "
                "- Aggregators: 1inch, Paraswap, Matcha "
                "- Chain: {{chain}} "
                "For each venue, gather: "
                "- Pool address and type (AMM model) "
                "- Total liquidity (USD) "
                "- 24h volume "
                "- Fee tier "
                "- Concentrated liquidity ranges (if applicable)"
            ),
            depends_on=[],
            parallel_execution=False,
            timeout_seconds=30,
            outputs=[
                "liquidity_venues",
                "pool_addresses",
                "total_liquidity_by_venue",
                "volume_24h",
                "fee_tiers",
            ],
        ),
        AgentStep(
            agent_name="@quantitative-analyst",
            prompt_template=(
                "Calculate liquidity depth metrics: "
                "For each venue from {{liquidity_venues}}: "
                "1. Liquidity Distribution: "
                "   - Bid/ask spread at current price "
                "   - Depth at ±1%, ±5%, ±10% from mid price "
                "   - Price impact for {{trade_size}} "
                "2. Order Book Simulation: "
                "   - Simulate trades from $1K to $1M "
                "   - Calculate effective price and slippage "
                "3. Liquidity Score: "
                "   - Volume/Liquidity ratio "
                "   - Depth concentration "
                "Create depth chart showing available liquidity by price level"
            ),
            depends_on=[0],
            parallel_execution=False,
            timeout_seconds=60,
            outputs=[
                "depth_by_price_level",
                "slippage_estimates",
                "liquidity_scores",
                "depth_chart",
            ],
        ),
        AgentStep(
            agent_name="@quantitative-analyst",
            prompt_template=(
                "Perform slippage analysis for target trade: "
                "Trade details: "
                "- Pair: {{trading_pair}} "
                "- Size: {{trade_size}} "
                "- Direction: {{trade_direction}} "
                "Calculate: "
                "1. Expected slippage per venue "
                "2. Total cost including: "
                "   - Slippage "
                "   - Protocol fees "
                "   - Gas costs "
                "3. Best execution route: "
                "   - Single venue vs split order "
                "   - Optimal routing through aggregator "
                "4. Market impact: "
                "   - Price impact percentage "
                "   - Recovery time estimate"
            ),
            depends_on=[1],
            parallel_execution=False,
            timeout_seconds=45,
            outputs=[
                "slippage_by_venue",
                "total_cost_breakdown",
                "optimal_route",
                "market_impact",
            ],
        ),
        AgentStep(
            agent_name="@data-analyst",
            prompt_template=(
                "Analyze liquidity provider composition: "
                "For top 3 pools from {{liquidity_venues}}: "
                "- Number of LPs "
                "- Top 10 LP positions (% of pool) "
                "- Whale concentration (top 3 LP %) "
                "- LP stability: "
                "  * Average LP duration "
                "  * Recent LP additions/removals "
                "- Impermanent loss for LPs "
                "Assess rug pull risk and LP retention"
            ),
            depends_on=[0],
            parallel_execution=True,
            timeout_seconds=45,
            outputs=[
                "lp_count",
                "whale_concentration",
                "lp_stability_metrics",
                "il_estimates",
                "rug_risk_score",
            ],
        ),
        AgentStep(
            agent_name="@market-analyst",
            prompt_template=(
                "Analyze historical liquidity trends: "
                "For {{trading_pair}} over {{time_period}}: "
                "1. Liquidity Evolution: "
                "   - Total liquidity chart (30d/90d) "
                "   - Significant liquidity events "
                "   - Correlation with price action "
                "2. Volume Patterns: "
                "   - Average daily volume "
                "   - Volume spikes and causes "
                "   - Volume/Liquidity ratio trends "
                "3. Volatility Impact: "
                "   - Liquidity during high volatility "
                "   - Flash crash vulnerability "
                "Predict liquidity stability for next 7 days"
            ),
            depends_on=[0],
            parallel_execution=True,
            timeout_seconds=60,
            outputs=[
                "liquidity_history",
                "volume_patterns",
                "volatility_correlation",
                "stability_forecast",
            ],
        ),
        AgentStep(
            agent_name="@defi-specialist",
            prompt_template=(
                "Identify liquidity risks and anomalies: "
                "Check for: "
                "1. Liquidity Fragmentation: "
                "   - Too many small pools "
                "   - Split across chains "
                "2. Asymmetric Liquidity: "
                "   - One-sided depth "
                "   - Unusual buy/sell ratios "
                "3. Artificial Liquidity: "
                "   - Mercenary capital (high APR only) "
                "   - Protocol-owned liquidity % "
                "4. Oracle Manipulation Risk: "
                "   - Thin liquidity allowing price manipulation "
                "   - Flash loan attack surface "
                "5. Regulatory Risk: "
                "   - Potential liquidity provider exit risks"
            ),
            depends_on=[3, 4],
            parallel_execution=False,
            timeout_seconds=45,
            outputs=[
                "liquidity_risks",
                "anomalies",
                "manipulation_risk",
                "risk_severity",
            ],
        ),
        AgentStep(
            agent_name="@portfolio-analyst",
            prompt_template=(
                "Generate execution recommendations: "
                "Based on analysis: "
                "1. For Trade Size {{trade_size}}: "
                "   - Recommended venue/route: {{optimal_route}} "
                "   - Expected slippage: {{slippage_by_venue}} "
                "   - Best execution time (avoid low liquidity hours) "
                "   - Limit order vs market order "
                "2. For Larger Positions: "
                "   - TWAP strategy parameters "
                "   - Split order sizes "
                "   - Multi-venue execution "
                "3. Risk Management: "
                "   - Maximum position size given liquidity "
                "   - Stop loss feasibility "
                "   - Emergency exit liquidity "
                "4. Ongoing Monitoring: "
                "   - Liquidity alerts to set "
                "   - Pool health indicators "
                "   - When to reassess"
            ),
            depends_on=[2, 5],
            parallel_execution=False,
            timeout_seconds=45,
            outputs=[
                "execution_strategy",
                "position_size_limits",
                "monitoring_plan",
                "liquidity_alerts",
            ],
        ),
        AgentStep(
            agent_name="@product-manager",
            prompt_template=(
                "Create comprehensive liquidity report: "
                "1. Executive Summary: "
                "   - Overall liquidity rating: [Excellent/Good/Moderate/Poor] "
                "   - Maximum trade size without significant slippage "
                "   - Recommended execution strategy "
                "2. Liquidity Landscape: "
                "   - Venues ranked by liquidity: {{total_liquidity_by_venue}} "
                "   - Depth chart: {{depth_chart}} "
                "   - Historical trends: {{liquidity_history}} "
                "3. Trade Analysis ({{trade_size}}): "
                "   - Slippage: {{slippage_estimates}} "
                "   - Market impact: {{market_impact}} "
                "   - Total cost: {{total_cost_breakdown}} "
                "   - Optimal route: {{optimal_route}} "
                "4. Risks & Considerations: "
                "   - Liquidity risks: {{liquidity_risks}} "
                "   - LP concentration: {{whale_concentration}} "
                "   - Stability forecast: {{stability_forecast}} "
                "5. Action Plan: "
                "   - Execution strategy: {{execution_strategy}} "
                "   - Position limits: {{position_size_limits}} "
                "   - Monitoring: {{monitoring_plan}}"
            ),
            depends_on=[6],
            parallel_execution=False,
            timeout_seconds=60,
            outputs=[
                "liquidity_report",
                "liquidity_rating",
                "final_recommendations",
            ],
        ),
    ]

    required_inputs = {
        "trading_pair": InputSpec(
            type="string",
            required=True,
            description="Trading pair to analyze (e.g., ETH/USDC, WBTC/ETH)",
        ),
        "chain": InputSpec(
            type="string",
            required=False,
            description="Blockchain network (ethereum, arbitrum, polygon, etc.)",
            default="ethereum",
        ),
        "trade_size": InputSpec(
            type="string",
            required=False,
            description="Target trade size in USD (e.g., '10000' for $10K)",
            default="10000",
        ),
        "trade_direction": InputSpec(
            type="string",
            required=False,
            description="Trade direction: 'buy' or 'sell'",
            default="buy",
        ),
        "time_period": InputSpec(
            type="string",
            required=False,
            description="Historical analysis period: '30d', '90d', '180d'",
            default="30d",
        ),
    }

    return ConversationTemplate.create(
        name="Liquidity Analysis",
        description=(
            "Comprehensive liquidity analysis for DeFi trading pairs. Analyzes pool depth, "
            "calculates slippage for various trade sizes, assesses LP composition, reviews "
            "historical trends, and provides optimal execution strategies. Includes risk "
            "assessment and position sizing recommendations."
        ),
        category="defi_analysis",
        agent_sequence=agent_sequence,
        required_inputs=required_inputs,
        estimated_duration_seconds=330,  # 5.5 minutes
        created_by=created_by,
        is_public=True,
        tags=["defi", "liquidity", "trading", "slippage", "execution"],
    )
