# Agent Library - Pre-configured Custom Agent Personalities

A curated library of 10+ expert AI agents specialized in DeFi protocols and blockchain development.

## Overview

This library provides production-ready agent configurations optimized for specific domains. Each agent is pre-configured with:

- **Expert system prompts** - Detailed domain knowledge and expertise
- **Optimized parameters** - Temperature, max_tokens, response style
- **Personality traits** - Analytical, risk-aware, security-focused, etc.
- **Capabilities** - DeFi analysis, risk assessment, code review, etc.
- **LLM provider preferences** - OpenAI, Anthropic fallbacks

## Categories

### DeFi Specialists (5 agents)

Expert agents for major DeFi protocols:

1. **Curve Finance Expert** (`curve_finance_expert`)
   - Curve pool mechanics (stableswap, cryptoswap)
   - Liquidity provision strategies
   - veCRV tokenomics and gauge voting
   - Risk assessment and IL calculation
   - **Use for**: Pool selection, yield optimization, strategy planning

2. **Aave Specialist** (`aave_specialist`)
   - Aave V2/V3 protocol mechanics
   - Health factor management
   - Lending/borrowing strategies
   - Liquidation risk prevention
   - **Use for**: Position management, risk monitoring, rate optimization

3. **Uniswap Expert** (`uniswap_expert`)
   - Uniswap V2/V3 AMM mechanics
   - Concentrated liquidity strategies
   - LP position optimization
   - Fee tier selection
   - **Use for**: LP strategies, range selection, IL analysis

4. **Yearn Strategist** (`yearn_strategist`)
   - Yearn vault mechanics
   - Strategy composition and risk
   - APY optimization
   - Auto-compounding strategies
   - **Use for**: Vault selection, yield farming, passive income

5. **Compound Advisor** (`compound_advisor`)
   - Compound V2/V3 money markets
   - Collateral factor optimization
   - Interest rate modeling
   - COMP governance
   - **Use for**: Lending strategies, collateral management

### Technical Experts (5 agents)

Specialized agents for blockchain development and security:

1. **Smart Contract Auditor** (`smart_contract_auditor`)
   - Security vulnerability detection
   - Code audit and review
   - Attack vector analysis
   - Best practices guidance
   - **Use for**: Security audits, code review, vulnerability assessment

2. **Gas Optimization Expert** (`gas_optimization_expert`)
   - EVM gas optimization
   - Transaction efficiency
   - Storage pattern optimization
   - EIP-1559 strategies
   - **Use for**: Gas cost reduction, optimization review

3. **MEV Protection Advisor** (`mev_protection_advisor`)
   - MEV attack prevention
   - Flashbots integration
   - Transaction privacy
   - Sandwich attack protection
   - **Use for**: MEV risk assessment, protection strategies

4. **Bridge Specialist** (`bridge_specialist`)
   - Cross-chain bridge security
   - Bridge comparison and selection
   - Multi-chain strategies
   - Recovery procedures
   - **Use for**: Bridge selection, cross-chain transfers

5. **Wallet Security Expert** (`wallet_security_expert`)
   - Wallet security best practices
   - Phishing prevention
   - Key management
   - Hardware wallet guidance
   - **Use for**: Wallet setup, security audits, user education

## Usage

### Basic Usage

```python
from app.application.agents.library import get_agent

# Get a specific agent
curve_expert = get_agent("curve_finance_expert")

# Use the agent configuration
print(f"Agent: {curve_expert.name}")
print(f"Temperature: {curve_expert.temperature}")
print(f"Expertise: {curve_expert.expertise_areas}")

# Convert to LLM prompt
system_prompt = curve_expert.to_llm_prompt()
```

### Get Multiple Agents

```python
from app.application.agents.library import (
    get_all_agents,
    get_defi_specialists,
    get_technical_experts,
)

# Get all agents
all_agents = get_all_agents()

# Get category-specific agents
defi_agents = get_defi_specialists()
tech_agents = get_technical_experts()
```

### Search and Filter

```python
from app.application.agents.library import get_agent_registry, search_agents

# Search by text
security_agents = search_agents("security")
lending_agents = search_agents("lending")

# Advanced filtering with registry
registry = get_agent_registry()

# Get agents by protocol
aave_agents = registry.get_agents_by_protocol("aave")

# Get agents by tag
audit_agents = registry.get_agents_by_tag("audit")

# Get library statistics
stats = registry.get_library_stats()
print(f"Total agents: {stats['total_agents']}")
print(f"Available tags: {stats['tags']}")
```

### Agent Summaries

