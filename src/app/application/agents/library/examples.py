"""
Agent Library Usage Examples.

Demonstrates how to use the pre-configured agent library in various scenarios.
"""

from app.application.agents.library import (
    get_agent,
    get_all_agents,
    get_defi_specialists,
    get_technical_experts,
    search_agents,
    get_agent_registry,
)


def example_basic_usage():
    """Example 1: Basic agent retrieval and usage."""
    print("\n=== Example 1: Basic Usage ===\n")

    # Get a specific agent
    curve_expert = get_agent("curve_finance_expert")

    if curve_expert:
        print(f"Agent Name: {curve_expert.name}")
        print(f"Description: {curve_expert.description}")
        print(f"Temperature: {curve_expert.temperature}")
        print(f"Max Tokens: {curve_expert.max_tokens}")
        print(f"Response Style: {curve_expert.response_style}")
        print(f"Expertise Areas: {', '.join(curve_expert.expertise_areas)}")

        # Validate configuration
        errors = curve_expert.validate()
        if errors:
            print(f"Validation errors: {errors}")
        else:
            print("Configuration is valid!")

        # Get system prompt
        prompt = curve_expert.to_llm_prompt()
        print(f"\nSystem prompt length: {len(prompt)} characters")
        print(f"First 200 chars: {prompt[:200]}...")


def example_get_by_category():
    """Example 2: Get agents by category."""
    print("\n=== Example 2: Get Agents by Category ===\n")

    # Get all DeFi specialists
    defi_agents = get_defi_specialists()
    print(f"DeFi Specialists ({len(defi_agents)}):")
    for agent in defi_agents:
        print(f"  - {agent.name}")

    print()

    # Get all technical experts
    tech_agents = get_technical_experts()
    print(f"Technical Experts ({len(tech_agents)}):")
    for agent in tech_agents:
        print(f"  - {agent.name}")


def example_search_and_filter():
    """Example 3: Search and filter agents."""
    print("\n=== Example 3: Search and Filter ===\n")

    # Search for security-related agents
    security_agents = search_agents("security")
    print(f"Security-related agents ({len(security_agents)}):")
    for agent in security_agents:
        print(f"  - {agent.name}: {agent.description[:60]}...")

    print()

    # Search for lending-related agents
    lending_agents = search_agents("lending")
    print(f"Lending-related agents ({len(lending_agents)}):")
    for agent in lending_agents:
        print(f"  - {agent.name}")


def example_advanced_filtering():
    """Example 4: Advanced filtering with registry."""
    print("\n=== Example 4: Advanced Filtering ===\n")

    registry = get_agent_registry()

    # Get agents by protocol
    print("Agents by protocol:")
    protocols = ["aave", "curve_finance", "uniswap"]
    for protocol in protocols:
        agents = registry.get_agents_by_protocol(protocol)
        if agents:
            print(f"  {protocol}: {', '.join(a.name for a in agents)}")

    print()

    # Get agents by tag
    print("Agents by tag:")
    tags = ["audit", "optimization", "bridge"]
    for tag in tags:
        agents = registry.get_agents_by_tag(tag)
        if agents:
            print(f"  {tag}: {', '.join(a.name for a in agents)}")


def example_library_stats():
    """Example 5: Library statistics and metadata."""
    print("\n=== Example 5: Library Statistics ===\n")

    registry = get_agent_registry()
    stats = registry.get_library_stats()

    print(f"Total Agents: {stats['total_agents']}")
    print(f"DeFi Specialists: {stats['defi_specialists']}")
    print(f"Technical Experts: {stats['technical_experts']}")
    print(f"Unique Tags: {stats['unique_tags']}")
    print(f"\nAll Tags: {', '.join(stats['tags'])}")
    print(f"\nAll Agent IDs:")
    for agent_id in stats["agent_ids"]:
        print(f"  - {agent_id}")


def example_agent_summaries():
    """Example 6: Agent summaries for UI display."""
    print("\n=== Example 6: Agent Summaries ===\n")

    registry = get_agent_registry()
    summaries = registry.list_agent_summaries()

    for summary in summaries:
        print(f"\n{summary['name']}")
        print(f"  ID: {summary['id']}")
        print(f"  Category: {summary['category']}")
        print(f"  Description: {summary['description'][:80]}...")
        print(f"  Tags: {', '.join(summary['tags'])}")
        print(f"  Response Style: {summary['response_style']}")
        print(f"  Temperature: {summary['temperature']}")


