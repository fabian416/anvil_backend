"""
Portfolio Health Check Template

Comprehensive 5-step portfolio analysis workflow.
Estimated duration: 3 minutes
"""

from uuid import UUID

from app.domain.entities.chat.conversation_template import (
    ConversationTemplate,
    AgentStep,
    InputSpec,
)


def create_portfolio_health_check_template(created_by: UUID) -> ConversationTemplate:
    """
    Create portfolio health check template.

    This template performs a comprehensive portfolio analysis including:
    - Current holdings overview
    - Diversification analysis
    - Performance metrics
    - Risk exposure assessment
    - Quick recommendations

    Args:
        created_by: User ID creating the template

    Returns:
        ConversationTemplate instance
    """

    agent_sequence = [
        AgentStep(
            agent_name="@portfolio-analyst",
            prompt_template=(
                "Analyze the portfolio for wallet {{wallet_address}}. "
                "Provide an overview of current holdings, total value, and asset allocation. "
                "Focus on: total portfolio value, number of positions, top 5 holdings by value."
            ),
            depends_on=[],
            parallel_execution=False,
            timeout_seconds=30,
            outputs=[
                "total_value",
                "num_positions",
                "top_holdings",
                "asset_allocation",
            ],
        ),
        AgentStep(
            agent_name="@risk-analyst",
            prompt_template=(
                "Evaluate the diversification and risk exposure for the portfolio. "
                "Using the allocation data: {{asset_allocation}}, calculate: "
                "- Concentration risk (% in top 3 assets) "
                "- Sector/protocol diversification "
                "- Chain diversification "
                "Provide a diversification score (1-10)."
            ),
            depends_on=[0],
            parallel_execution=False,
            timeout_seconds=30,
            outputs=["concentration_risk", "diversification_score", "risk_factors"],
        ),
        AgentStep(
            agent_name="@portfolio-analyst",
            prompt_template=(
                "Calculate performance metrics for the portfolio over {{time_period}}. "
                "Include: ROI, absolute P&L, best/worst performers, realized vs unrealized gains. "
                "Compare performance to {{benchmark}} if specified."
            ),
            depends_on=[0],
            parallel_execution=True,
            timeout_seconds=45,
            outputs=["roi", "pnl", "best_performers", "worst_performers"],
        ),
        AgentStep(
            agent_name="@defi-specialist",
            prompt_template=(
                "Analyze DeFi-specific risks in the portfolio: "
                "- Smart contract risks for protocols in use "
                "- Impermanent loss exposure "
                "- Staking/locking periods "
                "- Protocol health scores "
                "Summarize top 3 DeFi risks."
            ),
            depends_on=[0],
            parallel_execution=True,
            timeout_seconds=45,
            outputs=["defi_risks", "protocol_health", "il_exposure"],
        ),
        AgentStep(
            agent_name="@product-manager",
            prompt_template=(
                "Synthesize the portfolio health analysis: "
                "- Overall health score (1-10) "
                "- Key strengths "
                "- Critical issues "
                "- Top 3 actionable recommendations "
                "Using data: total_value={{total_value}}, diversification={{diversification_score}}, "
                "risks={{risk_factors}}, defi_risks={{defi_risks}}"
            ),
            depends_on=[0, 1, 2, 3],
            parallel_execution=False,
            timeout_seconds=30,
            outputs=["health_score", "recommendations", "summary_report"],
        ),
    ]

    required_inputs = {
        "wallet_address": InputSpec(
            type="wallet_address",
            required=True,
            description="Wallet address to analyze",
            validation_pattern=r"^0x[a-fA-F0-9]{40}$",
        ),
        "time_period": InputSpec(
            type="string",
            required=False,
            description="Time period for performance analysis (e.g., '30d', '90d', '1y')",
            default="30d",
        ),
        "benchmark": InputSpec(
            type="string",
            required=False,
            description="Benchmark for performance comparison (e.g., 'ETH', 'BTC', 'SPY')",
            default="ETH",
        ),
    }

    return ConversationTemplate.create(
        name="Portfolio Health Check",
        description=(
            "Comprehensive portfolio analysis including holdings overview, "
            "diversification, performance metrics, risk assessment, and actionable recommendations."
        ),
        category="portfolio_management",
        agent_sequence=agent_sequence,
        required_inputs=required_inputs,
        estimated_duration_seconds=180,  # 3 minutes
        created_by=created_by,
        is_public=True,
    )
