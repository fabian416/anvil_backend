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
    
    # Core User-Facing Agents (14)
    CHAT = "chat"
    GUEST_AUTH = "guest_auth"
    KNOWLEDGE = "knowledge"  # Knowledge Anvil - Educational queries and Anvil knowledge
    HUNTER_AI = "hunter_ai"
    RESEARCH = "research"
    EXECUTION = "execution"
    RISK_ANALYZER = "risk_analyzer"
    PORTFOLIO = "portfolio"
    TAX_OPTIMIZER = "tax_optimizer"
    DEFI_YIELD = "defi_yield"
    SECURITY_AUDITOR = "security_auditor"
    GAS_OPTIMIZER = "gas_optimizer"
    
    # Authenticated User Agents (requires login)
    WALLET = "wallet"  # Wallet management & balances (authenticated only)
    TRANSACTION_HISTORY = "transaction_history"  # Transaction history queries (authenticated only)
    
    # Workflow Agents (multi-step operations for authenticated users)
    SWAP_WORKFLOW = "swap_workflow"  # Multi-step swap workflow
    LENDING_WORKFLOW = "lending_workflow"  # Multi-step lending/deposit workflow
    BUY_WORKFLOW = "buy_workflow"  # Multi-step fiat on-ramp workflow
    TRANSFER_WORKFLOW = "transfer_workflow"  # Multi-step token transfer workflow
    MONEY_MARKET_WORKFLOW = "money_market_workflow"  # Multi-step compare & select workflow
    
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
            cls.KNOWLEDGE,
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
    def get_authenticated_agents(cls) -> list["AgentType"]:
        """Get list of agents that require authentication."""
        return [
            cls.WALLET,
            cls.TRANSACTION_HISTORY,
        ]
    
    @classmethod
    def is_authenticated_agent(cls, agent_type: "AgentType") -> bool:
        """Check if agent requires authentication."""
        return agent_type in cls.get_authenticated_agents()
    
    @classmethod
    def get_workflow_agents(cls) -> list["AgentType"]:
        """Get list of workflow agents (multi-step operations)."""
        return [
            cls.SWAP_WORKFLOW,
            cls.LENDING_WORKFLOW,
            cls.BUY_WORKFLOW,
            cls.TRANSFER_WORKFLOW,
            cls.MONEY_MARKET_WORKFLOW,
        ]
    
    @classmethod
    def is_workflow_agent(cls, agent_type: "AgentType") -> bool:
        """Check if agent is a workflow agent."""
        return agent_type in cls.get_workflow_agents()
    
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
        """Get all agents (excluding legacy aliases)."""
        return cls.get_core_agents() + cls.get_authenticated_agents() + cls.get_enterprise_agents()
