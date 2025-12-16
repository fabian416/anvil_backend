"""
Risk Assessment Report Template

Deep 7-step risk analysis workflow.
Estimated duration: 5 minutes
"""

from uuid import UUID

from app.domain.entities.chat.conversation_template import (
    ConversationTemplate,
    AgentStep,
    InputSpec,
)


def create_risk_assessment_report_template(created_by: UUID) -> ConversationTemplate:
    """
    Create comprehensive risk assessment report template.

    This template performs deep risk analysis including:
    - Market risk exposure
    - Smart contract risks
    - Liquidity risks
    - Concentration risks
    - Correlation analysis
    - Tail risk assessment
    - Risk mitigation recommendations

    Args:
        created_by: User ID creating the template

    Returns:
        ConversationTemplate instance
    """

    agent_sequence = [
        AgentStep(
            agent_name="@portfolio-analyst",
            prompt_template=(
                "Fetch current portfolio composition for {{wallet_address}}. "
                "List all positions with: asset, quantity, current value, % of portfolio."
            ),
            depends_on=[],
            parallel_execution=False,
            timeout_seconds=30,
            outputs=["positions", "total_value", "position_weights"],
        ),
        AgentStep(
            agent_name="@risk-analyst",
            prompt_template=(
                "Calculate market risk metrics: "
                "- Portfolio beta vs {{market_benchmark}} "
                "- Value at Risk (VaR) at {{confidence_level}}% confidence "
                "- Maximum drawdown potential "
                "- Volatility (30-day, 90-day) "
                "Use positions: {{positions}}"
            ),
            depends_on=[0],
            parallel_execution=False,
            timeout_seconds=45,
            outputs=["portfolio_beta", "var", "max_drawdown", "volatility"],
        ),
        AgentStep(
            agent_name="@security-specialist",
            prompt_template=(
                "Assess smart contract and protocol risks: "
                "For each DeFi protocol in the portfolio: "
                "- Audit status and score "
                "- Known vulnerabilities "
                "- Time since last audit "
                "- TVL and age of protocol "
                "- Bug bounty program presence "
                "Assign risk rating (Low/Medium/High/Critical) to each."
            ),
            depends_on=[0],
            parallel_execution=True,
            timeout_seconds=60,
            outputs=["protocol_risks", "audit_status", "vulnerability_count"],
        ),
        AgentStep(
            agent_name="@defi-specialist",
            prompt_template=(
                "Evaluate liquidity risks: "
                "- Slippage impact for 10%, 25%, 50% portfolio liquidation "
                "- DEX liquidity depth for each asset "
                "- Days to liquidate at normal volume "
                "- Assets with <$100k daily volume "
                "Flag assets with high liquidity risk."
            ),
            depends_on=[0],
            parallel_execution=True,
            timeout_seconds=45,
            outputs=["liquidity_score", "slippage_impact", "illiquid_assets"],
        ),
        AgentStep(
            agent_name="@risk-analyst",
            prompt_template=(
                "Analyze concentration and correlation risks: "
                "- Herfindahl index for concentration "
                "- Correlation matrix for top 10 assets "
                "- Sector/protocol concentration "
                "- Chain concentration risk "
                "Identify highly correlated clusters (>0.7 correlation)."
            ),
            depends_on=[0],
            parallel_execution=False,
            timeout_seconds=45,
            outputs=["concentration_index", "correlation_matrix", "risk_clusters"],
        ),
        AgentStep(
            agent_name="@quantitative-analyst",
            prompt_template=(
                "Perform tail risk analysis: "
                "- Historical stress scenarios (2020 crash, Terra collapse) "
                "- Portfolio performance in -50%, -70% market scenarios "
                "- Conditional VaR (CVaR) at {{confidence_level}}% "
                "- Black swan exposure assessment "
                "Estimate worst-case 30-day loss."
            ),
            depends_on=[1, 4],
            parallel_execution=False,
            timeout_seconds=60,
            outputs=["stress_test_results", "cvar", "worst_case_loss"],
        ),
        AgentStep(
            agent_name="@product-manager",
            prompt_template=(
                "Synthesize comprehensive risk report: "
                "1. Executive Summary: Overall risk rating (1-10) "
                "2. Key Risk Factors: Top 5 risks by severity "
                "3. Risk Breakdown: Market {{portfolio_beta}}, Smart Contract {{protocol_risks}}, "
                "   Liquidity {{liquidity_score}}, Concentration {{concentration_index}} "
                "4. Tail Risks: Worst case {{worst_case_loss}} "
                "5. Mitigation Recommendations: Actionable steps to reduce risk "
                "Format as detailed report with risk heat map."
            ),
            depends_on=[1, 2, 3, 4, 5],
            parallel_execution=False,
            timeout_seconds=45,
            outputs=["risk_rating", "risk_report", "mitigation_plan"],
        ),
    ]

    required_inputs = {
        "wallet_address": InputSpec(
            type="wallet_address",
            required=True,
            description="Wallet address to analyze",
            validation_pattern=r"^0x[a-fA-F0-9]{40}$",
        ),
        "market_benchmark": InputSpec(
            type="string",
            required=False,
            description="Market benchmark for beta calculation (e.g., 'ETH', 'BTC', 'TOTAL_CRYPTO')",
            default="ETH",
        ),
        "confidence_level": InputSpec(
            type="number",
            required=False,
            description="Confidence level for VaR calculation (e.g., 95, 99)",
            default=95,
        ),
    }

    return ConversationTemplate.create(
        name="Risk Assessment Report",
        description=(
            "Comprehensive risk analysis including market risk, smart contract risks, "
            "liquidity assessment, concentration analysis, tail risk evaluation, and mitigation strategies."
        ),
        category="portfolio_management",
        agent_sequence=agent_sequence,
        required_inputs=required_inputs,
        estimated_duration_seconds=300,  # 5 minutes
        created_by=created_by,
        is_public=True,
    )
