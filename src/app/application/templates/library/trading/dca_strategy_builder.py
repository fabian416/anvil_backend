"""DCA Strategy Builder Template

Designs Dollar Cost Averaging (DCA) strategies with optimized entry schedules,
size variations, and condition-based adjustments.
"""

from uuid import UUID

from app.domain.entities.chat.conversation_template import (
    AgentStep,
    ConversationTemplate,
    InputSpec,
)


def create_dca_strategy_builder_template(created_by: UUID) -> ConversationTemplate:
    """Create DCA strategy builder template.

    Comprehensive DCA strategy design including:
    - Fixed vs variable interval scheduling
    - Fixed vs dynamic size allocation
    - Condition-based adjustments (volatility, momentum)
    - Historical backtesting
    - Cost basis optimization
    - Exit strategy integration

    Args:
        created_by: User ID creating the template

    Returns:
        Configured ConversationTemplate instance
    """

    agent_sequence = [
        AgentStep(
            agent_name="@portfolio-analyst",
            prompt_template=(
                "Define DCA parameters for {{asset_symbol}}: "
                "1. Investment Parameters: "
                "   - Total capital: {{total_capital}} "
                "   - Investment period: {{investment_period}} "
                "   - Number of entries: {{num_entries}} or calculated "
                "   - Per-entry allocation: total / num_entries "
                "2. Strategy Type: "
                "   - {{strategy_type}}: 'fixed', 'value_averaging', 'dynamic' "
                "   - Fixed: Same $ amount each period "
                "   - Value averaging: Adjust to reach target value "
                "   - Dynamic: Vary based on conditions "
                "3. Current State: "
                "   - Current {{asset_symbol}} price "
                "   - Average price over {{investment_period}} "
                "   - Price volatility "
                "Calculate basic DCA structure"
            ),
            depends_on=[],
            parallel_execution=False,
            timeout_seconds=30,
            outputs=[
                "per_entry_allocation",
                "entry_schedule_outline",
                "current_market_state",
                "dca_structure",
            ],
        ),
        AgentStep(
            agent_name="@quantitative-analyst",
            prompt_template=(
                "Design entry schedule: "
                "For {{num_entries}} entries over {{investment_period}}: "
                "Option 1: Fixed Intervals "
                "- Equal time spacing (e.g., weekly, biweekly, monthly) "
                "- Interval = total_days / num_entries "
                "- Pros: Simple, disciplined "
                "- Cons: May miss volatility opportunities "
                "Option 2: Volatility-Based Intervals "
                "- Buy more frequently in high volatility "
                "- Buy less frequently in low volatility "
                "- Use ATR or Bollinger Band width as trigger "
                "Option 3: Price-Based Intervals "
                "- Buy when price drops X% from last purchase "
                "- Or when price reaches specific levels "
                "- Buy more when price is lower "
                "Option 4: Hybrid "
                "- Fixed interval as baseline "
                "- Add extra purchases on significant dips (>{{dip_threshold}}%) "
                "Recommend optimal interval strategy"
            ),
            depends_on=[0],
            parallel_execution=False,
            timeout_seconds=45,
            outputs=[
                "interval_options",
                "recommended_interval",
                "interval_rationale",
                "dip_thresholds",
            ],
        ),
        AgentStep(
            agent_name="@risk-analyst",
            prompt_template=(
                "Design position sizing per entry: "
                "Total capital: {{total_capital}} "
                "Entries: {{num_entries}} "
                "Strategy 1: Fixed Size "
                "- Amount per entry = {{total_capital}} / {{num_entries}} "
                "- Consistent regardless of price "
                "Strategy 2: Weighted by Price "
                "- Larger buys when price is lower "
                "- Smaller buys when price is higher "
                "- Example: If price is 20% below average, buy 20% more "
                "Strategy 3: Weighted by Volatility "
                "- Larger buys in high volatility (more opportunity) "
                "- Smaller buys in low volatility "
                "Strategy 4: Value Averaging "
                "- Set target portfolio value growth "
                "- Buy amount = target_value - current_value "
                "- May require larger purchases when behind target "
                "For {{strategy_type}}, calculate entry sizes"
            ),
            depends_on=[0],
            parallel_execution=True,
            timeout_seconds=45,
            outputs=[
                "sizing_strategies",
                "recommended_sizes",
                "size_adjustments",
                "reserve_allocation",
            ],
        ),
        AgentStep(
            agent_name="@market-analyst",
            prompt_template=(
                "Define condition-based adjustment rules: "
                "For {{asset_symbol}} DCA strategy: "
                "1. Momentum-Based Adjustments: "
                "   - If strong downtrend: Pause DCA or reduce size "
                "   - If uptrend established: Continue normally "
                "   - Use MA crossovers or RSI to detect regime "
                "2. Volatility-Based Adjustments: "
                "   - If volatility > 150% of average: Increase frequency "
                "   - If volatility < 50% of average: Decrease frequency "
                "   - Use ATR or historical volatility "
                "3. Support/Resistance Adjustments: "
                "   - Add extra buys at major support levels "
                "   - Reduce buys at resistance levels "
                "   - Identify key levels for {{asset_symbol}} "
                "4. News/Event Adjustments: "
                "   - Pause before major events (uncertainty) "
                "   - Buy more after negative news (opportunity) "
                "   - List upcoming events for {{investment_period}} "
                "Create decision tree for adjustments"
            ),
            depends_on=[1, 2],
            parallel_execution=False,
            timeout_seconds=45,
            outputs=[
                "momentum_rules",
                "volatility_rules",
                "level_adjustments",
                "adjustment_tree",
            ],
        ),
        AgentStep(
            agent_name="@data-analyst",
            prompt_template=(
                "Backtest DCA strategy: "
                "For {{asset_symbol}} over last {{backtest_period}}: "
                "Simulate: "
                "1. Fixed DCA: "
                "   - Same $ every interval "
                "   - Calculate final position and returns "
                "2. Dynamic DCA (recommended strategy): "
                "   - Apply rules: {{adjustment_tree}} "
                "   - Size adjustments: {{size_adjustments}} "
                "   - Calculate final position and returns "
                "3. Lump Sum Comparison: "
                "   - What if invested all {{total_capital}} at start "
                "   - Compare vs DCA results "
                "Metrics for each: "
                "- Average cost basis "
                "- Total units purchased "
                "- Unrealized P&L "
                "- Annualized return "
                "- Maximum drawdown "
                "- Sharpe ratio "
                "Show which strategy performed best historically"
            ),
            depends_on=[3],
            parallel_execution=False,
            timeout_seconds=60,
            outputs=[
                "backtest_results",
                "strategy_comparison",
                "performance_metrics",
                "winning_strategy",
            ],
        ),
        AgentStep(
            agent_name="@portfolio-analyst",
            prompt_template=(
                "Design exit strategy for DCA accumulation: "
                "After completing DCA phase: "
                "1. Exit Targets: "
                "   - Target 1: Cost basis + {{profit_target_1}}% (take 30%) "
                "   - Target 2: Cost basis + {{profit_target_2}}% (take 40%) "
                "   - Target 3: Cost basis + {{profit_target_3}}% (let 30% run) "
                "2. Time-Based Exits: "
                "   - Hold for minimum {{min_hold_period}} after last entry "
                "   - Review quarterly for rebalancing "
                "3. Trend-Based Exits: "
                "   - Exit if major downtrend confirmed (MA cross, support break) "
                "   - Implement trailing stop after Target 1 reached "
                "4. Rebalancing: "
                "   - If position grows to >{{max_position}}% of portfolio "
                "   - Take profits to rebalance "
                "Create complete exit plan"
            ),
            depends_on=[4],
            parallel_execution=False,
            timeout_seconds=45,
            outputs=[
                "exit_targets",
                "exit_triggers",
                "trailing_stop",
                "rebalancing_rules",
            ],
        ),
        AgentStep(
            agent_name="@product-manager",
            prompt_template=(
                "Generate comprehensive DCA strategy plan: "
                "1. Strategy Overview: "
                "   - Asset: {{asset_symbol}} "
                "   - Total capital: {{total_capital}} "
                "   - Period: {{investment_period}} "
                "   - Strategy type: {{strategy_type}} "
                "   - Number of entries: {{num_entries}} "
                "2. Entry Schedule: "
                "   - Interval: {{recommended_interval}} "
                "   - Rationale: {{interval_rationale}} "
                "   - Example schedule: [dates] "
                "   - Dip buying threshold: {{dip_thresholds}} "
                "3. Position Sizing: "
                "   - Base size per entry: {{per_entry_allocation}} "
                "   - Adjustments: {{size_adjustments}} "
                "   - Reserve capital: X% for opportunities "
                "4. Adjustment Rules: "
                "   - Momentum: {{momentum_rules}} "
                "   - Volatility: {{volatility_rules}} "
                "   - Key levels: {{level_adjustments}} "
                "   - Decision tree: {{adjustment_tree}} "
                "5. Historical Performance: "
                "   - Backtest period: {{backtest_period}} "
                "   - Results: {{backtest_results}} "
                "   - Best strategy: {{winning_strategy}} "
                "   - Expected avg cost basis: $X "
                "   - Expected return: Y% "
                "6. Exit Strategy: "
                "   - Targets: {{exit_targets}} "
                "   - Scaling: 30% / 40% / 30% "
                "   - Trailing stop: {{trailing_stop}} "
                "   - Rebalancing: {{rebalancing_rules}} "
                "7. Execution Checklist: "
                "   Entry #1 (Date): "
                "   - [ ] Check market conditions "
                "   - [ ] Confirm price in acceptable range "
                "   - [ ] Execute buy for $X "
                "   - [ ] Record cost basis "
                "   - [ ] Set next entry reminder "
                "   [Repeat for all {{num_entries}} entries] "
                "8. Monitoring: "
                "   - Track average cost basis "
                "   - Monitor unrealized P&L "
                "   - Review adjustment triggers weekly "
                "   - Rebalance quarterly"
            ),
            depends_on=[5],
            parallel_execution=False,
            timeout_seconds=60,
            outputs=[
                "dca_strategy_plan",
                "entry_schedule",
                "execution_checklist",
                "monitoring_plan",
            ],
        ),
    ]

    required_inputs = {
        "asset_symbol": InputSpec(
            type="string",
            required=True,
            description="Asset symbol to DCA into (e.g., BTC, ETH)",
        ),
        "total_capital": InputSpec(
            type="number",
            required=True,
            description="Total capital to invest over DCA period",
        ),
        "investment_period": InputSpec(
            type="string",
            required=True,
            description="Investment period (e.g., '3m', '6m', '12m')",
        ),
        "num_entries": InputSpec(
            type="number",
            required=False,
            description="Number of DCA entries (or calculated from period)",
            default=12,
        ),
        "strategy_type": InputSpec(
            type="string",
            required=False,
            description="DCA type: 'fixed', 'value_averaging', 'dynamic'",
            default="dynamic",
        ),
        "dip_threshold": InputSpec(
            type="number",
            required=False,
            description="Price dip % to trigger extra buy",
            default=10,
        ),
        "backtest_period": InputSpec(
            type="string",
            required=False,
            description="Historical backtest period (e.g., '12m', '24m')",
            default="12m",
        ),
        "profit_target_1": InputSpec(
            type="number",
            required=False,
            description="First profit target % above cost basis",
            default=25,
        ),
        "profit_target_2": InputSpec(
            type="number",
            required=False,
            description="Second profit target % above cost basis",
            default=50,
        ),
        "profit_target_3": InputSpec(
            type="number",
            required=False,
            description="Third profit target % above cost basis",
            default=100,
        ),
        "min_hold_period": InputSpec(
            type="string",
            required=False,
            description="Minimum hold period after last entry",
            default="6m",
        ),
        "max_position": InputSpec(
            type="number",
            required=False,
            description="Maximum position % of portfolio before rebalancing",
            default=20,
        ),
    }

    return ConversationTemplate.create(
        name="DCA Strategy Builder",
        description=(
            "Comprehensive Dollar Cost Averaging strategy designer. Creates optimized "
            "DCA plans with intelligent entry scheduling, dynamic position sizing, and "
            "condition-based adjustments. Includes historical backtesting, cost basis "
            "optimization, and integrated exit strategies."
        ),
        category="trading_strategy",
        agent_sequence=agent_sequence,
        required_inputs=required_inputs,
        estimated_duration_seconds=300,  # 5 minutes
        created_by=created_by,
        is_public=True,
        tags=["trading", "dca", "strategy", "accumulation", "long-term"],
    )
