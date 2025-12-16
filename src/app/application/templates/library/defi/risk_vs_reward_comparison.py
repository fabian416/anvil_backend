"""Risk vs Reward Comparison Template

Compares multiple DeFi opportunities across risk and reward dimensions to find
optimal yield strategies based on user risk tolerance.
"""

from uuid import UUID

from app.domain.entities.chat.conversation_template import (
    AgentStep,
    ConversationTemplate,
    InputSpec,
)


def create_risk_vs_reward_comparison_template(created_by: UUID) -> ConversationTemplate:
    """Create risk vs reward comparison template.

    Analyzes and compares multiple DeFi opportunities across:
    - Expected returns (APY, rewards, incentives)
    - Risk factors (smart contract, liquidity, market)
    - Capital efficiency and lock-up periods
    - Risk-adjusted returns (Sharpe ratio, Sortino ratio)
    - Recommendations based on risk tolerance

    Args:
        created_by: User ID creating the template

    Returns:
        Configured ConversationTemplate instance
    """

    agent_sequence = [
        AgentStep(
            agent_name="@defi-specialist",
            prompt_template=(
                "Scan and identify top DeFi opportunities for {{asset_type}} assets: "
                "{% if protocols %}"
                "Focus on these protocols: {{protocols}} "
                "{% else %}"
                "Scan top 20 protocols by TVL "
                "{% endif %}"
                "For each opportunity, gather: "
                "- Current APY/APR "
                "- Reward tokens and emissions "
                "- Lock-up requirements "
                "- Minimum deposit "
                "- Total TVL and user count"
            ),
            depends_on=[],
            parallel_execution=False,
            timeout_seconds=45,
            outputs=[
                "opportunities",
                "base_yields",
                "reward_tokens",
                "lock_periods",
            ],
        ),
        AgentStep(
            agent_name="@security-specialist",
            prompt_template=(
                "For each opportunity identified, assess security risks: "
                "Using opportunities: {{opportunities}} "
                "Evaluate: "
                "- Smart contract audit status (firm, date, findings) "
                "- Protocol age and battle-testing "
                "- Historical exploits or incidents "
                "- Admin key risks and governance "
                "- Bug bounty programs "
                "Assign risk score (1-10, 10 = highest risk)"
            ),
            depends_on=[0],
            parallel_execution=False,
            timeout_seconds=60,
            outputs=[
                "security_scores",
                "audit_status",
                "exploit_history",
                "risk_ratings",
            ],
        ),
        AgentStep(
            agent_name="@risk-analyst",
            prompt_template=(
                "Evaluate additional risk factors for each opportunity: "
                "- Liquidity risk: Depth of pools, slippage estimates "
                "- Market risk: Token volatility, correlation "
                "- Impermanent loss risk (for LP positions) "
                "- Counterparty risk (centralized components) "
                "- Regulatory risk exposure "
                "Calculate composite risk score combining all factors"
            ),
            depends_on=[1],
            parallel_execution=False,
            timeout_seconds=45,
            outputs=[
                "liquidity_risk",
                "market_risk",
                "il_risk",
                "composite_risk_score",
            ],
        ),
        AgentStep(
            agent_name="@quantitative-analyst",
            prompt_template=(
                "Calculate risk-adjusted returns for each opportunity: "
                "Using: "
                "- Base yields: {{base_yields}} "
                "- Composite risk scores: {{composite_risk_score}} "
                "- Historical volatility data "
                "Calculate: "
                "1. Expected total return (base + rewards) "
                "2. Sharpe ratio (return / volatility) "
                "3. Sortino ratio (downside deviation) "
                "4. Risk-adjusted yield = APY / (risk_score / 10) "
                "5. Capital efficiency (return per unit of capital locked)"
            ),
            depends_on=[2],
            parallel_execution=False,
            timeout_seconds=45,
            outputs=[
                "expected_returns",
                "sharpe_ratios",
                "sortino_ratios",
                "risk_adjusted_yields",
                "capital_efficiency",
            ],
        ),
        AgentStep(
            agent_name="@defi-specialist",
            prompt_template=(
                "Analyze practical considerations for each opportunity: "
                "- Gas costs for entry/exit and harvesting "
                "- Claiming and compounding frequency "
                "- Breakeven timeline (when yield > gas costs) "
                "- Minimum profitable position size "
                "- Ease of entry/exit "
                "- Protocol UI/UX quality"
            ),
            depends_on=[3],
            parallel_execution=True,
            timeout_seconds=30,
            outputs=[
                "gas_costs",
                "breakeven_days",
                "min_position_size",
                "ease_of_use",
            ],
        ),
        AgentStep(
            agent_name="@portfolio-analyst",
            prompt_template=(
                "Create risk-tiered recommendations based on {{risk_tolerance}}: "
                "Conservative (risk score < 3): "
                "- Prioritize battle-tested protocols, audited contracts "
                "- Accept lower yields for safety "
                "Moderate (risk score 3-6): "
                "- Balance risk and reward "
                "- Diversify across protocols "
                "Aggressive (risk score > 6): "
                "- Maximize yield potential "
                "- Accept higher risk for returns "
                "For each tier, recommend top 3 opportunities with rationale"
            ),
            depends_on=[4],
            parallel_execution=False,
            timeout_seconds=45,
            outputs=[
                "conservative_picks",
                "moderate_picks",
                "aggressive_picks",
                "tier_rationale",
            ],
        ),
        AgentStep(
            agent_name="@product-manager",
            prompt_template=(
                "Generate comprehensive comparison report: "
                "1. Opportunity Matrix: "
                "   - Sort by risk-adjusted yield "
                "   - Show APY, risk score, Sharpe ratio, lock period "
                "2. Risk vs Reward Chart: "
                "   - X-axis: Risk score (1-10) "
                "   - Y-axis: Expected APY "
                "   - Bubble size: TVL "
                "3. Tiered Recommendations: "
                "   - Conservative: {{conservative_picks}} "
                "   - Moderate: {{moderate_picks}} "
                "   - Aggressive: {{aggressive_picks}} "
                "4. Action Plan: "
                "   - Position allocation by risk tier "
                "   - Entry timing and strategy "
                "   - Monitoring and rebalancing schedule"
            ),
            depends_on=[5],
            parallel_execution=False,
            timeout_seconds=60,
            outputs=[
                "opportunity_matrix",
                "risk_reward_chart",
                "final_recommendations",
                "action_plan",
            ],
        ),
    ]

    required_inputs = {
        "asset_type": InputSpec(
            type="string",
            required=False,
            description="Asset type to analyze: 'stables', 'eth', 'btc', 'alts'",
            default="stables",
        ),
        "risk_tolerance": InputSpec(
            type="string",
            required=False,
            description="Risk tolerance: 'conservative', 'moderate', 'aggressive'",
            default="moderate",
        ),
        "protocols": InputSpec(
            type="string",
            required=False,
            description="Comma-separated list of protocols to focus on (optional)",
            default="",
        ),
        "min_tvl": InputSpec(
            type="number",
            required=False,
            description="Minimum protocol TVL in millions USD",
            default=10,
        ),
    }

    return ConversationTemplate.create(
        name="Risk vs Reward Comparison",
        description=(
            "Compare multiple DeFi opportunities across risk and reward dimensions. "
            "Analyzes yields, risk factors, and provides tiered recommendations based "
            "on risk tolerance. Includes risk-adjusted metrics (Sharpe, Sortino) and "
            "practical considerations (gas costs, capital efficiency)."
        ),
        category="defi_analysis",
        agent_sequence=agent_sequence,
        required_inputs=required_inputs,
        estimated_duration_seconds=300,  # 5 minutes
        created_by=created_by,
        is_public=True,
        tags=["defi", "yield", "risk-analysis", "comparison"],
    )
