"""Stop Loss Optimization Template

Optimizes stop loss placement using technical analysis, volatility metrics,
and historical data to balance risk protection with minimizing false stops.
"""

from uuid import UUID

from app.domain.entities.chat.conversation_template import (
    AgentStep,
    ConversationTemplate,
    InputSpec,
)


def create_stop_loss_optimization_template(created_by: UUID) -> ConversationTemplate:
    """Create stop loss optimization template.

    Advanced stop loss analysis including:
    - Technical stop placement (swing points, S/R)
    - Volatility-based stops (ATR, Bollinger Bands)
    - Historical whipsaw analysis
    - Optimal stop distance for timeframe
    - Dynamic stop adjustment rules
    - Risk-adjusted position sizing

    Args:
        created_by: User ID creating the template

    Returns:
        Configured ConversationTemplate instance
    """

    agent_sequence = [
        AgentStep(
            agent_name="@market-analyst",
            prompt_template=(
                "Analyze price action for {{asset_symbol}}: "
                "On {{timeframe}} timeframe: "
                "1. Recent Price Structure: "
                "   - Identify last 10 swing highs/lows "
                "   - Calculate swing point distances from current price "
                "   - Find consolidation zones "
                "2. Support/Resistance: "
                "   - Nearest support levels (for longs) "
                "   - Nearest resistance levels (for shorts) "
                "   - Historical significance of levels "
                "3. Current Position: "
                "   - Entry price: {{entry_price}} "
                "   - Position type: {{position_type}} "
                "   - Distance to key levels "
                "Identify logical technical stop locations"
            ),
            depends_on=[],
            parallel_execution=False,
            timeout_seconds=30,
            outputs=[
                "swing_points",
                "support_resistance",
                "technical_stop_candidates",
                "current_structure",
            ],
        ),
        AgentStep(
            agent_name="@technical-analyst",
            prompt_template=(
                "Calculate volatility-based stop levels: "
                "For {{asset_symbol}} on {{timeframe}}: "
                "1. ATR (Average True Range) Analysis: "
                "   - Current ATR value "
                "   - ATR percentile (vs 30-day range) "
                "   - Recommend stop: entry ± {{atr_multiplier}}x ATR "
                "2. Bollinger Bands: "
                "   - Current band width "
                "   - Stop at lower/upper band "
                "3. Standard Deviation: "
                "   - Price volatility (20-period) "
                "   - Stop at {{std_dev_multiplier}} std dev "
                "4. Keltner Channels: "
                "   - Stop beyond channel "
                "Compare all volatility methods and recommend optimal"
            ),
            depends_on=[0],
            parallel_execution=False,
            timeout_seconds=30,
            outputs=[
                "atr_value",
                "atr_stop_level",
                "bollinger_stop",
                "std_dev_stop",
                "volatility_recommendation",
            ],
        ),
        AgentStep(
            agent_name="@data-analyst",
            prompt_template=(
                "Perform historical whipsaw analysis: "
                "For {{asset_symbol}} over last {{lookback_days}} days: "
                "Test different stop distances from entry: "
                "- 1%, 2%, 3%, 5%, 7%, 10% "
                "- Also test ATR-based: 1x, 1.5x, 2x, 2.5x ATR "
                "For each stop distance, calculate: "
                "1. Whipsaw rate: "
                "   - How often stop hit before position profitable "
                "   - False stop percentage "
                "2. Win rate impact: "
                "   - Actual win rate with each stop "
                "   - Comparison to loose vs tight stops "
                "3. Average loss: "
                "   - Average $ lost when stopped out "
                "   - Largest loss with each stop "
                "Find optimal stop distance that minimizes whipsaws while controlling risk"
            ),
            depends_on=[1],
            parallel_execution=False,
            timeout_seconds=60,
            outputs=[
                "whipsaw_rates",
                "win_rates_by_stop",
                "avg_loss_by_stop",
                "optimal_stop_distance",
            ],
        ),
        AgentStep(
            agent_name="@risk-analyst",
            prompt_template=(
                "Calculate risk-based position sizing: "
                "Given: "
                "- Entry: {{entry_price}} "
                "- Account size: {{account_size}} "
                "- Max risk per trade: {{risk_percentage}}% "
                "For each stop candidate: "
                "1. Technical stops: {{technical_stop_candidates}} "
                "2. Volatility stops: {{volatility_recommendation}} "
                "3. Optimal historical stop: {{optimal_stop_distance}} "
                "Calculate: "
                "- Risk in dollars (entry - stop) × position_size "
                "- Maximum position size for {{risk_percentage}}% risk "
                "- Effective leverage required "
                "- Liquidation distance (for leveraged positions) "
                "Ensure position size keeps risk within limits for each stop option"
            ),
            depends_on=[2],
            parallel_execution=True,
            timeout_seconds=30,
            outputs=[
                "risk_dollars_by_stop",
                "position_sizes_by_stop",
                "leverage_required",
                "liquidation_levels",
            ],
        ),
        AgentStep(
            agent_name="@portfolio-analyst",
            prompt_template=(
                "Compare stop loss strategies: "
                "Evaluate each approach: "
                "1. Fixed Percentage Stop: "
                "   - Stop at {{entry_price}} ± X% "
                "   - Pros: Simple, consistent risk "
                "   - Cons: Ignores market structure "
                "2. Technical Stop: "
                "   - Stop at {{technical_stop_candidates}} "
                "   - Pros: Market structure-based "
                "   - Cons: Variable risk amount "
                "3. Volatility Stop (ATR): "
                "   - Stop at {{atr_stop_level}} "
                "   - Pros: Adapts to volatility "
                "   - Cons: Widens in volatile markets "
                "4. Hybrid Approach: "
                "   - Use technical level if within ATR range "
                "   - Otherwise use ATR stop "
                "   - Balance structure and volatility "
                "Recommend best approach for {{position_type}} position"
            ),
            depends_on=[3],
            parallel_execution=False,
            timeout_seconds=45,
            outputs=[
                "strategy_comparison",
                "pros_cons",
                "recommended_approach",
                "approach_rationale",
            ],
        ),
        AgentStep(
            agent_name="@risk-analyst",
            prompt_template=(
                "Design dynamic stop management rules: "
                "For active {{position_type}} position: "
                "1. Breakeven Stop: "
                "   - Move stop to breakeven after price moves {{breakeven_trigger}}x risk "
                "   - Timing: Immediate or wait for confirmation "
                "2. Trailing Stop: "
                "   - Activate after {{trailing_trigger}} profit "
                "   - Trail method: "
                "     * Fixed distance (e.g., -1 ATR) "
                "     * Percentage (e.g., -5% from high) "
                "     * Parabolic SAR "
                "     * Swing low/high tracking "
                "3. Time-Based Adjustments: "
                "   - Tighten stop if no progress after X hours "
                "   - Widen stop on timeframe change (e.g., day → week) "
                "4. Volatility Adjustments: "
                "   - Widen stop if ATR increases >50% "
                "   - Tighten stop if volatility contracts "
                "Create decision tree for stop management"
            ),
            depends_on=[4],
            parallel_execution=False,
            timeout_seconds=45,
            outputs=[
                "breakeven_rules",
                "trailing_stop_method",
                "adjustment_triggers",
                "stop_management_tree",
            ],
        ),
        AgentStep(
            agent_name="@product-manager",
            prompt_template=(
                "Generate comprehensive stop loss plan: "
                "1. Initial Stop Recommendation: "
                "   - Recommended approach: {{recommended_approach}} "
                "   - Stop level: {{atr_stop_level}} or {{technical_stop_candidates}} "
                "   - Distance from entry: X% or Y ATR "
                "   - Rationale: {{approach_rationale}} "
                "2. Position Sizing: "
                "   - Entry: {{entry_price}} "
                "   - Stop: [calculated level] "
                "   - Risk: {{risk_percentage}}% of {{account_size}} = $X "
                "   - Position size: {{position_sizes_by_stop}} "
                "   - Leverage (if any): {{leverage_required}} "
                "3. Historical Analysis: "
                "   - Whipsaw rate: {{whipsaw_rates}} "
                "   - Expected win rate: {{win_rates_by_stop}} "
                "   - Average loss if stopped: {{avg_loss_by_stop}} "
                "4. Dynamic Management: "
                "   - Breakeven: {{breakeven_rules}} "
                "   - Trailing: {{trailing_stop_method}} "
                "   - Adjustments: {{adjustment_triggers}} "
                "5. Execution: "
                "   - Set stop immediately after entry "
                "   - Stop order type: Stop-limit (avoid slippage) "
                "   - Limit buffer: 0.5% below stop for liquidity "
                "   - Monitor: {{stop_management_tree}} "
                "6. Risk Metrics: "
                "   - Max loss if stopped: $X "
                "   - Risk/reward ratio: 1:{{min_risk_reward}} "
                "   - Account impact: {{risk_percentage}}% "
                "   - Liquidation risk: {{liquidation_levels}}"
            ),
            depends_on=[5],
            parallel_execution=False,
            timeout_seconds=60,
            outputs=[
                "stop_loss_plan",
                "initial_stop",
                "position_size",
                "management_rules",
            ],
        ),
    ]

    required_inputs = {
        "asset_symbol": InputSpec(
            type="string",
            required=True,
            description="Asset symbol (e.g., BTC, ETH, LINK)",
        ),
        "position_type": InputSpec(
            type="string",
            required=True,
            description="Position type: 'long' or 'short'",
        ),
        "entry_price": InputSpec(
            type="number",
            required=True,
            description="Entry price for the position",
        ),
        "timeframe": InputSpec(
            type="string",
            required=False,
            description="Trading timeframe: '1h', '4h', '1d', '1w'",
            default="4h",
        ),
        "account_size": InputSpec(
            type="number",
            required=False,
            description="Total account size in USD",
            default=10000,
        ),
        "risk_percentage": InputSpec(
            type="number",
            required=False,
            description="Maximum risk per trade as % of account",
            default=1,
        ),
        "atr_multiplier": InputSpec(
            type="number",
            required=False,
            description="ATR multiplier for volatility-based stop (e.g., 1.5)",
            default=1.5,
        ),
        "std_dev_multiplier": InputSpec(
            type="number",
            required=False,
            description="Standard deviation multiplier for stop (e.g., 2)",
            default=2,
        ),
        "lookback_days": InputSpec(
            type="number",
            required=False,
            description="Days of historical data for whipsaw analysis",
            default=90,
        ),
        "breakeven_trigger": InputSpec(
            type="number",
            required=False,
            description="Move to breakeven after price moves X times initial risk",
            default=1,
        ),
        "trailing_trigger": InputSpec(
            type="number",
            required=False,
            description="Activate trailing stop after X% profit",
            default=5,
        ),
        "min_risk_reward": InputSpec(
            type="number",
            required=False,
            description="Minimum risk/reward ratio target",
            default=2,
        ),
    }

    return ConversationTemplate.create(
        name="Stop Loss Optimization",
        description=(
            "Advanced stop loss optimization using technical analysis, volatility metrics, "
            "and historical whipsaw analysis. Calculates optimal stop placement balancing "
            "risk protection with minimizing false stops. Includes dynamic stop management "
            "rules and risk-adjusted position sizing."
        ),
        category="trading_strategy",
        agent_sequence=agent_sequence,
        required_inputs=required_inputs,
        estimated_duration_seconds=270,  # 4.5 minutes
        created_by=created_by,
        is_public=True,
        tags=["trading", "stop-loss", "risk-management", "position-sizing"],
    )
