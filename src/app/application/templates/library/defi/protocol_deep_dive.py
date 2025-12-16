"""
Protocol Deep Dive Template

Comprehensive 10-step protocol analysis.
Estimated duration: 10 minutes
"""

from uuid import UUID

from app.domain.entities.chat.conversation_template import (
    ConversationTemplate,
    AgentStep,
    InputSpec,
)


def create_protocol_deep_dive_template(created_by: UUID) -> ConversationTemplate:
    """
    Create protocol deep dive analysis template.

    This template performs comprehensive protocol analysis:
    - Protocol overview and metrics
    - Security assessment
    - Tokenomics analysis
    - Competitive positioning
    - Financial health
    - User adoption trends
    - Risk assessment
    - Team and governance
    - Integration ecosystem
    - Investment recommendation

    Args:
        created_by: User ID creating the template

    Returns:
        ConversationTemplate instance
    """

    agent_sequence = [
        AgentStep(
            agent_name="@defi-specialist",
            prompt_template=(
                "Provide protocol overview for {{protocol_name}}: "
                "- Protocol type (DEX, lending, derivatives, etc.) "
                "- Launch date and age "
                "- Supported chains "
                "- Core functionality "
                "- Unique value proposition "
                "- Current TVL and ranking "
                "- 30-day volume "
                "- User count (if available)"
            ),
            depends_on=[],
            parallel_execution=False,
            timeout_seconds=30,
            outputs=["protocol_type", "launch_date", "tvl", "volume", "user_count"],
        ),
        AgentStep(
            agent_name="@security-specialist",
            prompt_template=(
                "Assess security posture of {{protocol_name}}: "
                "- Audit history (who, when, findings) "
                "- Number of audits completed "
                "- Critical vulnerabilities found "
                "- Bug bounty program (size, platform) "
                "- Historical exploits/incidents "
                "- Time-weighted security score "
                "- Multi-sig setup for admin keys "
                "- Upgrade mechanism security "
                "Assign security rating: A/B/C/D/F"
            ),
            depends_on=[],
            parallel_execution=True,
            timeout_seconds=60,
            outputs=["audit_history", "security_incidents", "security_rating", "bug_bounty_size"],
        ),
        AgentStep(
            agent_name="@tokenomics-analyst",
            prompt_template=(
                "Analyze tokenomics for {{protocol_name}} token: "
                "- Token ticker and contract address "
                "- Total supply and circulating supply "
                "- Emission schedule "
                "- Token utility (governance, fees, staking) "
                "- Revenue sharing mechanism "
                "- Token distribution (team, investors, community) "
                "- Vesting schedules "
                "- Inflation rate "
                "- Price performance (6m, 1y, all-time) "
                "Tokenomics sustainability score: 1-10"
            ),
            depends_on=[],
            parallel_execution=True,
            timeout_seconds=45,
            outputs=["token_info", "token_distribution", "inflation_rate", "tokenomics_score"],
        ),
        AgentStep(
            agent_name="@market-analyst",
            prompt_template=(
                "Analyze competitive positioning: "
                "- Top 3 direct competitors "
                "- Market share comparison "
                "- Feature comparison matrix "
                "- Fee structure vs competitors "
                "- User growth vs competitors "
                "- TVL trends vs competitors "
                "- Competitive advantages "
                "- Competitive disadvantages "
                "Market position: Leader/Challenger/Follower/Niche"
            ),
            depends_on=[0],
            parallel_execution=False,
            timeout_seconds=60,
            outputs=["competitors", "market_share", "competitive_advantages", "market_position"],
        ),
        AgentStep(
            agent_name="@financial-analyst",
            prompt_template=(
                "Evaluate financial health and sustainability: "
                "- Protocol revenue (last 30d, 90d, 1y) "
                "- Revenue trend (growing/stable/declining) "
                "- Token emissions vs revenue "
                "- Treasury size and runway "
                "- Revenue per TVL (efficiency) "
                "- Profitability status "
                "- Fee switch potential "
                "Financial health score: 1-10"
            ),
            depends_on=[0],
            parallel_execution=True,
            timeout_seconds=45,
            outputs=["protocol_revenue", "revenue_trend", "treasury_size", "financial_health_score"],
        ),
        AgentStep(
            agent_name="@data-analyst",
            prompt_template=(
                "Analyze user adoption and growth metrics: "
                "- Daily/Monthly active users trend "
                "- User retention rate "
                "- New user growth rate "
                "- Power user concentration (top 10 users % of volume) "
                "- Geographic distribution "
                "- User acquisition cost (if available) "
                "- Churn rate "
                "Adoption momentum: Accelerating/Stable/Declining"
            ),
            depends_on=[0],
            parallel_execution=True,
            timeout_seconds=45,
            outputs=["active_users", "user_growth", "retention_rate", "adoption_momentum"],
        ),
        AgentStep(
            agent_name="@risk-analyst",
            prompt_template=(
                "Comprehensive risk assessment: "
                "Risk categories: "
                "1. Smart contract risk: {{security_rating}} "
                "2. Centralization risk: Admin keys, governance "
                "3. Liquidity risk: DEX liquidity, exit scenarios "
                "4. Oracle risk: Price feed dependencies "
                "5. Composability risk: External protocol dependencies "
                "6. Regulatory risk: Compliance exposure "
                "7. Economic risk: Token sustainability, IL exposure "
                "Overall risk score: 1-10 (10 = highest risk)"
            ),
            depends_on=[1, 2],
            parallel_execution=False,
            timeout_seconds=60,
            outputs=["risk_breakdown", "overall_risk_score", "critical_risks"],
        ),
        AgentStep(
            agent_name="@governance-analyst",
            prompt_template=(
                "Evaluate team and governance: "
                "- Team transparency (anon vs doxxed) "
                "- Team background and experience "
                "- Governance model (token voting, multi-sig, etc.) "
                "- Governance participation rate "
                "- Recent governance proposals "
                "- Decentralization roadmap "
                "- Community strength and engagement "
                "Governance quality score: 1-10"
            ),
            depends_on=[],
            parallel_execution=True,
            timeout_seconds=45,
            outputs=["team_info", "governance_model", "community_engagement", "governance_score"],
        ),
        AgentStep(
            agent_name="@integration-specialist",
            prompt_template=(
                "Map integration ecosystem: "
                "- Number of integrations/partnerships "
                "- Key partners and integrations "
                "- Aggregator support (1inch, Matcha, etc.) "
                "- Wallet integrations "
                "- Institutional adoption "
                "- Developer activity (GitHub stats) "
                "- API/SDK availability "
                "Ecosystem strength: Strong/Moderate/Weak"
            ),
            depends_on=[0],
            parallel_execution=True,
            timeout_seconds=45,
            outputs=["integrations", "developer_activity", "ecosystem_strength"],
        ),
        AgentStep(
            agent_name="@product-manager",
            prompt_template=(
                "Synthesize complete protocol analysis: "
                "1. Executive Summary "
                "   - Protocol: {{protocol_name}} "
                "   - Category: {{protocol_type}} "
                "   - Overall Score: Average of all scores "
                "2. Key Metrics "
                "   - TVL: {{tvl}}, Volume: {{volume}} "
                "   - Users: {{user_count}}, Growth: {{adoption_momentum}} "
                "3. Strengths (Top 3) "
                "4. Weaknesses (Top 3) "
                "5. Risk Assessment: {{overall_risk_score}}/10 "
                "6. Scores Breakdown: "
                "   - Security: {{security_rating}} "
                "   - Tokenomics: {{tokenomics_score}}/10 "
                "   - Financial Health: {{financial_health_score}}/10 "
                "   - Governance: {{governance_score}}/10 "
                "7. Investment Thesis: Bull/Bear cases "
                "8. Recommendation: Strong Buy/Buy/Hold/Avoid "
                "9. Price Target (if applicable) "
                "10. Risk Level: Low/Medium/High/Critical"
            ),
            depends_on=[0, 1, 2, 3, 4, 5, 6, 7, 8],
            parallel_execution=False,
            timeout_seconds=60,
            outputs=["complete_analysis", "recommendation", "overall_score"],
        ),
    ]

    required_inputs = {
        "protocol_name": InputSpec(
            type="string",
            required=True,
            description="Protocol name to analyze (e.g., 'Uniswap', 'Aave', 'Curve')",
        ),
    }

    return ConversationTemplate.create(
        name="Protocol Deep Dive",
        description=(
            "Comprehensive 10-step protocol analysis covering security, tokenomics, "
            "competitive positioning, financial health, user adoption, risks, governance, "
            "ecosystem integrations, and investment recommendation."
        ),
        category="defi_analysis",
        agent_sequence=agent_sequence,
        required_inputs=required_inputs,
        estimated_duration_seconds=600,  # 10 minutes
        created_by=created_by,
        is_public=True,
    )
