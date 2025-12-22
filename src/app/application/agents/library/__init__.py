"""
Agent Library - Pre-configured Custom Agent Personalities.

This module provides a curated library of expert AI agents specialized
in various DeFi protocols and technical domains.

Categories:
-----------
1. DeFi Specialists (5 agents):
   - Curve Finance Expert: Curve pools, stableswap mechanics, veCRV strategies
   - Aave Specialist: Lending, borrowing, health factors, liquidation risk
   - Uniswap Expert: AMM mechanics, concentrated liquidity, LP strategies
   - Yearn Strategist: Vault strategies, yield optimization, auto-compounding
   - Compound Advisor: Money markets, collateral management, interest rates

2. Technical Experts (5 agents):
   - Smart Contract Auditor: Security analysis, vulnerability detection
   - Gas Optimization Expert: Transaction optimization, EVM efficiency
   - MEV Protection Advisor: Frontrunning prevention, Flashbots strategies
   - Bridge Specialist: Cross-chain transfers, bridge security
   - Wallet Security Expert: Key management, phishing prevention, best practices

Usage:
------
```python
from app.application.agents.library import (
    get_agent,
    get_all_agents,
    get_defi_specialists,
    get_technical_experts,
    search_agents,
)

# Get specific agent
curve_expert = get_agent("curve_finance_expert")

# Get all DeFi specialists
defi_agents = get_defi_specialists()

# Search agents
security_agents = search_agents("security")

# Get agent registry for advanced operations
from app.application.agents.library import get_agent_registry
registry = get_agent_registry()
stats = registry.get_library_stats()
```

Each agent configuration includes:
- System prompt (personality, expertise)
- Capabilities list
- Temperature and max_tokens settings
- Personality traits (JSONB)
- Response style (technical, balanced, beginner-friendly)
- Preferred LLM provider
"""

# Import individual agent factories
from app.application.agents.library.curve_finance_expert import create_curve_finance_expert
from app.application.agents.library.aave_specialist import create_aave_specialist
from app.application.agents.library.uniswap_expert import create_uniswap_expert
from app.application.agents.library.yearn_strategist import create_yearn_strategist
from app.application.agents.library.compound_advisor import create_compound_advisor
from app.application.agents.library.smart_contract_auditor import create_smart_contract_auditor
from app.application.agents.library.gas_optimization_expert import create_gas_optimization_expert
from app.application.agents.library.mev_protection_advisor import create_mev_protection_advisor
from app.application.agents.library.bridge_specialist import create_bridge_specialist
from app.application.agents.library.wallet_security_expert import create_wallet_security_expert

# Import registry and convenience functions
from app.application.agents.library.agent_registry import (
    AgentLibraryRegistry,
    AgentCategory,
    AgentLibraryEntry,
    get_agent_registry,
    get_agent,
    get_all_agents,
    get_defi_specialists,
    get_technical_experts,
    search_agents,
)


__all__ = [
    # Agent factory functions
    "create_curve_finance_expert",
    "create_aave_specialist",
    "create_uniswap_expert",
    "create_yearn_strategist",
    "create_compound_advisor",
    "create_smart_contract_auditor",
    "create_gas_optimization_expert",
    "create_mev_protection_advisor",
    "create_bridge_specialist",
    "create_wallet_security_expert",

    # Registry classes
    "AgentLibraryRegistry",
    "AgentCategory",
    "AgentLibraryEntry",

    # Convenience functions (recommended for most use cases)
    "get_agent_registry",
    "get_agent",
    "get_all_agents",
    "get_defi_specialists",
    "get_technical_experts",
    "search_agents",
]


# Version and metadata
__version__ = "1.0.0"
__author__ = "Anvil Backend Team"

# Library statistics (computed at import time)
_LIBRARY_STATS = {
    "total_agents": 10,
    "defi_specialists": 5,
    "technical_experts": 5,
    "supported_protocols": [
        "Curve Finance",
        "Aave",
        "Uniswap",
        "Yearn",
        "Compound",
    ],
    "supported_domains": [
        "Security",
        "Optimization",
        "Infrastructure",
    ],
}


def get_library_info() -> dict:
    """
    Get information about the agent library.

    Returns:
        Dictionary with library metadata and statistics
    """
    return {
        "version": __version__,
        "stats": _LIBRARY_STATS,
        "categories": [cat.value for cat in AgentCategory],
        "description": "Pre-configured expert AI agents for DeFi and blockchain development",
    }
