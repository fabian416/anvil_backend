"""
Agent types for multi-agent orchestration system.

Full 18-agent enterprise roster:
- 10 core user-facing agents
- 8 enterprise agents (compliance, treasury, crisis management)
"""

from enum import Enum


class AgentType(Enum):
    """
    Agent types for Agent Squad multi-agent orchestration.
    
    Core User-Facing Agents (11):
    - CHAT: General conversation
    - GUEST_AUTH: Authentication requirements for restricted features (guest users)
    - HUNTER_AI: Market sentiment & predictions
    - RESEARCH: Deep protocol analysis
    - EXECUTION: Transaction execution (Privy wallet)
    - RISK_ANALYZER: Risk assessment & scoring
    - PORTFOLIO: Portfolio optimization & rebalancing
    - TAX_OPTIMIZER: Tax-loss harvesting & reporting
    - DEFI_YIELD: Yield farming & APY analysis
    - SECURITY_AUDITOR: Smart contract security analysis
    - GAS_OPTIMIZER: Gas fee optimization & timing
    
    Enterprise Agents (8):
    - COMPLIANCE_MONITOR: AML/KYC, regulatory compliance
    - MULTISIG_COORDINATOR: Multi-sig treasury management
    - ALERT_MONITORING: Real-time alerts, anomaly detection
    - CRISIS_MANAGER: Emergency response, circuit breaker
    - BRIDGE_CROSSCHAIN: Layer 2, cross-chain operations
    - LENDING_BORROWING: Leverage, collateral optimization
    - NFT_ASSET_MANAGER: NFT portfolio, valuation
    - DAO_GOVERNANCE: Voting, proposals, delegation
    """
    
    # Core User-Facing Agents (11)
    CHAT = "chat"
    GUEST_AUTH = "guest_auth"
    HUNTER_AI = "hunter_ai"
    RESEARCH = "research"
    EXECUTION = "execution"
    RISK_ANALYZER = "risk_analyzer"
    PORTFOLIO = "portfolio"
    TAX_OPTIMIZER = "tax_optimizer"
    DEFI_YIELD = "defi_yield"
    SECURITY_AUDITOR = "security_auditor"
    GAS_OPTIMIZER = "gas_optimizer"
    
    # Enterprise Agents (8)
    COMPLIANCE_MONITOR = "compliance_monitor"
    MULTISIG_COORDINATOR = "multisig_coordinator"
    ALERT_MONITORING = "alert_monitoring"
    CRISIS_MANAGER = "crisis_manager"
    BRIDGE_CROSSCHAIN = "bridge_crosschain"
    LENDING_BORROWING = "lending_borrowing"
    NFT_ASSET_MANAGER = "nft_asset_manager"
    DAO_GOVERNANCE = "dao_governance"
    
    # Legacy agents (backwards compatibility)
    TRADING = "execution"  # Alias for EXECUTION
    YIELD_FARMING = "defi_yield"  # Alias for DEFI_YIELD
    RISK_ANALYSIS = "risk_analyzer"  # Alias for RISK_ANALYZER
    
    @classmethod
    def is_enterprise_agent(cls, agent_type: "AgentType") -> bool:
        """Check if agent is enterprise-tier (requires enterprise subscription)."""
        enterprise_agents = {
            cls.COMPLIANCE_MONITOR,
            cls.MULTISIG_COORDINATOR,
            cls.ALERT_MONITORING,
            cls.CRISIS_MANAGER,
            cls.BRIDGE_CROSSCHAIN,
            cls.LENDING_BORROWING,
            cls.NFT_ASSET_MANAGER,
            cls.DAO_GOVERNANCE,
        }
        return agent_type in enterprise_agents
    
    @classmethod
    def get_core_agents(cls) -> list["AgentType"]:
        """Get list of core user-facing agents."""
        return [
            cls.CHAT,
            cls.GUEST_AUTH,
            cls.HUNTER_AI,
            cls.RESEARCH,
            cls.EXECUTION,
            cls.RISK_ANALYZER,
            cls.PORTFOLIO,
            cls.TAX_OPTIMIZER,
            cls.DEFI_YIELD,
            cls.SECURITY_AUDITOR,
            cls.GAS_OPTIMIZER,
        ]
    
    @classmethod
    def get_enterprise_agents(cls) -> list["AgentType"]:
        """Get list of enterprise agents."""
        return [
            cls.COMPLIANCE_MONITOR,
            cls.MULTISIG_COORDINATOR,
            cls.ALERT_MONITORING,
            cls.CRISIS_MANAGER,
            cls.BRIDGE_CROSSCHAIN,
            cls.LENDING_BORROWING,
            cls.NFT_ASSET_MANAGER,
            cls.DAO_GOVERNANCE,
        ]
    
    @classmethod
    def get_all_agents(cls) -> list["AgentType"]:
        """Get all 18 agents (excluding legacy aliases)."""
        return cls.get_core_agents() + cls.get_enterprise_agents()
