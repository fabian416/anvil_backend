"""APR/APY Calculator Template

Calculates true yields for DeFi positions including base rates, reward tokens,
compounding effects, and real costs to determine actual returns.
"""

from uuid import UUID

from app.domain.entities.chat.conversation_template import (
    AgentStep,
    ConversationTemplate,
    InputSpec,
)


def create_apr_apy_calculator_template(created_by: UUID) -> ConversationTemplate:
    """Create APR/APY calculator template.

    Comprehensive yield calculation including:
    - Base APR from protocol fees
    - Reward token emissions and valuations
    - Compounding frequency and APY conversion
    - Real costs (gas, swap fees, IL)
    - Net yield after all expenses
    - Scenario analysis with different assumptions

    Args:
        created_by: User ID creating the template

    Returns:
        Configured ConversationTemplate instance
    """

    agent_sequence = [
        AgentStep(
            agent_name="@defi-specialist",
            prompt_template=(
                "Gather yield data for {{position_type}} on {{protocol_name}}: "
                "1. Base Yield: "
                "   - Protocol fees generated "
                "   - Fee distribution to LPs/stakers "
                "   - Current base APR "
                "2. Reward Tokens: "
                "   - List all reward tokens "
                "   - Emission rates (tokens/day) "
                "   - Current token prices "
                "   - Vesting or lock periods "
                "3. Position Details: "
                "   - Minimum deposit "
                "   - Lock period requirements "
                "   - Withdrawal fees "
                "   - Compounding mechanism (auto or manual)"
            ),
            depends_on=[],
            parallel_execution=False,
            timeout_seconds=45,
            outputs=[
                "base_apr",
                "reward_tokens",
                "emission_rates",
                "token_prices",
                "position_requirements",
            ],
        ),
        AgentStep(
            agent_name="@quantitative-analyst",
            prompt_template=(
                "Calculate gross yields: "
                "For position size {{position_size}} USD: "
                "1. Base Yield (Annual): "
                "   - Fee revenue = position_size × {{base_apr}} "
                "2. Reward Token Value (Annual): "
                "   - For each token in {{reward_tokens}}: "
                "     * Tokens earned = (emission_rate × share_of_pool × 365) "
                "     * USD value = tokens_earned × token_price "
                "   - Total reward value (sum all tokens) "
                "3. Gross APR: "
                "   - (Fee revenue + Total rewards) / position_size × 100% "
                "4. APY with Compounding: "
                "   - If auto-compound: APY = (1 + APR/n)^n - 1 "
                "   - n = compounding frequency (daily, weekly, monthly) "
                "   - If manual: APY = APR (no compounding benefit)"
            ),
            depends_on=[0],
            parallel_execution=False,
            timeout_seconds=45,
            outputs=[
                "base_fee_revenue",
                "reward_token_value",
                "gross_apr",
                "gross_apy",
                "compounding_benefit",
            ],
        ),
        AgentStep(
            agent_name="@defi-specialist",
            prompt_template=(
                "Calculate operating costs: "
                "For {{position_type}} on {{protocol_name}}: "
                "1. Transaction Costs: "
                "   - Entry: Deposit + approve transactions "
                "   - Ongoing: Harvest/compound frequency "
                "   - Exit: Withdraw + swap rewards "
                "   - Current gas price on {{chain}} "
                "   - Gas cost per transaction type "
                "2. Protocol Fees: "
                "   - Deposit fees (if any) "
                "   - Performance fees on rewards "
                "   - Withdrawal fees "
                "3. Swap Costs (for reward tokens): "
                "   - DEX fees for selling rewards "
                "   - Slippage for reward token sales "
                "Total annual cost = sum all costs"
            ),
            depends_on=[0],
            parallel_execution=True,
            timeout_seconds=30,
            outputs=[
                "gas_costs_annual",
                "protocol_fees",
                "swap_costs",
                "total_annual_costs",
            ],
        ),
        AgentStep(
            agent_name="@risk-analyst",
            prompt_template=(
                "Calculate impermanent loss (for LP positions): "
                "{% if position_type == 'liquidity_pool' %} "
                "For {{trading_pair}} pool: "
                "1. Historical IL Analysis: "
                "   - Price correlation between assets "
                "   - 30-day volatility "
                "   - Historical IL range (min, avg, max) "
                "2. Scenario Analysis: "
                "   - IL if price diverges 10%, 25%, 50% "
                "   - Breakeven APR to offset IL "
                "3. IL Estimate: "
                "   - Expected annual IL based on volatility "
                "   - Confidence interval "
                "{% else %} "
                "No impermanent loss for {{position_type}} "
                "{% endif %}"
            ),
            depends_on=[0],
            parallel_execution=True,
            timeout_seconds=45,
            outputs=[
                "il_scenarios",
                "expected_il_annual",
                "il_breakeven_apr",
            ],
        ),
        AgentStep(
            agent_name="@quantitative-analyst",
            prompt_template=(
                "Calculate net yields: "
                "Using all gathered data: "
                "Gross APY: {{gross_apy}} "
                "Less: "
                "- Annual costs: {{total_annual_costs}} / {{position_size}} = X% "
                "- Expected IL: {{expected_il_annual}} "
                "Net APR = Gross APY - Costs% - IL% "
                "Also calculate: "
                "1. Breakeven Analysis: "
                "   - Minimum time to recoup entry/exit costs "
                "   - Minimum position size for profitability "
                "2. Real Yield vs Nominal: "
                "   - If rewards in stable coins → real yield "
                "   - If rewards in volatile tokens → risk-adjusted yield "
                "3. Yield Sustainability: "
                "   - Are rewards from real revenue or token emissions? "
                "   - Emission schedule and future APR projections"
            ),
            depends_on=[1, 2, 3],
            parallel_execution=False,
            timeout_seconds=45,
            outputs=[
                "net_apr",
                "net_apy",
                "breakeven_days",
                "min_position_size",
                "yield_sustainability",
            ],
        ),
        AgentStep(
            agent_name="@market-analyst",
            prompt_template=(
                "Perform scenario analysis: "
                "Model yield under different conditions: "
                "1. Best Case (+20% reward token prices): "
                "   - Recalculate reward value "
                "   - New gross and net APY "
                "2. Expected Case (current prices): "
                "   - Use calculated {{net_apy}} "
                "3. Worst Case (-50% reward token prices): "
                "   - Reward value drops "
                "   - Potential negative net yield "
                "4. Market Condition Changes: "
                "   - TVL doubles (diluted rewards) "
                "   - TVL halves (concentrated rewards) "
                "   - Fee revenue changes ±30% "
                "Create distribution of possible outcomes"
            ),
            depends_on=[4],
            parallel_execution=False,
            timeout_seconds=45,
            outputs=[
                "best_case_apy",
                "expected_case_apy",
                "worst_case_apy",
                "scenario_distribution",
                "probability_weighted_return",
            ],
        ),
        AgentStep(
            agent_name="@portfolio-analyst",
            prompt_template=(
                "Generate optimization recommendations: "
                "Based on {{net_apy}} and scenarios: "
                "1. Position Optimization: "
                "   - Optimal position size: {{min_position_size}} to $X "
                "   - Recommended compounding frequency "
                "   - Auto-compound vs manual harvest "
                "2. Risk/Reward Assessment: "
                "   - Expected return: {{expected_case_apy}} "
                "   - Downside risk: {{worst_case_apy}} "
                "   - Upside potential: {{best_case_apy}} "
                "   - Sharpe ratio estimate "
                "3. Comparison: "
                "   - vs similar protocols "
                "   - vs risk-free rate "
                "   - Risk-adjusted attractiveness "
                "4. Monitoring Plan: "
                "   - APR tracking frequency "
                "   - Exit triggers (APR drops below X%) "
                "   - Rebalancing schedule"
            ),
            depends_on=[5],
            parallel_execution=False,
            timeout_seconds=45,
            outputs=[
                "optimal_position_size",
                "compound_frequency",
                "risk_reward_ratio",
                "comparative_analysis",
                "monitoring_triggers",
            ],
        ),
        AgentStep(
            agent_name="@product-manager",
            prompt_template=(
                "Create comprehensive yield report: "
                "1. Yield Summary: "
                "   - Advertised APY: (from protocol) "
                "   - Gross APY: {{gross_apy}} "
                "   - Net APY: {{net_apy}} "
                "   - Expected Return (probability-weighted): {{probability_weighted_return}} "
                "2. Yield Breakdown: "
                "   - Base fees: {{base_apr}} "
                "   - Reward tokens: {{reward_token_value}} "
                "   - Compounding benefit: {{compounding_benefit}} "
                "3. Cost Analysis: "
                "   - Gas costs: {{gas_costs_annual}} "
                "   - Protocol fees: {{protocol_fees}} "
                "   - Impermanent loss: {{expected_il_annual}} "
                "   - Total costs: {{total_annual_costs}} "
                "4. Scenario Analysis: "
                "   - Best case: {{best_case_apy}} "
                "   - Expected: {{expected_case_apy}} "
                "   - Worst case: {{worst_case_apy}} "
                "5. Recommendations: "
                "   - Position size: {{optimal_position_size}} "
                "   - Holding period: {{breakeven_days}}+ days "
                "   - Strategy: {{compound_frequency}} "
                "   - Monitoring: {{monitoring_triggers}} "
                "6. Sustainability Assessment: "
                "   - Yield source quality: {{yield_sustainability}} "
                "   - Long-term viability rating "
                "   - Rug risk indicators"
            ),
            depends_on=[6],
            parallel_execution=False,
            timeout_seconds=60,
            outputs=[
                "yield_report",
                "advertised_vs_real_apy",
                "recommendations",
                "sustainability_rating",
            ],
        ),
    ]

    required_inputs = {
        "protocol_name": InputSpec(
            type="string",
            required=True,
            description="DeFi protocol name (e.g., Aave, Curve, Yearn)",
        ),
        "position_type": InputSpec(
            type="string",
            required=True,
            description="Position type: 'liquidity_pool', 'lending', 'staking', 'farming'",
        ),
        "position_size": InputSpec(
            type="number",
            required=False,
            description="Position size in USD",
            default=10000,
        ),
        "chain": InputSpec(
            type="string",
            required=False,
            description="Blockchain network for gas cost calculation",
            default="ethereum",
        ),
        "trading_pair": InputSpec(
            type="string",
            required=False,
            description="Trading pair (for LP positions only, e.g., ETH/USDC)",
            default="",
        ),
    }

    return ConversationTemplate.create(
        name="APR/APY Calculator",
        description=(
            "Comprehensive yield calculator for DeFi positions. Calculates true returns "
            "including base rates, reward token emissions, compounding effects, and all costs "
            "(gas, fees, IL). Provides scenario analysis and risk-adjusted yield estimates. "
            "Reveals real yields vs advertised APYs."
        ),
        category="defi_analysis",
        agent_sequence=agent_sequence,
        required_inputs=required_inputs,
        estimated_duration_seconds=300,  # 5 minutes
        created_by=created_by,
        is_public=True,
        tags=["defi", "yield", "apr", "apy", "calculator", "returns"],
    )
