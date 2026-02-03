"""
Tax Loss Harvesting Template

6-step workflow for tax optimization.
Estimated duration: 4 minutes
"""

from uuid import UUID

from app.domain.entities.chat.conversation_template import (
    ConversationTemplate,
    AgentStep,
    InputSpec,
)


def create_tax_loss_harvesting_template(created_by: UUID) -> ConversationTemplate:
    """
    Create tax loss harvesting template.

    This template identifies tax optimization opportunities:
    - Unrealized loss identification
    - Wash sale rule compliance
    - Similar asset recommendations
    - Tax savings calculation
    - Optimal execution timing
    - Year-end tax planning

    Args:
        created_by: User ID creating the template

    Returns:
        ConversationTemplate instance
    """

    agent_sequence = [
        AgentStep(
            agent_name="@portfolio-analyst",
            prompt_template=(
                "Analyze all positions in wallet {{wallet_address}}: "
                "For each position, calculate: "
                "- Purchase price (cost basis) "
                "- Current price "
                "- Unrealized gain/loss ($ and %) "
                "- Holding period "
                "- Position size in USD "
                "Identify all positions with unrealized losses > {{min_loss_threshold}}%"
            ),
            depends_on=[],
            parallel_execution=False,
            timeout_seconds=45,
            outputs=["all_positions", "loss_positions", "total_unrealized_loss"],
        ),
        AgentStep(
            agent_name="@tax-specialist",
            prompt_template=(
                "Evaluate tax loss harvesting opportunities: "
                "For each loss position: "
                "- Potential tax savings at {{tax_rate}}% rate "
                "- Wash sale rule compliance (30-day rule for {{tax_jurisdiction}}) "
                "- Last transaction date "
                "- Safe to harvest date "
                "Filter positions safe to harvest before {{tax_year_end}}. "
                "Calculate total potential tax savings."
            ),
            depends_on=[0],
            parallel_execution=False,
            timeout_seconds=30,
            outputs=["harvestable_losses", "tax_savings", "wash_sale_warnings"],
        ),
        AgentStep(
            agent_name="@defi-specialist",
            prompt_template=(
                "Find similar assets for tax-loss harvesting: "
                "For each harvestable loss position, recommend 2-3 similar assets: "
                "- Maintain sector/theme exposure "
                "- Similar risk profile "
                "- Similar market cap tier "
                "- Sufficient liquidity "
                "Example: If selling ETH, suggest stETH, rETH, or ETH LSTs. "
                "If selling UNI, suggest SUSHI, CAKE, or other DEX tokens."
            ),
            depends_on=[1],
            parallel_execution=True,
            timeout_seconds=45,
            outputs=["replacement_assets", "similar_asset_map"],
        ),
        AgentStep(
            agent_name="@quantitative-analyst",
            prompt_template=(
                "Calculate execution costs and net benefit: "
                "For each harvest opportunity: "
                "- Selling gas cost "
                "- Buying replacement gas cost "
                "- Slippage impact "
                "- Total execution cost "
                "- Net tax benefit (tax savings - costs) "
                "- Breakeven holding period for replacement asset "
                "Only recommend harvests with net benefit > {{min_net_benefit}}$"
            ),
            depends_on=[2],
            parallel_execution=False,
            timeout_seconds=30,
            outputs=["execution_costs", "net_benefits", "recommended_harvests"],
        ),
        AgentStep(
            agent_name="@product-manager",
            prompt_template=(
                "Create tax loss harvesting strategy: "
                "Prioritize opportunities by: "
                "1. Highest net tax benefit "
                "2. Urgency (approaching tax year end: {{tax_year_end}}) "
                "3. Wash sale compliance "
                "For each recommended harvest: "
                "- Asset to sell "
                "- Recommended replacement "
                "- Tax savings "
                "- Net benefit "
                "- Execution steps "
                "Total potential tax savings: {{tax_savings}}"
            ),
            depends_on=[3],
            parallel_execution=False,
            timeout_seconds=30,
            outputs=[
                "harvest_strategy",
                "prioritized_opportunities",
                "execution_timeline",
            ],
        ),
        AgentStep(
            agent_name="@project-manager",
            prompt_template=(
                "Generate tax loss harvesting report: "
                "Executive Summary: "
                "- Total harvestable losses: {{total_unrealized_loss}} "
                "- Potential tax savings: {{tax_savings}} "
                "- Recommended actions: {{recommended_harvests}} count "
                "- Net benefit after costs: $X "
                "Implementation Plan: "
                "- Immediate actions (execute this week) "
                "- Scheduled actions (timing for wash sale compliance) "
                "- Year-end deadline actions "
                "Monitoring: "
                "- Track replacement asset performance "
                "- Re-entry strategy for sold assets after 30 days "
                "- Tax documentation requirements"
            ),
            depends_on=[4],
            parallel_execution=False,
            timeout_seconds=30,
            outputs=["tlh_report", "implementation_plan", "monitoring_checklist"],
        ),
    ]

    required_inputs = {
        "wallet_address": InputSpec(
            type="wallet_address",
            required=True,
            description="Wallet address to analyze",
            validation_pattern=r"^0x[a-fA-F0-9]{40}$",
        ),
        "tax_rate": InputSpec(
            type="number",
            required=False,
            description="Capital gains tax rate percentage",
            default=20,
        ),
        "tax_jurisdiction": InputSpec(
            type="string",
            required=False,
            description="Tax jurisdiction (e.g., 'US', 'UK', 'EU')",
            default="US",
        ),
        "tax_year_end": InputSpec(
            type="string",
            required=False,
            description="Tax year end date (YYYY-MM-DD)",
            default="2024-12-31",
        ),
        "min_loss_threshold": InputSpec(
            type="number",
            required=False,
            description="Minimum loss percentage to consider",
            default=10,
        ),
        "min_net_benefit": InputSpec(
            type="number",
            required=False,
            description="Minimum net benefit in USD to recommend harvest",
            default=100,
        ),
    }

    return ConversationTemplate.create(
        name="Tax Loss Harvesting",
        description=(
            "Strategic tax loss harvesting analysis to minimize tax liability while "
            "maintaining portfolio exposure. Includes wash sale compliance, similar asset "
            "recommendations, cost-benefit analysis, and implementation roadmap."
        ),
        category="portfolio_management",
        agent_sequence=agent_sequence,
        required_inputs=required_inputs,
        estimated_duration_seconds=240,  # 4 minutes
        created_by=created_by,
        is_public=True,
    )
