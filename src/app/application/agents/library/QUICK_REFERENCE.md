# Agent Library - Quick Reference

## Available Agents

### DeFi Specialists

| ID | Agent Name | Focus | Temperature | Style |
|---|---|---|---|---|
| `curve_finance_expert` | Curve Finance Expert | Curve pools, veCRV, stableswap | 0.3 | Technical |
| `aave_specialist` | Aave Specialist | Lending, health factors, liquidation | 0.2 | Technical |
| `uniswap_expert` | Uniswap Expert | V3 concentrated liquidity, LP | 0.3 | Technical |
| `yearn_strategist` | Yearn Strategist | Vaults, yield optimization | 0.4 | Balanced |
| `compound_advisor` | Compound Advisor | Money markets, collateral | 0.25 | Technical |

### Technical Experts

| ID | Agent Name | Focus | Temperature | Style |
|---|---|---|---|---|
| `smart_contract_auditor` | Smart Contract Auditor | Security, vulnerabilities | 0.2 | Technical |
| `gas_optimization_expert` | Gas Optimization Expert | EVM gas, efficiency | 0.3 | Technical |
| `mev_protection_advisor` | MEV Protection Advisor | Flashbots, frontrunning | 0.3 | Balanced |
| `bridge_specialist` | Bridge Specialist | Cross-chain, security | 0.3 | Balanced |
| `wallet_security_expert` | Wallet Security Expert | Phishing, key management | 0.2 | Beginner-friendly |

## Quick Usage

### Get a specific agent
```python
from app.application.agents.library import get_agent

agent = get_agent("curve_finance_expert")
prompt = agent.to_llm_prompt()
```

### Get all agents by category
```python
from app.application.agents.library import get_defi_specialists, get_technical_experts

defi = get_defi_specialists()
tech = get_technical_experts()
```

### Search agents
```python
from app.application.agents.library import search_agents

security = search_agents("security")
lending = search_agents("lending")
```

### Advanced filtering
```python
from app.application.agents.library import get_agent_registry

registry = get_agent_registry()

# By protocol
aave = registry.get_agents_by_protocol("aave")

# By tag
audits = registry.get_agents_by_tag("audit")

# Get stats
stats = registry.get_library_stats()
```

## Common Use Cases

### Security Audit
```python
auditor = get_agent("smart_contract_auditor")
```

### Gas Optimization
```python
gas_expert = get_agent("gas_optimization_expert")
```

### DeFi Strategy
```python
curve = get_agent("curve_finance_expert")
yearn = get_agent("yearn_strategist")
```

### User Safety
```python
wallet = get_agent("wallet_security_expert")
mev = get_agent("mev_protection_advisor")
```

## Agent Properties

```python
agent.name                    # Display name
agent.description            # Brief description
agent.system_prompt          # Expert prompt
agent.temperature            # 0.2-0.7
agent.max_tokens            # 1000-3000
agent.response_style        # technical/balanced/beginner-friendly
agent.expertise_areas       # List of domains
agent.personality_traits    # Dict of traits
agent.capabilities          # List of AgentCapability
agent.preferred_llm_provider  # openai/anthropic
agent.fallback_llm_provider   # fallback option
```

## Methods

```python
agent.to_llm_prompt()       # Generate system prompt
agent.validate()            # Validate configuration
```

## Response Styles

- **technical**: Code examples, precise terminology (developers)
- **balanced**: Mix of technical and accessible (intermediate)
- **beginner-friendly**: Clear explanations (all users)

## Temperature Guide

- **0.2**: Security-critical (auditor, wallet)
- **0.25-0.3**: Financial precision (Aave, Compound, Curve)
- **0.3**: Technical analysis (gas, MEV, bridge)
- **0.4**: Strategic thinking (Yearn)

## Example Queries by Agent

### Curve Finance Expert
- "What's the best Curve pool for stablecoins?"
- "How does veCRV boost work?"
- "Calculate IL for 3pool position"

### Aave Specialist
- "What's a safe health factor?"
- "Should I use E-mode?"
- "How to avoid liquidation?"

### Uniswap Expert
- "Best price range for ETH/USDC LP?"
- "Which fee tier should I use?"
- "Calculate IL on V3 position"

### Smart Contract Auditor
- "Review this contract for vulnerabilities"
- "Is this code safe from reentrancy?"
- "Audit this DeFi protocol"

### Gas Optimization Expert
- "How to reduce gas in my contract?"
- "Optimize this function"
- "When to submit transactions?"

### MEV Protection Advisor
- "How to avoid sandwich attacks?"
- "Should I use Flashbots?"
- "Protect my large trade"

### Bridge Specialist
- "Which bridge is safest?"
- "How to bridge to Arbitrum?"
- "My transfer is stuck"

### Wallet Security Expert
- "Is this website a scam?"
- "How to backup seed phrase?"
- "Best hardware wallet?"

## Testing

```bash
python3 -m app.application.agents.library.test_library
```

All 10 tests should pass.

## Import Cheatsheet

```python
# Individual factory functions
from app.application.agents.library import (
    create_curve_finance_expert,
    create_aave_specialist,
    create_uniswap_expert,
    create_yearn_strategist,
    create_compound_advisor,
    create_smart_contract_auditor,
    create_gas_optimization_expert,
    create_mev_protection_advisor,
    create_bridge_specialist,
    create_wallet_security_expert,
)

# Convenience functions (recommended)
from app.application.agents.library import (
    get_agent,
    get_all_agents,
    get_defi_specialists,
    get_technical_experts,
    search_agents,
    get_agent_registry,
    get_library_info,
)

# Registry classes
from app.application.agents.library import (
    AgentLibraryRegistry,
    AgentCategory,
    AgentLibraryEntry,
)
```

## Tips

1. **Cache agents**: Create once, reuse multiple times
2. **Validate first**: Always check `agent.validate()` before use
3. **Use search**: Don't know which agent? Use `search_agents()`
4. **Check metadata**: Registry provides rich metadata for each agent
5. **Test prompts**: Generate system prompt to preview agent behavior
