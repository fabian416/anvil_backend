"""
Rebalancing Recommendations Template

8-step workflow for portfolio rebalancing.
Estimated duration: 6 minutes
"""

from uuid import UUID

from app.domain.entities.chat.conversation_template import (
    ConversationTemplate,
    AgentStep,
    InputSpec,
)


def create_rebalancing_recommendations_template(created_by: UUID) -> ConversationTemplate:
    """
    Create rebalancing recommendations template.

    This template provides strategic rebalancing guidance:
    - Current vs target allocation analysis
    - Drift calculation
    - Tax implications
    - Transaction cost optimization
    - Rebalancing threshold analysis
    - Step-by-step execution plan
    - Performance projection
    - Scheduling recommendations

    Args:
        created_by: User ID creating the template

    Returns:
        ConversationTemplate instance
    """

    agent_sequence = [
        AgentStep(
            agent_name="@portfolio-analyst",
            prompt_template=(
                "Analyze current portfolio allocation for {{wallet_address}}: "
                "- Current asset weights (% of portfolio) "
                "- Asset categorization (by sector, protocol, chain, risk level) "
                "- Total portfolio value "
                "Generate current allocation breakdown."
            ),
            depends_on=[],
            parallel_execution=False,
            timeout_seconds=30,
            outputs=["current_allocation", "asset_categories", "total_value"],
        ),
        AgentStep(
            agent_name="@portfolio-analyst",
            prompt_template=(
                "Load or create target allocation strategy: "
                "{% if target_allocation %} "
                "Use provided target: {{target_allocation}} "
                "{% else %} "
                "Create recommended allocation based on {{strategy_type}} strategy: "
                "- conservative: 60% stables, 30% blue-chip, 10% alts "
                "- balanced: 30% stables, 50% blue-chip, 20% alts "
                "- growth: 10% stables, 50% blue-chip, 40% alts "
                "- aggressive: 5% stables, 35% blue-chip, 60% alts "
                "{% endif %}"
            ),
            depends_on=[],
            parallel_execution=False,
            timeout_seconds=15,
            outputs=["target_allocation", "allocation_strategy"],
        ),
        AgentStep(
            agent_name="@quantitative-analyst",
            prompt_template=(
                "Calculate allocation drift: "
                "For each asset category: "
                "- Current weight vs target weight "
                "- Absolute drift (percentage points) "
                "- Relative drift (% of target) "
                "- USD value to rebalance "
                "Total portfolio drift score (sum of absolute drifts). "
                "Flag categories with drift > {{rebalance_threshold}}%"
            ),
            depends_on=[0, 1],
            parallel_execution=False,
            timeout_seconds=30,
            outputs=["drift_analysis", "drift_score", "rebalance_needed"],
        ),
        AgentStep(
            agent_name="@tax-specialist",
            prompt_template=(
                "Analyze tax implications of rebalancing: "
                "- Identify positions with unrealized gains/losses "
                "- Calculate potential capital gains tax "
                "- Recommend tax-loss harvesting opportunities "
                "- Consider holding periods for long-term vs short-term gains "
                "- Suggest tax-efficient rebalancing sequence "
                "User's tax jurisdiction: {{tax_jurisdiction}}, rate: {{capital_gains_rate}}%"
            ),
            depends_on=[2],
            parallel_execution=True,
            timeout_seconds=45,
            outputs=["tax_implications", "tax_optimization_suggestions", "estimated_tax"],
        ),
        AgentStep(
            agent_name="@quantitative-analyst",
            prompt_template=(
                "Optimize transaction costs: "
                "- Estimate gas costs for each rebalancing trade "
                "- Calculate DEX vs CEX cost comparison "
                "- Identify slippage for each trade "
                "- Total rebalancing cost estimate "
                "- Cost as % of portfolio "
                "Recommend minimum rebalance amounts to justify costs."
            ),
            depends_on=[2],
            parallel_execution=True,
            timeout_seconds=45,
            outputs=["transaction_costs", "cost_optimization", "min_trade_amounts"],
        ),
        AgentStep(
            agent_name="@risk-analyst",
            prompt_template=(
                "Evaluate rebalancing impact on risk: "
                "- Current portfolio risk score "
                "- Projected risk score after rebalancing "
                "- Impact on diversification "
                "- Impact on volatility "
                "- Impact on concentration risk "
                "Ensure rebalancing aligns with {{risk_tolerance}} risk profile."
            ),
            depends_on=[1, 2],
            parallel_execution=False,
            timeout_seconds=30,
            outputs=["risk_impact", "current_risk_score", "projected_risk_score"],
        ),
        AgentStep(
            agent_name="@product-manager",
            prompt_template=(
                "Create rebalancing execution plan: "
                "Priority 1 (Critical): Drift > 15% "
                "Priority 2 (High): Drift 10-15% "
                "Priority 3 (Medium): Drift 5-10% "
                "For each trade: "
                "- Asset to sell/buy "
                "- Amount in USD "
                "- Expected gas cost "
                "- Tax implications "
                "- Optimal execution venue "
                "Sequence trades to minimize costs and taxes. "
                "Total rebalancing cost: {{transaction_costs}} + {{estimated_tax}}"
            ),
            depends_on=[2, 3, 4],
            parallel_execution=False,
            timeout_seconds=45,
            outputs=["execution_plan", "trade_sequence", "total_cost"],
        ),
        AgentStep(
            agent_name="@project-manager",
            prompt_template=(
                "Provide rebalancing summary and recommendations: "
                "1. Rebalancing Necessity: Drift score {{drift_score}}, recommend? "
                "2. Expected Outcome: "
                "   - Alignment with target: X% improvement "
                "   - Risk impact: {{risk_impact}} "
                "   - Total cost: {{total_cost}} ({{cost_percentage}}% of portfolio) "
                "3. Execution Plan: {{trade_sequence}} "
                "4. Next Rebalancing: Recommend schedule (monthly/quarterly/threshold-based) "
                "5. Monitoring: Key metrics to track post-rebalancing "
                "Decision: Execute now / Wait (explain why)"
            ),
            depends_on=[5, 6],
            parallel_execution=False,
            timeout_seconds=30,
            outputs=["rebalancing_recommendation", "next_rebalance_date", "monitoring_plan"],
        ),
    ]

    required_inputs = {
        "wallet_address": InputSpec(
            type="wallet_address",
            required=True,
            description="Wallet address to analyze",
            validation_pattern=r"^0x[a-fA-F0-9]{40}$",
        ),
        "strategy_type": InputSpec(
            type="string",
            required=False,
            description="Rebalancing strategy: 'conservative', 'balanced', 'growth', 'aggressive'",
            default="balanced",
        ),
        "target_allocation": InputSpec(
            type="string",
            required=False,
            description=(
                "Custom target allocation as JSON (e.g., '{\"stables\": 30, \"btc\": 25, \"eth\": 25, \"alts\": 20}'). "
                "If not provided, uses strategy_type."
            ),
            default=None,
        ),
        "rebalance_threshold": InputSpec(
            type="number",
            required=False,
            description="Minimum drift percentage to trigger rebalancing",
            default=5,
        ),
        "risk_tolerance": InputSpec(
            type="string",
            required=False,
            description="Risk tolerance: 'conservative', 'moderate', 'aggressive'",
            default="moderate",
        ),
        "tax_jurisdiction": InputSpec(
            type="string",
            required=False,
            description="Tax jurisdiction (e.g., 'US', 'UK', 'EU')",
            default="US",
        ),
        "capital_gains_rate": InputSpec(
            type="number",
            required=False,
            description="Capital gains tax rate percentage",
            default=20,
        ),
    }

    return ConversationTemplate.create(
        name="Rebalancing Recommendations",
        description=(
            "Comprehensive portfolio rebalancing analysis including drift calculation, "
            "tax optimization, cost analysis, risk assessment, and step-by-step execution plan."
        ),
        category="portfolio_management",
        agent_sequence=agent_sequence,
        required_inputs=required_inputs,
        estimated_duration_seconds=360,  # 6 minutes
        created_by=created_by,
        is_public=True,
    )
