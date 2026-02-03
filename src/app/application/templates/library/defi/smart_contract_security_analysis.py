"""Smart Contract Security Analysis Template

Deep security analysis of smart contracts for DeFi protocols, including
audit review, code analysis, and vulnerability assessment.
"""

from uuid import UUID

from app.domain.entities.chat.conversation_template import (
    AgentStep,
    ConversationTemplate,
    InputSpec,
)


def create_smart_contract_security_analysis_template(
    created_by: UUID,
) -> ConversationTemplate:
    """Create smart contract security analysis template.

    Comprehensive security assessment including:
    - Audit history and findings review
    - Code quality and complexity analysis
    - Common vulnerability patterns (reentrancy, overflow, etc.)
    - Access control and privilege analysis
    - Upgrade mechanisms and admin risks
    - Historical exploit analysis

    Args:
        created_by: User ID creating the template

    Returns:
        Configured ConversationTemplate instance
    """

    agent_sequence = [
        AgentStep(
            agent_name="@defi-specialist",
            prompt_template=(
                "Gather basic information about {{protocol_name}} smart contracts: "
                "- Main contract addresses on {{chain}} "
                "- Contract deployment dates "
                "- Verified source code links (Etherscan, etc.) "
                "- GitHub repository and commit hashes "
                "- Protocol documentation and architecture "
                "- Total value locked (TVL) "
                "- Number of users and transactions"
            ),
            depends_on=[],
            parallel_execution=False,
            timeout_seconds=30,
            outputs=[
                "contract_addresses",
                "deployment_dates",
                "source_code_links",
                "github_repo",
                "current_tvl",
            ],
        ),
        AgentStep(
            agent_name="@security-specialist",
            prompt_template=(
                "Review audit history and findings: "
                "For {{protocol_name}} contracts at {{contract_addresses}}, research: "
                "- All published audit reports (firm, date, scope) "
                "- Critical, High, Medium, Low findings counts "
                "- Status of findings (fixed, acknowledged, accepted risk) "
                "- Time between audit and deployment "
                "- Code changes since last audit "
                "- Bug bounty program details "
                "Provide audit timeline and current status"
            ),
            depends_on=[0],
            parallel_execution=False,
            timeout_seconds=60,
            outputs=[
                "audit_reports",
                "findings_summary",
                "remediation_status",
                "bug_bounty_program",
                "audit_score",
            ],
        ),
        AgentStep(
            agent_name="@security-specialist",
            prompt_template=(
                "Analyze code quality and architecture: "
                "Review source code from {{source_code_links}}: "
                "- Code complexity (lines of code, cyclomatic complexity) "
                "- Use of well-tested libraries (OpenZeppelin, etc.) "
                "- Custom crypto implementations (red flag) "
                "- Code documentation and comments "
                "- Test coverage percentage "
                "- Upgrade patterns (proxy, multisig) "
                "- External dependencies and oracle usage "
                "Rate code quality (1-10)"
            ),
            depends_on=[0],
            parallel_execution=True,
            timeout_seconds=60,
            outputs=[
                "code_complexity",
                "library_usage",
                "test_coverage",
                "upgrade_pattern",
                "code_quality_score",
            ],
        ),
        AgentStep(
            agent_name="@security-specialist",
            prompt_template=(
                "Check for common vulnerability patterns: "
                "Analyze contracts for: "
                "1. Reentrancy vulnerabilities "
                "   - Checks-Effects-Interactions pattern "
                "   - ReentrancyGuard usage "
                "2. Integer overflow/underflow "
                "   - SafeMath or Solidity 0.8+ "
                "3. Access control "
                "   - onlyOwner, role-based access "
                "   - Centralization risks "
                "4. Front-running risks "
                "   - MEV exposure "
                "   - Slippage protection "
                "5. Oracle manipulation "
                "   - TWAP vs spot prices "
                "   - Oracle diversity "
                "Flag any detected issues with severity"
            ),
            depends_on=[2],
            parallel_execution=False,
            timeout_seconds=60,
            outputs=[
                "vulnerability_findings",
                "severity_counts",
                "mitigation_measures",
                "vulnerability_score",
            ],
        ),
        AgentStep(
            agent_name="@security-specialist",
            prompt_template=(
                "Assess privilege and admin risks: "
                "For {{protocol_name}} contracts: "
                "- Admin key structure (EOA, multisig, DAO) "
                "- Multisig signers count and timelock "
                "- Admin capabilities: "
                "  * Pause/unpause "
                "  * Upgrade contracts "
                "  * Change parameters "
                "  * Withdraw funds "
                "- Emergency procedures "
                "- Governance process maturity "
                "Evaluate centralization risk (1-10, 10 = fully centralized)"
            ),
            depends_on=[3],
            parallel_execution=True,
            timeout_seconds=45,
            outputs=[
                "admin_structure",
                "admin_capabilities",
                "timelock_delay",
                "centralization_risk",
            ],
        ),
        AgentStep(
            agent_name="@data-analyst",
            prompt_template=(
                "Analyze historical security record: "
                "Research {{protocol_name}} history: "
                "- Past exploits or hacks (dates, amounts) "
                "- Post-mortem reports and lessons learned "
                "- Response time and communication quality "
                "- User fund recovery (full, partial, none) "
                "- Similar protocols with issues "
                "- Time in production without incidents "
                "Calculate battle-testing score based on TVL × days_live"
            ),
            depends_on=[0],
            parallel_execution=True,
            timeout_seconds=45,
            outputs=[
                "exploit_history",
                "incident_response_quality",
                "recovery_track_record",
                "battle_testing_score",
            ],
        ),
        AgentStep(
            agent_name="@risk-analyst",
            prompt_template=(
                "Calculate composite security score: "
                "Using all gathered data: "
                "- Audit score: {{audit_score}} (25% weight) "
                "- Code quality: {{code_quality_score}} (20% weight) "
                "- Vulnerability score: {{vulnerability_score}} (25% weight) "
                "- Centralization risk: {{centralization_risk}} (15% weight) "
                "- Battle testing: {{battle_testing_score}} (15% weight) "
                "Final score = weighted average (1-10, 10 = safest) "
                "Also calculate: "
                "- Maximum recommended position size "
                "- Insurance availability and cost"
            ),
            depends_on=[1, 2, 3, 4, 5],
            parallel_execution=False,
            timeout_seconds=30,
            outputs=[
                "composite_security_score",
                "max_position_size",
                "insurance_options",
                "risk_level",
            ],
        ),
        AgentStep(
            agent_name="@product-manager",
            prompt_template=(
                "Generate comprehensive security report: "
                "1. Executive Summary: "
                "   - Overall security rating: {{composite_security_score}}/10 "
                "   - Risk level: {{risk_level}} "
                "   - Maximum recommended exposure: {{max_position_size}} "
                "2. Detailed Findings: "
                "   - Audit Status: {{audit_reports}} "
                "   - Code Quality: {{code_quality_score}}/10 "
                "   - Vulnerabilities: {{vulnerability_findings}} "
                "   - Admin Risks: {{centralization_risk}}/10 "
                "   - Historical Record: {{exploit_history}} "
                "3. Risk Mitigation: "
                "   - Insurance options: {{insurance_options}} "
                "   - Monitoring recommendations "
                "   - Exit strategy planning "
                "4. Recommendations: "
                "   - Suitable for: [Conservative/Moderate/Aggressive] investors "
                "   - Position sizing guidance "
                "   - Ongoing monitoring checklist"
            ),
            depends_on=[6],
            parallel_execution=False,
            timeout_seconds=60,
            outputs=[
                "security_report",
                "risk_assessment",
                "recommendations",
                "monitoring_checklist",
            ],
        ),
    ]

    required_inputs = {
        "protocol_name": InputSpec(
            type="string",
            required=True,
            description="Name of the DeFi protocol to analyze",
        ),
        "chain": InputSpec(
            type="string",
            required=False,
            description="Blockchain network (ethereum, arbitrum, polygon, etc.)",
            default="ethereum",
        ),
        "contract_address": InputSpec(
            type="contract_address",
            required=False,
            description="Specific contract address to analyze (optional)",
            default="",
        ),
    }

    return ConversationTemplate.create(
        name="Smart Contract Security Analysis",
        description=(
            "Comprehensive smart contract security assessment for DeFi protocols. "
            "Reviews audit history, analyzes code quality, checks for common vulnerabilities, "
            "assesses admin risks, and provides risk-based recommendations. Includes "
            "composite security scoring and position sizing guidance."
        ),
        category="defi_analysis",
        agent_sequence=agent_sequence,
        required_inputs=required_inputs,
        estimated_duration_seconds=360,  # 6 minutes
        created_by=created_by,
        is_public=True,
        tags=["defi", "security", "smart-contracts", "audits", "risk-analysis"],
    )