```python
from app.application.agents.library import get_agent_registry

registry = get_agent_registry()

# Get all agent summaries (useful for UI)
summaries = registry.list_agent_summaries()

for summary in summaries:
    print(f"{summary['name']}: {summary['description']}")
    print(f"  Category: {summary['category']}")
    print(f"  Tags: {', '.join(summary['tags'])}")
```

## Integration with LLM Gateway

```python
from app.application.agents.library import get_agent
from app.infrastructure.adapters.ai.llm_gateway import LLMGateway

# Get agent configuration
agent = get_agent("smart_contract_auditor")

# Create LLM gateway with agent configuration
llm = LLMGateway(
    provider=agent.preferred_llm_provider,
    model="gpt-4",
    temperature=agent.temperature,
    max_tokens=agent.max_tokens,
)

# Use agent's system prompt
response = llm.chat(
    messages=[
        {"role": "system", "content": agent.to_llm_prompt()},
        {"role": "user", "content": "Review this Solidity contract..."},
    ]
)
```

## Agent Configuration Structure

Each agent configuration includes:

```python
CustomAgentConfig(
    config_id=uuid4(),
    name="Agent Name",
    description="Brief description",
    system_prompt="Detailed expert prompt...",
    capabilities=[
        AgentCapability.DEFI_ANALYSIS,
        AgentCapability.RISK_ASSESSMENT,
    ],
    temperature=0.3,  # 0.0-2.0
    max_tokens=2000,
    personality_traits={
        "analytical": 0.9,
        "risk_aware": 0.85,
        # ... more traits
    },
    expertise_areas=[
        "Domain 1",
        "Domain 2",
        # ...
    ],
    response_style="technical",  # technical, balanced, beginner-friendly
    preferred_llm_provider="openai",
    fallback_llm_provider="anthropic",
    is_active=True,
)
```

## Response Styles

Agents are configured with different response styles:

- **technical**: Detailed technical explanations with code examples (developers, advanced users)
- **balanced**: Mix of technical and accessible language (intermediate users)
- **beginner-friendly**: Clear, accessible explanations (all users, educational content)

## Temperature Settings

Temperature is optimized per agent:

- **0.2-0.3**: Security-critical agents (auditor, wallet security) - precise, consistent
- **0.3-0.4**: Technical experts (gas optimization, MEV) - balanced
- **0.4-0.7**: Strategic agents (Yearn, general DeFi) - creative problem-solving

## Adding New Agents

To add a new agent to the library:

1. Create agent configuration file: `src/app/application/agents/library/new_agent.py`

```python
from uuid import uuid4
from app.domain.value_objects.chat.orchestration import CustomAgentConfig, AgentCapability

def create_new_agent() -> CustomAgentConfig:
    system_prompt = """You are an expert in..."""

    return CustomAgentConfig(
        config_id=uuid4(),
        name="New Agent",
        # ... configuration
    )

AGENT_METADATA = {
    "category": "defi_specialist",  # or "technical_expert"
    "protocol": "protocol_name",
    "tags": ["tag1", "tag2"],
    # ...
}
```

2. Register in `agent_registry.py`:

```python
from app.application.agents.library.new_agent import create_new_agent, AGENT_METADATA as NEW_METADATA

# In _register_all_agents():
self._register(
    "new_agent",
    create_new_agent,
    NEW_METADATA,
    AgentCategory.DEFI_SPECIALIST,
)
```

3. Export in `__init__.py`

## Testing

Test individual agents:

```python
from app.application.agents.library import get_agent

agent = get_agent("curve_finance_expert")

# Validate configuration
errors = agent.validate()
assert len(errors) == 0, f"Validation errors: {errors}"

# Test system prompt generation
prompt = agent.to_llm_prompt()
assert len(prompt) > 100

# Check configuration
assert 0.0 <= agent.temperature <= 2.0
assert agent.max_tokens >= 100
```

## Best Practices

1. **Use appropriate agents**: Match agent expertise to user query
2. **Validate configurations**: Always validate before using in production
3. **Monitor performance**: Track agent response quality and user satisfaction
4. **Update prompts**: Keep system prompts current with protocol updates
5. **Test thoroughly**: Validate agent responses for accuracy and safety

## Future Enhancements

Potential additions to the library:

- More protocol specialists (Lido, Rocket Pool, Balancer)
- Strategy-specific agents (arbitrage, liquidation, MEV)
- Educational agents (beginner guides, tutorials)
- Governance experts (voting, proposals, DAOs)
- NFT specialists (marketplaces, valuations, trends)

## Support

For issues or questions about the agent library:

1. Check this README and code documentation
2. Review agent metadata and use cases
3. Test with the registry search and filter functions
4. Consult the main application documentation

## Version History

- **v1.0.0** (2024): Initial release with 10 expert agents
  - 5 DeFi specialists
  - 5 technical experts
  - Full registry and search capabilities
