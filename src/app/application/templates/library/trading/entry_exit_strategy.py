"""Entry/Exit Strategy Template

Develops optimal entry and exit strategies for trading positions based on
technical analysis, market conditions, and risk management principles.
"""

from uuid import UUID

from app.domain.entities.chat.conversation_template import (
    AgentStep,
    ConversationTemplate,
    InputSpec,
)


def create_entry_exit_strategy_template(created_by: UUID) -> ConversationTemplate:
    """Create entry/exit strategy template.

    Comprehensive strategy development including:
    - Market structure and trend analysis
    - Entry zone identification (support/resistance)
    - Confirmation signals and indicators
    - Exit targets (take profit levels)
    - Stop loss placement
    - Risk/reward optimization

    Args:
        created_by: User ID creating the template

    Returns:
        Configured ConversationTemplate instance
    """

    agent_sequence = [
        AgentStep(
            agent_name="@market-analyst",
            prompt_template=(
                "Analyze market structure for {{asset_symbol}}: "
                "1. Trend Identification: "
                "   - Higher timeframe trend (daily/weekly): bullish/bearish/ranging "
                "   - Current phase: accumulation/markup/distribution/markdown "
                "   - Trend strength: strong/moderate/weak "
                "2. Key Levels: "
                "   - Major support zones (last 3 months) "
                "   - Major resistance zones "
                "   - Historical high/low significance "
                "3. Market Context: "
                "   - Overall market sentiment (for crypto: BTC correlation) "
                "   - Sector performance "
                "   - Recent news/events impact "
                "   - Liquidity conditions"
            ),
            depends_on=[],
            parallel_execution=False,
            timeout_seconds=45,
            outputs=[
                "trend_direction",
                "trend_strength",
                "support_levels",
                "resistance_levels",
                "market_phase",
            ],
        ),
        AgentStep(
            agent_name="@technical-analyst",
            prompt_template=(
                "Identify entry opportunities for {{position_type}} position: "
                "Based on trend: {{trend_direction}} "
                "{% if position_type == 'long' %} "
                "Find bullish entry setups: "
                "- Pullbacks to support ({{support_levels}}) "
                "- Breakout above resistance with retest "
                "- Reversal patterns at key levels "
                "{% else %} "
                "Find bearish entry setups: "
                "- Rallies to resistance ({{resistance_levels}}) "
                "- Breakdown below support with retest "
                "- Reversal patterns at key levels "
                "{% endif %} "
                "For each setup, identify: "
                "- Optimal entry zone (price range) "
                "- Required confirmation signals "
                "- Expected timeframe for setup completion "
                "Prioritize highest probability setups"
            ),
            depends_on=[0],
            parallel_execution=False,
            timeout_seconds=45,
            outputs=[
                "entry_setups",
                "entry_zones",
                "confirmation_signals",
                "setup_probability",
            ],
        ),
        AgentStep(
            agent_name="@technical-analyst",
            prompt_template=(
                "Develop multi-indicator confirmation system: "
                "For {{asset_symbol}} on {{timeframe}} timeframe: "
                "1. Momentum Indicators: "
                "   - RSI: Oversold (<30) for longs, Overbought (>70) for shorts "
                "   - MACD: Bullish/bearish crossover "
                "   - Stochastic: Oversold/overbought conditions "
                "2. Trend Indicators: "
                "   - Moving averages: 20/50/200 EMA alignment "
                "   - Price position relative to EMAs "
                "   - ADX: Trend strength (>25 = trending) "
                "3. Volume Analysis: "
                "   - Volume profile at key levels "
                "   - Volume confirmation on breakouts "
                "   - Unusual volume spikes "
                "Create scoring system: 3+ confirmations = high probability entry"
            ),
            depends_on=[1],
            parallel_execution=False,
            timeout_seconds=45,
            outputs=[
                "momentum_signals",
                "trend_signals",
                "volume_analysis",
                "confirmation_score",
            ],
        ),
        AgentStep(
            agent_name="@risk-analyst",
            prompt_template=(
                "Design stop loss strategy: "
                "For entry zones: {{entry_zones}} "
                "Calculate stop loss placement: "
                "1. Technical Stops: "
                "   - Below/above swing low/high "
                "   - Beyond support/resistance (with buffer) "
                "   - ATR-based stop ({{atr_multiplier}}x ATR) "
                "2. Risk-Based Stops: "
                "   - Maximum risk per trade: {{risk_percentage}}% "
                "   - Position size calculation for each stop level "
                "3. Time-Based Stops: "
                "   - Exit if setup invalidates (timeframe dependent) "
                "   - Maximum holding period if no movement "
                "Recommend optimal stop placement balancing risk and whipsaw avoidance"
            ),
            depends_on=[1],
            parallel_execution=True,
            timeout_seconds=30,
            outputs=[
                "stop_loss_levels",
                "stop_rationale",
                "position_sizes",
                "invalidation_criteria",
            ],
        ),
        AgentStep(
            agent_name="@portfolio-analyst",
            prompt_template=(
                "Define exit targets and profit-taking strategy: "
                "Based on: "
                "- Entry zones: {{entry_zones}} "
                "- Stop levels: {{stop_loss_levels}} "
                "- Resistance: {{resistance_levels}} (for longs) "
                "- Support: {{support_levels}} (for shorts) "
                "1. Target Identification: "
                "   - Target 1: Risk/reward ratio {{min_risk_reward}} (conservative) "
                "   - Target 2: Next major resistance/support "
                "   - Target 3: Measured move or extension level "
                "2. Scaling Strategy: "
                "   - Take 30% profit at Target 1 "
                "   - Take 40% profit at Target 2 "
                "   - Let 30% run to Target 3 or trailing stop "
                "3. Trailing Stop: "
                "   - Activate after Target 1 reached "
                "   - Trail at breakeven +1 ATR "
                "   - Lock in profits progressively "
                "4. Time-Based Exits: "
                "   - If targets not hit in expected timeframe "
                "   - Re-evaluate position on each new swing high/low"
            ),
            depends_on=[3],
            parallel_execution=False,
            timeout_seconds=45,
            outputs=[
                "profit_targets",
                "scaling_plan",
                "trailing_stop_rules",
                "time_based_exits",
            ],
        ),
        AgentStep(
            agent_name="@risk-analyst",
            prompt_template=(
                "Calculate risk/reward profile: "
                "For each entry setup in {{entry_setups}}: "
                "Using: "
                "- Entry: {{entry_zones}} "
                "- Stop: {{stop_loss_levels}} "
                "- Targets: {{profit_targets}} "
                "Calculate: "
                "1. Risk per trade (entry - stop): "
                "   - Dollar risk for position size "
                "   - Percentage of account risk "
                "2. Reward potential: "
                "   - Target 1 R:R ratio "
                "   - Target 2 R:R ratio "
                "   - Target 3 R:R ratio "
                "   - Average expected R:R "
                "3. Expected Value: "
                "   - Win probability × Avg reward "
                "   - Loss probability × Risk "
                "   - Positive expectancy required "
                "4. Position Sizing: "
                "   - Optimal position for {{risk_percentage}}% risk "
                "   - Kelly Criterion suggestion "
                "Rank setups by expected value"
            ),
            depends_on=[4],
            parallel_execution=False,
            timeout_seconds=30,
            outputs=[
                "risk_amounts",
                "reward_amounts",
                "risk_reward_ratios",
                "expected_values",
                "ranked_setups",
            ],
        ),
        AgentStep(
            agent_name="@portfolio-analyst",
            prompt_template=(
                "Develop entry execution plan: "
                "For top-ranked setup: {{ranked_setups}} "
                "1. Pre-Entry Checklist: "
                "   - Confirm trend: {{trend_direction}} "
                "   - Wait for price in entry zone: {{entry_zones}} "
                "   - Verify confirmations: {{confirmation_signals}} "
                "   - Check market conditions: volatility, liquidity "
                "2. Entry Tactics: "
                "   - Limit order at entry zone boundary "
                "   - Scale in: 50% at first touch, 50% on confirmation "
                "   - Market order if strong momentum (breakout) "
                "3. Post-Entry Management: "
                "   - Set stop loss immediately: {{stop_loss_levels}} "
                "   - Set alerts for profit targets "
                "   - Monitor confirmation indicators "
                "4. Plan B (if setup fails): "
                "   - Alternative entry levels "
                "   - When to abandon setup "
                "   - Invalidation signs to watch"
            ),
            depends_on=[5],
            parallel_execution=False,
            timeout_seconds=45,
            outputs=[
                "pre_entry_checklist",
                "entry_tactics",
                "post_entry_rules",
                "contingency_plan",
            ],
        ),
        AgentStep(
            agent_name="@product-manager",
            prompt_template=(
                "Create comprehensive trading plan: "
                "1. Market Analysis Summary: "
                "   - Asset: {{asset_symbol}} "
                "   - Trend: {{trend_direction}} ({{trend_strength}}) "
                "   - Phase: {{market_phase}} "
                "   - Key levels: S {{support_levels}} / R {{resistance_levels}} "
                "2. Trading Setup: "
                "   - Position type: {{position_type}} "
                "   - Entry zones: {{entry_zones}} "
                "   - Confirmations needed: {{confirmation_signals}} "
                "   - Probability: {{setup_probability}} "
                "3. Risk Management: "
                "   - Stop loss: {{stop_loss_levels}} "
                "   - Risk per trade: {{risk_percentage}}% ({{risk_amounts}}) "
                "   - Position size: {{position_sizes}} "
                "4. Exit Strategy: "
                "   - Target 1: {{profit_targets}}[0] (take 30%) "
                "   - Target 2: {{profit_targets}}[1] (take 40%) "
                "   - Target 3: {{profit_targets}}[2] (let 30% run) "
                "   - Trailing stop: {{trailing_stop_rules}} "
                "5. Risk/Reward: "
                "   - Average R:R: {{risk_reward_ratios}} "
                "   - Expected value: {{expected_values}} "
                "6. Execution Plan: "
                "   - Pre-entry: {{pre_entry_checklist}} "
                "   - Entry: {{entry_tactics}} "
                "   - Management: {{post_entry_rules}} "
                "   - Exit: {{scaling_plan}} "
                "7. Contingencies: "
                "   - Invalidation: {{invalidation_criteria}} "
                "   - Plan B: {{contingency_plan}}"
            ),
            depends_on=[6],
            parallel_execution=False,
            timeout_seconds=60,
            outputs=[
                "trading_plan",
                "risk_summary",
                "execution_checklist",
            ],
        ),
    ]

    required_inputs = {
        "asset_symbol": InputSpec(
            type="string",
            required=True,
            description="Asset symbol to trade (e.g., BTC, ETH, LINK)",
        ),
        "position_type": InputSpec(
            type="string",
            required=True,
            description="Position type: 'long' or 'short'",
        ),
        "timeframe": InputSpec(
            type="string",
            required=False,
            description="Trading timeframe: '1h', '4h', '1d', '1w'",
            default="4h",
        ),
        "risk_percentage": InputSpec(
            type="number",
            required=False,
            description="Risk per trade as % of account",
            default=1,
        ),
        "min_risk_reward": InputSpec(
            type="number",
            required=False,
            description="Minimum acceptable risk/reward ratio",
            default=2,
        ),
        "atr_multiplier": InputSpec(
            type="number",
            required=False,
            description="ATR multiplier for stop loss (e.g., 1.5)",
            default=1.5,
        ),
    }

    return ConversationTemplate.create(
        name="Entry/Exit Strategy",
        description=(
            "Comprehensive trading strategy development for optimal entries and exits. "
            "Analyzes market structure, identifies high-probability setups, develops "
            "multi-indicator confirmation systems, calculates stop losses and profit targets, "
            "and creates detailed execution plans with risk management."
        ),
        category="trading_strategy",
        agent_sequence=agent_sequence,
        required_inputs=required_inputs,
        estimated_duration_seconds=300,  # 5 minutes
        created_by=created_by,
        is_public=True,
        tags=["trading", "strategy", "entry", "exit", "risk-management"],
    )
