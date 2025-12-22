"""
Quick test script to verify agent library functionality.

Run this to ensure all agents are properly configured and the registry works.
"""

from app.application.agents.library import (
    get_agent,
    get_all_agents,
    get_defi_specialists,
    get_technical_experts,
    search_agents,
    get_agent_registry,
    get_library_info,
)


def test_all_agents_load():
    """Test that all agents can be loaded."""
    print("Testing: All agents load correctly...")

    all_agents = get_all_agents()
    assert len(all_agents) == 10, f"Expected 10 agents, got {len(all_agents)}"

    for agent in all_agents:
        assert agent.name, f"Agent missing name: {agent}"
        assert agent.description, f"Agent missing description: {agent.name}"
        assert agent.system_prompt, f"Agent missing system_prompt: {agent.name}"

    print(f"✓ All {len(all_agents)} agents loaded successfully")


def test_categories():
    """Test category filtering."""
    print("\nTesting: Category filtering...")

    defi = get_defi_specialists()
    tech = get_technical_experts()

    assert len(defi) == 5, f"Expected 5 DeFi specialists, got {len(defi)}"
    assert len(tech) == 5, f"Expected 5 technical experts, got {len(tech)}"

    print(f"✓ DeFi specialists: {len(defi)}")
    print(f"✓ Technical experts: {len(tech)}")


def test_specific_agents():
    """Test getting specific agents by ID."""
    print("\nTesting: Specific agent retrieval...")

    agent_ids = [
        "curve_finance_expert",
        "aave_specialist",
        "uniswap_expert",
        "yearn_strategist",
        "compound_advisor",
        "smart_contract_auditor",
        "gas_optimization_expert",
        "mev_protection_advisor",
        "bridge_specialist",
        "wallet_security_expert",
    ]

    for agent_id in agent_ids:
        agent = get_agent(agent_id)
        assert agent is not None, f"Failed to get agent: {agent_id}"
        print(f"✓ {agent_id}: {agent.name}")


def test_agent_validation():
    """Test that all agents pass validation."""
    print("\nTesting: Agent configuration validation...")

    all_agents = get_all_agents()
    for agent in all_agents:
        errors = agent.validate()
        assert len(errors) == 0, f"Validation errors for {agent.name}: {errors}"

    print(f"✓ All {len(all_agents)} agents pass validation")


def test_agent_configurations():
    """Test agent configuration parameters."""
    print("\nTesting: Agent configuration parameters...")

    all_agents = get_all_agents()
    for agent in all_agents:
        # Check temperature range
        assert 0.0 <= agent.temperature <= 2.0, f"{agent.name}: Invalid temperature {agent.temperature}"

        # Check max_tokens
        assert 100 <= agent.max_tokens <= 8000, f"{agent.name}: Invalid max_tokens {agent.max_tokens}"

        # Check required fields
        assert agent.capabilities, f"{agent.name}: Missing capabilities"
        assert agent.personality_traits, f"{agent.name}: Missing personality_traits"
        assert agent.expertise_areas, f"{agent.name}: Missing expertise_areas"
        assert agent.response_style in ["technical", "balanced", "beginner-friendly"], \
            f"{agent.name}: Invalid response_style {agent.response_style}"

    print(f"✓ All agent configurations are valid")


def test_system_prompts():
    """Test system prompt generation."""
    print("\nTesting: System prompt generation...")

    all_agents = get_all_agents()
    for agent in all_agents:
        prompt = agent.to_llm_prompt()
        assert len(prompt) > 100, f"{agent.name}: System prompt too short ({len(prompt)} chars)"
        assert agent.name in prompt, f"{agent.name}: Name not in system prompt"

    print(f"✓ All {len(all_agents)} agents have valid system prompts")


def test_search():
    """Test search functionality."""
    print("\nTesting: Agent search...")

    # Search for security-related agents
    security = search_agents("security")
    assert len(security) > 0, "No security agents found"
    print(f"✓ Found {len(security)} security-related agents")

    # Search for lending
    lending = search_agents("lending")
    assert len(lending) > 0, "No lending agents found"
    print(f"✓ Found {len(lending)} lending-related agents")

    # Search for optimization
    optimization = search_agents("optimization")
    assert len(optimization) > 0, "No optimization agents found"
    print(f"✓ Found {len(optimization)} optimization-related agents")


def test_registry_features():
    """Test advanced registry features."""
    print("\nTesting: Registry advanced features...")

    registry = get_agent_registry()

    # Test protocol filtering
    aave_agents = registry.get_agents_by_protocol("aave")
    assert len(aave_agents) > 0, "No Aave agents found"
    print(f"✓ Protocol filtering: {len(aave_agents)} Aave agents")

    # Test tag filtering
    audit_agents = registry.get_agents_by_tag("audit")
    print(f"✓ Tag filtering: {len(audit_agents)} audit-related agents")

    # Test stats
    stats = registry.get_library_stats()
    assert stats["total_agents"] == 10, f"Stats show wrong count: {stats['total_agents']}"
    print(f"✓ Library stats: {stats['total_agents']} total agents")

    # Test summaries
    summaries = registry.list_agent_summaries()
    assert len(summaries) == 10, f"Wrong number of summaries: {len(summaries)}"
    print(f"✓ Agent summaries: {len(summaries)} entries")


def test_library_info():
    """Test library info function."""
    print("\nTesting: Library info...")

    info = get_library_info()
    assert "version" in info, "Missing version in library info"
    assert "stats" in info, "Missing stats in library info"
    print(f"✓ Library version: {info['version']}")
    print(f"✓ Library stats: {info['stats']}")


def test_personality_traits():
    """Test personality traits are properly defined."""
    print("\nTesting: Personality traits...")

    all_agents = get_all_agents()
    for agent in all_agents:
        for trait, value in agent.personality_traits.items():
            assert 0.0 <= value <= 1.0, f"{agent.name}: Invalid trait value {trait}={value}"

    print(f"✓ All personality traits are in valid range [0.0, 1.0]")


def run_all_tests():
    """Run all tests."""
    print("=" * 80)
    print("AGENT LIBRARY TEST SUITE")
    print("=" * 80)

    tests = [
        test_all_agents_load,
        test_categories,
        test_specific_agents,
        test_agent_validation,
        test_agent_configurations,
        test_system_prompts,
        test_search,
        test_registry_features,
        test_library_info,
        test_personality_traits,
    ]

    passed = 0
    failed = 0

    for test_fn in tests:
        try:
            test_fn()
            passed += 1
        except AssertionError as e:
            print(f"✗ FAILED: {test_fn.__name__}")
            print(f"  Error: {e}")
            failed += 1
        except Exception as e:
            print(f"✗ ERROR: {test_fn.__name__}")
            print(f"  Error: {e}")
            failed += 1

    print("\n" + "=" * 80)
    print(f"TEST RESULTS: {passed} passed, {failed} failed")
    print("=" * 80)

    if failed == 0:
        print("\n🎉 All tests passed! Agent library is working correctly.")
    else:
        print(f"\n⚠️  {failed} test(s) failed. Please review the errors above.")

    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    exit(0 if success else 1)
