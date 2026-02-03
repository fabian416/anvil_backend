"""
Get Enabled Agents Query.

This interactor retrieves all enabled agents for a user based on:
1. Feature flags (globally enabled/disabled agents)
2. User subscription tier (determines which agents are available)
"""

from app.domain.enums.agent_type import AgentType
from app.domain.ports.agent_squad.feature_flags_gateway import FeatureFlagsGateway


class GetEnabledAgents:
    """
    Query interactor for retrieving enabled agents.

    Responsibilities:
    - Get list of enabled agents from feature flags
    - Filter by user subscription tier (if applicable)
    - Return agent capabilities and metadata
    """

    def __init__(
        self,
        feature_flags: FeatureFlagsGateway,
    ):
        self._feature_flags = feature_flags

    async def execute(
        self,
        user_subscription_tier: str | None = None,
    ) -> dict:
        """
        Get all enabled agents for a user.

        Args:
            user_subscription_tier: User's subscription tier (free, pro, enterprise)
                                   None = return all enabled agents

        Returns:
            dict with:
                - agents: List of enabled agent configurations
                - total_count: Total number of enabled agents
                - subscription_tier: User's subscription tier

        Note:
            Subscription tier filtering:
            - Free: chat, hunter_ai, research, portfolio, gas_optimizer (5 agents)
            - Pro: Free + execution, risk_analyzer, tax_optimizer, defi_yield, security_auditor (10 agents)
            - Enterprise: All 18 agents
        """
        # Get all enabled agents from feature flags
        enabled_agents = await self._feature_flags.get_enabled_agents()

        # Filter by subscription tier
        if user_subscription_tier:
            enabled_agents = self._filter_by_tier(
                enabled_agents, user_subscription_tier
            )

        # Get agent configurations
        agent_configs = []
        for agent_type in enabled_agents:
            config = await self._feature_flags.get_agent_config(agent_type)
            agent_configs.append({
                "agent_type": agent_type.value,
                "name": self._get_agent_name(agent_type),
                "description": self._get_agent_description(agent_type),
                "capabilities": self._get_agent_capabilities(agent_type),
                "model": config.model,
                "temperature": config.temperature,
                "max_tokens": config.max_tokens,
                "tier_required": self._get_tier_required(agent_type),
            })

        return {
            "agents": agent_configs,
            "total_count": len(agent_configs),
            "subscription_tier": user_subscription_tier or "enterprise",
        }

    def _filter_by_tier(
        self,
        agents: list[AgentType],
        tier: str,
    ) -> list[AgentType]:
        """Filter agents by subscription tier."""
        tier = tier.lower()

        # Define tier access
        free_agents = {
            AgentType.CHAT,
            AgentType.HUNTER_AI,
            AgentType.RESEARCH,
            AgentType.PORTFOLIO,
            AgentType.GAS_OPTIMIZER,
        }

        pro_agents = free_agents | {
            AgentType.EXECUTION,
            AgentType.RISK_ANALYZER,
            AgentType.TAX_OPTIMIZER,
            AgentType.DEFI_YIELD,
            AgentType.SECURITY_AUDITOR,
        }

        # Enterprise gets all agents (no filter)

        if tier == "free":
            return [a for a in agents if a in free_agents]
        elif tier == "pro":
            return [a for a in agents if a in pro_agents]
        else:  # enterprise or unknown
            return agents

    def _get_agent_name(self, agent_type: AgentType) -> str:
        """Get human-readable agent name."""
        names = {
            AgentType.CHAT: "General Chat",
            AgentType.HUNTER_AI: "Hunter AI (Predictions)",
            AgentType.RESEARCH: "Research Assistant",
            AgentType.EXECUTION: "Transaction Executor",
            AgentType.RISK_ANALYZER: "Risk Analyzer",
            AgentType.PORTFOLIO: "Portfolio Manager",
            AgentType.TAX_OPTIMIZER: "Tax Optimizer",
            AgentType.DEFI_YIELD: "DeFi Yield Optimizer",
            AgentType.SECURITY_AUDITOR: "Security Auditor",
            AgentType.GAS_OPTIMIZER: "Gas Optimizer",
            AgentType.COMPLIANCE_MONITOR: "Compliance Monitor",
            AgentType.MULTISIG_COORDINATOR: "Multi-Sig Coordinator",
            AgentType.ALERT_MONITORING: "Alert & Monitoring",
            AgentType.CRISIS_MANAGER: "Crisis Manager",
            AgentType.BRIDGE_CROSSCHAIN: "Bridge & Cross-Chain",
            AgentType.LENDING_BORROWING: "Lending & Borrowing",
            AgentType.NFT_ASSET_MANAGER: "NFT & Asset Manager",
            AgentType.DAO_GOVERNANCE: "DAO Governance",
        }
        return names.get(agent_type, agent_type.value)

    def _get_agent_description(self, agent_type: AgentType) -> str:
        """Get agent description."""
        descriptions = {
            AgentType.CHAT: "General-purpose conversational agent for crypto/DeFi questions",
            AgentType.HUNTER_AI: "Market sentiment analysis and price predictions",
            AgentType.RESEARCH: "In-depth research on protocols, tokens, and trends",
            AgentType.EXECUTION: "Execute transactions with safety checks and 2FA",
            AgentType.RISK_ANALYZER: "Analyze portfolio risk and exposure",
            AgentType.PORTFOLIO: "Track and optimize portfolio performance",
            AgentType.TAX_OPTIMIZER: "Tax-loss harvesting and reporting",
            AgentType.DEFI_YIELD: "Find and optimize DeFi yield opportunities",
            AgentType.SECURITY_AUDITOR: "Smart contract security analysis",
            AgentType.GAS_OPTIMIZER: "Optimize transaction gas costs",
            AgentType.COMPLIANCE_MONITOR: "AML/KYC screening and regulatory compliance",
            AgentType.MULTISIG_COORDINATOR: "Multi-sig treasury management",
            AgentType.ALERT_MONITORING: "Real-time alerts and anomaly detection",
            AgentType.CRISIS_MANAGER: "Emergency response and circuit breakers",
            AgentType.BRIDGE_CROSSCHAIN: "Cross-chain bridging and Layer 2 operations",
            AgentType.LENDING_BORROWING: "Leverage and collateral optimization",
            AgentType.NFT_ASSET_MANAGER: "NFT portfolio and valuation management",
            AgentType.DAO_GOVERNANCE: "DAO voting, proposals, and delegation",
        }
        return descriptions.get(agent_type, "Agent description not available")

    def _get_agent_capabilities(self, agent_type: AgentType) -> list[str]:
        """Get agent capabilities."""
        capabilities_map = {
            AgentType.CHAT: ["general_qa", "explanations", "conversational"],
            AgentType.HUNTER_AI: [
                "sentiment_analysis",
                "price_predictions",
                "market_trends",
            ],
            AgentType.RESEARCH: [
                "protocol_research",
                "token_analysis",
                "trend_reports",
            ],
            AgentType.EXECUTION: ["swap", "stake", "bridge", "transaction_safety"],
            AgentType.RISK_ANALYZER: [
                "portfolio_risk",
                "exposure_analysis",
                "volatility",
            ],
            AgentType.PORTFOLIO: [
                "portfolio_tracking",
                "performance_metrics",
                "rebalancing",
            ],
            AgentType.TAX_OPTIMIZER: ["tax_loss_harvesting", "cost_basis", "reporting"],
            AgentType.DEFI_YIELD: [
                "yield_farming",
                "liquidity_mining",
                "apy_comparison",
            ],
            AgentType.SECURITY_AUDITOR: ["smart_contract_audit", "vulnerability_scan"],
            AgentType.GAS_OPTIMIZER: [
                "gas_estimation",
                "timing_optimization",
                "l2_recommendations",
            ],
            AgentType.COMPLIANCE_MONITOR: [
                "aml_kyc",
                "sanctions_screening",
                "pep_check",
            ],
            AgentType.MULTISIG_COORDINATOR: [
                "multisig_proposals",
                "treasury_management",
                "approval_tracking",
            ],
            AgentType.ALERT_MONITORING: [
                "real_time_alerts",
                "anomaly_detection",
                "threshold_monitoring",
            ],
            AgentType.CRISIS_MANAGER: [
                "emergency_response",
                "circuit_breaker",
                "protocol_pause",
            ],
            AgentType.BRIDGE_CROSSCHAIN: [
                "cross_chain_bridging",
                "l2_operations",
                "asset_transfer",
            ],
            AgentType.LENDING_BORROWING: [
                "leverage_optimization",
                "collateral_management",
                "liquidation_alerts",
            ],
            AgentType.NFT_ASSET_MANAGER: [
                "nft_valuation",
                "portfolio_tracking",
                "market_analysis",
            ],
            AgentType.DAO_GOVERNANCE: ["voting", "proposal_creation", "delegation"],
        }
        return capabilities_map.get(agent_type, [])

    def _get_tier_required(self, agent_type: AgentType) -> str:
        """Get minimum subscription tier required."""
        # Core user agents
        free_agents = {
            AgentType.CHAT,
            AgentType.HUNTER_AI,
            AgentType.RESEARCH,
            AgentType.PORTFOLIO,
            AgentType.GAS_OPTIMIZER,
        }

        pro_agents = {
            AgentType.EXECUTION,
            AgentType.RISK_ANALYZER,
            AgentType.TAX_OPTIMIZER,
            AgentType.DEFI_YIELD,
            AgentType.SECURITY_AUDITOR,
        }

        # Enterprise/advanced agents
        if agent_type in free_agents:
            return "free"
        elif agent_type in pro_agents:
            return "pro"
        else:
            return "enterprise"