def example_personality_traits():
    """Example 7: Examining agent personality traits."""
    print("\n=== Example 7: Agent Personality Traits ===\n")

    agents = get_all_agents()

    for agent in agents:
        print(f"\n{agent.name}:")
        print(f"  Response Style: {agent.response_style}")
        print(f"  Temperature: {agent.temperature}")
        print("  Personality Traits:")
        for trait, value in agent.personality_traits.items():
            print(f"    - {trait}: {value:.2f}")


def example_llm_integration():
    """Example 8: Integration with LLM (pseudo-code)."""
    print("\n=== Example 8: LLM Integration (Pseudo-code) ===\n")

    # Get agent
    auditor = get_agent("smart_contract_auditor")

    if auditor:
        print(f"Using agent: {auditor.name}")
        print(f"Provider: {auditor.preferred_llm_provider}")
        print(f"Fallback: {auditor.fallback_llm_provider}")

        # Pseudo-code for LLM integration
        print("\n# Integration code:")
        print(f"""
llm_config = {{
    "provider": "{auditor.preferred_llm_provider}",
    "temperature": {auditor.temperature},
    "max_tokens": {auditor.max_tokens},
}}

messages = [
    {{"role": "system", "content": auditor.to_llm_prompt()}},
    {{"role": "user", "content": "Review this contract for vulnerabilities..."}},
]

# response = llm_gateway.chat(messages, **llm_config)
        """)


def example_use_case_matching():
    """Example 9: Match user query to appropriate agent."""
    print("\n=== Example 9: Use Case Matching ===\n")

    # Sample user queries and matched agents
    use_cases = [
        ("How to optimize gas in my Solidity contract?", "gas_optimization_expert"),
        ("What's the best Curve pool for stablecoins?", "curve_finance_expert"),
        ("Is this website a phishing scam?", "wallet_security_expert"),
        ("Should I use Ethereum bridge or Arbitrum native?", "bridge_specialist"),
        ("How to avoid frontrunning on Uniswap?", "mev_protection_advisor"),
    ]

    for query, expected_agent_id in use_cases:
        agent = get_agent(expected_agent_id)
        if agent:
            print(f'\nQuery: "{query}"')
            print(f"→ Matched Agent: {agent.name}")
            print(f"  Expertise: {', '.join(agent.expertise_areas[:3])}...")


def example_compare_agents():
    """Example 10: Compare agents side-by-side."""
    print("\n=== Example 10: Compare Agents ===\n")

    # Compare lending protocol specialists
    agent_ids = ["aave_specialist", "compound_advisor"]
    agents = [get_agent(aid) for aid in agent_ids]

    print("Comparison of Lending Protocol Specialists:\n")
    print(f"{'Attribute':<20} {'Aave Specialist':<30} {'Compound Advisor':<30}")
    print("-" * 80)

    for agent in agents:
        if agent:
            print(f"{'Temperature':<20} {agent.temperature:<30} ", end="")
    print()

    for agent in agents:
        if agent:
            print(f"{'Max Tokens':<20} {agent.max_tokens:<30} ", end="")
    print()

    for agent in agents:
        if agent:
            print(f"{'Response Style':<20} {agent.response_style:<30} ", end="")
    print()

    print("\nExpertise Areas:")
    for agent in agents:
        if agent:
            print(f"\n{agent.name}:")
            for area in agent.expertise_areas:
                print(f"  - {area}")


def run_all_examples():
    """Run all examples."""
    examples = [
        example_basic_usage,
        example_get_by_category,
        example_search_and_filter,
        example_advanced_filtering,
        example_library_stats,
        example_agent_summaries,
        example_personality_traits,
        example_llm_integration,
        example_use_case_matching,
        example_compare_agents,
    ]

    for example_fn in examples:
        try:
            example_fn()
        except Exception as e:
            print(f"\nError in {example_fn.__name__}: {e}")

    print("\n" + "=" * 80)
    print("All examples completed!")
    print("=" * 80)


if __name__ == "__main__":
    # Run all examples
    run_all_examples()

    # Or run individual examples:
    # example_basic_usage()
    # example_search_and_filter()
    # example_library_stats()
