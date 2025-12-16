"""
Yield Optimization Analysis Template

6-step workflow to maximize portfolio yield.
Estimated duration: 4 minutes
"""

from uuid import UUID

from app.domain.entities.chat.conversation_template import (
    ConversationTemplate,
    AgentStep,
    InputSpec,
)


def create_yield_optimization_analysis_template(created_by: UUID) -> ConversationTemplate:
    """
    Create yield optimization analysis template.

    This template identifies opportunities to maximize yield:
    - Current yield analysis
    - Available yield opportunities
    - Risk-adjusted yield comparison
    - Gas cost impact analysis
    - Optimal reallocation strategy
    - Implementation roadmap

    Args:
        created_by: User ID creating the template

    Returns:
        ConversationTemplate instance
    """

    agent_sequence = [
        AgentStep(
            agent_name="@portfolio-analyst",
            prompt_template=(
                "Analyze current yield generation for wallet {{wallet_address}}: "
                "- Identify all yield-bearing positions "
                "- Calculate current APY/APR for each "
                "- Total annual yield in USD "
                "- Idle assets not earning yield "
                "- Weighted average portfolio yield"
            ),
            depends_on=[],
            parallel_execution=False,
            timeout_seconds=30,
            outputs=["current_yield_positions", "total_annual_yield", "idle_assets", "avg_portfolio_yield"],
        ),
        AgentStep(
            agent_name="@defi-specialist",
            prompt_template=(
                "Scan for yield opportunities matching {{risk_tolerance}} risk profile: "
                "- Lending platforms (Aave, Compound, etc.) "
                "- Liquidity pools with IL < {{max_impermanent_loss}}% "
                "- Staking opportunities "
                "- Yield aggregators (Yearn, Beefy, etc.) "
                "For each asset in the portfolio, find top 3 yield options. "
                "Chains to consider: {{chains}}"
            ),
            depends_on=[0],
            parallel_execution=False,
            timeout_seconds=60,
            outputs=["yield_opportunities", "platform_apys", "opportunity_count"],
        ),
        AgentStep(
            agent_name="@risk-analyst",
            prompt_template=(
                "Calculate risk-adjusted yield (Sharpe-like ratio) for opportunities: "
                "Formula: (APY - risk_free_rate) / risk_score "
                "Risk factors: smart contract risk, liquidity risk, IL risk, protocol age "
                "Rank opportunities by risk-adjusted yield. "
                "Filter out options with risk score > {{max_risk_score}}/10"
            ),
            depends_on=[1],
            parallel_execution=False,
            timeout_seconds=45,
            outputs=["risk_adjusted_rankings", "filtered_opportunities"],
        ),
        AgentStep(
            agent_name="@quantitative-analyst",
            prompt_template=(
                "Estimate gas costs and breakeven analysis: "
                "For each reallocation: "
                "- Estimated gas cost (current rates) "
                "- Breakeven period (how long to recoup gas costs) "
                "- Net APY after gas costs "
                "Remove opportunities with breakeven > {{max_breakeven_days}} days. "
                "Use portfolio size: {{total_value}}"
            ),
            depends_on=[2],
            parallel_execution=True,
            timeout_seconds=30,
            outputs=["gas_costs", "breakeven_periods", "net_apy"],
        ),
        AgentStep(
            agent_name="@product-manager",
            prompt_template=(
                "Design optimal reallocation strategy: "
                "- Target allocation across top opportunities "
                "- Expected yield increase (absolute and %) "
                "- Risk impact on overall portfolio "
                "- Maintain diversification (no single position > {{max_position_size}}%) "
                "Create allocation table with current vs. proposed yields."
            ),
            depends_on=[3],
            parallel_execution=False,
            timeout_seconds=30,
            outputs=["optimal_allocation", "expected_yield_increase", "allocation_table"],
        ),
        AgentStep(
            agent_name="@project-manager",
            prompt_template=(
                "Create implementation roadmap: "
                "1. Quick wins: Reallocations with <7 day breakeven "
                "2. Medium-term: Reallocations with 7-30 day breakeven "
                "3. Long-term: Reallocations with >30 day breakeven "
                "For each, provide: "
                "- Step-by-step transaction sequence "
                "- Estimated gas costs "
                "- Expected annual yield gain "
                "- Risk considerations "
                "Total expected yield improvement: {{expected_yield_increase}}"
            ),
            depends_on=[4],
            parallel_execution=False,
            timeout_seconds=30,
            outputs=["implementation_roadmap", "transaction_sequence", "summary"],
        ),
    ]

    required_inputs = {
        "wallet_address": InputSpec(
            type="wallet_address",
            required=True,
            description="Wallet address to analyze",
            validation_pattern=r"^0x[a-fA-F0-9]{40}$",
        ),
        "risk_tolerance": InputSpec(
            type="string",
            required=False,
            description="Risk tolerance level: 'conservative', 'moderate', 'aggressive'",
            default="moderate",
        ),
        "max_impermanent_loss": InputSpec(
            type="number",
            required=False,
            description="Maximum acceptable impermanent loss percentage",
            default=10,
        ),
        "max_risk_score": InputSpec(
            type="number",
            required=False,
            description="Maximum acceptable risk score (1-10 scale)",
            default=7,
        ),
        "max_breakeven_days": InputSpec(
            type="number",
            required=False,
            description="Maximum acceptable breakeven period in days",
            default=90,
        ),
        "max_position_size": InputSpec(
            type="number",
            required=False,
            description="Maximum position size as percentage of portfolio",
            default=25,
        ),
        "chains": InputSpec(
            type="string",
            required=False,
            description="Comma-separated list of chains to consider (e.g., 'ethereum,arbitrum,optimism')",
            default="ethereum,arbitrum,optimism,polygon",
        ),
    }

    return ConversationTemplate.create(
        name="Yield Optimization Analysis",
        description=(
            "Comprehensive yield optimization analysis to maximize portfolio returns while "
            "managing risk, including opportunity scanning, risk-adjusted comparison, gas cost "
            "analysis, and actionable implementation roadmap."
        ),
        category="portfolio_management",
        agent_sequence=agent_sequence,
        required_inputs=required_inputs,
        estimated_duration_seconds=240,  # 4 minutes
        created_by=created_by,
        is_public=True,
    )
