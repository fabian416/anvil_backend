"""Position Sizing Template

Calculates optimal position sizes using various methodologies including
fixed risk, Kelly Criterion, and volatility-based approaches.
"""

from uuid import UUID

from app.domain.entities.chat.conversation_template import (
    AgentStep,
    ConversationTemplate,
    InputSpec,
)


def create_position_sizing_template(created_by: UUID) -> ConversationTemplate:
    """Create position sizing template.

    Comprehensive position sizing analysis including:
    - Fixed risk percentage method
    - Kelly Criterion optimization
    - Volatility-adjusted sizing
    - Portfolio correlation analysis
    - Maximum position limits
    - Leverage considerations

    Args:
        created_by: User ID creating the template

    Returns:
        Configured ConversationTemplate instance
    """

    agent_sequence = [
        AgentStep(
            agent_name="@portfolio-analyst",
            prompt_template=(
                "Gather account and position information: "
                "1. Account Details: "
                "   - Total account size: {{account_size}} "
                "   - Available capital (not in positions) "
                "   - Current positions and exposure "
                "   - Cash reserves requirement "
                "2. Position Details: "
                "   - Asset: {{asset_symbol}} "
                "   - Entry price: {{entry_price}} "
                "   - Stop loss: {{stop_loss}} "
                "   - Risk per unit: (entry - stop) "
                "3. Risk Parameters: "
                "   - Max risk per trade: {{risk_per_trade}}% "
                "   - Max portfolio risk: {{max_portfolio_risk}}% "
                "   - Current portfolio risk exposure "
                "Calculate basic position parameters"
            ),
            depends_on=[],
            parallel_execution=False,
            timeout_seconds=30,
            outputs=[
                "available_capital",
                "current_exposure",
                "risk_per_unit",
                "basic_parameters",
            ],
        ),
        AgentStep(
            agent_name="@risk-analyst",
            prompt_template=(
                "Calculate fixed risk position size: "
                "Method 1: Fixed Dollar Risk "
                "- Risk amount = {{account_size}} × {{risk_per_trade}}% "
                "- Risk per unit = {{entry_price}} - {{stop_loss}} "
                "- Position size = Risk amount / Risk per unit "
                "Method 2: Fixed Percentage "
                "- Position = {{account_size}} × {{position_percentage}}% "
                "- Verify risk is within limits "
                "Method 3: Volatility-Weighted "
                "- Base size from Method 1 "
                "- Adjust for volatility: size × (avg_volatility / current_volatility) "
                "- High volatility → smaller position "
                "- Low volatility → larger position "
                "Calculate all three methods"
            ),
            depends_on=[0],
            parallel_execution=False,
            timeout_seconds=30,
            outputs=[
                "fixed_dollar_risk_size",
                "fixed_percentage_size",
                "volatility_adjusted_size",
                "method_comparison",
            ],
        ),
        AgentStep(
            agent_name="@quantitative-analyst",
            prompt_template=(
                "Calculate Kelly Criterion position size: "
                "Kelly formula: f* = (bp - q) / b "
                "Where: "
                "- p = win probability (from {{win_rate}}% or historical) "
                "- q = loss probability (1 - p) "
                "- b = win/loss ratio (avg_win / avg_loss) "
                "Steps: "
                "1. Estimate win rate for {{asset_symbol}} "
                "   - Use historical win rate if available "
                "   - Or estimate from setup quality "
                "2. Calculate average win/loss ratio "
                "   - From profit target vs stop distance "
                "   - Or historical performance "
                "3. Apply Kelly: "
                "   - Full Kelly = f* × account_size "
                "   - Half Kelly = 0.5 × f* × account_size (conservative) "
                "   - Quarter Kelly = 0.25 × f* × account_size (very conservative) "
                "4. Compare to fixed risk method "
                "   - Flag if Kelly suggests much larger size (potential overbet)"
            ),
            depends_on=[0],
            parallel_execution=True,
            timeout_seconds=45,
            outputs=[
                "win_rate_estimate",
                "win_loss_ratio",
                "kelly_percentage",
                "kelly_position_sizes",
            ],
        ),
        AgentStep(
            agent_name="@market-analyst",
            prompt_template=(
                "Analyze market and correlation factors: "
                "For {{asset_symbol}}: "
                "1. Market Conditions: "
                "   - Current volatility vs average "
                "   - Trending vs ranging market "
                "   - Liquidity conditions "
                "2. Correlation Analysis: "
                "   - Correlation with existing positions "
                "   - Correlation with BTC (for crypto) "
                "   - Sector concentration risk "
                "3. Concentration Limits: "
                "   - % of portfolio in single asset "
                "   - % in correlated assets "
                "   - Max recommended: {{max_single_position}}% "
                "4. Adjustments: "
                "   - Reduce size if high correlation with existing positions "
                "   - Reduce size in high volatility environments "
                "   - Reduce size if illiquid market"
            ),
            depends_on=[0],
            parallel_execution=True,
            timeout_seconds=45,
            outputs=[
                "volatility_regime",
                "correlation_scores",
                "concentration_risk",
                "size_adjustments",
            ],
        ),
        AgentStep(
            agent_name="@risk-analyst",
            prompt_template=(
                "Calculate leverage and margin requirements: "
                "For position sizes calculated: "
                "- Fixed risk: {{fixed_dollar_risk_size}} "
                "- Kelly: {{kelly_position_sizes}} "
                "Account capital: {{available_capital}} "
                "1. Leverage Calculation: "
                "   - Required leverage = Position size / Available capital "
                "   - If >1x, leverage is needed "
                "2. Margin Requirements: "
                "   - Initial margin (exchange specific) "
                "   - Maintenance margin level "
                "   - Buffer for volatility "
                "3. Liquidation Risk: "
                "   - Liquidation price for leveraged position "
                "   - Distance from liquidation % "
                "   - Risk of forced exit "
                "4. Constraints: "
                "   - Max leverage allowed: {{max_leverage}}x "
                "   - Reduce position if exceeds max leverage "
                "   - Account for funding costs if leveraged "
                "Flag if position requires risky leverage levels"
            ),
            depends_on=[1, 2],
            parallel_execution=False,
            timeout_seconds=30,
            outputs=[
                "leverage_required",
                "margin_requirements",
                "liquidation_price",
                "leverage_warnings",
            ],
        ),
        AgentStep(
            agent_name="@portfolio-analyst",
            prompt_template=(
                "Apply position sizing constraints and limits: "
                "Review calculated sizes: "
                "- Fixed risk: {{fixed_dollar_risk_size}} "
                "- Volatility-adjusted: {{volatility_adjusted_size}} "
                "- Kelly (half): {{kelly_position_sizes}} "
                "Apply constraints: "
                "1. Account Limits: "
                "   - Max per position: {{max_single_position}}% of account "
                "   - Max portfolio risk: {{max_portfolio_risk}}% "
                "   - Current risk + new position must be < max "
                "2. Practical Limits: "
                "   - Minimum position: {{min_position_size}} (avoid dust) "
                "   - Exchange minimum order size "
                "   - Round to tradeable increment "
                "3. Liquidity Limits: "
                "   - Max % of daily volume: {{max_volume_percentage}}% "
                "   - Reduce if size would impact market "
                "4. Correlation Limits: "
                "   - Reduce if high correlation: {{correlation_scores}} "
                "   - Apply adjustment: {{size_adjustments}} "
                "Calculate final constrained position size"
            ),
            depends_on=[3, 4],
            parallel_execution=False,
            timeout_seconds=30,
            outputs=[
                "constrained_sizes",
                "applied_limits",
                "final_position_size",
                "limit_rationale",
            ],
        ),
        AgentStep(
            agent_name="@product-manager",
            prompt_template=(
                "Generate comprehensive position sizing report: "
                "1. Position Summary: "
                "   - Asset: {{asset_symbol}} "
                "   - Entry: {{entry_price}} "
                "   - Stop: {{stop_loss}} "
                "   - Risk per unit: {{risk_per_unit}} "
                "2. Account Context: "
                "   - Total account: {{account_size}} "
                "   - Available capital: {{available_capital}} "
                "   - Current exposure: {{current_exposure}} "
                "   - Risk per trade limit: {{risk_per_trade}}% "
                "3. Position Size Methods: "
                "   a) Fixed Risk (${{risk_per_trade}}% account): "
                "      - Size: {{fixed_dollar_risk_size}} units "
                "      - Dollar value: $X "
                "      - Risk if stopped: $Y "
                "   b) Volatility-Adjusted: "
                "      - Size: {{volatility_adjusted_size}} units "
                "      - Adjustment reason: {{volatility_regime}} "
                "   c) Kelly Criterion (Half Kelly): "
                "      - Size: {{kelly_position_sizes}} units "
                "      - Win rate: {{win_rate_estimate}} "
                "      - Win/loss ratio: {{win_loss_ratio}} "
                "4. Recommended Position: "
                "   - Final size: {{final_position_size}} units "
                "   - Method used: [which method] "
                "   - Rationale: {{limit_rationale}} "
                "   - Dollar value: $X "
                "   - % of account: Y% "
                "5. Risk Metrics: "
                "   - Risk if stopped: $X ({{risk_per_trade}}%) "
                "   - Leverage required: {{leverage_required}}x "
                "   - Liquidation price: {{liquidation_price}} "
                "   - Distance to liquidation: Z% "
                "6. Constraints Applied: "
                "   - {{applied_limits}} "
                "   - Correlation adjustment: {{size_adjustments}} "
                "   - Warnings: {{leverage_warnings}} "
                "7. Execution: "
                "   - Order size: {{final_position_size}} units "
                "   - Order type: Limit at {{entry_price}} "
                "   - Stop loss: {{stop_loss}} "
                "   - Expected slippage allowance: 0.5%"
            ),
            depends_on=[5],
            parallel_execution=False,
            timeout_seconds=60,
            outputs=[
                "position_sizing_report",
                "recommended_size",
                "risk_metrics",
                "execution_plan",
            ],
        ),
    ]

    required_inputs = {
        "asset_symbol": InputSpec(
            type="string",
            required=True,
            description="Asset symbol to trade (e.g., BTC, ETH, LINK)",
        ),
        "entry_price": InputSpec(
            type="number",
            required=True,
            description="Planned entry price",
        ),
        "stop_loss": InputSpec(
            type="number",
            required=True,
            description="Stop loss price",
        ),
        "account_size": InputSpec(
            type="number",
            required=True,
            description="Total account size in USD",
        ),
        "risk_per_trade": InputSpec(
            type="number",
            required=False,
            description="Maximum risk per trade as % of account",
            default=1,
        ),
        "max_portfolio_risk": InputSpec(
            type="number",
            required=False,
            description="Maximum total portfolio risk %",
            default=5,
        ),
        "max_single_position": InputSpec(
            type="number",
            required=False,
            description="Maximum % of account in single position",
            default=10,
        ),
        "max_leverage": InputSpec(
            type="number",
            required=False,
            description="Maximum allowed leverage multiplier",
            default=3,
        ),
        "win_rate": InputSpec(
            type="number",
            required=False,
            description="Historical win rate % (for Kelly calculation)",
            default=50,
        ),
        "position_percentage": InputSpec(
            type="number",
            required=False,
            description="Fixed percentage of account for position (alternative method)",
            default=5,
        ),
        "min_position_size": InputSpec(
            type="number",
            required=False,
            description="Minimum position size in USD (avoid dust)",
            default=100,
        ),
        "max_volume_percentage": InputSpec(
            type="number",
            required=False,
            description="Maximum % of daily volume for position size",
            default=1,
        ),
    }

    return ConversationTemplate.create(
        name="Position Sizing",
        description=(
            "Comprehensive position sizing calculator using multiple methodologies. "
            "Calculates optimal position sizes using fixed risk, Kelly Criterion, and "
            "volatility-adjusted approaches. Considers portfolio correlation, leverage "
            "requirements, and practical constraints. Provides risk metrics and execution plan."
        ),
        category="trading_strategy",
        agent_sequence=agent_sequence,
        required_inputs=required_inputs,
        estimated_duration_seconds=240,  # 4 minutes
        created_by=created_by,
        is_public=True,
        tags=["trading", "position-sizing", "risk-management", "kelly-criterion"],
    )
